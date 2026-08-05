"""Resolve model-free subject, harness, task, verifier, and image identities."""

from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import subprocess
from collections.abc import Iterable
from pathlib import Path

from harness import lib
from harness.launch_contract import (
    LaunchRequest,
    LaunchRuntimeIdentity,
)


def _host_memory_bytes() -> int:
    """Return physical host RAM used for confirmed launch admission."""
    page_count = os.sysconf("SC_PHYS_PAGES")
    page_size = os.sysconf("SC_PAGE_SIZE")
    if not isinstance(page_count, int) or not isinstance(page_size, int):
        raise TypeError(
            "Launch host memory unresolved: sysconf returned non-integers"
        )
    host_memory_bytes = page_count * page_size
    if host_memory_bytes <= 0:
        raise RuntimeError(
            "Launch host memory unresolved: physical memory must be positive"
        )
    return host_memory_bytes


def _identity_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file() or path.is_symlink():
            files.add(path)
        elif path.is_dir():
            files.update(
                candidate
                for candidate in path.rglob("*")
                if (candidate.is_file() or candidate.is_symlink())
                and "__pycache__" not in candidate.parts
            )
    return sorted(files)


def _file_set_identity(root: Path, paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in _identity_files(paths):
        relative_path = path.relative_to(root).as_posix()
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(b"1" if path.stat().st_mode & 0o100 else b"0")
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


class RepositoryLaunchRuntimeResolver:
    """Resolve pinned runtime identities without pulling or running images."""

    def __init__(self, repository_root: Path, tasks_root: Path) -> None:
        """Bind runtime resolution to one repository and task corpus."""
        self.repository_root = repository_root
        self.tasks_root = tasks_root

    def _pi_subject_version(self) -> str:
        dockerfile = self.repository_root / "harness" / "Dockerfile.pi-agent"
        if not dockerfile.is_file():
            raise ValueError(
                "Launch runtime identity unresolved: Pi Dockerfile missing at "
                f"{dockerfile}"
            )
        match = re.search(
            r"^ARG PI_VERSION=(?P<version>\S+)$",
            dockerfile.read_text(),
            re.MULTILINE,
        )
        if match is None:
            raise ValueError(
                "Launch runtime identity unresolved: PI_VERSION is not "
                f"pinned in {dockerfile}"
            )
        return f"pi@{match.group('version')}"

    def _prime_agent_subject_version(self) -> str:
        """Read the pinned Prime Agent version without starting the subject."""
        dockerfile = self.repository_root / "harness" / "Dockerfile.prime-agent"
        if not dockerfile.is_file():
            raise ValueError(
                "Launch runtime identity unresolved: Prime Agent Dockerfile "
                f"missing at {dockerfile}"
            )
        match = re.search(
            r"^ARG PRIME_AGENT_VERSION=(?P<version>\S+)$",
            dockerfile.read_text(),
            re.MULTILINE,
        )
        if match is None:
            raise ValueError(
                "Launch runtime identity unresolved: PRIME_AGENT_VERSION is "
                f"not pinned in {dockerfile}"
            )
        return f"prime-agent@{match.group('version')}"

    @staticmethod
    def _image_identity(image_reference: str) -> str:
        completed = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                "{{.Id}}",
                image_reference,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        identity = completed.stdout.strip()
        if completed.returncode != 0 or not identity:
            detail = completed.stderr.strip() or "image is not present"
            raise ValueError(
                "Launch runtime identity unresolved: immutable image identity "
                f"for {image_reference!r}: {detail}"
            )
        return identity

    def _omp_subject_identity(self) -> tuple[str, dict[str, object]]:
        configured_binary = os.environ.get("OMP_BINARY")
        binary = Path(configured_binary) if configured_binary else None
        if binary is None:
            discovered_binary = shutil.which("omp")
            if discovered_binary is not None:
                binary = Path(discovered_binary)
        if binary is None or not binary.is_file():
            raise ValueError(
                "Launch runtime identity unresolved: OMP binary missing; "
                "set OMP_BINARY or install omp on PATH"
            )
        resolved_binary = binary.resolve()
        completed = subprocess.run(
            [str(resolved_binary), "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        version_output = (completed.stdout + completed.stderr).strip()
        if completed.returncode != 0 or not version_output:
            raise ValueError(
                "Launch runtime identity unresolved: OMP version probe "
                f"failed for {resolved_binary}"
            )
        version_match = re.search(r"\d+\.\d+\.\d+", version_output)
        if version_match is None:
            raise ValueError(
                "Launch runtime identity unresolved: OMP version output "
                f"has no semantic version: {version_output!r}"
            )
        return (
            f"omp@{version_match.group(0)}",
            {
                "binaryFingerprint": (
                    "sha256:" + hashlib.sha256(resolved_binary.read_bytes()).hexdigest()
                ),
                "binaryPath": str(resolved_binary),
                "versionOutput": version_output,
            },
        )

    def _harness_revision(self) -> str:
        paths = [
            self.repository_root / "harness",
            self.repository_root / "harness" / "Dockerfile.pi-agent",
            self.repository_root / "pyproject.toml",
            self.repository_root / "uv.lock",
        ]
        return _file_set_identity(self.repository_root, paths)

    def _task_revision(self, tasks: tuple[str, ...]) -> str:
        return _file_set_identity(
            self.tasks_root,
            [self.tasks_root / task for task in tasks],
        )

    def _task_revision_aliases(
        self,
        tasks: tuple[str, ...],
    ) -> dict[str, frozenset[str]]:
        """Map reproducible nested-subset revisions to their selected tasks."""
        selected_tasks = frozenset(tasks)
        aliases: dict[str, set[str]] = {self._task_revision(tasks): set(selected_tasks)}
        subsets_root = self.repository_root / "subsets"
        if not subsets_root.is_dir():
            return {
                revision: frozenset(alias_tasks)
                for revision, alias_tasks in aliases.items()
            }
        for subset_path in sorted(subsets_root.glob("*.txt")):
            subset_tasks = tuple(
                line
                for raw_line in subset_path.read_text().splitlines()
                if (line := raw_line.strip()) and not line.startswith("#")
            )
            if not subset_tasks or not frozenset(subset_tasks) <= selected_tasks:
                continue
            revision = self._task_revision(subset_tasks)
            aliases.setdefault(revision, set()).update(subset_tasks)
        return {
            revision: frozenset(alias_tasks)
            for revision, alias_tasks in aliases.items()
        }

    def _verifier_identity(self, task: str) -> str:
        verifier_root = self.tasks_root / task / "tests"
        if not verifier_root.is_dir():
            raise ValueError(
                "Launch runtime identity unresolved: verifier inputs "
                f"missing for task {task!r} at {verifier_root}"
            )
        return _file_set_identity(self.tasks_root, [verifier_root])

    @staticmethod
    def _omp_codex_credential_available() -> bool:
        database_path = Path.home() / ".omp" / "agent" / "agent.db"
        if not database_path.is_file():
            return False
        try:
            with sqlite3.connect(
                f"file:{database_path}?mode=ro",
                uri=True,
            ) as connection:
                credential = connection.execute(
                    "select 1 from auth_credentials where provider=? limit 1",
                    ("openai-codex",),
                ).fetchone()
        except sqlite3.Error:
            return False
        return credential is not None

    @classmethod
    def _available_credential_routes(cls, subject: str) -> frozenset[str]:
        routes = frozenset(name for name, value in os.environ.items() if value.strip())
        if subject == "omp":
            credential_available = cls._omp_codex_credential_available()
        elif subject == "pi":
            oauth_path = Path.home() / ".pi" / "agent" / "auth.json"
            credential_available = oauth_path.is_file()
        else:
            credential_available = False
        if credential_available:
            return routes | {"OPENAI_CODEX_OAUTH"}
        return routes

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Resolve repository, task, verifier, subject, and image identity."""
        if request.subject == "pi":
            subject_version = self._pi_subject_version()
            subject_capabilities = frozenset(
                {
                    "native-session-usage",
                    "pi-extensions",
                    "pi-rpc",
                    "pi-skills",
                }
            )
            subject_runtime_identity: dict[str, object] = {}
        elif request.subject == "omp":
            subject_version, subject_runtime_identity = self._omp_subject_identity()
            subject_capabilities = frozenset(
                {
                    "native-session-usage",
                    "omp-extensions",
                    "omp-rpc",
                    "omp-tools",
                }
            )
        elif request.subject == "prime-agent":
            subject_version = self._prime_agent_subject_version()
            subject_runtime_identity = {}
            subject_capabilities = frozenset(
                {
                    "native-session-usage",
                    "prime-agent-rpc",
                    "prime-agent-rlm-depth-one",
                    "recursive-child-usage",
                    "zai-bounded-proxy-usage",
                }
            )
        else:
            raise ValueError(
                "Launch runtime identity unresolved: unsupported subject "
                f"{request.subject!r}"
            )
        verifier_identities: dict[str, str] = {}
        image_identities: dict[str, dict[str, str]] = {}
        for task_id in tasks:
            task = lib.load_task(task_id, root=self.tasks_root)
            verifier_identities[task_id] = self._verifier_identity(task_id)
            agent_image = (
                task.prime_agent_image
                if request.subject == "prime-agent"
                else task.pi_image
            )
            image_identities[task_id] = {
                "agent": self._image_identity(agent_image),
                "environment": self._image_identity(task.env_image),
                "verifier": self._image_identity(task.verifier_image),
            }
        return LaunchRuntimeIdentity(
            subject_version=subject_version,
            harness_revision=self._harness_revision(),
            task_revision=self._task_revision(tasks),
            host_memory_bytes=_host_memory_bytes(),
            verifier_identities=verifier_identities,
            immutable_image_identities=image_identities,
            task_revision_aliases=self._task_revision_aliases(tasks),
            subject_capabilities=subject_capabilities,
            available_credential_routes=self._available_credential_routes(
                request.subject
            ),
            subject_runtime_identity=subject_runtime_identity,
        )

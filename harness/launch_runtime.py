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
        dockerfile = self.repository_root / "Dockerfile.pi-agent"
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
            self.repository_root / "Dockerfile.pi-agent",
            self.repository_root / "pyproject.toml",
            self.repository_root / "uv.lock",
        ]
        return _file_set_identity(self.repository_root, paths)

    def _task_revision(self, tasks: tuple[str, ...]) -> str:
        return _file_set_identity(
            self.tasks_root,
            [self.tasks_root / task for task in tasks],
        )

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
        else:
            oauth_path = Path.home() / ".pi" / "agent" / "auth.json"
            credential_available = oauth_path.is_file()
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
            image_identities[task_id] = {
                "agent": self._image_identity(task.pi_image),
                "environment": self._image_identity(task.env_image),
                "verifier": self._image_identity(task.verifier_image),
            }
        return LaunchRuntimeIdentity(
            subject_version=subject_version,
            harness_revision=self._harness_revision(),
            task_revision=self._task_revision(tasks),
            verifier_identities=verifier_identities,
            immutable_image_identities=image_identities,
            subject_capabilities=subject_capabilities,
            available_credential_routes=self._available_credential_routes(
                request.subject
            ),
            subject_runtime_identity=subject_runtime_identity,
        )

"""Create and verify secret-free locks for versioned config leaves."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from harness.config_resolution import (
    ResolvedConfigLeaf,
    parse_versioned_config_identity,
    resolve_config_leaf,
)

_CONFIG_LOCK_FILENAME = "config-lock.json"
_CONFIG_LOCK_SCHEMA_VERSION = 1
_VERSION_IMPACTS = frozenset({"reuse", "recompute", "rerun"})
_SHARED_BEHAVIOR_FILES = frozenset(
    {
        "env",
        "omp-extensions.txt",
        "omp-overlay.yml",
        "omp-system-prompt.md",
        "omp-tools.txt",
        "orchestration.md",
        "pi-flags",
        "smoke.json",
        "system_preamble.md",
    }
)
_SHARED_BEHAVIOR_DIRECTORIES = frozenset({"bin", "extensions", "skills", "tools"})
_IGNORED_BEHAVIOR_DIRECTORIES = frozenset({".git", "__pycache__", "node_modules"})
_METADATA_FIELDS = frozenset(
    {
        "credentialRoutes",
        "declaredRoles",
        "previousRelease",
        "requiredCapabilities",
        "testedSubjectVersions",
        "usageSources",
    }
)
_SECRET_KEY_SUFFIXES = frozenset(
    {
        "accesstoken",
        "apikey",
        "apitoken",
        "authtoken",
        "clientsecret",
        "credential",
        "credentials",
        "password",
        "privatekey",
        "refreshtoken",
        "secret",
        "secretkey",
        "sessiontoken",
    }
)
_CREDENTIAL_ROUTE = re.compile(
    r"^\$(?:\{(?P<braced>[A-Z][A-Z0-9_]*)\}|"
    r"(?P<plain>[A-Z][A-Z0-9_]*))$"
)


@dataclass(frozen=True, slots=True)
class ConfigLockVerification:
    """Describe behavior inputs that differ from a committed config lock."""

    lock_identity: str
    added: tuple[str, ...]
    removed: tuple[str, ...]
    changed: tuple[str, ...]

    @property
    def matches(self) -> bool:
        """Return whether every behavior input still matches the lock."""
        return not (self.added or self.removed or self.changed)


def canonical_config_lock_json(document: Mapping[str, object]) -> str:
    """Serialize a config lock deterministically for commits and identities."""
    return (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def parse_config_lock_json(serialized: str) -> dict[str, object]:
    """Parse one serialized config lock object for canonical round trips."""
    document = json.loads(serialized)
    if not isinstance(document, dict):
        raise TypeError("Config lock invalid: expected a JSON object")
    return document


def _sha256_identity(content: bytes) -> str:
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def _is_secret_key(key: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]", "", key.lower())
    return normalized == "token" or any(
        normalized.endswith(suffix) for suffix in _SECRET_KEY_SUFFIXES
    )


def _is_secret_environment_key(key: str) -> bool:
    return _is_secret_key(key) or key.upper().endswith("_TOKEN")


def _excluded_secret_value(key: str, value: object) -> dict[str, object]:
    if isinstance(value, str):
        route = _CREDENTIAL_ROUTE.fullmatch(value)
        if route is not None:
            return {"credentialRoute": route.group("braced") or route.group("plain")}
    return {"credentialName": key, "secretExcluded": True}


def _exclude_secret_values(value: object) -> object:
    if isinstance(value, dict):
        return {
            str(key): (
                _excluded_secret_value(str(key), item)
                if _is_secret_key(str(key))
                else _exclude_secret_values(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [_exclude_secret_values(item) for item in value]
    return value


def _canonical_json_bytes(content: bytes) -> bytes:
    value = _exclude_secret_values(json.loads(content))
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode()


def _canonical_env_bytes(content: bytes) -> bytes:
    settings: dict[str, object] = {}
    for raw_line in content.decode().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ValueError(
                f"Config lock env invalid: expected KEY=VALUE; got {line!r}"
            )
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        settings[key] = (
            _excluded_secret_value(key, value)
            if _is_secret_environment_key(key)
            else value
        )
    return canonical_config_lock_json(settings).encode()


def _input_content(path: Path) -> bytes:
    if path.is_symlink():
        return os.readlink(path).encode()
    content = path.read_bytes()
    if path.name == "env":
        return _canonical_env_bytes(content)
    if path.suffix == ".json":
        return _canonical_json_bytes(content)
    return content


def _behavior_input_kind(relative_path: Path) -> str:
    parts = relative_path.parts
    if parts[0] == "bin":
        return "generated-tool"
    if relative_path.name in {"package.json", "package-lock.json"}:
        return "package-identity"
    if relative_path.name == "env":
        return "environment"
    if relative_path.name == "smoke.json":
        return "smoke-contract"
    if relative_path.name in {"system_preamble.md", "orchestration.md"}:
        return "prompt"
    if relative_path.name == "pi-flags":
        return "flags"
    if parts[0] == "skills":
        return "skill"
    if parts[0] == "extensions":
        return "extension"
    if relative_path.name in {"settings.json", "models.json", "advisor.json"}:
        return "leaf-settings"
    return "behavior-file"


def _iter_behavior_files(resolved: ResolvedConfigLeaf) -> list[Path]:
    files: set[Path] = set()
    for name in _SHARED_BEHAVIOR_FILES:
        path = resolved.config_root / name
        if path.is_file() or path.is_symlink():
            files.add(path)
    for name in _SHARED_BEHAVIOR_DIRECTORIES:
        directory = resolved.config_root / name
        if not directory.is_dir():
            continue
        for path in directory.rglob("*"):
            if any(part in _IGNORED_BEHAVIOR_DIRECTORIES for part in path.parts):
                continue
            if path.is_file() or path.is_symlink():
                files.add(path)
    for path in resolved.config_leaf.rglob("*"):
        if path.name == _CONFIG_LOCK_FILENAME:
            continue
        if any(part in _IGNORED_BEHAVIOR_DIRECTORIES for part in path.parts):
            continue
        if path.is_file() or path.is_symlink():
            files.add(path)
    return sorted(
        files, key=lambda path: path.relative_to(resolved.config_root).as_posix()
    )


def collect_config_behavior_inputs(
    resolved: ResolvedConfigLeaf,
) -> list[dict[str, object]]:
    """Fingerprint every shared and leaf behavior input for one config leaf."""
    inputs: list[dict[str, object]] = []
    for path in _iter_behavior_files(resolved):
        relative_path = path.relative_to(resolved.config_root)
        inputs.append(
            {
                "executable": bool(path.stat().st_mode & 0o100),
                "fingerprint": _sha256_identity(_input_content(path)),
                "kind": _behavior_input_kind(relative_path),
                "path": relative_path.as_posix(),
                "scope": (
                    "leaf" if path.is_relative_to(resolved.config_leaf) else "shared"
                ),
            }
        )
    return inputs


def _ordered_metadata_value(value: object) -> object:
    if isinstance(value, list):
        normalized = [_ordered_metadata_value(item) for item in value]
        return sorted(
            normalized,
            key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
        )
    if isinstance(value, dict):
        return {
            str(key): _ordered_metadata_value(item)
            for key, item in sorted(value.items())
        }
    return value


def _normalized_metadata(metadata: Mapping[str, object]) -> dict[str, object]:
    unknown = sorted(set(metadata) - _METADATA_FIELDS)
    if unknown:
        raise ValueError(f"Config lock metadata invalid: unknown fields {unknown!r}")
    defaults: dict[str, object] = {
        field: [] for field in _METADATA_FIELDS if field != "previousRelease"
    }
    defaults["previousRelease"] = None
    return {
        field: _ordered_metadata_value(
            _exclude_secret_values(metadata.get(field, defaults[field]))
        )
        for field in sorted(_METADATA_FIELDS)
    }


def build_config_lock_document(
    resolved: ResolvedConfigLeaf,
    config_identity: str,
    version_impact: str,
    metadata: Mapping[str, object],
) -> dict[str, object]:
    """Build a canonical, secret-free config lock without writing it."""
    identity = parse_versioned_config_identity(config_identity)
    if identity is None:
        raise ValueError(
            "Config lock identity required: legacy unversioned configs cannot receive "
            "fabricated locks"
        )
    if version_impact not in _VERSION_IMPACTS:
        raise ValueError(
            "Config lock version impact invalid: expected reuse, recompute, or rerun; "
            f"got {version_impact!r}"
        )
    document: dict[str, object] = {
        "schemaVersion": _CONFIG_LOCK_SCHEMA_VERSION,
        "configIdentity": identity.rendered,
        "configName": identity.name,
        "configVersion": identity.version,
        "versionImpact": version_impact,
        "leaf": {
            "model": resolved.config_leaf.parent.name,
            "thinking": resolved.config_leaf.name,
            "path": resolved.config_leaf.relative_to(resolved.config_root).as_posix(),
        },
        "behaviorInputs": collect_config_behavior_inputs(resolved),
        **_normalized_metadata(metadata),
    }
    document["lockIdentity"] = _document_identity(document)
    return document


def _document_identity(document: Mapping[str, object]) -> str:
    identity_input = dict(document)
    identity_input.pop("lockIdentity", None)
    return _sha256_identity(canonical_config_lock_json(identity_input).encode())


def write_config_lock(
    repository_root: Path,
    config_identity: str,
    model: str,
    thinking: str,
    version_impact: str,
    metadata: Mapping[str, object],
    *,
    replace: bool = False,
) -> Path:
    """Explicitly create or refresh one candidate leaf's config lock."""
    resolved = resolve_config_leaf(
        repository_root,
        config_identity,
        model,
        thinking,
    )
    lock_path = resolved.config_leaf / _CONFIG_LOCK_FILENAME
    if lock_path.exists() and not replace:
        raise FileExistsError(
            f"Config lock already exists: {lock_path}; use the explicit refresh operation"
        )
    document = build_config_lock_document(
        resolved,
        config_identity,
        version_impact,
        metadata,
    )
    lock_path.write_text(canonical_config_lock_json(document))
    return lock_path


def _load_config_lock(lock_path: Path) -> dict[str, object]:
    try:
        document = json.loads(lock_path.read_text())
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(
            f"Config lock invalid: cannot read {lock_path}: {error}"
        ) from error
    if not isinstance(document, dict):
        raise TypeError(f"Config lock invalid: expected object in {lock_path}")
    if document.get("schemaVersion") != _CONFIG_LOCK_SCHEMA_VERSION:
        raise ValueError(
            "Config lock schema unsupported: "
            f"expected {_CONFIG_LOCK_SCHEMA_VERSION}, got {document.get('schemaVersion')!r}"
        )
    return document


def verify_config_lock(
    resolved: ResolvedConfigLeaf,
    config_identity: str,
) -> ConfigLockVerification:
    """Compare current behavior files with a versioned leaf's committed lock."""
    lock_path = resolved.config_leaf / _CONFIG_LOCK_FILENAME
    if not lock_path.is_file():
        raise ValueError(f"Config lock missing: {lock_path}")
    document = _load_config_lock(lock_path)
    if document.get("configIdentity") != config_identity:
        raise ValueError(
            "Config lock identity mismatch: "
            f"requested {config_identity!r}, lock has {document.get('configIdentity')!r}"
        )
    stored_identity = document.get("lockIdentity")
    if not isinstance(stored_identity, str) or stored_identity != _document_identity(
        document
    ):
        raise ValueError(
            f"Config lock identity mismatch: lock document was modified: {lock_path}"
        )

    expected_inputs = document.get("behaviorInputs")
    if not isinstance(expected_inputs, list):
        raise TypeError(
            f"Config lock invalid: behaviorInputs must be a list in {lock_path}"
        )
    expected_by_path: dict[str, object] = {}
    for item in expected_inputs:
        if not isinstance(item, dict):
            raise TypeError(
                f"Config lock invalid: behavior input needs a string path in {lock_path}"
            )
        input_path = item.get("path")
        if not isinstance(input_path, str):
            raise TypeError(
                f"Config lock invalid: behavior input needs a string path in {lock_path}"
            )
        expected_by_path[input_path] = item
    actual_by_path = {
        str(item["path"]): item for item in collect_config_behavior_inputs(resolved)
    }
    expected_paths = set(expected_by_path)
    actual_paths = set(actual_by_path)
    return ConfigLockVerification(
        lock_identity=stored_identity,
        added=tuple(sorted(actual_paths - expected_paths)),
        removed=tuple(sorted(expected_paths - actual_paths)),
        changed=tuple(
            sorted(
                path
                for path in expected_paths & actual_paths
                if expected_by_path[path] != actual_by_path[path]
            )
        ),
    )


def require_matching_config_lock(
    resolved: ResolvedConfigLeaf,
    config_identity: str,
) -> str | None:
    """Require a matching lock for releases while accepting legacy configs."""
    if parse_versioned_config_identity(config_identity) is None:
        return None
    verification = verify_config_lock(resolved, config_identity)
    if not verification.matches:
        raise ValueError(
            "Config lock mismatch: "
            f"config={config_identity!r}; added={list(verification.added)!r}; "
            f"removed={list(verification.removed)!r}; "
            f"changed={list(verification.changed)!r}"
        )
    return verification.lock_identity


def _metadata_from_path(path: Path | None) -> Mapping[str, object]:
    if path is None:
        return {}
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise TypeError(f"Config lock metadata invalid: expected object in {path}")
    return value


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explicitly create, refresh, or verify a versioned config lock."
    )
    subparsers = parser.add_subparsers(dest="operation", required=True)
    for operation in ("create", "refresh"):
        command = subparsers.add_parser(operation)
        command.add_argument("--repository", type=Path, required=True)
        command.add_argument("--config", required=True)
        command.add_argument("--model", required=True)
        command.add_argument("--thinking", required=True)
        command.add_argument(
            "--version-impact",
            choices=sorted(_VERSION_IMPACTS),
            required=True,
        )
        command.add_argument("--metadata", type=Path)
    verify = subparsers.add_parser("verify")
    verify.add_argument("--repository", type=Path, required=True)
    verify.add_argument("--config", required=True)
    verify.add_argument("--model", required=True)
    verify.add_argument("--thinking", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the explicit config-lock maintenance command."""
    args = _argument_parser().parse_args(argv)
    resolved = resolve_config_leaf(
        args.repository,
        args.config,
        args.model,
        args.thinking,
    )
    if args.operation == "verify":
        verification = verify_config_lock(resolved, args.config)
        print(
            json.dumps(
                {
                    "matches": verification.matches,
                    "lockIdentity": verification.lock_identity,
                    "added": verification.added,
                    "removed": verification.removed,
                    "changed": verification.changed,
                },
                sort_keys=True,
            )
        )
        return 0 if verification.matches else 1

    lock_path = write_config_lock(
        args.repository,
        args.config,
        args.model,
        args.thinking,
        args.version_impact,
        _metadata_from_path(args.metadata),
        replace=args.operation == "refresh",
    )
    print(lock_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

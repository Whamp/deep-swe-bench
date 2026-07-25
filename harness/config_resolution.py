"""Resolve one config root, model+thinking leaf, and smoke contract."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

try:
    from harness.lib import model_leaf
except ModuleNotFoundError:
    # Direct harness script execution adds harness/ to sys.path.
    from lib import model_leaf


_VERSIONED_CONFIG_IDENTITY = re.compile(
    r"^(?P<name>[a-z][a-z0-9]*(?:-[a-z0-9]+)*)@"
    r"(?P<version>(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\."
    r"(?:0|[1-9][0-9]*))$"
)
_VAGUE_CONFIG_NAME_SUFFIX = re.compile(r"-(?:v[0-9]+|new|latest)$")


@dataclass(frozen=True, slots=True)
class VersionedConfigIdentity:
    """A canonical config name and semantic release version."""

    name: str
    version: str

    @property
    def rendered(self) -> str:
        """Render the release identity as one config path segment."""
        return f"{self.name}@{self.version}"


@dataclass(frozen=True, slots=True)
class ResolvedConfigLeaf:
    """The exact config files selected for one model and thinking level."""

    config_root: Path
    config_leaf: Path
    smoke_contract: Path | None


def parse_versioned_config_identity(
    config: str,
) -> VersionedConfigIdentity | None:
    """Parse a versioned config identity while preserving legacy names."""
    if "@" not in config:
        return None
    match = _VERSIONED_CONFIG_IDENTITY.fullmatch(config)
    if match is None:
        raise ValueError(
            "Config identity invalid: expected "
            "<name>@<major>.<minor>.<patch> in one path segment; "
            f"got {config!r}"
        )
    name = match.group("name")
    if _VAGUE_CONFIG_NAME_SUFFIX.search(name):
        raise ValueError(
            "Config identity invalid: config names cannot end in vague lineage "
            f"suffixes -v<number>, -new, or -latest; got {config!r}"
        )
    return VersionedConfigIdentity(name=name, version=match.group("version"))


def resolve_config_leaf(
    repository_root: Path,
    config: str,
    model: str,
    thinking: str,
) -> ResolvedConfigLeaf:
    """Resolve exactly one config leaf or raise a searchable request error."""
    parse_versioned_config_identity(config)
    config_root = repository_root / "configs" / config
    requested_model_leaf = model_leaf(model)
    candidates = []
    if config_root.is_dir():
        for model_directory in config_root.iterdir():
            matches_model = (
                model_directory.name == requested_model_leaf
                or model_directory.name.startswith(f"{requested_model_leaf}+")
            )
            candidate = model_directory / thinking
            if matches_model and candidate.is_dir():
                candidates.append(candidate)
    candidates.sort()

    request = (
        f"config={config!r}, model_leaf={requested_model_leaf!r}, "
        f"thinking={thinking!r}"
    )
    if not candidates:
        raise ValueError(
            f"Config leaf missing: requested {request}; "
            f"config_root={str(config_root)!r}"
        )
    if len(candidates) > 1:
        rendered_candidates = [str(candidate) for candidate in candidates]
        raise ValueError(
            f"Config leaf ambiguous: requested {request}; "
            f"candidates={rendered_candidates!r}"
        )

    config_leaf = candidates[0]
    leaf_smoke_contract = config_leaf / "smoke.json"
    root_smoke_contract = config_root / "smoke.json"
    if leaf_smoke_contract.is_file():
        smoke_contract = leaf_smoke_contract
    elif root_smoke_contract.is_file():
        smoke_contract = root_smoke_contract
    else:
        smoke_contract = None
    return ResolvedConfigLeaf(
        config_root=config_root,
        config_leaf=config_leaf,
        smoke_contract=smoke_contract,
    )

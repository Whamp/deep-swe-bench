"""Resolve one config root, model+thinking leaf, and smoke contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    from harness.lib import model_leaf
except ModuleNotFoundError:
    # Direct harness script execution adds harness/ to sys.path.
    from lib import model_leaf


@dataclass(frozen=True, slots=True)
class ResolvedConfigLeaf:
    """The exact config files selected for one model and thinking level."""

    config_root: Path
    config_leaf: Path
    smoke_contract: Path | None


def resolve_config_leaf(
    repository_root: Path,
    config: str,
    model: str,
    thinking: str,
) -> ResolvedConfigLeaf:
    """Resolve exactly one config leaf or raise a searchable request error."""
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
        f"config={config!r}, model_leaf={requested_model_leaf!r}, thinking={thinking!r}"
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

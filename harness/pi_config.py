"""Read and validate config-owned Pi command-line arguments."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path, PurePosixPath

_RPC_OWNED_PI_FLAGS = frozenset(
    {
        "-p",
        "--append-system-prompt",
        "--mode",
        "--model",
        "--print",
        "--session-dir",
        "--thinking",
    }
)
_RPC_OWNED_PI_FLAG_PREFIXES = tuple(
    f"{flag}=" for flag in _RPC_OWNED_PI_FLAGS if flag.startswith("--")
)
_EXTENSION_FLAGS = frozenset({"-e", "--extension"})
_EXTENSION_FLAG_PREFIX = "--extension="
_CONTAINER_CONFIG_ROOT = PurePosixPath("/arm")


def read_config_pi_flags(config_root: Path) -> list[str]:
    """Read one Pi argv item per active line from a config release."""
    flags_path = config_root / "pi-flags"
    if not flags_path.is_file():
        return []
    return [
        line
        for raw_line in flags_path.read_text().splitlines()
        if (line := raw_line.strip()) and not line.startswith("#")
    ]


def validate_pi_flags(flags: Sequence[str]) -> None:
    """Reject config arguments owned by the confirmed RPC runner."""
    for flag in flags:
        if flag in _RPC_OWNED_PI_FLAGS or flag.startswith(
            _RPC_OWNED_PI_FLAG_PREFIXES
        ):
            raise ValueError(
                "Pi launch flag invalid: config pi-flags may not override "
                f"RPC runner control flag: {flag}"
            )


def _extension_targets(flags: Sequence[str]) -> list[str]:
    targets: list[str] = []
    index = 0
    while index < len(flags):
        flag = flags[index]
        if flag in _EXTENSION_FLAGS:
            if index + 1 >= len(flags):
                raise ValueError(
                    "Pi launch flag invalid: extension flag "
                    f"{flag!r} has no target"
                )
            targets.append(flags[index + 1])
            index += 2
            continue
        if flag.startswith(_EXTENSION_FLAG_PREFIX):
            targets.append(flag.removeprefix(_EXTENSION_FLAG_PREFIX))
        index += 1
    return targets


def _host_extension_path(config_root: Path, target: str) -> Path:
    container_path = PurePosixPath(target)
    try:
        relative_path = container_path.relative_to(_CONTAINER_CONFIG_ROOT)
    except ValueError as error:
        raise ValueError(
            "Pi launch flag invalid: extension target must be config-owned "
            f"under /arm; target={target!r}"
        ) from error
    if not relative_path.parts or ".." in relative_path.parts:
        raise ValueError(
            "Pi launch flag invalid: extension target must name a file or "
            f"directory under /arm; target={target!r}"
        )
    return config_root.joinpath(*relative_path.parts)


def validate_pi_config(config_root: Path) -> list[str]:
    """Validate Pi flags and every config-owned extension target."""
    flags = read_config_pi_flags(config_root)
    validate_pi_flags(flags)
    for target in _extension_targets(flags):
        host_path = _host_extension_path(config_root, target)
        if not host_path.exists():
            raise ValueError(
                "Pi launch flag invalid: extension target does not exist; "
                f"target={target!r}; host_path={str(host_path)!r}"
            )
    return flags

import json
from pathlib import Path

from harness.pi_config import read_config_pi_flags


def test_versioned_pi_extension_configs_have_explicit_extension_targets() -> None:
    """Maintained Pi extension configs load at least one target despite disabled discovery."""
    repository_root = Path(__file__).resolve().parents[1]
    checked_config_roots: set[Path] = set()

    for lock_path in repository_root.glob("configs/*/*/*/config-lock.json"):
        lock = json.loads(lock_path.read_text())
        if "pi-extensions" not in lock.get("requiredCapabilities", []):
            continue

        config_root = lock_path.parents[2]
        if config_root in checked_config_roots:
            continue
        checked_config_roots.add(config_root)

        flags = read_config_pi_flags(config_root)
        has_explicit_extension_target = any(
            flag in {"-e", "--extension"} or flag.startswith("--extension=")
            for flag in flags
        )
        assert has_explicit_extension_target, (
            f"{lock['configIdentity']} declares pi-extensions but pi-flags has no "
            "explicit -e/--extension target"
        )

    assert checked_config_roots

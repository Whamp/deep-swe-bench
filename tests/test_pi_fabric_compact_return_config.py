from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
CONTROL_CONFIG = "pi-fabric-output-telemetry@1.0.0"
TREATMENT_CONFIG = "pi-fabric-compact-return@1.0.0"
TELEMETRY_KIND = "pi-fabric.output-telemetry.v1"
GUIDANCE_MARKER = "pi_fabric.compact_return.v1"


def config_root(name: str) -> Path:
    return REPOSITORY / "configs" / name


def copy_pi_fabric_fixture(target: Path) -> None:
    fixture = REPOSITORY / "tests/fixtures/pi-fabric-0284"
    for source in fixture.rglob("*"):
        if source.is_file():
            destination = target / source.relative_to(fixture)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)


def apply_config_patch(config: str, package_root: Path) -> None:
    package = json.loads((config_root(config) / "extensions/package.json").read_text())
    postinstall = package["scripts"]["postinstall"].split()
    subprocess.run(
        [
            postinstall[0],
            str(config_root(config) / "extensions" / postinstall[1]),
            str(package_root),
        ],
        check=True,
    )


def test_configs_pin_same_fabric_and_do_not_append_system_prompt() -> None:
    for name in (CONTROL_CONFIG, TREATMENT_CONFIG):
        root = config_root(name)
        package = json.loads((root / "extensions/package.json").read_text())

        assert package["dependencies"]["pi-fabric"] == "0.28.4"
        assert not (root / "system_preamble.md").exists()
        assert not (root / "orchestration.md").exists()
        assert "--append-system-prompt" not in (root / "pi-flags").read_text()


def test_control_adds_metadata_telemetry_without_model_visible_guidance(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "control" / "pi-fabric"
    copy_pi_fabric_fixture(package_root)

    apply_config_patch(CONTROL_CONFIG, package_root)

    runtime = "\n".join(
        (package_root / relative).read_text()
        for relative in (
            "dist/core/action-registry.js",
            "dist/audit/details.js",
            "dist/fabric-exec-tool.js",
        )
    )
    model_surfaces = "\n".join(
        (package_root / relative).read_text()
        for relative in (
            "dist/fabric-exec-tool.js",
            "dist/index.js",
            "skills/fabric-exec/SKILL.md",
        )
    )

    assert TELEMETRY_KIND in runtime
    assert "nestedRawResultChars" in runtime
    assert "nestedRawResultBytes" in runtime
    assert "nestedSandboxResultChars" in runtime
    assert "nestedSandboxResultBytes" in runtime
    assert "returnedTextChars" in runtime
    assert "returnedTextBytes" in runtime
    assert GUIDANCE_MARKER not in model_surfaces


def test_treatment_adds_same_telemetry_and_compact_return_guidance(
    tmp_path: Path,
) -> None:
    package_root = tmp_path / "treatment" / "pi-fabric"
    copy_pi_fabric_fixture(package_root)

    apply_config_patch(TREATMENT_CONFIG, package_root)
    subprocess.run(
        ["node", "--check", str(package_root / "dist/index.js")],
        check=True,
    )

    runtime = "\n".join(
        (package_root / relative).read_text()
        for relative in (
            "dist/core/action-registry.js",
            "dist/audit/details.js",
            "dist/fabric-exec-tool.js",
        )
    )
    model_surfaces = "\n".join(
        (package_root / relative).read_text()
        for relative in (
            "dist/fabric-exec-tool.js",
            "dist/index.js",
            "skills/fabric-exec/SKILL.md",
        )
    )

    assert TELEMETRY_KIND in runtime
    assert GUIDANCE_MARKER in model_surfaces
    assert "loops, branches, retries" in model_surfaces
    assert "Promise.all" in model_surfaces
    assert "Keep intermediate tool results inside the sandbox" in model_surfaces
    assert "not raw files, broad search dumps, or full command logs" in model_surfaces
    assert "search results before choosing read ranges" not in model_surfaces

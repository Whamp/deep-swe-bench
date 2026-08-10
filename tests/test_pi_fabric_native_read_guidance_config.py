import json
import subprocess
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
CONFIG_NAME = "pi-fabric-native-read-guidance@1.0.0"
NATIVE_READ_GUIDANCE = (
    "Read the contents of a file. Supports text files and images "
    "(jpg, png, gif, webp, bmp). Images are sent as attachments. For text "
    "files, output is truncated to 2000 lines or 50KB (whichever is hit "
    "first). Use offset/limit for large files. When you need the full file, "
    "continue with offset until complete."
)


def config_root() -> Path:
    return REPOSITORY / "configs" / CONFIG_NAME


def test_config_uses_pi_fabric_0284_without_prompt_append() -> None:
    root = config_root()
    package = json.loads((root / "extensions" / "package.json").read_text())

    assert package["dependencies"]["pi-fabric"] == "0.28.4"
    assert not (root / "system_preamble.md").exists()
    assert not (root / "orchestration.md").exists()
    assert "--append-system-prompt" not in (root / "pi-flags").read_text()


def test_patch_adds_native_read_guidance_to_every_fabric_surface(
    tmp_path: Path,
) -> None:
    root = config_root()
    package_root = tmp_path / "pi-fabric"
    (package_root / "dist").mkdir(parents=True)
    (package_root / "skills" / "fabric-exec").mkdir(parents=True)

    fixture_root = REPOSITORY / "tests" / "fixtures" / "pi-fabric-0284"
    for relative_path in (
        "dist/fabric-exec-tool.js",
        "dist/index.js",
        "skills/fabric-exec/SKILL.md",
    ):
        target = package_root / relative_path
        target.write_text((fixture_root / relative_path).read_text())

    subprocess.run(
        [
            "node",
            str(root / "extensions" / "apply-native-read-guidance.mjs"),
            str(package_root),
        ],
        check=True,
    )

    tool_source = (package_root / "dist" / "fabric-exec-tool.js").read_text()
    hook_source = (package_root / "dist" / "index.js").read_text()
    skill_source = (package_root / "skills" / "fabric-exec" / "SKILL.md").read_text()

    assert NATIVE_READ_GUIDANCE in tool_source
    assert NATIVE_READ_GUIDANCE in hook_source
    assert NATIVE_READ_GUIDANCE in skill_source
    assert "observe search results before choosing read ranges" in tool_source
    assert "pi.read({path:'/x', offset:1, limit:200})" in hook_source
    assert "pi.read('/x')" not in hook_source

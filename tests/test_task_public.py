"""Tests for agent-visible /task materialization across task layouts."""

from __future__ import annotations

import stat

import pytest

from harness.lib import load_task, materialize_task_public

_TASK_TOML = """
[metadata]
base_commit_hash = "abc123"
language = "python"

[agent]
timeout_sec = 60.0

[verifier]
timeout_sec = 120.0

[environment]
docker_image = "example/env:latest"

[[verifier.collect]]
command = "cd /app && git diff --binary abc123 HEAD > /logs/artifacts/model.patch"
timeout_sec = 300.0

[[verifier.collect]]
command = "cp /app/EXTRA.md /logs/artifacts/extra.md"
"""

_TASK_TOML_NO_COLLECT = _TASK_TOML.split("[[verifier.collect]]")[0]


def _make_task(tmp_path, *, legacy_script: bool, with_collect: bool = True):
    task_dir = tmp_path / "some-task"
    task_dir.mkdir()
    (task_dir / "instruction.md").write_text("do the thing\n")
    toml = _TASK_TOML if with_collect else _TASK_TOML_NO_COLLECT
    (task_dir / "task.toml").write_text(toml)
    if legacy_script:
        (task_dir / "pre_artifacts.sh").write_text("#!/bin/bash\necho legacy\n")
    return load_task("some-task", root=tmp_path), tmp_path / "public"


def test_legacy_pre_artifacts_file_is_preferred(tmp_path):
    task, public = _make_task(tmp_path, legacy_script=True)

    materialize_task_public(task, public)

    assert (public / "instruction.md").read_text() == "do the thing\n"
    assert (public / "pre_artifacts.sh").read_text() == "#!/bin/bash\necho legacy\n"


def test_collect_commands_are_synthesized_when_legacy_script_absent(tmp_path):
    task, public = _make_task(tmp_path, legacy_script=False)

    materialize_task_public(task, public)

    script = (public / "pre_artifacts.sh").read_text()
    assert script.startswith("#!/bin/bash\n")
    assert "git diff --binary abc123 HEAD > /logs/artifacts/model.patch" in script
    assert "cp /app/EXTRA.md /logs/artifacts/extra.md" in script
    assert script.index("git diff") < script.index("cp /app/EXTRA.md")
    assert stat.S_IMODE((public / "pre_artifacts.sh").stat().st_mode) & 0o111


def test_missing_capture_contract_fails_closed(tmp_path):
    task, public = _make_task(tmp_path, legacy_script=False, with_collect=False)

    with pytest.raises(FileNotFoundError, match="pre_artifacts"):
        materialize_task_public(task, public)

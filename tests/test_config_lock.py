"""Behavior tests for versioned config locks through launch-facing seams."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from hypothesis import given
from hypothesis import strategies as st

from harness import config_lock, config_resolution, run_batch
from harness import run as run_subject


def _preflight_args() -> SimpleNamespace:
    return SimpleNamespace(
        model="provider/model",
        thinking="low",
        no_smoke_new_configs=False,
    )


def _write_config_lock(
    repository_root: Path,
    config_identity: str,
    metadata_path: Path,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "harness.config_lock",
            "create",
            "--repository",
            str(repository_root),
            "--config",
            config_identity,
            "--model",
            "provider/model",
            "--thinking",
            "low",
            "--state-root",
            str(repository_root / "results" / "_runs"),
            "--version-impact",
            "rerun",
            "--metadata",
            str(metadata_path),
        ],
        check=False,
        capture_output=True,
        text=True,
    )


@given(
    st.dictionaries(
        st.text(min_size=1, max_size=12),
        st.one_of(
            st.none(),
            st.booleans(),
            st.integers(),
            st.text(max_size=24),
            st.lists(st.integers(), max_size=5),
        ),
        max_size=8,
    )
)
def test_canonical_config_lock_serialization_round_trips(
    document: dict[str, object],
) -> None:
    """Canonical lock serialization preserves every JSON value exactly."""
    serialized = config_lock.canonical_config_lock_json(document)

    assert config_lock.parse_config_lock_json(serialized) == document


@given(
    st.text(
        alphabet=st.characters(min_codepoint=97, max_codepoint=122), min_size=1
    )
)
def test_config_lock_excludes_secret_values_from_identity(
    secret_suffix: str,
) -> None:
    """Changing secret values neither exposes nor changes the reviewed lock."""
    with tempfile.TemporaryDirectory() as directory:
        repository_root = Path(directory)
        config_identity = "review-assistant@1.0.0"
        config_leaf = (
            repository_root / "configs" / config_identity / "model" / "low"
        )
        config_leaf.mkdir(parents=True)
        env_path = config_leaf.parent.parent / "env"
        models_path = config_leaf / "models.json"
        first_secret = f"first-secret-{secret_suffix}"
        second_secret = f"second-secret-{secret_suffix}"
        env_path.write_text(
            "FEATURE_MODE=review\n"
            f"OPENAI_API_KEY={first_secret}\n"
            f"SESSION_COOKIE={first_secret}\n"
            f"GITHUB_PAT={first_secret}\n"
            f"INTERNAL_AUTH={first_secret}\n"
            f"CUSTOM_KEY={first_secret}\n"
        )
        models_path.write_text(
            json.dumps(
                {
                    "providers": {
                        "example": {
                            "apiKey": first_secret,
                            "authToken": "$ZAI_API_KEY",
                        }
                    }
                }
            )
        )
        resolved = config_resolution.resolve_config_leaf(
            repository_root,
            config_identity,
            "provider/model",
            "low",
        )
        metadata = {
            "credentialRoutes": ["OPENAI_API_KEY", "ZAI_API_KEY"],
            "declaredRoles": [{"name": "executor", "apiKey": first_secret}],
        }
        first_lock = config_lock.build_config_lock_document(
            resolved,
            config_identity,
            "rerun",
            metadata,
        )

        env_path.write_text(
            "FEATURE_MODE=review\n"
            f"OPENAI_API_KEY={second_secret}\n"
            f"SESSION_COOKIE={second_secret}\n"
            f"GITHUB_PAT={second_secret}\n"
            f"INTERNAL_AUTH={second_secret}\n"
            f"CUSTOM_KEY={second_secret}\n"
        )
        models_path.write_text(
            json.dumps(
                {
                    "providers": {
                        "example": {
                            "apiKey": second_secret,
                            "authToken": "$ZAI_API_KEY",
                        }
                    }
                }
            )
        )
        metadata["declaredRoles"] = [
            {"name": "executor", "apiKey": second_secret}
        ]
        second_lock = config_lock.build_config_lock_document(
            resolved,
            config_identity,
            "rerun",
            metadata,
        )

        serialized_locks = config_lock.canonical_config_lock_json(
            {"first": first_lock, "second": second_lock}
        )
        assert first_secret not in serialized_locks
        assert second_secret not in serialized_locks
        assert "OPENAI_API_KEY" in serialized_locks
        assert "ZAI_API_KEY" in serialized_locks
        assert first_lock["lockIdentity"] == second_lock["lockIdentity"]


@given(
    st.dictionaries(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=8,
        ),
        st.integers(),
        max_size=8,
    ),
    st.lists(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=8,
        ),
        unique=True,
        max_size=8,
    ),
)
def test_config_lock_identity_ignores_nonbehavioral_ordering(
    settings: dict[str, int],
    capabilities: list[str],
) -> None:
    """JSON key and declaration order cannot change aggregate lock identity."""
    with tempfile.TemporaryDirectory() as directory:
        repository_root = Path(directory)
        config_identity = "review-assistant@1.0.0"
        config_leaf = (
            repository_root / "configs" / config_identity / "model" / "low"
        )
        config_leaf.mkdir(parents=True)
        settings_path = config_leaf / "settings.json"
        settings_path.write_text(json.dumps(settings))
        resolved = config_resolution.resolve_config_leaf(
            repository_root,
            config_identity,
            "provider/model",
            "low",
        )
        first_lock = config_lock.build_config_lock_document(
            resolved,
            config_identity,
            "rerun",
            {"requiredCapabilities": capabilities},
        )

        settings_path.write_text(json.dumps(dict(reversed(settings.items()))))
        second_lock = config_lock.build_config_lock_document(
            resolved,
            config_identity,
            "rerun",
            {"requiredCapabilities": list(reversed(capabilities))},
        )

        assert first_lock["lockIdentity"] == second_lock["lockIdentity"]


def test_pi_subject_cli_loads_config_lock_verifier_without_execution() -> None:
    """The direct Pi runner CLI can load the lock verifier and show help."""
    repository_root = Path(__file__).resolve().parents[1]

    completed = subprocess.run(
        [sys.executable, str(repository_root / "harness" / "run.py"), "--help"],
        cwd=repository_root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "--config" in completed.stdout


def test_config_maintainer_creates_lock_consumed_by_preflight_plan(
    tmp_path: Path,
) -> None:
    """One explicit operation locks every reviewed behavior-input category."""
    config_identity = "review-assistant@1.2.3"
    config_root = tmp_path / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    (config_root / "skills" / "review").mkdir(parents=True)
    (config_root / "extensions").mkdir()
    (config_root / "bin").mkdir()
    config_leaf.mkdir(parents=True)
    (config_root / "orchestration.md").write_text("Reviewed prompt.\n")
    (config_root / "pi-flags").write_text(
        "--extension\n/arm/extensions/index.ts\n"
    )
    (config_root / "env").write_text("FEATURE_MODE=review\n")
    (config_root / "skills" / "review" / "SKILL.md").write_text("# Review\n")
    (config_root / "extensions" / "index.ts").write_text("export {};\n")
    (config_root / "extensions" / "package-lock.json").write_text("{}\n")
    (config_root / "bin" / "generated-tool").write_bytes(b"tool-v1")
    (config_leaf / "settings.json").write_text(
        '{"defaultThinkingLevel":"low"}\n'
    )
    (config_leaf / "smoke.json").write_text('{"requireFiles":[]}\n')
    metadata_path = tmp_path / "release-metadata.json"
    metadata_path.write_text(
        json.dumps(
            {
                "declaredRoles": [{"name": "executor"}],
                "launchSurfaces": [
                    {
                        "modelRoles": ["executor"],
                        "path": "extensions/index.ts",
                    }
                ],
                "usageSources": ["session/*.jsonl"],
                "requiredCapabilities": ["rpc"],
                "testedSubjectVersions": ["pi@0.50.0"],
            }
        )
    )

    completed = _write_config_lock(tmp_path, config_identity, metadata_path)

    assert completed.returncode == 0, completed.stderr
    lock_path = config_leaf / "config-lock.json"
    lock = json.loads(lock_path.read_text())
    assert lock["schemaVersion"] == 1
    assert lock["configIdentity"] == config_identity
    assert lock["configName"] == "review-assistant"
    assert lock["configVersion"] == "1.2.3"
    assert lock["versionImpact"] == "rerun"
    assert lock["leaf"] == {
        "model": "model",
        "path": "model/low",
        "thinking": "low",
    }
    assert lock["declaredRoles"] == [{"name": "executor"}]
    assert lock["launchSurfaces"] == [
        {"modelRoles": ["executor"], "path": "extensions/index.ts"}
    ]
    assert lock["usageSources"] == ["session/*.jsonl"]
    assert lock["requiredCapabilities"] == ["rpc"]
    assert lock["testedSubjectVersions"] == ["pi@0.50.0"]
    assert {item["path"] for item in lock["behaviorInputs"]} == {
        "bin/generated-tool",
        "env",
        "extensions/index.ts",
        "extensions/package-lock.json",
        "model/low/settings.json",
        "model/low/smoke.json",
        "orchestration.md",
        "pi-flags",
        "skills/review/SKILL.md",
    }
    assert lock["lockIdentity"].startswith("sha256:")

    smoke_subset = tmp_path / "subsets" / "12_v0.txt"
    smoke_subset.parent.mkdir()
    smoke_subset.write_text("task-a\n")
    with (
        patch.object(run_batch, "REPO", tmp_path),
        patch.object(run_batch, "SMOKE_SUBSET", smoke_subset),
    ):
        plan = run_batch.preflight_plan(
            _preflight_args(),
            [config_identity],
            ["task-a"],
        )
        result_path = run_batch.result_path(
            "provider/model",
            "low",
            config_identity,
            "task-a",
            0,
        )

    assert plan[0]["config_lock_identity"] == lock["lockIdentity"]
    assert result_path == (
        tmp_path
        / "results"
        / "model"
        / "low"
        / config_identity
        / "task-a"
        / "rep0"
        / "result.json"
    )


def test_preflight_plan_rejects_versioned_config_without_creating_lock(
    tmp_path: Path,
) -> None:
    """Planning rejects a missing release lock and leaves the leaf untouched."""
    config_identity = "review-assistant@1.0.0"
    config_leaf = tmp_path / "configs" / config_identity / "model" / "low"
    config_leaf.mkdir(parents=True)
    smoke_subset = tmp_path / "subsets" / "12_v0.txt"
    smoke_subset.parent.mkdir()
    smoke_subset.write_text("task-a\n")

    with (
        patch.object(run_batch, "REPO", tmp_path),
        patch.object(run_batch, "SMOKE_SUBSET", smoke_subset),
        pytest.raises(ValueError, match="^Config lock missing:"),
    ):
        run_batch.preflight_plan(
            _preflight_args(),
            [config_identity],
            ["task-a"],
        )

    assert not (config_leaf / "config-lock.json").exists()


def test_preflight_plan_preserves_unversioned_config_without_fabricated_lock(
    tmp_path: Path,
) -> None:
    """Legacy configs remain readable and never receive fabricated locks."""
    config_leaf = tmp_path / "configs" / "legacy-config" / "model" / "low"
    config_leaf.mkdir(parents=True)
    smoke_subset = tmp_path / "subsets" / "12_v0.txt"
    smoke_subset.parent.mkdir()
    smoke_subset.write_text("task-a\n")

    with (
        patch.object(run_batch, "REPO", tmp_path),
        patch.object(run_batch, "SMOKE_SUBSET", smoke_subset),
    ):
        plan = run_batch.preflight_plan(
            _preflight_args(),
            ["legacy-config"],
            ["task-a"],
        )

    assert plan[0]["config_lock_identity"] is None
    assert not (config_leaf / "config-lock.json").exists()


def test_preflight_plan_reports_config_lock_input_mismatches(
    tmp_path: Path,
) -> None:
    """Launch planning identifies each added, removed, and changed input."""
    config_identity = "review-assistant@1.0.0"
    config_root = tmp_path / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    skill_path = config_root / "skills" / "review" / "SKILL.md"
    skill_path.parent.mkdir(parents=True)
    config_leaf.mkdir(parents=True)
    prompt_path = config_root / "orchestration.md"
    prompt_path.write_text("Original prompt.\n")
    skill_path.write_text("# Review\n")
    metadata_path = tmp_path / "release-metadata.json"
    metadata_path.write_text("{}\n")
    completed = _write_config_lock(tmp_path, config_identity, metadata_path)
    assert completed.returncode == 0, completed.stderr
    lock_path = config_leaf / "config-lock.json"
    original_lock = lock_path.read_bytes()

    prompt_path.write_text("Changed prompt.\n")
    skill_path.unlink()
    added_path = config_root / "extensions" / "new.ts"
    added_path.parent.mkdir()
    added_path.write_text("export {};\n")
    smoke_subset = tmp_path / "subsets" / "12_v0.txt"
    smoke_subset.parent.mkdir()
    smoke_subset.write_text("task-a\n")

    with (
        patch.object(run_batch, "REPO", tmp_path),
        patch.object(run_batch, "SMOKE_SUBSET", smoke_subset),
        pytest.raises(ValueError) as raised,
    ):
        run_batch.preflight_plan(
            _preflight_args(),
            [config_identity],
            ["task-a"],
        )

    message = str(raised.value)
    assert message.startswith("Config lock mismatch:")
    assert "added=['extensions/new.ts']" in message
    assert "removed=['skills/review/SKILL.md']" in message
    assert "changed=['orchestration.md']" in message
    assert lock_path.read_bytes() == original_lock


def test_non_secret_token_setting_change_invalidates_config_lock(
    tmp_path: Path,
) -> None:
    """Token-limit settings remain behavior inputs rather than secret values."""
    config_identity = "review-assistant@1.0.0"
    config_leaf = tmp_path / "configs" / config_identity / "model" / "low"
    config_leaf.mkdir(parents=True)
    settings_path = config_leaf / "settings.json"
    settings_path.write_text('{"maxOutputToken":100}\n')
    metadata_path = tmp_path / "release-metadata.json"
    metadata_path.write_text("{}\n")
    completed = _write_config_lock(tmp_path, config_identity, metadata_path)
    assert completed.returncode == 0, completed.stderr
    settings_path.write_text('{"maxOutputToken":200}\n')

    with pytest.raises(
        ValueError, match="changed=\\['model/low/settings.json'\\]"
    ):
        run_subject.load_config(
            config_identity,
            "provider/model",
            "low",
            repository_root=tmp_path,
        )


def test_config_lock_refresh_rejects_unreadable_seal_evidence(
    tmp_path: Path,
) -> None:
    """Unreadable result evidence cannot make a release appear revisable."""
    config_identity = "review-assistant@1.0.0"
    config_root = tmp_path / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    config_leaf.mkdir(parents=True)
    prompt_path = config_root / "orchestration.md"
    prompt_path.write_text("Original behavior.\n")
    results_root = tmp_path / "other-results"
    state_root = tmp_path / "central-state"
    config_lock.write_config_lock(
        tmp_path,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {},
        state_root=state_root,
    )
    result_path = (
        results_root
        / "model"
        / "low"
        / config_identity
        / "task-a"
        / "rep0"
        / "result.json"
    )
    result_path.parent.mkdir(parents=True)
    result_path.write_text("{not-json\n")
    prompt_path.write_text("Changed behavior.\n")

    with pytest.raises(
        ValueError,
        match=r"^Config release seal evidence invalid:",
    ) as raised:
        config_lock.write_config_lock(
            tmp_path,
            config_identity,
            "provider/model",
            "low",
            "rerun",
            {},
            state_root=state_root,
            replace=True,
            results_root=results_root,
        )

    assert str(result_path) in str(raised.value)
    assert isinstance(raised.value.__cause__, json.JSONDecodeError)


def test_subject_config_loading_rejects_drift_without_refreshing_lock(
    tmp_path: Path,
) -> None:
    """Subject execution cannot accept drift or refresh its config lock."""
    config_identity = "review-assistant@1.0.0"
    config_leaf = tmp_path / "configs" / config_identity / "model" / "low"
    config_leaf.mkdir(parents=True)
    settings_path = config_leaf / "settings.json"
    settings_path.write_text('{"defaultThinkingLevel":"low"}\n')
    metadata_path = tmp_path / "release-metadata.json"
    metadata_path.write_text("{}\n")
    completed = _write_config_lock(tmp_path, config_identity, metadata_path)
    assert completed.returncode == 0, completed.stderr
    lock_path = config_leaf / "config-lock.json"
    original_lock = lock_path.read_bytes()
    settings_path.write_text('{"defaultThinkingLevel":"medium"}\n')

    with pytest.raises(ValueError, match="^Config lock mismatch:"):
        run_subject.load_config(
            config_identity,
            "provider/model",
            "low",
            repository_root=tmp_path,
        )

    assert lock_path.read_bytes() == original_lock


@pytest.mark.parametrize(
    "config_identity",
    ["", "config/other", "config,other", "config\0other"],
)
def test_config_resolution_rejects_unsafe_legacy_identity_segments(
    tmp_path: Path,
    config_identity: str,
) -> None:
    """The public resolver rejects unsafe identities before path lookup."""
    with pytest.raises(ValueError, match="^Config identity invalid:"):
        config_resolution.resolve_config_leaf(
            tmp_path,
            config_identity,
            "provider/model",
            "low",
        )


@pytest.mark.parametrize(
    "config_identity",
    [
        "@1.0.0",
        "config@",
        "config@@1.0.0",
        "config@1.0.0/other",
        "config@1.0.0,other",
        "config-v2@1.0.0",
        "config-new@1.0.0",
        "config-latest@1.0.0",
    ],
)
def test_preflight_plan_rejects_invalid_versioned_config_identity(
    tmp_path: Path,
    config_identity: str,
) -> None:
    """Malformed or vague release identities fail before launch planning."""
    config_leaf = tmp_path / "configs" / config_identity / "model" / "low"
    config_leaf.mkdir(parents=True)
    smoke_subset = tmp_path / "subsets" / "12_v0.txt"
    smoke_subset.parent.mkdir()
    smoke_subset.write_text("task-a\n")

    with (
        patch.object(run_batch, "REPO", tmp_path),
        patch.object(run_batch, "SMOKE_SUBSET", smoke_subset),
        pytest.raises(ValueError, match="^Config identity invalid:"),
    ):
        run_batch.preflight_plan(
            _preflight_args(),
            [config_identity],
            ["task-a"],
        )

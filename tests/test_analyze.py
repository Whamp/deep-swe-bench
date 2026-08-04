"""Tests for harness/analyze.py results reading (ticket #4).

Proves the reader migrates onto harness/results_tree.py: load_results routes
through lib.REPO (via Tree.of) instead of a baked-in module-local repo root,
and the glob-lexicographic -> rep-as-int ordering change is semantically
irrelevant to the comparison output (rep10 is present to stress it).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness import analyze, lib

# A model whose leaf does not exist in the real results tree, so the reader is
# forced to read the tmp tree we build (proving it reads via lib.REPO, not a
# baked-in root). lib.model_leaf(MODEL) == LEAF.
MODEL = "test-vendor/synth-analyze-v1"
LEAF = "synth-analyze-v1"


def _write_result(
    tree_root: Path,
    config: str,
    rep: int,
    reward_partial: float,
    tokens: int,
) -> None:
    _write_task_result(
        tree_root,
        config,
        rep,
        reward_partial,
        tokens,
        task="t1",
        task_revision="sha256:task-fixture",
    )


def _write_task_result(
    tree_root: Path,
    config: str,
    rep: int,
    reward_partial: float,
    tokens: int,
    *,
    task: str,
    task_revision: str,
) -> None:
    cell = (
        tree_root
        / "results"
        / LEAF
        / "high"
        / config
        / task
        / f"rep{rep}"
    )
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "result.json").write_text(
        json.dumps(
            {
                "config": config,
                "config_lock_identity": f"sha256:lock-{config}",
                "subject": "pi",
                "subject_version": "pi@fixture",
                "model": MODEL,
                "thinking_level": "high",
                "task": task,
                "rep": rep,
                "harness_revision": "sha256:harness-fixture",
                "task_revision": task_revision,
                "verifier_identity": f"sha256:verifier-{task}",
                "immutable_image_identities": {
                    "agent": f"sha256:agent-{task}",
                    "environment": f"sha256:environment-{task}",
                    "verifier": f"sha256:verifier-image-{task}",
                },
                "launch_plan_identity": f"sha256:plan-{config}-{rep}",
                "reward_partial": reward_partial,
                "reward_binary": 0,
                "total_tokens": tokens,
                "cost_usd": tokens * 0.00001,
                "agent_timed_out": False,
            }
        )
    )


@pytest.fixture
def synth_tree(tmp_path: Path) -> Path:
    """tmp results tree: 2 configs x t1 x reps {0,2,10} (rep10 stresses ordering)."""
    for rep, partial in [(0, 0.10), (2, 0.20), (10, 0.30)]:
        _write_result(tmp_path, "baseline", rep, partial, tokens=100 * (rep + 1))
    for rep, partial in [(0, 0.40), (2, 0.50), (10, 0.60)]:
        _write_result(tmp_path, "alt", rep, partial, tokens=400 * (rep + 1))
    return tmp_path


def test_load_results_reads_via_results_tree_module(monkeypatch, synth_tree):
    # Redirect the canonical repo root to the tmp tree. Only takes effect once
    # load_results routes through lib.REPO (via Tree.of) — i.e. after the #4
    # migrate. On pre-migrate code (module-local REPO) this returns [] and fails.
    monkeypatch.setattr(lib, "REPO", synth_tree)

    rows = analyze.load_results(MODEL, "high", ["baseline", "alt"])

    assert len(rows) == 6
    by_key = {(r["config"], r["rep"]): r["reward_partial"] for r in rows}
    assert by_key == {
        ("baseline", 0): 0.10,
        ("baseline", 2): 0.20,
        ("baseline", 10): 0.30,
        ("alt", 0): 0.40,
        ("alt", 2): 0.50,
        ("alt", 10): 0.60,
    }


def test_load_results_accepts_task_specific_revisions(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Subset expansion may retain a different compatible revision per task."""
    for config in ("baseline", "alt"):
        _write_task_result(
            tmp_path,
            config,
            0,
            0.5,
            100,
            task="t1",
            task_revision="sha256:nested-subset",
        )
        _write_task_result(
            tmp_path,
            config,
            0,
            0.5,
            100,
            task="t2",
            task_revision="sha256:expanded-subset",
        )
    monkeypatch.setattr(lib, "REPO", tmp_path)

    rows = analyze.load_results(MODEL, "high", ["baseline", "alt"])

    assert len(rows) == 4


def test_load_results_rejects_incompatible_selected_provenance(
    monkeypatch: pytest.MonkeyPatch,
    synth_tree: Path,
) -> None:
    """A comparison cannot aggregate reps from different harness setups."""
    incompatible_path = (
        synth_tree
        / "results"
        / LEAF
        / "high"
        / "alt"
        / "t1"
        / "rep2"
        / "result.json"
    )
    incompatible = json.loads(incompatible_path.read_text())
    incompatible["harness_revision"] = "sha256:other-harness"
    incompatible_path.write_text(json.dumps(incompatible))
    monkeypatch.setattr(lib, "REPO", synth_tree)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ) as raised:
        analyze.load_results(MODEL, "high", ["baseline", "alt"])

    assert str(incompatible_path) in str(raised.value)
    assert "harness_revision" in str(raised.value)


def test_load_results_rejects_mixed_resource_policies(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """A comparison cannot combine reps produced under different limits."""
    _write_result(tmp_path, "baseline@1.0.0", 0, 0.1, 100)
    _write_result(tmp_path, "other@1.0.0", 0, 0.2, 200)
    result_paths = sorted(tmp_path.glob("results/*/*/*/*/rep*/result.json"))
    for index, result_path in enumerate(result_paths):
        record = json.loads(result_path.read_text())
        record["resource_policy"] = {
            "additional_swap_gib": 0.0,
            "host_reserve_gib": 12.0,
            "subject_memory_gib": float(8 + index * 4),
            "verifier_memory_gib": 12.0,
        }
        result_path.write_text(json.dumps(record))
    monkeypatch.setattr(lib, "REPO", tmp_path)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ) as raised:
        analyze.load_results(
            MODEL,
            "high",
            ["baseline@1.0.0", "other@1.0.0"],
        )

    assert "resource_policy" in str(raised.value)


def test_load_results_rejects_mixed_omp_binary_identities(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """An OMP comparison cannot combine results from different binaries."""
    _write_result(tmp_path, "baseline@1.0.0", 0, 0.1, 100)
    _write_result(tmp_path, "other@1.0.0", 0, 0.2, 200)
    result_paths = sorted(tmp_path.glob("results/*/*/*/*/rep*/result.json"))
    for index, result_path in enumerate(result_paths):
        record = json.loads(result_path.read_text())
        record.update(
            {
                "subject": "omp",
                "subject_runtime_identity": {
                    "binaryFingerprint": f"sha256:omp-binary-{index}",
                    "binaryPath": "/fixture/bin/omp",
                    "versionOutput": "omp 16.3.5",
                },
                "subject_version": "omp@16.3.5",
            }
        )
        result_path.write_text(json.dumps(record))
    monkeypatch.setattr(lib, "REPO", tmp_path)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ) as raised:
        analyze.load_results(
            MODEL,
            "high",
            ["baseline@1.0.0", "other@1.0.0"],
        )

    assert "subject_runtime_identity" in str(raised.value)


def _remove_modern_result_provenance(result_path: Path) -> None:
    """Turn one fixture result into an honest pre-confirmed-launch record."""
    record = json.loads(result_path.read_text())
    for field in (
        "config_lock_identity",
        "harness_revision",
        "immutable_image_identities",
        "launch_plan_identity",
        "subject",
        "subject_version",
        "task_revision",
        "verifier_identity",
    ):
        record.pop(field)
    result_path.write_text(json.dumps(record))


def test_load_results_reads_legacy_corpus_only_after_explicit_decision(
    monkeypatch: pytest.MonkeyPatch,
    synth_tree: Path,
) -> None:
    """An explicit flag keeps an entirely legacy comparison readable."""
    for result_path in synth_tree.glob("results/*/*/*/*/rep*/result.json"):
        _remove_modern_result_provenance(result_path)
    monkeypatch.setattr(lib, "REPO", synth_tree)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ):
        analyze.load_results(MODEL, "high", ["baseline", "alt"])

    with pytest.warns(UserWarning, match="legacy result provenance accepted"):
        rows = analyze.load_results(
            MODEL,
            "high",
            ["baseline", "alt"],
            allow_legacy_results=True,
        )

    assert len(rows) == 6
    assert all("config_lock_identity" not in row for row in rows)


def test_load_results_rejects_mixed_modern_and_legacy_provenance(
    monkeypatch: pytest.MonkeyPatch,
    synth_tree: Path,
) -> None:
    """Legacy opt-in cannot silently mix provenanced and unknown setups."""
    legacy_path = (
        synth_tree
        / "results"
        / LEAF
        / "high"
        / "alt"
        / "t1"
        / "rep2"
        / "result.json"
    )
    _remove_modern_result_provenance(legacy_path)
    monkeypatch.setattr(lib, "REPO", synth_tree)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ) as raised:
        analyze.load_results(
            MODEL,
            "high",
            ["baseline", "alt"],
            allow_legacy_results=True,
        )

    assert "mixed modern and legacy" in str(raised.value)


def test_load_results_reports_corrupt_selected_result(
    monkeypatch: pytest.MonkeyPatch,
    synth_tree: Path,
) -> None:
    """Unreadable selected cells fail visibly instead of changing the sample."""
    corrupt_path = (
        synth_tree
        / "results"
        / LEAF
        / "high"
        / "alt"
        / "t1"
        / "rep2"
        / "result.json"
    )
    corrupt_path.write_text("{not-json\n")
    monkeypatch.setattr(lib, "REPO", synth_tree)

    with pytest.raises(
        ValueError,
        match=r"^Comparison result provenance mismatch:",
    ) as raised:
        analyze.load_results(MODEL, "high", ["baseline", "alt"])

    assert str(corrupt_path) in str(raised.value)
    assert isinstance(raised.value.__cause__, json.JSONDecodeError)


def test_load_results_preserves_distinct_versioned_config_identities(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Different config releases remain separate comparison identities."""
    _write_result(tmp_path, "baseline@1.0.0", 0, 0.1, 100)
    _write_result(tmp_path, "baseline@2.0.0", 0, 0.2, 200)
    monkeypatch.setattr(lib, "REPO", tmp_path)

    rows = analyze.load_results(
        MODEL,
        "high",
        ["baseline@1.0.0", "baseline@2.0.0"],
    )

    assert [row["config"] for row in rows] == [
        "baseline@1.0.0",
        "baseline@2.0.0",
    ]
    assert rows[0]["config_lock_identity"] != rows[1]["config_lock_identity"]


def test_main_output_with_rep10_is_correct_and_int_ordered(monkeypatch, synth_tree, capsys):
    monkeypatch.setattr(lib, "REPO", synth_tree)
    monkeypatch.setattr("sys.argv", [
        "analyze", "--model", MODEL, "--thinking", "high",
        "--comparison", "x", "--configs", "baseline,alt",
    ])

    analyze.main()
    out = capsys.readouterr().out

    # Config-summary mean_partial is order-independent (mean of the 3 reps,
    # formatted to 3dp the way analyze.fmt does). Independently computed:
    #   baseline mean(0.10,0.20,0.30) = 0.200
    #   alt      mean(0.40,0.50,0.60) = 0.500
    baseline_line = next(l for l in out.splitlines() if l.startswith("baseline,"))
    alt_line = next(l for l in out.splitlines() if l.startswith("alt,"))
    # line shape: config,n,mean_partial,...
    assert baseline_line.split(",")[2] == "0.200"
    assert alt_line.split(",")[2] == "0.500"

    # Per-task rows for t1 appear sorted by rep-as-int (0,2,10), NOT glob-lex
    # (0,10,2) — direct evidence that the rep-ordering change is semantically
    # irrelevant: the output uses int ordering regardless of the rows list order.
    t1_reps = [int(l.split(",")[1]) for l in out.splitlines() if l.startswith("t1,")]
    assert t1_reps == [0, 2, 10]

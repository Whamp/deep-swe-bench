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


def _write_result(tree_root: Path, config: str, rep: int,
                  reward_partial: float, tokens: int) -> None:
    cell = (tree_root / "results" / LEAF / "high" / config / "t1"
            / f"rep{rep}")
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "result.json").write_text(json.dumps({
        "config": config,
        "task": "t1",
        "rep": rep,
        "reward_partial": reward_partial,
        "reward_binary": 0,
        "total_tokens": tokens,
        "cost_usd": tokens * 0.00001,
        "agent_timed_out": False,
    }))


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

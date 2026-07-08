"""Property + concrete tests for harness/results_tree.py.

The results-tree address module is pure-address (no writes), so its interface
is the test surface. The load-bearing invariant is **path identity**: the module
must produce byte-identical paths to the grammar every caller hand-builds today
(`results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`), so that migrating
callers onto it cannot drift the resume-by-existence keys (ADR-0001).

Expected values come from independent sources of truth, never recomputed the way
the module does:
  - a concrete worked example lifted from tests/test_run_batch.py
    (`deepseek-v4-flash/high/cfg/task-a/rep0/result.json`), and
  - the inline leaf derivation `model.rstrip('/').split('/')[-1]`, cross-checked
    against `lib.model_leaf` to prove the three current derivations collapse.

Run fast during the loop:  HYPOTHESIS_PROFILE=dev pytest tests/test_results_tree.py -q
Final thorough run:         pytest tests/test_results_tree.py -q   (ci profile, 500)
"""
from __future__ import annotations

from pathlib import Path

from hypothesis import given, strategies as st

from harness import lib
from harness.results_tree import Tree, Cell

# Path-segment alphabet: letters, digits, -, _. No "/" (segments are single path
# parts), no "." / ".." edge cases.
_seg = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Nd"), whitelist_characters="-_"),
    min_size=1,
    max_size=12,
)
_model = st.lists(_seg, min_size=1, max_size=4).map("/".join)
_thinking = st.sampled_from(["off", "minimal", "low", "medium", "high", "xhigh"])
_rep = st.integers(min_value=0, max_value=30)


# --- Slice A: cell address (dir, result) + leaf equivalence -----------------


def test_cell_result_matches_existing_suite_literal(tmp_path):
    # Worked example from tests/test_run_batch.py — the independent source of
    # truth for the results-tree grammar.
    tree = Tree.of("openrouter/deepseek/deepseek-v4-flash", "high", repo=tmp_path)
    cell = tree.cell("cfg", "task-a", 0)
    assert cell.result == (
        tmp_path / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
    )
    assert cell.dir == (
        tmp_path / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0"
    )


@given(model=_model, thinking=_thinking, config=_seg, task=_seg, rep=_rep)
def test_cell_address_grammar_uses_inline_leaf(model, thinking, config, task, rep):
    # Expected path derived from the INLINE leaf (independent of the module's
    # choice to call lib.model_leaf). If the module used a different leaf or
    # grammar, this disagrees. Pure derivation — no filesystem, so a dummy repo
    # path is enough and avoids a function-scoped fixture inside @given.
    repo = Path("/__repo_dummy__")
    leaf = model.rstrip("/").split("/")[-1]
    expected_dir = repo / "results" / leaf / thinking / config / task / f"rep{rep}"
    cell = Tree.of(model, thinking, repo=repo).cell(config, task, rep)
    assert cell.dir == expected_dir
    assert cell.result == expected_dir / "result.json"


@given(model=_model)
def test_leaf_derivation_collapses_to_one(model):
    # The three current derivations must agree for the executor (one-arg) case,
    # and the module's cell address must use that same leaf.
    assert lib.model_leaf(model) == model.rstrip("/").split("/")[-1]
    repo = Path("/__repo_dummy__")
    cell = Tree.of(model, "high", repo=repo).cell("c", "t", 1)
    assert cell.dir == repo / "results" / lib.model_leaf(model) / "high" / "c" / "t" / "rep1"


# --- Slice B: canonical cell paths, has_result, tree-level paths, escape hatch -


@given(model=_model, thinking=_thinking, config=_seg, task=_seg, rep=_rep)
def test_cell_canonical_paths_match_grammar(model, thinking, config, task, rep):
    # Canonical files/subdirs derive from the cell dir with the names the
    # writers actually create (run.py: cell/transient_error.json, cell/artifacts,
    # cell/verifier, cell/logs, cell/session). Expected dir is inline-derived.
    repo = Path("/__repo_dummy__")
    leaf = model.rstrip("/").split("/")[-1]
    d = repo / "results" / leaf / thinking / config / task / f"rep{rep}"
    cell = Tree.of(model, thinking, repo=repo).cell(config, task, rep)
    assert cell.transient_error == d / "transient_error.json"
    assert cell.artifacts == d / "artifacts"
    assert cell.verifier == d / "verifier"
    assert cell.logs == d / "logs"
    assert cell.session == d / "session"


def test_cell_has_result_reflects_filesystem(tmp_path):
    # has_result() is the resume existence check; it must track result.json.
    tree = Tree.of("openrouter/deepseek/deepseek-v4-flash", "high", repo=tmp_path)
    cell = tree.cell("cfg", "task-a", 0)
    assert not cell.has_result()
    cell.dir.mkdir(parents=True)
    cell.result.write_text("{}")
    assert cell.has_result()


@given(model=_model, thinking=_thinking, config=_seg, task=_seg, rep=_rep)
def test_tree_level_paths(model, thinking, config, task, rep):
    # Tree-level: root (escape hatch), results.jsonl (run.py:647), and the
    # per-cell flat log under <thinking>/logs/ (run_batch.py log_path).
    repo = Path("/__repo_dummy__")
    leaf = model.rstrip("/").split("/")[-1]
    tree = Tree.of(model, thinking, repo=repo)
    assert tree.root == repo / "results" / leaf / thinking
    assert tree.results_jsonl == repo / "results" / leaf / thinking / "results.jsonl"
    assert tree.log_file(config, task, rep) == (
        repo / "results" / leaf / thinking / "logs" / f"{task}__{config}__rep{rep}.log"
    )


def test_escape_hatch_reaches_non_canonical_files(tmp_path):
    # dir / root are exposed so callers reach files the module does NOT name
    # (tool-usage.jsonl today; a future comparison manifest) without a module
    # edit — the closed-canonical / open-escape-hatch split.
    tree = Tree.of("a/b/c", "high", repo=tmp_path)
    cell = tree.cell("cfg", "t", 2)
    assert cell.dir / "tool-usage.jsonl" == (
        tmp_path / "results" / "c" / "high" / "cfg" / "t" / "rep2" / "tool-usage.jsonl"
    )
    assert tree.root / "comparisons" / "c1" / "manifest.json" == (
        tmp_path / "results" / "c" / "high" / "comparisons" / "c1" / "manifest.json"
    )


# --- Slice C: existence + iteration (has_results, cells, rep-as-int order) ----


def test_has_results_reflects_filesystem(tmp_path):
    # config-level existence (the resume gate): True iff some result.json lives
    # under root/config/*/rep*/. Mirrors run_batch.config_has_results.
    tree = Tree.of("openrouter/deepseek/deepseek-v4-flash", "high", repo=tmp_path)
    assert not tree.has_results("cfg")  # no config dir at all
    (tree.root / "cfg" / "t" / "rep0").mkdir(parents=True)
    assert not tree.has_results("cfg")  # dir exists but no result.json
    (tree.root / "cfg" / "t" / "rep0" / "result.json").write_text("{}")
    assert tree.has_results("cfg")
    assert not tree.has_results("other")


def test_cells_iterates_in_rep_as_int_order(tmp_path):
    # The fix: lexicographic glob orders rep10 before rep2; numeric order is
    # 1, 2, 10. cells() must yield rep-as-int order.
    tree = Tree.of("a/b/c", "high", repo=tmp_path)
    for rep in (2, 10, 1):
        d = tree.cell("cfg", "t", rep).dir
        d.mkdir(parents=True)
        (d / "result.json").write_text("{}")
    assert [c.rep for c in tree.cells()] == [1, 2, 10]


def test_cells_yield_carries_identity_and_paths(tmp_path):
    tree = Tree.of("a/b/c", "high", repo=tmp_path)
    for cfg, task, rep in [("cfg-a", "t1", 0), ("cfg-b", "t2", 3)]:
        c = tree.cell(cfg, task, rep)
        c.dir.mkdir(parents=True)
        c.result.write_text("{}")
    cells = list(tree.cells())
    assert [(c.config, c.task, c.rep) for c in cells] == [
        ("cfg-a", "t1", 0),
        ("cfg-b", "t2", 3),
    ]
    # each yielded Cell's result path round-trips through cell()
    assert cells[0].result == tree.cell("cfg-a", "t1", 0).result


def test_cells_filters_to_requested_configs(tmp_path):
    tree = Tree.of("a/b/c", "high", repo=tmp_path)
    for cfg in ("cfg-a", "cfg-b", "cfg-c"):
        c = tree.cell(cfg, "t", 0)
        c.dir.mkdir(parents=True)
        c.result.write_text("{}")
    assert [c.config for c in tree.cells(configs=["cfg-b"])] == ["cfg-b"]
    assert sorted(c.config for c in tree.cells(configs=["cfg-c", "cfg-a"])) == [
        "cfg-a",
        "cfg-c",
    ]


# --- Review fix: leaf is sealed + executor-only (not a bypassable field) ------


@given(model=_model)
def test_leaf_is_sealed_executor_only(model):
    # The leaf is sealed and executor-only: always lib.model_leaf(model), never
    # the +advisor configs-leaf form, regardless of how the Tree is made.
    # (ADR-0001: the results tree is executor-only.) leaf is a derived property,
    # not a stored field, so direct construction cannot inject one.
    tree = Tree.of(model, "high", repo=Path("/x"))
    assert tree.leaf == lib.model_leaf(model)
    assert "+" not in tree.leaf
    direct = Tree(model=model, thinking="high", repo=Path("/x"))
    assert direct.leaf == lib.model_leaf(model)

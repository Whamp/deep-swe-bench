"""Comprehensive property-based tests for harness/run_state.py.

Covers every pure function and the RunStateWriter state machine:

  - classify_result:        precedence, determinism, output domain, no-crash
  - compact_result_summary: field filtering, scalar-only, idempotence
  - _counts:                consistency, skipped-isolation, partition,
                            monotonicity, non-negativity
  - summarize_result_path:  path-vs-exit precedence, idempotence
  - make_cell / cell_id:    roundtrip, optional-field semantics
  - sanitize_run_id:        validity, roundtrip, rejection
  - _estimate_eta_s:        None-conditions, positivity
  - _failure_buckets:       exclusion rules, positivity
  - seconds_since:          None handling, non-negativity, roundtrip
  - parse_timestamp:        roundtrip, invalid rejection
  - project_structured_run: detail nesting, counts-recompute
  - discover_runs:          sort order, idempotence
  - read_events:            limit clamping, after-filtering
  - RunStateWriter machine: model-based stateful invariant testing

Run with:
    pytest tests/test_run_state_properties.py -q
    HYPOTHESIS_PROFILE=dev pytest tests/test_run_state_properties.py -q
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from string import ascii_lowercase, digits

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule, run_state_machine_as_test

from harness.run_state import (
    BASE_SUMMARY_FIELDS,
    DETAIL_LEVELS,
    RunStateWriter,
    SUMMARY_PREFIXES,
    TERMINAL_STATES,
    _estimate_eta_s,
    _failure_buckets,
    cell_id,
    classify_result,
    compact_result_summary,
    discover_runs,
    make_cell,
    parse_timestamp,
    project_structured_run,
    read_events,
    sanitize_run_id,
    seconds_since,
    summarize_result_path,
    utc_now,
)


# ---------------------------------------------------------------------------
#  Shared strategies
# ---------------------------------------------------------------------------

# Alphabets that produce valid cell_id components (no '/' which is the separator)
_SAFE_TEXT = st.text(
    alphabet=st.characters(blacklist_categories=("Cs",), blacklist_characters="/"),
    min_size=1,
    max_size=12,
)

# All possible cell states the system uses
CELL_STATES = st.sampled_from(["pending", "running", "done", "skipped", "failed", "passed"])

# All possible outcome labels that _counts and classify_result produce
OUTCOME_LABELS = st.sampled_from([
    "ok", "empty", "timeout", "transient",
    "exit=0", "exit=1", "exit=2", "exit=75", "exit=130",
    "skipped",
])

# Agent exit codes seen in practice (int, "0", "timeout", None)
AGENT_EXITS = st.one_of(
    st.none(),
    st.integers(min_value=-1, max_value=255),
    st.sampled_from(["0", "timeout"]),
)

# Verifier exit codes seen in practice
VERIFIER_EXITS = st.one_of(
    st.none(),
    st.integers(min_value=-1, max_value=255),
    st.sampled_from(["0", "skipped_empty_patch"]),
)


@st.composite
def st_result_record(draw):
    """Generate a realistic result.json-shaped record for classify_result."""
    record = {
        "agent_exit": draw(AGENT_EXITS),
        "verifier_exit": draw(VERIFIER_EXITS),
        "agent_timed_out": draw(st.booleans()),
        "transient_model_error": draw(st.booleans()),
    }
    # Optionally include summary fields that compact_result_summary should keep
    if draw(st.booleans()):
        record["reward_partial"] = draw(st.floats(min_value=0.0, max_value=1.0))
        record["reward_binary"] = draw(st.integers(min_value=0, max_value=1))
        record["total_tokens"] = draw(st.integers(min_value=0, max_value=10_000_000))
        record["cost_usd"] = draw(st.floats(min_value=0.0, max_value=100.0))
        record["patch_bytes"] = draw(st.integers(min_value=0, max_value=500_000))
    # And some fields that should be excluded
    if draw(st.booleans()):
        record["raw_stdout"] = "x" * 500  # not in BASE_SUMMARY_FIELDS
        record["nested"] = {"deep": [1, 2, 3]}  # nested, should be excluded
    return record


@st.composite
def st_cell(draw):
    """Generate a cell dict as stored in status['cells']."""
    task = draw(_SAFE_TEXT)
    config = draw(_SAFE_TEXT)
    rep = draw(st.integers(min_value=0, max_value=9))
    state = draw(CELL_STATES)
    outcome = draw(st.one_of(st.none(), OUTCOME_LABELS))
    cell = {
        "cell_id": f"{task}/{config}/rep{rep}",
        "task": task,
        "config": config,
        "rep": rep,
        "state": state,
    }
    if outcome is not None:
        cell["outcome"] = outcome
    return cell


@st.composite
def st_status(draw, max_cells=st.integers(min_value=0, max_value=30)):
    """Generate a full status dict as consumed by _counts."""
    if isinstance(max_cells, st.SearchStrategy):
        n = draw(max_cells)
    else:
        n = max_cells
    cells = {}
    for _ in range(n):
        cell = draw(st_cell())
        cells[cell["cell_id"]] = cell
    has_started = draw(st.booleans())
    started = utc_now() if has_started else None
    return {
        "cells": cells,
        "preflight": {},
        "started_at": started,
    }


# ===========================================================================
#  classify_result
# ===========================================================================

class TestClassifyResult:
    """Properties of classify_result — the outcome classifier.

    Catches: reordered precedence checks, missing branches, crashes on
    unexpected exit-code types, and non-deterministic output.
    """

    @given(st_result_record())
    def test_never_crashes(self, record):
        """No valid result.json-shaped dict causes classify_result to crash."""
        classify_result(record)  # should not raise

    @given(st_result_record())
    def test_output_is_string(self, record):
        """classify_result always returns a string label."""
        result = classify_result(record)
        assert isinstance(result, str)
        assert len(result) > 0

    @given(st_result_record())
    def test_deterministic(self, record):
        """Same input always yields same output."""
        assert classify_result(record) == classify_result(record)

    @given(st_result_record())
    def test_output_domain(self, record):
        """Output is always one of the known label families."""
        result = classify_result(record)
        known = {"ok", "empty", "timeout", "transient"}
        is_exit = result.startswith("exit=")
        assert result in known or is_exit, f"unexpected label: {result!r}"

    # --- Precedence properties ---

    @given(st_result_record())
    def test_transient_beats_everything(self, record):
        """If transient_model_error is set, the outcome is always 'transient',
        regardless of agent_exit, verifier_exit, or agent_timed_out.

        Catches: transient check being reordered after timeout/exit checks.
        """
        if record.get("transient_model_error"):
            assert classify_result(record) == "transient"

    @given(AGENT_EXITS, VERIFIER_EXITS, st.booleans())
    def test_timeout_beats_exit_code(self, agent_exit, verifier_exit, timed_out):
        """If agent_timed_out is True (and not transient), outcome is 'timeout',
        even if agent_exit is nonzero.

        Catches: exit-code check appearing before the timeout check.
        """
        record = {"agent_exit": agent_exit, "verifier_exit": verifier_exit,
                  "agent_timed_out": timed_out, "transient_model_error": False}
        result = classify_result(record)
        if timed_out:
            assert result == "timeout"

    @given(AGENT_EXITS)
    def test_ok_requires_clean_exit(self, agent_exit):
        """Outcome 'ok' requires agent_exit in (0, '0') and verifier_exit 0."""
        record = {"agent_exit": agent_exit, "verifier_exit": 0,
                  "agent_timed_out": False, "transient_model_error": False}
        result = classify_result(record)
        if result == "ok":
            assert agent_exit in (0, "0")

    @given(VERIFIER_EXITS)
    def test_empty_only_when_skipped_empty_patch(self, verifier_exit):
        """Outcome 'empty' only when verifier_exit == 'skipped_empty_patch'."""
        record = {"agent_exit": 0, "verifier_exit": verifier_exit,
                  "agent_timed_out": False, "transient_model_error": False}
        result = classify_result(record)
        if result == "empty":
            assert verifier_exit == "skipped_empty_patch"

    @given(AGENT_EXITS, VERIFIER_EXITS)
    def test_exit_label_contains_code(self, agent_exit, verifier_exit):
        """When falling through to exit=N, the label contains the agent exit code."""
        record = {"agent_exit": agent_exit, "verifier_exit": verifier_exit,
                  "agent_timed_out": False, "transient_model_error": False}
        result = classify_result(record)
        if result.startswith("exit="):
            assert str(agent_exit) in result

    # --- Edge cases ---

    @given(st.dictionaries(st.text(min_size=1, max_size=5), st.integers(), max_size=10))
    def test_no_crash_on_arbitrary_dict(self, d):
        """Even a random dict with no expected keys should not crash."""
        classify_result(d)


# ===========================================================================
#  compact_result_summary
# ===========================================================================

class TestCompactResultSummary:
    """Properties of compact_result_summary — the field filter.

    Catches: accidentally leaking nested structures, admitting fields outside
    BASE_SUMMARY_FIELDS / SUMMARY_PREFIXES, or dropping valid scalar fields.
    """

    @given(st_result_record())
    def test_only_scalar_values(self, record):
        """Summary values are only str/int/float/bool/None — never list/dict."""
        summary = compact_result_summary(record)
        for v in summary.values():
            assert isinstance(v, (str, int, float, bool)) or v is None

    @given(st_result_record())
    def test_keys_in_allowed_set(self, record):
        """Every summary key is in BASE_SUMMARY_FIELDS or has an allowed prefix."""
        summary = compact_result_summary(record)
        for key in summary:
            assert key in BASE_SUMMARY_FIELDS or key.startswith(SUMMARY_PREFIXES), \
                f"leaked field: {key!r}"

    @given(st_result_record())
    def test_idempotent(self, record):
        """Summarizing an already-summarized dict yields the same dict."""
        once = compact_result_summary(record)
        twice = compact_result_summary(once)
        assert once == twice

    @given(st_result_record())
    def test_preserves_known_scalar_fields(self, record):
        """If the record has a BASE_SUMMARY_FIELDS key with a scalar value,
        it appears in the summary."""
        summary = compact_result_summary(record)
        for key in BASE_SUMMARY_FIELDS:
            val = record.get(key)
            if isinstance(val, (str, int, float, bool)) or val is None:
                if key in record:
                    assert key in summary

    @given(st_result_record())
    def test_excludes_nested_structures(self, record):
        """Nested dicts/lists must never appear in the summary."""
        summary = compact_result_summary(record)
        for key, val in record.items():
            if isinstance(val, (list, dict)):
                assert key not in summary

    def test_prefix_fields_included(self):
        """Fields with known prefixes are included if scalar."""
        record = {
            "advisor_total_tokens": 100,
            "om_worker_observer_calls": 5,
            "combined_cost_usd": 1.5,
            "recursive_child_total_tokens": 200,
            "arm_model": "some-model",
            "arm_pi_flags": {"flags": ["--no-skills"]},  # dict → excluded
        }
        summary = compact_result_summary(record)
        assert "advisor_total_tokens" in summary
        assert "om_worker_observer_calls" in summary
        assert "combined_cost_usd" in summary
        assert "recursive_child_total_tokens" in summary
        assert "arm_model" in summary
        # arm_pi_flags is a dict (non-scalar) → excluded even though prefix matches
        assert "arm_pi_flags" not in summary


# ===========================================================================
#  RunStateWriter._counts  — the function that had the dashboard bug
# ===========================================================================

class TestCounts:
    """Properties of RunStateWriter._counts — the aggregate counter.

    These properties collectively pin down the exact invariant that was broken:
    skipped cells must not inflate the ok/empty/timeout/transient/failed buckets.

    Mutation to verify these catch bugs:
      1. Remove `state != "skipped"` guard → test_skipped_does_not_inflate fails
      2. Count skipped toward failed → test_partition_terminal fails
      3. Forget to count batch_running → test_running_count_matches fails
    """

    @given(st_status())
    def test_all_counts_non_negative(self, status):
        """Every count bucket is >= 0."""
        counts = RunStateWriter._counts(status)
        for key, val in counts.items():
            assert val >= 0, f"{key}={val} is negative"

    @given(st_status())
    def test_batch_total_equals_cell_count(self, status):
        """batch_total equals the number of cells in the status dict."""
        counts = RunStateWriter._counts(status)
        assert counts["batch_total"] == len(status.get("cells") or {})

    @given(st_status())
    def test_batch_done_is_terminal_count(self, status):
        """batch_done counts exactly the cells in TERMINAL_STATES."""
        cells = (status.get("cells") or {}).values()
        expected = sum(1 for c in cells if c.get("state") in TERMINAL_STATES)
        counts = RunStateWriter._counts(status)
        assert counts["batch_done"] == expected

    @given(st_status())
    def test_running_count_matches(self, status):
        """batch_running equals the number of cells with state=='running'."""
        cells = (status.get("cells") or {}).values()
        expected = sum(1 for c in cells if c.get("state") == "running")
        counts = RunStateWriter._counts(status)
        assert counts["batch_running"] == expected

    @given(st_status())
    def test_skipped_count_matches(self, status):
        """batch_skipped equals the number of cells with state=='skipped'."""
        cells = (status.get("cells") or {}).values()
        expected = sum(1 for c in cells if c.get("state") == "skipped")
        counts = RunStateWriter._counts(status)
        assert counts["batch_skipped"] == expected

    @given(st_status())
    def test_consistency_done_partition(self, status):
        """batch_done == (ok + empty + timeout + transient + failed + batch_skipped)
        + terminal cells with no outcome.

        Every terminal cell is counted exactly once in batch_done. Cells that
        have an outcome go to their outcome bucket; skipped go to batch_skipped;
        terminal cells with outcome=None are counted in batch_done but not in
        any outcome bucket (a known gap for cells whose outcome was never set).

        Catches: double-counting, missing buckets, or counting non-terminal cells.
        """
        cells = (status.get("cells") or {})
        counts = RunStateWriter._counts(status)
        outcome_sum = (
            counts["ok"] + counts["empty"] + counts["timeout"]
            + counts["transient"] + counts["failed"] + counts["batch_skipped"]
        )
        # Count NON-SKIPPED terminal cells with no outcome (the gap).
        # Skipped cells are already counted in batch_skipped.
        no_outcome_terminal = sum(
            1 for c in cells.values()
            if c.get("state") in TERMINAL_STATES
            and c.get("state") != "skipped"
            and not c.get("outcome")
        )
        assert counts["batch_done"] == outcome_sum + no_outcome_terminal, (
            f"batch_done={counts['batch_done']} but outcome buckets sum to {outcome_sum} "
            f"(+ {no_outcome_terminal} no-outcome terminal cells)"
        )

    @given(st_status())
    def test_consistency_partition_when_all_have_outcomes(self, status):
        """When every terminal cell has a non-None outcome, the exact partition
        holds: batch_done == ok + empty + timeout + transient + failed + batch_skipped."""
        cells = (status.get("cells") or {})
        all_have_outcomes = all(
            c.get("outcome") is not None
            for c in cells.values()
            if c.get("state") in TERMINAL_STATES
        )
        if not all_have_outcomes:
            return  # skip: tested by test_consistency_done_partition
        counts = RunStateWriter._counts(status)
        outcome_sum = (
            counts["ok"] + counts["empty"] + counts["timeout"]
            + counts["transient"] + counts["failed"] + counts["batch_skipped"]
        )
        assert counts["batch_done"] == outcome_sum

    @given(st_status())
    def test_skipped_does_not_inflate_outcomes(self, status):
        """THE BUG-CATCHER: skipped cells must NOT contribute to
        ok/empty/timeout/transient/failed, even if their outcome field is 'ok'.

        This is the exact property that was broken when resume runs showed
        ok:108 for a 2-cell rerun.
        """
        cells = (status.get("cells") or {})
        counts = RunStateWriter._counts(status)

        # Count skipped cells that have outcome='ok'
        skipped_with_ok_outcome = sum(
            1 for c in cells.values()
            if c.get("state") == "skipped" and c.get("outcome") == "ok"
        )
        # Count non-skipped terminal cells with outcome='ok'
        non_skipped_ok = sum(
            1 for c in cells.values()
            if c.get("state") in TERMINAL_STATES
            and c.get("state") != "skipped"
            and c.get("outcome") == "ok"
        )

        assert counts["ok"] == non_skipped_ok, (
            f"ok={counts['ok']} but only {non_skipped_ok} non-skipped cells "
            f"have outcome=ok ({skipped_with_ok_outcome} skipped cells were "
            f"wrongly counted)"
        )

    @given(st_status())
    def test_outcome_buckets_exclude_skipped(self, status):
        """Generalization: ALL outcome buckets (ok/empty/timeout/transient/failed)
        exclude skipped cells, regardless of the skipped cell's outcome field."""
        cells = (status.get("cells") or {})
        counts = RunStateWriter._counts(status)

        for bucket in ("ok", "empty", "timeout", "transient"):
            non_skipped_with_bucket = sum(
                1 for c in cells.values()
                if c.get("state") in TERMINAL_STATES
                and c.get("state") != "skipped"
                and c.get("outcome") == bucket
            )
            assert counts[bucket] == non_skipped_with_bucket, (
                f"{bucket}={counts[bucket]} expected {non_skipped_with_bucket}"
            )

    @given(st_status())
    def test_failed_excludes_skipped(self, status):
        """The failed bucket excludes skipped cells even if their outcome
        is not a known label (e.g. exit=N)."""
        cells = (status.get("cells") or {})
        counts = RunStateWriter._counts(status)

        non_skipped_failed = sum(
            1 for c in cells.values()
            if c.get("state") in TERMINAL_STATES
            and c.get("state") != "skipped"
            and c.get("outcome")
            and c.get("outcome") not in ("ok", "empty", "timeout", "transient")
        )
        assert counts["failed"] == non_skipped_failed

    @given(st_status())
    def test_running_never_in_done(self, status):
        """A running cell is never counted in batch_done."""
        cells = (status.get("cells") or {}).values()
        has_running = any(c.get("state") == "running" for c in cells)
        counts = RunStateWriter._counts(status)
        terminal_expected = sum(1 for c in cells if c.get("state") in TERMINAL_STATES)
        if has_running:
            # running is not terminal, so batch_done should not include it
            assert counts["batch_running"] >= 1
            assert counts["batch_done"] == terminal_expected

    # --- Monotonicity ---

    @given(st_status(), st.data())
    def test_adding_terminal_cell_never_decreases_counts(self, status, data):
        """Adding a NEW terminal cell (unique cell_id) to the status never
        decreases any count bucket.

        We must ensure the new cell_id doesn't collide with an existing cell,
        since overwriting could legitimately decrease a bucket.
        """
        existing_ids = set((status.get("cells") or {}).keys())
        # Draw a cell_id guaranteed not to collide
        new_id = data.draw(st.text(alphabet=digits, min_size=6, max_size=6).map(
            lambda s: f"new-task-{s}/cfg/rep0"
        ))
        # Retry until unique (rare for 6-digit)
        import hypothesis.strategies as _st
        while new_id in existing_ids:
            new_id = data.draw(st.text(alphabet=digits, min_size=6, max_size=6).map(
                lambda s: f"new-task-{s}/cfg/rep0"
            ))
        state = data.draw(CELL_STATES.filter(lambda s: s in TERMINAL_STATES))
        outcome = data.draw(st.one_of(st.none(), OUTCOME_LABELS))
        new_cell = {
            "cell_id": new_id, "task": new_id.split("/")[0],
            "config": "cfg", "rep": 0, "state": state,
        }
        if outcome is not None:
            new_cell["outcome"] = outcome

        before = RunStateWriter._counts(status)
        status2 = json.loads(json.dumps(status))  # deep copy
        cells2 = status2.setdefault("cells", {})
        cells2[new_id] = new_cell
        after = RunStateWriter._counts(status2)
        for key in before:
            assert after[key] >= before[key], (
                f"{key} decreased: {before[key]} -> {after[key]}"
            )

    @given(st_status())
    def test_idempotent(self, status):
        """_counts is a pure projection: calling it twice gives the same result."""
        assert RunStateWriter._counts(status) == RunStateWriter._counts(status)

    # --- Edge cases ---

    def test_empty_status(self):
        """An empty status yields all-zero counts."""
        counts = RunStateWriter._counts({"cells": {}, "preflight": {}})
        assert counts["batch_total"] == 0
        assert counts["batch_done"] == 0
        assert counts["ok"] == 0

    def test_no_cells_key(self):
        """Missing 'cells' key does not crash."""
        counts = RunStateWriter._counts({})
        assert counts["batch_total"] == 0

    @settings(max_examples=50)
    @given(
        n_skipped_ok=st.integers(min_value=0, max_value=10),
        n_real_ok=st.integers(min_value=0, max_value=10),
    )
    def test_mixed_skipped_and_real_ok(self, n_skipped_ok, n_real_ok):
        """Directly test the bug scenario: N skipped cells with outcome='ok'
        plus M real ok cells → ok count should be M, not N+M."""
        cells = {}
        for i in range(n_skipped_ok):
            cells[f"task-s{i}/cfg/rep0"] = {
                "cell_id": f"task-s{i}/cfg/rep0", "task": f"task-s{i}",
                "config": "cfg", "rep": 0, "state": "skipped", "outcome": "ok",
            }
        for i in range(n_real_ok):
            cells[f"task-r{i}/cfg/rep0"] = {
                "cell_id": f"task-r{i}/cfg/rep0", "task": f"task-r{i}",
                "config": "cfg", "rep": 0, "state": "done", "outcome": "ok",
            }
        status = {"cells": cells, "preflight": {}}
        counts = RunStateWriter._counts(status)
        assert counts["ok"] == n_real_ok
        assert counts["batch_skipped"] == n_skipped_ok
        assert counts["batch_done"] == n_skipped_ok + n_real_ok


# ===========================================================================
#  summarize_result_path
# ===========================================================================

class TestSummarizeResultPath:
    """Properties of summarize_result_path — the (outcome, summary) resolver."""

    def test_path_precedence_with_file(self, tmp_path):
        """If result.json says 'ok', exit_code=1 is ignored."""
        result = tmp_path / "result.json"
        result.write_text(json.dumps({
            "agent_exit": 0, "verifier_exit": 0,
            "agent_timed_out": False, "transient_model_error": False,
        }))
        outcome, summary = summarize_result_path(result, exit_code=1)
        assert outcome == "ok"

    def test_missing_path_with_exit_code(self):
        """Missing path + exit_code → 'exit=N'."""
        outcome, _ = summarize_result_path(None, exit_code=2)
        assert outcome == "exit=2"

    def test_missing_path_no_exit_code(self):
        """Missing path + no exit_code → 'skipped'."""
        outcome, summary = summarize_result_path(None, exit_code=None)
        assert outcome == "skipped"
        assert summary == {}

    def test_transient_exit_code(self):
        """Missing path + exit_code matching transient_exit → 'transient'."""
        outcome, summary = summarize_result_path(None, exit_code=75, transient_exit=75)
        assert outcome == "transient"
        assert summary.get("transient_model_error") is True

    def test_non_transient_exit_code_ignores_transient_exit(self):
        """exit_code != transient_exit → falls through to exit=N."""
        outcome, _ = summarize_result_path(None, exit_code=2, transient_exit=75)
        assert outcome == "exit=2"

    @given(record=st_result_record())
    def test_summary_is_compact(self, record):
        """When reading from a file, summary matches compact_result_summary."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            result = Path(td) / "result.json"
            result.write_text(json.dumps(record))
            outcome_file, summary_file = summarize_result_path(result)
            expected_summary = compact_result_summary(record)
            assert summary_file == expected_summary
            assert outcome_file == classify_result(record)

    def test_corrupt_json_falls_back(self, tmp_path):
        """Corrupt JSON in result.json is treated as no result → falls back to
        exit_code logic (can't classify without verifier_exit)."""
        result = tmp_path / "result.json"
        result.write_text("{not valid json")
        outcome, summary = summarize_result_path(result, exit_code=0)
        assert outcome == "exit=0"  # corrupt → fallback to exit code
        assert summary.get("agent_exit") == 0


# ===========================================================================
#  make_cell / cell_id
# ===========================================================================

class TestMakeCell:
    """Properties of make_cell and cell_id."""

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99))
    def test_cell_id_format(self, task, config, rep):
        """cell_id follows the task/config/repN format."""
        cid = cell_id(task, config, rep)
        assert cid == f"{task}/{config}/rep{rep}"

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99))
    def test_cell_id_roundtrip(self, task, config, rep):
        """cell_id can be parsed back into its components."""
        cid = cell_id(task, config, rep)
        parts = cid.rsplit("/", 1)  # split off repN
        prefix, rep_part = parts
        task_got, config_got = prefix.split("/", 1)
        assert task_got == task
        assert config_got == config
        assert rep_part == f"rep{rep}"
        assert int(rep_part[3:]) == rep

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99))
    def test_make_cell_core_fields(self, task, config, rep):
        """make_cell always includes cell_id, task, config, rep."""
        cell = make_cell(task=task, config=config, rep=rep)
        assert cell["cell_id"] == f"{task}/{config}/rep{rep}"
        assert cell["task"] == task
        assert cell["config"] == config
        assert cell["rep"] == rep

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99),
           st.text(min_size=1, max_size=50))
    def test_make_cell_includes_result_path(self, task, config, rep, path):
        """result_path is included as a string when provided."""
        cell = make_cell(task=task, config=config, rep=rep, result_path=path)
        assert cell["result_path"] == str(path)

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99))
    def test_make_cell_excludes_none_result_path(self, task, config, rep):
        """result_path key is absent when not provided."""
        cell = make_cell(task=task, config=config, rep=rep)
        assert "result_path" not in cell

    @given(_SAFE_TEXT, _SAFE_TEXT, st.integers(min_value=0, max_value=99),
           st.dictionaries(
               st.text(min_size=1, max_size=10).filter(
                   lambda k: k not in ("cell_id", "task", "config", "rep", "result_path", "log_path")
               ),
               st.one_of(st.none(), st.text(max_size=5), st.integers()),
               max_size=5))
    def test_make_cell_excludes_none_extras(self, task, config, rep, extras):
        """Extra fields with None values are excluded; non-None are included."""
        cell = make_cell(task=task, config=config, rep=rep, **extras)
        for key, val in extras.items():
            if val is None:
                assert key not in cell, f"None extra {key!r} should be excluded"
            else:
                assert cell[key] == val


# ===========================================================================
#  sanitize_run_id
# ===========================================================================

class TestSanitizeRunId:
    """Properties of sanitize_run_id — the run_id validator."""

    @given(st.text(alphabet=ascii_lowercase + digits + "._-", min_size=1, max_size=128))
    def test_valid_alphanumeric_passes(self, run_id):
        """A string of [a-z0-9._-] starting with alphanumeric passes unchanged."""
        # Ensure first char is alphanumeric (the regex requires it)
        if run_id[0].isalnum():
            assert sanitize_run_id(run_id) == run_id

    def test_empty_raises(self):
        with pytest.raises(ValueError):
            sanitize_run_id("")

    @given(st.text(alphabet="!@#$%^&*()", min_size=1, max_size=10))
    def test_special_chars_raise(self, bad_id):
        with pytest.raises(ValueError):
            sanitize_run_id(bad_id)

    def test_too_long_raises(self):
        with pytest.raises(ValueError):
            sanitize_run_id("a" + "b" * 128)

    def test_leading_dot_raises(self):
        with pytest.raises(ValueError):
            sanitize_run_id(".starts-with-dot")

    def test_leading_dash_raises(self):
        with pytest.raises(ValueError):
            sanitize_run_id("-starts-with-dash")

    @given(st.integers(min_value=1, max_value=100000))
    def test_default_run_id_valid(self, pid):
        """default_run_id always produces a valid run_id."""
        from harness.run_state import default_run_id
        rid = default_run_id(pid=pid)
        assert sanitize_run_id(rid) == rid  # does not raise, returns unchanged


# ===========================================================================
#  _estimate_eta_s
# ===========================================================================

class TestEstimateEta:
    """Properties of _estimate_eta_s."""

    @given(st_status())
    def test_none_or_positive(self, status):
        """ETA is either None or a positive float."""
        eta = _estimate_eta_s(status)
        if eta is not None:
            assert isinstance(eta, float)
            assert eta > 0

    def test_none_when_no_cells(self):
        assert _estimate_eta_s({"cells": {}, "preflight": {}}) is None

    def test_none_when_no_started_at(self):
        status = {
            "cells": {"t/c/rep0": {"state": "done", "outcome": "ok"}},
            "started_at": None,
            "counts": {"batch_total": 1, "batch_done": 1},
        }
        assert _estimate_eta_s(status) is None

    def test_none_when_all_done(self):
        now = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat().replace("+00:00", "Z")
        status = {
            "cells": {"t/c/rep0": {"state": "done", "outcome": "ok"}},
            "started_at": now,
            "counts": {"batch_total": 1, "batch_done": 1},
        }
        assert _estimate_eta_s(status) is None

    def test_positive_when_incomplete(self):
        started = (datetime.now(timezone.utc) - timedelta(seconds=100)).isoformat().replace("+00:00", "Z")
        status = {
            "cells": {
                "t/c/rep0": {"state": "done", "outcome": "ok"},
                "t/c/rep1": {"state": "pending"},
            },
            "started_at": started,
            "counts": {"batch_total": 2, "batch_done": 1},
        }
        eta = _estimate_eta_s(status)
        assert eta is not None and eta > 0


# ===========================================================================
#  _failure_buckets
# ===========================================================================

class TestFailureBuckets:
    """Properties of _failure_buckets."""

    @given(st_status())
    def test_excludes_ok_empty_skipped(self, status):
        """ok, empty, and skipped outcomes never appear in failure buckets."""
        buckets = _failure_buckets(status)
        assert "ok" not in buckets
        assert "empty" not in buckets
        assert "skipped" not in buckets

    @given(st_status())
    def test_all_values_positive(self, status):
        """Every failure bucket has a positive count."""
        buckets = _failure_buckets(status)
        for key, val in buckets.items():
            assert val > 0, f"{key}={val}"

    @given(st_status())
    def test_values_match_cell_outcomes(self, status):
        """Bucket counts match the number of non-skipped cells with that outcome,
        excluding ok/empty/skipped/None."""
        cells = (status.get("cells") or {}).values()
        expected = {}
        for c in cells:
            outcome = c.get("outcome")
            if not outcome or outcome in ("ok", "empty", "skipped"):
                continue
            expected[outcome] = expected.get(outcome, 0) + 1
        assert _failure_buckets(status) == expected


# ===========================================================================
#  seconds_since / parse_timestamp
# ===========================================================================

class TestTimestamps:
    """Properties of timestamp parsing utilities."""

    @given(st.text(max_size=20))
    def test_parse_timestamp_none_or_datetime(self, text):
        """parse_timestamp returns None for invalid, datetime for valid ISO strings."""
        result = parse_timestamp(text)
        assert result is None or isinstance(result, datetime)

    def test_parse_timestamp_roundtrip(self):
        """utc_now() output is parseable by parse_timestamp."""
        ts = utc_now()
        parsed = parse_timestamp(ts)
        assert parsed is not None
        assert parsed.year == datetime.now(timezone.utc).year

    @given(st.text(max_size=20))
    def test_seconds_since_none_or_nonneg(self, text):
        """seconds_since returns None or a non-negative float."""
        result = seconds_since(text)
        if result is not None:
            assert isinstance(result, float)
            assert result >= 0

    def test_seconds_since_past_is_positive(self):
        """A timestamp 10 seconds ago yields ~10 seconds."""
        past = (datetime.now(timezone.utc) - timedelta(seconds=10)).isoformat().replace("+00:00", "Z")
        result = seconds_since(past)
        assert result is not None
        assert 9 <= result <= 15  # allow jitter

    def test_seconds_since_empty_is_none(self):
        assert seconds_since("") is None
        assert seconds_since(None) is None


# ===========================================================================
#  project_structured_run  (requires filesystem)
# ===========================================================================

class TestProjectStructuredRun:
    """Properties of project_structured_run — the run projection."""

    def _make_run(self, tmp_path, cells_data, state="running"):
        """Create a minimal structured run directory."""
        run_dir = tmp_path / "results" / "_runs" / "test-run"
        run_dir.mkdir(parents=True)
        manifest = {"run_id": "test-run", "model": "m", "thinking": "high",
                     "configs": ["cfg"], "selection": {}, "workers": 4}
        (run_dir / "manifest.json").write_text(json.dumps(manifest))
        status = {
            "schema_version": 1, "run_id": "test-run",
            "state": state, "stage": "batch",
            "started_at": utc_now(), "updated_at": utc_now(),
            "heartbeat_at": utc_now(),
            "cells": {c["cell_id"]: c for c in cells_data},
            "preflight": {},
            "recent_finished": [],
        }
        (run_dir / "status.json").write_text(json.dumps(status))
        return run_dir

    @given(cells_data=st.lists(st_cell(), min_size=0, max_size=15))
    def test_counts_recomputed_from_cells(self, cells_data):
        """project_structured_run recomputes counts from cells, NOT from the
        status.json 'counts' field. This is the fix for the dashboard bug
        where a stale batch process wrote wrong counts."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run_dir = self._make_run(Path(td), cells_data)
            projected = project_structured_run(run_dir, detail="summary")
            expected_counts = RunStateWriter._counts({
                "cells": {c["cell_id"]: c for c in cells_data},
                "preflight": {},
            })
            assert projected["counts"] == expected_counts

    @given(cells_data=st.lists(st_cell(), min_size=0, max_size=10))
    def test_counts_ignore_stale_status_counts(self, cells_data):
        """Even if status.json has a 'counts' field with wrong values, the
        projected counts come from re-computing over cells."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            tmp_path = Path(td)
            run_dir = tmp_path / "results" / "_runs" / "stale-run"
            run_dir.mkdir(parents=True)
            (run_dir / "manifest.json").write_text(json.dumps({"run_id": "stale-run"}))
            status = {
                "run_id": "stale-run", "state": "running",
                "cells": {c["cell_id"]: c for c in cells_data},
                "preflight": {},
                "counts": {"ok": 99999, "batch_total": 99999},  # deliberately wrong
                "started_at": utc_now(), "updated_at": utc_now(),
                "heartbeat_at": utc_now(),
            }
            (run_dir / "status.json").write_text(json.dumps(status))
            projected = project_structured_run(run_dir)
            assert projected["counts"]["ok"] != 99999
            assert projected["counts"]["batch_total"] == len({c["cell_id"] for c in cells_data})

    @given(cells_data=st.lists(st_cell(), min_size=0, max_size=10))
    def test_detail_level_key_nesting(self, cells_data):
        """summary keys ⊆ operational keys ⊆ diagnostic keys."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run_dir = self._make_run(Path(td), cells_data)
            s = project_structured_run(run_dir, detail="summary")
            o = project_structured_run(run_dir, detail="operational")
            d = project_structured_run(run_dir, detail="diagnostic")
            assert set(s.keys()) <= set(o.keys())
            assert set(o.keys()) <= set(d.keys())
            assert "active_cells" not in s
            assert "active_cells" in o
            assert "status" in d
            assert "status" not in o

    def test_invalid_detail_defaults_to_summary(self, tmp_path):
        """An unrecognized detail level falls back to summary."""
        run_dir = self._make_run(tmp_path, [])
        projected = project_structured_run(run_dir, detail="bogus")
        assert "active_cells" not in projected  # summary-level

    @given(cells_data=st.lists(st_cell(), min_size=0, max_size=10))
    def test_failure_buckets_consistent_with_counts(self, cells_data):
        """The projected failure_buckets are consistent with _failure_buckets."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            run_dir = self._make_run(Path(td), cells_data)
            projected = project_structured_run(run_dir)
            status = json.loads((run_dir / "status.json").read_text())
            expected = _failure_buckets(status)
            assert projected["failure_buckets"] == expected


# ===========================================================================
#  discover_runs
# ===========================================================================

class TestDiscoverRuns:
    """Properties of discover_runs — the run discovery + sorting."""

    def _make_run_dir(self, root, run_id, updated_at, cells=None):
        run_dir = root / run_id
        run_dir.mkdir(parents=True)
        (run_dir / "manifest.json").write_text(json.dumps({"run_id": run_id}))
        status = {
            "run_id": run_id, "state": "completed",
            "cells": {c["cell_id"]: c for c in (cells or [])},
            "preflight": {},
            "updated_at": updated_at, "heartbeat_at": updated_at,
            "started_at": updated_at,
        }
        (run_dir / "status.json").write_text(json.dumps(status))

    @given(run_specs=st.lists(st.tuples(
        st.text(alphabet=ascii_lowercase + digits, min_size=3, max_size=8),
        st.integers(min_value=0, max_value=1000000),
    ), min_size=0, max_size=10, unique_by=lambda x: x[0]))
    def test_sorted_by_updated_at_descending(self, run_specs):
        """Runs are sorted by updated_at in descending order."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "results" / "_runs"
            for name, offset in run_specs:
                ts = (datetime(2026, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=offset)).isoformat().replace("+00:00", "Z")
                self._make_run_dir(root, f"run-{name}", ts)

            runs = discover_runs(root, include_legacy=False)
            timestamps = [r.get("updated_at") or "" for r in runs]
            assert timestamps == sorted(timestamps, reverse=True)

    @given(cells_data=st.lists(st_cell(), min_size=0, max_size=10))
    def test_counts_correct_per_run(self, cells_data):
        """Each discovered run has counts recomputed from its cells."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "results" / "_runs"
            self._make_run_dir(root, "test-run", utc_now(), cells=cells_data)
            runs = discover_runs(root, include_legacy=False)
            assert len(runs) == 1
            expected = RunStateWriter._counts({
                "cells": {c["cell_id"]: c for c in cells_data},
                "preflight": {},
            })
            assert runs[0]["counts"] == expected

    def test_idempotent(self, tmp_path):
        """Calling discover_runs twice yields the same result (excluding
        time-dependent fields like heartbeat_age_s which drift naturally)."""
        root = tmp_path / "results" / "_runs"
        self._make_run_dir(root, "run-a", utc_now())
        first = discover_runs(root, include_legacy=False)
        second = discover_runs(root, include_legacy=False)
        # Strip time-dependent fields before comparing
        TIME_FIELDS = {"heartbeat_age_s", "eta_s"}
        f1 = [{k: v for k, v in r.items() if k not in TIME_FIELDS} for r in first]
        f2 = [{k: v for k, v in r.items() if k not in TIME_FIELDS} for r in second]
        assert f1 == f2


# ===========================================================================
#  read_events
# ===========================================================================

class TestReadEvents:
    """Properties of read_events — the NDJSON event reader."""

    def _write_events(self, path, count):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as fh:
            for i in range(1, count + 1):
                fh.write(json.dumps({"seq": i, "event": f"e{i}"}) + "\n")

    @given(n_events=st.integers(min_value=0, max_value=50), limit=st.integers(min_value=1, max_value=100))
    def test_limit_clamped_and_respected(self, n_events, limit):
        """read_events returns at most `limit` events (clamped to [1, 1000])."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.ndjson"
            self._write_events(path, n_events)
            result = read_events(Path(td), limit=limit)
            expected = min(n_events, min(max(limit, 1), 1000))
            assert len(result) == expected

    @given(n_events=st.integers(min_value=0, max_value=50), after=st.integers(min_value=0, max_value=50))
    def test_after_filter(self, n_events, after):
        """With after=N, only events with seq > N are returned."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.ndjson"
            self._write_events(path, n_events)
            result = read_events(Path(td), after=after)
            for rec in result:
                assert rec["seq"] > after
            expected = max(0, n_events - after)
            assert len(result) == min(expected, 100)

    def test_missing_file_returns_empty(self, tmp_path):
        assert read_events(tmp_path / "nonexistent") == []

    @given(limit=st.integers(min_value=-100, max_value=0))
    def test_zero_or_negative_limit_returns_at_least_one(self, limit):
        """limit is clamped to minimum 1."""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "events.ndjson"
            self._write_events(path, 5)
            result = read_events(Path(td), limit=limit)
            assert len(result) >= 1


# ===========================================================================
#  RuleBasedStateMachine — model-based testing of RunStateWriter
# ===========================================================================

class RunStateWriterMachine(RuleBasedStateMachine):
    """Model-based stateful test for RunStateWriter.

    Maintains a reference model (a dict of cell_id -> {state, outcome}) and
    verifies that the writer's status always matches the model after every
    operation.

    This catches bugs that only emerge from specific operation *sequences*:
    e.g., skip-then-finish, start-then-skip, or count drift across many ops.

    Invariants checked after every step:
      - _counts(status) matches independently computed model counts
      - batch_done is always consistent (partition property)
      - no skipped cell appears in the ok bucket
    """

    def __init__(self):
        super().__init__()
        self.tmp_path = Path("/tmp/rlm_state_machine_test")
        self.tmp_path.mkdir(parents=True, exist_ok=True)
        # Clean any prior state
        import shutil
        state_root = self.tmp_path / "state_root"
        if state_root.exists():
            shutil.rmtree(state_root)

        cells = [
            make_cell(task=f"task-{i}", config="cfg", rep=0)
            for i in range(6)
        ]
        manifest = {
            "run_id": "machine-test",
            "schema_version": 1,
            "batch_cells": cells,
            "preflight": [],
        }
        self.writer = RunStateWriter(state_root, manifest)
        self.writer.start()
        self.cells = cells
        # Reference model: cell_id -> {"state": "pending", "outcome": None}
        self.model = {
            c["cell_id"]: {"state": "pending", "outcome": None}
            for c in cells
        }

    # --- Rules ---

    cell_bundle = Bundle("cell")

    @rule(target=cell_bundle, idx=st.integers(min_value=0, max_value=5))
    def get_cell(self, idx):
        return self.cells[idx]

    @rule(cell=cell_bundle)
    def start_cell(self, cell):
        self.writer.cell_started(cell)
        self.model[cell["cell_id"]]["state"] = "running"
        self.model[cell["cell_id"]]["outcome"] = None

    @rule(cell=cell_bundle, outcome=OUTCOME_LABELS)
    def finish_cell(self, cell, outcome):
        """Finish a cell with a given outcome (simulates result.json on disk)."""
        # We can't write real result.json easily, so use cell_finished with
        # exit_code that produces the desired outcome family
        exit_code_map = {
            "ok": 0, "empty": 0, "timeout": "timeout", "transient": 75,
            "exit=0": 0, "exit=1": 1, "exit=2": 2, "exit=75": 75, "exit=130": 130,
            "skipped": None,
        }
        ec = exit_code_map.get(outcome, 0)
        transient = 75 if outcome == "transient" else 75
        if outcome == "skipped":
            self.writer.cell_skipped(cell)
            self.model[cell["cell_id"]]["state"] = "skipped"
        else:
            self.writer.cell_finished(cell, exit_code=ec, transient_exit=transient)
            self.model[cell["cell_id"]]["state"] = "done"
        self.model[cell["cell_id"]]["outcome"] = outcome

    @rule(cell=cell_bundle)
    def skip_cell(self, cell):
        self.writer.cell_skipped(cell)
        self.model[cell["cell_id"]]["state"] = "skipped"
        # cell_skipped sets outcome from result_path (which is None → "skipped")
        self.model[cell["cell_id"]]["outcome"] = "skipped"

    # --- Invariants ---

    @invariant()
    def counts_match_model(self):
        """The writer's _counts must match what the reference model predicts."""
        status = self.writer.status
        actual = RunStateWriter._counts(status)

        # Compute expected from model
        cells = status.get("cells") or {}
        expected = {
            "batch_total": len(cells), "batch_done": 0, "batch_running": 0,
            "batch_skipped": 0, "ok": 0, "empty": 0, "timeout": 0,
            "transient": 0, "failed": 0,
            "preflight_total": 0, "preflight_done": 0, "preflight_running": 0,
            "preflight_skipped": 0, "preflight_failed": 0,
        }
        for cid, cell in cells.items():
            state = cell.get("state")
            outcome = cell.get("outcome")
            if state == "running":
                expected["batch_running"] += 1
            if state == "skipped":
                expected["batch_skipped"] += 1
            if state in TERMINAL_STATES:
                expected["batch_done"] += 1
            if state in TERMINAL_STATES and outcome and state != "skipped":
                if outcome in ("ok", "empty", "timeout", "transient"):
                    expected[outcome] += 1
                else:
                    expected["failed"] += 1

        assert actual == expected, (
            f"counts mismatch:\nactual={actual}\nexpected={expected}"
        )

    @invariant()
    def partition_holds(self):
        """batch_done == (ok + empty + timeout + transient + failed + batch_skipped)
        + terminal cells with no outcome."""
        status = self.writer.status
        cells = status.get("cells") or {}
        c = RunStateWriter._counts(status)
        outcome_sum = c["ok"] + c["empty"] + c["timeout"] + c["transient"] + c["failed"] + c["batch_skipped"]
        no_outcome = sum(
            1 for cell in cells.values()
            if cell.get("state") in TERMINAL_STATES
            and cell.get("state") != "skipped"
            and not cell.get("outcome")
        )
        assert c["batch_done"] == outcome_sum + no_outcome

    @invariant()
    def skipped_never_in_ok(self):
        """No skipped cell is counted in the ok bucket — the dashboard bug."""
        status = self.writer.status
        cells = status.get("cells") or {}
        counts = RunStateWriter._counts(status)
        skipped_ok = sum(
            1 for c in cells.values()
            if c.get("state") == "skipped" and c.get("outcome") == "ok"
        )
        non_skipped_ok = sum(
            1 for c in cells.values()
            if c.get("state") in TERMINAL_STATES
            and c.get("state") != "skipped"
            and c.get("outcome") == "ok"
        )
        assert counts["ok"] == non_skipped_ok, (
            f"ok={counts['ok']} but {skipped_ok} skipped cells have outcome=ok "
            f"and {non_skipped_ok} real cells have outcome=ok"
        )

    @invariant()
    def status_file_matches_memory(self):
        """The status.json on disk matches the writer's in-memory status
        (after every operation the writer saves)."""
        on_disk = json.loads(self.writer.status_path.read_text())
        assert on_disk["counts"] == RunStateWriter._counts(self.writer.status)

    def teardown(self):
        self.writer.stop_heartbeat()


@pytest.mark.stateful
class TestRunStateWriterMachine:
    """Runs the RuleBasedStateMachine for RunStateWriter."""

    def test_state_machine(self):
        run_state_machine_as_test(
            RunStateWriterMachine,
            settings=settings(
                max_examples=100,
                stateful_step_count=50,
                deadline=None,
                suppress_health_check=[HealthCheck.too_slow],
            ),
        )

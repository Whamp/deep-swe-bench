from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parents[1]))

from analysis.trajectory_process_signals.baseline_analysis import (
    CATEGORICAL_CONTROL_NAMES,
    LENGTH_FEATURE_NAMES,
    STOCK_PI_BASELINE_CONFIGS,
    _average_precision,
    build_task_folds,
    classify_primary_model_disposition,
    discover_result_inventory,
    is_canonical_result_path,
    select_analysis_tasks,
)
from analysis.trajectory_process_signals.extractor import (
    PROCESS_FEATURE_NAMES,
    extract_session_process_features,
    normalize_tool_action,
    parse_native_session,
)


def _message(role: str, content: list[dict], **fields: object) -> dict:
    return {
        "type": "message",
        "message": {"role": role, "content": content, **fields},
    }


def _assistant_tool(call_id: str, name: str, arguments: dict) -> dict:
    return _message(
        "assistant",
        [{"type": "toolCall", "id": call_id, "name": name, "arguments": arguments}],
        stopReason="toolUse",
        usage={"input": 10, "output": 2, "totalTokens": 12},
    )


def _tool_result(call_id: str, name: str, text: str, *, is_error: bool) -> dict:
    return _message(
        "toolResult",
        [{"type": "text", "text": text}],
        toolCallId=call_id,
        toolName=name,
        isError=is_error,
    )


def _write_session(path: Path, records: list[dict]) -> None:
    path.write_text("".join(json.dumps(record) + "\n" for record in records))


def test_normalize_tool_action_is_stable_but_preserves_meaning() -> None:
    left = normalize_tool_action(
        "read", {"path": "/app/src/example.py", "offset": 1, "limit": 20}
    )
    right = normalize_tool_action(
        "READ", {"limit": 20, "offset": 1, "path": "./src/example.py"}
    )

    assert left == right
    assert left != normalize_tool_action(
        "read", {"path": "/app/src/example.py", "offset": 21, "limit": 20}
    )
    assert normalize_tool_action(
        "bash", {"command": "  python  -m pytest   tests/test_x.py  "}
    ) == normalize_tool_action("bash", {"command": "python -m pytest tests/test_x.py"})


def test_extract_transition_features_only_uses_pre_verifier_session_events(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / "session.jsonl"
    records = [
        {"type": "session", "id": "s1", "cwd": "/app", "timestamp": 1},
        {"type": "model_change", "provider": "example", "modelId": "model"},
        {"type": "thinking_level_change", "thinkingLevel": "low"},
        _assistant_tool("r1", "read", {"path": "/app/src/example.py"}),
        _tool_result("r1", "read", "one", is_error=False),
        _assistant_tool("r2", "read", {"path": "./src/example.py"}),
        _tool_result("r2", "read", "one", is_error=False),
        _assistant_tool("t1", "bash", {"command": "python -m pytest tests/test_x.py"}),
        _tool_result("t1", "bash", "1 failed", is_error=True),
        _assistant_tool("t2", "bash", {"command": "python  -m pytest tests/test_x.py"}),
        _tool_result("t2", "bash", "1 failed", is_error=True),
        _assistant_tool(
            "e1",
            "edit",
            {"path": "/app/src/example.py", "oldText": "before", "newText": "after"},
        ),
        _tool_result("e1", "edit", "updated", is_error=False),
        _message(
            "assistant",
            [
                {
                    "type": "thinking",
                    "thinking": "That failed. I need to rethink this approach.",
                }
            ],
            stopReason="stop",
            usage={"input": 10, "output": 2, "totalTokens": 12},
        ),
        _assistant_tool("t3", "bash", {"command": "python -m pytest tests/test_x.py"}),
        _tool_result("t3", "bash", "1 passed", is_error=False),
        _assistant_tool(
            "e2",
            "edit",
            {"path": "src/example.py", "oldText": "after", "newText": "before"},
        ),
        _tool_result("e2", "edit", "updated", is_error=False),
        _assistant_tool("t4", "bash", {"command": "python -m pytest tests/test_x.py"}),
        _tool_result("t4", "bash", "1 failed again", is_error=True),
    ]
    _write_session(session_path, records)

    parsed = parse_native_session(session_path)
    features = extract_session_process_features(parsed)

    assert parsed.assistant_turns == 9
    assert parsed.tool_calls == 8
    assert features["repeated_normalized_tool_actions"] == 4
    assert features["repeated_read_targets"] == 1
    assert features["repeated_tests_without_observed_edit"] == 1
    assert features["repeated_unchanged_test_failures"] == 1
    assert features["test_failure_to_pass_transitions"] == 1
    assert features["test_pass_to_failure_transitions"] == 1
    assert features["direct_mutation_target_revisits"] == 1
    assert features["exact_inverse_edit_pairs"] == 1
    assert features["strategy_reset_turns"] == 1
    assert features["opaque_top_level_tool_calls"] == 0


def test_opaque_nested_tool_surface_is_marked_unsupported(tmp_path: Path) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_session(
        session_path,
        [
            {"type": "session", "id": "s1", "cwd": "/app"},
            _assistant_tool(
                "f1",
                "fabric_exec",
                {"code": "return await pi.bash({cmd: 'pytest -q'});"},
            ),
            _tool_result("f1", "fabric_exec", "1 failed", is_error=True),
        ],
    )

    features = extract_session_process_features(parse_native_session(session_path))

    assert features["opaque_top_level_tool_calls"] == 1
    assert features["observable_test_runs"] == 0
    assert features["semantic_event_coverage"] == 0.0


def test_primary_model_disposition_separates_censoring_and_verifier_errors() -> None:
    valid = {
        "agent_timed_out": False,
        "agent_exit": 0,
        "verifier_exit": 0,
        "reward_binary": 0,
        "reward_partial": 0.75,
    }

    assert classify_primary_model_disposition(valid, session_count=1) == "eligible"
    assert (
        classify_primary_model_disposition(
            {**valid, "agent_timed_out": True, "agent_exit": "timeout"},
            session_count=1,
        )
        == "agent_timeout"
    )
    assert (
        classify_primary_model_disposition(
            {**valid, "verifier_exit": "timeout", "reward_binary": -1},
            session_count=1,
        )
        == "verifier_timeout"
    )
    assert (
        classify_primary_model_disposition(
            {**valid, "verifier_exit": "skipped_empty_patch", "reward_binary": -1},
            session_count=1,
        )
        == "verifier_skipped_empty_patch"
    )
    assert (
        classify_primary_model_disposition(valid, session_count=0) == "missing_session"
    )
    assert (
        classify_primary_model_disposition(valid, session_count=2)
        == "ambiguous_multiple_sessions"
    )
    assert (
        classify_primary_model_disposition(
            valid, session_count=1, terminal_stop_reason="length"
        )
        == "terminal_output_truncation"
    )


def test_canonical_result_path_excludes_reserved_or_nested_roots(
    tmp_path: Path,
) -> None:
    results = tmp_path / "results"
    canonical = results / "model" / "low" / "config" / "task" / "rep2" / "result.json"
    archived = (
        results
        / "_archives"
        / "snapshot"
        / "model"
        / "low"
        / "config"
        / "task"
        / "rep2"
        / "result.json"
    )

    assert is_canonical_result_path(canonical, results)
    assert not is_canonical_result_path(archived, results)
    assert not is_canonical_result_path(
        canonical.with_name("result.copy.json"), results
    )


def test_schema_inventory_counts_native_verifier_and_patch_shapes(
    tmp_path: Path,
) -> None:
    results = tmp_path / "results"
    cell = results / "model" / "low" / "config" / "task" / "rep0"
    (cell / "session").mkdir(parents=True)
    (cell / "artifacts").mkdir()
    (cell / "verifier").mkdir()
    (cell / "session" / "session.jsonl").write_text("{}\n")
    patch = "diff --git a/a.py b/a.py\n+new\n"
    (cell / "artifacts" / "model.patch").write_text(patch)
    (cell / "verifier" / "reward.json").write_text(
        json.dumps({"reward": 0.5, "f2p": 1.0, "p2p": 0.0})
    )
    (cell / "verifier" / "ctrf.json").write_text(
        json.dumps(
            {
                "results": {
                    "summary": {"tests": 2, "passed": 1, "failed": 1},
                    "tests": [],
                }
            }
        )
    )
    result = {
        "task": "task",
        "config": "config",
        "rep": 0,
        "model": "provider/model",
        "thinking_level": "low",
        "reward_binary": 0,
        "reward_partial": 0.5,
        "total_tokens": 100,
        "turns": 2,
        "tool_calls": 1,
        "agent_wall_s": 3.0,
        "agent_exit": 0,
        "agent_timed_out": False,
        "verifier_exit": 0,
        "patch_bytes": len(patch.encode()),
    }
    (cell / "result.json").write_text(json.dumps(result))

    rows, audit = discover_result_inventory(results)

    assert rows[0]["primary_disposition"] == "eligible"
    assert audit["candidate_native_session_files"] == 1
    assert audit["native_session_dispositions"] == {
        "attached_to_selected_canonical_result": 1
    }
    assert audit["model_patch_schema"]["size_matches_result_patch_bytes"] == 1
    assert audit["model_patch_schema"]["unified_diff_header"] == 1
    assert audit["verifier_reward_schema"]["reward"]["present"] == 1
    assert audit["verifier_reward_schema"]["reward"]["missing_from_reward_files"] == 0
    assert audit["verifier_ctrf_schema"]["summary_fields"]["failed"]["present"] == 1


def test_inventory_filters_to_stock_pi_baseline_configs(tmp_path: Path) -> None:
    results = tmp_path / "results"
    result_template = {
        "task": "task",
        "rep": 0,
        "model": "provider/model",
        "thinking_level": "low",
        "reward_binary": 0,
        "reward_partial": 0.5,
        "total_tokens": 100,
        "turns": 1,
        "tool_calls": 0,
        "agent_wall_s": 1.0,
        "agent_exit": 0,
        "agent_timed_out": False,
        "verifier_exit": 0,
        "patch_bytes": 0,
    }
    for config in ("baseline", "pi-fabric"):
        cell = results / "model" / "low" / config / "task" / "rep0"
        (cell / "session").mkdir(parents=True)
        (cell / "session" / "session.jsonl").write_text("{}\n")
        (cell / "result.json").write_text(
            json.dumps({**result_template, "config": config})
        )

    rows, audit = discover_result_inventory(
        results, allowed_configs=STOCK_PI_BASELINE_CONFIGS
    )

    assert [row["config"] for row in rows] == ["baseline"]
    assert audit["analysis_scope"]["allowed_configs"] == [
        "baseline",
        "baseline@1.0.0",
        "baseline@1.1.0",
    ]
    assert audit["analysis_scope"]["excluded_canonical_results"] == 1
    assert audit["analysis_scope"]["excluded_config_counts"] == {"pi-fabric": 1}
    assert audit["native_session_dispositions"] == {
        "attached_to_excluded_canonical_result": 1,
        "attached_to_selected_canonical_result": 1,
    }


def test_default_analysis_task_selection_includes_every_eligible_task() -> None:
    rows = [
        {"task": "alpha", "primary_disposition": "eligible"},
        {"task": "beta", "primary_disposition": "eligible"},
        {"task": "excluded", "primary_disposition": "agent_timeout"},
    ]

    assert set(select_analysis_tasks(rows, task_limit=None)) == {"alpha", "beta"}
    assert len(select_analysis_tasks(rows, task_limit=1)) == 1


def test_task_folds_are_deterministic_and_task_disjoint() -> None:
    rows = [
        {"task": task, "cell_id": f"{task}-{rep}"}
        for task in ("alpha", "beta", "gamma", "delta", "epsilon", "zeta")
        for rep in range(2)
    ]

    folds = build_task_folds(rows, fold_count=3)

    assert folds == build_task_folds(list(reversed(rows)), fold_count=3)
    assert len(folds) == 3
    seen_test_tasks: set[str] = set()
    for fold in folds:
        train_tasks = set(fold["train_tasks"])
        test_tasks = set(fold["test_tasks"])
        assert train_tasks.isdisjoint(test_tasks)
        seen_test_tasks.update(test_tasks)
    assert seen_test_tasks == {row["task"] for row in rows}


def test_average_precision_handles_prediction_ties_without_row_order_bias() -> None:
    outcomes = np.array([0.0, 1.0, 0.0, 1.0])
    tied_predictions = np.full(4, 0.5)

    assert _average_precision(outcomes, tied_predictions) == 0.5
    assert _average_precision(outcomes[::-1], tied_predictions) == 0.5


def test_predictor_allowlist_excludes_outcomes_and_verifier_artifacts() -> None:
    predictor_names = {
        *LENGTH_FEATURE_NAMES,
        *PROCESS_FEATURE_NAMES,
        *CATEGORICAL_CONTROL_NAMES,
    }

    assert not {
        name
        for name in predictor_names
        if name.startswith(("reward", "verifier", "f2p", "p2p"))
        or name in {"patch_bytes", "artifacts", "result_path"}
    }

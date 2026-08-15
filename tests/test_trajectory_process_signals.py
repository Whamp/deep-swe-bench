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
    summarize_task_controlled_feature_effects,
)
from analysis.trajectory_process_signals.extractor import (
    MUTATION_STYLE_FEATURE_NAMES,
    OPENING_FEATURE_NAMES,
    PROCESS_FEATURE_NAMES,
    TEST_FLOW_FEATURE_NAMES,
    extract_session_process_features,
    normalize_tool_action,
    parse_native_session,
)
from analysis.trajectory_process_signals.random_forest_analysis import (
    RANDOM_FOREST_SPECIFICATIONS,
    RandomForestParameters,
    encode_random_forest_design,
    evaluate_random_forest_held_out_tasks,
    select_certain_source_mutation_rows,
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


def test_sequence_features_separate_diagnosis_implementation_and_validation(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / "session.jsonl"
    records = [
        {"type": "session", "id": "s1", "cwd": "/app"},
        _assistant_tool("r1", "read", {"path": "/app/src/example.py"}),
        _tool_result("r1", "read", "source", is_error=False),
        _assistant_tool("t0", "bash", {"command": "pytest -q"}),
        _tool_result("t0", "bash", "1 failed", is_error=True),
        _assistant_tool(
            "w0", "write", {"path": "repro_bug.py", "content": "assert False\n"}
        ),
        _tool_result("w0", "write", "created", is_error=False),
        _assistant_tool(
            "e1",
            "edit",
            {"path": "src/example.py", "oldText": "before", "newText": "after"},
        ),
        _tool_result("e1", "edit", "updated", is_error=False),
        _assistant_tool("t1", "bash", {"command": "pytest -q"}),
        _tool_result("t1", "bash", "still failing", is_error=True),
        _assistant_tool(
            "w1", "write", {"path": "src/example.py", "content": "replacement\n"}
        ),
        _tool_result("w1", "write", "updated", is_error=False),
        _assistant_tool("t2", "bash", {"command": "pytest -q"}),
        _tool_result("t2", "bash", "passed", is_error=False),
        _assistant_tool(
            "e2",
            "edit",
            {"path": "src/example.py", "oldText": "replacement", "newText": "extra"},
        ),
        _tool_result("e2", "edit", "updated", is_error=False),
        _assistant_tool("t3", "bash", {"command": "pytest -q"}),
        _tool_result("t3", "bash", "failed again", is_error=True),
    ]
    _write_session(session_path, records)

    features = extract_session_process_features(parse_native_session(session_path))

    assert features["has_successful_source_mutation"] == 1
    assert features["first_workspace_mutation_is_write"] == 1
    assert features["first_source_mutation_is_write"] == 0
    assert features["tool_calls_before_first_source_mutation"] == 3
    assert features["turns_before_first_source_mutation"] == 3
    assert features["tokens_before_first_source_mutation"] == 36
    assert features["reads_before_first_source_mutation"] == 1
    assert features["unique_paths_read_before_first_source_mutation"] == 1
    assert features["tests_before_first_source_mutation"] == 1
    assert features["failed_tests_before_first_source_mutation"] == 1
    assert features["successful_edit_calls"] == 2
    assert features["successful_write_calls"] == 2
    assert features["source_mutation_calls"] == 3
    assert features["source_edit_calls"] == 2
    assert features["source_write_calls"] == 1
    assert features["reproduction_mutation_calls"] == 1
    assert features["mutation_tool_switches"] == 3
    assert features["write_then_edit_same_target"] == 1
    assert features["tests_after_first_source_mutation"] == 3
    assert features["source_mutations_before_first_post_mutation_test"] == 1
    assert features["implementation_to_validation_transitions"] == 3
    assert features["validation_to_implementation_backtracks"] == 2
    assert features["source_mutations_after_passing_test"] == 1
    assert features["pass_mutation_fail_patterns"] == 1
    assert features["tests_after_final_source_mutation"] == 1
    assert features["has_passing_test_after_final_source_mutation"] == 0
    assert set(OPENING_FEATURE_NAMES) <= features.keys()
    assert set(MUTATION_STYLE_FEATURE_NAMES) <= features.keys()
    assert set(TEST_FLOW_FEATURE_NAMES) <= features.keys()


def test_possible_shell_mutation_before_source_edit_is_marked_uncertain(
    tmp_path: Path,
) -> None:
    session_path = tmp_path / "session.jsonl"
    _write_session(
        session_path,
        [
            {"type": "session", "id": "s1", "cwd": "/app"},
            _assistant_tool("b1", "bash", {"command": "sed -i 's/a/b/' src/a.py"}),
            _tool_result("b1", "bash", "", is_error=False),
            _assistant_tool(
                "e1",
                "edit",
                {"path": "src/a.py", "oldText": "b", "newText": "c"},
            ),
            _tool_result("e1", "edit", "updated", is_error=False),
        ],
    )

    features = extract_session_process_features(parse_native_session(session_path))

    assert features["possible_shell_mutations_before_first_source_mutation"] == 1
    assert features["first_source_mutation_boundary_uncertain"] == 1


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


def test_task_controlled_effects_compare_outcomes_within_each_task() -> None:
    rows = [
        {"task": "a", "reward_binary": 0, "reads": 1.0},
        {"task": "a", "reward_binary": 1, "reads": 3.0},
        {"task": "b", "reward_binary": 0, "reads": 10.0},
        {"task": "b", "reward_binary": 1, "reads": 12.0},
        {"task": "success-only", "reward_binary": 1, "reads": 100.0},
    ]

    summary = summarize_task_controlled_feature_effects(rows, ("reads",))

    assert summary["reads"]["contested_tasks"] == 2
    assert summary["reads"]["mean_success_minus_failure"] == 2.0
    assert summary["reads"]["fraction_tasks_higher_in_success"] == 1.0


def test_average_precision_handles_prediction_ties_without_row_order_bias() -> None:
    outcomes = np.array([0.0, 1.0, 0.0, 1.0])
    tied_predictions = np.full(4, 0.5)

    assert _average_precision(outcomes, tied_predictions) == 0.5
    assert _average_precision(outcomes[::-1], tied_predictions) == 0.5


def test_predictor_allowlist_excludes_outcomes_and_verifier_artifacts() -> None:
    predictor_names = {
        *LENGTH_FEATURE_NAMES,
        *PROCESS_FEATURE_NAMES,
        *OPENING_FEATURE_NAMES,
        *MUTATION_STYLE_FEATURE_NAMES,
        *TEST_FLOW_FEATURE_NAMES,
        *CATEGORICAL_CONTROL_NAMES,
        *(name for names in RANDOM_FOREST_SPECIFICATIONS.values() for name in names),
    }

    assert not {
        name
        for name in predictor_names
        if name.startswith(("reward", "verifier", "f2p", "p2p"))
        or name in {"patch_bytes", "artifacts", "result_path"}
    }


def test_random_forest_clean_boundary_requires_observed_certain_source_change() -> None:
    rows = [
        {
            "cell_id": "clean",
            "has_successful_source_mutation": 1.0,
            "first_source_mutation_boundary_uncertain": 0.0,
        },
        {
            "cell_id": "shell-uncertain",
            "has_successful_source_mutation": 1.0,
            "first_source_mutation_boundary_uncertain": 1.0,
        },
        {
            "cell_id": "no-source-change",
            "has_successful_source_mutation": 0.0,
            "first_source_mutation_boundary_uncertain": 0.0,
        },
    ]

    assert [row["cell_id"] for row in select_certain_source_mutation_rows(rows)] == [
        "clean"
    ]


def test_random_forest_encoder_uses_training_categories_without_outcome_fields() -> (
    None
):
    train_rows = [
        {"signal": 1.0, "model": "a", "reward_binary": 0},
        {"signal": 2.0, "model": "b", "reward_binary": 1},
    ]
    test_rows = [{"signal": 3.0, "model": "unseen", "reward_binary": 1}]

    train, test, names = encode_random_forest_design(
        train_rows,
        test_rows,
        numeric_names=("signal",),
        categorical_names=("model",),
    )

    assert names == ("signal", "model=a", "model=b")
    assert train.tolist() == [[1.0, 1.0, 0.0], [2.0, 0.0, 1.0]]
    assert test.tolist() == [[3.0, 0.0, 0.0]]
    assert all("reward" not in name for name in names)


def test_random_forest_finds_nonlinear_signal_on_whole_held_out_tasks() -> None:
    feature_names = set(RANDOM_FOREST_SPECIFICATIONS["test_flow"])
    rows: list[dict[str, object]] = []
    for task_index in range(18):
        for rep in range(8):
            left = float((rep // 2) % 2)
            right = float(rep % 2)
            row: dict[str, object] = {name: 0.0 for name in feature_names}
            row.update(
                {
                    "task": f"task-{task_index:02d}",
                    "cell_id": f"task-{task_index:02d}-rep{rep}",
                    "model": "model",
                    "thinking_level": "high",
                    "config": "baseline",
                    "reward_binary": int(bool(left) != bool(right)),
                    "tests_after_first_source_mutation": left,
                    "implementation_to_validation_transitions": right,
                }
            )
            rows.append(row)
    specifications = {
        name: RANDOM_FOREST_SPECIFICATIONS[name] for name in ("length", "test_flow")
    }
    parameters = (
        RandomForestParameters(max_depth=6, min_samples_leaf=2, max_features=1.0),
    )

    first = evaluate_random_forest_held_out_tasks(
        rows,
        outer_fold_count=3,
        inner_fold_count=2,
        specifications=specifications,
        parameter_grid=parameters,
        tuning_trees=40,
        final_trees=80,
        final_seeds=(11, 29),
    )
    second = evaluate_random_forest_held_out_tasks(
        rows,
        outer_fold_count=3,
        inner_fold_count=2,
        specifications=specifications,
        parameter_grid=parameters,
        tuning_trees=40,
        final_trees=80,
        final_seeds=(11, 29),
    )

    assert first["design"] == second["design"]
    assert [fold["test_tasks"] for fold in first["folds"]] == [
        fold["test_tasks"] for fold in second["folds"]
    ]
    assert [fold["selected_parameters"] for fold in first["folds"]] == [
        fold["selected_parameters"] for fold in second["folds"]
    ]
    for name in specifications:
        np.testing.assert_allclose(
            list(first["binary_metrics"][name].values()),
            list(second["binary_metrics"][name].values()),
            rtol=1e-12,
            atol=1e-12,
        )
    assert first["binary_metrics"]["test_flow"]["auroc"] > 0.95
    assert (
        first["binary_metrics"]["test_flow"]["log_loss"]
        < first["binary_metrics"]["length"]["log_loss"] - 0.2
    )
    assert len(first["folds"]) == 3
    for fold in first["folds"]:
        assert set(fold["train_tasks"]).isdisjoint(fold["test_tasks"])
        assert set(fold["oob_diagnostics"]) == {"length", "test_flow"}

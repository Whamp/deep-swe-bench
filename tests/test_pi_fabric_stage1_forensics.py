from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ANALYZER_PATH = (
    Path(__file__).parents[1]
    / "analysis/pi-fabric-native-read-guidance-stage1/analyze_stage1.py"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location("analyze_stage1", ANALYZER_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assistant(tool_call_id: str, code: str, cache_read: int) -> dict:
    return {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "id": tool_call_id,
                    "name": "fabric_exec",
                    "arguments": {"code": code},
                }
            ],
            "usage": {"cacheRead": cache_read, "input": 10, "output": 5},
        },
    }


def tool_result(tool_call_id: str, operations: list[dict]) -> dict:
    return {
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolName": "fabric_exec",
            "toolCallId": tool_call_id,
            "content": [{"type": "text", "text": "ok"}],
            "details": {
                "success": True,
                "trace": {"operations": operations},
            },
        },
    }


def test_detects_serialized_search_fragmented_reads_and_mutation(
    tmp_path: Path,
) -> None:
    analyzer = load_analyzer()
    session = tmp_path / "session.jsonl"
    records = [
        assistant("search", "return pi.grep('needle', 'src')", 100),
        tool_result(
            "search",
            [{"ref": "pi.grep", "args": {"pattern": "needle", "path": "src"}}],
        ),
        assistant(
            "read-one", "return pi.read({path:'src/a.py', offset:1, limit:100})", 200
        ),
        tool_result(
            "read-one",
            [
                {
                    "ref": "pi.read",
                    "args": {"path": "src/a.py", "offset": 1, "limit": 100},
                }
            ],
        ),
        assistant(
            "read-two-edit",
            "const text = await pi.read({path:'src/a.py', offset:81, limit:80}); "
            "await pi.edit({path:'src/a.py', oldText:'x', newText:'y'}); return text",
            300,
        ),
        tool_result(
            "read-two-edit",
            [
                {
                    "ref": "pi.read",
                    "args": {"path": "src/a.py", "offset": 81, "limit": 80},
                },
                {
                    "ref": "pi.edit",
                    "args": {"path": "src/a.py", "oldText": "x", "newText": "y"},
                },
            ],
        ),
    ]
    session.write_text("\n".join(json.dumps(record) for record in records))

    trajectory = analyzer.parse_fabric_session(session, task="task-a", rep=0)
    metrics = analyzer.summarize_trajectory(trajectory)

    assert metrics["outer_calls"] == 3
    assert metrics["operation_count_histogram"] == {1: 2, 2: 1}
    assert metrics["read_calls"] == 2
    assert metrics["read_operations"] == 2
    assert metrics["bounded_read_operations"] == 2
    assert metrics["whole_file_read_operations"] == 0
    assert metrics["search_only_to_read_transitions"] == 1
    assert metrics["read_to_read_transitions"] == 1
    assert metrics["cross_call_repeated_path_reads"] == 1
    assert metrics["cross_call_overlapping_reads"] == 1
    assert metrics["retrieval_calls_before_first_mutation"] == 2
    assert metrics["cache_read_before_first_mutation"] == 300
    assert metrics["cache_read_for_retrieval_continuations"] == 500
    assert metrics["mutation_calls"] == 1
    assert metrics["mutation_operations"] == 1
    assert metrics["unique_mutation_paths"] == 1
    assert metrics["repeated_mutation_path_operations"] == 0


def test_same_call_search_and_read_is_not_serialized(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    session = tmp_path / "session.jsonl"
    records = [
        assistant(
            "combined",
            "const hits = await pi.grep('needle', 'src'); "
            "return pi.read({path:'src/a.py', offset:1, limit:40})",
            80,
        ),
        tool_result(
            "combined",
            [
                {"ref": "pi.grep", "args": {"pattern": "needle", "path": "src"}},
                {
                    "ref": "pi.read",
                    "args": {"path": "src/a.py", "offset": 1, "limit": 40},
                },
            ],
        ),
    ]
    session.write_text("\n".join(json.dumps(record) for record in records))

    trajectory = analyzer.parse_fabric_session(session, task="task-a", rep=0)
    metrics = analyzer.summarize_trajectory(trajectory)

    assert metrics["same_call_search_and_read"] == 1
    assert metrics["outer_calls"] == 1
    assert metrics["search_only_to_read_transitions"] == 0
    assert metrics["trajectories_with_explicit_mutation"] == 0
    assert metrics["retrieval_calls_before_first_mutation"] == 0


def native_assistant(tool_calls: list[tuple[str, str, dict]], cache_read: int) -> dict:
    return {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "toolCall",
                    "id": tool_call_id,
                    "name": name,
                    "arguments": arguments,
                }
                for tool_call_id, name, arguments in tool_calls
            ],
            "usage": {"cacheRead": cache_read, "input": 10, "output": 5},
        },
    }


def native_result(tool_call_id: str, name: str, *, is_error: bool = False) -> dict:
    return {
        "type": "message",
        "message": {
            "role": "toolResult",
            "toolName": name,
            "toolCallId": tool_call_id,
            "content": [{"type": "text", "text": "ok"}],
            "isError": is_error,
        },
    }


def test_native_parallel_tools_are_one_outer_turn(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    session = tmp_path / "session.jsonl"
    records = [
        native_assistant(
            [
                ("read", "read", {"path": "src/a.py", "offset": 1, "limit": 50}),
                (
                    "edit",
                    "edit",
                    {"path": "src/a.py", "oldText": "x", "newText": "y"},
                ),
            ],
            100,
        ),
        native_result("edit", "edit"),
        native_result("read", "read"),
        native_assistant(
            [("test", "bash", {"command": "pytest -q"})],
            200,
        ),
        native_result("test", "bash"),
    ]
    session.write_text("\n".join(json.dumps(record) for record in records))

    trajectory = analyzer.parse_native_session(session, task="task-a", rep=0)
    metrics = analyzer.summarize_trajectory(trajectory)

    assert metrics["outer_calls"] == 2
    assert metrics["nested_operations"] == 3
    assert metrics["multi_operation_calls"] == 1
    assert metrics["parallel_calls"] == 1
    assert metrics["mutation_calls"] == 1
    assert metrics["calls_after_first_mutation"] == 1
    assert metrics["cache_read_before_first_mutation"] == 0
    assert metrics["cache_read_after_first_mutation"] == 200
    assert metrics["assistant_cache_read"] == 300


def test_detects_repeated_mutation_rounds_on_the_same_path(tmp_path: Path) -> None:
    analyzer = load_analyzer()
    session = tmp_path / "session.jsonl"
    records = [
        assistant("edit-one", "return pi.edit({path:'src/a.py'})", 100),
        tool_result(
            "edit-one",
            [{"ref": "pi.edit", "args": {"path": "src/a.py"}}],
        ),
        assistant("edit-two", "return pi.edit({path:'src/a.py'})", 200),
        tool_result(
            "edit-two",
            [{"ref": "pi.edit", "args": {"path": "src/a.py"}}],
        ),
    ]
    session.write_text("\n".join(json.dumps(record) for record in records))

    trajectory = analyzer.parse_fabric_session(session, task="task-a", rep=0)
    metrics = analyzer.summarize_trajectory(trajectory)

    assert metrics["mutation_calls"] == 2
    assert metrics["mutation_operations"] == 2
    assert metrics["unique_mutation_paths"] == 1
    assert metrics["repeated_mutation_path_operations"] == 1
    assert metrics["consecutive_mutation_transitions"] == 1
    assert metrics["calls_after_first_mutation"] == 1
    assert metrics["cache_read_after_first_mutation"] == 200

import json
from pathlib import Path

import pytest

from trajectory_evidence import (
    classify_repository_file,
    extract_shell_content_targets,
    extract_trajectory_evidence,
    is_validation_command,
    normalize_repository_path,
    summarize_tool_results,
)


def test_normalize_repository_path_removes_task_root() -> None:
    assert normalize_repository_path("/app/src/index.ts") == "src/index.ts"
    assert normalize_repository_path("./tests/test_api.py") == "tests/test_api.py"
    assert normalize_repository_path("/tmp/output.txt") is None
    assert normalize_repository_path("src/*.ts") is None


def test_classify_repository_file_recognizes_analysis_focus() -> None:
    assert classify_repository_file("src/index.ts") == "source"
    assert classify_repository_file("src/index.test.ts") == "test"
    assert classify_repository_file("tests/test_api.py") == "test"
    assert classify_repository_file("docs/design.md") == "docs"
    assert classify_repository_file("package.json") == "config"
    assert classify_repository_file("fixtures/sample.sql") == "other"


def test_extract_shell_content_targets_keeps_only_exact_files() -> None:
    command = (
        'rg -n "Error" src test* package.json && '
        "cat /app/tsconfig.json && sed -n '1,80p' src/index.ts"
    )
    assert extract_shell_content_targets(command) == [
        "package.json",
        "tsconfig.json",
        "src/index.ts",
    ]


@pytest.mark.parametrize(
    "command",
    [
        "go test ./...",
        "go build ./checkers/...",
        "go vet ./checkers/internal/astwalk ./checkers",
        "cat > /tmp/probe.go <<'EOF'\npackage main\nEOF\ngo build /tmp/probe.go",
        "uv run pytest tests/test_api.py -q",
        "ruff check src tests",
        "python -m compileall -q src",
        "tox -e lint",
        "jest --runInBand tests/example.test.js",
        "npm run test",
    ],
)
def test_is_validation_command_covers_supported_task_languages(command: str) -> None:
    assert is_validation_command(command)


@pytest.mark.parametrize(
    "command",
    [
        "git status --short",
        'rg -n "ruff|mypy" tox.ini pyproject.toml',
        'grep -n "go build" README.md',
    ],
)
def test_is_validation_command_excludes_diagnostic_commands(command: str) -> None:
    assert not is_validation_command(command)


def test_extract_trajectory_evidence_excludes_failed_or_non_file_reads(
    tmp_path: Path,
) -> None:
    session_root = tmp_path / "session"
    session_root.mkdir()
    records = [
        {
            "type": "message",
            "message": {
                "role": "assistant",
                "content": [
                    {
                        "type": "toolCall",
                        "id": "ok",
                        "name": "read",
                        "arguments": {"path": "/app/src/index.ts"},
                    },
                    {
                        "type": "toolCall",
                        "id": "bad",
                        "name": "read",
                        "arguments": {"path": "/app/src/missing.ts"},
                    },
                    {
                        "type": "toolCall",
                        "id": "attribute",
                        "name": "read",
                        "arguments": {"path": "self.backend"},
                    },
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolCallId": "bad",
                "isError": True,
                "content": [{"type": "text", "text": "not found"}],
            },
        },
    ]
    (session_root / "session.jsonl").write_text(
        "".join(json.dumps(record) + "\n" for record in records)
    )

    evidence = extract_trajectory_evidence(tmp_path)

    assert evidence["content_read_paths"] == ["src/index.ts"]
    assert evidence["failed_tool_calls"] == 1
    assert evidence["tool_results"]["errors"] == 1


def test_summarize_tool_results_separates_shell_failures_from_bad_edit_shapes() -> None:
    records = [
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "bash",
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": "2 tests failed\nCommand exited with code 1",
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "edit",
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": (
                            'Validation failed for tool "edit":\n'
                            "  - path: must have required properties path\n\n"
                            'Received arguments:\n{"edits":[{"path":"src/a.py",'
                            '"oldText":"a","newText":"b"}]}'
                        ),
                    }
                ],
            },
        },
        {
            "type": "message",
            "message": {
                "role": "toolResult",
                "toolName": "read",
                "isError": False,
                "content": [{"type": "text", "text": "contents"}],
            },
        },
    ]

    summary = summarize_tool_results(records)

    assert summary["total"] == 3
    assert summary["errors"] == 2
    assert summary["error_categories"] == {
        "shell command returned nonzero": 1,
        "malformed edit arguments": 1,
    }
    assert summary["malformed_edit_shapes"] == {
        "path put inside each edit instead of at top level": 1
    }

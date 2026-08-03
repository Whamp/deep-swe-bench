"""Extract comparable file-coverage and decision evidence from Pi sessions."""

from __future__ import annotations

import collections
import json
import re
import shlex
from pathlib import Path
from typing import Any

VALIDATION_PATTERN = re.compile(
    r"(?:^|[;&|\n]\s*)(?:go\s+(?:test|build|vet)\b|pytest\b|"
    r"python(?:3)?\s+-m\s+(?:pytest|compileall|ruff|tox)\b|"
    r"ruff\s+(?:check|format)\b|tox(?:\s|$)|jest(?:\s|$)|"
    r"uvx\b[^\n;&|]*\bruff\s+(?:check|format)\b|"
    r"npm\s+(?:test|run\s+(?:test|lint|typecheck|build))\b|"
    r"pnpm\s+(?:test|run\s+(?:test|lint|typecheck|build))\b|"
    r"yarn\s+(?:test|lint|typecheck|build)\b|npx\s+(?:tsc|jest|vitest)\b|"
    r"cargo\s+test\b|make\s+(?:test|check)\b|uv\s+run\b)",
    re.IGNORECASE,
)
DISCOVERY_PATTERN = re.compile(r"(?:^|[;&|]\s*)(?:find|ls|tree)\b")
SEARCH_PATTERN = re.compile(r"(?:^|[;&|]\s*)(?:rg|grep)\b")
STATUS_PATTERN = re.compile(r"\bgit\s+(?:status|diff|log|show)\b")
SHELL_MUTATION_PATTERN = re.compile(
    r"(?:\bapply_patch\b|\bsed\s+-i\b|\bperl\s+-i\b|"
    r"(?:^|[;&|]\s*)(?:cat|printf|echo)\b[^\n]*(?:>|>>)|"
    r"\bpython(?:3)?\b[^\n]*(?:write_text|open\([^)]*,\s*['\"]w))",
    re.IGNORECASE,
)
CONTENT_COMMAND_PATTERN = re.compile(
    r"(?:^|[;&|]\s*)(?:cat|head|tail|sed|rg|grep)\b", re.IGNORECASE
)
PATH_TOKEN_PATTERN = re.compile(
    r"^(?:/app/|\./)?(?:[A-Za-z0-9_@.+-]+/)*[A-Za-z0-9_@.+-]+(?:\.[A-Za-z0-9_+-]+)+$"
)
KNOWN_FILE_NAMES = {
    "Dockerfile",
    "Makefile",
    "README",
    "LICENSE",
    "go.mod",
    "go.sum",
    "package.json",
    "tsconfig.json",
    "pyproject.toml",
    "Cargo.toml",
    "Cargo.lock",
}
SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".h",
    ".hpp",
    ".java",
    ".js",
    ".jsx",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".swift",
    ".ts",
    ".tsx",
}
CONFIG_SUFFIXES = {
    ".json",
    ".jsonc",
    ".lock",
    ".toml",
    ".yaml",
    ".yml",
}
REPOSITORY_FILE_SUFFIXES = (
    SOURCE_SUFFIXES
    | CONFIG_SUFFIXES
    | {
        ".cfg",
        ".conf",
        ".css",
        ".gradle",
        ".html",
        ".ini",
        ".md",
        ".mdx",
        ".ne",
        ".proto",
        ".rst",
        ".scss",
        ".sh",
        ".sql",
        ".template",
        ".tmpl",
        ".txt",
        ".xml",
    }
)


def normalize_repository_path(raw_path: str) -> str | None:
    """Normalize one task-repository path without inventing glob expansions."""
    path = raw_path.strip().strip("'\"")
    path = path.rstrip(";,:)")
    if not path or any(character in path for character in "*$?{}"):
        return None
    if path.startswith("file://"):
        path = path.removeprefix("file://")
    if path == "/app":
        return None
    if path.startswith("/app/"):
        path = path.removeprefix("/app/")
    while path.startswith("./"):
        path = path[2:]
    if path.startswith(("../", "/")):
        return None
    path = re.sub(r"/+", "/", path)
    if not path or path.endswith("/"):
        return None
    return path


def looks_like_file_path(raw_path: str) -> bool:
    """Return whether a shell token denotes one exact file rather than a directory."""
    token = raw_path.strip().strip("'\"").rstrip(";,:)")
    name = token.rsplit("/", 1)[-1]
    suffix = Path(name).suffix.lower()
    return (
        name in KNOWN_FILE_NAMES
        or suffix in REPOSITORY_FILE_SUFFIXES
        and bool(PATH_TOKEN_PATTERN.fullmatch(token))
    )


def classify_repository_file(path: str) -> str:
    """Classify one repository file as source, test, docs, config, or other."""
    lowered = path.lower()
    parts = lowered.split("/")
    name = parts[-1]
    suffix = Path(name).suffix
    test_markers = (
        "test" in parts
        or "tests" in parts
        or "spec" in parts
        or "specs" in parts
        or name.startswith("test_")
        or name.endswith("_test.go")
        or ".test." in name
        or ".spec." in name
    )
    if test_markers:
        return "test"
    if (
        "docs" in parts
        or suffix in {".md", ".mdx", ".rst"}
        or name.startswith(("readme", "changelog", "contributing"))
    ):
        return "docs"
    if (
        suffix in CONFIG_SUFFIXES
        or name in {value.lower() for value in KNOWN_FILE_NAMES}
        or name.startswith(("tsconfig", "eslint", "prettier", "jest", "vitest"))
    ):
        return "config"
    if suffix in SOURCE_SUFFIXES:
        return "source"
    return "other"


def extract_shell_content_targets(command: str) -> list[str]:
    """Extract exact file arguments from shell commands that inspect file content."""
    if not CONTENT_COMMAND_PATTERN.search(command):
        return []
    try:
        tokens = shlex.split(command, comments=False, posix=True)
    except ValueError:
        tokens = command.split()
    paths = []
    for token in tokens:
        if not looks_like_file_path(token):
            continue
        normalized = normalize_repository_path(token)
        if normalized:
            paths.append(normalized)
    return list(dict.fromkeys(paths))


def is_validation_command(command: str) -> bool:
    """Return whether a shell command executes a likely validation surface."""
    return bool(VALIDATION_PATTERN.search(command))


def load_session_records(cell_root: Path) -> list[dict[str, Any]]:
    """Load all valid JSON records from one cell's ordered Pi session files."""
    records = []
    for session_path in sorted((cell_root / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def find_failed_tool_call_ids(records: list[dict[str, Any]]) -> set[str]:
    """Return tool call IDs whose recorded result is an error."""
    failed_ids = set()
    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        if message.get("role") != "toolResult" or message.get("isError") is not True:
            continue
        failed_ids.add(str(message.get("toolCallId")))
    return failed_ids


def tool_result_text(message: dict[str, Any]) -> str:
    """Join text blocks from one recorded tool result."""
    content = message.get("content")
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(block.get("text", ""))
        for block in content
        if isinstance(block, dict) and block.get("type") == "text"
    )


def malformed_edit_shape(error_text: str) -> str:
    """Describe the schema mistake in a rejected edit call."""
    marker = "Received arguments:\n"
    if marker not in error_text:
        return "unclassified malformed edit arguments"
    try:
        arguments = json.loads(error_text.split(marker, 1)[1])
    except json.JSONDecodeError:
        return "unparseable edit arguments"
    if not isinstance(arguments, dict):
        return "edit arguments were not an object"
    if isinstance(arguments.get("edits"), str):
        return "edits sent as a JSON string"
    edits = arguments.get("edits")
    if (
        "path" not in arguments
        and isinstance(edits, list)
        and any(isinstance(edit, dict) and "path" in edit for edit in edits)
    ):
        return "path put inside each edit instead of at top level"
    if "path" not in arguments:
        return "top-level path omitted"
    return "other malformed edit arguments"


def summarize_tool_results(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Count recorded tool failures without treating every nonzero command as a tool bug."""
    totals: collections.Counter[str] = collections.Counter()
    errors: collections.Counter[str] = collections.Counter()
    categories: collections.Counter[str] = collections.Counter()
    malformed_shapes: collections.Counter[str] = collections.Counter()

    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message")
        if not isinstance(message, dict) or message.get("role") != "toolResult":
            continue
        tool_name = str(message.get("toolName", "unknown"))
        totals[tool_name] += 1
        if message.get("isError") is not True:
            continue
        errors[tool_name] += 1
        error_text = tool_result_text(message)
        lowered = error_text.lower()
        if tool_name == "edit" and "validation failed for tool" in lowered:
            categories["malformed edit arguments"] += 1
            malformed_shapes[malformed_edit_shape(error_text)] += 1
        elif tool_name == "edit" and any(
            phrase in lowered
            for phrase in (
                "could not find the exact text",
                "oldtext must",
                "old text must",
                "must be unique",
                "found 2 occurrences",
                "did not match",
            )
        ):
            categories["edit target text did not match"] += 1
        elif tool_name == "edit":
            categories["other edit rejection"] += 1
        elif tool_name == "bash" and (
            "author identity unknown" in lowered
            or "unable to auto-detect email address" in lowered
        ):
            categories["git identity was not configured"] += 1
        elif tool_name == "bash":
            categories["shell command returned nonzero"] += 1
        elif tool_name == "read":
            categories["read request failed"] += 1
        else:
            categories[f"other {tool_name} failure"] += 1

    error_total = sum(errors.values())
    result_total = sum(totals.values())
    return {
        "total": result_total,
        "errors": error_total,
        "error_rate": error_total / result_total if result_total else 0,
        "by_tool_total": dict(totals),
        "by_tool_errors": dict(errors),
        "error_categories": dict(categories),
        "malformed_edit_shapes": dict(malformed_shapes),
    }


def extract_trajectory_evidence(cell_root: Path) -> dict[str, Any]:
    """Extract file coverage, command focus, and decision timing from one trajectory."""
    records = load_session_records(cell_root)
    failed_tool_call_ids = find_failed_tool_call_ids(records)
    tool_results = summarize_tool_results(records)
    tool_counts: collections.Counter[str] = collections.Counter()
    command_counts: collections.Counter[str] = collections.Counter()
    tool_events: list[dict[str, Any]] = []
    explicit_read_events: list[dict[str, Any]] = []
    shell_content_events: list[dict[str, Any]] = []
    validation_commands: list[dict[str, Any]] = []
    mutation_events: list[dict[str, Any]] = []
    thinking_samples: list[dict[str, Any]] = []
    final_text = ""
    assistant_turn = 0
    event_index = 0

    for record in records:
        if record.get("type") != "message":
            continue
        message = record.get("message", {})
        if message.get("role") != "assistant":
            continue
        assistant_turn += 1
        for block in message.get("content") or []:
            if not isinstance(block, dict):
                continue
            block_type = block.get("type")
            if block_type == "thinking":
                thinking = str(block.get("thinking", ""))
                if thinking:
                    thinking_samples.append(
                        {
                            "turn": assistant_turn,
                            "text": thinking[:1600],
                            "chars": len(thinking),
                        }
                    )
                continue
            if block_type == "text":
                text = str(block.get("text", ""))
                if text:
                    final_text = text
                continue
            if block_type != "toolCall":
                continue

            event_index += 1
            tool_name = str(block.get("name", "unknown"))
            tool_call_id = str(block.get("id", ""))
            tool_failed = tool_call_id in failed_tool_call_ids
            arguments = block.get("arguments") or {}
            tool_counts[tool_name] += 1
            event = {
                "event": event_index,
                "turn": assistant_turn,
                "tool": tool_name,
                "failed": tool_failed,
            }
            if tool_name == "read":
                raw_path = str(arguments.get("path", ""))
                normalized = normalize_repository_path(raw_path)
                if normalized and looks_like_file_path(raw_path) and not tool_failed:
                    event["path"] = normalized
                    explicit_read_events.append(dict(event))
            elif tool_name == "bash":
                command = str(arguments.get("command", ""))
                event["command"] = command
                if DISCOVERY_PATTERN.search(command):
                    command_counts["discovery"] += 1
                if SEARCH_PATTERN.search(command):
                    command_counts["search"] += 1
                if STATUS_PATTERN.search(command):
                    command_counts["status"] += 1
                if is_validation_command(command):
                    command_counts["validation"] += 1
                    validation_commands.append(event)
                if SHELL_MUTATION_PATTERN.search(command):
                    command_counts["mutation"] += 1
                    mutation_events.append(event)
                if not tool_failed:
                    for path in extract_shell_content_targets(command):
                        shell_content_events.append({**event, "path": path})
            elif tool_name in {"edit", "write"}:
                path = normalize_repository_path(str(arguments.get("path", "")))
                event["path"] = path
                mutation_events.append(dict(event))
            tool_events.append(event)

    first_mutation_event = min(
        (event["event"] for event in mutation_events), default=None
    )
    first_validation_event = min(
        (event["event"] for event in validation_commands), default=None
    )
    explicit_paths = [event["path"] for event in explicit_read_events]
    shell_paths = [event["path"] for event in shell_content_events]
    content_events = explicit_read_events + shell_content_events
    content_paths = sorted(set(explicit_paths) | set(shell_paths))
    first_test_read_event = min(
        (
            event["event"]
            for event in content_events
            if classify_repository_file(event["path"]) == "test"
        ),
        default=None,
    )
    pre_mutation_paths = sorted(
        {
            event["path"]
            for event in content_events
            if first_mutation_event is None or event["event"] < first_mutation_event
        }
    )

    def category_counts(paths: list[str]) -> dict[str, int]:
        counts = collections.Counter(classify_repository_file(path) for path in paths)
        return {
            category: counts.get(category, 0)
            for category in ("source", "test", "docs", "config", "other")
        }

    return {
        "assistant_turns": assistant_turn,
        "failed_tool_calls": len(failed_tool_call_ids),
        "tool_results": tool_results,
        "tool_counts": dict(tool_counts),
        "tool_events": tool_events,
        "command_counts": dict(command_counts),
        "explicit_read_events": explicit_read_events,
        "shell_content_events": shell_content_events,
        "content_read_paths": content_paths,
        "content_read_count": len(content_paths),
        "content_read_categories": category_counts(content_paths),
        "pre_mutation_paths": pre_mutation_paths,
        "pre_mutation_count": len(pre_mutation_paths),
        "pre_mutation_categories": category_counts(pre_mutation_paths),
        "first_mutation_event": first_mutation_event,
        "first_test_read_event": first_test_read_event,
        "first_validation_event": first_validation_event,
        "validation_commands": validation_commands,
        "mutation_events": mutation_events,
        "thinking_samples": thinking_samples,
        "final_text": final_text,
    }


def parse_changed_files(cell_root: Path) -> list[str]:
    """Return normalized files changed by the saved model patch."""
    candidates = [cell_root / "model.patch", cell_root / "artifacts/model.patch"]
    patch_path = next((path for path in candidates if path.exists()), None)
    if patch_path is None:
        return []
    patch = patch_path.read_text(errors="replace")
    return list(
        dict.fromkeys(re.findall(r"^diff --git a/(.*?) b/", patch, re.MULTILINE))
    )


def load_result(cell_root: Path) -> dict[str, Any]:
    """Load one benchmark result with its artifact root attached."""
    result = json.loads((cell_root / "result.json").read_text())
    result["artifact_root"] = str(cell_root)
    return result

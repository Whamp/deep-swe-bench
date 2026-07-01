#!/usr/bin/env python3
"""Throwaway parser for a potential codebase-memory bash hook.

Input: one bash command string + optional tool output.
Output: whether to augment, search tokens, and output files to use as ranking hints.

Design target: simple, data-shaped, fail-open. No shell execution, no config mutation.
"""
from __future__ import annotations

import re
import shlex
from collections import Counter
from dataclasses import dataclass, asdict
from typing import Iterable

SOURCE_EXT_RE = re.compile(r"\.(py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs)$")
TEST_PATH_RE = re.compile(r"(^|/)(__tests__|tests?|testdata|fixtures?)(/|$)|(_test\.go|\.test\.[tj]sx?$|\.spec\.[tj]sx?$|test_.*\.py$|_test\.rs$)")
SKIP_PATH_PARTS = (
    ".git/", "node_modules/", "vendor/", "dist/", "build/", "target/", ".cache/",
    "__pycache__/", "site-packages/", ".venv/", "coverage/",
)
NOISE_TOKENS = {
    "grep", "egrep", "fgrep", "rg", "find", "xargs", "git", "status", "branch", "show",
    "current", "short", "head", "tail", "sort", "uniq", "sed", "awk", "cat", "less", "more",
    "maxdepth", "mindepth", "type", "name", "path", "print", "exec", "include", "exclude",
    "files", "file", "src", "pkg", "lib", "app", "test", "tests", "true", "false", "null",
    "package", "config", "index", "main", "from", "import", "const", "func", "def", "class",
}
VALIDATION_RE = re.compile(
    r"\b(go\s+test|go\s+build|cargo\s+(test|check|build)|pytest|python\s+-m\s+pytest|"
    r"npm\s+(test|run)|npx\s+(tsc|jest|vitest)|pnpm|yarn|make|gofmt|ruff|mypy|"
    r"git\s+(add|commit|checkout|push|pull|merge|rebase|stash|clean|reset)|"
    r"pip\s+install|poetry|uv\s+)\b"
)
SEARCH_VERB_RE = re.compile(r"\b(git\s+grep|grep|egrep|fgrep|rg|ripgrep)\b")
DISCOVERY_ONLY_RE = re.compile(r"\b(find|fd|ls|tree)\b")
DEPENDENCY_MANIFEST_RE = re.compile(r"\b(go\.sum|go\.mod|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|poetry\.lock)\b")

PATH_COLON_RE = re.compile(r"(?m)^(?:\x1b\[[0-9;]*m)*(?P<path>[^:\n\r]+?):(?P<line>\d+)(?::\d+)?:")
BARE_PATH_RE = re.compile(r"(?m)^\s*(?:\./)?(?P<path>[A-Za-z0-9_./@+\-]+\.(?:py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs))\s*$")
GIT_STATUS_RE = re.compile(r"(?m)^[ MARCUD!?]{1,2}\s+(?P<path>.+?)(?: -> (?P<new>.+))?$")
DIFF_STAT_RE = re.compile(r"(?m)^\s*(?P<path>[^|\n]+?)\s+\|\s+\d+")
DIFF_GIT_RE = re.compile(r"(?m)^diff --git a/(?P<a>.+?) b/(?P<b>.+)$")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,95}")
SMALL_FILE_LIMIT = 8

@dataclass
class Decision:
    augment: bool
    reason: str
    tokens: list[str]
    files: list[str]
    command_kind: str

    def to_dict(self) -> dict:
        return asdict(self)


def split_segments(command: str) -> list[str]:
    """Split on common shell separators while respecting quotes enough for observed sessions."""
    parts: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    esc = False
    i = 0
    while i < len(command):
        ch = command[i]
        if esc:
            buf.append(ch); esc = False; i += 1; continue
        if ch == "\\":
            buf.append(ch); esc = True; i += 1; continue
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1; continue
        if ch in "'\"`":
            quote = ch; buf.append(ch); i += 1; continue
        if command.startswith("&&", i) or command.startswith("||", i):
            part = "".join(buf).strip()
            if part: parts.append(part)
            buf = []; i += 2; continue
        if ch in ";|":
            part = "".join(buf).strip()
            if part: parts.append(part)
            buf = []; i += 1; continue
        buf.append(ch); i += 1
    part = "".join(buf).strip()
    if part: parts.append(part)
    return parts


def shell_words(segment: str) -> list[str]:
    try:
        return shlex.split(segment, posix=True)
    except ValueError:
        # Good enough fallback for malformed/truncated commands.
        return re.findall(r"'[^']*'|\"[^\"]*\"|\S+", segment)


def normalize_path(path: str) -> str | None:
    p = path.strip().strip("'\"`")
    if " -> " in p:
        p = p.split(" -> ")[-1]
    p = p.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if p.startswith("/app/"):
        p = p[5:]
    if p.startswith("a/") or p.startswith("b/"):
        p = p[2:]
    if p.startswith("/") or ".." in p.split("/"):
        return None
    if any(part in p for part in SKIP_PATH_PARTS):
        return None
    if not SOURCE_EXT_RE.search(p):
        return None
    return p


def extract_output_files(output: str, include_tests: bool = False) -> Counter[str]:
    files: Counter[str] = Counter()
    for rx, group in [
        (PATH_COLON_RE, "path"),
        (BARE_PATH_RE, "path"),
        (GIT_STATUS_RE, "new"),
        (DIFF_STAT_RE, "path"),
        (DIFF_GIT_RE, "b"),
    ]:
        for m in rx.finditer(output or ""):
            raw = m.groupdict().get(group) or m.groupdict().get("path") or m.groupdict().get("b")
            p = normalize_path(raw or "")
            if not p:
                continue
            if not include_tests and TEST_PATH_RE.search(p):
                continue
            files[p] += 1
    return files


def extract_command_files(command: str, include_tests: bool = False) -> Counter[str]:
    """Source-file operands from the command itself, e.g. `grep pat file.py`.

    Output parsing misses single-file grep because GNU grep prints `line:text`,
    not `path:line:text`. Command operands fill that gap.
    """
    files: Counter[str] = Counter()
    for seg in split_segments(command[:4000]):
        for w in shell_words(seg):
            if any(ch in w for ch in "*$(){}[]"):
                continue
            p = normalize_path(w)
            if not p:
                continue
            if not include_tests and TEST_PATH_RE.search(p):
                continue
            files[p] += 1
    return files


def is_option_taking_pattern(cmd: str, opt: str) -> bool:
    return cmd in {"grep", "egrep", "fgrep", "rg", "ripgrep", "git grep"} and opt in {"-e", "--regexp"}


def extract_patterns_from_words(words: list[str]) -> list[str]:
    if not words:
        return []
    cmd = words[0]
    start = 1
    if len(words) >= 2 and words[0] == "git" and words[1] == "grep":
        cmd = "git grep"; start = 2
    elif cmd not in {"grep", "egrep", "fgrep", "rg", "ripgrep"}:
        # xargs grep -n PATTERN, env FOO=1 rg PATTERN, etc.
        for i, w in enumerate(words):
            if w in {"grep", "egrep", "fgrep", "rg", "ripgrep"}:
                cmd = w; start = i + 1; break
        else:
            return []

    patterns: list[str] = []
    i = start
    while i < len(words):
        w = words[i]
        if is_option_taking_pattern(cmd, w):
            if i + 1 < len(words):
                patterns.append(words[i + 1])
            i += 2; continue
        if w.startswith("--regexp="):
            patterns.append(w.split("=", 1)[1]); i += 1; continue
        if w == "--":
            i += 1
            if i < len(words): patterns.append(words[i])
            break
        if w.startswith("-"):
            # Skip common options plus their argument when needed.
            if w in {"-g", "--glob", "--include", "--exclude", "--exclude-dir", "-m", "-A", "-B", "-C", "--context"} and i + 1 < len(words):
                i += 2
            else:
                i += 1
            continue
        patterns.append(w)
        break
    return patterns


def token_score(tok: str) -> tuple[int, int, int]:
    camel = 1 if re.search(r"[a-z][A-Z]|[A-Z][a-z]", tok) else 0
    snake = 1 if "_" in tok else 0
    allcaps = 1 if tok.isupper() and len(tok) <= 5 else 0
    return (camel + snake - allcaps, len(tok), 0)


def tokens_from_patterns(patterns: Iterable[str], limit: int = 5) -> list[str]:
    seen: set[str] = set()
    toks: list[str] = []
    for pat in patterns:
        # Normalize common grep alternation escaping so every branch can become a token.
        expanded = pat.replace("\\|", "|")
        for tok in IDENT_RE.findall(expanded):
            if tok in seen:
                continue
            if tok.lower() in NOISE_TOKENS:
                continue
            # Drop pure extension/file globs and very plain lowercase words unless long enough.
            if tok.islower() and len(tok) < 7:
                continue
            seen.add(tok); toks.append(tok)
    toks.sort(key=token_score, reverse=True)
    return toks[:limit]


def classify_command(command: str) -> tuple[str, list[str]]:
    if VALIDATION_RE.search(command):
        return "skip_validation_or_mutation", []
    patterns: list[str] = []
    saw_search = False
    saw_find_xargs_grep = False
    for seg in split_segments(command[:4000]):
        words = shell_words(seg)
        if not words:
            continue
        joined = " ".join(words)
        if SEARCH_VERB_RE.search(joined):
            saw_search = True
            patterns.extend(extract_patterns_from_words(words))
        if "xargs" in words and any(w in {"grep", "rg", "ripgrep"} for w in words):
            saw_find_xargs_grep = True
            patterns.extend(extract_patterns_from_words(words))
    if saw_search or saw_find_xargs_grep:
        return "search", patterns
    if DISCOVERY_ONLY_RE.search(command):
        return "skip_listing_no_pattern", []
    return "skip_other", []


def decide(command: str, output: str = "") -> Decision:
    kind, patterns = classify_command(command)
    file_counts = extract_output_files(output)
    file_counts.update(extract_command_files(command))
    all_files = [p for p, _ in file_counts.most_common()]
    files = all_files[:SMALL_FILE_LIMIT]

    if kind == "search":
        tokens = tokens_from_patterns(patterns)
        if tokens and DEPENDENCY_MANIFEST_RE.search(command) and not all_files:
            return Decision(False, "skip_dependency_manifest_search", [], files, kind)
        if tokens:
            return Decision(True, "search_with_tokens", tokens, files, kind)
        if all_files:
            return Decision(True, "search_file_output", [], files, kind)
        return Decision(False, "search_no_good_token", [], files, kind)

    if kind == "skip_listing_no_pattern" and 0 < len(all_files) <= SMALL_FILE_LIMIT:
        return Decision(True, "listing_small_file_output", [], files, kind)

    return Decision(False, kind, [], files, kind)


if __name__ == "__main__":
    import sys, json
    cmd = " ".join(sys.argv[1:])
    print(json.dumps(decide(cmd).to_dict(), indent=2))

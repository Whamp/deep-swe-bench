#!/usr/bin/env python3
"""Independent-ish golden label builder for the CMB bash-hook prototype.

This intentionally does NOT import prototype_parser. It labels real bash calls by
brute-force command/output evidence:
- grep-like command with code-looking search identifiers => token target
- grep/search output naming source files => file target
- small file listing naming source files => file target
- validation/build/mutation commands => negative

The result is still heuristic, not human truth, but it is less circular than
scoring the prototype against itself.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

SOURCE_EXT_RE = re.compile(r"\.(py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs)$")
TEST_PATH_RE = re.compile(r"(^|/)(__tests__|tests?|testdata|fixtures?)(/|$)|(_test\.go|\.test\.[tj]sx?$|\.spec\.[tj]sx?$|test_.*\.py$|_test\.rs$)")
SKIP_PATH_PARTS = (".git/", "node_modules/", "vendor/", "dist/", "build/", "target/", ".cache/", "__pycache__/", "site-packages/", ".venv/")
VALIDATION_OR_MUTATION_RE = re.compile(
    r"\b(go\s+test|go\s+build|cargo\s+(test|check|build)|pytest|python\s+-m\s+pytest|"
    r"npm\s+(test|run)|npx\s+(tsc|jest|vitest)|pnpm|yarn|make|gofmt|ruff|mypy|"
    r"git\s+(add|commit|checkout|push|pull|merge|rebase|stash|clean|reset)|"
    r"pip\s+install|poetry|uv\s+)\b"
)
GREPISH_RE = re.compile(r"\b(git\s+grep|grep|egrep|fgrep|rg|ripgrep)\b")
LISTING_RE = re.compile(r"\b(find|fd|ls|tree)\b")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{3,95}")
QUOTED_RE = re.compile(r"(['\"])(.*?)\1")
WORD_RE = re.compile(r"'[^']*'|\"[^\"]*\"|\S+")
PATH_COLON_RE = re.compile(r"(?m)^(?:\x1b\[[0-9;]*m)*(?P<path>[^:\n\r]+?):(?P<line>\d+)(?::\d+)?:")
BARE_PATH_RE = re.compile(r"(?m)^\s*(?:\./)?(?P<path>[A-Za-z0-9_./@+\-]+\.(?:py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs))\s*$")
GIT_STATUS_RE = re.compile(r"(?m)^[ MARCUD!?]{1,2}\s+(?P<path>.+?)(?: -> (?P<new>.+))?$")
DIFF_STAT_RE = re.compile(r"(?m)^\s*(?P<path>[^|\n]+?)\s+\|\s+\d+")
DIFF_GIT_RE = re.compile(r"(?m)^diff --git a/(?P<a>.+?) b/(?P<b>.+)$")

STOP = {
    "grep", "egrep", "fgrep", "find", "xargs", "head", "tail", "sort", "uniq", "sed", "awk",
    "case", "switch", "type", "name", "path", "maxdepth", "mindepth", "class", "def", "func",
    "struct", "impl", "const", "import", "from", "return", "true", "false", "null", "none",
    "schema", "config", "package", "index", "main", "src", "pkg", "test", "tests", "file", "files",
}
SMALL_FILE_LIMIT = 8


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
    if TEST_PATH_RE.search(p):
        return None
    if not SOURCE_EXT_RE.search(p):
        return None
    return p


def command_files(command: str) -> list[str]:
    c: Counter[str] = Counter()
    for raw in WORD_RE.findall(command[:4000]):
        if any(ch in raw for ch in "*$(){}[]"):
            continue
        p = normalize_path(raw)
        if p:
            c[p] += 1
    return [p for p, _ in c.most_common()]


def output_files(output: str) -> list[str]:
    c: Counter[str] = Counter()
    for rx, group in [(PATH_COLON_RE, "path"), (BARE_PATH_RE, "path"), (GIT_STATUS_RE, "new"), (DIFF_STAT_RE, "path"), (DIFF_GIT_RE, "b")]:
        for m in rx.finditer(output or ""):
            gd = m.groupdict()
            raw = gd.get(group) or gd.get("path") or gd.get("b")
            p = normalize_path(raw or "")
            if p:
                c[p] += 1
    return [p for p, _ in c.most_common()]


def command_text_candidates(command: str) -> list[str]:
    # Independent but conservative: quoted search strings are the real pattern in
    # observed sessions. Avoid mining path operands as fake symbol tokens.
    if not GREPISH_RE.search(command):
        return []
    vals = [m.group(2) for m in QUOTED_RE.finditer(command) if m.group(2)]
    if vals:
        return vals
    for m in GREPISH_RE.finditer(command):
        tail = re.split(r"[|;&]", command[m.end(): m.end() + 160], 1)[0]
        # Fallback only to the first non-option, non-path word.
        for raw in WORD_RE.findall(tail):
            w = raw.strip("'\"`")
            if not w or w.startswith("-") or "/" in w or "." in w:
                continue
            vals.append(w)
            return vals
    return vals


def gold_tokens(command: str) -> list[str]:
    seen: set[str] = set()
    toks: list[str] = []
    for text in command_text_candidates(command):
        text = text.replace("\\|", "|")
        for tok in IDENT_RE.findall(text):
            low = tok.lower()
            if low in STOP:
                continue
            if tok.islower() and len(tok) < 7:
                continue
            if tok in seen:
                continue
            seen.add(tok)
            toks.append(tok)
    toks.sort(key=lambda t: ((1 if re.search(r"[a-z][A-Z]|[A-Z][a-z]|_", t) else 0), len(t)), reverse=True)
    return toks[:8]


def label(sample: dict[str, Any]) -> dict[str, Any]:
    cmd = sample["command"]
    out = sample.get("output", "")
    merged = Counter(output_files(out))
    merged.update(command_files(cmd))
    files = [p for p, _ in merged.most_common()]
    toks = gold_tokens(cmd)
    validation = bool(VALIDATION_OR_MUTATION_RE.search(cmd))
    grepish = bool(GREPISH_RE.search(cmd))
    listing = bool(LISTING_RE.search(cmd))

    reasons: list[str] = []
    if not validation and grepish and toks:
        reasons.append("grep_tokens")
    if not validation and grepish and files:
        reasons.append("grep_output_files")
    if not validation and (not grepish) and listing and 0 < len(files) <= SMALL_FILE_LIMIT:
        reasons.append("small_listing_files")

    return {
        "id": sample["id"],
        "positive": bool(reasons),
        "reason": "+".join(reasons) if reasons else "negative",
        "tokens": toks,
        "files": files[:SMALL_FILE_LIMIT],
        "all_file_count": len(files),
    }


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("samples")
    ap.add_argument("out")
    args = ap.parse_args()
    with open(args.samples) as f, open(args.out, "w") as o:
        for line in f:
            if line.strip():
                o.write(json.dumps(label(json.loads(line))) + "\n")

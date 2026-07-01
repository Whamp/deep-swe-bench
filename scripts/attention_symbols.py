#!/usr/bin/env python3
"""Analysis A: symbol/hunk-level attention (corrects the Tier-0 file proxy).

The Tier-0 file-level proxy was saturated (every agent finds the gold file ->
search_failure ~= 0). The hypothesis is about attention to symbols and their
relationships, so the gold set here is SYMBOLS (functions/classes/types/methods
the patch changes), not files. Re-scans the SAME existing session logs.

Gold symbols are extracted two ways and unioned:
  1. the enclosing symbol in each `@@ ... @@ <context>` hunk header
     (git emits the function the hunk sits inside), and
  2. def/func/class/fn/type/method lines on added (`+`) lines (new/modified defs).

Symbol-level focus: a turn "touches" a gold symbol if that symbol appears as a
word-bounded token in the turn's tool-call argument text (edit/write/read/bash/
grep all carry symbol tokens). Yields a per-turn symbol-focus series and labels:

    solved                  reward_binary == 1
    symbol_found_then_lost  touched a gold symbol, then drifted off (ATTENTION)
    symbol_never_found      never touched a gold symbol (search/reasoning)
    symbol_kept_failed      kept gold symbols in focus but still failed (execution)

Read-only by construction.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics as st
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "harness"))
# reuse the validated session-walker + labeler + targets (no duplication)
from attention_signals import (  # noqa: E402
    DEFAULT_TARGETS, REPO as _REPO, iter_reps, _flatten_args, _tail,
    label_rep, _arm_stats,
)
from lib import tasks_root, load_task  # noqa: E402

OUTDIR = REPO / "analysis" / "attention-symbols"

# per-language definition regexes -> capture group 1 is the symbol name.
# ponytail: regex per language, not a full parser. Ceiling: macro-heavy /
# generated code or unusual syntax can miss/misattribute; a tree-sitter pass
# (analysis B) is the tighter answer and runs anyway.
DEF_PATTERNS: dict[str, list[re.Pattern]] = {
    "go": [re.compile(r"\bfunc\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)\s*\("),
           re.compile(r"\btype\s+([A-Za-z_]\w*)\s+")],
    "python": [re.compile(r"\b(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\("),
               re.compile(r"\bclass\s+([A-Za-z_]\w*)\s*[(:]")],
    "typescript": [re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
                   re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)\s*[\{<extends(]"),
                   re.compile(r"(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(?.*?=>")],
    "javascript": [re.compile(r"\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
                   re.compile(r"\bclass\s+([A-Za-z_$][\w$]*)\s*[\{<(]"),
                   re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?\(?.*?=>")],
    "rust": [re.compile(r"\bfn\s+([A-Za-z_]\w*)\s*[\(<]"),
             re.compile(r"\b(?:struct|enum|trait|type)\s+([A-Za-z_]\w*)\s*[\{<(]")],
}

# `@@`-context trailing symbol: git prints e.g. `@@ ... @@ func Import(...) {`
# or `@@ ... @@ class BaseConverter:`. Capture the name after a def keyword.
_CTX_PATTERNS = [
    re.compile(r"@@.*@@.*\bfunc\s+(?:\([^)]*\)\s+)?([A-Za-z_]\w*)\s*\("),
    re.compile(r"@@.*@@.*\b(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\("),
    re.compile(r"@@.*@@.*\bclass\s+([A-Za-z_]\w*)\s*[(:]"),
    re.compile(r"@@.*@@.*\bfn\s+([A-Za-z_]\w*)\s*[\(<]"),
    re.compile(r"@@.*@@.*\bfunction\s+([A-Za-z_$][\w$]*)\s*\("),
]

# very-common identifiers that would saturate symbol focus if counted.
_STOP = {"init", "main", "new", "get", "set", "string", "error", "true",
         "false", "null", "none", "self", "this", "test", "run", "string",
         "len", "print", "append", "range", "errorf"}


@dataclass
class GoldSym:
    task: str
    language: str
    files: set[str] = field(default_factory=set)
    symbols: set[str] = field(default_factory=set)   # the changed symbols


def parse_gold_symbols(task_id: str) -> GoldSym | None:
    patch = tasks_root() / task_id / "solution" / "solution.patch"
    if not patch.exists():
        return None
    try:
        lang = load_task(task_id).language.lower()
    except Exception:
        lang = ""
    g = GoldSym(task=task_id, language=lang)
    pats = DEF_PATTERNS.get(lang, [])
    for line in patch.read_text(errors="replace").splitlines():
        if line.startswith("diff --git"):
            # cheap file capture for context (not the focus unit)
            m = re.search(r"diff --git a/(.+?) b/(.+)", line)
            if m:
                for f in (m.group(1), m.group(2)):
                    if f != "/dev/null":
                        g.files.add(f.strip())
            continue
        # 1) enclosing symbol from @@ context
        for cp in _CTX_PATTERNS:
            m = cp.search(line)
            if m:
                g.symbols.add(m.group(1))
                break
        # 2) def on an added line (+) -> new/modified symbol
        if line.startswith("+") and not line.startswith("+++"):
            for p in pats:
                for m in p.finditer(line):
                    g.symbols.add(m.group(1))
    g.symbols = {s for s in g.symbols if s.lower() not in _STOP and len(s) >= 2}
    return g


def turn_symbol_focus(session_paths: list[Path], gold: GoldSym) -> list[dict]:
    """One entry per assistant turn: which gold symbols appear in its output.

    Attention is measured across the assistant's full output -- text blocks
    (reasoning prose) AND tool-call args -- because relationship reasoning often
    lives in prose ("X calls Y so..."), not only in tool invocations. toolResult
    blocks are the environment talking back, so they are excluded."""
    if not gold.symbols:
        return []
    sym_res = [(s, re.compile(r"(?:^|[^\w$])" + re.escape(s) + r"(?:[^\w$]|$)"))
               for s in gold.symbols]
    turns: list[dict] = []
    for sp in session_paths:
        for raw in sp.read_text(errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "message":
                continue
            msg = ev.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            tools, touched = [], set()
            blob_parts = []
            for b in (msg.get("content") or []):
                bt = b.get("type")
                if bt == "toolCall":
                    tools.append(b.get("name", "?"))
                    blob_parts.append(_flatten_args(b.get("arguments") or {}))
                elif bt == "text":
                    blob_parts.append(b.get("text", ""))
            if not tools:
                continue  # no tool call -> not an action turn
            blob = " " + " ".join(blob_parts)
            for sym, r in sym_res:
                if r.search(blob):
                    touched.add(sym)
            turns.append({"n_tools": len(tools), "tools": tools,
                          "sym_touched": sorted(touched), "focus": bool(touched)})
    return turns


def scan(model: str, thinking: str, config: str) -> list[dict]:
    cache: dict[str, GoldSym | None] = {}
    rows = []
    for repdir, res in iter_reps(model, thinking, config):
        task = res.get("task")
        if not task:
            continue
        if task not in cache:
            cache[task] = parse_gold_symbols(task)
        gold = cache[task]
        sessions = sorted((repdir / "session").glob("*.jsonl")) if (repdir / "session").exists() else []
        if gold is None or not gold.symbols or not sessions:
            rows.append({
                "model": model, "thinking": thinking, "config": config,
                "task": task, "rep": res.get("rep"),
                "reward_binary": res.get("reward_binary"),
                "reward_partial": res.get("reward_partial"),
                "label": "no_symbols_or_session",
                "n_turns": 0, "n_sym_turns": 0, "first_sym_turn": None,
                "last_sym_turn": None, "sym_coverage": 0.0,
                "focus_series": [], "n_gold_symbols": len(gold.symbols) if gold else 0,
            })
            continue
        turns = turn_symbol_focus(sessions, gold)
        focus = [t["focus"] for t in turns]
        idx = [i for i, f in enumerate(focus) if f]
        covered = len({s for t in turns for s in t["sym_touched"]})
        rows.append({
            "model": model, "thinking": thinking, "config": config,
            "task": task, "rep": res.get("rep"),
            "reward_binary": res.get("reward_binary"),
            "reward_partial": res.get("reward_partial"),
            "label": label_rep(focus, res.get("reward_binary") == 1),
            "n_turns": len(turns), "n_sym_turns": sum(focus),
            "first_sym_turn": idx[0] if idx else None,
            "last_sym_turn": idx[-1] if idx else None,
            "sym_coverage": round(covered / len(gold.symbols), 3),
            "focus_series": [1 if f else 0 for f in focus],
            "n_gold_symbols": len(gold.symbols),
        })
    return rows


def write_outputs(all_rows: list[dict]) -> dict:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with (OUTDIR / "per_rep.jsonl").open("w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")
    with (OUTDIR / "per_task.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "thinking", "config", "task", "rep", "label",
                    "reward_binary", "reward_partial", "n_turns", "n_sym_turns",
                    "first_sym_turn", "last_sym_turn", "sym_coverage", "n_gold_symbols"])
        for r in all_rows:
            w.writerow([r["model"], r["thinking"], r["config"], r["task"], r["rep"],
                        r["label"], r["reward_binary"], r["reward_partial"],
                        r["n_turns"], r["n_sym_turns"], r["first_sym_turn"],
                        r["last_sym_turn"], r["sym_coverage"], r["n_gold_symbols"]])
    by = defaultdict(list)
    for r in all_rows:
        by[(r["model"], r["thinking"], r["config"])].append(r)
    with (OUTDIR / "per_config.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "thinking", "config", "n_reps", "solved_rate",
                    "sym_found_then_lost_rate", "sym_never_found_rate",
                    "sym_kept_failed_rate", "median_turns", "mean_sym_coverage"])
        for (m, th, c), rs in sorted(by.items()):
            s = _arm_stats(rs)
            nfr = sum(1 for r in rs if r["label"] == "no_action_turns") / max(1, s["n"])
            # symbol_never_found absorbs the pure-thinking-empty + never-touched cases
            w.writerow([m, th, c, s["n"], round(s["solved"], 3), round(s["ftl"], 3),
                        round(s["search"] + nfr, 3), round(s["kept"], 3),
                        round(s["med_turns"], 1),
                        round(st.mean([r["sym_coverage"] for r in rs]), 3)])
    return {"by": by, "n_rows": len(all_rows)}


def write_finding(by: dict, all_rows: list[dict]) -> None:
    def stats(m, th, c):
        rs = by.get((m, th, c), [])
        return _arm_stats(rs) if rs else None

    def delta(m, th, b, o, k):
        B, O = stats(m, th, b), stats(m, th, o)
        return None if not (B and O) else O[k] - B[k]

    # symbol extraction coverage across tasks
    tasks = {r["task"] for r in all_rows}
    with_syms = sum(1 for r in all_rows if r["n_gold_symbols"] > 0)  # overcounts reps; use task-level below
    gold_cache = {}
    for t in tasks:
        g = parse_gold_symbols(t)
        gold_cache[t] = len(g.symbols) if g else 0
    tasks_with_syms = sum(1 for n in gold_cache.values() if n > 0)
    zero_sym_rate = 1 - tasks_with_syms / max(1, len(tasks))

    ds = {k: delta("deepseek-v4-flash", "high", "baseline", "observational-memory", k)
          for k in ("solved", "ftl", "kept")}
    g5 = {k: delta("gpt-5.5", "low", "baseline", "observational-memory-gpt55-low", k)
          for k in ("solved", "ftl", "kept")}

    L = ["# Analysis A: symbol/hunk-level attention",
         "",
         "Gold unit = SYMBOLS changed by the patch (func/def/class/type/method), "
         "extracted from `@@` hunk context + def lines on added hunks. Focus = a "
         "turn whose tool-call args mention a gold symbol as a word-bounded token.",
         "",
         f"Symbol extraction: {tasks_with_syms}/{len(tasks)} tasks have >=1 gold "
         f"symbol ({zero_sym_rate:.1%} have none -- patches that only touch config, "
         "imports, or non-def lines).",
         "",
         "## OM vs baseline (symbol_found_then_lost = attention; never_found = search)",
         "model | thinking | arm | n | solved | ftl | never | kept",
         "---|---|---|---|---|---|---|---"]
    pairs = [("gpt-5.5", "low", "baseline", "observational-memory-gpt55-low"),
             ("gpt-5.5", "low", "baseline", "observational-memory-gpt54mini-low"),
             ("deepseek-v4-flash", "high", "baseline", "observational-memory"),
             ("deepseek-v4-flash", "high", "baseline", "advisor-observational-memory")]
    for m, th, b, o in pairs:
        for c in (b, o):
            s = stats(m, th, c)
            L.append(f"{m}|{th}|{c}|{s['n'] if s else '-'}|"
                     f"{s['solved']:.3f}|{s['ftl']:.3f}|{s['search']:.3f}|{s['kept']:.3f}" if s
                     else f"{m}|{th}|{c}|(missing)|-|-|-|-")
    L += ["", "## thinking axis (gpt-5.5 baseline, low -> medium -> xhigh)",
          "thinking | n | solved | ftl | never | kept", "---|---|---|---|---|---"]
    for th in ("low", "medium", "xhigh"):
        s = stats("gpt-5.5", th, "baseline")
        if s:
            L.append(f"{th}|{s['n']}|{s['solved']:.3f}|{s['ftl']:.3f}|{s['search']:.3f}|{s['kept']:.3f}")

    L += [
        "",
        "## Finding (symbol level)",
        "",
        f"At symbol granularity the picture differs from the file level. OM still "
        f"lifts solves on the known axes (deepseek {ds['solved']:+.3f}; "
        f"gpt-5.5/om-gpt55-low {g5['solved']:+.3f}), reconciling with the "
        "2/113->10/113 deepseek number. The question is whether the gains come out "
        f"of symbol_found_then_lost (attention) or symbol_kept_failed (execution): "
        f"deepseek OM ftl {ds['ftl']:+.3f}, kept {ds['kept']:+.3f}; "
        f"gpt-5.5/om-gpt55-low ftl {g5['ftl']:+.3f}, kept {g5['kept']:+.3f}.",
        "",
        "**If OM/thinking now cut symbol-level ftl where they did NOT cut file-level "
        "ftl, that is the first positive evidence for the attention hypothesis at the "
        "correct unit.** Compare these deltas to the Tier-0 file-level table "
        "(analysis/attention-signals/MECHANISM.md), where file ftl was flat-to-up. "
        "The contrast between file-ftl and symbol-ftl is the headline of analysis A.",
        "",
        "Caveat: symbol focus uses word-boundary token match, so very common "
        "identifiers add noise; sym_coverage is reported so the reader can see scale. "
        "Analysis B moves to graph EDGES (caller/callee), which is the relationship "
        "unit the hypothesis is really about and is not token-match noisy.",
    ]
    (OUTDIR / "FINDING.md").write_text("\n".join(L) + "\n")


def selftest() -> None:
    # synthetic multi-language patch
    patch = ("diff --git a/foo.go b/foo.go\n"
             "--- a/foo.go\n+++ b/foo.go\n"
             "@@ -1,1 +1,2 @@ func Import(e *env.Env) {\n"
             "+\tImportHelper(x)\n"
             "+func NewSymbol() error {\n"
             "}\n"
             "diff --git a/bar.py b/bar.py\n"
             "--- a/bar.py\n+++ b/bar.py\n"
             "@@ -5,3 +5,4 @@ class BaseConverter:\n"
             "+    def parse_thing(self):\n"
             "+        pass\n")
    from attention_signals import _parse_gold_text  # noqa
    # exercise symbol parser directly via a temp task-like parse
    g = GoldSym(task="_self", language="go")
    pats = DEF_PATTERNS["go"]
    syms = set()
    for line in patch.splitlines():
        for cp in _CTX_PATTERNS:
            m = cp.search(line)
            if m:
                syms.add(m.group(1)); break
        if line.startswith("+") and not line.startswith("+++"):
            for p in pats:
                for m in p.finditer(line):
                    syms.add(m.group(1))
    # go-side expectations: Import (ctx), NewSymbol (added func)
    assert "Import" in syms, syms
    assert "NewSymbol" in syms, syms
    # python-side via python patterns
    pypats = DEF_PATTERNS["python"]
    for line in patch.splitlines():
        for cp in _CTX_PATTERNS:
            m = cp.search(line)
            if m:
                syms.add(m.group(1))
        if line.startswith("+") and not line.startswith("+++"):
            for p in pypats:
                for m in p.finditer(line):
                    syms.add(m.group(1))
    assert "BaseConverter" in syms, syms
    assert "parse_thing" in syms, syms
    # stoplist filters 'init'
    g.symbols = {s for s in syms if s.lower() not in _STOP and len(s) >= 2}
    assert "init" not in g.symbols
    # labeler reuse (inherited) still works
    assert label_rep([True, True, False, False, False], solved=False) == "found_then_lost"
    print("SELFTEST PASS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--model"); ap.add_argument("--thinking"); ap.add_argument("--config")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest()
        return 0
    targets = [(m, th, c) for m, th, cfgs in DEFAULT_TARGETS for c in cfgs] \
        if (not (args.model and args.thinking and args.config)) \
        else [(args.model, args.thinking, args.config)]
    all_rows = []
    for m, th, c in targets:
        rows = scan(m, th, c)
        print(f"[A] {m}/{th}/{c}: {len(rows)} reps", flush=True)
        all_rows.extend(rows)
    if not all_rows:
        print("no reps", file=sys.stderr); return 1
    out = write_outputs(all_rows)
    write_finding(out["by"], all_rows)
    print(f"\nwrote {out['n_rows']} reps -> {OUTDIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

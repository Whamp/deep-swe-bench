#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import math
import re
from collections import Counter, defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-historical-corpus"
OUT_JSON = ANALYSIS_DIR / "prompt_discordant_audit.json"
OUT_HTML = ROOT / "reports/gpt55-low-prompt-discordant-audit/index.html"
RESULT_ROOT = ROOT / "results/gpt-5.5/low"
PROMPT_SHAPED = ANALYSIS_DIR / "prompt_shaped_neighbor_divergence.json"
CORPUS = ANALYSIS_DIR / "corpus_overlap_vs_clean_low.json"

PAIR_SPECS = [
    ("workflow_checklist_vs_clean", "baseline", "baseline-wf-only", "Does the checklist beat clean low?"),
    ("engineer_preamble_vs_clean", "baseline", "baseline-preamble-only", "Does the generic engineer preamble beat clean low?"),
    ("checklist_vs_preamble_plus_checklist", "baseline-preamble-orchestration-wf", "baseline-wf-only", "Does adding the preamble to the checklist hurt?"),
    ("preamble_vs_preamble_plus_neutral", "baseline-preamble-orchestration", "baseline-preamble-only", "Does neutral orchestration change preamble behavior?"),
]

TEST_RE = re.compile(r"\b(go test|pytest|cargo test|npm (run )?test|pnpm (run )?test|yarn test|vitest|jest|mocha|rspec|phpunit|mvn test|gradle test|make test|ctest|tox|ruff|eslint|tsc|mypy)\b", re.I)
SEARCH_RE = re.compile(r"\b(rg|grep|git grep|find|fd|ls|tree)\b", re.I)
REPRO_RE = re.compile(r"(repro|reproduce|regression|minimal|scratch|tmp|node\s+-\s*<<|python\s+-\s*<<|ruby\s+-\s*<<|cat\s+>\s*/tmp|cat\s+>\s+.*test|tee\s+.*test)", re.I)
COMMIT_RE = re.compile(r"\bgit\s+commit\b", re.I)
BRANCH_RE = re.compile(r"\bgit\s+(checkout\s+-b|switch\s+-c)\b", re.I)


def e(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float | None) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.2f}"


def pct(value: float | None) -> str:
    return "—" if value is None else f"{value:+.1%}"


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def solved(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") == 1


def result_cost(row: dict[str, Any]) -> float:
    return float(row.get("combined_cost_usd", row.get("cost_usd", 0.0)) or 0.0)


def result_tokens(row: dict[str, Any]) -> int:
    return int(row.get("combined_total_tokens", row.get("total_tokens", 0)) or 0)


@lru_cache(maxsize=None)
def cell_map(config: str) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    base = RESULT_ROOT / config
    for result_path in base.glob("*/rep*/result.json"):
        try:
            row = load_json(result_path)
        except Exception:
            continue
        key = f"{result_path.parts[-3]}/{result_path.parts[-2]}"
        row["_result_path"] = str(result_path.relative_to(ROOT))
        row["_cell_dir"] = result_path.parent
        out[key] = row
    return out


def tool_calls_from_session(cell_dir: Path) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    sessions = sorted((cell_dir / "session").glob("*.jsonl"))
    for session in sessions:
        with session.open(errors="replace") as f:
            for line in f:
                try:
                    event = json.loads(line)
                except Exception:
                    continue
                msg = event.get("message") or {}
                if msg.get("role") != "assistant":
                    continue
                for part in msg.get("content") or []:
                    if part.get("type") == "toolCall":
                        calls.append({
                            "name": part.get("name"),
                            "arguments": part.get("arguments") or {},
                            "event_id": event.get("id"),
                            "timestamp": event.get("timestamp"),
                        })
    return calls


def patch_changed_files(cell_dir: Path) -> list[str]:
    patch = cell_dir / "artifacts/model.patch"
    if not patch.exists():
        return []
    files = []
    for line in patch.read_text(errors="replace").splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3][2:] if parts[3].startswith("b/") else parts[3])
    return files


def features(row: dict[str, Any]) -> dict[str, Any]:
    cell_dir = Path(row["_cell_dir"])
    calls = tool_calls_from_session(cell_dir)
    bash_commands: list[str] = []
    read_paths: list[str] = []
    edit_paths: list[str] = []
    write_paths: list[str] = []
    for call in calls:
        name = call.get("name")
        args = call.get("arguments") or {}
        if name == "bash":
            cmd = str(args.get("command") or "")
            bash_commands.append(cmd)
        elif name == "read":
            read_paths.append(str(args.get("path") or ""))
        elif name == "edit":
            edit_paths.append(str(args.get("path") or ""))
        elif name == "write":
            write_paths.append(str(args.get("path") or ""))
    changed = patch_changed_files(cell_dir)
    test_files = [p for p in changed if re.search(r"(test|spec|__tests__|tests?)/|(_test|\.test|\.spec)\.", p, re.I)]
    search_commands = [c for c in bash_commands if SEARCH_RE.search(c)]
    test_commands = [c for c in bash_commands if TEST_RE.search(c)]
    repro_commands = [c for c in bash_commands if REPRO_RE.search(c)]
    repro_paths = [p for p in write_paths + edit_paths + changed if REPRO_RE.search(p)]
    return {
        "reward_binary": row.get("reward_binary"),
        "reward_partial": row.get("reward_partial"),
        "solved": solved(row),
        "agent_exit": row.get("agent_exit"),
        "verifier_exit": row.get("verifier_exit"),
        "agent_timed_out": bool(row.get("agent_timed_out")),
        "turns": int(row.get("turns") or 0),
        "tool_calls": int(row.get("tool_calls") or 0),
        "cost_usd": result_cost(row),
        "tokens": result_tokens(row),
        "patch_bytes": int(row.get("patch_bytes") or 0),
        "agent_wall_s": float(row.get("agent_wall_s") or 0.0),
        "f2p": row.get("f2p"),
        "p2p": row.get("p2p"),
        "f2p_passed": row.get("f2p_passed"),
        "f2p_total": row.get("f2p_total"),
        "p2p_passed": row.get("p2p_passed"),
        "p2p_total": row.get("p2p_total"),
        "changed_files": changed,
        "changed_test_files": test_files,
        "bash_count": len(bash_commands),
        "read_count": len(read_paths),
        "edit_count": len(edit_paths),
        "write_count": len(write_paths),
        "search_command_count": len(search_commands),
        "test_command_count": len(test_commands),
        "repro_signal_count": len(repro_commands) + len(repro_paths),
        "commit_command_count": sum(1 for c in bash_commands if COMMIT_RE.search(c)),
        "branch_command_count": sum(1 for c in bash_commands if BRANCH_RE.search(c)),
        "sample_bash_commands": bash_commands[:10],
        "sample_test_commands": test_commands[:6],
        "sample_repro_commands": repro_commands[:6],
        "sample_read_paths": read_paths[:10],
        "sample_edit_paths": edit_paths[:10],
        "sample_write_paths": write_paths[:10],
        "result_path": row["_result_path"],
    }


def rel_delta(w: float, l: float) -> float | None:
    if l == 0:
        return None if w == 0 else math.inf
    return (w - l) / l


def classify(winner_features: dict[str, Any], loser_features: dict[str, Any]) -> list[str]:
    labels: list[str] = []
    if winner_features["repro_signal_count"] > loser_features["repro_signal_count"]:
        labels.append("winner_more_repro_signal")
    if winner_features["test_command_count"] > loser_features["test_command_count"]:
        labels.append("winner_more_verification")
    if winner_features["search_command_count"] + winner_features["read_count"] > 1.3 * max(1, loser_features["search_command_count"] + loser_features["read_count"]):
        labels.append("winner_more_localization")
    if loser_features["cost_usd"] > 1.25 * max(0.01, winner_features["cost_usd"]):
        labels.append("loser_cost_blowup")
    if loser_features["tokens"] > 1.25 * max(1, winner_features["tokens"]):
        labels.append("loser_token_blowup")
    if loser_features["turns"] > 1.25 * max(1, winner_features["turns"]):
        labels.append("loser_turn_blowup")
    if winner_features["patch_bytes"] and loser_features["patch_bytes"] and winner_features["patch_bytes"] < 0.55 * loser_features["patch_bytes"]:
        labels.append("winner_smaller_patch")
    if loser_features["patch_bytes"] and winner_features["patch_bytes"] and loser_features["patch_bytes"] < 0.25 * winner_features["patch_bytes"]:
        labels.append("loser_tiny_patch")
    if loser_features["agent_exit"] not in (0, None) or loser_features["agent_timed_out"]:
        labels.append("loser_agent_failure")
    if loser_features["verifier_exit"] not in (0, None):
        labels.append("loser_verifier_failure")
    if winner_features["changed_test_files"] and not loser_features["changed_test_files"]:
        labels.append("winner_added_or_touched_tests")
    if not labels:
        labels.append("no_simple_trace_difference")
    return labels


def build_pair(pair_id: str, a: str, b: str, question: str) -> dict[str, Any]:
    ac = cell_map(a)
    bc = cell_map(b)
    keys = sorted(set(ac) & set(bc))
    discordants = []
    both = a_only = b_only = neither = 0
    feature_deltas = Counter()
    winner_feature_sum = Counter()
    loser_feature_sum = Counter()
    all_a_features: list[dict[str, Any]] = []
    all_b_features: list[dict[str, Any]] = []
    for key in keys:
        af = features(ac[key])
        bf = features(bc[key])
        all_a_features.append(af)
        all_b_features.append(bf)
        a_solved = af["solved"]
        b_solved = bf["solved"]
        both += int(a_solved and b_solved)
        a_only += int(a_solved and not b_solved)
        b_only += int(b_solved and not a_solved)
        neither += int((not a_solved) and (not b_solved))
        if a_solved == b_solved:
            continue
        winner = a if a_solved else b
        loser = b if a_solved else a
        wf = af if a_solved else bf
        lf = bf if a_solved else af
        labels = classify(wf, lf)
        feature_deltas.update(labels)
        for name in ["repro_signal_count", "test_command_count", "search_command_count", "read_count", "turns", "tool_calls", "cost_usd", "tokens", "patch_bytes"]:
            winner_feature_sum[name] += wf[name]
            loser_feature_sum[name] += lf[name]
        discordants.append({
            "cell": key,
            "winner": winner,
            "loser": loser,
            "labels": labels,
            "winner_features": wf,
            "loser_features": lf,
            "a_config": a,
            "b_config": b,
            "a_solved": a_solved,
            "b_solved": b_solved,
            "a_features": af,
            "b_features": bf,
        })
    def avg(items: list[dict[str, Any]], field: str) -> float:
        return sum(float(x[field]) for x in items) / len(items) if items else 0.0
    def avg_disc(counter: Counter, field: str) -> float:
        return counter[field] / len(discordants) if discordants else 0.0
    return {
        "pair_id": pair_id,
        "question": question,
        "a_config": a,
        "b_config": b,
        "cells": len(keys),
        "a_solves": both + a_only,
        "b_solves": both + b_only,
        "both": both,
        "a_only": a_only,
        "b_only": b_only,
        "neither": neither,
        "discordant_cells": len(discordants),
        "discordant_label_counts": dict(feature_deltas),
        "discordant_winner_avg": {k: round(avg_disc(winner_feature_sum, k), 3) for k in winner_feature_sum},
        "discordant_loser_avg": {k: round(avg_disc(loser_feature_sum, k), 3) for k in loser_feature_sum},
        "all_a_avg": {
            "turns": round(avg(all_a_features, "turns"), 3),
            "tool_calls": round(avg(all_a_features, "tool_calls"), 3),
            "cost_usd": round(avg(all_a_features, "cost_usd"), 6),
            "tokens": round(avg(all_a_features, "tokens"), 1),
            "test_command_count": round(avg(all_a_features, "test_command_count"), 3),
            "repro_signal_count": round(avg(all_a_features, "repro_signal_count"), 3),
        },
        "all_b_avg": {
            "turns": round(avg(all_b_features, "turns"), 3),
            "tool_calls": round(avg(all_b_features, "tool_calls"), 3),
            "cost_usd": round(avg(all_b_features, "cost_usd"), 6),
            "tokens": round(avg(all_b_features, "tokens"), 1),
            "test_command_count": round(avg(all_b_features, "test_command_count"), 3),
            "repro_signal_count": round(avg(all_b_features, "repro_signal_count"), 3),
        },
        "discordants": discordants,
    }


def synthesize(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    # Focus on the pair that isolates checklist-only vs preamble+checklist and the two clean-baseline gains.
    by_id = {p["pair_id"]: p for p in pairs}
    wf_clean = by_id["workflow_checklist_vs_clean"]
    pre_clean = by_id["engineer_preamble_vs_clean"]
    wf_combo = by_id["checklist_vs_preamble_plus_checklist"]
    pre_neutral = by_id["preamble_vs_preamble_plus_neutral"]
    return {
        "primary_takeaways": [
            "The workflow checklist is the strongest clean-Pi prompt-shaped row, but its evidence is not simply 'more work': across all 108 cells it spends more turns/tokens than clean, while on discordant wins the trace signal is mixed.",
            "The closest prompt-only neighbor pair isolates interference: checklist-only beats preamble+checklist by 35 vs 31 direct solves, even though the combined prompt is semantically very close.",
            "The generic engineer preamble is a real positive signal by aggregate solves, but adding neutral orchestration makes it cheaper and only one solve lower; wording/composition matters as much as semantic cluster membership.",
            "The next config should ablate checklist structure before trying broader prompt optimization: reproduction-script step, commit instruction, and generic preamble layering are the nearest causal questions.",
        ],
        "headline_metrics": {
            "workflow_vs_clean": {k: wf_clean[k] for k in ["a_config", "b_config", "a_solves", "b_solves", "a_only", "b_only", "discordant_cells"]},
            "preamble_vs_clean": {k: pre_clean[k] for k in ["a_config", "b_config", "a_solves", "b_solves", "a_only", "b_only", "discordant_cells"]},
            "checklist_vs_combo": {k: wf_combo[k] for k in ["a_config", "b_config", "a_solves", "b_solves", "a_only", "b_only", "discordant_cells"]},
            "preamble_vs_neutral": {k: pre_neutral[k] for k in ["a_config", "b_config", "a_solves", "b_solves", "a_only", "b_only", "discordant_cells"]},
        },
        "recommended_next_sweep": [
            {
                "name": "workflow-no-repro-script-step",
                "purpose": "Test whether the explicit reproduction-script line drives the checklist lift.",
                "draft_prompt_text_for_approval": "Work through this task step by step:\n\n1. Analyze the codebase by finding and reading relevant files.\n2. Edit the source code to resolve the issue.\n3. Verify your fix works by running the relevant checks.\n4. Test edge cases to ensure your fix is robust.\n5. Commit all of your changes so your work can be captured.",
                "write_config_files": False,
            },
            {
                "name": "workflow-no-commit-step",
                "purpose": "Test whether the benchmark-specific commit instruction is helping/hurting versus the work-order checklist itself.",
                "draft_prompt_text_for_approval": "Work through this task step by step:\n\n1. Analyze the codebase by finding and reading relevant files.\n2. Create a script to reproduce the issue.\n3. Edit the source code to resolve the issue.\n4. Verify your fix works by running your script again.\n5. Test edge cases to ensure your fix is robust.",
                "write_config_files": False,
            },
            {
                "name": "workflow-tight-checklist",
                "purpose": "Test whether a shorter concrete checklist preserves the gain with less prompt/token overhead.",
                "draft_prompt_text_for_approval": "Use a tight fix loop: locate the relevant code, reproduce the issue, make the smallest correct edit, verify it, check one edge case, then commit the result.",
                "write_config_files": False,
            },
        ],
    }


def build() -> dict[str, Any]:
    prompt_shaped = load_json(PROMPT_SHAPED)
    corpus = load_json(CORPUS)
    pairs = [build_pair(*spec) for spec in PAIR_SPECS]
    return {
        "inputs": {
            "corpus_overlap": str(CORPUS.relative_to(ROOT)),
            "prompt_shaped_neighbor_divergence": str(PROMPT_SHAPED.relative_to(ROOT)),
            "result_root": str(RESULT_ROOT.relative_to(ROOT)),
        },
        "prompt_files": {
            "baseline-wf-only": ["configs/baseline-wf-only/orchestration.md"],
            "baseline-preamble-only": ["configs/baseline-preamble-only/system_preamble.md"],
            "baseline-preamble-orchestration": ["configs/baseline-preamble-orchestration/system_preamble.md", "configs/baseline-preamble-orchestration/orchestration.md"],
            "baseline-preamble-orchestration-wf": ["configs/baseline-preamble-orchestration-wf/system_preamble.md", "configs/baseline-preamble-orchestration-wf/orchestration.md"],
        },
        "scope": "clean-Pi prompt-only discordant-cell audit; behavioral wrappers excluded from primary conclusions",
        "note": "Draft prompt text is proposed for approval only; this script does not write config prompt files.",
        "source_summary_counts": {
            "corpus_rows": len(corpus.get("rows", [])),
            "prompt_shaped_configs": len(prompt_shaped.get("included_configs", [])),
        },
        "pairs": pairs,
        "synthesis": synthesize(pairs),
    }


def label_badges(counts: dict[str, int]) -> str:
    if not counts:
        return '<span class="muted">none</span>'
    ordered = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:6]
    return " ".join(f'<span class="tag neutral">{e(k)} · {v}</span>' for k, v in ordered)


def pair_row(pair: dict[str, Any]) -> str:
    a, b = pair["a_config"], pair["b_config"]
    if pair["b_solves"] >= pair["a_solves"]:
        winner = b
        gap = pair["b_solves"] - pair["a_solves"]
        unique = f"{pair['b_only']} / {pair['a_only']}"
    else:
        winner = a
        gap = pair["a_solves"] - pair["b_solves"]
        unique = f"{pair['a_only']} / {pair['b_only']}"
    return f'''<tr><td><b>{e(pair['question'])}</b><div class="muted"><code>{e(a)}</code> ↔ <code>{e(b)}</code></div></td><td>{pair['a_solves']}/{pair['cells']} vs {pair['b_solves']}/{pair['cells']}</td><td><span class="tag {'good' if gap > 0 else 'neutral'}">{e(winner)} +{gap}</span><div class="muted">unique wins {unique}</div></td><td>{pair['discordant_cells']}</td><td>{label_badges(pair['discordant_label_counts'])}</td><td>{pair['all_a_avg']['turns']:.1f} → {pair['all_b_avg']['turns']:.1f}</td><td>{money(pair['all_b_avg']['cost_usd'] - pair['all_a_avg']['cost_usd'])}</td></tr>'''


def example_rows(pair: dict[str, Any], limit: int = 8) -> str:
    rows = []
    # Show high-signal examples first: repro/test/localization and blowups.
    def score(d: dict[str, Any]) -> tuple[int, int]:
        labels = d["labels"]
        return (
            int("winner_more_repro_signal" in labels) + int("winner_more_verification" in labels) + int("loser_cost_blowup" in labels) + int("winner_more_localization" in labels),
            len(labels),
        )
    for d in sorted(pair["discordants"], key=score, reverse=True)[:limit]:
        wf = d["winner_features"]
        lf = d["loser_features"]
        rows.append(f'''<tr><td><code>{e(d['cell'])}</code></td><td><span class="tag good">{e(d['winner'])}</span><div class="muted">lost by {e(d['loser'])}</div></td><td>{', '.join(e(x) for x in d['labels'])}</td><td>{wf['test_command_count']} / {lf['test_command_count']}</td><td>{wf['repro_signal_count']} / {lf['repro_signal_count']}</td><td>{wf['turns']} / {lf['turns']}</td><td>{money(wf['cost_usd'])} / {money(lf['cost_usd'])}</td><td><code>{e(wf['result_path'])}</code><br><span class="muted">vs</span><br><code>{e(lf['result_path'])}</code></td></tr>''')
    return "".join(rows)


def prompt_text_block(title: str, text: str) -> str:
    return f'<div class="prompt"><h3>{e(title)}</h3><pre>{e(text)}</pre></div>'


def render(data: dict[str, Any]) -> str:
    pairs = data["pairs"]
    synth = data["synthesis"]
    recs = synth["recommended_next_sweep"]
    rec_html = "".join(prompt_text_block(r["name"], r["draft_prompt_text_for_approval"]) + f'<p class="muted">Purpose: {e(r["purpose"])}</p>' for r in recs)
    takeaways = "".join(f"<li>{e(t)}</li>" for t in synth["primary_takeaways"])
    html_doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>GPT-5.5 low prompt discordant-cell audit</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,#173c54,#07111f 43%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}main{{max-width:1320px;margin:0 auto;padding:36px 22px 64px}}.hero,.card,.callout{{background:rgba(15,29,49,.91);border:1px solid var(--line);border-radius:24px;padding:22px}}.hero{{padding:32px;background:linear-gradient(135deg,rgba(52,211,153,.16),rgba(15,29,49,.94) 45%,rgba(96,165,250,.10))}}h1{{font-size:clamp(34px,5vw,64px);line-height:.96;letter-spacing:-.055em;margin:12px 0 16px}}h2{{margin:34px 0 12px}}p,li{{color:#dbe7fb;max-width:1040px}}.kicker{{color:var(--green);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:30px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap;margin:1px}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.pills{{display:flex;gap:10px;flex-wrap:wrap}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}code,pre{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px}}code{{padding:1px 5px;font-size:12px}}pre{{white-space:pre-wrap;padding:12px;overflow:auto}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.prompt{{background:rgba(9,18,32,.62);border:1px solid var(--line);border-radius:18px;padding:14px;margin:12px 0}}@media(max-width:900px){{.stats,.grid{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">Discordant-cell audit · GPT-5.5 low · clean-Pi prompt-only</div><h1>The next ablation should test checklist structure, not another embedding cluster.</h1><p>This audit follows the prompt-shaped branch: behavioral wrappers are excluded, and direct task/rep cells decide what changed. Session traces are classified with deterministic heuristics over tool calls, verification commands, repro signals, turns, cost, tokens, and patch size.</p><div class="pills"><span class="pill good">4 targeted pairs</span><span class="pill neutral">108 cells each</span><span class="pill neutral">reward_binary == 1</span><span class="pill caution">draft prompt text for approval only</span></div><div class="src">Inputs: <code>{e(data['inputs']['corpus_overlap'])}</code>, <code>{e(data['inputs']['prompt_shaped_neighbor_divergence'])}</code>, and direct cells under <code>{e(data['inputs']['result_root'])}</code>.</div></section>
<div class="stats"><div class="stat"><b>+7</b><span>workflow checklist vs clean low</span></div><div class="stat"><b>+6</b><span>engineer preamble vs clean low</span></div><div class="stat"><b>+4</b><span>checklist-only vs preamble+checklist</span></div><div class="stat"><b>3</b><span>candidate ablations proposed for approval</span></div></div>
<section class="callout good"><h2>Verdict</h2><p>The evidence supports a small config sweep, but not a broad prompt search. The best first hypothesis is that <b>concrete ordered workflow</b> helps, while <b>generic competence preamble layered onto the workflow</b> can interfere. The next sweep should isolate the reproduction-script line, the commit line, and checklist compression.</p></section>
<div class="grid"><section class="card"><h2>Primary takeaways</h2><ul>{takeaways}</ul></section><section class="callout caution"><h2>Method caveat</h2><p>The labels are deterministic trace heuristics, not a human semantic judge. They are useful for prioritizing ablations, not proving causality. The strongest evidence remains paired direct solves and the fact that the proposed configs each remove or compress one prompt ingredient.</p></section></div>
<h2>Pair summary</h2><table><thead><tr><th>Question</th><th>Solves</th><th>Winner</th><th>Discordant cells</th><th>Trace labels</th><th>Avg turns</th><th>Avg cost Δ/cell</th></tr></thead><tbody>{''.join(pair_row(p) for p in pairs)}</tbody></table>
<h2>High-signal discordant examples</h2>{''.join(f'<h3>{e(p["question"])}</h3><table><thead><tr><th>Cell</th><th>Winner</th><th>Labels</th><th>Tests win/loss</th><th>Repro win/loss</th><th>Turns win/loss</th><th>Cost win/loss</th><th>Evidence paths</th></tr></thead><tbody>{example_rows(p)}</tbody></table>' for p in pairs)}
<h2>Proposed next config sweep — exact prompt text for approval, not written</h2><p>These are intentionally small. Each tests one ingredient in the current best prompt-shaped result.</p>{rec_html}
<section class="callout neutral"><h2>Recommended launch shape after approval</h2><ul><li>Start with a 12_v0 or small 36_v2 smoke/mini-sweep before any full 36_v2 × 3 run.</li><li>Keep model leaf fixed: <code>openai-codex/gpt-5.5</code>, thinking <code>low</code>.</li><li>Compare against clean low, <code>baseline-wf-only</code>, and <code>baseline-preamble-only</code> using paired task/rep cells.</li><li>Do not mix OMP/tool-surface or behavioral-wrapper rows into prompt-only claims.</li></ul></section>
<section class="callout"><h2>Evidence</h2><p>Generated JSON: <code>{e(OUT_JSON.relative_to(ROOT))}</code>. This script reads direct <code>result.json</code> and copied session logs; it does not write config prompt files.</p></section>
</main></body></html>'''
    return html_doc


def main() -> None:
    data = build()
    OUT_JSON.write_text(json.dumps(data, indent=2))
    OUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUT_HTML.write_text(render(data))
    print("wrote", OUT_JSON.relative_to(ROOT), OUT_JSON.stat().st_size)
    print("wrote", OUT_HTML.relative_to(ROOT), OUT_HTML.stat().st_size)


if __name__ == "__main__":
    main()

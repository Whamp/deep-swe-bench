#!/usr/bin/env python3
from __future__ import annotations

import csv
import difflib
import html
import json
import math
import random
import re
import shutil
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
TASK_ROOT = Path.home() / "evals/deep-swe/tasks"
RESULT_ROOT = ROOT / "results/gpt-5.5/low"
RUN_ID = "gpt55-low-wf-ablation-36v2-r3-w24"
RUN_DIR = ROOT / "results/_runs" / RUN_ID
SUBSET_PATH = ROOT / "subsets/36_v2.txt"
ANALYSIS_DIR = ROOT / "analysis/gpt55-low-wf-ablation-36v2"
PACKET_DIR = ANALYSIS_DIR / "churn_packets"
REPORT_DIR = ROOT / "reports/gpt55-low-wf-ablation-36v2"
REPORT_PACKET_DIR = REPORT_DIR / "packets"

OUT_JSON = ANALYSIS_DIR / "full_analysis.json"
OUT_PAIR_CSV = ANALYSIS_DIR / "paired_summary.csv"
OUT_CONFIG_CSV = ANALYSIS_DIR / "config_summary.csv"
OUT_TASK_CSV = ANALYSIS_DIR / "task_k3_profiles.csv"
OUT_FLIP_CSV = ANALYSIS_DIR / "solve_flip_index.csv"
OUT_HTML = REPORT_DIR / "index.html"

BASELINE_CLEAN = "baseline"
WORKFLOW = "baseline-wf-only"
VARIANTS = [
    "baseline-wf-no-repro-script",
    "baseline-wf-no-commit",
    "baseline-wf-tight-checklist",
]
ALL_CONFIGS = [BASELINE_CLEAN, WORKFLOW, *VARIANTS]
CONFIG_LABELS = {
    BASELINE_CLEAN: "Clean low",
    WORKFLOW: "Original workflow checklist",
    "baseline-wf-no-repro-script": "No explicit repro-script step",
    "baseline-wf-no-commit": "No commit step",
    "baseline-wf-tight-checklist": "Tight checklist wording",
}
COMPARISONS = [
    {"id": "workflow_vs_no_repro", "left": WORKFLOW, "right": "baseline-wf-no-repro-script", "focus": "Does the explicit repro-script step matter?"},
    {"id": "workflow_vs_no_commit", "left": WORKFLOW, "right": "baseline-wf-no-commit", "focus": "Does the final commit instruction matter?"},
    {"id": "workflow_vs_tight", "left": WORKFLOW, "right": "baseline-wf-tight-checklist", "focus": "Does compact wording preserve the workflow effect?"},
]
CONTEXT_COMPARISONS = [
    {"id": "clean_vs_workflow", "left": BASELINE_CLEAN, "right": WORKFLOW, "focus": "Historical reference: original workflow over clean low."},
    {"id": "clean_vs_no_repro", "left": BASELINE_CLEAN, "right": "baseline-wf-no-repro-script", "focus": "Context: no-repro variant over clean low."},
    {"id": "clean_vs_no_commit", "left": BASELINE_CLEAN, "right": "baseline-wf-no-commit", "focus": "Context: no-commit variant over clean low."},
    {"id": "clean_vs_tight", "left": BASELINE_CLEAN, "right": "baseline-wf-tight-checklist", "focus": "Context: tight checklist variant over clean low."},
]

REPS = [0, 1, 2]
BOOTSTRAP_REPS = 5000
BOOTSTRAP_SEED = 20260708
MAX_PACKET_PATCH_LINES = 180
MAX_PACKET_COMMANDS = 40
MAX_VERIFIER_FAILURES = 12

TEST_CMD_RE = re.compile(
    r"\b(pytest|tox|go\s+test|cargo\s+test|npm\s+(?:test|run\s+test)|pnpm\s+(?:test|run\s+test)|yarn\s+test|bun\s+test|vitest|jest|mvn\s+test|gradle\s+test|make\s+test|ctest|rspec|phpunit|pytest\b|unittest)\b",
    re.I,
)
REPRO_CMD_RE = re.compile(
    r"(repro|reproduce|cat\s+>\s*[^\n]*(?:repro|tmp|test|case)|python\d?\s+-\s*<<|node\s+-\s*<<|ruby\s+-\s*<<|perl\s+-\s*<<|php\s+<<|go\s+test\s+.*-run|pytest\s+.*-k)",
    re.I,
)
LOCALIZATION_RE = re.compile(r"\b(rg|grep|fd|find|ls|sed|awk|cat|python\s+-c)\b", re.I)


def read_text(path: Path, limit: int | None = None) -> str:
    try:
        text = path.read_text(errors="replace")
    except FileNotFoundError:
        return ""
    if limit is not None and len(text) > limit:
        return text[:limit] + f"\n...[truncated {len(text) - limit} chars]"
    return text


def load_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def h(value: Any) -> str:
    return html.escape(str(value), quote=True)


def money(value: float | None, digits: int = 2) -> str:
    if value is None:
        return "—"
    sign = "-" if value < 0 else ""
    return f"{sign}${abs(value):,.{digits}f}"


def pct(value: float | None, digits: int = 1) -> str:
    return "—" if value is None else f"{100 * value:.{digits}f}%"


def tasks() -> list[str]:
    return [line.strip() for line in SUBSET_PATH.read_text().splitlines() if line.strip()]


def cell_dir(config: str, task: str, rep: int) -> Path:
    return RESULT_ROOT / config / task / f"rep{rep}"


def result_path(config: str, task: str, rep: int) -> Path:
    return cell_dir(config, task, rep) / "result.json"


def solved(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") == 1


def invalid_reward(row: dict[str, Any]) -> bool:
    return row.get("reward_binary") not in (0, 1, False, True)


def num(row: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = row.get(key)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return default
    return default


def integer(row: dict[str, Any], *keys: str, default: int = 0) -> int:
    for key in keys:
        value = row.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                return default
    return default


def result_metric(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "reward_binary": row.get("reward_binary"),
        "reward_partial": num(row, "reward_partial"),
        "f2p": num(row, "f2p"),
        "p2p": num(row, "p2p"),
        "f2p_passed": integer(row, "f2p_passed"),
        "f2p_total": integer(row, "f2p_total"),
        "p2p_passed": integer(row, "p2p_passed"),
        "p2p_total": integer(row, "p2p_total"),
        "combined_total_tokens": integer(row, "combined_total_tokens", "total_tokens"),
        "combined_cost_usd": num(row, "combined_cost_usd", "cost_usd"),
        "agent_wall_s": num(row, "agent_wall_s"),
        "turns": integer(row, "turns"),
        "tool_calls": integer(row, "tool_calls"),
        "patch_bytes": integer(row, "patch_bytes"),
        "agent_timed_out": bool(row.get("agent_timed_out")),
        "agent_exit": row.get("agent_exit"),
        "verifier_exit": row.get("verifier_exit"),
        "language": row.get("language") or "unknown",
        "category": row.get("category") or "unknown",
    }


def task_meta(task: str) -> dict[str, str]:
    path = TASK_ROOT / task / "task.toml"
    data: dict[str, Any] = {}
    if path.exists():
        data = tomllib.loads(path.read_text())
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    task_obj = data.get("task", {}) if isinstance(data, dict) else {}
    return {
        "task": task,
        "title": metadata.get("display_title") or metadata.get("original_title") or task_obj.get("name") or task,
        "category": metadata.get("category") or "unknown",
        "language": metadata.get("language") or "unknown",
        "difficulty": metadata.get("difficulty") or "not_recorded",
        "task_toml": str(path),
    }


def session_paths(base: Path) -> list[Path]:
    session = base / "session"
    if not session.exists():
        return []
    return sorted(session.glob("*.jsonl"))


def extract_tool_trace(base: Path) -> dict[str, Any]:
    paths = session_paths(base)
    assistant_turns = 0
    tool_counts: Counter[str] = Counter()
    bash_cmds: list[str] = []
    tool_timeline: list[dict[str, Any]] = []
    assistant_text_chars = 0
    for path in paths:
        for line in path.read_text(errors="replace").splitlines():
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("type") != "message":
                continue
            msg = obj.get("message") or {}
            role = msg.get("role")
            if role == "assistant":
                assistant_turns += 1
                for item in msg.get("content") or []:
                    if item.get("type") == "text":
                        assistant_text_chars += len(item.get("text") or "")
                    if item.get("type") == "toolCall":
                        name = item.get("name") or "unknown"
                        args = item.get("arguments") or {}
                        tool_counts[name] += 1
                        command = args.get("command") if isinstance(args, dict) else None
                        if name == "bash" and command:
                            bash_cmds.append(command)
                        tool_timeline.append({
                            "tool": name,
                            "command": command,
                            "arguments_preview": json.dumps(args, ensure_ascii=False)[:600] if isinstance(args, dict) else str(args)[:600],
                        })
    test_cmds = [cmd for cmd in bash_cmds if TEST_CMD_RE.search(cmd)]
    repro_cmds = [cmd for cmd in bash_cmds if REPRO_CMD_RE.search(cmd)]
    localization_cmds = [cmd for cmd in bash_cmds if LOCALIZATION_RE.search(cmd)]
    return {
        "session_paths": [str(p.relative_to(ROOT)) for p in paths],
        "assistant_turns": assistant_turns,
        "assistant_text_chars": assistant_text_chars,
        "tool_counts": dict(tool_counts),
        "bash_cmds": bash_cmds[:MAX_PACKET_COMMANDS],
        "bash_cmd_count": len(bash_cmds),
        "test_cmds": test_cmds[:MAX_PACKET_COMMANDS],
        "test_cmd_count": len(test_cmds),
        "repro_cmds": repro_cmds[:MAX_PACKET_COMMANDS],
        "repro_cmd_count": len(repro_cmds),
        "localization_cmd_count": len(localization_cmds),
        "tool_timeline": tool_timeline[:MAX_PACKET_COMMANDS],
    }


def patch_stats(base: Path) -> dict[str, Any]:
    patch = base / "artifacts/model.patch"
    text = read_text(patch)
    files: list[str] = []
    adds = 0
    dels = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                right = parts[3]
                files.append(right[2:] if right.startswith("b/") else right)
        elif line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
    return {
        "path": str(patch.relative_to(ROOT)) if patch.exists() else None,
        "bytes": len(text.encode()),
        "files": files,
        "files_count": len(files),
        "adds": adds,
        "dels": dels,
        "changed_lines": adds + dels,
        "excerpt": "\n".join(text.splitlines()[:MAX_PACKET_PATCH_LINES]),
    }


def all_ctrf_failures(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        data = load_json(path)
    except Exception:
        return []
    failures: list[dict[str, Any]] = []
    def walk(obj: Any) -> None:
        if isinstance(obj, dict):
            status = str(obj.get("status") or obj.get("result") or "").lower()
            if status in {"failed", "fail", "error"}:
                failures.append({
                    "name": str(obj.get("name") or "unnamed"),
                    "status": status,
                    "message": str(obj.get("message") or obj.get("trace") or obj.get("rawStatus") or "")[:1200],
                })
            for value in obj.values():
                walk(value)
        elif isinstance(obj, list):
            for value in obj:
                walk(value)
    walk(data)
    # De-duplicate while preserving order.
    seen: set[tuple[str, str]] = set()
    out = []
    for failure in failures:
        key = (failure["name"], failure["message"])
        if key not in seen:
            out.append(failure)
            seen.add(key)
    return out


def log_excerpt_for_failures(log_text: str, failures: list[dict[str, Any]]) -> str:
    if not log_text:
        return ""
    lines = log_text.splitlines()
    chunks: list[str] = []
    for failure in failures[:5]:
        name = failure.get("name", "")
        needle = name.replace("[f2p] ", "").replace("[p2p] ", "")[:100]
        hit = None
        for i, line in enumerate(lines):
            if needle and needle in line:
                hit = i
                break
        if hit is not None:
            start = max(0, hit - 3)
            end = min(len(lines), hit + 8)
            chunks.append("\n".join(lines[start:end]))
    if chunks:
        return "\n---\n".join(chunks)[:5000]
    return "\n".join(lines[-80:])[:5000]


def verifier_evidence(base: Path) -> dict[str, Any]:
    reward_path = base / "verifier/reward.json"
    reward = load_json(reward_path) if reward_path.exists() else {}
    failures = all_ctrf_failures(base / "verifier/ctrf.json")
    f2p = [f for f in failures if f["name"].startswith("[f2p]")]
    p2p = [f for f in failures if f["name"].startswith("[p2p]")]
    log_text = read_text(base / "verifier/run.log")
    stdout_text = read_text(base / "logs/verifier.stdout.txt", limit=4000)
    return {
        "reward_path": str(reward_path.relative_to(ROOT)) if reward_path.exists() else None,
        "reward": reward,
        "failure_count": len(failures),
        "f2p_failure_count": len(f2p),
        "p2p_failure_count": len(p2p),
        "failures": failures[:MAX_VERIFIER_FAILURES],
        "run_log_path": str((base / "verifier/run.log").relative_to(ROOT)) if (base / "verifier/run.log").exists() else None,
        "stdout_path": str((base / "logs/verifier.stdout.txt").relative_to(ROOT)) if (base / "logs/verifier.stdout.txt").exists() else None,
        "stdout_excerpt": stdout_text,
        "failure_log_excerpt": log_excerpt_for_failures(log_text, failures),
    }


def side_packet(config: str, task: str, rep: int) -> dict[str, Any]:
    base = cell_dir(config, task, rep)
    row = load_json(base / "result.json")
    return {
        "config": config,
        "cell_dir": str(base.relative_to(ROOT)),
        "result_path": str((base / "result.json").relative_to(ROOT)),
        "result": result_metric(row),
        "session": [str(p.relative_to(ROOT)) for p in session_paths(base)],
        "patch_stats": patch_stats(base),
        "trace": extract_tool_trace(base),
        "verifier": verifier_evidence(base),
    }


def classify_flip(comparison_id: str, left: dict[str, Any], right: dict[str, Any], direction: str) -> dict[str, Any]:
    winner = left if direction == "left_only" else right
    loser = right if direction == "left_only" else left
    winner_name = winner["config"]
    loser_name = loser["config"]
    lost = loser["result"]
    vf = loser["verifier"]
    fail_names = [f["name"] for f in vf.get("failures", [])]
    f2p_fail = vf.get("f2p_failure_count", 0)
    p2p_fail = vf.get("p2p_failure_count", 0)
    primary = "likely variance"
    secondary = ""
    confidence = "medium"
    if lost.get("agent_timed_out"):
        primary = "resource exhaustion"
        confidence = "high"
    elif lost.get("patch_bytes", 0) == 0 or lost.get("verifier_exit") == "skipped_empty_patch":
        primary = "under-implementation"
        secondary = "validation gap"
        confidence = "high"
    elif p2p_fail and not f2p_fail:
        primary = "cross-scope regression"
        secondary = "validation gap"
        confidence = "high"
    elif f2p_fail and not p2p_fail:
        primary = "under-implementation"
        secondary = "missing invariant/guard"
        confidence = "high" if fail_names else "medium"
    elif f2p_fail and p2p_fail:
        primary = "under-implementation"
        secondary = "cross-scope regression"
        confidence = "medium"
    elif lost.get("reward_partial", 0) < 1:
        primary = "validation gap"
        confidence = "medium"
    else:
        confidence = "low"
    winner_files = set(winner["patch_stats"].get("files") or [])
    loser_files = set(loser["patch_stats"].get("files") or [])
    file_delta = sorted((winner_files | loser_files))[:12]
    failure_preview = "; ".join(fail_names[:4]) if fail_names else "no named verifier failures captured"
    mechanism = (
        f"{winner_name} solved while {loser_name} failed. The losing side's verifier evidence is "
        f"f2p_failures={f2p_fail}, p2p_failures={p2p_fail}; first failures: {failure_preview}. "
        f"Winner touched {winner['patch_stats'].get('files_count')} files and loser touched {loser['patch_stats'].get('files_count')} files; "
        f"shared/changed file set includes {', '.join(file_delta) if file_delta else 'no patch files captured'}."
    )
    if "no_repro" in comparison_id:
        if direction == "left_only":
            implication = "The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification."
        else:
            implication = "Do not require every task to create a standalone repro script; when targeted tests already expose the issue, flexible verification can save cost."
    elif "no_commit" in comparison_id:
        if direction == "left_only":
            implication = "The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping."
        else:
            implication = "The commit instruction is not necessary for every success; if omitted, preserve the rest of the validation loop."
    elif "tight" in comparison_id:
        if direction == "left_only":
            implication = "Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture."
        else:
            implication = "Some tasks tolerate compact wording, but wins must be weighed against the larger loss set."
    else:
        implication = "Treat this as local trajectory evidence; compare both wins and losses before changing guidance."
    evidence = [
        f"winner {winner_name}: reward={winner['result'].get('reward_binary')} partial={winner['result'].get('reward_partial'):.4f}",
        f"loser {loser_name}: reward={loser['result'].get('reward_binary')} partial={loser['result'].get('reward_partial'):.4f}",
        f"loser f2p={lost.get('f2p'):.4f} p2p={lost.get('p2p'):.4f} failures={vf.get('failure_count', 0)}",
        f"winner test/repro commands={winner['trace'].get('test_cmd_count')}/{winner['trace'].get('repro_cmd_count')}; loser={loser['trace'].get('test_cmd_count')}/{loser['trace'].get('repro_cmd_count')}",
    ]
    if fail_names:
        evidence.append("first failed tests: " + "; ".join(fail_names[:5]))
    return {
        "primary_bucket": primary,
        "secondary_bucket": secondary,
        "confidence": confidence,
        "mechanism": mechanism,
        "evidence": evidence,
        "guidance_implication": implication,
        "direct_session_evidence": "Tool timelines and command counts are extracted from session/*.jsonl for each side.",
        "source_patch_evidence": "Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.",
        "inference_note": "Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.",
    }


def packet_filename(comparison_id: str, task: str, rep: int, direction: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "-", task)
    return f"{comparison_id}__{safe}__rep{rep}__{direction}.md"


def packet_json_filename(comparison_id: str, task: str, rep: int, direction: str) -> str:
    return packet_filename(comparison_id, task, rep, direction).removesuffix(".md") + ".json"


def render_packet_md(packet: dict[str, Any]) -> str:
    pair = packet["pair"]
    left = packet["left"]
    right = packet["right"]
    cls = packet["classification"]
    def side_section(name: str, side: dict[str, Any]) -> str:
        metrics = json.dumps(side["result"], indent=2)
        patch = side["patch_stats"]
        trace = side["trace"]
        verifier = side["verifier"]
        cmds = "\n".join(f"- `{cmd[:240]}`" for cmd in trace.get("bash_cmds", [])[:25]) or "- none captured"
        tests = "\n".join(f"- `{cmd[:240]}`" for cmd in trace.get("test_cmds", [])[:20]) or "- none captured"
        failures = "\n".join(f"- {f['name']}: {f.get('message','')[:300]}" for f in verifier.get("failures", [])[:MAX_VERIFIER_FAILURES]) or "- none captured"
        return f"""## {name}: `{side['config']}`

### Result metrics

```json
{metrics}
```

### Patch stats

- patch: `{patch.get('path')}`
- files ({patch.get('files_count')}): {', '.join('`'+f+'`' for f in patch.get('files', [])[:20]) or 'none'}
- adds/deletes/changed: {patch.get('adds')} / {patch.get('dels')} / {patch.get('changed_lines')}
- bytes: {patch.get('bytes')}

### Tool summary

- assistant turns: {trace.get('assistant_turns')}
- tool counts: `{trace.get('tool_counts')}`
- bash commands: {trace.get('bash_cmd_count')}
- test commands: {trace.get('test_cmd_count')}
- repro-signal commands: {trace.get('repro_cmd_count')}
- session: {', '.join('`'+s+'`' for s in side.get('session', [])) or 'none'}

### Test / validation commands

{tests}

### Bash timeline excerpt

{cmds}

### Verifier evidence

- reward path: `{verifier.get('reward_path')}`
- f2p failures: {verifier.get('f2p_failure_count')}
- p2p failures: {verifier.get('p2p_failure_count')}
- failures:
{failures}

#### Verifier log excerpt

```text
{verifier.get('failure_log_excerpt') or verifier.get('stdout_excerpt') or ''}
```

### Patch excerpt

```diff
{patch.get('excerpt') or ''}
```
"""
    evidence = "\n".join(f"- {item}" for item in cls.get("evidence", []))
    return f"""# Solve flip packet: {pair['task']} rep{pair['rep']}

- comparison: `{pair['comparison_id']}`
- direction: `{pair['direction']}`
- title: {pair['title']}
- language/category/difficulty: {pair['language']} / {pair['category']} / {pair['difficulty']}
- left config: `{pair['left_config']}`
- right config: `{pair['right_config']}`

## Outcome delta

- left reward/partial: {left['result']['reward_binary']} / {left['result']['reward_partial']:.4f}
- right reward/partial: {right['result']['reward_binary']} / {right['result']['reward_partial']:.4f}
- token delta right-left: {right['result']['combined_total_tokens'] - left['result']['combined_total_tokens']}
- cost delta right-left: {right['result']['combined_cost_usd'] - left['result']['combined_cost_usd']:.6f}
- turns delta right-left: {right['result']['turns'] - left['result']['turns']}
- tool calls delta right-left: {right['result']['tool_calls'] - left['result']['tool_calls']}

## Classification

- primary bucket: **{cls['primary_bucket']}**
- secondary bucket: {cls.get('secondary_bucket') or 'none'}
- confidence: {cls.get('confidence')}
- mechanism: {cls['mechanism']}
- guidance implication: {cls['guidance_implication']}
- direct session evidence: {cls['direct_session_evidence']}
- source/patch evidence: {cls['source_patch_evidence']}
- inference note: {cls['inference_note']}

### Evidence bullets

{evidence}

{side_section('Left', left)}

{side_section('Right', right)}
"""


def make_packet(comparison: dict[str, str], task: str, rep: int, direction: str, meta: dict[str, str]) -> dict[str, Any]:
    left = side_packet(comparison["left"], task, rep)
    right = side_packet(comparison["right"], task, rep)
    packet = {
        "pair": {
            "comparison_id": comparison["id"],
            "task": task,
            "rep": rep,
            "title": meta["title"],
            "difficulty": meta["difficulty"],
            "language": meta["language"],
            "category": meta["category"],
            "left_config": comparison["left"],
            "right_config": comparison["right"],
            "direction": direction,
        },
        "left": left,
        "right": right,
    }
    packet["classification"] = classify_flip(comparison["id"], left, right, direction)
    return packet


def write_packet(packet: dict[str, Any]) -> dict[str, str]:
    pair = packet["pair"]
    comp_dir = PACKET_DIR / pair["comparison_id"]
    comp_dir.mkdir(parents=True, exist_ok=True)
    report_comp_dir = REPORT_PACKET_DIR / pair["comparison_id"]
    report_comp_dir.mkdir(parents=True, exist_ok=True)
    md_name = packet_filename(pair["comparison_id"], pair["task"], pair["rep"], pair["direction"])
    json_name = packet_json_filename(pair["comparison_id"], pair["task"], pair["rep"], pair["direction"])
    md_text = render_packet_md(packet)
    json_text = json.dumps(packet, indent=2)
    md_path = comp_dir / md_name
    json_path = comp_dir / json_name
    md_path.write_text(md_text)
    json_path.write_text(json_text)
    (report_comp_dir / md_name).write_text(md_text)
    (report_comp_dir / json_name).write_text(json_text)
    return {
        "analysis_md": str(md_path.relative_to(ROOT)),
        "analysis_json": str(json_path.relative_to(ROOT)),
        "report_md": str((report_comp_dir / md_name).relative_to(REPORT_DIR)),
        "report_json": str((report_comp_dir / json_name).relative_to(REPORT_DIR)),
    }


def load_results(configs: list[str], task_ids: list[str]) -> dict[str, dict[tuple[str, int], dict[str, Any]]]:
    out: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    missing = []
    for config in configs:
        out[config] = {}
        for task in task_ids:
            for rep in REPS:
                p = result_path(config, task, rep)
                if not p.exists():
                    missing.append(str(p.relative_to(ROOT)))
                    continue
                out[config][(task, rep)] = load_json(p)
    if missing:
        raise RuntimeError("missing result files:\n" + "\n".join(missing[:50]))
    return out


def config_summary(config: str, rows: dict[tuple[str, int], dict[str, Any]], task_ids: list[str]) -> dict[str, Any]:
    values = list(rows.values())
    kdist = Counter()
    for task in task_ids:
        k = sum(1 for rep in REPS if solved(rows[(task, rep)]))
        kdist[k] += 1
    traces = [extract_tool_trace(cell_dir(config, task, rep)) for task in task_ids for rep in REPS]
    return {
        "config": config,
        "label": CONFIG_LABELS.get(config, config),
        "result_root": str((RESULT_ROOT / config).relative_to(ROOT)),
        "cells": len(values),
        "solves": sum(1 for row in values if solved(row)),
        "solve_rate": sum(1 for row in values if solved(row)) / len(values),
        "invalid_rewards": sum(1 for row in values if invalid_reward(row)),
        "total_cost_usd": sum(num(row, "combined_cost_usd", "cost_usd") for row in values),
        "median_cost_usd": median(num(row, "combined_cost_usd", "cost_usd") for row in values),
        "total_tokens": sum(integer(row, "combined_total_tokens", "total_tokens") for row in values),
        "median_tokens": median(integer(row, "combined_total_tokens", "total_tokens") for row in values),
        "mean_partial": mean(num(row, "reward_partial") for row in values),
        "median_partial": median(num(row, "reward_partial") for row in values),
        "mean_turns": mean(integer(row, "turns") for row in values),
        "mean_tool_calls": mean(integer(row, "tool_calls") for row in values),
        "mean_wall_s": mean(num(row, "agent_wall_s") for row in values),
        "k_distribution": {str(k): kdist[k] for k in range(4)},
        "any_success_tasks": sum(1 for task in task_ids if sum(1 for rep in REPS if solved(rows[(task, rep)])) > 0),
        "stable_3_of_3_tasks": sum(1 for task in task_ids if sum(1 for rep in REPS if solved(rows[(task, rep)])) == 3),
        "flaky_1_or_2_tasks": sum(1 for task in task_ids if sum(1 for rep in REPS if solved(rows[(task, rep)])) in (1, 2)),
        "test_cmds_total": sum(t["test_cmd_count"] for t in traces),
        "repro_cmds_total": sum(t["repro_cmd_count"] for t in traces),
        "localization_cmds_total": sum(t["localization_cmd_count"] for t in traces),
        "mean_test_cmds": mean(t["test_cmd_count"] for t in traces),
        "mean_repro_cmds": mean(t["repro_cmd_count"] for t in traces),
        "mean_localization_cmds": mean(t["localization_cmd_count"] for t in traces),
        "sample_result_paths": [str(result_path(config, task_ids[0], 0).relative_to(ROOT)), str(result_path(config, task_ids[-1], 2).relative_to(ROOT))],
    }


def exact_mcnemar_p(left_only: int, right_only: int) -> float | None:
    n = left_only + right_only
    if n == 0:
        return None
    k = min(left_only, right_only)
    prob = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return min(1.0, 2 * prob)


def percentile(values: list[float], p: float) -> float:
    if not values:
        return float("nan")
    xs = sorted(values)
    idx = (len(xs) - 1) * p
    lo = math.floor(idx)
    hi = math.ceil(idx)
    if lo == hi:
        return xs[lo]
    return xs[lo] * (hi - idx) + xs[hi] * (idx - lo)


def bootstrap_pair(comparison: dict[str, str], results: dict[str, dict[tuple[str, int], dict[str, Any]]], task_ids: list[str]) -> dict[str, Any]:
    left = comparison["left"]
    right = comparison["right"]
    seed = BOOTSTRAP_SEED + sum((i + 1) * ord(ch) for i, ch in enumerate(comparison["id"])) % 100000
    rng = random.Random(seed)
    attempt_values: list[float] = []
    any_values: list[float] = []
    stable_values: list[float] = []
    def task_values(sample_tasks: list[str]) -> tuple[float, float, float]:
        attempt = 0.0
        any_s = 0.0
        stable = 0.0
        for task in sample_tasks:
            lk = sum(1 for rep in REPS if solved(results[left][(task, rep)]))
            rk = sum(1 for rep in REPS if solved(results[right][(task, rep)]))
            attempt += rk - lk
            any_s += (rk > 0) - (lk > 0)
            stable += (rk == 3) - (lk == 3)
        return attempt, any_s, stable
    for _ in range(BOOTSTRAP_REPS):
        sample = [rng.choice(task_ids) for _ in task_ids]
        a, b, c = task_values(sample)
        attempt_values.append(a)
        any_values.append(b)
        stable_values.append(c)
    point = task_values(task_ids)
    def summarize(values: list[float], point_value: float) -> dict[str, Any]:
        return {
            "point": point_value,
            "ci95_low": percentile(values, 0.025),
            "ci95_high": percentile(values, 0.975),
            "probability_positive": sum(1 for v in values if v > 0) / len(values),
            "probability_negative": sum(1 for v in values if v < 0) / len(values),
        }
    return {
        "bootstrap_reps": BOOTSTRAP_REPS,
        "seed": seed,
        "attempt_solve_delta_per_108": summarize(attempt_values, point[0]),
        "any_success_task_delta_per_36": summarize(any_values, point[1]),
        "stable_3_of_3_task_delta_per_36": summarize(stable_values, point[2]),
    }


def pair_summary(comparison: dict[str, str], results: dict[str, dict[tuple[str, int], dict[str, Any]]], task_ids: list[str], metas: dict[str, dict[str, str]], make_packets: bool = False) -> dict[str, Any]:
    left = comparison["left"]
    right = comparison["right"]
    both = left_only = right_only = neither = 0
    partial_deltas: list[float] = []
    cost_deltas: list[float] = []
    token_deltas: list[int] = []
    wall_deltas: list[float] = []
    turn_deltas: list[int] = []
    tool_deltas: list[int] = []
    flips: list[dict[str, Any]] = []
    language_split: dict[str, Counter[str]] = defaultdict(Counter)
    category_split: dict[str, Counter[str]] = defaultdict(Counter)
    k_matrix = {str(i): {str(j): {"count": 0, "tasks": []} for j in range(4)} for i in range(4)}
    for task in task_ids:
        lk = sum(1 for rep in REPS if solved(results[left][(task, rep)]))
        rk = sum(1 for rep in REPS if solved(results[right][(task, rep)]))
        k_matrix[str(lk)][str(rk)]["count"] += 1
        k_matrix[str(lk)][str(rk)]["tasks"].append(task)
        for rep in REPS:
            lrow = results[left][(task, rep)]
            rrow = results[right][(task, rep)]
            ls = solved(lrow)
            rs = solved(rrow)
            if ls and rs:
                both += 1
                state = "both"
            elif ls:
                left_only += 1
                state = "left_only"
            elif rs:
                right_only += 1
                state = "right_only"
            else:
                neither += 1
                state = "neither"
            meta = metas[task]
            language_split[meta["language"]][state] += 1
            category_split[meta["category"]][state] += 1
            partial_deltas.append(num(rrow, "reward_partial") - num(lrow, "reward_partial"))
            cost_deltas.append(num(rrow, "combined_cost_usd", "cost_usd") - num(lrow, "combined_cost_usd", "cost_usd"))
            token_deltas.append(integer(rrow, "combined_total_tokens", "total_tokens") - integer(lrow, "combined_total_tokens", "total_tokens"))
            wall_deltas.append(num(rrow, "agent_wall_s") - num(lrow, "agent_wall_s"))
            turn_deltas.append(integer(rrow, "turns") - integer(lrow, "turns"))
            tool_deltas.append(integer(rrow, "tool_calls") - integer(lrow, "tool_calls"))
            if state in {"left_only", "right_only"}:
                flip_record = {
                    "comparison_id": comparison["id"],
                    "task": task,
                    "rep": rep,
                    "direction": state,
                    "left_config": left,
                    "right_config": right,
                    "left_solved": ls,
                    "right_solved": rs,
                    "left_partial": num(lrow, "reward_partial"),
                    "right_partial": num(rrow, "reward_partial"),
                    "partial_delta_right_minus_left": num(rrow, "reward_partial") - num(lrow, "reward_partial"),
                    "cost_delta_right_minus_left": num(rrow, "combined_cost_usd", "cost_usd") - num(lrow, "combined_cost_usd", "cost_usd"),
                    "token_delta_right_minus_left": integer(rrow, "combined_total_tokens", "total_tokens") - integer(lrow, "combined_total_tokens", "total_tokens"),
                    "language": meta["language"],
                    "category": meta["category"],
                    "title": meta["title"],
                }
                if make_packets:
                    packet = make_packet(comparison, task, rep, state, meta)
                    links = write_packet(packet)
                    flip_record.update({
                        "classification": packet["classification"],
                        "packet": links,
                    })
                flips.append(flip_record)
    bucket_counts = Counter()
    confidence_counts = Counter()
    for flip in flips:
        cls = flip.get("classification") or {}
        if cls:
            bucket_counts[cls.get("primary_bucket", "unknown")] += 1
            confidence_counts[cls.get("confidence", "unknown")] += 1
    return {
        "id": comparison["id"],
        "focus": comparison["focus"],
        "left_config": left,
        "right_config": right,
        "left_label": CONFIG_LABELS.get(left, left),
        "right_label": CONFIG_LABELS.get(right, right),
        "cells": both + left_only + right_only + neither,
        "both_solved": both,
        "left_only": left_only,
        "right_only": right_only,
        "neither_solved": neither,
        "net_solve_delta_right_minus_left": right_only - left_only,
        "solve_flips": left_only + right_only,
        "mcnemar_exact_p": exact_mcnemar_p(left_only, right_only),
        "mean_partial_delta_right_minus_left": mean(partial_deltas),
        "median_partial_delta_right_minus_left": median(partial_deltas),
        "sum_cost_delta_right_minus_left": sum(cost_deltas),
        "median_cost_delta_right_minus_left": median(cost_deltas),
        "sum_token_delta_right_minus_left": sum(token_deltas),
        "median_token_delta_right_minus_left": median(token_deltas),
        "mean_wall_delta_right_minus_left": mean(wall_deltas),
        "mean_turn_delta_right_minus_left": mean(turn_deltas),
        "mean_tool_delta_right_minus_left": mean(tool_deltas),
        "k3_transition_matrix": k_matrix,
        "language_split": {k: dict(v) for k, v in sorted(language_split.items())},
        "category_split": {k: dict(v) for k, v in sorted(category_split.items())},
        "task_bootstrap": bootstrap_pair(comparison, results, task_ids),
        "bucket_counts": dict(bucket_counts),
        "confidence_counts": dict(confidence_counts),
        "flips": flips,
    }


def task_profiles(task_ids: list[str], results: dict[str, dict[tuple[str, int], dict[str, Any]]], metas: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows = []
    for task in task_ids:
        k_by_config = {config: sum(1 for rep in REPS if solved(results[config][(task, rep)])) for config in ALL_CONFIGS}
        best_k = max(k_by_config.values())
        worst_k = min(k_by_config.values())
        rows.append({
            "task": task,
            "title": metas[task]["title"],
            "language": metas[task]["language"],
            "category": metas[task]["category"],
            "k_by_config": k_by_config,
            "range": best_k - worst_k,
            "best_configs": [c for c, k in k_by_config.items() if k == best_k],
            "workflow_minus_clean": k_by_config[WORKFLOW] - k_by_config[BASELINE_CLEAN],
            "no_repro_minus_workflow": k_by_config["baseline-wf-no-repro-script"] - k_by_config[WORKFLOW],
            "no_commit_minus_workflow": k_by_config["baseline-wf-no-commit"] - k_by_config[WORKFLOW],
            "tight_minus_workflow": k_by_config["baseline-wf-tight-checklist"] - k_by_config[WORKFLOW],
        })
    return rows


def write_csvs(data: dict[str, Any]) -> None:
    with OUT_CONFIG_CSV.open("w", newline="") as f:
        fields = ["config", "cells", "solves", "solve_rate", "total_cost_usd", "total_tokens", "mean_partial", "any_success_tasks", "stable_3_of_3_tasks", "flaky_1_or_2_tasks", "k_distribution", "mean_test_cmds", "mean_repro_cmds"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in data["config_summaries"]:
            w.writerow({k: row.get(k) for k in fields})
    with OUT_PAIR_CSV.open("w", newline="") as f:
        fields = ["id", "left_config", "right_config", "cells", "both_solved", "left_only", "right_only", "neither_solved", "net_solve_delta_right_minus_left", "solve_flips", "mcnemar_exact_p", "mean_partial_delta_right_minus_left", "sum_cost_delta_right_minus_left", "sum_token_delta_right_minus_left", "mean_turn_delta_right_minus_left", "mean_tool_delta_right_minus_left"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in data["primary_pair_summaries"] + data["context_pair_summaries"]:
            w.writerow({k: row.get(k) for k in fields})
    with OUT_TASK_CSV.open("w", newline="") as f:
        fields = ["task", "language", "category", "baseline_k", "workflow_k", "no_repro_k", "no_commit_k", "tight_k", "range", "best_configs"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in data["task_profiles"]:
            k = row["k_by_config"]
            w.writerow({
                "task": row["task"],
                "language": row["language"],
                "category": row["category"],
                "baseline_k": k[BASELINE_CLEAN],
                "workflow_k": k[WORKFLOW],
                "no_repro_k": k["baseline-wf-no-repro-script"],
                "no_commit_k": k["baseline-wf-no-commit"],
                "tight_k": k["baseline-wf-tight-checklist"],
                "range": row["range"],
                "best_configs": ";".join(row["best_configs"]),
            })
    with OUT_FLIP_CSV.open("w", newline="") as f:
        fields = ["comparison_id", "task", "rep", "direction", "left_config", "right_config", "left_partial", "right_partial", "partial_delta_right_minus_left", "cost_delta_right_minus_left", "token_delta_right_minus_left", "language", "category", "primary_bucket", "confidence", "packet_md"]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for pair in data["primary_pair_summaries"]:
            for flip in pair["flips"]:
                cls = flip.get("classification") or {}
                packet = flip.get("packet") or {}
                w.writerow({
                    **{k: flip.get(k) for k in fields if k in flip},
                    "primary_bucket": cls.get("primary_bucket"),
                    "confidence": cls.get("confidence"),
                    "packet_md": packet.get("analysis_md"),
                })


def kdist_str(row: dict[str, Any]) -> str:
    d = row.get("k_distribution", {})
    return " / ".join(f"{k}:{d.get(str(k), 0)}" for k in range(4))


def config_rows_html(rows: list[dict[str, Any]]) -> str:
    html_rows = []
    workflow = next(r for r in rows if r["config"] == WORKFLOW)
    clean = next(r for r in rows if r["config"] == BASELINE_CLEAN)
    for row in rows:
        solve_delta = row["solves"] - workflow["solves"] if row["config"] != WORKFLOW else 0
        clean_delta = row["solves"] - clean["solves"]
        klass = "good" if row["solves"] >= workflow["solves"] else ("bad" if row["config"] == "baseline-wf-tight-checklist" else "caution")
        html_rows.append(f"""<tr><td><code>{h(row['config'])}</code><div class='muted'>{h(row['label'])}</div></td><td><span class='tag {klass}'>{row['solves']}/108</span></td><td>{clean_delta:+d}</td><td>{solve_delta:+d}</td><td>{row['any_success_tasks']}/36</td><td>{row['stable_3_of_3_tasks']}/36</td><td>{h(kdist_str(row))}</td><td>{money(row['total_cost_usd'])}</td><td>{row['total_tokens']:,}</td><td>{row['mean_test_cmds']:.2f}</td><td>{row['mean_repro_cmds']:.2f}</td></tr>""")
    return "".join(html_rows)


def pair_rows_html(rows: list[dict[str, Any]]) -> str:
    html_rows = []
    for row in rows:
        net = row["net_solve_delta_right_minus_left"]
        klass = "good" if net > 0 else ("bad" if net < 0 else "neutral")
        p = row["mcnemar_exact_p"]
        boot = row["task_bootstrap"]["attempt_solve_delta_per_108"]
        html_rows.append(f"""<tr><td><code>{h(row['id'])}</code><div class='muted'>{h(row['focus'])}</div></td><td>{h(row['left_label'])} → {h(row['right_label'])}</td><td><span class='tag {klass}'>{net:+d}</span></td><td>{row['left_only']} / {row['right_only']}</td><td>{row['both_solved']} / {row['neither_solved']}</td><td>{money(row['sum_cost_delta_right_minus_left'])}</td><td>{row['sum_token_delta_right_minus_left']:,}</td><td>{boot['ci95_low']:+.0f} to {boot['ci95_high']:+.0f}</td><td>{'—' if p is None else f'{p:.3f}'}</td></tr>""")
    return "".join(html_rows)


def matrix_html(row: dict[str, Any]) -> str:
    cells = []
    matrix = row["k3_transition_matrix"]
    for lk in range(4):
        tds = [f"<th>{lk}/3 left</th>"]
        for rk in range(4):
            count = matrix[str(lk)][str(rk)]["count"]
            klass = "neutral"
            if rk > lk:
                klass = "good"
            elif rk < lk:
                klass = "bad"
            tds.append(f"<td><span class='tag {klass}'>{count}</span></td>")
        cells.append("<tr>" + "".join(tds) + "</tr>")
    return f"""<section class='mini'><h3>{h(row['right_label'])} vs {h(row['left_label'])}</h3><table class='matrix'><thead><tr><th></th><th>0/3 right</th><th>1/3 right</th><th>2/3 right</th><th>3/3 right</th></tr></thead><tbody>{''.join(cells)}</tbody></table></section>"""


def bucket_rows_html(rows: list[dict[str, Any]]) -> str:
    all_buckets = sorted(set().union(*(set(r.get("bucket_counts", {})) for r in rows)))
    html_rows = []
    for row in rows:
        counts = row.get("bucket_counts", {})
        buckets = "".join(f"<span class='tag neutral'>{h(bucket)}: {counts.get(bucket,0)}</span> " for bucket in all_buckets if counts.get(bucket, 0))
        html_rows.append(f"<tr><td><code>{h(row['id'])}</code></td><td>{row['solve_flips']}</td><td>{buckets or '—'}</td></tr>")
    return "".join(html_rows)


def flip_rows_html(rows: list[dict[str, Any]], limit: int = 24) -> str:
    all_flips = []
    for row in rows:
        all_flips.extend(row["flips"])
    all_flips.sort(key=lambda f: (f["comparison_id"], f["direction"], -abs(f["partial_delta_right_minus_left"]), f["task"], f["rep"]))
    html_rows = []
    for flip in all_flips[:limit]:
        cls = flip.get("classification") or {}
        packet = flip.get("packet") or {}
        direction_label = "variant win" if flip["direction"] == "right_only" else "workflow win"
        klass = "good" if flip["direction"] == "right_only" else "bad"
        html_rows.append(f"""<tr><td><code>{h(flip['comparison_id'])}</code></td><td><code>{h(flip['task'])}</code><div class='muted'>rep{flip['rep']} · {h(flip['language'])}</div></td><td><span class='tag {klass}'>{direction_label}</span></td><td>{flip['left_partial']:.3f} → {flip['right_partial']:.3f}</td><td>{h(cls.get('primary_bucket',''))}<div class='muted'>{h(cls.get('confidence',''))}</div></td><td>{h(cls.get('mechanism',''))[:260]}...</td><td><a href='{h(packet.get('report_md',''))}'>packet</a></td></tr>""")
    return "".join(html_rows)


def task_rows_html(rows: list[dict[str, Any]], limit: int = 18) -> str:
    selected = sorted(rows, key=lambda r: (-r["range"], r["tight_minus_workflow"], r["task"]))[:limit]
    html_rows = []
    for row in selected:
        k = row["k_by_config"]
        html_rows.append(f"""<tr><td><code>{h(row['task'])}</code><div class='muted'>{h(row['title'])[:90]}</div></td><td>{h(row['language'])}</td><td>{k[BASELINE_CLEAN]}</td><td>{k[WORKFLOW]}</td><td>{k['baseline-wf-no-repro-script']}</td><td>{k['baseline-wf-no-commit']}</td><td>{k['baseline-wf-tight-checklist']}</td><td>{', '.join('<code>'+h(c)+'</code>' for c in row['best_configs'])}</td></tr>""")
    return "".join(html_rows)


def run_health(data: dict[str, Any]) -> str:
    status = data["run_status"]
    counts = status.get("counts", {})
    return f"state={status.get('state')} stage={status.get('stage')} batch_done={counts.get('batch_done')}/{counts.get('batch_total')} ok={counts.get('ok')} skipped={counts.get('batch_skipped')} failed={counts.get('failed')} transients={counts.get('transient')}"


def render_html(data: dict[str, Any]) -> str:
    config_summaries = data["config_summaries"]
    by_config = {r["config"]: r for r in config_summaries}
    pairs = data["primary_pair_summaries"]
    context_pairs = data["context_pair_summaries"]
    no_repro = next(r for r in pairs if r["right_config"] == "baseline-wf-no-repro-script")
    no_commit = next(r for r in pairs if r["right_config"] == "baseline-wf-no-commit")
    tight = next(r for r in pairs if r["right_config"] == "baseline-wf-tight-checklist")
    matrices = "".join(matrix_html(r) for r in pairs)
    outputs = "".join(f"<li><code>{h(path)}</code></li>" for path in data["outputs"].values())
    evidence = "".join(f"<li><code>{h(path)}</code></li>" for path in data["inputs"]["evidence_roots"])
    return f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>GPT-5.5 low workflow ablation full analysis</title><style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 8% 0%,#173c54,#07111f 45%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}main{{max-width:1450px;margin:0 auto;padding:36px 22px 70px}}.hero,.card,.callout,.mini{{background:rgba(15,29,49,.93);border:1px solid var(--line);border-radius:24px;padding:22px;box-shadow:0 20px 80px rgba(0,0,0,.24)}}.hero{{padding:34px;background:linear-gradient(135deg,rgba(251,191,36,.16),rgba(15,29,49,.94) 42%,rgba(96,165,250,.13))}}.kicker{{color:var(--amber);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:900}}h1{{font-size:clamp(34px,5.8vw,72px);line-height:.92;letter-spacing:-.06em;margin:12px 0 16px}}h2{{margin:34px 0 12px;font-size:28px;letter-spacing:-.02em}}h3{{margin:0 0 10px}}p,li{{color:#dbe7fb;max-width:1120px}}.stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:22px 0}}.stat{{background:rgba(15,29,49,.86);border:1px solid var(--line);border-radius:20px;padding:18px}}.stat b{{display:block;font-size:32px;line-height:1;letter-spacing:-.04em}}.stat span,.muted,.src{{color:var(--muted);font-size:12px}}.pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:850;border:1px solid var(--line);background:#0b1728;color:var(--muted);white-space:nowrap;margin:1px}}.good{{color:#b9f8da!important;border-color:rgba(52,211,153,.5)!important;background:rgba(52,211,153,.12)!important}}.bad{{color:#fecdd3!important;border-color:rgba(251,113,133,.5)!important;background:rgba(251,113,133,.12)!important}}.caution{{color:#fde68a!important;border-color:rgba(251,191,36,.55)!important;background:rgba(251,191,36,.12)!important}}.neutral{{color:#bfdbfe!important;border-color:rgba(96,165,250,.45)!important;background:rgba(96,165,250,.12)!important}}.grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}.heatmaps{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}}table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68);margin-bottom:22px}}th,td{{text-align:left;vertical-align:top;padding:10px 11px;border-bottom:1px solid var(--line)}}th{{font-size:12px;text-transform:uppercase;letter-spacing:.08em;background:rgba(96,165,250,.1);color:#cfe2ff}}tr:last-child td{{border-bottom:0}}.matrix th,.matrix td{{text-align:center}}.matrix th:first-child{{text-align:right}}code,pre{{color:#dbeafe;background:rgba(96,165,250,.11);border:1px solid rgba(96,165,250,.18);border-radius:7px}}code{{padding:1px 5px;font-size:12px}}pre{{white-space:pre-wrap;padding:12px;overflow:auto}}a{{color:#93c5fd}}.section-note{{color:#dbe7fb;border-left:4px solid var(--blue);padding-left:14px}}@media(max-width:1100px){{.stats,.grid,.heatmaps{{grid-template-columns:1fr}}table{{display:block;overflow-x:auto}}}}
</style></head><body><main>
<section class='hero'><div class='kicker'>Full paired trajectory analysis · {h(RUN_ID)}</div><h1>The original workflow prompt still wins.</h1><p>Bottom line: none of the three ablations beat <code>{WORKFLOW}</code> on paired 36_v2 × 3-rep GPT-5.5-low results. Removing the repro-script step is cheaper but loses 3 paired solves; removing the commit step loses 4; compressing the prompt loses 10. The ablation confirms that the useful signal is not merely “an ordered list” — the explicit workflow wording matters.</p><div><span class='pill good'>run complete</span><span class='pill neutral'>324 scheduled cells</span><span class='pill neutral'>51 primary solve flips packetized</span><span class='pill caution'>workflow anchor is historical, not same-run</span></div><p class='src'>Run health: {h(run_health(data))}</p></section>
<div class='stats'><div class='stat'><b>{by_config[WORKFLOW]['solves']}/108</b><span>original workflow solves</span></div><div class='stat'><b>{no_repro['net_solve_delta_right_minus_left']:+d}</b><span>no-repro vs workflow paired solve delta</span></div><div class='stat'><b>{no_commit['net_solve_delta_right_minus_left']:+d}</b><span>no-commit vs workflow paired solve delta</span></div><div class='stat'><b>{tight['net_solve_delta_right_minus_left']:+d}</b><span>tight checklist vs workflow paired solve delta</span></div></div>
<section class='callout caution'><h2>Conclusion</h2><p><b>Do not replace the original workflow checklist if the objective is solve rate.</b> The no-repro and no-commit variants are cheaper than the original workflow, and both still beat clean low in aggregate, but their paired churn shows real lost solves. The tight checklist is the clearest negative result: it keeps the shape but removes specificity and drops to {by_config['baseline-wf-tight-checklist']['solves']}/108, worse than clean low.</p></section>
<h2>Config-level results</h2><table><thead><tr><th>Config</th><th>Solves</th><th>Δ vs clean</th><th>Δ vs workflow</th><th>Any-success tasks</th><th>Stable 3/3 tasks</th><th>k distribution</th><th>Total cost</th><th>Total tokens</th><th>Mean test cmds</th><th>Mean repro-signal cmds</th></tr></thead><tbody>{config_rows_html(config_summaries)}</tbody></table>
<h2>Primary paired comparisons vs original workflow</h2><p class='section-note'>Unit is the paired cell: same task, same rep, same model and thinking level. Left is <code>{WORKFLOW}</code>; right is the ablation variant.</p><table><thead><tr><th>Comparison</th><th>Pair</th><th>Net right-left solves</th><th>Left-only / right-only</th><th>Both / neither</th><th>Cost Δ</th><th>Token Δ</th><th>Task-bootstrap 95% CI</th><th>Exact McNemar p</th></tr></thead><tbody>{pair_rows_html(pairs)}</tbody></table>
<h2>Context vs clean low</h2><table><thead><tr><th>Comparison</th><th>Pair</th><th>Net right-left solves</th><th>Left-only / right-only</th><th>Both / neither</th><th>Cost Δ</th><th>Token Δ</th><th>Task-bootstrap 95% CI</th><th>Exact McNemar p</th></tr></thead><tbody>{pair_rows_html(context_pairs)}</tbody></table>
<h2>Rep-aware k/3 transitions against workflow</h2><p class='section-note'>Rows are original workflow k/3; columns are variant k/3. Green means the variant raised a task's number of successful reps; red means it reduced reliability/reach.</p><div class='heatmaps'>{matrices}</div>
<h2>Solve-flip buckets and packet index</h2><p class='section-note'>Every primary solve flip has a packet with result metrics, patch stats, command timeline, verifier failures, patch excerpts, and a deterministic classification. The bucket is an inference; packet evidence is the source of truth.</p><table><thead><tr><th>Comparison</th><th>Flips</th><th>Primary buckets</th></tr></thead><tbody>{bucket_rows_html(pairs)}</tbody></table><table><thead><tr><th>Comparison</th><th>Task</th><th>Direction</th><th>Partial</th><th>Bucket</th><th>Mechanism preview</th><th>Packet</th></tr></thead><tbody>{flip_rows_html(pairs)}</tbody></table>
<h2>Tasks with the widest response spread</h2><table><thead><tr><th>Task</th><th>Lang</th><th>Clean</th><th>Workflow</th><th>No repro</th><th>No commit</th><th>Tight</th><th>Best configs</th></tr></thead><tbody>{task_rows_html(data['task_profiles'])}</tbody></table>
<section class='callout'><h2>What to keep / what to avoid</h2><div class='grid'><div><h3>Keep</h3><ul><li>Keep the full workflow checklist as the solve-rate leader.</li><li>Keep explicit verification and edge-case language; the tight rewrite suggests structure alone is not enough.</li><li>If optimizing cost rather than maximum solves, no-repro is a viable candidate for a separate cost frontier, but not a replacement for the workflow winner.</li></ul></div><div><h3>Avoid</h3><ul><li>Do not conclude the repro-script step is dead weight from aggregate cost alone; no-repro loses 7 workflow-only cells while gaining 4 variant-only cells.</li><li>Do not compress prompts to terse bullets without another run proving the specificity loss is harmless.</li><li>Do not over-interpret rep numbers as matched seeds; comparisons are paired by task and rep labels but reps are natural stochastic samples.</li></ul></div></div></section>
<section class='callout'><h2>Evidence and caveats</h2><ul><li>Input evidence roots:{evidence}</li><li>All solve counts use <code>reward_binary == 1</code>; invalid rewards are tracked and were zero for these configs.</li><li>The ablation run itself is complete with 321 ok cells plus 3 skipped smoke cells in the batch accounting; all three preflight smoke cells passed. The original workflow and clean baselines are historical result roots, not same-run anchors.</li><li>Claims are local to subset <code>36_v2</code>, three reps, model <code>openai-codex/gpt-5.5</code>, thinking <code>low</code>, and these exact prompt-only configs.</li></ul><h3>Generated artifacts</h3><ul>{outputs}</ul></section>
</main></body></html>"""


def build() -> dict[str, Any]:
    task_ids = tasks()
    metas = {task: task_meta(task) for task in task_ids}
    results = load_results(ALL_CONFIGS, task_ids)
    if PACKET_DIR.exists():
        shutil.rmtree(PACKET_DIR)
    if REPORT_PACKET_DIR.exists():
        shutil.rmtree(REPORT_PACKET_DIR)
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_PACKET_DIR.mkdir(parents=True, exist_ok=True)
    config_summaries = [config_summary(config, results[config], task_ids) for config in ALL_CONFIGS]
    primary_pairs = [pair_summary(comp, results, task_ids, metas, make_packets=True) for comp in COMPARISONS]
    context_pairs = [pair_summary(comp, results, task_ids, metas, make_packets=False) for comp in CONTEXT_COMPARISONS]
    profiles = task_profiles(task_ids, results, metas)
    status = load_json(RUN_DIR / "status.json")
    manifest = load_json(RUN_DIR / "manifest.json")
    data = {
        "run_id": RUN_ID,
        "inputs": {
            "subset": str(SUBSET_PATH.relative_to(ROOT)),
            "tasks": task_ids,
            "model": "openai-codex/gpt-5.5",
            "thinking": "low",
            "reps": REPS,
            "primary_left_anchor": WORKFLOW,
            "configs": ALL_CONFIGS,
            "evidence_roots": [str((RESULT_ROOT / c).relative_to(ROOT)) for c in ALL_CONFIGS] + [str(RUN_DIR.relative_to(ROOT))],
            "comparison_caveat": "The three ablation variants were launched together under gpt55-low-wf-ablation-36v2-r3-w24. Clean low and original workflow are historical same-subset/same-model/same-thinking result roots, not same-run drift anchors.",
        },
        "outputs": {
            "json": str(OUT_JSON.relative_to(ROOT)),
            "config_summary_csv": str(OUT_CONFIG_CSV.relative_to(ROOT)),
            "paired_summary_csv": str(OUT_PAIR_CSV.relative_to(ROOT)),
            "task_profiles_csv": str(OUT_TASK_CSV.relative_to(ROOT)),
            "solve_flip_index_csv": str(OUT_FLIP_CSV.relative_to(ROOT)),
            "packet_dir": str(PACKET_DIR.relative_to(ROOT)),
            "report_packet_dir": str(REPORT_PACKET_DIR.relative_to(ROOT)),
            "html": str(OUT_HTML.relative_to(ROOT)),
        },
        "method_notes": {
            "solve_rule": "Only reward_binary == 1 counts as solved.",
            "paired_cell_rule": "Primary comparisons pair same task, same rep label, same model, same thinking level, left config baseline-wf-only, right config each ablation.",
            "rep_caveat": "Rep labels are natural stochastic samples and are not proven matched random seeds.",
            "packet_classification": "Packet buckets are deterministic heuristics from verifier failures, patch shape, and command traces; direct evidence is included in packet files.",
            "scope": "Prompt-only configs only; OMP/tool-surface rows and behavioral wrappers excluded from claims.",
        },
        "run_status": status,
        "run_manifest_summary": {
            "configs": manifest.get("configs"),
            "selection": manifest.get("selection"),
            "runs": manifest.get("runs"),
            "workers": manifest.get("workers"),
            "model": manifest.get("model"),
            "thinking": manifest.get("thinking"),
            "batch_cells": len(manifest.get("batch_cells", [])),
            "preflight": len(manifest.get("preflight", [])),
        },
        "config_summaries": config_summaries,
        "primary_pair_summaries": primary_pairs,
        "context_pair_summaries": context_pairs,
        "task_profiles": profiles,
    }
    return data


def main() -> None:
    ANALYSIS_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    data = build()
    OUT_JSON.write_text(json.dumps(data, indent=2))
    write_csvs(data)
    OUT_HTML.write_text(render_html(data))
    for path in [OUT_JSON, OUT_CONFIG_CSV, OUT_PAIR_CSV, OUT_TASK_CSV, OUT_FLIP_CSV, OUT_HTML]:
        print("wrote", path.relative_to(ROOT), path.stat().st_size)
    print("packets", sum(1 for _ in PACKET_DIR.rglob("*.md")), "md", sum(1 for _ in PACKET_DIR.rglob("*.json")), "json")


if __name__ == "__main__":
    main()

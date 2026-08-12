#!/usr/bin/env python3
"""Build the testing-skills 1.0 versus 1.1 paired comparison report."""

from __future__ import annotations

import html
import json
import re
import statistics
from collections import Counter
from pathlib import Path
from typing import TypedDict

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
LEFT_CONFIG = "testing-skills@1.0.0"
RIGHT_CONFIG = "testing-skills@1.1.0"
LEFT_ROOT = RESULTS_ROOT / LEFT_CONFIG
RIGHT_ROOT = RESULTS_ROOT / RIGHT_CONFIG
SUBSET_PATH = REPOSITORY_ROOT / "subsets/36_v2_no_wazero.txt"
QUARANTINE_ROOT = Path(
    "/home/will/evals/deep-swe-bench/results/_contaminated/resource-oom/"
    "gpt56-sol-low-testing-skills-1-1-vs-1-0-36v2-no---"
    "f8033fe26f0b5e2b91c55daf3949e3732999301d6e496a75185207f142b78e01"
)
ANALYSIS_PATH = Path(__file__).with_name("comparison-36v2.json")
REPORT_ROOT = REPOSITORY_ROOT / "reports/testing-skills-1.1-vs-1.0-36v2"
REPORT_PATH = REPORT_ROOT / "index.html"
PACKET_ROOT = REPORT_ROOT / "packets"
SKILL_NAMES = ("testing", "fuzzing", "property-based-testing")
SPECIALIST_NAMES = ("fuzzing", "property-based-testing")
SPECIALIST_TECHNIQUE_PATTERN = re.compile(
    r"\b(hypothesis|fast-check|proptest|quickcheck|cargo-fuzz|libfuzzer|"
    r"afl\+\+|testing\.f|rapid\.check)\b",
    re.IGNORECASE,
)


class MetricRecord(TypedDict):
    """Compact numeric result fields used by paired calculations."""

    reward_binary: int
    reward_partial: float
    f2p_passed: int
    f2p_total: int
    p2p_passed: int
    p2p_total: int
    total_tokens: int
    combined_cost_usd: float
    agent_wall_s: float
    tool_calls: int
    turns: int
    patch_bytes: int


SkillReads = TypedDict(
    "SkillReads",
    {
        "testing": bool,
        "fuzzing": bool,
        "property-based-testing": bool,
    },
)


class PairRow(TypedDict):
    """One clean matched task and rep comparison."""

    task: str
    rep: int
    left_solved: bool
    right_solved: bool
    left_result: MetricRecord
    right_result: MetricRecord
    left_changed_paths: list[str]
    right_changed_paths: list[str]
    left_failed_tests: list[str]
    right_failed_tests: list[str]
    right_skill_reads: SkillReads
    right_specialist_technique_in_patch: bool


def read_result_cells(
    root: Path, tasks: set[str]
) -> dict[tuple[str, int], tuple[Path, dict]]:
    """Read available result cells in the selected task and rep domain."""
    cells = {}
    for result_path in root.glob("*/rep*/result.json"):
        task = result_path.parts[-3]
        rep = int(result_path.parts[-2][3:])
        if task in tasks and rep < 3:
            cells[(task, rep)] = (
                result_path.parent,
                json.loads(result_path.read_text()),
            )
    return cells


def read_quarantined_cells(tasks: set[str]) -> dict[tuple[str, int], tuple[Path, dict]]:
    """Read OOM-contaminated cells only for a separate diagnostic ledger."""
    return read_result_cells(QUARANTINE_ROOT, tasks)


def session_text(cell_path: Path) -> str:
    """Concatenate native Pi session records for one result cell."""
    return "\n".join(
        path.read_text(errors="replace")
        for path in sorted((cell_path / "session").glob("*.jsonl"))
    )


def patch_text(cell_path: Path) -> str:
    """Read the model patch when present."""
    path = cell_path / "artifacts/model.patch"
    return path.read_text(errors="replace") if path.exists() else ""


def patch_paths(cell_path: Path) -> list[str]:
    """Extract changed file paths from a model patch."""
    return re.findall(r"^\+\+\+ b/(.+)$", patch_text(cell_path), re.MULTILINE)


def is_test_path(path: str) -> bool:
    """Return whether a path uses a conventional test name or directory."""
    return bool(
        re.search(
            r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.",
            path,
            re.IGNORECASE,
        )
    )


def failed_verifier_tests(cell_path: Path) -> list[str]:
    """Extract failed CTRF test names from one result cell."""
    path = cell_path / "verifier/ctrf.json"
    if not path.exists():
        return []
    report = json.loads(path.read_text())
    results = report.get("results")
    if not isinstance(results, dict):
        raise TypeError(f"CTRF report has no results object: {path}")
    tests = results.get("tests")
    if not isinstance(tests, list):
        raise TypeError(f"CTRF report has no tests list: {path}")
    return [
        str(test.get("name", "unnamed test"))
        for test in tests
        if test.get("status") == "failed"
    ]


def skill_reads(cell_path: Path) -> SkillReads:
    """Return which configured skill entrypoints were read by the model."""
    text = session_text(cell_path)
    return {
        "testing": "/arm/skills/testing/SKILL.md" in text,
        "fuzzing": "/arm/skills/fuzzing/SKILL.md" in text,
        "property-based-testing": (
            "/arm/skills/property-based-testing/SKILL.md" in text
        ),
    }


def skill_advertisement(cell_path: Path) -> dict[str, bool]:
    """Return which skills appeared in the captured initial system prompt."""
    prompt = (cell_path / "initial_context/system_prompt.txt").read_text(
        errors="replace"
    )
    return {name: f"<name>{name}</name>" in prompt for name in SKILL_NAMES}


def outcome_bucket(result: MetricRecord) -> str:
    """Classify the concrete grading failure of an unsolved result."""
    p2p_missing = result.get("p2p_total", 0) - result.get("p2p_passed", 0)
    f2p_missing = result.get("f2p_total", 0) - result.get("f2p_passed", 0)
    if p2p_missing > 0:
        return "cross-scope regression"
    if f2p_missing > 3:
        return "under-implementation"
    if f2p_missing > 0:
        return "missing invariant/guard"
    return "likely variance"


def build_flip_packet(row: PairRow, reciprocal_tasks: set[str]) -> dict:
    """Build a self-contained packet for one binary solve flip."""
    losing_result = row["left_result"] if row["right_solved"] else row["right_result"]
    return {
        "task": row["task"],
        "rep": row["rep"],
        "direction": "gain" if row["right_solved"] else "loss",
        "left": row["left_result"],
        "right": row["right_result"],
        "left_changed_paths": row["left_changed_paths"],
        "right_changed_paths": row["right_changed_paths"],
        "left_failed_tests": row["left_failed_tests"],
        "right_failed_tests": row["right_failed_tests"],
        "right_skill_reads": row["right_skill_reads"],
        "primary_driver": outcome_bucket(losing_result),
        "config_attribution": (
            "likely variance: this task has a gain and a loss across matched reps"
            if row["task"] in reciprocal_tasks
            else "unresolved implementation divergence; no specialist read in this cell"
        ),
    }


def result_metrics(result: dict) -> MetricRecord:
    """Select compact result metrics for the report and flip packets."""
    return {
        "reward_binary": int(result["reward_binary"]),
        "reward_partial": float(result["reward_partial"]),
        "f2p_passed": int(result["f2p_passed"]),
        "f2p_total": int(result["f2p_total"]),
        "p2p_passed": int(result["p2p_passed"]),
        "p2p_total": int(result["p2p_total"]),
        "total_tokens": int(result["total_tokens"]),
        "combined_cost_usd": float(result["combined_cost_usd"]),
        "agent_wall_s": float(result["agent_wall_s"]),
        "tool_calls": int(result["tool_calls"]),
        "turns": int(result["turns"]),
        "patch_bytes": int(result["patch_bytes"]),
    }


def build_analysis() -> dict:
    """Build clean efficacy, delivery, contamination, and churn ledgers."""
    tasks = set(SUBSET_PATH.read_text().splitlines())
    left = read_result_cells(LEFT_ROOT, tasks)
    right = read_result_cells(RIGHT_ROOT, tasks)
    quarantined = read_quarantined_cells(tasks)
    expected_keys = {(task, rep) for task in tasks for rep in range(3)}
    if set(left) != expected_keys:
        raise RuntimeError(f"Left side has {len(left)} cells; expected 105")
    if set(right) | set(quarantined) != expected_keys:
        raise RuntimeError(
            "Canonical and quarantined right cells do not cover 105 cells"
        )
    if set(right) & set(quarantined):
        raise RuntimeError(
            "A right-side cell appears in canonical and quarantine roots"
        )

    rows: list[PairRow] = []
    advertised = Counter()
    left_reads = Counter()
    reads = Counter()
    left_test_patches = 0
    right_test_patches = 0
    for task, rep in sorted(set(left) & set(right)):
        left_path, left_result = left[(task, rep)]
        right_path, right_result = right[(task, rep)]
        left_cell_reads = skill_reads(left_path)
        right_reads = skill_reads(right_path)
        left_reads["testing"] += left_cell_reads["testing"]
        left_reads["fuzzing"] += left_cell_reads["fuzzing"]
        left_reads["property-based-testing"] += left_cell_reads[
            "property-based-testing"
        ]
        for name, present in skill_advertisement(right_path).items():
            advertised[name] += present
        reads["testing"] += right_reads["testing"]
        reads["fuzzing"] += right_reads["fuzzing"]
        reads["property-based-testing"] += right_reads["property-based-testing"]
        left_paths = patch_paths(left_path)
        right_paths = patch_paths(right_path)
        left_test_patches += any(is_test_path(path) for path in left_paths)
        right_test_patches += any(is_test_path(path) for path in right_paths)
        rows.append(
            {
                "task": task,
                "rep": rep,
                "left_solved": left_result.get("reward_binary") == 1,
                "right_solved": right_result.get("reward_binary") == 1,
                "left_result": result_metrics(left_result),
                "right_result": result_metrics(right_result),
                "left_changed_paths": left_paths,
                "right_changed_paths": right_paths,
                "left_failed_tests": failed_verifier_tests(left_path),
                "right_failed_tests": failed_verifier_tests(right_path),
                "right_skill_reads": right_reads,
                "right_specialist_technique_in_patch": bool(
                    SPECIALIST_TECHNIQUE_PATTERN.search(patch_text(right_path))
                ),
            }
        )

    task_directions: dict[str, set[str]] = {}
    for row in rows:
        if row["left_solved"] == row["right_solved"]:
            continue
        direction = "gain" if row["right_solved"] else "loss"
        task_directions.setdefault(row["task"], set()).add(direction)
    reciprocal_tasks = {
        task for task, directions in task_directions.items() if len(directions) == 2
    }

    flip_packets = []
    for row in rows:
        if row["left_solved"] != row["right_solved"]:
            packet = build_flip_packet(row, reciprocal_tasks)
            packet_name = f"{row['task']}__rep{row['rep']}.json"
            packet["packet"] = f"packets/{packet_name}"
            flip_packets.append(packet)

    left_only = sum(row["left_solved"] and not row["right_solved"] for row in rows)
    right_only = sum(row["right_solved"] and not row["left_solved"] for row in rows)
    both = sum(row["left_solved"] and row["right_solved"] for row in rows)
    neither = len(rows) - left_only - right_only - both
    partial_deltas = [
        row["right_result"]["reward_partial"] - row["left_result"]["reward_partial"]
        for row in rows
    ]
    aggregate_fields = (
        "total_tokens",
        "combined_cost_usd",
        "agent_wall_s",
        "tool_calls",
        "turns",
        "patch_bytes",
    )
    aggregates = {}
    for field in aggregate_fields:
        left_total = sum(row["left_result"][field] or 0 for row in rows)
        right_total = sum(row["right_result"][field] or 0 for row in rows)
        aggregates[field] = {
            "left": left_total,
            "right": right_total,
            "delta_percent": (right_total / left_total - 1) * 100,
        }

    specialist_rows: list[PairRow] = [
        row
        for row in rows
        if any(row["right_skill_reads"][name] for name in SPECIALIST_NAMES)
    ]
    contaminated_rows = []
    for (task, rep), (path, result) in sorted(quarantined.items()):
        memory_events = result.get("subject_memory_events")
        if not isinstance(memory_events, dict):
            raise TypeError(f"Result has no subject memory events: {path}")
        contaminated_rows.append(
            {
                "task": task,
                "rep": rep,
                "reward_binary": result.get("reward_binary"),
                "reward_partial": result.get("reward_partial"),
                "subject_oom_kills": memory_events.get("oom_kill", 0),
                "path": str(path),
            }
        )

    return {
        "scope": {
            "left": LEFT_CONFIG,
            "right": RIGHT_CONFIG,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "tasks": 35,
            "reps": 3,
            "intended_pairs": 105,
            "clean_pairs": len(rows),
            "contaminated_pairs": len(contaminated_rows),
            "excluded_task": "wazero-multi-module-snapshots",
            "roles": "same-model config control; only skill routing wording changed",
        },
        "outcomes": {
            "left_solves": sum(row["left_solved"] for row in rows),
            "right_solves": sum(row["right_solved"] for row in rows),
            "left_only": left_only,
            "right_only": right_only,
            "both_solved": both,
            "neither_solved": neither,
            "mean_partial_delta": statistics.mean(partial_deltas),
            "median_partial_delta": statistics.median(partial_deltas),
            "reciprocal_flip_tasks": sorted(reciprocal_tasks),
        },
        "delivery": {
            "advertised": dict(advertised),
            "left_read": dict(left_reads),
            "read": dict(reads),
            "specialist_read_cells": len(specialist_rows),
            "specialist_technique_patch_cells": sum(
                row["right_specialist_technique_in_patch"] for row in specialist_rows
            ),
        },
        "behavior": {
            "left_cells_with_test_patch": left_test_patches,
            "right_cells_with_test_patch": right_test_patches,
            "aggregates": aggregates,
        },
        "specialist_rows": specialist_rows,
        "contaminated_rows": contaminated_rows,
        "flip_packets": flip_packets,
        "ledger": rows,
    }


def outcome_pill(left_solved: bool, right_solved: bool) -> str:
    """Render one paired solve outcome."""
    if not left_solved and right_solved:
        return '<span class="pill good">gain</span>'
    if left_solved and not right_solved:
        return '<span class="pill bad">loss</span>'
    if left_solved:
        return '<span class="pill neutral">both</span>'
    return '<span class="pill neutral">neither</span>'


def render_html(analysis: dict) -> str:
    """Render the self-contained Tailnet report."""
    scope = analysis["scope"]
    outcomes = analysis["outcomes"]
    delivery = analysis["delivery"]
    behavior = analysis["behavior"]
    ledger = analysis["ledger"]
    by_task = {}
    for row in ledger:
        by_task.setdefault(row["task"], []).append(row)
    task_rows = []
    for task in sorted(by_task):
        rows = by_task[task]
        left = sum(row["left_solved"] for row in rows)
        right = sum(row["right_solved"] for row in rows)
        reads = Counter(
            name
            for row in rows
            for name, present in row["right_skill_reads"].items()
            if present
        )
        task_rows.append(
            f"<tr><td><code>{html.escape(task)}</code></td><td>{len(rows)}</td>"
            f"<td>{left}</td><td>{right}</td><td>{right - left:+d}</td>"
            f"<td>{html.escape(', '.join(f'{name} × {count}' for name, count in reads.items()) or '—')}</td></tr>"
        )
    ledger_rows = []
    packet_paths = {
        packet["task"] + f"/{packet['rep']}": packet["packet"]
        for packet in analysis["flip_packets"]
    }
    for row in ledger:
        key = row["task"] + f"/{row['rep']}"
        pair = outcome_pill(row["left_solved"], row["right_solved"])
        if key in packet_paths:
            pair = f'<a href="{html.escape(packet_paths[key])}">{pair}</a>'
        reads = (
            ", ".join(
                name for name, present in row["right_skill_reads"].items() if present
            )
            or "—"
        )
        failed = (
            "<br>".join(html.escape(name) for name in row["right_failed_tests"][:3])
            or "—"
        )
        ledger_rows.append(
            f"<tr><td><code>{html.escape(row['task'])}</code></td><td>{row['rep']}</td>"
            f"<td>{int(row['left_solved'])}</td><td>{int(row['right_solved'])}</td><td>{pair}</td>"
            f"<td>{html.escape(reads)}</td><td>{row['right_result']['reward_partial']:.6f}</td>"
            f"<td class='failure'>{failed}</td></tr>"
        )
    specialist_rows = []
    for row in analysis["specialist_rows"]:
        specialists = [
            name for name in SPECIALIST_NAMES if row["right_skill_reads"][name]
        ]
        specialist_rows.append(
            f"<tr><td><code>{html.escape(row['task'])}</code></td><td>{row['rep']}</td>"
            f"<td>{html.escape(', '.join(specialists))}</td>"
            f"<td>{int(row['left_solved'])} → {int(row['right_solved'])}</td>"
            f"<td>{'yes' if row['right_specialist_technique_in_patch'] else 'no—ordinary example/parametrized tests'}</td></tr>"
        )
    contaminated_rows = "".join(
        f"<tr><td><code>{html.escape(row['task'])}</code></td><td>{row['rep']}</td>"
        f"<td>{row['reward_binary']}</td><td>{row['subject_oom_kills']}</td></tr>"
        for row in analysis["contaminated_rows"]
    )
    reciprocal = ", ".join(
        f"<code>{html.escape(task)}</code>"
        for task in outcomes["reciprocal_flip_tasks"]
    )
    token_delta = behavior["aggregates"]["total_tokens"]["delta_percent"]
    cost_delta = behavior["aggregates"]["combined_cost_usd"]["delta_percent"]
    wall_delta = behavior["aggregates"]["agent_wall_s"]["delta_percent"]
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%232563eb%22/></svg>"><title>Testing skills 1.1 vs 1.0 · 36v2</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#667085;--blue:#2563eb;--green:#138a5b;--red:#c43d4b;--amber:#b7791f;--line:#dce3ed}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}}main{{max-width:1280px;margin:auto;padding:42px 24px 64px}}.hero{{background:linear-gradient(135deg,#15223b,#244b83);color:white;border-radius:22px;padding:38px;box-shadow:0 16px 45px #15223b22}}h1{{font-size:clamp(2rem,5vw,3.6rem);line-height:1.04;margin:.3rem 0 1rem;max-width:20ch}}h2{{margin:34px 0 14px}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#9cc2ff;font-size:.78rem}}.subtitle{{max-width:900px;color:#d9e7ff;font-size:1.12rem}}.pills{{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}}.pill,.tag{{display:inline-block;border-radius:999px;padding:4px 9px;font-size:.76rem;font-weight:800;white-space:nowrap}}.hero .pill{{background:#ffffff18;color:#fff;border:1px solid #ffffff30}}.pill.good{{background:#dcf7ea;color:#08734a}}.pill.bad{{background:#fee7ea;color:#a72f3d}}.pill.caution,.tag{{background:#fff0d2;color:#8b5b0c}}.pill.neutral{{background:#e8eef7;color:#475467}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:20px 0}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px}}.stat b{{display:block;font-size:1.8rem;line-height:1.1}}.stat span{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.card,.surface,.callout{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px 20px}}.surface{{padding:8px 20px 18px;overflow:auto}}.callout{{margin-top:18px;border-left:5px solid var(--blue)}}.callout.bad{{border-left-color:var(--red)}}.callout.caution{{border-left-color:var(--amber)}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;vertical-align:top;padding:10px 9px;border-bottom:1px solid var(--line)}}th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}code{{font-size:.8rem}}.failure{{max-width:460px}}a{{color:var(--blue)}}footer{{margin-top:28px;color:var(--muted)}}@media(max-width:850px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}main{{padding:20px 12px 40px}}.hero{{padding:26px}}}}
</style></head><body><main><section class="hero"><div class="eyebrow">Same-model config control · GPT-5.6 Sol low · 36v2</div><h1>Better discovery, no clean score gain</h1><p class="subtitle">Rewriting the skill descriptions activated fuzzing or property-testing reads in five clean cells, up from zero. On the 103 uncontaminated matched cells, solves stayed exactly flat while 28 cells flipped direction.</p><div class="pills"><span class="pill">{scope["clean_pairs"]} clean pairs</span><span class="pill">{outcomes["left_solves"]} → {outcomes["right_solves"]} solves</span><span class="pill">{outcomes["right_only"]} gains</span><span class="pill">{outcomes["left_only"]} losses</span><span class="pill">5 specialist reads</span></div></section>
<section class="stats"><div class="stat"><b>0</b><span>net clean solves</span></div><div class="stat"><b>28</b><span>solve flips</span></div><div class="stat"><b>5/103</b><span>specialist-read cells</span></div><div class="stat"><b>{token_delta:+.1f}%</b><span>token change</span></div><div class="stat"><b>{wall_delta:+.1f}%</b><span>wall-time change</span></div></section>
<div class="callout"><strong>Verdict:</strong> The wording revision fixed the first routing problem—it made specialists discoverable enough to be opened—but did not yet change testing practice. All five specialist-read patches still used ordinary example or parametrized tests. Clean efficacy was flat: {outcomes["left_solves"]}/{scope["clean_pairs"]} on both sides.</div>
<div class="callout caution"><strong>Do not read the flat score as stability.</strong> There were {outcomes["right_only"]} gains and {outcomes["left_only"]} losses. Seven tasks flipped in both directions across reps: {reciprocal}. That reciprocal churn is stronger evidence of implementation variance than a systematic wording effect.</div>
<div class="callout bad"><strong>Resource exclusion:</strong> Two revised-skill SQL Formatter cells solved but recorded 19 and 21 subject OOM kills. They are quarantined and excluded from the 103-pair efficacy result. <code>wazero</code> remains excluded from both configs.</div>
<h2>What changed</h2><div class="grid"><div class="card"><h3>Specialist discovery improved</h3><p>All three skills were advertised in {delivery["advertised"]["testing"]}/{scope["clean_pairs"]} clean prompts. The revised run read <code>testing</code> in {delivery["read"]["testing"]} cells, <code>fuzzing</code> in {delivery["read"]["fuzzing"]}, and <code>property-based-testing</code> in {delivery["read"]["property-based-testing"]}. Version 1.0 read neither specialist in any cell.</p></div><div class="card"><h3>Technique adoption did not</h3><p>Fuzzing was opened on two HTTPX reps; property testing was opened on all three PSD reps. None added a fuzz target, property-testing framework, generator/shrinker, or generated invariant suite. The visible behavior remained ordinary example and parametrized tests.</p></div><div class="card"><h3>Specialist outcomes were mixed</h3><p>HTTPX stayed solved in both specialist-read reps. PSD produced one gain, one loss, and one unchanged failure. This is not evidence that specialist activation caused a score gain.</p></div><div class="card"><h3>Execution became slower</h3><p>Across clean pairs, native tokens rose {token_delta:+.1f}%, recorded cost {cost_delta:+.1f}%, and agent wall time {wall_delta:+.1f}%. Tool calls and turns fell slightly. The revision did not buy lower execution cost.</p></div></div>
<h2>Specialist-read cells</h2><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Specialist</th><th>Solve</th><th>Specialist method in patch?</th></tr></thead><tbody>{"".join(specialist_rows)}</tbody></table></div>
<h2>Clean task-level outcomes</h2><p>SQL Formatter has one clean pair because two revised cells were quarantined.</p><div class="surface"><table><thead><tr><th>Task</th><th>Clean reps</th><th>1.0 solves</th><th>1.1 solves</th><th>Δ</th><th>1.1 skill reads</th></tr></thead><tbody>{"".join(task_rows)}</tbody></table></div>
<h2>Churn interpretation</h2><div class="grid"><div class="card"><h3>Matched outcome counts</h3><p>{outcomes["both_solved"]} both solved, {outcomes["neither_solved"]} neither solved, {outcomes["right_only"]} revised-only, and {outcomes["left_only"]} old-only. Mean partial-reward delta was {outcomes["mean_partial_delta"]:+.6f}; median was {outcomes["median_partial_delta"]:+.6f}.</p></div><div class="card"><h3>Packet rule</h3><p>Every binary solve flip receives a linked JSON packet containing paired metrics, changed files, failed verifier tests, skill reads, and a concrete grading-failure bucket. Reciprocal task flips are explicitly attributed to likely variance rather than the wording change.</p></div></div>
<h2>Quarantined resource events</h2><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Solved</th><th>Subject OOM kills</th></tr></thead><tbody>{contaminated_rows}</tbody></table></div>
<h2>Complete clean paired ledger</h2><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>1.0</th><th>1.1</th><th>Pair</th><th>1.1 skill reads</th><th>1.1 partial</th><th>1.1 failed tests</th></tr></thead><tbody>{"".join(ledger_rows)}</tbody></table></div>
<div class="callout"><strong>Next design hypothesis:</strong> Description wording is sufficient to trigger occasional specialist reads, but not enough to make the agent execute the method. The next iteration should test a small, explicit handoff inside each specialist: after reading, name one concrete target/property and either implement it or state why the repository cannot support it. That should be A/B tested on the five activation cells plus matched counterexamples—not rolled out based on this flat aggregate.</div>
<footer>Generated from canonical result records, native Pi sessions, captured prompts, model patches, and CTRF verifier reports. Primary efficacy excludes quarantined resource-contaminated cells. Data: <code>analysis/testing-skills-1.1.0/comparison-36v2.json</code>.</footer></main></body></html>"""


def main() -> None:
    """Write the evidence JSON, flip packets, and self-contained HTML report."""
    analysis = build_analysis()
    ANALYSIS_PATH.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    for packet in analysis["flip_packets"]:
        packet_path = REPORT_ROOT / packet["packet"]
        packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(render_html(analysis))
    print(f"wrote {ANALYSIS_PATH}")
    print(f"wrote {len(analysis['flip_packets'])} flip packets")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the final DeepSeek V4 WNA16 12_v2 reconciliation report."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from statistics import mean, median

REPORT_DIR = Path(__file__).resolve().parent
REPO_ROOT = REPORT_DIR.parents[1]
RESULTS_ROOT = REPO_ROOT / "results"

WNA16_RESULT_BASE = Path(
    "deepseek-v4-flash-0731-wna16-quality-12035985/max/"
    "baseline-vllm-deepseek-v4-flash-0731-wna16@1.2.0"
)
WNA16_THROUGHPUT_ROOT = RESULTS_ROOT / "_throughput/deepseek-v4-wna16-quality-speed/max"
GGUF_MAX_ROOT = (
    RESULTS_ROOT / "deepseek-v4-flash-0731-q8-fast-prefill/max/"
    "baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0"
)

ORIGINAL_PLAN_IDENTITY = (
    "sha256:87e818a89e65d49f3d250fc1e36809eadb455c95508784e770af8e74bee7a13c"
)
FIRST_RERUN_PLAN_IDENTITY = (
    "sha256:cdcd7deb18f2c87cbab8319bd857ab9899bfa0c2740b81b3eed0a386cfe413b9"
)
REMAINING_RERUN_PLAN_IDENTITY = (
    "sha256:df948cbb5e573099505ba9a7a3b290ba7ab132cf6942aee8921711b21bc7f2d9"
)
MOBLY_RERUN_PLAN_IDENTITY = (
    "sha256:2bb2651c3a1e2b901f19a3a4f928eb85a592eae3f4b55c63777733d38c20d6a3"
)

FINAL_WNA16_TASK_SOURCES = {
    "superjson-error-stack-serialization": (
        "workers-1",
        "Original run",
        ORIGINAL_PLAN_IDENTITY,
    ),
    "participle-grammar-conflict-analysis": (
        "workers-1",
        "Original run",
        ORIGINAL_PLAN_IDENTITY,
    ),
    "langchain-request-coalescing": (
        "workers-1",
        "Original run",
        ORIGINAL_PLAN_IDENTITY,
    ),
    "tengo-callable-instance-isolation": (
        "workers-1",
        "Original run",
        ORIGINAL_PLAN_IDENTITY,
    ),
    "obsidian-linter-link-format-conversion": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun A",
        FIRST_RERUN_PLAN_IDENTITY,
    ),
    "dateutil-rfc5545-timezone-interop": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "claude-code-by-agents-recursive-delegation": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "go-critic-doc-link-checker": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "adaptix-name-mapping-aliases": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "goreleaser-retry-publish-auditing": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "sql-formatter-bigquery-pipe-formatting": (
        "workers-1-watchdog-disabled",
        "Watchdog-disabled rerun B",
        REMAINING_RERUN_PLAN_IDENTITY,
    ),
    "mobly-grouped-test-barriers": (
        "workers-1-mobly-fail-fast",
        "Mobly fail-fast rerun",
        MOBLY_RERUN_PLAN_IDENTITY,
    ),
}

RUN_STATUS_SPECS = [
    (
        "Original one-worker run",
        (
            "dsv4-wna16-quality-speed-max-12v2-r1-w1--"
            "b06215a20f419e91a729fe402643e3b16d35a667bc29fd1cf5e5557664d3e89a"
        ),
        "Four usable results; seven watchdog closures and Mobly timeout were replaced.",
    ),
    (
        "First watchdog-disabled rerun",
        (
            "dsv4-wna16-quality-speed-max-watchdog-disabled-7--"
            "521e35a13b467993d56e14bd70e4e597889d51bc3caade465e459ce3dad85718"
        ),
        "Obsidian is usable; Dateutil verifier OOM stopped the launch.",
    ),
    (
        "Remaining six reruns",
        (
            "dsv4-wna16-quality-speed-max-watchdog-disabled-r--"
            "efdc9b053ffafc76d3294bcd10daa3fa53630327f5b773391aa595844422acbd"
        ),
        "All six completed with normal verification.",
    ),
    (
        "Mobly fail-fast rerun",
        (
            "dsv4-wna16-quality-speed-max-mobly-fail-fast-w1--"
            "061d4d23147a413e4da3f002d667b2c7ac4210af692199c6a24fe2db7fab1580"
        ),
        "Completed with normal verification; the 120-second suite guard did not fire.",
    ),
]

TASK_LABELS = {
    "superjson-error-stack-serialization": "SuperJSON",
    "obsidian-linter-link-format-conversion": "Obsidian",
    "participle-grammar-conflict-analysis": "Participle",
    "dateutil-rfc5545-timezone-interop": "Dateutil",
    "langchain-request-coalescing": "LangChain",
    "claude-code-by-agents-recursive-delegation": "Recursive delegation",
    "go-critic-doc-link-checker": "go-critic",
    "mobly-grouped-test-barriers": "Mobly",
    "tengo-callable-instance-isolation": "Tengo",
    "adaptix-name-mapping-aliases": "Adaptix",
    "goreleaser-retry-publish-auditing": "GoReleaser",
    "sql-formatter-bigquery-pipe-formatting": "SQL Formatter",
}


@dataclass(frozen=True)
class TaskResult:
    task: str
    label: str
    source: str
    source_root: str
    plan_identity: str
    binary: float
    partial: float
    f2p: float
    f2p_passed: int
    f2p_total: int
    p2p: float
    p2p_passed: int
    p2p_total: int
    agent_wall_s: float
    output_tokens: int
    input_tokens: int
    turns: int
    patch_bytes: int
    timed_out: bool
    verifier_exit: int | str
    result_path: str


@dataclass(frozen=True)
class AggregateMetrics:
    trajectories: int
    solves: int
    mean_partial: float
    mean_f2p: float
    mean_p2p: float
    agent_hours: float
    mean_cell_minutes: float
    median_cell_minutes: float
    output_tokens: int
    input_tokens: int
    timeouts: int


def load_result(path: Path, source: str, source_root: str) -> TaskResult:
    """Load one graded trajectory while preserving its exact source identity."""
    record = json.loads(path.read_text())
    return TaskResult(
        task=record["task"],
        label=TASK_LABELS[record["task"]],
        source=source,
        source_root=source_root,
        plan_identity=record["launch_plan_identity"],
        binary=float(record["reward_binary"]),
        partial=float(record["reward_partial"]),
        f2p=float(record["f2p"]),
        f2p_passed=int(record["f2p_passed"]),
        f2p_total=int(record["f2p_total"]),
        p2p=float(record["p2p"]),
        p2p_passed=int(record["p2p_passed"]),
        p2p_total=int(record["p2p_total"]),
        agent_wall_s=float(record["agent_wall_s"]),
        output_tokens=int(record["output_tokens"]),
        input_tokens=int(record["input_tokens"]),
        turns=int(record["turns"]),
        patch_bytes=int(record["patch_bytes"]),
        timed_out=bool(record["agent_timed_out"]),
        verifier_exit=record["verifier_exit"],
        result_path=str(path.relative_to(REPO_ROOT)),
    )


def load_final_wna16_results() -> list[TaskResult]:
    """Select exactly one canonical final WNA16 result for each 12_v2 task."""
    results = []
    for task, (
        source_root,
        source,
        expected_plan_identity,
    ) in FINAL_WNA16_TASK_SOURCES.items():
        path = (
            WNA16_THROUGHPUT_ROOT
            / source_root
            / WNA16_RESULT_BASE
            / task
            / "rep0/result.json"
        )
        result = load_result(path, source, source_root)
        if result.plan_identity != expected_plan_identity:
            raise ValueError(
                f"WNA16 result plan identity drift for {task}: "
                f"expected={expected_plan_identity}; observed={result.plan_identity}"
            )
        results.append(result)
    if len(results) != 12 or len({result.task for result in results}) != 12:
        raise ValueError("WNA16 final selection must contain 12 unique tasks")
    return results


def load_gguf_max_results(tasks: list[str]) -> list[TaskResult]:
    """Load the matched one-pass IQ2_XXS GGUF max results for context."""
    return [
        load_result(
            GGUF_MAX_ROOT / task / "rep0/result.json",
            "IQ2_XXS GGUF max",
            "llama.cpp-max",
        )
        for task in tasks
    ]


def aggregate_results(results: list[TaskResult]) -> AggregateMetrics:
    """Compute unweighted task means and summed trajectory cost fields."""
    return AggregateMetrics(
        trajectories=len(results),
        solves=sum(result.binary > 0 for result in results),
        mean_partial=mean(result.partial for result in results),
        mean_f2p=mean(result.f2p for result in results),
        mean_p2p=mean(result.p2p for result in results),
        agent_hours=sum(result.agent_wall_s for result in results) / 3600,
        mean_cell_minutes=mean(result.agent_wall_s for result in results) / 60,
        median_cell_minutes=median(result.agent_wall_s for result in results) / 60,
        output_tokens=sum(result.output_tokens for result in results),
        input_tokens=sum(result.input_tokens for result in results),
        timeouts=sum(result.timed_out for result in results),
    )


def load_run_statuses() -> list[dict[str, object]]:
    """Load the structured states used to reconcile the original and reruns."""
    statuses = []
    for label, run_dir_name, disposition in RUN_STATUS_SPECS:
        path = RESULTS_ROOT / "_runs" / run_dir_name / "status.json"
        status = json.loads(path.read_text())
        statuses.append(
            {
                "label": label,
                "run_dir": run_dir_name,
                "state": status["state"],
                "stage": status["stage"],
                "started_at": status.get("started_at"),
                "updated_at": status.get("updated_at"),
                "counts": status["counts"],
                "active_cell_ids": status.get("active_cell_ids", []),
                "disposition": disposition,
            }
        )
    return statuses


def percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def token_count(value: int) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.2f}M"
    return f"{value / 1_000:.0f}K"


def minutes(value: float) -> str:
    return f"{value / 60:.1f}m"


def status_tag(state: str) -> str:
    style = "good" if state == "completed" else "caution"
    return f'<span class="tag {style}">{escape(state)}</span>'


def outcome_tag(result: TaskResult) -> str:
    if result.binary > 0:
        return '<span class="tag good">solve</span>'
    if result.partial >= 0.98:
        return '<span class="tag caution">near</span>'
    if result.partial < 0.5:
        return '<span class="tag bad">low</span>'
    return '<span class="tag neutral">partial</span>'


def build_task_rows(
    wna16_results: list[TaskResult],
    gguf_by_task: dict[str, TaskResult],
) -> str:
    rows = []
    for result in wna16_results:
        gguf = gguf_by_task[result.task]
        delta = result.partial - gguf.partial
        delta_class = "good" if delta >= 0 else "bad"
        rows.append(
            "<tr>"
            f"<td><strong>{escape(result.label)}</strong><br>"
            f'<span class="muted tiny">{escape(result.source)}</span></td>'
            f"<td>{outcome_tag(result)}</td>"
            f'<td class="num">{percent(result.partial)}</td>'
            f'<td class="num">{result.f2p_passed}/{result.f2p_total}</td>'
            f'<td class="num">{result.p2p_passed}/{result.p2p_total}</td>'
            f'<td class="num">{minutes(result.agent_wall_s)}</td>'
            f'<td class="num">{token_count(result.output_tokens)}</td>'
            f'<td class="num">{percent(gguf.partial)}</td>'
            f'<td class="num {delta_class}">{delta * 100:+.2f}</td>'
            "</tr>"
        )
    return "".join(rows)


def build_status_rows(statuses: list[dict[str, object]]) -> str:
    rows = []
    for status in statuses:
        counts = status["counts"]
        active_cell_ids = status["active_cell_ids"]
        assert isinstance(counts, dict)
        assert isinstance(active_cell_ids, list)
        rows.append(
            "<tr>"
            f"<td><strong>{escape(str(status['label']))}</strong></td>"
            f"<td>{status_tag(str(status['state']))}</td>"
            f'<td class="num">{counts.get("batch_done", 0)}/'
            f"{counts.get('batch_total', 0)}</td>"
            f'<td class="num">{len(active_cell_ids)}</td>'
            f"<td>{escape(str(status['disposition']))}</td>"
            "</tr>"
        )
    return "".join(rows)


def build_report_html(
    wna16_results: list[TaskResult],
    wna16: AggregateMetrics,
    gguf: AggregateMetrics,
    statuses: list[dict[str, object]],
) -> str:
    """Render the final self-contained HTML report."""
    gguf_by_task = {
        result.task: result
        for result in load_gguf_max_results([result.task for result in wna16_results])
    }
    speedup = gguf.agent_hours / wna16.agent_hours
    output_ratio = wna16.output_tokens / gguf.output_tokens
    non_sql = [
        result
        for result in wna16_results
        if result.task != "sql-formatter-bigquery-pipe-formatting"
    ]
    non_sql_partial = mean(result.partial for result in non_sql)
    non_sql_p2p = mean(result.p2p for result in non_sql)
    task_rows = build_task_rows(wna16_results, gguf_by_task)
    status_rows = build_status_rows(statuses)
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>DeepSeek V4 WNA16 · final 12_v2 results</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px;--max:1260px}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.1),transparent 30%),linear-gradient(180deg,#f8fbff,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5}}.wrap{{max-width:var(--max);margin:auto;padding:28px 20px 44px}}.hero,section{{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}}.hero{{padding:clamp(24px,4vw,40px)}}section{{margin-top:20px;padding:clamp(18px,3vw,28px)}}h1,h2,h3{{margin:0;line-height:1.08;letter-spacing:-.03em}}h1{{font-size:clamp(2.2rem,4.8vw,4.4rem);max-width:18ch;margin-top:14px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}}.subtitle,.muted{{color:var(--muted)}}.subtitle{{max-width:82ch;font-size:1.06rem}}.tiny{{font-size:.78rem}}.pills{{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}}.pill,.tag{{display:inline-flex;padding:7px 11px;border-radius:999px;font-size:12px;font-weight:800}}.neutral{{color:#1d3fb8}}.pill.neutral,.tag.neutral{{background:#eef3ff}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.caution,.tag.caution{{background:var(--amber-soft);color:#8b6200}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:24px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.06em}}.stat .value{{display:block;font-size:1.75rem;font-weight:900;margin-top:8px}}.stat .sub{{display:block;color:var(--muted);font-size:.84rem;margin-top:5px}}.head{{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:16px}}.head p{{margin:6px 0 0;max-width:82ch}}.table-wrap{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:.9rem}}th,td{{padding:11px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.05em;color:var(--muted);background:var(--surface-2)}}.num{{text-align:right;font-variant-numeric:tabular-nums}}td.good{{color:var(--green);font-weight:800}}td.bad{{color:var(--red);font-weight:800}}.callout{{margin-top:16px;padding:15px 17px;border-radius:14px;background:#f4f7ff;border-left:5px solid var(--blue)}}.callout.good{{background:var(--green-soft);border-color:var(--green);color:#125f41}}.callout.bad{{background:var(--red-soft);border-color:var(--red);color:#8f302b}}.grid{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.card{{border:1px solid var(--line);border-radius:18px;padding:17px;background:var(--surface)}}.card p{{margin:9px 0 0;color:var(--muted)}}.bar{{height:9px;background:#e8edf5;border-radius:99px;margin-top:15px;overflow:hidden}}.bar i{{display:block;height:100%;background:var(--blue);border-radius:99px}}code{{background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}}.foot{{color:var(--muted);font-size:.8rem;margin:18px 4px 0}}
@media(max-width:900px){{.stats{{grid-template-columns:repeat(2,minmax(0,1fr))}}.grid{{grid-template-columns:1fr}}}}@media(max-width:620px){{.wrap{{padding:14px 10px 28px}}.stats{{grid-template-columns:1fr}}th,td{{padding:9px 8px}}}}
</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">Final reconstructed denominator · 12 tasks · 1 trajectory each</span><h1>Everything finished. WNA16 completed all 12 tasks, but solved none.</h1><p class="subtitle">The final set keeps four normally graded results from the original one-worker run, replaces seven false watchdog closures with watchdog-disabled trajectories, and replaces the Mobly timeout with the fail-fast-verifier rerun. Every selected cell has a nonempty patch, verifier exit 0, and complete F2P/P2P grading.</p>
<div class="pills"><span class="pill good">12/12 final cells verified</span><span class="pill bad">0/12 strict solves</span><span class="pill caution">44.95% mean feature pass rate</span><span class="pill neutral">2.06× faster than GGUF max</span></div>
<div class="stats"><div class="stat"><span class="label">Strict solves</span><span class="value">0/12</span><span class="sub">GGUF max: 6/12</span></div><div class="stat"><span class="label">Mean partial</span><span class="value">{percent(wna16.mean_partial)}</span><span class="sub">GGUF max: {percent(gguf.mean_partial)}</span></div><div class="stat"><span class="label">Mean F2P</span><span class="value">{percent(wna16.mean_f2p)}</span><span class="sub">GGUF max: {percent(gguf.mean_f2p)}</span></div><div class="stat"><span class="label">Mean P2P</span><span class="value">{percent(wna16.mean_p2p)}</span><span class="sub">GGUF max: {percent(gguf.mean_p2p)}</span></div><div class="stat"><span class="label">Summed agent time</span><span class="value">{wna16.agent_hours:.2f}h</span><span class="sub">GGUF max: {gguf.agent_hours:.2f}h</span></div></div></header>
<section><div class="head"><div><h2>Run reconciliation</h2><p class="muted">A failed intermediate launch is retained as provenance, not counted as a final quality result. All structured states now have zero active cells.</p></div></div><div class="table-wrap"><table><thead><tr><th>Launch</th><th>State</th><th class="num">Cells done</th><th class="num">Active</th><th>Disposition</th></tr></thead><tbody>{status_rows}</tbody></table></div><div class="callout good"><strong>Completion audit:</strong> the original run, remaining-six run, and Mobly run are canonically completed. The first rerun is canonically failed because of the Dateutil verifier OOM; its valid Obsidian result is retained, while Dateutil comes from the later successful rerun.</div></section>
<section><div class="head"><div><h2>Complete task denominator</h2><p class="muted">WNA16 runs Pi 0.84.1 on vLLM with max reasoning. The comparison column is the same model family under IQ2_XXS GGUF, llama.cpp, Pi 0.84.0, and max reasoning. “Δ partial” is WNA16 minus GGUF percentage points.</p></div></div><div class="table-wrap"><table><thead><tr><th>Task / source</th><th>WNA16 outcome</th><th class="num">WNA16 partial</th><th class="num">F2P</th><th class="num">P2P</th><th class="num">Agent time</th><th class="num">Output</th><th class="num">GGUF partial</th><th class="num">Δ partial</th></tr></thead><tbody>{task_rows}</tbody></table></div><div class="callout"><strong>Input-token totals are omitted from the comparison.</strong> vLLM counts repeated context as input and reports no cache-read tokens, while llama.cpp separates cached tokens. Those raw input totals are not comparable. Output tokens and agent wall time remain descriptive.</div></section>
<section><div class="head"><div><h2>Capability shape</h2></div></div><div class="grid"><div class="card"><h3>Strong near-completions</h3><p>Obsidian, Dateutil, Adaptix, and Mobly all exceeded 97.8% partial reward. None was a strict solve: their feature coverage was 55/60, 54/67, 3/44, and 60/79 respectively. Large preservation suites make Dateutil and Adaptix partial reward look closer to complete than their feature coverage.</p><div class="bar"><i style="width:{wna16.mean_f2p * 100:.2f}%"></i></div></div><div class="card"><h3>One cross-scope collapse</h3><p>SQL Formatter passed 0/26 feature tests and only 52/5,709 preservation tests, for 0.91% partial reward. Excluding that one task, WNA16 mean partial rises to {percent(non_sql_partial)} and mean P2P to {percent(non_sql_p2p)}.</p><div class="bar"><i style="width:0.91%;background:var(--red)"></i></div></div><div class="card"><h3>Speed did not come from shorter output</h3><p>WNA16 used {token_count(wna16.output_tokens)} output tokens versus {token_count(gguf.output_tokens)} for GGUF max ({output_ratio:.2f}×), yet summed agent time was {wna16.agent_hours:.2f} hours versus {gguf.agent_hours:.2f} hours. This serving stack was {speedup:.2f}× faster on final selected trajectories.</p><div class="bar"><i style="width:{min(100, 100 / speedup):.2f}%;background:var(--green)"></i></div></div></div></section>
<section><div class="head"><div><h2>Bottom line</h2></div></div><div class="callout bad"><strong>The clean quality result is 0/12 strict solves.</strong> WNA16 trailed GGUF max on 11 tasks and tied Participle on partial reward. GGUF max solved six tasks. WNA16’s largest gaps were SQL Formatter (−99.06 points), GoReleaser (−37.93), recursive delegation (−15.79), and go-critic (−10.53).</div><div class="callout good"><strong>The clean operational result is that the rerun strategy worked.</strong> Disabling the false watchdog produced ordinary patches and grades for all seven affected tasks. The Mobly fail-fast verifier completed normally and did not misclassify the new patch.</div><div class="callout"><strong>Interpretation limit:</strong> this is one trajectory per task and a reconstructed final set, not one untouched launch. WNA16 and GGUF also differ in quantization, serving engine, Pi version, context window, and Mobly verifier revision. Treat the result as a capability-shape contrast, not a quantization-only causal claim.</div></section>
<div class="foot">Generated {datetime.now(UTC).isoformat(timespec="seconds")} · Data: <code>comparison.json</code> · Final WNA16 source mapping is pinned by launch-plan SHA-256.</div></div></body></html>"""


def main() -> None:
    wna16_results = load_final_wna16_results()
    gguf_results = load_gguf_max_results([result.task for result in wna16_results])
    wna16_metrics = aggregate_results(wna16_results)
    gguf_metrics = aggregate_results(gguf_results)
    statuses = load_run_statuses()

    if any(status["active_cell_ids"] for status in statuses):
        raise ValueError("reconciled runs must have zero active cells")
    if any(result.verifier_exit != 0 for result in wna16_results):
        raise ValueError("all final WNA16 results must have verifier exit 0")
    if any(result.timed_out for result in wna16_results):
        raise ValueError("all final WNA16 results must avoid agent timeout")

    comparison = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": {
            "subset": "12_v2",
            "reps": 1,
            "thinking": "max",
            "final_result_rule": "four original + seven watchdog-disabled + Mobly fail-fast",
        },
        "wna16": asdict(wna16_metrics),
        "gguf_max": asdict(gguf_metrics),
        "wna16_tasks": [asdict(result) for result in wna16_results],
        "gguf_max_tasks": [asdict(result) for result in gguf_results],
        "run_statuses": statuses,
    }
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    (REPORT_DIR / "comparison.json").write_text(
        json.dumps(comparison, indent=2, sort_keys=True) + "\n"
    )
    (REPORT_DIR / "index.html").write_text(
        build_report_html(
            wna16_results,
            wna16_metrics,
            gguf_metrics,
            statuses,
        )
    )
    print(f"wrote {REPORT_DIR / 'comparison.json'}")
    print(f"wrote {REPORT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()

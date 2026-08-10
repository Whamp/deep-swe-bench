#!/usr/bin/env python3
"""Build the matched Ornith and Gemma pi-check comparison report."""

from __future__ import annotations

import html
import json
import statistics
import subprocess
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
WORKTREE_ROOT = REPORT_DIR.parents[1]
DATA_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=WORKTREE_ROOT,
        text=True,
    ).strip()
).parent
OUTPUT_HTML = REPORT_DIR / "index.html"
RESULT_ROOTS = {
    "gemma_baseline": DATA_ROOT / "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0",
    "gemma_pi_check": DATA_ROOT / "results/gemma-4-31b/high/pi-check@1.1.0",
    "ornith_raw": DATA_ROOT / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0",
    "ornith_guard": DATA_ROOT / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.1.0",
    "ornith_pi_check": DATA_ROOT / "results/ornith-1.0-35b/high/pi-check@1.2.0",
}
LABELS = {
    "gemma_baseline": "Gemma baseline",
    "gemma_pi_check": "Gemma + pi-check",
    "ornith_adjusted": "Ornith timeout-adjusted baseline",
    "ornith_pi_check": "Ornith + timeout360 + pi-check",
}


def load_result_cells(root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load result cells keyed by task and rep."""
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for path in root.glob("*/rep*/result.json"):
        result = json.loads(path.read_text())
        cells[(result["task"], int(result["rep"]))] = result
    return cells


def nonzero_exit(value: object) -> bool:
    """Return whether a recorded exit represents a failure."""
    return value not in (0, "0", None, False)


def aggregate_result_cells(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate the metrics used by the cross-model comparison."""
    values = list(cells.values())
    partials = [float(value["reward_partial"]) for value in values]
    return {
        "cells": len(values),
        "solves": sum(float(value["reward_binary"]) >= 1 for value in values),
        "mean": statistics.fmean(partials),
        "median": statistics.median(partials),
        "timeouts": sum(bool(value["agent_timed_out"]) for value in values),
        "agent_exits": sum(nonzero_exit(value["agent_exit"]) for value in values),
        "verifier_exits": sum(nonzero_exit(value["verifier_exit"]) for value in values),
        "tokens": sum(int(value["total_tokens"]) for value in values),
        "wall_s": sum(float(value["agent_wall_s"]) for value in values),
    }


def relative_delta(current: float, previous: float) -> str:
    """Format the relative change between two nonzero metrics."""
    return f"{(current / previous - 1) * 100:+.1f}%" if previous else "n/a"


def metric_row(label: str, values: list[str]) -> str:
    """Render one four-way metric row."""
    return f"<tr><td>{html.escape(label)}</td>{''.join(f'<td>{value}</td>' for value in values)}</tr>"


def build_report() -> str:
    """Build the self-contained matched comparison report."""
    results = {name: load_result_cells(root) for name, root in RESULT_ROOTS.items()}
    original = results["ornith_raw"]
    guard = results["ornith_guard"]
    adjusted = {key: guard.get(key, value) for key, value in original.items()}
    results["ornith_adjusted"] = adjusted
    comparison_names = [
        "gemma_baseline",
        "gemma_pi_check",
        "ornith_adjusted",
        "ornith_pi_check",
    ]
    expected_cells = set(results["gemma_baseline"])
    assert len(expected_cells) == 36
    for name in comparison_names:
        assert set(results[name]) == expected_cells, (
            f"{name} does not match the 36-cell grid"
        )
    metrics = {name: aggregate_result_cells(results[name]) for name in comparison_names}

    ornith_delta = {
        key: float(results["ornith_pi_check"][key]["reward_partial"])
        - float(adjusted[key]["reward_partial"])
        for key in expected_cells
    }
    cross_delta = {
        key: float(results["ornith_pi_check"][key]["reward_partial"])
        - float(results["gemma_pi_check"][key]["reward_partial"])
        for key in expected_cells
    }
    gemma_solves = [
        key
        for key, value in results["gemma_pi_check"].items()
        if float(value["reward_binary"]) >= 1
    ]
    assert len(gemma_solves) == 2

    ordered = [metrics[name] for name in comparison_names]
    table_rows = "".join(
        [
            metric_row(
                "Binary solves", [f"{value['solves']} / 36" for value in ordered]
            ),
            metric_row("Mean partial", [f"{value['mean']:.4f}" for value in ordered]),
            metric_row(
                "Median partial", [f"{value['median']:.4f}" for value in ordered]
            ),
            metric_row("Agent timeouts", [str(value["timeouts"]) for value in ordered]),
            metric_row(
                "Nonzero agent exits", [str(value["agent_exits"]) for value in ordered]
            ),
            metric_row(
                "Nonzero verifier exits",
                [str(value["verifier_exits"]) for value in ordered],
            ),
            metric_row(
                "Total tokens",
                [f"{value['tokens'] / 1_000_000:.1f}M" for value in ordered],
            ),
            metric_row(
                "Agent wall time",
                [f"{value['wall_s'] / 3600:.2f}h" for value in ordered],
            ),
        ]
    )
    headers = "".join(
        f"<th>{html.escape(LABELS[name])}</th>" for name in comparison_names
    )
    ornith_base = metrics["ornith_adjusted"]
    ornith_check = metrics["ornith_pi_check"]
    gemma_check = metrics["gemma_pi_check"]

    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ornith pi-check + timeout360 versus Gemma</title><style>
:root{{--bg:#08111f;--surface:#111d2e;--ink:#eef5ff;--blue:#62a8ff;--green:#45d19a;--red:#ff7188;--amber:#f4c66a;--muted:#9fb1c8;--line:#2a3c55}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:38px 22px 72px}}h1{{font-size:42px;line-height:1.08;margin:10px 0}}h2{{margin-top:38px}}p{{color:var(--muted)}}code{{color:#b9d8ff}}.hero{{padding:34px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(135deg,#12243b,#101b2b)}}.eyebrow{{color:var(--blue);font-weight:800;text-transform:uppercase;letter-spacing:.08em}}.pills{{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px}}.pill,.tag{{display:inline-block;padding:5px 10px;border-radius:999px;font-weight:750;font-size:13px}}.good{{background:#123d34;color:var(--green)}}.bad{{background:#461d29;color:var(--red)}}.caution{{background:#47391e;color:var(--amber)}}.neutral{{background:#1d3048;color:#c4d5e8}}.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}}.stat{{background:var(--surface);border:1px solid var(--line);padding:18px;border-radius:14px}}.stat strong{{display:block;font-size:27px}}.stat span{{color:var(--muted)}}table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:14px;overflow:hidden}}th,td{{padding:12px;border-bottom:1px solid var(--line);text-align:right}}th{{color:var(--muted)}}th:first-child,td:first-child{{text-align:left}}.callout{{border-left:4px solid var(--blue);background:var(--surface);padding:18px 20px;margin:22px 0;border-radius:0 12px 12px 0}}.warn{{border-left-color:var(--amber)}}small{{color:var(--muted)}}@media(max-width:800px){{.stats{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:31px}}table{{font-size:11px}}th,td{{padding:7px}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">Matched 12_v2 · 3 reps · 36 cells per column</div><h1>Ornith finishes more of every task. Gemma is the only model that fully solves any.</h1><p>The primary within-Ornith baseline substitutes the nine timeout360 reruns for the original timeout-prone cells. This separates pi-check from the timeout guard as far as the available evidence permits.</p><div class="pills"><span class="pill caution">Ornith pi-check: 0 solves</span><span class="pill good">Ornith mean partial 0.921</span><span class="pill neutral">Gemma pi-check: 2 solves</span><span class="pill good">Ornith: 0 timeouts</span></div></section>
<div class="stats"><div class="stat"><strong>{ornith_check["mean"] - ornith_base["mean"]:+.3f}</strong><span>pi-check partial gain on Ornith</span></div><div class="stat"><strong>{sum(value > 1e-12 for value in ornith_delta.values())}–{sum(value < -1e-12 for value in ornith_delta.values())}</strong><span>Ornith paired wins–losses</span></div><div class="stat"><strong>{statistics.fmean(cross_delta.values()):+.3f}</strong><span>Ornith vs Gemma pi-check partial</span></div><div class="stat"><strong>31–3</strong><span>Ornith vs Gemma higher cells</span></div></div>
<h2>Four-way aggregate</h2><table><thead><tr><th>Metric</th>{headers}</tr></thead><tbody>{table_rows}</tbody></table>
<h2>What pi-check changed on Ornith</h2><table><thead><tr><th>Metric</th><th>Timeout-adjusted baseline</th><th>Pi-check + timeout360</th><th>Change</th></tr></thead><tbody>
<tr><td>Binary solves</td><td>{ornith_base["solves"]}</td><td>{ornith_check["solves"]}</td><td><span class="tag caution">no change</span></td></tr>
<tr><td>Mean partial</td><td>{ornith_base["mean"]:.4f}</td><td>{ornith_check["mean"]:.4f}</td><td><span class="tag good">{ornith_check["mean"] - ornith_base["mean"]:+.4f}</span></td></tr>
<tr><td>Paired partial cells</td><td colspan="2">17 higher · 9 lower · 10 tied</td><td>median Δ {statistics.median(ornith_delta.values()):+.4f}</td></tr>
<tr><td>Tokens</td><td>{ornith_base["tokens"] / 1_000_000:.1f}M</td><td>{ornith_check["tokens"] / 1_000_000:.1f}M</td><td><span class="tag caution">{relative_delta(ornith_check["tokens"], ornith_base["tokens"])}</span></td></tr>
<tr><td>Agent wall</td><td>{ornith_base["wall_s"] / 3600:.2f}h</td><td>{ornith_check["wall_s"] / 3600:.2f}h</td><td><span class="tag caution">{relative_delta(ornith_check["wall_s"], ornith_base["wall_s"])}</span></td></tr>
</tbody></table>
<h2>Ornith pi-check versus Gemma pi-check</h2><table><thead><tr><th>Metric</th><th>Gemma + pi-check</th><th>Ornith + timeout360 + pi-check</th><th>Difference</th></tr></thead><tbody>
<tr><td>Binary solves</td><td>{gemma_check["solves"]}</td><td>{ornith_check["solves"]}</td><td><span class="tag bad">Ornith −2</span></td></tr>
<tr><td>Mean partial</td><td>{gemma_check["mean"]:.4f}</td><td>{ornith_check["mean"]:.4f}</td><td><span class="tag good">{ornith_check["mean"] - gemma_check["mean"]:+.4f}</span></td></tr>
<tr><td>Higher partial cells</td><td>3</td><td>31</td><td>2 ties</td></tr>
<tr><td>Agent timeouts</td><td>{gemma_check["timeouts"]}</td><td>{ornith_check["timeouts"]}</td><td><span class="tag good">Ornith −9</span></td></tr>
<tr><td>Tokens</td><td>{gemma_check["tokens"] / 1_000_000:.1f}M</td><td>{ornith_check["tokens"] / 1_000_000:.1f}M</td><td><span class="tag caution">Ornith {ornith_check["tokens"] / gemma_check["tokens"]:.2f}×</span></td></tr>
<tr><td>Agent wall</td><td>{gemma_check["wall_s"] / 3600:.2f}h</td><td>{ornith_check["wall_s"] / 3600:.2f}h</td><td><span class="tag good">{relative_delta(ornith_check["wall_s"], gemma_check["wall_s"])}</span></td></tr>
</tbody></table>
<div class="callout"><strong>Verdict.</strong> On Ornith, pi-check is a small partial-quality gain bought with large extra compute: +0.013 mean partial, no new solves, +42.3% tokens, and +50.5% wall time. Against Gemma pi-check, Ornith is much more consistent—higher partial reward in 31/36 cells and no timeouts—but Gemma’s two full solves remain the most decision-relevant advantage.</div>
<div class="callout warn"><strong>Caveat.</strong> The Ornith timeout-adjusted baseline is synthetic: 27 original baseline cells plus nine timeout360 reruns. The Gemma pi-check run did not have the mechanical timeout guard, so its nine timeouts combine model and operational behavior. The two Gemma solves were both <code>claude-code-by-agents-recursive-delegation</code> reps 0 and 1.</div>
<p><small>Sources: <code>{html.escape(str(RESULT_ROOTS["gemma_baseline"].relative_to(DATA_ROOT)))}</code>, <code>{html.escape(str(RESULT_ROOTS["gemma_pi_check"].relative_to(DATA_ROOT)))}</code>, <code>{html.escape(str(RESULT_ROOTS["ornith_raw"].relative_to(DATA_ROOT)))}</code>, <code>{html.escape(str(RESULT_ROOTS["ornith_guard"].relative_to(DATA_ROOT)))}</code>, and <code>{html.escape(str(RESULT_ROOTS["ornith_pi_check"].relative_to(DATA_ROOT)))}</code>.</small></p>
</main></body></html>"""


if __name__ == "__main__":
    OUTPUT_HTML.write_text(build_report())
    print(OUTPUT_HTML)

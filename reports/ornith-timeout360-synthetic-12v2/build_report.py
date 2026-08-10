#!/usr/bin/env python3
"""Build the synthetic Ornith timeout360-adjusted 12_v2 aggregate report."""

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
ORIGINAL_ROOT = DATA_ROOT / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0"
TIMEOUT360_ROOT = DATA_ROOT / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.1.0"
REPLACED_TASKS = {
    "langchain-request-coalescing",
    "mobly-grouped-test-barriers",
    "obsidian-linter-link-format-conversion",
}


def load_result_cells(root: Path) -> dict[tuple[str, int], dict[str, Any]]:
    """Load result cells keyed by matched task and rep identity."""
    cells: dict[tuple[str, int], dict[str, Any]] = {}
    for path in root.glob("*/rep*/result.json"):
        result = json.loads(path.read_text())
        cells[(result["task"], int(result["rep"]))] = result
    return cells


def is_nonzero_exit(value: object) -> bool:
    """Return whether an agent or verifier exit value represents failure."""
    return value not in (0, "0", None, False)


def aggregate_result_cells(
    cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate result metrics over an exact set of cells."""
    results = list(cells.values())
    partials = [float(result.get("reward_partial", 0)) for result in results]
    return {
        "cells": len(results),
        "binary_solves": sum(
            float(result.get("reward_binary", 0)) >= 1 for result in results
        ),
        "partial_mean": statistics.fmean(partials),
        "partial_median": statistics.median(partials),
        "partial_min": min(partials),
        "agent_timeouts": sum(
            bool(result.get("agent_timed_out")) for result in results
        ),
        "nonzero_agent_exits": sum(
            is_nonzero_exit(result.get("agent_exit")) for result in results
        ),
        "nonzero_verifier_exits": sum(
            is_nonzero_exit(result.get("verifier_exit")) for result in results
        ),
        "total_tokens": sum(
            int(result.get("total_tokens", 0) or 0) for result in results
        ),
        "wall_total_s": sum(
            float(result.get("agent_wall_s", 0) or 0) for result in results
        ),
        "wall_mean_s": statistics.fmean(
            float(result.get("agent_wall_s", 0) or 0) for result in results
        ),
        "turns": sum(int(result.get("turns", 0) or 0) for result in results),
        "tool_calls": sum(int(result.get("tool_calls", 0) or 0) for result in results),
        "patch_bytes": sum(
            int(result.get("patch_bytes", 0) or 0) for result in results
        ),
        "f2p_passed": sum(int(result.get("f2p_passed", 0) or 0) for result in results),
        "f2p_total": sum(int(result.get("f2p_total", 0) or 0) for result in results),
        "p2p_passed": sum(int(result.get("p2p_passed", 0) or 0) for result in results),
        "p2p_total": sum(int(result.get("p2p_total", 0) or 0) for result in results),
    }


def format_delta(current: float, previous: float, *, digits: int = 3) -> str:
    """Format a signed arithmetic delta."""
    return f"{current - previous:+.{digits}f}"


def format_relative_delta(current: float, previous: float) -> str:
    """Format a signed relative percentage delta."""
    if previous == 0:
        return "n/a"
    return f"{(current / previous - 1) * 100:+.1f}%"


def task_replacement_rows(
    original: dict[tuple[str, int], dict[str, Any]],
    timeout360: dict[tuple[str, int], dict[str, Any]],
) -> str:
    """Render task-level metrics for the nine substituted cells."""
    rows: list[str] = []
    for task in sorted(REPLACED_TASKS):
        old_cells = {key: value for key, value in original.items() if key[0] == task}
        new_cells = {key: value for key, value in timeout360.items() if key[0] == task}
        old = aggregate_result_cells(old_cells)
        new = aggregate_result_cells(new_cells)
        rows.append(
            "<tr>"
            f"<td><code>{html.escape(task)}</code></td>"
            f"<td>{old['partial_mean']:.3f}</td>"
            f"<td>{new['partial_mean']:.3f}</td>"
            f"<td><span class='tag good'>{format_delta(new['partial_mean'], old['partial_mean'])}</span></td>"
            f"<td>{old['agent_timeouts']} → {new['agent_timeouts']}</td>"
            f"<td>{old['total_tokens'] / 1_000_000:.1f}M → {new['total_tokens'] / 1_000_000:.1f}M</td>"
            f"<td>{old['wall_total_s'] / 3600:.2f}h → {new['wall_total_s'] / 3600:.2f}h</td>"
            "</tr>"
        )
    return "".join(rows)


def build_report() -> str:
    """Build and return the self-contained synthetic aggregate HTML report."""
    original = load_result_cells(ORIGINAL_ROOT)
    timeout360 = load_result_cells(TIMEOUT360_ROOT)
    expected_replacements = {(task, rep) for task in REPLACED_TASKS for rep in range(3)}
    assert len(original) == 36, f"expected 36 original cells, found {len(original)}"
    assert set(timeout360) == expected_replacements, (
        "timeout360 result set is not the expected nine cells"
    )

    synthetic = {key: timeout360.get(key, value) for key, value in original.items()}
    old_replaced = {key: original[key] for key in expected_replacements}
    original_metrics = aggregate_result_cells(original)
    replaced_old_metrics = aggregate_result_cells(old_replaced)
    replaced_new_metrics = aggregate_result_cells(timeout360)
    synthetic_metrics = aggregate_result_cells(synthetic)

    for key in expected_replacements:
        old = original[key]
        new = timeout360[key]
        assert old["harness_revision"] == new["harness_revision"]
        assert old["verifier_identity"] == new["verifier_identity"]
        assert old["immutable_image_identities"] == new["immutable_image_identities"]
        old_cell = ORIGINAL_ROOT / key[0] / f"rep{key[1]}"
        new_cell = TIMEOUT360_ROOT / key[0] / f"rep{key[1]}"
        assert (old_cell / "initial_context/user_prompt.txt").read_bytes() == (
            new_cell / "initial_context/user_prompt.txt"
        ).read_bytes()
        assert (old_cell / "initial_context/system_prompt.txt").read_bytes() == (
            new_cell / "initial_context/system_prompt.txt"
        ).read_bytes()

    mean_delta = synthetic_metrics["partial_mean"] - original_metrics["partial_mean"]
    timeout_delta = (
        synthetic_metrics["agent_timeouts"] - original_metrics["agent_timeouts"]
    )
    token_delta = synthetic_metrics["total_tokens"] - original_metrics["total_tokens"]
    wall_delta = synthetic_metrics["wall_total_s"] - original_metrics["wall_total_s"]
    max_partial = max(float(result["reward_partial"]) for result in synthetic.values())

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Ornith timeout360-adjusted 12_v2 aggregate</title>
<style>
:root{{--bg:#08111f;--surface:#111d2e;--surface2:#17263b;--ink:#eef5ff;--muted:#9fb1c8;--blue:#62a8ff;--green:#45d19a;--red:#ff7188;--amber:#f4c66a;--line:#2a3c55}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,-apple-system,sans-serif}} main{{max-width:1180px;margin:auto;padding:36px 22px 72px}} h1{{font-size:42px;line-height:1.08;margin:10px 0 14px}} h2{{margin-top:38px}} p{{color:var(--muted)}} code{{color:#b9d8ff}} .hero{{padding:34px;border:1px solid var(--line);border-radius:20px;background:linear-gradient(135deg,#12243b,#101b2b)}} .eyebrow{{color:var(--blue);font-weight:750;letter-spacing:.08em;text-transform:uppercase}} .pills{{display:flex;gap:9px;flex-wrap:wrap;margin-top:18px}} .pill,.tag{{display:inline-block;border-radius:999px;padding:5px 10px;font-weight:700;font-size:13px}} .good{{background:#123d34;color:var(--green)}} .bad{{background:#461d29;color:var(--red)}} .caution{{background:#47391e;color:var(--amber)}} .neutral{{background:#1d3048;color:#c4d5e8}} .stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:20px 0}} .stat{{background:var(--surface);border:1px solid var(--line);padding:18px;border-radius:14px}} .stat strong{{display:block;font-size:28px}} .stat span{{color:var(--muted)}} table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:14px;overflow:hidden}} th,td{{padding:12px 13px;border-bottom:1px solid var(--line);text-align:right}} th{{color:var(--muted);background:var(--surface2)}} th:first-child,td:first-child{{text-align:left}} .callout{{border-left:4px solid var(--blue);background:var(--surface);padding:17px 20px;margin:22px 0;border-radius:0 12px 12px 0}} .callout.caution-box{{border-left-color:var(--amber)}} .bar{{height:9px;background:#233650;border-radius:99px;overflow:hidden;margin-top:8px}} .bar i{{display:block;height:100%;background:var(--green)}} small{{color:var(--muted)}} @media(max-width:800px){{.stats{{grid-template-columns:repeat(2,1fr)}}h1{{font-size:32px}}table{{font-size:12px}}th,td{{padding:8px}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">Synthetic aggregate · Ornith 1.0 35B · high thinking</div>
<h1>Timeout guard lifts partial quality, not solves</h1>
<p>This view keeps the original 27 unaffected <code>12_v2</code> cells and substitutes all nine timeout360 reruns for LangChain, Mobly, and Obsidian. It is an analytical aggregate—not a persisted run or a new config result.</p>
<div class="pills"><span class="pill caution">0 / 36 binary solves</span><span class="pill good">mean partial {synthetic_metrics["partial_mean"]:.3f}</span><span class="pill good">0 agent timeouts</span><span class="pill neutral">36 matched task/rep cells</span></div></section>

<div class="stats">
<div class="stat"><strong>{synthetic_metrics["partial_mean"]:.3f}</strong><span>mean partial · {mean_delta:+.3f}</span><div class="bar"><i style="width:{synthetic_metrics["partial_mean"] * 100:.1f}%"></i></div></div>
<div class="stat"><strong>{synthetic_metrics["partial_median"]:.3f}</strong><span>median partial · {format_delta(synthetic_metrics["partial_median"], original_metrics["partial_median"])}</span></div>
<div class="stat"><strong>{synthetic_metrics["agent_timeouts"]}</strong><span>agent timeouts · {timeout_delta:+d}</span></div>
<div class="stat"><strong>{synthetic_metrics["total_tokens"] / 1_000_000:.1f}M</strong><span>tokens · {format_relative_delta(synthetic_metrics["total_tokens"], original_metrics["total_tokens"])}</span></div>
</div>

<h2>Original versus substituted aggregate</h2>
<table><thead><tr><th>Metric</th><th>Original baseline</th><th>Synthetic timeout360-adjusted</th><th>Change</th></tr></thead><tbody>
<tr><td>Binary solves</td><td>{original_metrics["binary_solves"]} / 36</td><td>{synthetic_metrics["binary_solves"]} / 36</td><td><span class="tag caution">no change</span></td></tr>
<tr><td>Mean partial</td><td>{original_metrics["partial_mean"]:.4f}</td><td>{synthetic_metrics["partial_mean"]:.4f}</td><td><span class="tag good">{mean_delta:+.4f}</span></td></tr>
<tr><td>Median partial</td><td>{original_metrics["partial_median"]:.4f}</td><td>{synthetic_metrics["partial_median"]:.4f}</td><td><span class="tag good">{format_delta(synthetic_metrics["partial_median"], original_metrics["partial_median"], digits=4)}</span></td></tr>
<tr><td>Minimum partial</td><td>{original_metrics["partial_min"]:.4f}</td><td>{synthetic_metrics["partial_min"]:.4f}</td><td><span class="tag good">{format_delta(synthetic_metrics["partial_min"], original_metrics["partial_min"], digits=4)}</span></td></tr>
<tr><td>Agent timeouts / nonzero exits</td><td>{original_metrics["agent_timeouts"]} / {original_metrics["nonzero_agent_exits"]}</td><td>{synthetic_metrics["agent_timeouts"]} / {synthetic_metrics["nonzero_agent_exits"]}</td><td><span class="tag good">−6 / −6</span></td></tr>
<tr><td>Nonzero verifier exits</td><td>{original_metrics["nonzero_verifier_exits"]}</td><td>{synthetic_metrics["nonzero_verifier_exits"]}</td><td><span class="tag good">−4</span></td></tr>
<tr><td>Total tokens</td><td>{original_metrics["total_tokens"]:,}</td><td>{synthetic_metrics["total_tokens"]:,}</td><td><span class="tag caution">{token_delta:+,} · {format_relative_delta(synthetic_metrics["total_tokens"], original_metrics["total_tokens"])}</span></td></tr>
<tr><td>Total agent wall time</td><td>{original_metrics["wall_total_s"] / 3600:.2f} h</td><td>{synthetic_metrics["wall_total_s"] / 3600:.2f} h</td><td><span class="tag good">{wall_delta / 3600:+.2f} h · {format_relative_delta(synthetic_metrics["wall_total_s"], original_metrics["wall_total_s"])}</span></td></tr>
<tr><td>Mean agent wall / cell</td><td>{original_metrics["wall_mean_s"] / 60:.1f} min</td><td>{synthetic_metrics["wall_mean_s"] / 60:.1f} min</td><td>{format_relative_delta(synthetic_metrics["wall_mean_s"], original_metrics["wall_mean_s"])}</td></tr>
<tr><td>Turns / tool calls</td><td>{original_metrics["turns"]:,} / {original_metrics["tool_calls"]:,}</td><td>{synthetic_metrics["turns"]:,} / {synthetic_metrics["tool_calls"]:,}</td><td>{synthetic_metrics["turns"] - original_metrics["turns"]:+,} / {synthetic_metrics["tool_calls"] - original_metrics["tool_calls"]:+,}</td></tr>
<tr><td>F2P checks</td><td>{original_metrics["f2p_passed"]:,} / {original_metrics["f2p_total"]:,}</td><td>{synthetic_metrics["f2p_passed"]:,} / {synthetic_metrics["f2p_total"]:,}</td><td>denominators differ</td></tr>
<tr><td>P2P checks</td><td>{original_metrics["p2p_passed"]:,} / {original_metrics["p2p_total"]:,}</td><td>{synthetic_metrics["p2p_passed"]:,} / {synthetic_metrics["p2p_total"]:,}</td><td>denominators differ</td></tr>
</tbody></table>

<h2>The nine substituted cells</h2>
<div class="stats">
<div class="stat"><strong>{replaced_old_metrics["partial_mean"]:.3f} → {replaced_new_metrics["partial_mean"]:.3f}</strong><span>mean partial</span></div>
<div class="stat"><strong>{replaced_old_metrics["agent_timeouts"]} → {replaced_new_metrics["agent_timeouts"]}</strong><span>agent timeouts</span></div>
<div class="stat"><strong>{replaced_old_metrics["total_tokens"] / 1_000_000:.1f}M → {replaced_new_metrics["total_tokens"] / 1_000_000:.1f}M</strong><span>tokens</span></div>
<div class="stat"><strong>{replaced_old_metrics["wall_total_s"] / 3600:.2f}h → {replaced_new_metrics["wall_total_s"] / 3600:.2f}h</strong><span>agent wall time</span></div>
</div>
<table><thead><tr><th>Task</th><th>Old partial</th><th>New partial</th><th>Δ</th><th>Timeouts</th><th>Tokens</th><th>Wall</th></tr></thead><tbody>{task_replacement_rows(original, timeout360)}</tbody></table>

<div class="callout"><strong>Bottom line.</strong> Treating the mechanical timeout guard as operational hygiene raises the 36-cell mean partial from {original_metrics["partial_mean"]:.3f} to {synthetic_metrics["partial_mean"]:.3f}, eliminates all six agent timeouts and four nonzero verifier exits, and cuts aggregate agent wall time by {abs(wall_delta) / 3600:.2f} hours. It still produces zero binary solves. The guard rescued incomplete work; it did not make Ornith finish the benchmark’s full contracts.</div>
<div class="callout caution-box"><strong>Interpretation limit.</strong> This is a synthetic substitution, not a canonical run. The nine reruns used <code>baseline-ornith-35b@1.1.0</code> and the other 27 used <code>@1.0.0</code>. Prompts, harness revision, verifier identities, and immutable images match for every substituted pair; only the mechanical Bash timeout surface differs. F2P/P2P denominators changed because more tests completed, so partial reward is the safer aggregate.</div>
<p><small>Sources: <code>{html.escape(str(ORIGINAL_ROOT.relative_to(DATA_ROOT)))}</code> (36 original cells) and <code>{html.escape(str(TIMEOUT360_ROOT.relative_to(DATA_ROOT)))}</code> (9 replacement cells). Maximum synthetic partial: {max_partial:.4f}. Generated reproducibly by <code>build_report.py</code>.</small></p>
</main></body></html>"""


if __name__ == "__main__":
    OUTPUT_HTML.write_text(build_report())
    print(OUTPUT_HTML)

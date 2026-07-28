#!/usr/bin/env python3
"""Render the Stage 1 Pi Fabric trajectory-forensics report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def esc(value: object) -> str:
    return html.escape(str(value))


def percent_change(left: float, right: float) -> str:
    if left == 0:
        return "n/a"
    return f"{((right / left) - 1) * 100:+.1f}%"


def number(value: float) -> str:
    return f"{value:,.0f}"


def metric_row(
    label: str, left: float, right: float, interpretation: str, tone: str
) -> str:
    return (
        f"<tr><td>{esc(label)}</td><td class='num'>{number(left)}</td>"
        f"<td class='num'>{number(right)}</td>"
        f"<td class='num {tone}'>{percent_change(left, right)}</td>"
        f"<td>{esc(interpretation)}</td></tr>"
    )


def task_rows(rows: list[dict[str, Any]], tone: str) -> str:
    return "".join(
        "<tr>"
        f"<td><code>{esc(row['task'])}</code></td>"
        f"<td class='num {tone}'>{row['token_delta']:+,.0f}</td>"
        f"<td class='num'>{row['call_delta']:+.1f}</td>"
        f"<td class='num'>{row['mutation_call_delta']:+.1f}</td>"
        f"<td class='num'>{row['repeated_mutation_path_delta']:+.1f}</td>"
        "</tr>"
        for row in rows
    )


def render(summary: dict[str, Any]) -> str:
    historical = summary["historical"]
    guided = summary["guided"]
    left = historical["totals"]
    right = guided["totals"]
    correlations = summary["task_delta_correlations"]
    post_cache_delta = (
        right["cache_read_after_first_mutation"]
        - left["cache_read_after_first_mutation"]
    )
    pre_cache_delta = (
        right["cache_read_before_first_mutation"]
        - left["cache_read_before_first_mutation"]
    )
    mutation_cache_delta = (
        right["mutation_call_cache_read"] - left["mutation_call_cache_read"]
    )
    regression_rows = task_rows(summary["largest_token_regressions"][:6], "bad")
    improvement_rows = task_rows(summary["largest_token_improvements"][:6], "good")
    comparison_rows = "".join(
        [
            metric_row(
                "Calls before first explicit mutation",
                left["calls_before_first_mutation"],
                right["calls_before_first_mutation"],
                "Not the source of the aggregate increase.",
                "good",
            ),
            metric_row(
                "Cache before first explicit mutation",
                left["cache_read_before_first_mutation"],
                right["cache_read_before_first_mutation"],
                "Guided Fabric reached editing with less aggregate cache use.",
                "good",
            ),
            metric_row(
                "Calls after first explicit mutation",
                left["calls_after_first_mutation"],
                right["calls_after_first_mutation"],
                "All net call growth is after implementation starts.",
                "bad",
            ),
            metric_row(
                "Cache after first explicit mutation",
                left["cache_read_after_first_mutation"],
                right["cache_read_after_first_mutation"],
                "The post-edit loop adds 17.30M cache-read tokens gross.",
                "bad",
            ),
            metric_row(
                "Mutation calls",
                left["mutation_calls"],
                right["mutation_calls"],
                "More separate edit/write rounds.",
                "bad",
            ),
            metric_row(
                "Repeated mutations of an already-mutated path",
                left["repeated_mutation_path_operations"],
                right["repeated_mutation_path_operations"],
                "The same files are revisited more often.",
                "bad",
            ),
            metric_row(
                "Consecutive mutation→mutation transitions",
                left["consecutive_mutation_transitions"],
                right["consecutive_mutation_transitions"],
                "A direct signal of fragmented implementation rounds.",
                "bad",
            ),
            metric_row(
                "Final patch bytes",
                left["final_patch_bytes"],
                right["final_patch_bytes"],
                "Final changes grow much less than mutation activity.",
                "caution",
            ),
            metric_row(
                "Final patch files",
                left["final_patch_files"],
                right["final_patch_files"],
                "The final file surface is essentially unchanged.",
                "neutral",
            ),
        ]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi Fabric Stage 1 trajectory forensics</title>
<style>
:root{{--bg:#090d14;--surface:#121a27;--surface2:#182235;--ink:#edf5ff;--muted:#9aabc1;--line:#2a3850;--blue:#72b7ff;--green:#5fe0a5;--red:#ff7d89;--amber:#f4c96c}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 88% 0,#173053,var(--bg) 42%);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:28px 18px 72px}}h1{{font-size:clamp(2.25rem,7vw,5rem);line-height:.98;margin:.15em 0}}h2{{margin-top:42px}}h3{{margin-top:0}}.hero p{{font-size:1.2rem;max-width:900px;color:var(--muted)}}.pills{{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}}.pill,.tag{{border:1px solid var(--line);border-radius:999px;padding:6px 11px;font-weight:700}}.pill.good{{color:var(--green)}}.pill.bad{{color:var(--red)}}.pill.caution{{color:var(--amber)}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:13px}}.stat,.card,.callout{{background:linear-gradient(145deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:17px;padding:18px}}.stat strong{{display:block;font-size:1.75rem}}.stat span,.muted{{color:var(--muted)}}.callout{{border-left:5px solid var(--blue);margin:22px 0}}.callout.badline{{border-left-color:var(--red)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}table{{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line)}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:.77rem;color:var(--muted);text-transform:uppercase}}td.num,th.num{{text-align:right}}tr:last-child td{{border:0}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}code{{color:#bbdcff}}a{{color:var(--blue)}}li{{margin:.55em 0}}.small{{font-size:.86rem;color:var(--muted)}}@media(max-width:760px){{table{{font-size:.78rem}}th,td{{padding:7px 4px}}}}
</style></head><body><main>
<section class="hero"><div class="muted">Stage 1 · existing trajectories only · 108 matched reps per config</div><h1>The extra tokens arrive after editing starts.</h1><p>Native read guidance changed retrieval behavior, but the full trajectory evidence does not support “search and bounded reads made Fabric spend more before coding.” Guided Fabric reaches the first explicit edit with less aggregate cache use. It then enters a substantially longer implementation and verification loop.</p></section>
<div class="pills"><span class="pill good">No model calls</span><span class="pill good">No benchmark rerun</span><span class="pill bad">Post-edit calls +33%</span><span class="pill bad">Repeated mutations +64%</span><span class="pill caution">Version-confounded</span></div>
<section class="stats"><div class="stat"><strong class="good">{pre_cache_delta / 1_000_000:+.2f}M</strong><span>cache delta before first mutation</span></div><div class="stat"><strong class="bad">{post_cache_delta / 1_000_000:+.2f}M</strong><span>cache delta after first mutation</span></div><div class="stat"><strong class="bad">+{right["mutation_calls"] - left["mutation_calls"]:,}</strong><span>additional mutation calls</span></div><div class="stat"><strong class="bad">{mutation_cache_delta / 1_000_000:+.2f}M</strong><span>cache delta on mutation-producing turns</span></div></section>
<section class="callout badline"><strong>Best current explanation:</strong> the guided configuration executes a less consolidated post-edit loop. It uses more separate mutation rounds, revisits already-mutated paths more often, and crosses mutation↔verification boundaries more often. That creates many additional model turns, and each turn rereads the accumulated transcript.</section>
<h2>Where the trajectory diverges</h2><table><thead><tr><th>Measure</th><th class="num">Historical Fabric</th><th class="num">Guided Fabric</th><th class="num">Change</th><th>Meaning</th></tr></thead><tbody>{comparison_rows}</tbody></table>
<h2>Program composition moved away from “one program, many capabilities”</h2><div class="grid"><div class="card"><h3>Less parallel composition</h3><p><code>Promise.all</code> appears in <strong>{historical["rates"]["promise_all_call_share"] * 100:.1f}%</strong> of historical calls and <strong>{guided["rates"]["promise_all_call_share"] * 100:.1f}%</strong> of guided calls.</p></div><div class="card"><h3>More single-operation calls</h3><p>The single-operation share rises from <strong>{historical["rates"]["single_operation_call_share"] * 100:.1f}%</strong> to <strong>{guided["rates"]["single_operation_call_share"] * 100:.1f}%</strong>.</p></div><div class="card"><h3>More edit-loop crossings</h3><p>Mutation→mutation transitions rise <strong>{percent_change(left["consecutive_mutation_transitions"], right["consecutive_mutation_transitions"])}</strong>; verification→mutation rises <strong>{percent_change(left["verification_to_mutation_transitions"], right["verification_to_mutation_transitions"])}</strong>.</p></div></div>
<p class="callout"><strong>Important correction to the earlier hypothesis:</strong> search-only→read transitions have essentially no task-level relationship with token regression (<code>r={correlations["search_to_read_delta"]:.3f}</code>). Retrieval calls before mutation are negatively associated with token delta (<code>r={correlations["retrieval_before_mutation_delta"]:.3f}</code>). The stronger associations are total call growth (<code>r={correlations["call_delta"]:.3f}</code>), calls after mutation (<code>r={correlations["calls_after_first_mutation_delta"]:.3f}</code>), repeated mutation paths (<code>r={correlations["repeated_mutation_path_delta"]:.3f}</code>), and mutation operations (<code>r={correlations["mutation_operation_delta"]:.3f}</code>).</p>
<h2>Largest task movements</h2><div class="grid"><div><h3>Token regressions</h3><table><thead><tr><th>Task</th><th class="num">Tokens</th><th class="num">Calls</th><th class="num">Mutation calls</th><th class="num">Repeated mutation</th></tr></thead><tbody>{regression_rows}</tbody></table></div><div><h3>Token improvements</h3><table><thead><tr><th>Task</th><th class="num">Tokens</th><th class="num">Calls</th><th class="num">Mutation calls</th><th class="num">Repeated mutation</th></tr></thead><tbody>{improvement_rows}</tbody></table></div></div>
<h2>Concrete outlier</h2><section class="card"><h3>Koota query predicates · rep1</h3><p>Historical Fabric used <strong>32 calls</strong>, <strong>2 mutation calls</strong>, and <strong>1.32M tokens</strong>. Guided Fabric used <strong>77 calls</strong>, <strong>37 mutation calls</strong>, and <strong>4.07M tokens</strong>. This is not a longer initial search; it is an extended mutation-heavy implementation loop.</p></section>
<h2>What this says about the author’s expectation</h2><div class="grid"><div class="card"><h3>What worked</h3><ul><li>Median nested operations are {guided["call_operation_distribution"]["median"]:.0f} and p90 is {guided["call_operation_distribution"]["p90"]}, matching the author’s telemetry.</li><li>Whole-file reads and oversized returned results fall sharply.</li><li>Program failure rate falls from {historical["rates"]["failed_call_share"] * 100:.1f}% to {guided["rates"]["failed_call_share"] * 100:.1f}%, close to the author’s reported trace failure rate.</li></ul></div><div class="card"><h3>What did not materialize</h3><ul><li>The intended read→branch→edit→verify→compact-proof flow did not consolidate into fewer outer turns.</li><li>Implementation and verification became more fragmented after the first edit.</li><li>The runtime makes compact evidence possible, but does not guarantee fewer model boundaries.</li></ul></div></div>
<h2>What Stage 1 cannot prove</h2><ul><li>The comparison is historical Fabric 0.25.6 versus Fabric 0.28.4 plus guidance. It localizes the observed mechanism but cannot assign causality between the version change and the guidance.</li><li>Existing traces omit hidden nested-result sizes, so they cannot measure raw-to-returned compression.</li><li>Edit payload text is stripped from traces. Mutation rounds and paths are measurable; exact intermediate edit size is not.</li><li><code>pi.edit</code>/<code>pi.write</code> mark explicit mutation. Bash-based mutation remains a known blind spot.</li></ul>
<section class="callout"><strong>Stage 1 conclusion:</strong> the evidence now points to post-edit fragmentation—not initial bounded retrieval—as the direct source of the added tokens. Determining whether our guidance caused that fragmentation, or whether Pi Fabric 0.28.4 changed the model’s implementation style, requires the same-version work that Will has not approved. No Stage 2 or Stage 3 work was performed.</section>
<p class="small">Primary design source: <a href="https://monotykamary.com/posts/i-gave-pi-one-tool/">I gave Pi one tool</a>. Derived data: <code>summary.json</code> and <code>trajectory-metrics.json</code>.</p>
</main></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    summary = json.loads(args.summary.read_text())
    args.output.write_text(render(summary))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Render the three-way Pi Fabric Stage 1 trajectory report."""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any


def esc(value: object) -> str:
    return html.escape(str(value))


def change(left: float, right: float) -> float:
    return ((right / left) - 1) * 100 if left else 0.0


def pct(left: float, right: float) -> str:
    return f"{change(left, right):+.1f}%"


def num(value: float) -> str:
    return f"{value:,.0f}"


def money(value: float) -> str:
    return f"${value:,.2f}"


def metric_row(
    label: str,
    baseline: float,
    historical: float,
    guided: float,
    interpretation: str,
) -> str:
    return (
        f"<tr><td>{esc(label)}</td>"
        f"<td class='num'>{num(baseline)}</td>"
        f"<td class='num'>{num(historical)}</td>"
        f"<td class='num'>{num(guided)}</td>"
        f"<td>{esc(interpretation)}</td></tr>"
    )


def task_rows(rows: list[dict[str, Any]], tone: str) -> str:
    return "".join(
        "<tr>"
        f"<td><code>{esc(row['task'])}</code></td>"
        f"<td class='num {tone}'>{row['token_delta']:+,.0f}</td>"
        f"<td class='num'>{row['call_delta']:+.1f}</td>"
        f"<td class='num'>{row['calls_after_first_mutation_delta']:+.1f}</td>"
        f"<td class='num'>{row['mutation_call_delta']:+.1f}</td>"
        "</tr>"
        for row in rows
    )


def render(summary: dict[str, Any]) -> str:
    baseline = summary["baseline"]
    historical = summary["historical"]
    guided = summary["guided"]
    b = baseline["totals"]
    h = historical["totals"]
    g = guided["totals"]
    bo = baseline["outcomes"]
    ho = historical["outcomes"]
    go = guided["outcomes"]
    first_comparison = summary["comparisons"]["baseline_to_historical"]
    second_comparison = summary["comparisons"]["historical_to_guided"]
    original_regressions = task_rows(
        first_comparison["largest_token_regressions"][:5], "bad"
    )
    original_improvements = task_rows(
        first_comparison["largest_token_improvements"][:5], "good"
    )
    guided_regressions = task_rows(
        second_comparison["largest_token_regressions"][:5], "bad"
    )
    table_rows = "".join(
        [
            metric_row(
                "Outer model/tool turns",
                b["outer_calls"],
                h["outer_calls"],
                g["outer_calls"],
                "Original Fabric reduced boundaries; guidance added them back.",
            ),
            metric_row(
                "Nested/native operations",
                b["nested_operations"],
                h["nested_operations"],
                g["nested_operations"],
                "Fabric composed more work inside each boundary.",
            ),
            metric_row(
                "Visible tool-result characters",
                b["returned_result_chars"],
                h["returned_result_chars"],
                g["returned_result_chars"],
                "Original Fabric returned far more evidence to the transcript.",
            ),
            metric_row(
                "Assistant cache-read tokens",
                b["assistant_cache_read"],
                h["assistant_cache_read"],
                g["assistant_cache_read"],
                "Every later turn rereads the accumulated evidence.",
            ),
            metric_row(
                "Calls before first explicit mutation",
                b["calls_before_first_mutation"],
                h["calls_before_first_mutation"],
                g["calls_before_first_mutation"],
                "Original Fabric spent more outer turns investigating before editing.",
            ),
            metric_row(
                "Cache before first explicit mutation",
                b["cache_read_before_first_mutation"],
                h["cache_read_before_first_mutation"],
                g["cache_read_before_first_mutation"],
                "Original Fabric entered implementation with a much larger context bill.",
            ),
            metric_row(
                "Calls after first explicit mutation",
                b["calls_after_first_mutation"],
                h["calls_after_first_mutation"],
                g["calls_after_first_mutation"],
                "Original Fabric consolidated implementation; guidance fragmented it.",
            ),
            metric_row(
                "Cache after first explicit mutation",
                b["cache_read_after_first_mutation"],
                h["cache_read_after_first_mutation"],
                g["cache_read_after_first_mutation"],
                "Fewer original-Fabric turns were still much more expensive each.",
            ),
            metric_row(
                "Mutation calls",
                b["mutation_calls"],
                h["mutation_calls"],
                g["mutation_calls"],
                "Original Fabric packed edits together; guidance split them apart.",
            ),
            metric_row(
                "Mutation operations",
                b["mutation_operations"],
                h["mutation_operations"],
                g["mutation_operations"],
                "Original Fabric performed similar edit volume in fewer calls.",
            ),
            metric_row(
                "Whole-file reads",
                b["whole_file_read_operations"],
                h["whole_file_read_operations"],
                g["whole_file_read_operations"],
                "The guidance fixed the specific whole-file-read behavior.",
            ),
        ]
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Pi Fabric Stage 1 trajectory forensics</title>
<style>
:root{{--bg:#090d14;--surface:#121a27;--surface2:#182235;--ink:#edf5ff;--muted:#9aabc1;--line:#2a3850;--blue:#72b7ff;--green:#5fe0a5;--red:#ff7d89;--amber:#f4c96c}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at 88% 0,#173053,var(--bg) 42%);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:28px 18px 72px}}h1{{font-size:clamp(2.25rem,7vw,5rem);line-height:.98;margin:.15em 0}}h2{{margin-top:42px}}h3{{margin-top:0}}.hero p{{font-size:1.2rem;max-width:930px;color:var(--muted)}}.pills{{display:flex;gap:9px;flex-wrap:wrap;margin:22px 0}}.pill,.tag{{border:1px solid var(--line);border-radius:999px;padding:6px 11px;font-weight:700}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:13px}}.stat,.card,.callout{{background:linear-gradient(145deg,var(--surface2),var(--surface));border:1px solid var(--line);border-radius:17px;padding:18px}}.stat strong{{display:block;font-size:1.75rem}}.stat span,.muted{{color:var(--muted)}}.callout{{border-left:5px solid var(--blue);margin:22px 0}}.callout.badline{{border-left-color:var(--red)}}.callout.goodline{{border-left-color:var(--green)}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}}table{{width:100%;border-collapse:collapse;background:var(--surface);border:1px solid var(--line)}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:.77rem;color:var(--muted);text-transform:uppercase}}td.num,th.num{{text-align:right}}tr:last-child td{{border:0}}code{{color:#bbdcff}}a{{color:var(--blue)}}li{{margin:.55em 0}}.small{{font-size:.86rem;color:var(--muted)}}@media(max-width:760px){{table{{font-size:.77rem}}th,td{{padding:7px 4px}}}}
</style></head><body><main>
<section class="hero"><div class="muted">Stage 1 · 324 existing trajectories · no new benchmark run</div><h1>The first Fabric run composed work—but returned too much of it.</h1><p>The original vanilla-Pi comparison resolves the missing question. Pi Fabric 0.25.6 did exploit its one-program interface: it used fewer outer turns and consolidated edits. Its token regression came from broad evidence returning to the conversation, especially before the first edit, making every later turn expensive.</p></section>
<div class="pills"><span class="pill good">Original comparison restored</span><span class="pill good">No model calls</span><span class="pill bad">Original visible result text +{change(b["returned_result_chars"], h["returned_result_chars"]):.0f}%</span><span class="pill bad">Original cache reads +{change(b["assistant_cache_read"], h["assistant_cache_read"]):.0f}%</span><span class="pill caution">Guidance comparison version-confounded</span></div>
<section class="stats"><div class="stat"><strong class="good">{pct(b["outer_calls"], h["outer_calls"])}</strong><span>original Fabric outer turns</span></div><div class="stat"><strong class="good">{pct(b["calls_after_first_mutation"], h["calls_after_first_mutation"])}</strong><span>original post-edit turns</span></div><div class="stat"><strong class="bad">{pct(b["cache_read_before_first_mutation"], h["cache_read_before_first_mutation"])}</strong><span>original pre-edit cache</span></div><div class="stat"><strong class="bad">{pct(b["returned_result_chars"], h["returned_result_chars"])}</strong><span>original visible result text</span></div></section>
<section class="callout goodline"><strong>What worked in the first run:</strong> Fabric reduced outer turns from {b["outer_calls"]:,} to {h["outer_calls"]:,}, reduced post-edit turns by {abs(change(b["calls_after_first_mutation"], h["calls_after_first_mutation"])):.1f}%, and concentrated {h["mutation_operations"]:,} mutation operations into {h["mutation_calls"]:,} mutation calls. Vanilla Pi used {b["mutation_calls"]:,} calls for {b["mutation_operations"]:,} mutation operations. The programmable-tool composition idea was functioning.</section>
<section class="callout badline"><strong>What failed in the first run:</strong> Fabric returned {pct(b["returned_result_chars"], h["returned_result_chars"])} more tool-result text and consumed {pct(b["assistant_cache_read"], h["assistant_cache_read"])} more cache-read tokens. Before the first explicit edit, cache use rose from {b["cache_read_before_first_mutation"] / 1_000_000:.2f}M to {h["cache_read_before_first_mutation"] / 1_000_000:.2f}M. “Only the final result returns” does not save context when the chosen final result is itself a broad source bundle.</section>
<h2>Three-way trajectory comparison</h2><table><thead><tr><th>Measure</th><th class="num">Vanilla Pi</th><th class="num">Fabric 0.25.6</th><th class="num">Guided 0.28.4</th><th>Interpretation</th></tr></thead><tbody>{table_rows}</tbody></table>
<h2>End-to-end outcomes</h2><div class="grid"><div class="card"><h3>Vanilla Pi</h3><p><strong>{bo["solves"]} solves</strong> · mean partial {bo["mean_partial_reward"]:.4f}</p><p>{num(bo["total_tokens"])} tokens · {money(bo["total_cost_usd"])}</p></div><div class="card"><h3>Fabric 0.25.6</h3><p><strong>{ho["solves"]} solves</strong> · mean partial {ho["mean_partial_reward"]:.4f}</p><p>{num(ho["total_tokens"])} tokens · {money(ho["total_cost_usd"])}</p><p class="bad">{pct(bo["total_tokens"], ho["total_tokens"])} tokens vs vanilla</p></div><div class="card"><h3>Guided Fabric 0.28.4</h3><p><strong>{go["solves"]} solves</strong> · mean partial {go["mean_partial_reward"]:.4f}</p><p>{num(go["total_tokens"])} tokens · {money(go["total_cost_usd"])}</p><p class="bad">{pct(ho["total_tokens"], go["total_tokens"])} tokens vs original Fabric</p></div></div>
<h2>What the guidance changed</h2><p>The guidance successfully corrected the targeted retrieval behavior: whole-file reads fell from {h["whole_file_read_operations"]:,}/{h["read_operations"]:,} ({h["whole_file_read_operations"] / h["read_operations"] * 100:.1f}%) to {g["whole_file_read_operations"]:,}/{g["read_operations"]:,} ({g["whole_file_read_operations"] / g["read_operations"] * 100:.1f}%), and visible result text fell {abs(change(h["returned_result_chars"], g["returned_result_chars"])):.1f}%.</p><p>But it changed the shape of the agent loop. Outer turns rose {pct(h["outer_calls"], g["outer_calls"])}; post-edit turns rose {pct(h["calls_after_first_mutation"], g["calls_after_first_mutation"])}; mutation calls rose {pct(h["mutation_calls"], g["mutation_calls"])}; and repeated mutations of an already-mutated path rose {pct(h["repeated_mutation_path_operations"], g["repeated_mutation_path_operations"])}. The retrieval fix was real, but the later implementation loop became more fragmented.</p>
<div class="grid"><div class="card"><h3>Original Fabric composition</h3><ul><li>{historical["rates"]["multi_operation_call_share"] * 100:.1f}% multi-operation calls</li><li>{historical["rates"]["promise_all_call_share"] * 100:.1f}% <code>Promise.all</code> calls</li><li>{h["mutation_operations"] / h["mutation_calls"]:.2f} mutations per mutation call</li></ul></div><div class="card"><h3>Guided Fabric composition</h3><ul><li>{guided["rates"]["multi_operation_call_share"] * 100:.1f}% multi-operation calls</li><li>{guided["rates"]["promise_all_call_share"] * 100:.1f}% <code>Promise.all</code> calls</li><li>{g["mutation_operations"] / g["mutation_calls"]:.2f} mutations per mutation call</li></ul></div></div>
<h2>Where the original run lost tokens</h2><div class="grid"><div><h3>Largest original regressions vs vanilla</h3><table><thead><tr><th>Task</th><th class="num">Tokens</th><th class="num">Calls</th><th class="num">Post-edit</th><th class="num">Mutation</th></tr></thead><tbody>{original_regressions}</tbody></table></div><div><h3>Largest original improvements vs vanilla</h3><table><thead><tr><th>Task</th><th class="num">Tokens</th><th class="num">Calls</th><th class="num">Post-edit</th><th class="num">Mutation</th></tr></thead><tbody>{original_improvements}</tbody></table></div></div>
<h2>Where guidance later regressed</h2><table><thead><tr><th>Task</th><th class="num">Tokens</th><th class="num">Calls</th><th class="num">Post-edit</th><th class="num">Mutation</th></tr></thead><tbody>{guided_regressions}</tbody></table>
<h2>Answer relative to Tom’s expectations</h2><div class="grid"><div class="card"><h3>Confirmed</h3><ul><li>Fabric composed more operations behind fewer model boundaries.</li><li>Edits were consolidated into fewer mutation-producing turns.</li><li>Its median program remained small while still allowing branching and batching.</li></ul></div><div class="card"><h3>Violated</h3><ul><li>Intermediate exploration was often returned as broad evidence rather than reduced inside the sandbox.</li><li>Pre-edit investigation inflated the transcript before implementation began.</li><li>Cache rereads then charged for that evidence on every later turn.</li></ul></div></div>
<section class="callout"><strong>Corrected Stage 1 conclusion:</strong> the original Fabric run was not failing because the one-tool architecture prevented composition. It was composing successfully. It failed the context-efficiency goal because the agent used the programmable boundary to gather broad source bundles and returned too much of them. The later guidance fixed whole-file reading but made implementation convergence worse. Only the narrow attribution of that later regression—guidance versus the 0.28.4 upgrade—remains unresolved.</section>
<h2>Limits</h2><ul><li>Pre/post-mutation phase totals include only trajectories that reached an explicit mutation: {b["trajectories_with_explicit_mutation"]:.0f}/108 vanilla, {h["trajectories_with_explicit_mutation"]:.0f}/108 original Fabric, and {g["trajectories_with_explicit_mutation"]:.0f}/108 guided Fabric.</li><li>Vanilla Pi’s parallel native tool calls are grouped by assistant message into one outer turn, matching one <code>fabric_exec</code> conversational boundary.</li><li>Fabric traces expose nested operations and returned text, but not the byte size of hidden intermediate results.</li><li>Explicit mutation uses <code>edit</code>/<code>write</code>; mutation hidden inside Bash remains a blind spot in all three configs.</li><li>The original vanilla→Fabric comparison is matched and not version-confounded. The later Fabric 0.25.6→guided 0.28.4 comparison is version-confounded.</li></ul>
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

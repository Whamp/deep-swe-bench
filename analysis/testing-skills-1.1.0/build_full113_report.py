#!/usr/bin/env python3
"""Render the full-113 testing-skills comparison as a Tailnet HTML report."""

from __future__ import annotations

import html
import json
from collections import Counter
from typing import Any

from full113_analysis import REPOSITORY_ROOT, write_full113_analysis

REPORT_ROOT = REPOSITORY_ROOT / "reports/testing-skills-1.1-vs-baseline-full113"
REPORT_PATH = REPORT_ROOT / "index.html"
PACKET_ROOT = REPORT_ROOT / "packets"


def escape(value: Any) -> str:
    """Escape one value for safe HTML text or attribute output."""
    return html.escape(str(value), quote=True)


def outcome_pill(left: bool, right: bool) -> str:
    """Render one valid paired binary outcome."""
    if not left and right:
        return '<span class="pill good">gain</span>'
    if left and not right:
        return '<span class="pill bad">loss</span>'
    if left:
        return '<span class="pill neutral">both</span>'
    return '<span class="pill neutral">neither</span>'


def render_planned_pair_rows(analysis: dict[str, Any]) -> str:
    """Render all 339 planned task and rep pairs, including exclusions."""
    clean = {(row["task"], row["rep"]): row for row in analysis["ledger"]}
    excluded = {(row["task"], row["rep"]): row for row in analysis["excluded_pairs"]}
    packet_paths = {
        (packet["task"], packet["rep"]): packet["packet"]
        for packet in analysis["packets"]
    }
    task_metadata = {row["task"]: row for row in analysis["task_summaries"]}
    rows = []
    for task in sorted(task_metadata):
        meta = task_metadata[task]
        for rep in range(3):
            key = (task, rep)
            if key in clean:
                row = clean[key]
                outcome = outcome_pill(row["left_solved"], row["right_solved"])
                if key in packet_paths:
                    outcome = f'<a href="{escape(packet_paths[key])}">{outcome}</a>'
                reads = (
                    ", ".join(
                        name
                        for name, present in row["right_skill_reads"].items()
                        if present
                    )
                    or "—"
                )
                cells = (
                    f"<td>{int(row['left_solved'])}</td>"
                    f"<td>{int(row['right_solved'])}</td><td>{outcome}</td>"
                    f"<td>{escape(reads)}</td>"
                    f"<td>{row['right_result']['reward_partial']:.6f}</td>"
                )
            else:
                row = excluded[key]
                reason = (
                    "invalid verifier"
                    if "harness-failure"
                    in (row["left_disposition"], row["right_disposition"])
                    else "OOM excluded"
                )
                cells = (
                    f"<td>{escape(row['left_reward_binary'])}</td>"
                    f"<td>{escape(row['right_reward_binary'])}</td>"
                    f'<td><span class="pill caution">{escape(reason)}</span></td>'
                    "<td>—</td><td>—</td>"
                )
            rows.append(
                f"<tr><td><code>{escape(task)}</code></td><td>{rep}</td>"
                f"<td>{escape(meta['language'])}</td>{cells}</tr>"
            )
    return "".join(rows)


def render_task_rows(analysis: dict[str, Any]) -> str:
    """Render one aggregate row for each of the 113 tasks."""
    rows = []
    for task in analysis["task_summaries"]:
        delta = task["right_solves"] - task["left_solves"]
        tag_class = "good" if delta > 0 else "bad" if delta < 0 else "neutral"
        rows.append(
            f"<tr><td><code>{escape(task['task'])}</code><small>{escape(task['title'])}</small></td>"
            f"<td>{escape(task['language'])}</td><td>{task['pairs']}</td>"
            f"<td>{task['left_solves']}</td><td>{task['right_solves']}</td>"
            f'<td><span class="pill {tag_class}">{delta:+d}</span></td>'
            f"<td>{task['specialist_read_pairs']}</td><td>{task['excluded_pairs']}</td></tr>"
        )
    return "".join(rows)


def render_packet_rows(analysis: dict[str, Any]) -> str:
    """Render the predeclared material-trajectory packet index."""
    rows = []
    for packet in analysis["packets"]:
        direction = (
            "gain"
            if packet["left"]["reward_binary"] != 1
            and packet["right"]["reward_binary"] == 1
            else "loss"
            if packet["left"]["reward_binary"] == 1
            and packet["right"]["reward_binary"] != 1
            else "partial"
        )
        rows.append(
            "<tr><td><a href="
            + f'"{escape(packet["packet"])}"><code>{escape(packet["task"])}</code></a></td>'
            f"<td>{packet['rep']}</td><td>{escape(packet['language'])}</td>"
            f'<td><span class="pill {"good" if direction == "gain" else "bad" if direction == "loss" else "caution"}">{direction}</span></td>'
            f"<td>{escape(', '.join(packet['selection_reasons']))}</td>"
            f"<td>{escape(packet['primary_driver'])}</td></tr>"
        )
    return "".join(rows)


def render_exclusion_rows(analysis: dict[str, Any]) -> str:
    """Render invalid and resource-contaminated pair evidence."""
    rows = []
    for row in analysis["excluded_pairs"]:
        rows.append(
            f"<tr><td><code>{escape(row['task'])}</code></td><td>{row['rep']}</td>"
            f"<td>{escape(row['left_disposition'])}</td><td>{escape(row['right_disposition'])}</td>"
            f"<td>{escape(row['left_reward_binary'])} → {escape(row['right_reward_binary'])}</td>"
            f"<td>{row['left_oom_kills']} / {row['right_oom_kills']}</td></tr>"
        )
    return "".join(rows)


def render_fuzz_target_rows(analysis: dict[str, Any]) -> str:
    """Render cells that added an actual fuzz target."""
    return "".join(
        f"<tr><td><code>{escape(row['task'])}</code></td><td>{row['rep']}</td>"
        f"<td>{int(row['left_solved'])} → {int(row['right_solved'])}</td>"
        "<td>Go native fuzz target</td></tr>"
        for row in analysis["delivery"]["fuzz_target_rows"]
    )


def render_language_rows(analysis: dict[str, Any]) -> str:
    """Render paired solve movement by implementation language."""
    rows = []
    for language, summary in analysis["splits"]["languages"].items():
        delta = summary["right_solves"] - summary["left_solves"]
        rows.append(
            f"<tr><td>{escape(language)}</td><td>{summary['pairs']}</td>"
            f"<td>{summary['left_solves']}</td><td>{summary['right_solves']}</td>"
            f"<td>{delta:+d}</td><td>{summary['gains']}</td><td>{summary['losses']}</td></tr>"
        )
    return "".join(rows)


def render_tool_error_rows(analysis: dict[str, Any]) -> str:
    """Render tool-result errors with causes and denominators."""
    rows = []
    for config, audit in analysis["behavior"]["tool_errors"].items():
        causes = ", ".join(
            f"{cause}: {count}" for cause, count in sorted(audit["by_cause"].items())
        )
        rate = 100 * audit["errors"] / audit["tool_results"]
        rows.append(
            f"<tr><td><code>{escape(config)}</code></td><td>{audit['tool_results']:,}</td>"
            f"<td>{audit['errors']:,}</td><td>{rate:.1f}%</td><td>{escape(causes)}</td></tr>"
        )
    return "".join(rows)


def render_bucket_rows(analysis: dict[str, Any]) -> str:
    """Render packet driver counts without overstating causal certainty."""
    buckets = Counter(packet["primary_driver"] for packet in analysis["packets"])
    return "".join(
        f"<tr><td>{escape(bucket)}</td><td>{count}</td>"
        "<td>grading-backed packet label; config causality unresolved</td></tr>"
        for bucket, count in buckets.most_common()
    )


def render_html(analysis: dict[str, Any]) -> str:
    """Render the complete evidence-first HTML report."""
    scope = analysis["scope"]
    outcomes = analysis["outcomes"]
    delivery = analysis["delivery"]
    behavior = analysis["behavior"]
    aggregates = behavior["aggregates"]
    score_delta_points = outcomes["solve_rate_delta"] * 100
    interval = outcomes["paired_bootstrap_95_percent"]
    token_delta = aggregates["total_tokens"]["delta_percent"]
    cost_delta = aggregates["combined_cost_usd"]["delta_percent"]
    wall_delta = aggregates["agent_wall_s"]["delta_percent"]
    split_36 = analysis["splits"]["36_v2"]
    split_added = analysis["splits"]["added_77"]
    specialist = delivery["specialist_association"]
    nonspecialist = delivery["non_specialist_association"]
    left_rate = outcomes["left_solves"] / scope["valid_clean_pairs"] * 100
    right_rate = outcomes["right_solves"] / scope["valid_clean_pairs"] * 100
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%232563eb%22/></svg>">
<title>Testing skills vs Pi baseline · full 113</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#667085;--blue:#2563eb;--green:#138a5b;--red:#c43d4b;--amber:#b7791f;--line:#dce3ed}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}}main{{max-width:1360px;margin:auto;padding:42px 24px 64px}}.hero{{background:linear-gradient(135deg,#142039,#28558f);color:#fff;border-radius:22px;padding:38px;box-shadow:0 16px 45px #15223b22}}h1{{font-size:clamp(2rem,5vw,3.6rem);line-height:1.04;margin:.3rem 0 1rem;max-width:18ch}}h2{{margin:38px 0 14px}}h3{{margin-top:0}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#a8c9ff;font-size:.78rem}}.subtitle{{max-width:920px;color:#dce9ff;font-size:1.12rem}}.pills{{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}}.pill{{display:inline-block;border-radius:999px;padding:4px 9px;font-size:.76rem;font-weight:800;white-space:nowrap}}.hero .pill{{background:#ffffff18;color:#fff;border:1px solid #ffffff30}}.pill.good{{background:#dcf7ea;color:#08734a}}.pill.bad{{background:#fee7ea;color:#a72f3d}}.pill.caution{{background:#fff0d2;color:#8b5b0c}}.pill.neutral{{background:#e8eef7;color:#475467}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:20px 0}}.stat,.card,.surface,.callout{{background:var(--surface);border:1px solid var(--line);border-radius:16px}}.stat{{padding:20px}}.stat b{{display:block;font-size:1.8rem;line-height:1.1}}.stat span,small,footer{{color:var(--muted)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}.card,.callout{{padding:18px 20px}}.surface{{padding:8px 20px 18px;overflow:auto}}.callout{{margin-top:18px;border-left:5px solid var(--blue)}}.callout.good{{border-left-color:var(--green)}}.callout.bad{{border-left-color:var(--red)}}.callout.caution{{border-left-color:var(--amber)}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;vertical-align:top;padding:9px;border-bottom:1px solid var(--line)}}th{{position:sticky;top:0;background:var(--surface);z-index:1}}code{{font-size:.86em}}td small{{display:block;max-width:52ch}}a{{color:#175fc0;text-decoration:none}}a:hover{{text-decoration:underline}}.bars{{display:grid;gap:10px}}.bar-row{{display:grid;grid-template-columns:170px 1fr 70px;align-items:center;gap:10px}}.track{{height:14px;background:#e8eef7;border-radius:999px;overflow:hidden}}.fill{{height:100%;background:var(--blue);border-radius:999px}}.fill.green{{background:var(--green)}}footer{{margin-top:36px}}@media(max-width:850px){{main{{padding:20px 12px 44px}}.hero{{padding:26px}}.stats{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}.bar-row{{grid-template-columns:115px 1fr 54px}}}}@media(max-width:430px){{.stats{{grid-template-columns:1fr 1fr}}th,td{{padding:8px 6px}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">Same-model config control · GPT-5.6 Sol low · 113 tasks × 3 reps</div><h1>More solves, but not from specialist testing yet</h1><p class="subtitle">Adding the three testing skills raised the valid clean score from {outcomes["left_solves"]} to {outcomes["right_solves"]} solves. The gain is promising, but 85 pairs flipped direction, the paired interval crosses zero, and actual fuzz or property-test adoption explains none of the solve flips.</p><div class="pills"><span class="pill">{scope["valid_clean_pairs"]} valid clean pairs</span><span class="pill">{outcomes["left_solves"]} → {outcomes["right_solves"]} solves</span><span class="pill">{outcomes["gains"]} gains</span><span class="pill">{outcomes["losses"]} losses</span><span class="pill">{scope["excluded_pairs"]} excluded pairs</span></div></section>
<section class="stats"><div class="stat"><b>+{outcomes["solve_delta"]}</b><span>net valid solves</span></div><div class="stat"><b>{score_delta_points:+.1f} pp</b><span>solve-rate change</span></div><div class="stat"><b>{delivery["specialist_read_cells"]}</b><span>specialist-read cells</span></div><div class="stat"><b>{delivery["fuzz_target_cells"]}</b><span>actual fuzz targets</span></div><div class="stat"><b>{token_delta:+.1f}%</b><span>token change</span></div></section>
<div class="callout good"><strong>Observed result:</strong> On {scope["valid_clean_pairs"]} valid matched pairs, plain Pi solved {outcomes["left_solves"]} ({left_rate:.1f}%) and the testing-skills config solved {outcomes["right_solves"]} ({right_rate:.1f}%). That is +{outcomes["solve_delta"]} solves, with {outcomes["gains"]} treatment-only wins and {outcomes["losses"]} baseline-only wins.</div>
<div class="callout caution"><strong>Confidence:</strong> The exact paired McNemar p-value is {outcomes["exact_mcnemar_p_value"]:.3f}; a deterministic paired bootstrap gives a 95% interval of {interval[0] * 100:+.1f} to {interval[1] * 100:+.1f} percentage points. This is a positive signal, not a conclusive estimate.</div>
<div class="callout"><strong>Mechanism:</strong> Specialist discovery worked: fuzzing was read in {delivery["treatment_reads"]["fuzzing"]} cells and property-based testing in {delivery["treatment_reads"]["property-based-testing"]}. But only {delivery["fuzz_target_cells"]} cells added a fuzz target, none added a property-based test, and all seven fuzz-target cells kept the same solved/unsolved status as baseline. The aggregate gain therefore cannot be credited to specialist technique adoption.</div>
<div class="callout bad"><strong>Validity exclusions:</strong> {scope["excluded_pairs"]} pairs are outside primary efficacy. Fifteen trajectories recorded subject OOM kills; six <code>igel</code> trajectories were ungraded because the verifier image lacked <code>pytest</code>. The raw planned outcomes were {outcomes["raw_planned_left_solves"]}→{outcomes["raw_planned_right_solves"]}, but those numbers include invalid evidence.</div>
<h2>Score and execution cost</h2><div class="grid"><div class="card"><h3>Strict solves</h3><div class="bars"><div class="bar-row"><span>Plain Pi</span><div class="track"><div class="fill" style="width:{left_rate:.2f}%"></div></div><b>{left_rate:.1f}%</b></div><div class="bar-row"><span>Testing skills</span><div class="track"><div class="fill green" style="width:{right_rate:.2f}%"></div></div><b>{right_rate:.1f}%</b></div></div><p>Mean partial reward moved {outcomes["mean_partial_delta"]:+.4f}; median movement was {outcomes["median_partial_delta"]:+.4f}.</p></div><div class="card"><h3>Cost of the treatment</h3><p>Native tokens increased <strong>{token_delta:+.1f}%</strong>, recorded cost <strong>{cost_delta:+.1f}%</strong>, and agent wall time <strong>{wall_delta:+.1f}%</strong>. Test-file patches rose from {behavior["left_test_patch_cells"]} to {behavior["right_test_patch_cells"]} cells. The skills made the model test more, but at substantial token cost.</p></div></div>
<h2>All 339 planned task × rep pairs</h2><p>This complete table appears before filtered cohorts. Linked outcome pills open packets selected by the predeclared material-change rule.</p><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Language</th><th>Baseline</th><th>Skills</th><th>Outcome</th><th>Skills read</th><th>Skills partial</th></tr></thead><tbody>{render_planned_pair_rows(analysis)}</tbody></table></div>
<h2>Where the gain appeared</h2><div class="grid"><div class="card"><h3>Original 36v2 tasks</h3><p>{split_36["left_solves"]}→{split_36["right_solves"]} solves across {split_36["pairs"]} valid pairs: {split_36["gains"]} gains and {split_36["losses"]} losses.</p></div><div class="card"><h3>Added 77 tasks</h3><p>{split_added["left_solves"]}→{split_added["right_solves"]} solves across {split_added["pairs"]} valid pairs: {split_added["gains"]} gains and {split_added["losses"]} losses.</p></div></div><div class="surface"><table><thead><tr><th>Language</th><th>Pairs</th><th>Baseline</th><th>Skills</th><th>Δ</th><th>Gains</th><th>Losses</th></tr></thead><tbody>{render_language_rows(analysis)}</tbody></table></div>
<h2>Skill delivery and adoption</h2><div class="grid"><div class="card"><h3>Delivery was clean</h3><p>All three skills were advertised in {delivery["advertised"]["testing"]}/{scope["valid_clean_pairs"]} treatment prompts. The baseline had zero skill-path reads. The treatment read the broad testing skill in {delivery["treatment_reads"]["testing"]} cells, fuzzing in {delivery["treatment_reads"]["fuzzing"]}, and property testing in {delivery["treatment_reads"]["property-based-testing"]}.</p></div><div class="card"><h3>Specialist reads were not the score mechanism</h3><p>The {delivery["specialist_read_cells"]} specialist-read cells moved {specialist["left_solves"]}→{specialist["right_solves"]} (+{specialist["right_solves"] - specialist["left_solves"]}); the other {nonspecialist["pairs"]} cells moved {nonspecialist["left_solves"]}→{nonspecialist["right_solves"]} (+{nonspecialist["right_solves"] - nonspecialist["left_solves"]}). This association is post-treatment and not causal. More importantly, the seven actual fuzz-target cells produced no solve flips.</p></div></div>
<div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Solve</th><th>Added method</th></tr></thead><tbody>{render_fuzz_target_rows(analysis)}</tbody></table></div>
<h2>Trajectory-backed examples</h2><div class="grid"><div class="card"><h3>Keep: broader contract coverage</h3><p><code>drizzle-orm-window-function-builders</code> improved 0/3→3/3. Baseline repeatedly omitted SingleStore support or frame combinations; the treatment covered those seams and added repository tests. <code>dynamodb-toolbox-lazy-recursive-schemas</code> and <code>valibot-recursive-schema-composition</code> also improved 0/3→3/3 by covering recursive serialization, formatting, async, and composition cases that baseline left incomplete.</p></div><div class="card"><h3>Prevent: example-driven drift</h3><p><code>textual-richlog-follow-state</code> fell 3/3→0/3. All three treatment patches used plain strings for the expanded RichLog example; baseline used Rich <code>Text</code> or <code>Align</code>. The same verifier check failed in every treatment rep. Reading the broad testing skill did not prevent this contract miss.</p></div></div>
<div class="callout"><strong>Interpretation:</strong> The repeatable gains came from broader implementation and example-test coverage, not from fuzzing or property-based testing. The repeatable loss shows the cost of using tests as local confirmation without first pinning the exact observable contract. The next skill change should not force more specialist reads; it should require a short requirement-to-test map before implementation and a final check that every example-facing behavior is exercised.</div>
<h2>Tool-result audit</h2><p>An error-marked shell result usually means a test or diagnostic command returned nonzero, not that the tool broke. Every recorded error is classified below; no malformed argument or parser/transport category was observed.</p><div class="surface"><table><thead><tr><th>Config</th><th>Tool results</th><th>Error-marked</th><th>Rate</th><th>Causes</th></tr></thead><tbody>{render_tool_error_rows(analysis)}</tbody></table></div>
<h2>Excluded evidence and sensitivity</h2><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Baseline disposition</th><th>Skills disposition</th><th>Raw reward</th><th>OOM kills L/R</th></tr></thead><tbody>{render_exclusion_rows(analysis)}</tbody></table></div>
<h2>Task-level valid outcomes</h2><div class="surface"><table><thead><tr><th>Task</th><th>Language</th><th>Valid reps</th><th>Baseline</th><th>Skills</th><th>Δ</th><th>Specialist reads</th><th>Excluded</th></tr></thead><tbody>{render_task_rows(analysis)}</tbody></table></div>
<h2>Material trajectory packets</h2><p>{escape(analysis["packet_rule"])} This selected {analysis["packet_count"]} pairs. Each packet includes paired grading, changed files and line counts, exact successful reads, tool timelines, stage ledgers, failed verifier tests, and a grading-backed driver label.</p><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Language</th><th>Direction</th><th>Trigger</th><th>Driver</th></tr></thead><tbody>{render_packet_rows(analysis)}</tbody></table></div>
<h2>Packet driver ledger</h2><div class="surface"><table><thead><tr><th>Driver</th><th>Packets</th><th>Meaning</th></tr></thead><tbody>{render_bucket_rows(analysis)}</tbody></table></div>
<div class="callout caution"><strong>Decision:</strong> Keep the testing-skills config as a promising candidate, not a proven default. It produced +15 valid solves, but required +{token_delta:.1f}% tokens and the uncertainty interval includes no effect. The full-set result argues for one narrower follow-up: retain the broad testing skill, replace specialist routing work with a requirement-coverage completion check, and A/B it on the 85 solve-flip cells with a fixed cost ceiling.</div>
<footer>Generated from {scope["full_trajectories"]} planned result artifacts, native Pi sessions, captured prompts, model patches, CTRF verifier reports, and quarantine provenance. Primary efficacy uses {scope["valid_clean_trajectories"]} valid clean trajectories ({scope["valid_clean_pairs"]} matched pairs). {escape(scope["difficulty_note"])} Data: <code>analysis/testing-skills-1.1.0/full113-comparison.json</code>.</footer>
</main></body></html>"""


def write_full113_report() -> dict[str, Any]:
    """Generate evidence JSON, packet files, and the self-contained report."""
    analysis = write_full113_analysis()
    PACKET_ROOT.mkdir(parents=True, exist_ok=True)
    for stale in PACKET_ROOT.glob("*.json"):
        stale.unlink()
    for packet in analysis["packets"]:
        packet_path = REPORT_ROOT / packet["packet"]
        packet_path.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.write_text(render_html(analysis))
    return analysis


if __name__ == "__main__":
    result = write_full113_report()
    print(f"wrote {REPORT_PATH}")
    print(f"wrote {result['packet_count']} packets")

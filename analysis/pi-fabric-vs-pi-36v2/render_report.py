#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
import json
import re
import shutil
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
OUT = REPO / "reports/pi-fabric-vs-pi-36v2"
SUMMARY = json.loads((HERE / "summary.json").read_text())
CLASS = json.loads((HERE / "churn_deep_dive/classification.json").read_text())


def esc(value: object) -> str:
    return html.escape(str(value))


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def signed(value: float, digits: int = 3) -> str:
    return f"{value:+.{digits}f}"


def money(value: float) -> str:
    return f"${value:,.3f}"


def metric_rows() -> str:
    agg = SUMMARY["aggregate"]
    n = agg["n"]
    base, fabric, delta = agg["baseline"], agg["pi-fabric"], agg["delta"]
    rows = [
        (
            "Full solves",
            f"{base['solves']}/{n}",
            f"{fabric['solves']}/{n}",
            f"{fabric['solves'] - base['solves']:+d}",
            "bad",
        ),
        (
            "Mean partial reward",
            f"{base['mean_partial']:.3f}",
            f"{fabric['mean_partial']:.3f}",
            signed(delta["mean_reward_partial"]),
            "neutral",
        ),
        (
            "Mean feature tests",
            pct(base["mean_f2p"]),
            pct(fabric["mean_f2p"]),
            signed(delta["mean_f2p"]),
            "bad",
        ),
        (
            "Mean preservation tests",
            pct(base["mean_p2p"]),
            pct(fabric["mean_p2p"]),
            signed(delta["mean_p2p"]),
            "neutral",
        ),
        (
            "Median tokens",
            f"{base['median_tokens']:,.0f}",
            f"{fabric['median_tokens']:,.0f}",
            f"{delta['median_combined_total_tokens']:+,.0f}",
            "bad",
        ),
        (
            "Median cost",
            money(base["median_cost"]),
            money(fabric["median_cost"]),
            f"{delta['median_combined_cost_usd']:+.3f}",
            "bad",
        ),
        (
            "Median wall time",
            f"{base['median_wall_s']:.1f}s",
            f"{fabric['median_wall_s']:.1f}s",
            f"{delta['median_agent_wall_s']:+.1f}s",
            "bad",
        ),
        (
            "Median turns",
            f"{base['median_turns']:.1f}",
            f"{fabric['median_turns']:.1f}",
            f"{delta['median_turns']:+.1f}",
            "neutral",
        ),
        (
            "Median outer tool calls",
            f"{base['median_tool_calls']:.1f}",
            f"{fabric['median_tool_calls']:.1f}",
            f"{delta['median_tool_calls']:+.1f}",
            "neutral",
        ),
        (
            f"Total cost · {n} cells",
            money(base["total_cost"]),
            money(fabric["total_cost"]),
            f"{fabric['total_cost'] - base['total_cost']:+.3f}",
            "bad",
        ),
    ]
    return "".join(
        f"<tr><td>{name}</td><td class='num'>{left}</td><td class='num'>{right}</td><td class='num {tone}'>{change}</td></tr>"
        for name, left, right, change, tone in rows
    )


def difficulty_rows() -> str:
    rows = []
    for difficulty in ["hard", "medium", "easy"]:
        item = SUMMARY["by_difficulty"][difficulty]
        base, fabric, delta = item["baseline"], item["pi-fabric"], item["delta"]
        rows.append(
            f"<tr><td><strong>{difficulty.title()}</strong> · n={item['n']}</td>"
            f"<td class='num'>{base['solves']} → {fabric['solves']}</td>"
            f"<td class='num {'good' if delta['mean_reward_partial'] > 0 else 'bad'}'>{signed(delta['mean_reward_partial'])}</td>"
            f"<td class='num bad'>{delta['median_combined_total_tokens']:+,.0f}</td>"
            f"<td class='num bad'>{delta['median_combined_cost_usd']:+.3f}</td></tr>"
        )
    return "".join(rows)


def packet_rows() -> str:
    csv_rows = {}
    with (HERE / "paired_cells.csv").open() as handle:
        for row in csv.DictReader(handle):
            csv_rows[(row["task"], int(row["rep"]))] = row
    rows = []
    for key, classification in CLASS["items"].items():
        task, rep_text = key.rsplit("__rep", 1)
        rep = int(rep_text)
        row = csv_rows[(task, rep)]
        left_bin = float(row["baseline_reward_binary"]) == 1
        right_bin = float(row["pi_fabric_reward_binary"]) == 1
        if left_bin != right_bin:
            movement = "Fabric gain" if right_bin > left_bin else "Fabric loss"
            tone = "good" if right_bin > left_bin else "bad"
        else:
            movement, tone = "Material partial shift", "neutral"
        packet = f"packets/{task}__rep{rep}.json"
        rows.append(
            f"<tr><td><a href='{packet}'><code>{esc(task)}</code> · rep{rep}</a><br><span class='muted'>{esc(row['difficulty'])} · {esc(row['language'])}</span></td>"
            f"<td><span class='tag {tone}'>{movement}</span><br><span class='muted'>{float(row['baseline_reward_partial']):.3f} → {float(row['pi_fabric_reward_partial']):.3f}</span></td>"
            f"<td><strong>{esc(classification['primary_bucket'])}</strong><br><span class='muted'>{esc(classification['mechanism'])}</span></td></tr>"
        )
    return "".join(rows)


def language_rows() -> str:
    rows = []
    for language, item in SUMMARY["by_language"].items():
        base, fabric, delta = item["baseline"], item["pi-fabric"], item["delta"]
        rows.append(
            f"<tr><td><strong>{esc(language.title())}</strong> · n={item['n']}</td>"
            f"<td class='num'>{base['solves']} → {fabric['solves']}</td>"
            f"<td class='num'>{signed(delta['mean_reward_partial'])}</td>"
            f"<td class='num bad'>{delta['median_combined_cost_usd']:+.3f}</td></tr>"
        )
    return "".join(rows)


def bucket_rows() -> str:
    return "".join(
        f"<tr><td>{esc(bucket)}</td><td class='num'>{count}</td></tr>"
        for bucket, count in sorted(
            CLASS["counts"].items(), key=lambda item: (-item[1], item[0])
        )
    )


def guidance_rows() -> str:
    hypotheses = [
        (
            "Option matrix",
            "List and test every mode × option interaction.",
            "SuperJSON and SQL formatter losses",
            "Participle improved without a full matrix.",
        ),
        (
            "State scope",
            "Key lifecycle state by owner, test, group, name, and generation.",
            "Two Mobly losses; Tengo rep2 timeout",
            "Tengo reps 0 and 1 succeeded with different runtime seams.",
        ),
        (
            "Protocol contract",
            "Test success, error, empty, unknown, and recursive branches end to end.",
            "Claude delegation and Go doc-link losses",
            "Protocol tests do not explain Adaptix or Mobly.",
        ),
        (
            "Final validation",
            "Run an import/full targeted suite after the last edit.",
            "Adaptix plain-Pi syntax error",
            "Single-cell evidence; treat as a completion-discipline hypothesis.",
        ),
    ]
    return "".join(
        f"<tr><td><strong>{esc(trigger)}</strong></td><td>{esc(action)}</td><td>{esc(evidence)}</td><td class='muted'>{esc(counterexample)}</td></tr>"
        for trigger, action, evidence, counterexample in hypotheses
    )


def behavior_audit() -> dict[str, Any]:
    root = REPO / "results/gpt-5.6-sol/low/pi-fabric"
    tools: Counter[str] = Counter()
    core: Counter[str] = Counter()
    skill_reads: Counter[str] = Counter()
    mesh_cells = 0
    fabric_cells = 0
    names = [
        "fabric-exec",
        "fabric-advisor",
        "fabric-ambient",
        "fabric-council",
        "fabric-fusion",
        "fabric-guide",
        "fabric-rlm",
        "fabric-schema",
        "fabric-supervisor",
        "fabric-swarm",
        "fabric-workflow",
    ]
    for cell in root.glob("*/rep*"):
        if not (cell / "result.json").exists():
            continue
        patch = (cell / "artifacts/model.patch").read_text(errors="replace")
        mesh_cells += int(".pi/fabric/mesh/state.json" in patch)
        used = False
        for session in cell.glob("session/*.jsonl"):
            for line in session.read_text(errors="replace").splitlines():
                record = json.loads(line)
                content = record.get("message", {}).get("content", [])
                if not isinstance(content, list):
                    continue
                for item in content:
                    if item.get("type") != "toolCall":
                        continue
                    name = item.get("name", "unknown")
                    tools[name] += 1
                    body = str(item.get("arguments", {}).get("code", ""))
                    used |= name == "fabric_exec"
                    for operation in [
                        "read",
                        "bash",
                        "bashSettled",
                        "find",
                        "ls",
                        "grep",
                        "write",
                        "edit",
                    ]:
                        core[operation] += len(
                            re.findall(rf"\bpi\.{operation}\s*\(", body)
                        )
                    if "SKILL.md" in body:
                        for skill in names:
                            if f"/{skill}/SKILL.md" in body:
                                skill_reads[skill] += 1
        fabric_cells += int(used)
    return {
        "fabric_cells": fabric_cells,
        "mesh_cells": mesh_cells,
        "tools": dict(tools),
        "core": dict(core),
        "skill_reads": dict(skill_reads),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    packets = OUT / "packets"
    packets.mkdir(exist_ok=True)
    for stale in packets.glob("*__rep*.json"):
        stale.unlink()
    for source in (HERE / "churn_deep_dive").glob("*__rep*.json"):
        shutil.copy2(source, packets / source.name)
    shutil.copy2(HERE / "summary.json", OUT / "summary.json")
    shutil.copy2(HERE / "paired_cells.csv", OUT / "paired_cells.csv")
    audit = behavior_audit()
    agg = SUMMARY["aggregate"]
    base, fabric = agg["baseline"], agg["pi-fabric"]
    agreement = SUMMARY["agreement"]
    ci_low, ci_high = SUMMARY["cluster_bootstrap_partial_ci95"]
    cost_pct = (fabric["median_cost"] / base["median_cost"] - 1) * 100
    token_pct = (fabric["median_tokens"] / base["median_tokens"] - 1) * 100
    wall_pct = (fabric["median_wall_s"] / base["median_wall_s"] - 1) * 100
    n = agg["n"]
    packet_count = len(CLASS["items"])
    core_items = ", ".join(
        f"{name} {count:,}" for name, count in audit["core"].items() if count
    )
    doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Pi Fabric vs plain Pi · GPT-5.6-sol low</title><link rel='icon' href='data:,'><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:26px;--max:1240px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.11),transparent 30%),radial-gradient(circle at top right,rgba(208,71,63,.08),transparent 26%),linear-gradient(180deg,#fbfdff,var(--bg));color:var(--ink);font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;line-height:1.55}}.wrap{{max-width:var(--max);margin:auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:var(--radius);box-shadow:var(--shadow)}}.hero{{padding:clamp(26px,4vw,44px)}}section{{padding:clamp(20px,3vw,30px);margin-top:20px;overflow-x:auto}}h1,h2,h3{{margin:0;line-height:1.08;letter-spacing:-.03em}}h1{{font-size:clamp(2.2rem,5vw,4.5rem);max-width:15ch;margin-top:14px}}h2{{font-size:clamp(1.4rem,2.4vw,2rem)}}p{{color:var(--muted)}}.eyebrow,.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.05em;text-transform:uppercase}}.eyebrow{{padding:8px 12px;background:#eef3ff;color:#1d3fb8}}.pillrow{{display:flex;flex-wrap:wrap;gap:10px;margin-top:22px}}.pill{{padding:8px 12px;border:1px solid var(--line)}}.pill.good,.tag.good{{background:var(--green-soft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--red-soft);color:var(--red)}}.pill.caution{{background:var(--amber-soft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:26px}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;min-height:116px}}.stat .label{{display:block;color:var(--muted);font-size:11px;font-weight:850;text-transform:uppercase;letter-spacing:.07em}}.stat .value{{display:block;font-size:clamp(1.35rem,2vw,2rem);font-weight:900;margin-top:8px;letter-spacing:-.04em}}.stat .sub{{display:block;color:var(--muted);font-size:.88rem;margin-top:7px}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.neutral{{color:#1d3fb8}}.muted{{color:var(--muted)}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:15px 17px;margin-top:16px}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid2>*{{min-width:0}}.head{{margin-bottom:16px}}.head p{{margin:.45rem 0 0;max-width:86ch}}table{{width:100%;border-collapse:collapse;font-size:.92rem}}th,td{{padding:11px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}td.num,th.num{{text-align:right;white-space:nowrap;font-variant-numeric:tabular-nums}}code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:#eef2ff;color:#24346f;border-radius:6px;padding:.12em .35em}}a{{color:var(--blue);text-decoration:none}}a:hover{{text-decoration:underline}}.tag{{padding:4px 9px}}.bars{{display:grid;gap:14px}}.barrow{{display:grid;grid-template-columns:110px 1fr 110px;gap:12px;align-items:center}}.track{{height:18px;border-radius:999px;background:#edf2f7;border:1px solid #dde5ef;overflow:hidden}}.fill{{height:100%;background:linear-gradient(90deg,#6a8cff,#335dff);border-radius:999px}}.fill.bad{{background:linear-gradient(90deg,#f26a5f,#d0473f)}}.foot{{margin-top:22px;text-align:center;color:var(--muted);font-size:.86rem}}@media(max-width:900px){{.stats,.grid2{{grid-template-columns:1fr 1fr}}}}@media(max-width:650px){{.stats,.grid2{{grid-template-columns:1fr}}.barrow{{grid-template-columns:1fr}}table{{font-size:.8rem}}th,td{{padding:7px 5px}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>DeepSWE · 36_v2 × 3 reps · GPT-5.6-sol low</span><h1>Similar solve rate, substantially higher cost</h1><p>Matched comparison of plain Pi against the out-of-box Pi Fabric extension on the same 36 tasks and three repetitions. Delivery was confirmed in all {n} paired cells. Pi Fabric produced nearly the same full-solve rate and a small, uncertain partial-credit increase, while materially increasing tokens, cost, and wall time.</p><div class='pillrow'><span class='pill neutral'>Solves: {base["solves"]} → {fabric["solves"]}</span><span class='pill bad'>Median cost: +{cost_pct:.0f}%</span><span class='pill bad'>Median tokens: +{token_pct:.0f}%</span><span class='pill neutral'>Partial: {agg["delta"]["mean_reward_partial"]:+.3f}, inconclusive</span><span class='pill good'>{n}/{n} completed</span></div><div class='stats'><div class='stat'><span class='label'>Full solves</span><span class='value neutral'>{base["solves"]} → {fabric["solves"]}</span><span class='sub'>{agreement["net"]:+d} net cells</span></div><div class='stat'><span class='label'>Solve churn</span><span class='value'>{agreement["right_only"]} / {agreement["left_only"]}</span><span class='sub'>Fabric-only / plain-Pi-only</span></div><div class='stat'><span class='label'>Mean partial</span><span class='value neutral'>{agg["delta"]["mean_reward_partial"]:+.3f}</span><span class='sub'>95% clustered CI {ci_low:+.3f} to {ci_high:+.3f}</span></div><div class='stat'><span class='label'>Median cost</span><span class='value bad'>{money(base["median_cost"])} → {money(fabric["median_cost"])}</span><span class='sub'>+{cost_pct:.1f}%</span></div><div class='stat'><span class='label'>Median wall time</span><span class='value bad'>+{wall_pct:.0f}%</span><span class='sub'>{base["median_wall_s"]:.1f}s → {fabric["median_wall_s"]:.1f}s</span></div></div><div class='callout'><strong>Verdict:</strong> the 36_v2 result does not show a reliable efficacy change: Pi Fabric is {agreement["net"]:+d} full solves with exact paired p={agreement["mcnemar_p"]:.3f}, and the clustered partial-reward interval crosses zero. The clear measured effect is resource use: higher tokens, cost, and latency. The trajectories are still useful because they expose concrete winning and losing implementation patterns for the maintainer.</div></header>
<section><div class='head'><h2>Headline comparison</h2><p>Every row uses the same task, repetition, model, and low thinking level. Outer tool calls are not directly comparable because Pi Fabric batches multiple file or shell operations into one call.</p></div><table><thead><tr><th>Metric</th><th class='num'>Plain Pi</th><th class='num'>Pi Fabric</th><th class='num'>Paired change</th></tr></thead><tbody>{metric_rows()}</tbody></table></section>
<section><div class='head'><h2>Net score hides {agreement["left_only"] + agreement["right_only"]} solve flips</h2><p>{packet_count} cells were selected for packet review: every binary flip, every |Δpartial|, |Δf2p|, or |Δp2p| ≥ 0.10 cell, and any timeout or negative-reward discordance. The table names the concrete verifier-linked mechanism rather than treating churn as noise.</p></div><div style='overflow-x:auto'><table><thead><tr><th>Cell</th><th>Movement</th><th>Primary driver and evidence</th></tr></thead><tbody>{packet_rows()}</tbody></table></div><div class='callout'><strong>Pattern:</strong> Pi Fabric gained {agreement["right_only"]} solves and lost {agreement["left_only"]}. Across both directions, packet evidence most often points to implementation completeness, protocol handling, and missing invariants. No packet establishes one uniform causal mechanism, and no optional Fabric orchestration skill was used.</div></section>
<section><div class='head'><h2>Difficulty and language splits</h2><p>These splits are descriptive only. The paired trajectory packets, not subgroup averages, are the basis for mechanism claims.</p></div><div class='grid2'><table><thead><tr><th>Difficulty</th><th class='num'>Solves · Pi → Fabric</th><th class='num'>Mean Δpartial</th><th class='num'>Median Δtokens</th><th class='num'>Median Δcost</th></tr></thead><tbody>{difficulty_rows()}</tbody></table><table><thead><tr><th>Language</th><th class='num'>Solves · Pi → Fabric</th><th class='num'>Mean Δpartial</th><th class='num'>Median Δcost</th></tr></thead><tbody>{language_rows()}</tbody></table></div></section><section><div class='head'><h2>Driver buckets and improvement hypotheses</h2><p>These are local, evidence-linked hypotheses for this package and comparison—not proven general rules.</p></div><div class='grid2'><table><thead><tr><th>Primary driver</th><th class='num'>Packets</th></tr></thead><tbody>{bucket_rows()}</tbody></table><table><thead><tr><th>Trigger</th><th>Action</th><th>Observed evidence</th><th>Counterexample / limit</th></tr></thead><tbody>{guidance_rows()}</tbody></table></div></section>
<section><div class='head'><h2>What the extension actually did</h2><p>This matters for interpretation: the benchmark installed all shipped skills with their default discoverability, but the model-facing behavior was overwhelmingly the Fabric execution wrapper.</p></div><div class='grid2'><div><div class='callout good'><strong>Delivery confirmed:</strong> {n}/{n} cells exposed <code>fabric_exec</code>, the <code>fabric-exec</code> skill, GPT-5.6-sol, and low reasoning in captured provider requests. No extension-load errors appeared.</div><div class='callout'><strong>Observed use:</strong> <code>fabric_exec</code> was called {audit["tools"].get("fabric_exec", 0):,} times across {n}/{n} cells. Statically extracted inner operations: {esc(core_items)}.</div></div><div><div class='callout'><strong>Skill use:</strong> only <code>fabric-exec</code> was opened ({audit["skill_reads"].get("fabric-exec", 0)} reads). No advisor, council, workflow, swarm, or other optional Fabric skill was opened in the trajectories.</div><div class='callout bad'><strong>Workspace pollution:</strong> {audit["mesh_cells"]}/{n} Pi Fabric patches included extension-generated <code>.pi/fabric/mesh/state.json</code>. The verifier generally ignored it, but it inflated patches and is undesirable out-of-box behavior.</div></div></div></section>
<section><div class='head'><h2>Resource tradeoff</h2><p>Pi Fabric increased tokens and cost even though median turns were flat and counted outer tool calls fell. Batching makes call counts smaller, not the underlying work.</p></div><div class='bars'><div class='barrow'><strong>Median tokens</strong><div class='track'><div class='fill bad' style='width:100%'></div></div><span>{fabric["median_tokens"]:,.0f} · +{token_pct:.1f}%</span></div><div class='barrow'><strong>Median cost</strong><div class='track'><div class='fill bad' style='width:{fabric["median_cost"] / 1.2 * 100:.1f}%'></div></div><span>{money(fabric["median_cost"])} · +{cost_pct:.1f}%</span></div><div class='barrow'><strong>Median wall</strong><div class='track'><div class='fill bad' style='width:{fabric["median_wall_s"] / 400 * 100:.1f}%'></div></div><span>{fabric["median_wall_s"]:.1f}s · +{wall_pct:.1f}%</span></div></div></section>
<section><div class='head'><h2>Conclusion</h2></div><div class='grid2'><div class='callout'><strong>Observed:</strong> Pi Fabric solved {fabric["solves"]}/{n} cells versus plain Pi's {base["solves"]}/{n}. Median cost rose {cost_pct:.1f}%, tokens {token_pct:.1f}%, and wall time {wall_pct:.1f}%.</div><div class='callout'><strong>Uncertain:</strong> mean partial rose {agg["delta"]["mean_reward_partial"]:+.3f}, but the clustered 95% interval crosses zero and the median paired delta is zero.</div></div><div class='callout'><strong>Maintainer takeaway:</strong> the extension did not materially change aggregate solve rate in this comparison, but it imposed substantial overhead. The most actionable evidence is in the {packet_count} paired packets: keep the cases where Fabric trajectories covered more surfaces or preserved runtime state, and target the recurring incomplete protocol, lifecycle, and edge-case implementations.</div><p class='muted'>Scope: <code>baseline</code> vs <code>pi-fabric</code>, 36_v2, 3 reps, <code>openai-codex/gpt-5.6-sol</code>, low thinking. Baseline results were reused from the matching completed baseline corpus; Pi Fabric reused the completed 12_v2 cells and ran the remaining 72. All {n} paired cells have results. One baseline empty-patch cell has no f2p/p2p grades, so those means use 107 paired graded cells; binary and partial outcomes still include all {n}. Raw data: <a href='summary.json'>summary.json</a> · <a href='paired_cells.csv'>paired_cells.csv</a>.</p></section><div class='foot'>Deterministic analysis: <code>analysis/pi-fabric-vs-pi-36v2/</code> · Run: <code>gpt56-sol-low-pi-fabric-36v2-r3-w16-20260724</code></div>
</div></body></html>"""
    (OUT / "index.html").write_text(doc)
    (HERE / "index.html").write_text(doc)
    print(OUT / "index.html")


if __name__ == "__main__":
    main()

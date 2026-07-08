#!/usr/bin/env python3
from __future__ import annotations
import html, json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "summary.json").read_text())
S = DATA["summaries"]; P = DATA["pairs"]
USEAM = DATA["codegraph_usage_seam"]; UOLD = DATA["codegraph_usage_old"]
LABELS = DATA["labels"]
BASE = "baseline"; OLD = "codegraph-cli-skill"; SEAM = "codegraph-cli-skill-seam-checkpoint"
SKILL = "codegraph-skill"; WF = "baseline-wf-only"; GOAL = "pi-codex-goal"
MED = "baseline__gpt55_medium"; PMED = "baseline-preamble-orchestration__gpt55_medium"
ORDER = [BASE, OLD, SEAM, SKILL, WF, GOAL, MED, PMED]
SHORT = {BASE: "Clean Pi low", OLD: "CodeGraph CLI · old skill", SEAM: "CodeGraph CLI · seam skill",
         SKILL: "CodeGraph skill low", WF: "Workflow prompt low", GOAL: "pi-codex-goal low",
         MED: "Clean Pi medium", PMED: "Pi preamble/orch medium"}


def esc(x): return html.escape(str(x))
def fmt_int(x): return f"{int(round(x)):,}"
def money(x, d=3): return f"${x:,.{d}f}"
def f4(x): return f"{x:.4f}"
def signed(x, d=3, dollar=False, integer=False):
    pref = "+" if x >= 0 else "−"; v = abs(x)
    if dollar: body = money(v, d)
    elif integer: body = fmt_int(v)
    else: body = f"{v:.{d}f}"
    return pref + body
def tone(x, higher=True):
    if abs(x) < 1e-12: return "neutral"
    return "good" if ((x > 0) == higher) else "bad"
def pval(x): return "—" if x is None else f"p={x:.3g}"
def th(x, cls=""): return f"<th class='{cls}'>{esc(x)}</th>"
def td(x, cls=""): return f"<td class='{cls}'>{x}</td>"
def tr(cells, cls=""): return f"<tr class='{cls}'>" + "".join(cells) + "</tr>"
def pill(text, kind="neutral"): return f"<span class='pill {kind}'>{esc(text)}</span>"


def main_rows():
    out = []
    for c in ORDER:
        s = S[c]
        out.append(tr([
            td(f"<strong>{esc(SHORT[c])}</strong><br><span class='muted mono'>{esc(c)}</span>"),
            td(f"{s['solves']}/108", "num"), td(f4(s["mean_partial"]), "num"), td(money(s["median_cost"]), "num"),
            td(fmt_int(s["median_tokens"]), "num"), td(f"{s['median_wall_s']:.1f}s", "num"), td(f"{s['median_turns']:.1f}", "num"),
            td(f"{s['median_tool_calls']:.1f}", "num"), td(money(s["total_cost"], 2), "num")]))
    return "\n".join(out)


def pair_rows(keys):
    out = []
    for key, label in keys:
        p = P[key]
        out.append(tr([
            td(f"<strong>{esc(label)}</strong><br><span class='muted'>{esc(p['a_label'])} → {esc(p['b_label'])}</span>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"), td(signed(p["solve_delta"], integer=True), f"num {tone(p['solve_delta'])}"),
            td(signed(p["mean_delta_partial"], 4), f"num {tone(p['mean_delta_partial'])}"),
            td(signed(p["median_delta_cost"], dollar=True), f"num {tone(p['median_delta_cost'], False)}"),
            td(signed(p["median_delta_tokens"], integer=True), f"num {tone(p['median_delta_tokens'], False)}"),
            td(signed(p["median_delta_wall_s"], 1), f"num {tone(p['median_delta_wall_s'], False)}"),
            td(f"{p['b_only']} / {p['a_only']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num")]))
    return "\n".join(out)


def difficulty_rows(pair_key):
    p = P[pair_key]; out = []
    for b in ["hard", "medium", "easy"]:
        d = p["difficulty"][b]
        out.append(tr([td(b.title()), td(f"{d['a_solves']} → {d['b_solves']}", "num"), td(signed(d["solve_delta"], integer=True), f"num {tone(d['solve_delta'])}"), td(signed(d["mean_delta_partial"], 4), f"num {tone(d['mean_delta_partial'])}"), td(signed(d["median_delta_cost"], dollar=True), f"num {tone(d['median_delta_cost'], False)}"), td(signed(d["median_delta_tokens"], integer=True), f"num {tone(d['median_delta_tokens'], False)}")]))
    return "\n".join(out)


def group_rows():
    out = []
    for c in ORDER:
        for b in ["hard", "medium", "easy"]:
            d = S[c]["by_difficulty"].get(b, {"n": 0, "solves": 0, "mean_partial": 0, "median_cost": 0, "median_tokens": 0})
            out.append(tr([td(SHORT[c]), td(b.title()), td(f"{d['solves']}/{d['n']}", "num"), td(f4(d["mean_partial"]), "num"), td(money(d["median_cost"]), "num"), td(fmt_int(d["median_tokens"]), "num")]))
    return "\n".join(out)


def usage_compare_rows():
    seam = USEAM["command_counter"]; old = UOLD["command_counter"]
    keys = sorted(set(list(seam) + list(old)), key=lambda k: -(seam.get(k, 0) + old.get(k, 0)))
    out = []
    for k in keys:
        out.append(tr([td(k), td(fmt_int(old.get(k, 0)), "num"), td(fmt_int(seam.get(k, 0)), "num"), td(signed(seam.get(k, 0) - old.get(k, 0), integer=True), f"num {tone(seam.get(k,0)-old.get(k,0))}")]))
    return "\n".join(out)


def flip_rows(pair_key, kind):
    arr = P[pair_key][kind][:12]
    return "\n".join(tr([td(f"<strong>{esc(m['title'])}</strong><br><span class='muted mono'>{esc(m['task'])} · rep{m['rep']} · {m['difficulty']}</span>"), td(f"{m['a_partial']:.3f} → {m['b_partial']:.3f}", "num"), td(signed(m["delta_partial"], 3), f"num {tone(m['delta_partial'])}"), td(signed(m["delta_tokens"], integer=True), f"num {tone(m['delta_tokens'], False)}")]) for m in arr) or tr([td("None"), td("—", "num"), td("—", "num"), td("—", "num")])


def pareto_rows():
    out = []
    for r in DATA["pareto"]:
        frontier = not r["dominated_by"]
        out.append(tr([td(f"<strong>{esc(SHORT[r['config']])}</strong>"), td(f"{r['solves']}/108", "num"), td(money(r["median_cost"]), "num"), td(f4(r["mean_partial"]), "num"), td(f"<span class='tag {'good' if frontier else 'neutral'}'>{'frontier' if frontier else 'dominated'}</span>"), td(", ".join(SHORT[d] for d in r["dominated_by"]) or "—")]))
    return "\n".join(out)


seam_head = P[f"{OLD}__vs__{SEAM}"]
base_head = P[f"{BASE}__vs__{SEAM}"]
med_head = P[f"{SEAM}__vs__{MED}"]

html_doc = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'><title>CodeGraph seam-checkpoint skill · 36_v2 report</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:24px}}*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.13),transparent 30%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);line-height:1.5}}.wrap{{max-width:1360px;margin:0 auto;padding:28px 20px 52px}}.hero,section{{background:rgba(255,255,255,.95);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;letter-spacing:-.03em;line-height:1.08}}h1{{font-size:clamp(2.1rem,4.8vw,4.2rem);max-width:20ch;margin-top:14px}}h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}h3{{font-size:1.05rem;margin:12px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.08rem;max-width:96ch}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good,.tag.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:#1d3fb8}}.tag{{padding:4px 9px}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:118px}}.stat .label{{display:block;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.08em;font-weight:850;margin-bottom:8px}}.stat .value{{display:block;font-size:clamp(1.35rem,2vw,2rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;color:var(--muted);font-size:.9rem;margin-top:8px;font-weight:650}}table{{width:100%;border-collapse:collapse;font-size:.92rem}}th,td{{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}.mono,code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}code{{background:#eef2ff;border-radius:6px;padding:.12em .35em}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:#1d3fb8}}.grid2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin:14px 0}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}.head{{display:flex;justify-content:space-between;align-items:end;gap:14px;flex-wrap:wrap;margin-bottom:14px}}.head p{{margin:.4rem 0 0;max-width:88ch}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}@media(max-width:900px){{.stats,.grid2,.grid3{{grid-template-columns:1fr}}.hero{{padding:26px}}table{{font-size:.82rem}}th,td{{padding:7px 6px}}}}
</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>CodeGraph seam-checkpoint skill · GPT-5.5 low · 36_v2 × 3 reps</span><h1>The seam-checkpoint additions did not move the needle.</h1><p class='subtitle'>This run isolates the <strong>skill-text change only</strong>. <code>codegraph-cli-skill-seam-checkpoint</code> differs from the original <code>codegraph-cli-skill</code> by exactly one thing: the CodeGraph skill file was updated to add a pre-edit <em>seam checkpoint</em>, a <em>choose the behavioral seam</em> scout step, and a rule to <em>let CodeGraph make the edit smaller</em>. Same model, same tools, same one-line prompt, same CLI. At 3 reps the two skills are statistically indistinguishable.</p>
<div class='pillrow'>{pill('run complete: 108/108 results','good')}{pill('0 transient / 0 timeout / 0 empty','good')}{pill('skill has seam checkpoint + behavioral seam','good')}{pill('old skill 30 → seam skill 31','neutral')}{pill('not significant','caution')}</div>
<div class='stats'><div class='stat'><span class='label'>Old skill</span><span class='value'>30/108</span><span class='sub'>{money(S[OLD]['median_cost'])} median cost</span></div><div class='stat'><span class='label'>Seam skill</span><span class='value'>31/108</span><span class='sub'>{money(S[SEAM]['median_cost'])} median cost</span></div><div class='stat'><span class='label'>Δ solves (seam − old)</span><span class='value'>+1</span><span class='sub caution'>p={seam_head['mcnemar_p']:.2f}, not significant</span></div><div class='stat'><span class='label'>Δ median cost</span><span class='value'>{signed(seam_head['median_delta_cost'], dollar=True)}</span><span class='sub good'>seam slightly cheaper</span></div><div class='stat'><span class='label'>vs Clean Pi medium</span><span class='value'>−19</span><span class='sub bad'>thinking still wins</span></div></div></header>

<section><div class='head'><div><h2>Run health and treatment validation</h2><p>The run completed cleanly and the treatment is exactly the intended single-variable change.</p></div></div><div class='grid2'><div class='callout good'><strong>Run health:</strong> state done, 108/108 cells ok, 0 transient, 0 failed, 0 timeout, 0 empty patches, 0 reward=−1.</div><div class='callout'><strong>Treatment isolation:</strong> same one-line orchestration <code>{esc(DATA['treatment']['orchestration'])}</code> in 108/108 captured prompts; skill file verified to contain both <code>seam checkpoint</code> and <code>Choose the behavioral seam before editing</code>; same vendored CLI and PATH. The only delta is the skill markdown.</div></div><table><thead><tr>{th('Evidence')}{th('Seam skill','num')}{th('Old skill','num')}</tr></thead><tbody><tr><td>CodeGraph cells</td><td class='num'>{USEAM['codegraph_cells']}/108</td><td class='num'>{UOLD['codegraph_cells']}/108</td></tr><tr><td>Cells with <code>codegraph build</code></td><td class='num'>{USEAM['build_cells']}/108</td><td class='num'>{UOLD['build_cells']}/108</td></tr><tr><td>Cells that read the skill file</td><td class='num'>{USEAM['read_skill_cells']}/108</td><td class='num'>{UOLD['read_skill_cells']}/108</td></tr><tr><td>Total bash calls containing <code>codegraph</code>/<code>cg</code></td><td class='num'>{fmt_int(USEAM['total_codegraph_calls'])}</td><td class='num'>{fmt_int(UOLD['total_codegraph_calls'])}</td></tr></tbody></table></section>

<section><div class='head'><div><h2>Headline comparison: old skill → seam skill</h2><p>The two skill variants are indistinguishable at 3 reps. The seam skill nets +1 solve but that is well inside the solve-flip churn (10 gains, 9 losses).</p></div></div><table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}{th('Median wall','num')}{th('Turns','num')}{th('Tool calls','num')}{th('Total cost','num')}</tr></thead><tbody>{main_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Paired deltas</h2><p>The headline row is the controlled skill-text comparison. The other rows place the seam skill against clean low, the workflow prompt, and clean medium.</p></div></div><table><thead><tr>{th('Comparison')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('Median Δ wall','num')}{th('Right-only / left-only','num')}{th('Tests','num')}</tr></thead><tbody>{pair_rows([(f'{OLD}__vs__{SEAM}','Old skill → seam skill (controlled)'),(f'{BASE}__vs__{SEAM}','Clean Pi low → seam skill'),(f'{SKILL}__vs__{SEAM}','CodeGraph skill → seam skill'),(f'{WF}__vs__{SEAM}','Workflow prompt → seam skill'),(f'{SEAM}__vs__{MED}','Seam skill low → clean Pi medium')])}</tbody></table><div class='callout caution'><strong>Statistical read:</strong> the controlled skill delta is +1 solve (McNemar p={seam_head['mcnemar_p']:.2f}, Wilcoxon partial p={seam_head['wilcoxon_partial_p']:.2f}); the +3 vs clean Pi low is also not reliable (McNemar p={base_head['mcnemar_p']:.2f}). No defensible quality signal at 3 reps.</div></section>

<section><div class='head'><div><h2>Difficulty split: old skill → seam skill</h2><p>The seam skill trades medium solves for easy solves, with hard flat. That is a least-valuable direction: easy solves were already near ceiling.</p></div></div><table><thead><tr>{th('Bucket')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}</tr></thead><tbody>{difficulty_rows(f'{OLD}__vs__{SEAM}')}</tbody></table></section>

<section><div class='head'><div><h2>CodeGraph command behavior: old vs seam</h2><p>The seam skill nudged the agent toward slightly more verification (<code>check</code> +{USEAM['command_counter'].get('check',0)-UOLD['command_counter'].get('check',0)}, <code>where</code> +{USEAM['command_counter'].get('where',0)-UOLD['command_counter'].get('where',0)}) but the overall workflow shape is unchanged.</p></div></div><table><thead><tr>{th('Subcommand')}{th('Old skill','num')}{th('Seam skill','num')}{th('Δ','num')}</tr></thead><tbody>{usage_compare_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Task flips: old skill → seam skill</h2><p>10 seam-only solves vs 9 old-only solves. The flips are near-threshold on both sides, with large symmetric partial swings (participle +0.31 rep2 / −0.31 rep0; pest −0.73 rep1), indicating noise rather than a systematic skill effect.</p></div></div><div class='grid2'><div><h3>Seam-only solves (old non-solve → seam solve)</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ partial','num')}{th('Δ tokens','num')}</tr></thead><tbody>{flip_rows(f'{OLD}__vs__{SEAM}','solve_gains')}</tbody></table></div><div><h3>Old-only solves (old solve → seam non-solve)</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ partial','num')}{th('Δ tokens','num')}</tr></thead><tbody>{flip_rows(f'{OLD}__vs__{SEAM}','solve_losses')}</tbody></table></div></div></section>

<section><div class='head'><div><h2>Difficulty summary across configs</h2><p>Both CodeGraph CLI variants sit between clean Pi low and the workflow prompt; both are well below clean Pi medium.</p></div></div><table><thead><tr>{th('Config')}{th('Bucket')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}</tr></thead><tbody>{group_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Solve-cost frontier</h2><p>Neither CodeGraph CLI variant is on the frontier. Workflow prompt low (35 solves, {money(S[WF]['median_cost'])}) dominates both, and clean Pi medium (50 solves) dominates both by a wide margin on solve count.</p></div></div><table><thead><tr>{th('Config')}{th('Solves','num')}{th('Median cost','num')}{th('Mean partial','num')}{th('Status')}{th('Dominated by')}</tr></thead><tbody>{pareto_rows()}</tbody></table></section>

<section><div class='head'><div><h2>Conclusion</h2></div></div><div class='grid2'><div class='callout bad'><strong>No skill-text effect:</strong> the seam-checkpoint / behavioral-seam / smaller-edit additions produced +1 solve (31 vs 30), not significant, with large symmetric churn. The two skills are effectively the same treatment at this sample size.</div><div class='callout good'><strong>Clean isolation:</strong> the run holds everything else constant, so this is real evidence that the over-engineering we previously attributed to CodeGraph is <em>not</em> fixed by prompt-level seam/invariant guidance. The problem is structural, not instructional.</div></div><div class='callout'><strong>Directional takeaway:</strong> the seam skill was slightly cheaper ({signed(seam_head['median_delta_cost'], dollar=True)} median cost, {signed(seam_head['median_delta_tokens'], integer=True)} median tokens) with no quality cost, so keeping the refined skill is harmless — but it does not rescue CodeGraph on this benchmark. Thinking budget (clean Pi medium, +19 solves) remains the only tested lever that expands the frontier.</div></section>

<div class='foot'>Generated from <code>analysis/codegraph-cli-seam-checkpoint-36v2/summary.json</code>. Run state: <code>results/_runs/gpt55-low-codegraph-cli-seam-checkpoint-36v2-r3-w24/</code>.</div>
</div></body></html>"""
(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")

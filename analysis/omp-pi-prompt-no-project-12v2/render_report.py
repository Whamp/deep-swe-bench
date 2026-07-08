#!/usr/bin/env python3
from __future__ import annotations

import html
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
DATA = json.loads((OUT / "summary.json").read_text())
S = DATA["summaries"]
P = DATA["pairs"]
LABELS = DATA["labels"]

CLEAN = "baseline"
BASH = "baseline-omp-pi-prompt-bash-only-no-project"
GREP = "baseline-omp-pi-prompt-grepglob-no-project"
AST = "baseline-omp-pi-prompt-ast-no-project"
PRIOR_BASH = "baseline-omp-pi-prompt-bash-only"
PRIOR_GREP = "baseline-omp-pi-prompt-grepglob"
PRIOR_AST = "baseline-omp-pi-prompt-ast"
DEF_BASH = "baseline-omp-bash-only"
DEF_GREP = "baseline-omp"
DEF_AST = "baseline-omp-ast"
NO_PROJECT = [BASH, GREP, AST]


def fmt_int(x):
    return f"{int(round(x)):,}"


def fmt_money(x, digits=3):
    return f"${x:,.{digits}f}"


def fmt_float(x, digits=4):
    return f"{x:.{digits}f}"


def pct(x, digits=1):
    return f"{100*x:.{digits}f}%"


def sign(x, digits=3, money=False, integer=False):
    prefix = "+" if x >= 0 else "−"
    val = abs(x)
    if money:
        body = fmt_money(val, digits)
    elif integer:
        body = fmt_int(val)
    else:
        body = f"{val:.{digits}f}"
    return prefix + body


def cls(x, higher=True):
    if abs(x) < 1e-12:
        return "neutral"
    good = x > 0 if higher else x < 0
    return "good" if good else "bad"


def pill(text, kind="neutral"):
    return f"<span class='pill {kind}'>{html.escape(text)}</span>"


def tag(text, kind="neutral"):
    return f"<span class='tag {kind}'>{html.escape(text)}</span>"


def td(x, cl=""):
    return f"<td class='{cl}'>{x}</td>"


def th(x, cl=""):
    return f"<th class='{cl}'>{x}</th>"


def tr(cells, cl=""):
    return f"<tr class='{cl}'>" + "".join(cells) + "</tr>"


def pval(x):
    return "—" if x is None else f"p={x:.3f}"


def config_short(c):
    return {
        CLEAN: "Pi",
        BASH: "OMP bash-only",
        GREP: "OMP grep/glob",
        AST: "OMP AST",
        PRIOR_BASH: "Prior bash-only",
        PRIOR_GREP: "Prior grep/glob",
        PRIOR_AST: "Prior AST",
        DEF_BASH: "Default bash-only",
        DEF_GREP: "Default grep/glob",
        DEF_AST: "Default AST",
    }.get(c, c)


def main_table(configs):
    rows = []
    for c in configs:
        s = S[c]
        rows.append(tr([
            td(f"<strong>{html.escape(config_short(c))}</strong><br><span class='muted t-mono'>{html.escape(c)}</span>"),
            td(f"{s['solves']}/36", "num"),
            td(fmt_float(s["mean_partial"]), "num"),
            td(fmt_money(s["median_cost"]), "num"),
            td(fmt_int(s["median_tokens"]), "num"),
            td(f"{s['median_turns']:.1f}", "num"),
            td(f"{s['median_tool_calls']:.1f}", "num"),
            td(fmt_money(s["total_cost"], 2), "num"),
        ]))
    return "\n".join(rows)


def pair_vs_pi_rows():
    rows = []
    for c in NO_PROJECT:
        p = P[f"{CLEAN}__vs__{c}"]
        rows.append(tr([
            td(f"<strong>{html.escape(config_short(c))}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(sign(p["solve_delta"], integer=True), f"num {cls(p['solve_delta'])}"),
            td(sign(p["mean_delta_partial"], 4), f"num {cls(p['mean_delta_partial'])}"),
            td(sign(p["median_delta_combined_cost_usd"], money=True), f"num {cls(p['median_delta_combined_cost_usd'], higher=False)}"),
            td(sign(p["median_delta_combined_total_tokens"], integer=True), f"num {cls(p['median_delta_combined_total_tokens'], higher=False)}"),
            td(f"{p['b_only']} / {p['a_only']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(rows)


def difficulty_rows():
    rows = []
    for c in NO_PROJECT:
        p = P[f"{CLEAN}__vs__{c}"]
        for bucket in ["hard", "medium", "easy"]:
            d = p["difficulty"][bucket]
            rows.append(tr([
                td(config_short(c)),
                td(bucket.title()),
                td(f"{d['a_solves']} → {d['b_solves']}", "num"),
                td(sign(d["solve_delta"], integer=True), f"num {cls(d['solve_delta'])}"),
                td(sign(d["mean_delta_partial"], 4), f"num {cls(d['mean_delta_partial'])}"),
                td(sign(d["median_delta_cost"], money=True), f"num {cls(d['median_delta_cost'], higher=False)}"),
            ]))
    return "\n".join(rows)


def provider_rows():
    rows = []
    for c in [CLEAN] + NO_PROJECT + [PRIOR_BASH]:
        s = S[c]
        tools = ", ".join(s["provider_tool_variants"][0]) if s.get("provider_tool_variants") else "—"
        roles = ", ".join(s["provider_input_role_variants"][0]) if s.get("provider_input_role_variants") else "—"
        rows.append(tr([
            td(f"<strong>{html.escape(config_short(c))}</strong>"),
            td(fmt_int(s["provider_instructions_chars_median"]), "num"),
            td(fmt_int(s["provider_tool_schema_bytes_median"]), "num"),
            td(fmt_int(s["provider_payload_bytes_median"]), "num"),
            td(html.escape(roles)),
            td(html.escape(tools)),
            td(str(s["provider_project_cells"]), "num"),
            td(str(s["provider_generate_image_cells"]), "num"),
        ]))
    return "\n".join(rows)


def strip_audit_rows():
    rows = []
    for c in NO_PROJECT:
        s = S[c]
        rows.append(tr([
            td(config_short(c)),
            td(f"{s['provider_project_cells']}/36", "num good"),
            td(f"{s['provider_generate_image_cells']}/36", "num good"),
            td(str(s["stripped_project_total"]), "num"),
            td(f"{s['stripped_generate_image_cells']}/36", "num"),
            td(f"{s['provider_input_role_variants']}", "t-mono"),
            td(f"{s['transient_json_cells']}", "num good"),
            td(f"{s['stderr_nonempty_cells']}", "num good"),
        ]))
    return "\n".join(rows)


def pause_rows():
    rows = []
    for a in DATA["pause_audit"]["quota_hit_cells"]:
        rows.append(tr([
            td(f"<strong>{html.escape(a['config'])}</strong><br><span class='muted'>{html.escape(a['task'])} · rep{a['rep']}</span>"),
            td(str(a["session_count"]), "num"),
            td("yes" if a["stale_usage_limit_sessions"] else "no", "num caution"),
            td("yes" if a["latest_has_usage_limit"] else "no", "num good"),
            td("yes" if a["usage_matches_latest_session"] else "no", "num good"),
            td(", ".join(a["provider_input_roles"]), "num"),
            td(", ".join(a["provider_tools"]), "t-mono"),
        ]))
    return "\n".join(rows)


def project_delta_rows():
    rows = []
    pairs = [(PRIOR_BASH, BASH), (PRIOR_GREP, GREP), (PRIOR_AST, AST)]
    for prior, clean in pairs:
        p = P[f"{prior}__vs__{clean}"]
        rows.append(tr([
            td(f"<strong>{config_short(prior).replace('Prior ', '')}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(sign(p["solve_delta"], integer=True), f"num {cls(p['solve_delta'])}"),
            td(sign(p["mean_delta_partial"], 4), f"num {cls(p['mean_delta_partial'])}"),
            td(sign(p["median_delta_combined_cost_usd"], money=True), f"num {cls(p['median_delta_combined_cost_usd'], higher=False)}"),
            td(sign(p["median_delta_combined_total_tokens"], integer=True), f"num {cls(p['median_delta_combined_total_tokens'], higher=False)}"),
            td(f"{p['b_only']} / {p['a_only']}", "num"),
            td(f"{pval(p['mcnemar_p'])}<br><span class='muted'>{pval(p['wilcoxon_partial_p'])} partial</span>", "num"),
        ]))
    return "\n".join(rows)


def default_rows():
    rows = []
    for default, clean in [(DEF_BASH, BASH), (DEF_GREP, GREP), (DEF_AST, AST)]:
        p = P[f"{default}__vs__{clean}"]
        rows.append(tr([
            td(f"<strong>{config_short(default).replace('Default ', '')}</strong>"),
            td(f"{p['a_solves']} → {p['b_solves']}", "num"),
            td(sign(p["solve_delta"], integer=True), f"num {cls(p['solve_delta'])}"),
            td(sign(p["mean_delta_partial"], 4), f"num {cls(p['mean_delta_partial'])}"),
            td(sign(p["median_delta_combined_cost_usd"], money=True), f"num {cls(p['median_delta_combined_cost_usd'], higher=False)}"),
            td(sign(p["median_delta_combined_total_tokens"], integer=True), f"num {cls(p['median_delta_combined_total_tokens'], higher=False)}"),
        ]))
    return "\n".join(rows)


def tool_rows():
    rows = []
    for c in [CLEAN] + NO_PROJECT + [DEF_BASH, DEF_GREP, DEF_AST]:
        counts = S[c]["tool_counts"]
        rows.append(tr([
            td(f"<strong>{config_short(c)}</strong>"),
            td(fmt_int(sum(counts.values())), "num"),
            td(fmt_int(counts.get("bash", 0)), "num"),
            td(fmt_int(counts.get("read", 0)), "num"),
            td(fmt_int(counts.get("edit", 0)), "num"),
            td(fmt_int(counts.get("grep", 0)), "num"),
            td(fmt_int(counts.get("glob", 0)), "num"),
            td(fmt_int(counts.get("ast_grep", 0)), "num"),
            td(fmt_int(counts.get("ast_edit", 0)), "num"),
        ]))
    return "\n".join(rows)


def solve_flip_rows(pair_name, gains=True):
    p = P[pair_name]
    items = p["solve_gains" if gains else "solve_losses"]
    rows = []
    for x in items:
        rows.append(tr([
            td(f"<strong>{html.escape(x['title'])}</strong><br><span class='muted t-mono'>{html.escape(x['task'])} · rep{x['rep']} · {x['difficulty']}</span>"),
            td(f"{x['a_partial']:.3f} → {x['b_partial']:.3f}", "num"),
            td(sign(x["delta_partial"], 3), f"num {cls(x['delta_partial'])}"),
        ]))
    return "\n".join(rows) or tr([td("None"), td("—", "num"), td("—", "num")])


def bar_chart():
    configs = [CLEAN] + NO_PROJECT + [DEF_BASH, DEF_GREP, DEF_AST]
    max_cost = max(S[c]["median_cost"] for c in configs)
    rows = []
    for c in configs:
        s = S[c]
        width = 100 * s["median_cost"] / max_cost
        rows.append(f"""
        <div class='bar-row'>
          <div class='bar-label'>{html.escape(config_short(c))}</div>
          <div class='bar-track'><div class='bar' style='width:{width:.1f}%'></div></div>
          <div class='bar-val'>{s['solves']}/36 · {fmt_money(s['median_cost'])}</div>
        </div>""")
    return "\n".join(rows)


html_doc = f"""<!doctype html>
<html lang='en'>
<head>
<meta charset='utf-8' />
<meta name='viewport' content='width=device-width, initial-scale=1' />
<title>OMP no-PROJECT rerun · DeepSWE report</title>
<style>
:root {{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue2:#1d3fb8;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--greenSoft:#e7f7ef;--redSoft:#fdeceb;--amberSoft:#fff5dd;--shadow:0 24px 60px rgba(14,30,62,.08);--radius:26px;}}
*{{box-sizing:border-box}}body{{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.12),transparent 28%),linear-gradient(180deg,#fbfdff,var(--bg));font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;color:var(--ink);line-height:1.52}}.wrap{{max-width:1320px;margin:0 auto;padding:28px 20px 48px}}.hero,section{{background:rgba(255,255,255,.94);border:1px solid var(--line);box-shadow:var(--shadow);border-radius:var(--radius)}}.hero{{padding:42px}}section{{padding:26px;margin-top:20px}}.eyebrow{{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue2);font-size:12px;font-weight:850;letter-spacing:.08em;text-transform:uppercase}}h1,h2,h3{{margin:0;line-height:1.08;letter-spacing:-.03em}}h1{{font-size:clamp(2.1rem,4.6vw,4rem);margin-top:14px;max-width:18ch}}h2{{font-size:clamp(1.35rem,2.2vw,2rem)}}h3{{font-size:1.05rem;margin:10px 0}}p{{color:var(--muted)}}.subtitle{{font-size:1.08rem;max-width:90ch;margin:14px 0 0}}.pillrow{{display:flex;gap:10px;flex-wrap:wrap;margin-top:22px}}.pill,.tag{{display:inline-flex;border-radius:999px;font-size:12px;font-weight:850;letter-spacing:.04em;text-transform:uppercase}}.pill{{padding:8px 13px;border:1px solid var(--line);background:#f8fafc;color:#31415d}}.pill.good,.tag.good{{background:var(--greenSoft);color:var(--green)}}.pill.bad,.tag.bad{{background:var(--redSoft);color:var(--red)}}.pill.caution,.tag.caution{{background:var(--amberSoft);color:var(--amber)}}.pill.neutral,.tag.neutral{{background:#eef3ff;color:var(--blue2)}}.tag{{padding:4px 9px}}.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:28px}}.stat{{background:#fff;border:1px solid var(--line);border-radius:18px;padding:16px;min-height:120px}}.stat .label{{display:block;font-size:12px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);font-weight:850;margin-bottom:9px}}.stat .value{{font-size:clamp(1.35rem,2vw,2rem);font-weight:900;letter-spacing:-.04em}}.stat .sub{{display:block;margin-top:8px;color:var(--muted);font-size:.9rem;font-weight:650}}.good{{color:var(--green)}}.bad{{color:var(--red)}}.caution{{color:var(--amber)}}.neutral{{color:var(--blue2)}}.grid-2{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:18px}}.grid-3{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}}.callout{{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;margin-top:14px}}.callout.good{{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}}.callout.bad{{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}}.callout.caution{{border-left-color:var(--amber);background:linear-gradient(90deg,#fff8e6,#fff)}}table{{width:100%;border-collapse:collapse;font-size:.92rem}}th,td{{text-align:left;vertical-align:top;padding:9px 10px;border-bottom:1px solid var(--line)}}th{{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:850}}td.num,th.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}tbody tr:hover{{background:#f8fafc}}.muted{{color:var(--muted)}}.t-mono,code{{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}}code{{background:#eef2ff;color:#25346c;border-radius:6px;padding:.12em .35em}}.section-head{{display:flex;justify-content:space-between;align-items:end;gap:14px;flex-wrap:wrap;margin-bottom:14px}}.section-head p{{margin:6px 0 0;max-width:80ch}}.bar-row{{display:grid;grid-template-columns:180px 1fr 140px;gap:12px;align-items:center;margin:10px 0}}.bar-label{{font-weight:750}}.bar-track{{height:14px;background:#edf2f7;border-radius:999px;overflow:hidden}}.bar{{height:100%;background:linear-gradient(90deg,var(--blue),#6f8cff);border-radius:999px}}.bar-val{{font-variant-numeric:tabular-nums;text-align:right;color:var(--muted)}}.foot{{text-align:center;color:var(--muted);font-size:.86rem;margin-top:24px}}@media(max-width:900px){{.stats,.grid-2,.grid-3{{grid-template-columns:1fr}}.hero{{padding:26px}}.bar-row{{grid-template-columns:1fr}}.bar-val{{text-align:left}}table{{font-size:.82rem}}th,td{{padding:7px 6px}}}}
</style>
</head>
<body><div class='wrap'>
<header class='hero'>
  <span class='eyebrow'>OMP no-PROJECT rerun · GPT-5.5 low · 12_v2 × 3 reps</span>
  <h1>The hidden OMP message was removed. The run is clean. The result got smaller.</h1>
  <p class='subtitle'>The rerun stripped OMP's provider-visible <code>PROJECT</code> developer message and the unintended <code>generate_image</code> tool from the three Pi-like OMP toolsets. The pause left three stale usage-limit session files, but the final trajectories, provider requests, patches, verifier outputs, and result usage came from clean retry sessions.</p>
  <div class='pillrow'>
    {pill('run completed: 108/108 result.json', 'good')}
    {pill('no PROJECT in 108/108 provider requests', 'good')}
    {pill('no generate_image in 108/108 provider requests', 'good')}
    {pill('all no-project OMP variants: 10/36 solves', 'neutral')}
    {pill('still much more expensive than Pi', 'caution')}
  </div>
  <div class='stats'>
    <div class='stat'><span class='label'>Clean Pi</span><span class='value'>{S[CLEAN]['solves']}/36</span><span class='sub'>{fmt_money(S[CLEAN]['median_cost'])} median cost</span></div>
    <div class='stat'><span class='label'>Best no-project OMP solves</span><span class='value'>10/36</span><span class='sub good'>+2 vs Pi, not decisive</span></div>
    <div class='stat'><span class='label'>Cheapest no-project OMP</span><span class='value'>{fmt_money(S[BASH]['median_cost'])}</span><span class='sub bad'>+{fmt_money(S[BASH]['median_cost']-S[CLEAN]['median_cost'])} vs Pi</span></div>
    <div class='stat'><span class='label'>No-project toolsets</span><span class='value'>tied</span><span class='sub'>bash, grep/glob, AST all 10 solves</span></div>
    <div class='stat'><span class='label'>Pause artifact risk</span><span class='value'>score-safe</span><span class='sub good'>3 stale failed sessions ignored by result usage</span></div>
  </div>
</header>

<section>
  <div class='section-head'><div><h2>Run-health audit</h2><p>The subscription pause did leave old failed session files, but not in the final scored trajectories.</p></div></div>
  <div class='grid-3'>
    <div class='callout good'><strong>Clean final provider requests.</strong> All 108 no-project cells had input roles <code>['user']</code>, expected tool lists, zero <code>PROJECT</code> messages, and zero <code>generate_image</code> tools.</div>
    <div class='callout good'><strong>Retry usage is clean.</strong> The three quota-hit cells each have one stale usage-limit session plus one clean retry session. <code>result.json</code> usage matches the latest clean root session in all 108 cells.</div>
    <div class='callout caution'><strong>Artifact caveat.</strong> Ad hoc analyses must not sum every <code>session/*.jsonl</code> in those three cells. Use latest-root semantics or <code>result.json</code>. The stale files are artifact noise, not score evidence.</div>
  </div>
  <table><thead><tr>{th('Quota-hit cell')}{th('sessions','num')}{th('stale usage-limit','num')}{th('latest has usage limit','num')}{th('usage matches latest','num')}{th('roles','num')}{th('provider tools')}</tr></thead><tbody>{pause_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Headline result</h2><p>The no-project OMP variants all beat clean Pi by two solves on this small slice, but they paid a large cost/token premium and none cleared a statistical bar.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Solves','num')}{th('Mean partial','num')}{th('Median cost','num')}{th('Median tokens','num')}{th('Median turns','num')}{th('Median tools','num')}{th('Total cost','num')}</tr></thead><tbody>{main_table([CLEAN] + NO_PROJECT)}</tbody></table>
  <div class='callout caution'><strong>Interpretation:</strong> this is a directional result, not proof that OMP is better. The cleanest claim is: after removing the hidden OMP runtime message, OMP still bought a small solve-rate lift on 12_v2, but at roughly 1.6–1.8× median cost and 2.3–2.5× median tokens versus clean Pi.</div>
</section>

<section>
  <div class='section-head'><div><h2>Paired against clean Pi</h2><p>All three no-project OMP configs have the same solve count. Grep/glob has the best mean partial; bash-only is cheapest.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('OMP-only / Pi-only solves','num')}{th('Tests','num')}</tr></thead><tbody>{pair_vs_pi_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Difficulty split vs clean Pi</h2><p>The solve gains are not all from easy tasks. Grep/glob and AST trade one easy solve away for more hard/medium solves.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Bucket')}{th('Solves','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}</tr></thead><tbody>{difficulty_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>What the hidden PROJECT message changed</h2><p>Removing the hidden OMP developer/runtime message did not have one uniform effect. It made grep/glob and AST better, but it erased the earlier bash-only spike.</p></div></div>
  <table><thead><tr>{th('Toolset')}{th('Solves, prior → clean','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}{th('Clean-only / prior-only solves','num')}{th('Tests','num')}</tr></thead><tbody>{project_delta_rows()}</tbody></table>
  <div class='callout bad'><strong>Old conclusion to discard:</strong> “OMP Pi-like bash-only solved 13/36” depended on a provider-visible <code>PROJECT</code> developer message and an unintended <code>generate_image</code> tool. The clean bash-only number is 10/36.</div>
</section>

<section>
  <div class='section-head'><div><h2>Provider-visible surface</h2><p>The rerun achieved instruction-message cleanup, but not tool-schema parity. OMP's tool definitions remain much larger than Pi's.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Instr chars','num')}{th('Tool schema bytes','num')}{th('Provider request bytes','num')}{th('Input roles')}{th('Tools')}{th('PROJECT cells','num')}{th('generate_image cells','num')}</tr></thead><tbody>{provider_rows()}</tbody></table>
  <div class='callout'><strong>Key mechanism left standing:</strong> OMP bash-only's instruction text is near Pi's median length ({fmt_int(S[BASH]['provider_instructions_chars_median'])} vs {fmt_int(S[CLEAN]['provider_instructions_chars_median'])} chars), but its tool schemas are about 6× larger ({fmt_int(S[BASH]['provider_tool_schema_bytes_median'])} vs {fmt_int(S[CLEAN]['provider_tool_schema_bytes_median'])} bytes). Tool definitions, not the top-level prompt, now dominate the prompt-surface gap.</div>
</section>

<section>
  <div class='section-head'><div><h2>Strip-extension validation</h2><p>The instrumentation did what it was supposed to do.</p></div></div>
  <table><thead><tr>{th('Config')}{th('PROJECT cells','num')}{th('generate_image cells','num')}{th('PROJECT strips','num')}{th('cells stripping generate_image','num')}{th('input role variants')}{th('transient json','num')}{th('stderr nonempty','num')}</tr></thead><tbody>{strip_audit_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Tool behavior</h2><p>Removing the PROJECT message did not make OMP behave like Pi. OMP still reads more, edits more often, and carries heavier tool contracts.</p></div></div>
  <table><thead><tr>{th('Config')}{th('Total tool starts','num')}{th('bash','num')}{th('read','num')}{th('edit','num')}{th('grep','num')}{th('glob','num')}{th('ast_grep','num')}{th('ast_edit','num')}</tr></thead><tbody>{tool_rows()}</tbody></table>
  <div class='callout caution'><strong>AST finding:</strong> the AST config exposed <code>ast_grep</code> and <code>ast_edit</code>, but GPT-5.5 low used <code>ast_grep</code> only 10 times across 36 cells and never used <code>ast_edit</code>. AST tools did not buy more solves than the simpler OMP configs.</div>
</section>

<section>
  <div class='section-head'><div><h2>Default OMP vs Pi-like no-project OMP</h2><p>The Pi-like prompt plus stripped runtime message is better than default OMP on this slice.</p></div></div>
  <table><thead><tr>{th('Toolset')}{th('Solves, default → Pi-like no-project','num')}{th('Δ solves','num')}{th('Δ partial','num')}{th('Median Δ cost','num')}{th('Median Δ tokens','num')}</tr></thead><tbody>{default_rows()}</tbody></table>
</section>

<section>
  <div class='section-head'><div><h2>Solve-cost view</h2><p>Clean Pi is still cheapest. OMP bash-only no-project is the only no-project OMP row on the solve-cost frontier because it ties the other OMP variants on solves and costs less.</p></div></div>
  <div class='bar-wrap'>{bar_chart()}</div>
  <div class='callout'><strong>Frontier read:</strong> on 12_v2, clean Pi is the low-cost anchor. OMP bash-only no-project buys +2 solves for +{fmt_money(S[BASH]['median_cost']-S[CLEAN]['median_cost'])} median cost. Grep/glob and AST may be interesting for partial quality, but they do not improve the solve-cost frontier over bash-only.</div>
</section>

<section>
  <div class='section-head'><div><h2>Concrete solve flips vs clean Pi</h2><p>Representative flips show why this is noisy: some gains are near-threshold conversions, and some losses are repeated on the same task family.</p></div></div>
  <div class='grid-3'>
    <div><h3>Bash-only gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{BASH}', True)}</tbody></table><h3>Bash-only losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{BASH}', False)}</tbody></table></div>
    <div><h3>Grep/glob gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{GREP}', True)}</tbody></table><h3>Grep/glob losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{GREP}', False)}</tbody></table></div>
    <div><h3>AST gains</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{AST}', True)}</tbody></table><h3>AST losses</h3><table><thead><tr>{th('Task')}{th('Partial','num')}{th('Δ','num')}</tr></thead><tbody>{solve_flip_rows(f'{CLEAN}__vs__{AST}', False)}</tbody></table></div>
  </div>
</section>

<section>
  <div class='section-head'><div><h2>Conclusion</h2><p>The rerun answers the immediate question and changes the OMP story.</p></div></div>
  <div class='grid-2'>
    <div class='callout good'><strong>Use this rerun as the clean OMP Pi-like toolset result.</strong> It removed the hidden developer message and unintended image tool. The pause did not corrupt scored trajectories.</div>
    <div class='callout caution'><strong>Do not over-read 12_v2.</strong> OMP no-project is directionally above clean Pi on solves, but only by +2/36 with high overhead and weak tests. It deserves a 36_v2 follow-up only if the cost premium is acceptable.</div>
  </div>
  <div class='callout'><strong>Recommended next harness fix:</strong> on transient retry, archive or clear stale <code>session/</code> files and record the selected latest root session path in <code>result.json</code>. Current scoring and usage are safe, but stale failed session files can confuse future forensic scripts.</div>
</section>

<div class='foot'>Generated from <code>analysis/omp-pi-prompt-no-project-12v2/summary.json</code>. Result paths under <code>results/gpt-5.5/low/</code>. Run state: <code>results/_runs/omp-pi-prompt-toolsets-no-project-12v2-r3-w24/</code>.</div>
</div></body></html>
"""

(OUT / "index.html").write_text(html_doc)
print(OUT / "index.html")

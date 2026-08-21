#!/usr/bin/env python3
"""Build the gguf-tp vs llama.cpp vs OpenRouter 12_v2 serving-stack comparison report.

Reads every number from on-disk result.json artifacts (read-only), asserts the
gguf-tp ground truth, writes comparison.json and index.html next to this script.
"""
import datetime
import json
import pathlib

ROOT = pathlib.Path("/home/will/evals/deep-swe-bench")
HERE = pathlib.Path(__file__).parent

TASKS = [
    "adaptix-name-mapping-aliases",
    "claude-code-by-agents-recursive-delegation",
    "dateutil-rfc5545-timezone-interop",
    "go-critic-doc-link-checker",
    "goreleaser-retry-publish-auditing",
    "langchain-request-coalescing",
    "mobly-grouped-test-barriers",
    "obsidian-linter-link-format-conversion",
    "participle-grammar-conflict-analysis",
    "sql-formatter-bigquery-pipe-formatting",
    "superjson-error-stack-serialization",
    "tengo-callable-instance-isolation",
]

SYSTEMS = {
    "gguf-tp": {
        "label": "vLLM GGUF-TP (local)",
        "short": "GGUF-TP",
        "path": "results/_throughput/deepseek-v4-gguf-tp/max/workers-2/deepseek-v4-flash-0731-gguf-tp/max/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.1.0/{task}/rep0/result.json",
        "serving": "local vLLM, 4\u00d7RTX 3090 TP4, server60:8034, 148k ctx",
        "quant": "Antirez GGUF mixed IQ2_XXS/Q2_K/Q8_0",
        "config": "baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.1.0",
    },
    "llamacpp-max": {
        "label": "llama.cpp IQ2_XXS (local)",
        "short": "llama.cpp",
        "path": "results/deepseek-v4-flash-0731-q8-fast-prefill/max/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/{task}/rep0/result.json",
        "serving": "local llama.cpp, IQ2_XXS, q8-fast-prefill leaf",
        "quant": "IQ2_XXS GGUF",
        "config": "baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0",
    },
    "openrouter-max": {
        "label": "OpenRouter hosted API",
        "short": "OpenRouter",
        "path": "results/deepseek-v4-flash-0731/max/baseline-openrouter-deepseek-v4-flash-0731@1.0.0/{task}/rep0/result.json",
        "serving": "hosted OpenRouter API (full precision)",
        "quant": "hosted full-precision",
        "config": "baseline-openrouter-deepseek-v4-flash-0731@1.0.0",
    },
    "llamacpp-low": {
        "label": "llama.cpp IQ2_XXS \u00b7 low thinking (secondary)",
        "short": "llama.cpp low",
        "path": "results/deepseek-v4-flash-0731-q8-fast-prefill/low/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0/{task}/rep0/result.json",
        "serving": "local llama.cpp, IQ2_XXS, low thinking",
        "quant": "IQ2_XXS GGUF",
        "config": "baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0",
    },
}

FIELDS = [
    "reward_binary", "reward_partial", "reward_unverified",
    "f2p", "f2p_passed", "f2p_total", "p2p", "p2p_passed", "p2p_total",
    "agent_wall_s", "combined_total_tokens", "input_tokens", "output_tokens",
    "cache_read_tokens", "turns", "agent_timed_out", "agent_exit",
    "verifier_exit", "model", "subject_version", "language", "category",
    "patch_bytes",
]


def load():
    data = {}
    for name, meta in SYSTEMS.items():
        rows = []
        for t in TASKS:
            p = ROOT / meta["path"].format(task=t)
            d = json.loads(p.read_text())
            row = {"task": t, "source": str(p)}
            for k in FIELDS:
                row[k] = d.get(k)
            rows.append(row)
        data[name] = rows
    return data


def agg(rows):
    solves = sum(r["reward_binary"] for r in rows)
    partials = [r["reward_partial"] for r in rows if r["reward_partial"] is not None]
    f2ps = [r["f2p"] for r in rows if r["f2p"] is not None]
    p2ps = [r["p2p"] for r in rows if r["p2p"] is not None]
    wall = sum(r["agent_wall_s"] for r in rows)
    tok = sum(r["combined_total_tokens"] for r in rows)
    out_tok = sum(r["output_tokens"] for r in rows)
    turns = sum(r["turns"] for r in rows)
    return {
        "solves": solves, "n": len(rows),
        "mean_partial": sum(partials) / len(partials),
        "mean_f2p": sum(f2ps) / len(f2ps), "f2p_n": len(f2ps),
        "mean_p2p": sum(p2ps) / len(p2ps), "p2p_n": len(p2ps),
        "wall_s": wall, "wall_h": wall / 3600,
        "total_tokens": tok, "output_tokens": out_tok, "turns": turns,
    }


def main():
    data = load()
    A = {name: agg(rows) for name, rows in data.items()}

    # ---- ground-truth assertions (gguf-tp) ----
    g = A["gguf-tp"]
    GT_SOLVES = {
        "adaptix-name-mapping-aliases": 1, "claude-code-by-agents-recursive-delegation": 1,
        "dateutil-rfc5545-timezone-interop": 0, "go-critic-doc-link-checker": 0,
        "goreleaser-retry-publish-auditing": 1, "langchain-request-coalescing": 0,
        "mobly-grouped-test-barriers": 1, "obsidian-linter-link-format-conversion": 1,
        "participle-grammar-conflict-analysis": 0, "sql-formatter-bigquery-pipe-formatting": 1,
        "superjson-error-stack-serialization": 1, "tengo-callable-instance-isolation": 0,
    }
    for r in data["gguf-tp"]:
        assert r["reward_binary"] == GT_SOLVES[r["task"]], f"solve mismatch {r['task']}"
    assert g["solves"] == 7, g["solves"]
    assert abs(g["mean_partial"] - 0.9066) < 5e-5, g["mean_partial"]
    assert abs(g["mean_f2p"] - 0.9624) < 5e-5, g["mean_f2p"]
    assert abs(g["wall_h"] - 8.71) < 0.01, g["wall_h"]  # 31,329.6s = 8.7027h
    assert abs(g["total_tokens"] / 1e6 - 142.6) < 0.05, g["total_tokens"]

    # gguf mean partial excluding the ungraded langchain cell (verifier timeout)
    g_parts = [r["reward_partial"] for r in data["gguf-tp"] if r["task"] != "langchain-request-coalescing"]
    g_mean_partial_excl = sum(g_parts) / len(g_parts)

    comparison = {
        "generated": datetime.datetime.now(datetime.UTC).isoformat(),
        "subset": "12_v2", "reps": "rep0", "thinking": "max (llamacpp-low row excepted)",
        "systems": {name: {**meta, "path": meta["path"]} for name, meta in SYSTEMS.items()},
        "aggregates": A,
        "gguf_tp_mean_partial_excl_verifier_timeout": g_mean_partial_excl,
        "cells": data,
    }
    (HERE / "comparison.json").write_text(json.dumps(comparison, indent=1, default=str))

    html = render(data, A, g_mean_partial_excl)
    (HERE / "index.html").write_text(html)
    print("wrote", HERE / "comparison.json")
    print("wrote", HERE / "index.html", f"({len(html)} bytes)")
    for name, a in A.items():
        print(f"{name:14s} {a['solves']}/{a['n']}  partial {a['mean_partial']:.4f}  f2p {a['mean_f2p']:.4f}  wall {a['wall_h']:.2f}h  tok {a['total_tokens']/1e6:.1f}M")


def pct(x, nd=2):
    return f"{x * 100:.{nd}f}%"


def fmt_tok(t):
    return f"{t / 1e6:.2f}M" if t >= 1e6 else f"{t / 1e3:.0f}K"


def fmt_wall(s):
    return f"{s / 60:.1f}m" if s < 3600 else f"{s / 3600:.2f}h"


def frac(r, key):
    p, t = r.get(f"{key}_passed"), r.get(f"{key}_total")
    return f"{p}/{t}" if p is not None else "\u2014"


def cell_tag(r):
    if r["reward_binary"] == 1:
        return '<span class="tag good">solved</span>'
    if r.get("reward_unverified") or r.get("verifier_exit") == "timeout":
        return '<span class="tag caution">ungraded</span>'
    return '<span class="tag neutral">missed</span>'


def cell_html(r):
    bits = [cell_tag(r)]
    detail = f'partial {pct(r["reward_partial"])} \u00b7 F2P {frac(r, "f2p")} \u00b7 P2P {frac(r, "p2p")} \u00b7 {fmt_wall(r["agent_wall_s"])} \u00b7 {fmt_tok(r["combined_total_tokens"])}'
    note = ""
    if r.get("verifier_exit") == "timeout":
        note = '<br><span class="tiny" style="color:var(--amber);font-weight:700">verifier timeout \u2014 59.6KB patch never graded</span>'
    elif r.get("agent_timed_out"):
        note = '<br><span class="tiny" style="color:var(--amber);font-weight:700">agent hit 3h cap \u2014 trending 46/50 F2P</span>'
    return f'{bits[0]}<br><span class="tiny muted">{detail}</span>{note}'


def render(data, A, g_excl):
    rows_g, rows_l, rows_o = data["gguf-tp"], data["llamacpp-max"], data["openrouter-max"]

    # ----- per-task table rows -----
    task_rows = []
    n_discord = 0
    for i, t in enumerate(TASKS):
        g, l, o = rows_g[i], rows_l[i], rows_o[i]
        s = (g["reward_binary"], l["reward_binary"], o["reward_binary"])
        solvers = [name for name, v in zip(["GGUF-TP", "llama.cpp", "OpenRouter"], s) if v == 1]
        if s == (1, 1, 1):
            agree = '<span class="tag good">all solve</span>'
        elif s == (0, 0, 0):
            agree = '<span class="tag neutral">all miss</span>'
        else:
            n_discord += 1
            if len(solvers) == 1:
                agree = f'<span class="tag caution">flip</span><br><span class="tiny muted">{solvers[0]} only</span>'
            else:
                misser = next(name for name, v in zip(["GGUF-TP", "llama.cpp", "OpenRouter"], s) if v == 0)
                agree = f'<span class="tag caution">flip</span><br><span class="tiny muted">{misser} misses</span>'
        lang = g["language"]
        task_rows.append(
            f'<tr><td><strong>{t}</strong><br><span class="muted tiny">{lang} \u00b7 {g["category"]}</span></td>'
            f"<td>{cell_html(g)}</td><td>{cell_html(l)}</td><td>{cell_html(o)}</td><td>{agree}</td></tr>"
        )
    task_rows_html = "\n".join(task_rows)

    # ----- churn table (discordant tasks) -----
    churn_rows = []
    for i, t in enumerate(TASKS):
        g, l, o = rows_g[i], rows_l[i], rows_o[i]
        s = (g["reward_binary"], l["reward_binary"], o["reward_binary"])
        if s in ((1, 1, 1), (0, 0, 0)):
            continue
        who = []
        for nm, r in zip(["GGUF-TP", "llama.cpp", "OpenRouter"], (g, l, o)):
            mark = "\u2713" if r["reward_binary"] == 1 else "\u2717"
            who.append(f"{nm} {mark}")
        sep = "\u00b7"
        churn_rows.append(
            f'<tr><td><strong>{t}</strong></td><td>{f" {sep} ".join(who)}</td>'
            f'<td class="num">{pct(g["reward_partial"])}</td><td class="num">{pct(l["reward_partial"])}</td><td class="num">{pct(o["reward_partial"])}</td>'
            f"<td>{CHURN_NOTES[t]}</td></tr>"
        )
    churn_html = "\n".join(churn_rows)

    # ----- efficiency bars -----
    wall_max = max(a["wall_h"] for a in A.values())
    tok_max = max(a["total_tokens"] for a in A.values())
    bar_wall = "".join(
        BAR_ROW.format(label=BAR_LABELS[k], width=a["wall_h"] / wall_max * 100, cls=BAR_CLS[k],
                       val=f'{a["wall_h"]:.2f}h')
        for k, a in A.items()
    )
    bar_tok = "".join(
        BAR_ROW.format(label=BAR_LABELS[k], width=a["total_tokens"] / tok_max * 100, cls=BAR_CLS[k],
                       val=f'{a["total_tokens"] / 1e6:.1f}M')
        for k, a in A.items()
    )
    bar_out = "".join(
        BAR_ROW.format(label=BAR_LABELS[k], width=a["output_tokens"] / max(x["output_tokens"] for x in A.values()) * 100,
                       cls=BAR_CLS[k], val=f'{a["output_tokens"] / 1e6:.2f}M')
        for k, a in A.items()
    )

    gen = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    body = BODY_TEMPLATE
    repl = {
        "@@GEN@@": gen,
        "@@TASK_ROWS@@": task_rows_html,
        "@@CHURN_ROWS@@": churn_html,
        "@@N_DISCORD@@": str(n_discord),
        "@@BAR_WALL@@": bar_wall,
        "@@BAR_TOK@@": bar_tok,
        "@@BAR_OUT@@": bar_out,
        "@@G_EXCL@@": f"{g_excl:.4f}",
        "@@G_EXCL_PCT@@": pct(g_excl),
    }
    for k, v in repl.items():
        body = body.replace(k, v)
    return CSS + body


BAR_LABELS = {"gguf-tp": "GGUF-TP", "llamacpp-max": "llama.cpp max", "openrouter-max": "OpenRouter", "llamacpp-low": "llama.cpp low"}
BAR_CLS = {"gguf-tp": "fill-gguf", "llamacpp-max": "fill-llama", "openrouter-max": "fill-or", "llamacpp-low": "fill-low"}
BAR_ROW = '<div class="bar-row"><div class="bar-label">{label}</div><div class="bar-track"><div class="bar-fill {cls}" style="width:{width:.1f}%"></div></div><div class="bar-val">{val}</div></div>'

CHURN_NOTES = {
    "claude-code-by-agents-recursive-delegation": "Both local stacks solve it; OpenRouter posts its worst cell of the comparison (F2P 2/7).",
    "dateutil-rfc5545-timezone-interop": "llama.cpp passes 67/67. GGUF-TP and OpenRouter land identical near-misses (66/67, partial 0.9995).",
    "go-critic-doc-link-checker": "llama.cpp passes 3/3. GGUF-TP and OpenRouter miss the same single F2P test (2/3, partial 0.8947).",
    "langchain-request-coalescing": "OpenRouter-only solve. GGUF-TP cell ungraded (verifier timeout, 59.6KB patch); llama.cpp agent hit the 3h cap at 46/50 F2P.",
    "obsidian-linter-link-format-conversion": "GGUF-TP-only solve (60/60). llama.cpp misses one test (59/60), OpenRouter five (55/60).",
    "sql-formatter-bigquery-pipe-formatting": "GGUF-TP and OpenRouter solve; llama.cpp near-misses at 24/26 F2P (partial 0.9997).",
    "superjson-error-stack-serialization": "GGUF-TP-only solve (80/80). llama.cpp 78/80; OpenRouter 74/80 plus the comparison's only P2P dip (57/58).",
    "tengo-callable-instance-isolation": "OpenRouter-only solve (23/23). GGUF-TP misses one test (22/23), llama.cpp three (20/23).",
}

CSS = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><link rel="icon" href="data:,">
<title>DeepSeek V4 Flash 0731 \u00b7 three serving stacks \u00b7 12_v2</title>
<style>
:root{--bg:#f4f7fb;--surface:#fff;--surface-2:#f8fafc;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--blue-2:#1d3fb8;--green:#178a5b;--green-soft:#e7f7ef;--red:#d0473f;--red-soft:#fdeceb;--amber:#c58a00;--amber-soft:#fff4d8;--shadow:0 24px 60px rgba(14,30,62,.08);--shadow-sm:0 10px 30px rgba(14,30,62,.06);--radius:24px;--max:1360px}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top left,rgba(51,93,255,.10),transparent 30%),radial-gradient(circle at top right,rgba(23,138,91,.08),transparent 24%),linear-gradient(180deg,#f8fbff 0%,var(--bg) 100%);color:var(--ink);font-family:Inter,system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.55;-webkit-font-smoothing:antialiased}
code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:.9em;background:#eef2ff;color:#24346f;padding:.12em .35em;border-radius:6px}
.wrap{max-width:var(--max);margin:0 auto;padding:28px 20px 44px}
.hero,section{background:rgba(255,255,255,.9);border:1px solid rgba(217,225,236,.9);border-radius:var(--radius);box-shadow:var(--shadow)}
.hero{padding:clamp(24px,4vw,40px)}
section{margin-top:20px;padding:clamp(18px,3vw,28px)}
h1,h2,h3{margin:0;line-height:1.08;letter-spacing:-.03em}
h1{font-size:clamp(2rem,4.2vw,3.6rem);margin-top:14px;max-width:24ch}
h2{font-size:clamp(1.35rem,2.2vw,1.9rem)}
.eyebrow{display:inline-flex;padding:8px 12px;border-radius:999px;background:#eef3ff;color:var(--blue-2);font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}
.subtitle{max-width:92ch;color:var(--muted);font-size:1.05rem;margin:14px 0 0}
.muted{color:var(--muted)}.tiny{font-size:.78rem}
.pills{display:flex;gap:10px;flex-wrap:wrap;margin-top:20px}
.pill,.tag{display:inline-flex;padding:7px 12px;border-radius:999px;font-size:12px;font-weight:800;letter-spacing:.03em}
.pill.neutral,.tag.neutral{background:#eef3ff;color:var(--blue-2)}
.pill.good,.tag.good{background:var(--green-soft);color:var(--green)}
.pill.caution,.tag.caution{background:var(--amber-soft);color:#8b6200}
.pill.bad,.tag.bad{background:var(--red-soft);color:var(--red)}
.stats{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin-top:24px}
.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:var(--shadow-sm)}
.stat .label{display:block;color:var(--muted);font-size:11px;font-weight:800;text-transform:uppercase;letter-spacing:.07em}
.stat .value{display:block;font-size:clamp(1.35rem,2vw,1.8rem);font-weight:900;margin-top:8px;letter-spacing:-.03em}
.stat .sub{display:block;color:var(--muted);font-size:.82rem;margin-top:6px;font-weight:600}
.head{display:flex;justify-content:space-between;gap:20px;align-items:end;flex-wrap:wrap;margin-bottom:16px}
.head p{margin:6px 0 0;max-width:88ch;color:var(--muted)}
.table-wrap{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:.93rem}
th,td{text-align:left;padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top}
th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:800;white-space:nowrap}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
tbody tr:hover{background:var(--surface-2)}
.callout{border-left:5px solid var(--blue);background:linear-gradient(90deg,#f4f7ff,#fff);border-radius:14px;padding:14px 16px;color:#22314d;margin-top:14px}
.callout.bad{border-left-color:var(--red);background:linear-gradient(90deg,#fff5f4,#fff)}
.callout.good{border-left-color:var(--green);background:linear-gradient(90deg,#f2fbf6,#fff)}
.callout.caution{border-left-color:var(--amber);background:linear-gradient(90deg,#fffaf0,#fff)}
.callout strong{color:var(--blue-2)}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}
.card{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:18px;box-shadow:var(--shadow-sm)}
.card h3{font-size:1.02rem;margin-bottom:8px}
.card p{margin:0;color:#33425e;font-size:.93rem}
.bar-list{display:grid;gap:12px;margin-top:8px}
.bar-row{display:grid;grid-template-columns:130px 1fr 84px;gap:14px;align-items:center}
.bar-label{font-weight:800;color:#22314d;font-size:.88rem}
.bar-track{position:relative;height:18px;border-radius:999px;background:#edf2f7;overflow:hidden;border:1px solid #dde5ef}
.bar-fill{position:absolute;inset:0 auto 0 0;border-radius:inherit}
.fill-gguf{background:linear-gradient(90deg,#3a73ff,#1d3fb8)}
.fill-llama{background:linear-gradient(90deg,#9aa9bf,#7d8ba1)}
.fill-or{background:linear-gradient(90deg,#29b36f,#178a5b)}
.fill-low{background:linear-gradient(90deg,#e3b34c,#c58a00)}
.bar-val{font-size:.85rem;color:var(--muted);font-weight:700;text-align:right;font-variant-numeric:tabular-nums}
.legend{display:flex;gap:18px;flex-wrap:wrap;margin:4px 0 12px;font-size:.85rem;color:var(--muted);font-weight:700}
.legend span{display:inline-flex;align-items:center;gap:7px}
.dot{width:12px;height:12px;border-radius:4px;display:inline-block}
.foot{margin-top:26px;color:var(--muted);font-size:.85rem;text-align:center}
.up{color:var(--green);font-weight:800}.down{color:var(--red);font-weight:800}.warn{color:var(--amber);font-weight:800}
@media(max-width:1000px){.stats{grid-template-columns:repeat(2,minmax(0,1fr))}.grid{grid-template-columns:1fr}.bar-row{grid-template-columns:96px 1fr 70px}}
</style></head><body><div class="wrap">
"""

BODY_TEMPLATE = """
<header class="hero">
<span class="eyebrow">Serving-stack comparison \u00b7 DeepSWE 12_v2 \u00b7 12 tasks \u00d7 1 rep \u00b7 max thinking</span>
<h1>Same weights, three serving stacks: 7, 6, and 6 strict solves \u2014 and @@N_DISCORD@@ of 12 tasks disagree.</h1>
<p class="subtitle">One base model \u2014 <strong>DeepSeek V4 Flash 0731</strong> \u2014 served three ways: a new local <strong>vLLM GGUF tensor-parallel</strong> stack (4\u00d7RTX 3090, 148k context), local <strong>llama.cpp IQ2_XXS</strong>, and the <strong>OpenRouter hosted full-precision API</strong>. Matched task/rep cells (rep0) on the 12_v2 subset. This is a capability-shape / serving-stack contrast, not a quantization-causal claim: quantization, serving engine, context window, and Pi subject version all differ across the columns.</p>
<div class="pills">
<span class="pill good">vLLM GGUF-TP \u00b7 7/12 solves</span>
<span class="pill neutral">llama.cpp IQ2_XXS \u00b7 6/12</span>
<span class="pill neutral">OpenRouter FP \u00b7 6/12</span>
<span class="pill caution">@@N_DISCORD@@/12 tasks discordant</span>
<span class="pill caution">GGUF-TP: run at concurrency 1</span>
</div>
<div class="stats">
<div class="stat"><span class="label">Strict solves \u00b7 GGUF-TP</span><span class="value">7/12</span><span class="sub">llama.cpp 6/12 \u00b7 OpenRouter 6/12</span></div>
<div class="stat"><span class="label">Mean partial \u00b7 GGUF-TP</span><span class="value">0.9066</span><span class="sub">@@G_EXCL@@ excl. the ungraded verifier-timeout cell</span></div>
<div class="stat"><span class="label">Mean F2P \u00b7 GGUF-TP</span><span class="value">0.9624</span><span class="sub">llama.cpp 0.8911 \u00b7 OpenRouter 0.8973</span></div>
<div class="stat"><span class="label">Agent wall \u00b7 GGUF-TP</span><span class="value">8.70h</span><span class="sub">llama.cpp 19.85h \u00b7 OpenRouter 4.54h</span></div>
<div class="stat"><span class="label">Total tokens \u00b7 GGUF-TP</span><span class="value">142.6M</span><span class="sub">llama.cpp 224.8M \u00b7 OpenRouter 161.3M</span></div>
</div></header>

<section><div class="head"><div><h2>Headline metrics</h2><p>All numbers read from on-disk <code>result.json</code> artifacts (rep0, 12_v2). Mean F2P/P2P are computed over cells where grading is defined (GGUF-TP n=11: its LangChain cell was never graded). Total tokens are the harness <code>combined_total_tokens</code> (input + output + cache reads). The llama.cpp low-thinking row is a complete secondary reference, not part of the max-thinking comparison.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>System</th><th>Serving / quantization</th><th class="num">Strict solves</th><th class="num">Mean partial</th><th class="num">Mean F2P</th><th class="num">Mean P2P</th><th class="num">Agent wall</th><th class="num">Total tokens</th><th class="num">Output tokens</th><th>Verdict</th></tr></thead><tbody>
<tr><td><strong>vLLM GGUF-TP</strong> <span class="tag good">new</span><br><span class="muted tiny">baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.1.0</span></td><td>local vLLM TP4 \u00d7 3090, 148k ctx<br><span class="muted tiny">mixed IQ2_XXS/Q2_K/Q8_0 GGUF</span></td><td class="num"><strong>7/12</strong></td><td class="num">0.9066 <span class="muted tiny">(@@G_EXCL@@ excl.)</span></td><td class="num">0.9624</td><td class="num">0.9943</td><td class="num">8.70h</td><td class="num">142.6M</td><td class="num">1.51M</td><td><span class="tag good">most solves, cheapest local</span></td></tr>
<tr><td><strong>llama.cpp IQ2_XXS</strong><br><span class="muted tiny">baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0</span></td><td>local llama.cpp, q8-fast-prefill leaf<br><span class="muted tiny">IQ2_XXS GGUF</span></td><td class="num"><strong>6/12</strong></td><td class="num">0.9657</td><td class="num">0.8911</td><td class="num">1.0000</td><td class="num">19.85h</td><td class="num">224.8M</td><td class="num">1.83M</td><td><span class="tag neutral">two unique solves; slowest</span></td></tr>
<tr><td><strong>OpenRouter hosted</strong><br><span class="muted tiny">baseline-openrouter-deepseek-v4-flash-0731@1.0.0</span></td><td>hosted API, full precision<br><span class="muted tiny">$3.18 total for the 12 cells</span></td><td class="num"><strong>6/12</strong></td><td class="num">0.9761</td><td class="num">0.8973</td><td class="num">0.9934</td><td class="num">4.54h</td><td class="num">161.3M</td><td class="num">1.32M</td><td><span class="tag neutral">highest partial, fastest</span></td></tr>
<tr><td><strong>llama.cpp IQ2_XXS \u00b7 low</strong> <span class="tag caution">secondary</span><br><span class="muted tiny">same config, low thinking</span></td><td>local llama.cpp<br><span class="muted tiny">IQ2_XXS GGUF</span></td><td class="num">5/12</td><td class="num">0.9555</td><td class="num">0.8551</td><td class="num">0.9948</td><td class="num">12.24h</td><td class="num">151.3M</td><td class="num">1.08M</td><td><span class="tag caution">low thinking costs one solve</span></td></tr>
</tbody></table></div>
<div class="callout caution"><strong>Timeout sensitivity.</strong> Two headline cells never got a fair grade: GGUF-TP's LangChain cell returned a 59.6KB patch but the <em>verifier</em> timed out (recorded ungraded, partial 0.0), and llama.cpp's LangChain cell hit the 3h <em>agent</em> cap while trending 46/50 F2P (partial 0.9858). Counting those as best-case solves, the ranges are GGUF-TP <strong>7\u20138</strong>, llama.cpp <strong>6\u20137</strong>, OpenRouter <strong>6</strong>. As-graded remains primary.</div></section>

<section><div class="head"><div><h2>Matched task \u00d7 rep cells</h2><p>One trajectory per task per system. Each cell shows the strict-solve verdict, partial reward, F2P/P2P fractions, agent wall time, and total tokens. \u201cUngraded\u201d marks a substrate failure (verifier timeout), not a model failure.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th>vLLM GGUF-TP (local)</th><th>llama.cpp IQ2_XXS (local)</th><th>OpenRouter hosted FP</th><th>Agreement</th></tr></thead><tbody>
@@TASK_ROWS@@
</tbody></table></div></section>

<section><div class="head"><div><h2>Solve flips: @@N_DISCORD@@ of 12 tasks disagree</h2><p>Only four tasks are unanimous \u2014 adaptix, goreleaser, and mobly solve everywhere; participle solves nowhere. Everything else flips. With one rep per task, any single flip is noise-compatible; the shape of the flips is the signal.</p></div></div>
<div class="table-wrap"><table><thead><tr><th>Task</th><th>Who solves</th><th class="num">GGUF-TP partial</th><th class="num">llama.cpp partial</th><th class="num">OpenRouter partial</th><th>Note</th></tr></thead><tbody>
@@CHURN_ROWS@@
</tbody></table></div>
<div class="callout"><strong>Pairwise churn.</strong> GGUF-TP vs llama.cpp: 5 flips (+3 net to GGUF-TP). GGUF-TP vs OpenRouter: 5 flips (+1 net to GGUF-TP). llama.cpp vs OpenRouter: 6 flips (net 0). Two discordant tasks \u2014 dateutil and go-critic \u2014 produced <em>identical</em> partials and F2P fractions on GGUF-TP and OpenRouter (66/67 and 2/3 respectively): the same model reaching the same final state through two stacks, with llama.cpp the outlier that finished both.</div></section>

<section><div class="head"><div><h2>Capability shape by serving stack</h2><p>What each runtime makes the same model reliably do on 12_v2. Strict solves and F2P are the primary evidence; large preservation suites keep partial reward close to 1 even on misses.</p></div></div>
<div class="grid">
<div class="card"><h3>vLLM GGUF-TP \u2014 most solves, near-miss profile</h3><p>7/12 with the two TypeScript unique solves (obsidian 60/60, superjson 80/80 \u2014 no other stack solved either). Every graded non-solve is a near-miss: minimum partial 0.8947, and three of four misses are single-test F2P gaps (dateutil 66/67, participle 89/91, tengo 22/23). Fastest and cheapest local stack: 8.70h vs llama.cpp's 19.85h, 142.6M vs 224.8M tokens.</p></div>
<div class="card"><h3>llama.cpp IQ2_XXS \u2014 unique solves, one collapse</h3><p>6/12 including the only dateutil (67/67) and go-critic (3/3) solves in the comparison. But it owns the worst cell of the set: participle at F2P 2/91 (partial 0.6352) where the other stacks reach 89/91 and 90/91. Slowest by far (19.85h; langchain hit the 3h cap at 46/50 F2P) and most tokens (224.8M). Low thinking drops it to 5/12.</p></div>
<div class="card"><h3>OpenRouter hosted FP \u2014 highest partial, fastest wall</h3><p>6/12 with the highest mean partial (0.9761) and by far the fastest wall (4.54h, 1.9\u00d7 faster than GGUF-TP) for $3.18 total. Uniquely solved langchain and tengo. Its weak spots are agentic TypeScript tasks: claude-code-by-agents is its worst cell (F2P 2/7, partial 0.8684 \u2014 both local stacks solved it) and superjson adds the comparison's only P2P dip (57/58).</p></div>
</div></section>

<section><div class="head"><div><h2>Efficiency</h2><p>Summed agent wall time and tokens over the 12 cells. Deterministic CSS bars; widths scale to the largest value in each row group.</p></div></div>
<div class="legend"><span><span class="dot" style="background:#1d3fb8"></span>GGUF-TP</span><span><span class="dot" style="background:#7d8ba1"></span>llama.cpp max</span><span><span class="dot" style="background:#178a5b"></span>OpenRouter</span><span><span class="dot" style="background:#c58a00"></span>llama.cpp low (secondary)</span></div>
<div class="grid" style="grid-template-columns:repeat(3,minmax(0,1fr))">
<div class="card"><h3>Agent wall (hours)</h3><div class="bar-list">@@BAR_WALL@@</div></div>
<div class="card"><h3>Total tokens (incl. cache reads)</h3><div class="bar-list">@@BAR_TOK@@</div></div>
<div class="card"><h3>Output tokens (model-generated)</h3><div class="bar-list">@@BAR_OUT@@</div></div>
</div>
<div class="callout"><strong>Token accounting differs by stack.</strong> <code>combined_total_tokens</code> = input + output + cache reads. The GGUF-TP vLLM server reported no prefix-cache hits, so every turn's full prompt counts as input; llama.cpp and OpenRouter report cache reads explicitly (e.g. llama.cpp adaptix: 32.1M of 32.3M total are cache reads). Output tokens are the cleaner cross-stack volume signal: 1.51M (GGUF-TP) vs 1.83M (llama.cpp) vs 1.32M (OpenRouter). Turns: 1,877 vs 1,728 vs 1,337.</div></section>

<section><div class="head"><div><h2>Production caveat: the 148k gate is a concurrency-1 server</h2><p>Evidence from the launch of the GGUF-TP config.</p></div></div>
<div class="callout bad"><strong>Under 2-way concurrent prefill at the 148k context gate, the vLLM GGUF-TP server terminates sequences.</strong> The server runs 4\u00d7RTX 3090 TP4 with <code>max_num_seqs=2</code>, <code>max_num_batched_tokens=256</code>, FP8 MLA KV, and <strong>154,519 GPU KV-cache tokens</strong> against a 148,000-token gate \u2014 a measured <code>max_context_concurrency</code> of 1.1. The first launch attempt ran workers=2: the obsidian and participle cells died mid-run with session-log entries <code>stopReason: "error"</code> / <code>errorMessage: "terminated"</code> and zero-usage responses, ending as near-empty trajectories (52.4K and 17.6K total tokens, 15 and 12 turns, empty patches, <code>verifier_exit: skipped_empty_patch</code>). Those two cells are preserved under <code>_concurrency2-discarded/</code> and excluded here. Re-run solo, both tasks completed cleanly (obsidian solved 60/60, participle 89/91). <strong>Production guidance: run this stack at concurrency 1.</strong></div>
<div class="callout caution"><strong>Provenance on the reused superjson cell.</strong> SuperJSON's GGUF-TP result was reused from the crashed concurrency-2 attempt via <code>compatible_existing_result</code> \u2014 it had passed preflight cleanly before the crash, and its identity (config lock, harness revision, image digests, verifier, task revision) matched the relaunch plan. The final run state: 10 ok, 1 failed (langchain verifier timeout), 1 skipped (superjson reuse).</div></section>

<section><div class="head"><div><h2>Substrate and provenance notes</h2></div></div>
<div class="table-wrap"><table><thead><tr><th>Item</th><th>Detail</th><th>Treatment</th></tr></thead><tbody>
<tr><td><strong>GGUF-TP langchain cell</strong></td><td>Agent finished (70.1m, 216 turns, 59.6KB patch); verifier timed out, <code>reward_unverified: true</code>, partial 0.0, F2P/P2P undefined.</td><td><span class="tag caution">grading failure</span> counted as non-solve; excluded from mean F2P; sensitivity view above.</td></tr>
<tr><td><strong>llama.cpp langchain cell</strong></td><td>Agent hit the 3h cap at exactly 180.0m with partial 0.9858, F2P 46/50.</td><td><span class="tag neutral">agent timeout</span> observed outcome kept primary; best-case range noted.</td></tr>
<tr><td><strong>llama.cpp run selection</strong></td><td>Max-thinking results come from the completed <code>llamacpp-dsv4f0731-iq2xxs-max-12v2-r1-w1-3h</code> run (completed 2026-08-12); low from <code>\u2026-low-12v2-r1-w1</code> (completed 2026-08-11). A second low run failed at launch and is ignored.</td><td><span class="tag good">verified complete</span> 12/12 cells each via manifest result_path fields.</td></tr>
<tr><td><strong>Pi subject versions</strong></td><td>GGUF-TP cells ran pi@0.84.1; llama.cpp and OpenRouter cells ran pi@0.84.0.</td><td><span class="tag neutral">provenance only</span> per project rule; not treated as a behavioral confound.</td></tr>
<tr><td><strong>Wall-time rounding</strong></td><td>Launch note cited 8.71h for GGUF-TP; on-disk <code>agent_wall_s</code> sums to 31,329.6s = 8.7027h (26s delta).</td><td><span class="tag neutral">noted</span> this report displays the on-disk 8.70h.</td></tr>
<tr><td><strong>Token comparability</strong></td><td>GGUF-TP server reports no prefix-cache reads; other stacks do.</td><td><span class="tag neutral">accounting caveat</span> output tokens and turns provided as the cleaner signal.</td></tr>
</tbody></table></div></section>

<section><div class="head"><div><h2>Bottom line</h2></div></div>
<div class="callout good"><strong>The local GGUF-TP stack is capability-competitive with hosted full-precision on 12_v2.</strong> It posts the most strict solves (7/12 vs 6/6), the best local wall time (8.70h vs llama.cpp's 19.85h), the fewest total tokens (142.6M), and a near-miss-only failure profile \u2014 every graded non-solve sits at partial \u2265 0.8947 with single-test F2P gaps on three of four.</div>
<div class="callout"><strong>The stacks differ more in which tasks they solve than in how well they solve them.</strong> @@N_DISCORD@@/12 tasks are discordant and every system owns at least one unique solve (GGUF-TP: obsidian, superjson; llama.cpp: dateutil, go-critic; OpenRouter: langchain, tengo). Mean partials are 0.91\u20130.98 across the board. At one rep per task this is churn, not a ranking \u2014 the reliable read is each stack's distinctive miss: llama.cpp's participle collapse (2/91 F2P), OpenRouter's recursive-delegation miss (2/7 F2P), GGUF-TP's ungraded langchain cell.</div>
<div class="callout bad"><strong>Operate the GGUF-TP server at concurrency 1.</strong> At the 148k production gate the KV budget (154,519 tokens) fits ~1.1 max-length contexts; 2-way concurrent prefill terminated sequences mid-run (<code>stopReason: error / "terminated"</code>, zero usage). Solo execution was clean for all 12 tasks.</div>
<div class="callout"><strong>Interpretation limit.</strong> Quantization (mixed IQ2_XXS/Q2_K/Q8_0 vs IQ2_XXS vs full precision), serving engine (vLLM TP vs llama.cpp vs hosted), context window (148k vs provider), and Pi subject version (0.84.1 vs 0.84.0) all vary together, and two headline cells carry substrate failures. Treat this as a capability-shape / serving-stack contrast over one rep per task \u2014 not a quantization-isolated causal claim and not a product ranking.</div></section>

<div class="foot">Generated @@GEN@@ \u00b7 Data: <code>comparison.json</code> (built from 48 on-disk <code>result.json</code> artifacts) \u00b7 Subset 12_v2, rep0, max thinking unless marked \u00b7 GGUF-TP run <code>dsv4-gguf-tp-max-12v2-r1-w1</code> \u00b7 llama.cpp runs <code>llamacpp-dsv4f0731-iq2xxs-{max-3h,low}-12v2-r1-w1</code></div>
</div></body></html>
"""

if __name__ == "__main__":
    main()

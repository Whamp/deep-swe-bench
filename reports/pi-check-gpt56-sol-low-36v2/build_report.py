#!/usr/bin/env python3
import collections
import html
import json
import math
import random
import statistics
import tomllib
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("index.html")
CONFIGS = ("baseline", "pi-check")
ROOTS = {name: REPO / "results" / "gpt-5.6-sol" / "low" / name for name in CONFIGS}
CHECK_PROMPT = "Re-audit every requirement in the original request with fresh, independent evidence"


def pct(value):
    return f"{value * 100:.1f}%"


def delta_pct(value):
    return f"{value * 100:+.1f} pp"


def signed(value, digits=1):
    return f"{value:+.{digits}f}"


def load_results():
    records = {}
    for config, root in ROOTS.items():
        for path in root.glob("*/rep*/result.json"):
            record = json.loads(path.read_text())
            records[(config, record["task"], record["rep"])] = record
    return records


def task_title(task):
    path = REPO.parent / "deep-swe" / "tasks" / task / "task.toml"
    if not path.exists():
        return task
    with path.open("rb") as f:
        return tomllib.load(f).get("metadata", {}).get("display_title", task)


def post_check_tools(task, rep):
    session_paths = list((ROOTS["pi-check"] / task / f"rep{rep}" / "session").glob("*.jsonl"))
    after = False
    tools = collections.Counter()
    final_count = 0
    prompt_count = 0
    for line in session_paths[0].read_text(errors="replace").splitlines():
        record = json.loads(line)
        if record.get("type") != "message":
            continue
        message = record.get("message", {})
        content = message.get("content")
        text = content if isinstance(content, str) else " ".join(
            part.get("text", "") for part in (content or []) if isinstance(part, dict)
        )
        if message.get("role") == "user" and CHECK_PROMPT in text:
            prompt_count += 1
            after = True
            continue
        if not after:
            continue
        if message.get("role") == "assistant" and isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and part.get("type") == "toolCall":
                    tools[part.get("name", "unknown")] += 1
        if message.get("role") == "assistant" and message.get("stopReason") == "stop":
            final_count += 1
    return tools, final_count, prompt_count


def exact_sign_p(left_only, right_only):
    n = left_only + right_only
    if not n:
        return 1.0
    tail = min(left_only, right_only)
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(tail + 1)) / (2**n))


records = load_results()
baseline_keys = {(task, rep) for config, task, rep in records if config == "baseline"}
check_keys = {(task, rep) for config, task, rep in records if config == "pi-check"}
if baseline_keys != check_keys or len(baseline_keys) != 108:
    raise SystemExit(f"expected 108 exact pairs, got baseline={len(baseline_keys)} pi-check={len(check_keys)}")
keys = sorted(baseline_keys)
tasks = sorted({task for task, _ in keys})

summary = {}
for config in CONFIGS:
    rows = [records[(config, *key)] for key in keys]
    summary[config] = {
        "solves": sum(row["reward_binary"] == 1 for row in rows),
        "partial": statistics.mean(row["reward_partial"] for row in rows),
        "mean_f2p": statistics.mean(row["f2p"] or 0 for row in rows),
        "mean_p2p": statistics.mean(row["p2p"] or 0 for row in rows),
        "f2p_passed": sum(row["f2p_passed"] or 0 for row in rows),
        "f2p_total": sum(row["f2p_total"] or 0 for row in rows),
        "p2p_passed": sum(row["p2p_passed"] or 0 for row in rows),
        "p2p_total": sum(row["p2p_total"] or 0 for row in rows),
        "tokens": sum(row["total_tokens"] for row in rows),
        "mean_tokens": statistics.mean(row["total_tokens"] for row in rows),
        "cost": sum(row["cost_usd"] for row in rows),
        "mean_wall": statistics.mean(row["agent_wall_s"] for row in rows),
        "mean_turns": statistics.mean(row["turns"] for row in rows),
        "mean_tools": statistics.mean(row["tool_calls"] for row in rows),
        "timeouts": sum(bool(row["agent_timed_out"]) for row in rows),
        "empty_patches": sum(row["verifier_exit"] == "skipped_empty_patch" for row in rows),
        "bad_agent_exit": sum(row["agent_exit"] != 0 for row in rows),
    }
    by_task = collections.defaultdict(list)
    for row in rows:
        by_task[row["task"]].append(row["reward_binary"] == 1)
    summary[config]["tasks_any"] = sum(any(values) for values in by_task.values())
    summary[config]["tasks_majority"] = sum(sum(values) >= 2 for values in by_task.values())
    summary[config]["tasks_all"] = sum(sum(values) == 3 for values in by_task.values())

both = baseline_only = check_only = neither = 0
flip_rows: list[dict[str, Any]] = []
post_check_mutation = collections.Counter()
for task, rep in keys:
    left = records[("baseline", task, rep)]
    right = records[("pi-check", task, rep)]
    left_solve = left["reward_binary"] == 1
    right_solve = right["reward_binary"] == 1
    if left_solve and right_solve:
        bucket = "both"
        both += 1
    elif left_solve:
        bucket = "baseline-only"
        baseline_only += 1
    elif right_solve:
        bucket = "pi-check-only"
        check_only += 1
    else:
        bucket = "neither"
        neither += 1
    tools, final_count, prompt_count = post_check_tools(task, rep)
    explicit_mutation = tools["edit"] + tools["write"] > 0
    post_check_mutation[(bucket, explicit_mutation)] += 1
    if bucket in ("baseline-only", "pi-check-only"):
        flip_rows.append({
            "task": task,
            "title": task_title(task),
            "rep": rep,
            "bucket": bucket,
            "left": left,
            "right": right,
            "tools": tools,
            "mutation": explicit_mutation,
            "final_count": final_count,
            "prompt_count": prompt_count,
        })

# Delivery audit.
delivery = {}
for config in CONFIGS:
    prompt_counts = collections.Counter()
    flag_counts = collections.Counter()
    low_requests = model_requests = request_total = 0
    model_thinking_ok = 0
    for task, rep in keys:
        result = records[(config, task, rep)]
        cell = ROOTS[config] / task / f"rep{rep}"
        session_text = "".join(path.read_text(errors="replace") for path in (cell / "session").glob("*.jsonl"))
        prompt_counts[session_text.count(CHECK_PROMPT)] += 1
        flag_counts[tuple(result.get("arm_pi_flags") or [])] += 1
        model_thinking_ok += result.get("model") == "openai-codex/gpt-5.6-sol" and result.get("thinking_level") == "low"
        for path in (cell / "initial_context").glob("provider_request_*.json"):
            request = json.loads(path.read_text())
            request_total += 1
            low_requests += request.get("reasoning", {}).get("effort") == "low"
            model_requests += request.get("model") == "gpt-5.6-sol"
    delivery[config] = {
        "prompt_counts": dict(prompt_counts),
        "flag_counts": {str(key): value for key, value in flag_counts.items()},
        "request_total": request_total,
        "low_requests": low_requests,
        "model_requests": model_requests,
        "model_thinking_ok": model_thinking_ok,
    }

# Task-cluster bootstrap keeps the three reps for a task together.
rng = random.Random(20260723)
bootstrap = []
for _ in range(20_000):
    sampled_tasks = [rng.choice(tasks) for _ in tasks]
    delta = sum(
        (records[("pi-check", task, rep)]["reward_binary"] == 1) - (records[("baseline", task, rep)]["reward_binary"] == 1)
        for task in sampled_tasks for rep in range(3)
    ) / (len(tasks) * 3)
    bootstrap.append(delta)
bootstrap.sort()
ci_low = bootstrap[int(0.025 * len(bootstrap))]
ci_high = bootstrap[int(0.975 * len(bootstrap)) - 1]

# Language splits and task vectors.
language_rows = []
for language in sorted({records[("baseline", *key)]["language"] for key in keys}):
    language_keys = [key for key in keys if records[("baseline", *key)]["language"] == language]
    left = sum(records[("baseline", *key)]["reward_binary"] == 1 for key in language_keys)
    right = sum(records[("pi-check", *key)]["reward_binary"] == 1 for key in language_keys)
    language_rows.append((language, len(language_keys), left, right))

task_rows = []
for task in tasks:
    left = sum(records[("baseline", task, rep)]["reward_binary"] == 1 for rep in range(3))
    right = sum(records[("pi-check", task, rep)]["reward_binary"] == 1 for rep in range(3))
    task_rows.append((task, task_title(task), records[("baseline", task, 0)]["language"], left, right))
task_rows.sort(key=lambda row: (-(row[4] - row[3]), row[0]))

base = summary["baseline"]
check = summary["pi-check"]
solve_delta = (check["solves"] - base["solves"]) / 108
cost_delta = check["cost"] / base["cost"] - 1
token_delta = check["tokens"] / base["tokens"] - 1
wall_delta = check["mean_wall"] / base["mean_wall"] - 1
sign_p = exact_sign_p(baseline_only, check_only)
weighted_f2p_base = base["f2p_passed"] / base["f2p_total"]
weighted_f2p_check = check["f2p_passed"] / check["f2p_total"]
weighted_p2p_base = base["p2p_passed"] / base["p2p_total"]
weighted_p2p_check = check["p2p_passed"] / check["p2p_total"]

metric_rows = [
    ("Binary solves", f'{base["solves"]}/108 · {pct(base["solves"]/108)}', f'{check["solves"]}/108 · {pct(check["solves"]/108)}', delta_pct(solve_delta), "good"),
    ("Tasks with ≥1 solve", f'{base["tasks_any"]}/36', f'{check["tasks_any"]}/36', f'+{check["tasks_any"]-base["tasks_any"]}', "good"),
    ("Tasks with majority solve", f'{base["tasks_majority"]}/36', f'{check["tasks_majority"]}/36', f'+{check["tasks_majority"]-base["tasks_majority"]}', "good"),
    ("Mean partial reward", pct(base["partial"]), pct(check["partial"]), delta_pct(check["partial"]-base["partial"]), "good"),
    ("Weighted F2P", f'{base["f2p_passed"]:,}/{base["f2p_total"]:,} · {pct(weighted_f2p_base)}', f'{check["f2p_passed"]:,}/{check["f2p_total"]:,} · {pct(weighted_f2p_check)}', delta_pct(weighted_f2p_check-weighted_f2p_base), "good"),
    ("Weighted P2P", f'{base["p2p_passed"]:,}/{base["p2p_total"]:,} · {pct(weighted_p2p_base)}', f'{check["p2p_passed"]:,}/{check["p2p_total"]:,} · {pct(weighted_p2p_check)}', delta_pct(weighted_p2p_check-weighted_p2p_base), "good"),
    ("Total tokens", f'{base["tokens"]/1e6:.1f}M', f'{check["tokens"]/1e6:.1f}M', f'+{token_delta*100:.1f}%', "bad"),
    ("Mean tokens / cell", f'{base["mean_tokens"]/1000:.0f}K', f'{check["mean_tokens"]/1000:.0f}K', f'+{token_delta*100:.1f}%', "bad"),
    ("Total recorded cost", f'${base["cost"]:.2f}', f'${check["cost"]:.2f}', f'+{cost_delta*100:.1f}%', "bad"),
    ("Mean agent wall time", f'{base["mean_wall"]:.1f}s', f'{check["mean_wall"]:.1f}s', f'+{wall_delta*100:.1f}%', "bad"),
    ("Mean turns", f'{base["mean_turns"]:.1f}', f'{check["mean_turns"]:.1f}', f'+{(check["mean_turns"]/base["mean_turns"]-1)*100:.1f}%', "bad"),
    ("Mean tool calls", f'{base["mean_tools"]:.1f}', f'{check["mean_tools"]:.1f}', f'+{(check["mean_tools"]/base["mean_tools"]-1)*100:.1f}%', "bad"),
    ("Timeouts / empty patches", f'{base["timeouts"]} / {base["empty_patches"]}', f'{check["timeouts"]} / {check["empty_patches"]}', "−1 empty", "good"),
]

style = """
:root{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--radius:22px;--shadow:0 20px 55px rgba(14,30,62,.08)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,rgba(51,93,255,.11),transparent 28%),linear-gradient(#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:1220px;margin:auto;padding:28px 20px 60px}.hero,section{background:rgba(255,255,255,.92);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:38px;position:relative;overflow:hidden}.eyebrow{display:inline-block;padding:7px 11px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1{font-size:clamp(2.4rem,5vw,4.8rem);line-height:1.02;letter-spacing:-.045em;max-width:12ch;margin:14px 0}.lede{font-size:1.1rem;color:var(--muted);max-width:75ch}.pills{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.pill,.tag{display:inline-flex;padding:6px 10px;border-radius:999px;font-weight:800;font-size:12px}.good{background:var(--green-soft);color:var(--green)}.bad{background:var(--red-soft);color:var(--red)}.caution{background:var(--amber-soft);color:#8a6100}.neutral{background:#edf1f7;color:#536173}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-top:20px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.7rem;line-height:1.1;letter-spacing:-.04em}.stat span{color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:28px}h2{font-size:1.75rem;letter-spacing:-.03em;margin:0 0 6px}.section-lede{color:var(--muted);margin:0 0 18px}.callout{border-left:5px solid var(--blue);background:#f6f8ff;padding:15px 17px;border-radius:13px;margin:16px 0}.callout.goodline{border-color:var(--green);background:var(--green-soft)}.callout.warn{border-color:var(--amber);background:var(--amber-soft)}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}.table-wrap{overflow-x:auto}.bars{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.bar-card{border:1px solid var(--line);border-radius:16px;padding:15px}.bar-card strong{font-size:1.55rem}.bar{height:9px;border-radius:99px;background:#edf1f7;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;border-radius:99px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.evidence{font-family:ui-monospace,monospace;font-size:13px;background:#f7f9fc;border:1px solid var(--line);padding:13px;border-radius:12px}details{border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:12px}summary{cursor:pointer;font-weight:800}code{background:#eef2ff;padding:.1em .35em;border-radius:5px}.muted{color:var(--muted)}footer{color:var(--muted);text-align:center;padding:25px}.winner{font-weight:800;color:var(--green)}.loser{font-weight:800;color:var(--red)}
@media(max-width:850px){.stats{grid-template-columns:repeat(2,1fr)}.bars,.grid2{grid-template-columns:1fr}.hero,section{padding:22px}}@media(max-width:520px){.stats{grid-template-columns:1fr}}
"""

metric_html = "".join(
    f'<tr><td>{html.escape(name)}</td><td class="num">{left}</td><td class="num">{right}</td><td class="num"><span class="tag {verdict}">{delta}</span></td></tr>'
    for name, left, right, delta, verdict in metric_rows
)

flip_html = "".join(
    f'<tr><td><strong>{html.escape(row["task"])}</strong><br><span class="muted">{html.escape(row["title"])}</span></td>'
    f'<td class="num">{row["rep"]}</td>'
    f'<td><span class="tag {"good" if row["bucket"] == "pi-check-only" else "bad"}">{html.escape(row["bucket"])}</span></td>'
    f'<td class="num">{row["left"]["f2p_passed"]}/{row["left"]["f2p_total"]}<br><span class="muted">partial {row["left"]["reward_partial"]:.3f}</span></td>'
    f'<td class="num">{row["right"]["f2p_passed"]}/{row["right"]["f2p_total"]}<br><span class="muted">partial {row["right"]["reward_partial"]:.3f}</span></td>'
    f'<td>{sum(row["tools"].values())} calls; edit/write {row["tools"]["edit"] + row["tools"]["write"]}</td></tr>'
    for row in sorted(flip_rows, key=lambda row: (row["bucket"] != "pi-check-only", row["task"], row["rep"]))
)

task_html = "".join(
    f'<tr><td><strong>{html.escape(task)}</strong><br><span class="muted">{html.escape(title)}</span></td><td>{html.escape(language)}</td><td class="num">{left}/3</td><td class="num">{right}/3</td><td class="num"><span class="tag {"good" if right>left else "bad" if right<left else "neutral"}">{right-left:+d}</span></td></tr>'
    for task, title, language, left, right in task_rows
)

language_html = "".join(
    f'<tr><td>{html.escape(language)}</td><td class="num">{count}</td><td class="num">{left}</td><td class="num">{right}</td><td class="num">{right-left:+d}</td></tr>'
    for language, count, left, right in language_rows
)

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>pi-check · GPT-5.6-SOL low · 36_v2</title><style>{style}</style></head>
<body><div class="wrap">
<header class="hero">
  <span class="eyebrow">DeepSWE · matched 36_v2 comparison · 3 reps</span>
  <h1>pi-check wins again—with more churn.</h1>
  <p class="lede">On 108 paired GPT-5.6-SOL-low cells, pi-check raised actual solves from <strong>53 to 67</strong>. The gain survived task-clustered resampling, but came with <strong>90.8% more tokens</strong>, <strong>69.6% more recorded cost</strong>, and seven baseline-only solve flips.</p>
  <div class="pills"><span class="pill good">+14 net solves</span><span class="pill good">+13.0 percentage points</span><span class="pill good">21 gains vs 7 losses</span><span class="pill neutral">0 timeout discordances</span><span class="pill bad">+90.8% tokens</span></div>
  <div class="stats">
    <div class="stat"><strong>62.0%</strong><span>pi-check solved</span></div>
    <div class="stat"><strong>49.1%</strong><span>baseline solved</span></div>
    <div class="stat"><strong>+26.4%</strong><span>relative solve lift</span></div>
    <div class="stat"><strong>$53.82</strong><span>incremental cost</span></div>
    <div class="stat"><strong>108/108</strong><span>check delivered once</span></div>
  </div>
</header>

<section>
  <h2>Verdict</h2><p class="section-lede">The matched comparison favors pi-check, with meaningful churn and a substantial efficiency tax.</p>
  <div class="callout goodline"><strong>Adopt for efficacy-sensitive work.</strong> pi-check solved 14 more cells net, expanded tasks with at least one successful rep from 24/36 to 28/36, and raised all-three-rep task solves from 11 to 18. The task-cluster bootstrap 95% interval for solve-rate delta is {delta_pct(ci_low)} to {delta_pct(ci_high)}. The cell-level discordant sign test is p={sign_p:.4f}, but unlike the bootstrap it does not account for three-rep task clustering.</div>
  <div class="callout warn"><strong>Do not describe it as uniformly better.</strong> Seven baseline solves flipped to failures, and the follow-up nearly doubled tokens. The observed incremental spend divided by the 14 net extra solves is ${(check['cost']-base['cost'])/(check['solves']-base['solves']):.2f} per net additional solve; that ratio is descriptive, not a causal price.</div>
</section>

<section>
  <h2>Score and efficiency</h2><p class="section-lede">Intention-to-treat results. Every baseline cell maps to exactly one pi-check cell with the same task, rep, model, and thinking level.</p>
  <div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{metric_html}</tbody></table></div>
  <div class="callout warn"><strong>Empty-patch sensitivity:</strong> baseline <code>koota-query-predicates/rep1</code> produced no patch and carries the harness sentinel <code>reward_binary = -1</code>. It is retained as unsolved in the 53/108 primary result. Excluding that matched pair yields 53/107 versus 67/107 (+13.1 pp), essentially unchanged. Weighted F2P/P2P use only graded tests, so their baseline denominators are slightly smaller.</div>
</section>

<section>
  <h2>Net versus churn</h2><p class="section-lede">The +14 net result is composed of 21 gains and 7 losses—not 14 cells moving in one direction.</p>
  <div class="bars">
    <div class="bar-card"><strong>{both}</strong><div>both solved</div><div class="bar"><i style="width:{both/108*100:.1f}%;background:var(--blue)"></i></div></div>
    <div class="bar-card"><strong class="winner">{check_only}</strong><div>pi-check only</div><div class="bar"><i style="width:{check_only/108*100:.1f}%;background:var(--green)"></i></div></div>
    <div class="bar-card"><strong class="loser">{baseline_only}</strong><div>baseline only</div><div class="bar"><i style="width:{baseline_only/108*100:.1f}%;background:var(--red)"></i></div></div>
    <div class="bar-card"><strong>{neither}</strong><div>neither solved</div><div class="bar"><i style="width:{neither/108*100:.1f}%;background:var(--amber)"></i></div></div>
  </div>
  <div class="callout"><strong>Pattern:</strong> 17 of the 21 pi-check-only wins started from baseline partial reward ≥95%, consistent with fresh verification converting many near-misses. But the audit is interventionist: 19/21 wins and all 7 losses contain explicit <code>edit</code>/<code>write</code> calls after the check prompt.</div>
  <div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Flip</th><th class="num">Baseline F2P</th><th class="num">pi-check F2P</th><th>Post-check activity</th></tr></thead><tbody>{flip_html}</tbody></table></div>
</section>

<section>
  <h2>What the follow-up actually did</h2>
  <div class="grid2">
    <div><h3>Winning behavior</h3><p>In <code>goreleaser-retry-publish-auditing/rep2</code>, baseline passed only 2/29 feature tests. After the check prompt, pi-check identified retry and audit gaps, edited the implementation, added focused tests, ran race and package tests, and reached 29/29 F2P with full P2P preservation.</p></div>
    <div><h3>Failure mode</h3><p>In <code>claude-code-by-agents-recursive-delegation/rep1</code> and <code>rep2</code>, baseline was 7/7 F2P. The follow-up edited recursive error handling and added tests, reported success, but the external verifier fell to 2/7 F2P in both reps. The other five losses were narrower misses of one to three feature tests.</p></div>
  </div>
  <div class="callout warn"><strong>Interpretation, not proof:</strong> the direct session evidence shows the follow-up changing code in both wins and losses. It supports “fresh audit can repair near-misses” and “fresh audit can over-edit,” but does not fully isolate those edits from model sampling variance. A prompt change should be treated as a new hypothesis and rerun.</div>
</section>

<section>
  <h2>Delivery and run integrity</h2><p class="section-lede">The treatment was not missing or leaked.</p>
  <div class="grid2">
    <div class="evidence"><strong>Baseline</strong><br>108/108 model + thinking records: openai-codex/gpt-5.6-sol · low<br>108/108 sessions with zero check prompts<br>108/108 empty config pi-flags<br>216/216 captured requests: gpt-5.6-sol · effort low<br>0 timeouts · 1 empty patch retained as unsolved</div>
    <div class="evidence"><strong>pi-check</strong><br>108/108 model + thinking records: openai-codex/gpt-5.6-sol · low<br>108/108 sessions with exactly one check prompt<br>108/108 exact extension + --check flags<br>216/216 captured requests: gpt-5.6-sol · effort low<br>0 timeouts · 0 empty patches</div>
  </div>
  <p class="muted">Run roots: <code>results/gpt-5.6-sol/low/baseline</code> and <code>results/gpt-5.6-sol/low/pi-check</code>. Structured run: <code>gpt56-sol-low-baseline-pi-check-36v2-r3-w12</code>. Its status is completed with 216 batch cells and both smoke contracts passed.</p>
</section>

<section>
  <h2>Language direction</h2><p class="section-lede">No language regressed in net binary solves; the largest observed lift was Go. Counts are cells, not independent tasks.</p>
  <div class="table-wrap"><table><thead><tr><th>Language</th><th class="num">Cells</th><th class="num">Baseline solves</th><th class="num">pi-check solves</th><th class="num">Net</th></tr></thead><tbody>{language_html}</tbody></table></div>
</section>

<section>
  <h2>All 36 tasks</h2><p class="section-lede">Solved reps out of three. Seventeen tasks changed; five previously all-failing tasks gained at least one solve.</p>
  <details><summary>Open task-by-task table</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th>Language</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{task_html}</tbody></table></div></details>
</section>

<section>
  <h2>Conclusion</h2>
  <div class="callout goodline"><strong>Bottom line:</strong> pi-check materially improved GPT-5.6-SOL-low performance on 36_v2: 67/108 versus 53/108, with 21 favorable and 7 unfavorable solve flips. The price was 53.9M additional tokens, $53.82 additional recorded cost, and 181 seconds more mean agent time per cell.</div>
  <div class="callout"><strong>Next decision:</strong> keep the extension if solve rate dominates cost. If efficiency matters, test a narrower verification contract—fresh targeted tests first, code edits only when evidence identifies a concrete unmet requirement—without changing the current result’s interpretation.</div>
</section>
<footer>Generated from immutable DeepSWE result artifacts · subset 36_v2 · GPT-5.6-SOL low · 3 reps · 23 July 2026</footer>
</div></body></html>"""
OUT.write_text(page)
print(OUT)

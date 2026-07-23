#!/usr/bin/env python3
import json, pathlib, html
OUT=pathlib.Path('analysis/thinkingcap-qwen36-high-12v2-failures')
data=json.loads((OUT/'summary.json').read_text())
rows=data['rows']; summary=data['summary']

def esc(x): return html.escape(str(x))
def pct(n,d): return f"{100*n/d:.1f}%" if d else '—'
def result(r,k,default='—'):
    res=r.get('result') or {}
    return res.get(k, default)

def snippet(r):
    evs=(r.get('traj') or {}).get('last_events') or []
    bits=[]
    for e in evs[-3:]:
        role=e.get('role') or e.get('type')
        text=(e.get('text') or '')
        if len(text)>420: text=text[:420]+'…'
        bits.append(f"<div class='event'><b>{esc(role)}</b> {esc(e.get('tool',''))} <span>{esc(text)}</span></div>")
    return ''.join(bits) if bits else '<span class="muted">No completed session events.</span>'

def cls_label(c):
    return {
        'early_stop_after_orientation_no_edit':'early stop / no edit',
        'no_diff_after_work':'worked, no diff',
        'agent_timeout_after_patch':'agent timeout after patch',
        'verifier_timeout_after_patch':'verifier timeout after patch',
        'first_completion_hang_no_session':'first completion hang',
    }.get(c,c)

# Compact derived facts
empty=[r for r in rows if r['outcome']=='empty']
timeouts=[r for r in rows if r['outcome']=='timeout']
failed=[r for r in rows if r['outcome']=='exit=1']

html_rows=[]
for r in rows:
    res=r.get('result') or {}
    html_rows.append(f"""
<tr>
  <td><code>{esc(r['task'])}</code><br><span class='muted'>rep {r['rep']}</span></td>
  <td><span class='tag {('bad' if r['outcome'] in ['empty','exit=1'] else 'caution')}'>{esc(r['outcome'])}</span></td>
  <td>{esc(cls_label(r['class']))}</td>
  <td>{esc(res.get('reward_partial','—'))}</td>
  <td>{esc(res.get('patch_bytes','—'))}</td>
  <td>{esc(res.get('agent_wall_s','—'))}</td>
  <td>{esc((r.get('traj') or {}).get('assistant_turns','—'))} / {esc((r.get('traj') or {}).get('tool_calls','—'))}</td>
  <td>{snippet(r)}</td>
</tr>
""")

by_class=''.join(f"<li><b>{esc(cls_label(k))}</b>: {v}</li>" for k,v in summary['by_class'].items())
by_task=''.join(f"<tr><td><code>{esc(k)}</code></td><td>{esc(dict(v))}</td></tr>" for k,v in summary['by_task'].items())

doc=f"""<!doctype html>
<html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width, initial-scale=1'>
<title>ThinkingCap-Qwen3.6 failure trajectories</title>
<style>
:root {{ --bg:#0b1020; --surface:#111936; --surface2:#172247; --ink:#eef3ff; --muted:#9fb0d0; --blue:#7cc7ff; --green:#67e8a5; --red:#ff7d8a; --amber:#ffd166; }}
*{{box-sizing:border-box}} body{{margin:0;background:linear-gradient(180deg,#081020,#0b1020 30%,#0d1328);color:var(--ink);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif}}
main{{max-width:1180px;margin:0 auto;padding:32px 20px 56px}} .hero{{background:linear-gradient(135deg,#16214a,#101832);border:1px solid #26345f;border-radius:24px;padding:28px;box-shadow:0 20px 60px #0008}}
h1{{font-size:clamp(30px,5vw,56px);line-height:1;margin:0 0 12px}} h2{{margin-top:34px;font-size:26px}} h3{{margin:20px 0 8px}} .muted{{color:var(--muted)}}
.stats{{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:14px;margin:20px 0}} .stat{{background:var(--surface);border:1px solid #26345f;border-radius:18px;padding:18px}} .stat b{{display:block;font-size:30px;line-height:1.1}} .stat span{{color:var(--muted)}}
.pills{{display:flex;gap:10px;flex-wrap:wrap;margin-top:16px}} .pill,.tag{{display:inline-flex;align-items:center;border-radius:999px;padding:4px 10px;font-weight:700;font-size:12px}} .pill.good,.tag.good{{background:#123c2a;color:var(--green)}} .pill.bad,.tag.bad{{background:#481821;color:var(--red)}} .pill.caution,.tag.caution{{background:#463817;color:var(--amber)}} .pill.neutral,.tag.neutral{{background:#1c2d52;color:var(--blue)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .card,.callout{{background:var(--surface);border:1px solid #26345f;border-radius:18px;padding:18px;margin:14px 0}} .callout{{border-left:5px solid var(--blue)}} .callout.bad{{border-left-color:var(--red)}} .callout.caution{{border-left-color:var(--amber)}}
table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:16px;overflow:hidden;margin:14px 0}} th,td{{border-bottom:1px solid #26345f;padding:10px 12px;text-align:left;vertical-align:top}} th{{background:#172247;color:#cfe0ff}} tr:last-child td{{border-bottom:0}} code{{color:#a8d8ff}} .event{{margin:0 0 6px;color:#dbe7ff}} .event span{{color:#b8c6e6}} ul{{margin-top:8px}} .bar{{height:12px;background:#243258;border-radius:99px;overflow:hidden}} .bar>i{{display:block;height:100%;background:linear-gradient(90deg,var(--red),var(--amber));}}
@media(max-width:850px){{.stats,.grid{{grid-template-columns:1fr}} table{{font-size:13px}}}}
</style></head><body><main>
<section class='hero'>
  <p class='muted'>GPT-5? no — local-vLLM <b>ThinkingCap-Qwen3.6-27B high</b> · subset 12_v2 · 3 reps · config <code>baseline-thinkingcap-qwen36</code></p>
  <h1>Failure trajectories: mostly non-action, plus Mobly verifier hangs</h1>
  <p>The run completed overnight. The bad-looking cells were not one uniform failure mode: most empty patches came from the model stopping after planning or emitting commands as prose instead of tool calls; the timeouts split into one agent timeout with a high-partial patch and three Mobly verifier timeouts; the single hard failure was a first-response stream that never completed a session file.</p>
  <div class='pills'><span class='pill bad'>13 empty patches</span><span class='pill caution'>4 timeouts</span><span class='pill bad'>1 exit=1</span><span class='pill good'>payload fields validated</span></div>
</section>
<div class='stats'>
  <div class='stat'><b>36</b><span>scheduled cells</span></div>
  <div class='stat'><b>17</b><span>ok cells</span></div>
  <div class='stat'><b>13</b><span>empty patches</span></div>
  <div class='stat'><b>4</b><span>timeouts</span></div>
  <div class='stat'><b>1</b><span>no-result failure</span></div>
</div>
<section class='callout bad'><b>Main diagnosis.</b> ThinkingCap-Qwen3.6 high is not reliably agentic under this clean Pi prompt. The dominant failure is not bad code; it is failure to enter the edit loop. In 12 of 13 empty cells, the model stopped after orientation/planning with no repository modification. Nine empty cells made zero tool calls at all.</section>
<section class='grid'>
 <div class='card'><h2>Failure buckets</h2><ul>{by_class}</ul></div>
 <div class='card'><h2>What the empty patches looked like</h2><ul>
  <li><b>9/13</b> empty cells made no tool calls at all.</li>
  <li><b>5/13</b> printed shell commands inside normal text instead of using the bash tool.</li>
  <li><b>2/13</b> explicitly asked for repo/context even though the repo was mounted at <code>/app</code>.</li>
  <li><b>1/13</b> stopped by length while generating a huge prose block, still with no tool call.</li>
 </ul></div>
</section>
<section class='callout caution'><b>Payload validation is not the culprit.</b> Initial provider requests and stderr debug rows show <code>chat_template_kwargs.preserve_thinking=true</code>, <code>thinking_token_budget=32768</code>, <code>temperature=1</code>, <code>top_p=0.95</code>, <code>top_k=20</code>, and <code>min_p=0</code>. The failure is downstream behavior after a valid request.</section>
<h2>All anomalous trajectories</h2>
<table><thead><tr><th>Cell</th><th>Outcome</th><th>Class</th><th>Partial</th><th>Patch B</th><th>Wall s</th><th>Turns/tools</th><th>Last trajectory evidence</th></tr></thead><tbody>{''.join(html_rows)}</tbody></table>
<h2>Task concentration</h2>
<table><thead><tr><th>Task</th><th>Failure classes</th></tr></thead><tbody>{by_task}</tbody></table>
<section class='callout'><b>Interpretation for next run.</b> If we continue with this model, the next thing to test is not more task coverage. It is a tiny prompt/tool-use calibration: can this model, under Pi, reliably use tools instead of writing tool-shaped prose? A minimal scaffold like “use the available bash/read/edit/write tools; do not print shell commands as markdown” may be necessary, but that would no longer be the clean stock-Pi baseline.</section>
<p class='muted'>Generated from <code>analysis/thinkingcap-qwen36-high-12v2-failures/summary.json</code>.</p>
</main></body></html>"""
(OUT/'index.html').write_text(doc)
print(OUT/'index.html')

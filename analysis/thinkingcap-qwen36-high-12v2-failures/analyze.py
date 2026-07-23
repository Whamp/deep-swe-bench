#!/usr/bin/env python3
import json, pathlib, re, statistics, html
from collections import Counter, defaultdict
ROOT=pathlib.Path('results/ThinkingCap-Qwen3.6-27B/high/baseline-thinkingcap-qwen36')
STATE=pathlib.Path('results/_runs/thinkingcap-qwen36-high-baseline-12v2-r3-w4/status.json')
OUT=pathlib.Path('analysis/thinkingcap-qwen36-high-12v2-failures')

def load_json(p):
    try: return json.loads(p.read_text())
    except Exception: return None

def session_file(cell):
    files=list((cell/'session').glob('*.jsonl'))
    return max(files, key=lambda p:p.stat().st_mtime) if files else None

def read_jsonl(p):
    if not p or not p.exists(): return []
    rows=[]
    for line in p.read_text(errors='ignore').splitlines():
        if line.strip():
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def msg_text(m):
    bits=[]
    for c in m.get('content') or []:
        typ=c.get('type')
        if typ=='text': bits.append(c.get('text',''))
        elif typ=='thinking': bits.append('[thinking] '+c.get('thinking',''))
        elif typ=='toolCall': bits.append('[toolCall] '+c.get('name','')+' '+json.dumps(c.get('arguments',{}))[:500])
    return '\n'.join(bits)

def trajectory(cell):
    sf=session_file(cell)
    rows=read_jsonl(sf)
    turns=0; tools=[]; assistants=[]; last=[]; errors=[]
    for r in rows:
        m=r.get('message') or {}
        role=m.get('role')
        if role=='assistant':
            turns+=1; assistants.append(m)
        elif role=='toolResult':
            tools.append(m.get('toolName'))
            if m.get('isError'): errors.append((m.get('toolName'), str(m.get('content'))[:300]))
    for r in rows[-10:]:
        m=r.get('message') or {}
        role=m.get('role')
        if role=='assistant': last.append({'role':'assistant','text':msg_text(m)[:1200], 'stop':m.get('stopReason')})
        elif role=='toolResult': last.append({'role':'toolResult','tool':m.get('toolName'),'isError':m.get('isError'),'text':str(m.get('content'))[:1200]})
        else: last.append({'type':r.get('type'), 'text':str(r)[:500]})
    return {'session': str(sf) if sf else None, 'events':len(rows), 'assistant_turns':turns, 'tool_calls':len(tools), 'tool_counts':Counter(tools), 'tool_errors':errors[:10], 'last_events':last}

def classify(cell, result, state_cell=None):
    tr=trajectory(cell)
    patch_bytes=(result or {}).get('patch_bytes')
    timed=(result or {}).get('agent_timed_out') or ((state_cell or {}).get('outcome')=='timeout')
    verifier=(result or {}).get('verifier_exit')
    agent_exit=(result or {}).get('agent_exit')
    if result is None:
        rpc=cell/'logs'/'pi-rpc-runner.jsonl'
        rt=rpc.read_text(errors='ignore') if rpc.exists() else ''
        if '"event":"timeout"' in rt and not tr['session']:
            return 'first_completion_hang_no_session'
        return 'harness_failed_no_result'
    if patch_bytes==0:
        if tr['assistant_turns']<=2 and tr['tool_calls']<=3:
            return 'early_stop_after_orientation_no_edit'
        return 'no_diff_after_work'
    if timed:
        if verifier=='timeout': return 'verifier_timeout_after_patch'
        if agent_exit=='timeout' or (result or {}).get('agent_timed_out'): return 'agent_timeout_after_patch'
        return 'timeout_other'
    if (result or {}).get('reward_binary') == -1:
        return 'reward_minus_one_other'
    return 'other'

state=load_json(STATE) or {}
state_cells=state.get('cells') or {}
rows=[]
# include state cells to catch failed no result
for key, sc in sorted(state_cells.items()):
    if sc.get('config')!='baseline-thinkingcap-qwen36': continue
    task=sc.get('task'); rep=sc.get('rep')
    cell=ROOT/task/f'rep{rep}'
    result=load_json(cell/'result.json') if (cell/'result.json').exists() else None
    outcome=sc.get('outcome') or ('missing' if result is None else None)
    if result:
        outcome = outcome or ('timeout' if result.get('agent_timed_out') else 'empty' if result.get('patch_bytes')==0 else 'ok')
    if outcome in {'empty','timeout','failed','missing','exit=1'} or str(outcome).startswith('exit=') or (result and (result.get('patch_bytes')==0 or result.get('agent_timed_out') or result.get('verifier_exit')=='timeout')):
        tr=trajectory(cell)
        cls=classify(cell,result,sc)
        rows.append({'key':key,'task':task,'rep':rep,'outcome':outcome,'class':cls,'result':result,'state':sc,'traj':tr})

summary={'total_problem_rows':len(rows),'by_outcome':Counter(r['outcome'] for r in rows),'by_class':Counter(r['class'] for r in rows)}
# task aggregates
by_task=defaultdict(list)
for r in rows: by_task[r['task']].append(r)
summary['by_task']={k:Counter(x['class'] for x in v) for k,v in by_task.items()}
# serializable counters
summary=json.loads(json.dumps(summary, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))
(OUT/'summary.json').write_text(json.dumps({'summary':summary,'rows':rows}, indent=2, default=lambda o: dict(o) if isinstance(o, Counter) else str(o)))
print(json.dumps(summary, indent=2))

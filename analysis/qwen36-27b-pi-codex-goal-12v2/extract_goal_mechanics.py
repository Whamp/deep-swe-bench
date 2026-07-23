#!/usr/bin/env python3
import csv, glob, json, os, re, statistics
from pathlib import Path

ROOT=Path('results/Qwen3.6-27B-AWQ-BF16-INT4/high')
T=ROOT/'qwen36-27b-pi-codex-goal'; B=ROOT/'baseline-qwen36-27b'
OUT=Path('analysis/qwen36-27b-pi-codex-goal-12v2'); OUT.mkdir(parents=True,exist_ok=True)

def text(c):
    if isinstance(c,str): return c
    if not isinstance(c,list): return ''
    return '\n'.join(x.get('text',x.get('thinking','')) for x in c if isinstance(x,dict))

def load_cell(d):
    r=json.load(open(d/'result.json'))
    sf=next((d/'session').glob('*.jsonl'))
    es=[]
    for n,l in enumerate(open(sf),1):
        x=json.loads(l); x['_line']=n; es.append(x)
    assistants=[]; calls=[]; customs=[]
    for x in es:
        if x.get('type') in ('custom','custom_message') and x.get('customType')=='pi-codex-goal': customs.append(x)
        if x.get('type')=='message' and x.get('message',{}).get('role')=='assistant':
            assistants.append(x)
            for c in x['message'].get('content',[]):
                if isinstance(c,dict) and c.get('type')=='toolCall': calls.append((c.get('name'),x,c))
    create=[z for z in calls if z[0]=='create_goal']; update=[z for z in calls if z[0]=='update_goal']; get=[z for z in calls if z[0]=='get_goal']
    idx={id(x):i+1 for i,x in enumerate(assistants)}
    cturn=idx.get(id(create[0][1])) if create else None
    hidden=[x for x in customs if x.get('details',{}).get('kind')=='continuation']
    budget=[x for x in customs if x.get('details',{}).get('kind')=='budget_limit']
    sets=[x for x in customs if (x.get('data') or {}).get('kind')=='set']
    completed=[x for x in sets if (x.get('data') or {}).get('goal',{}).get('status')=='complete']
    first_user=next((text(x['message'].get('content')) for x in es if x.get('type')=='message' and x.get('message',{}).get('role')=='user'),'')
    expanded_adapter_prompt=(
        'Turn the user task into exactly one durable pi-codex-goal objective' in first_user
        and 'call the goal creation tool' in first_user
    )
    literal_create_goal_command=first_user.lstrip().startswith('/create-goal')
    return dict(r=r,sf=sf,es=es,assistants=assistants,calls=calls,customs=customs,create=create,update=update,get=get,cturn=cturn,hidden=hidden,budget=budget,sets=sets,completed=completed,first_user=first_user,expanded_adapter_prompt=expanded_adapter_prompt,literal_create_goal_command=literal_create_goal_command)

rows=[]; contexts=[]
for rd in sorted(T.glob('*/rep*')):
    if not (rd/'result.json').exists(): continue
    task=rd.parent.name; rep=int(rd.name[3:]); t=load_cell(rd); b=load_cell(B/task/rd.name)
    ur=t['update'][0][1] if t['update'] else None
    # Direct-evidence signals before completion call.
    prior=[]
    if ur:
        for x in t['es']:
            if x['_line']>=ur['_line']: break
            if x.get('type')=='message': prior.append(text(x.get('message',{}).get('content')))
    p='\n'.join(prior).lower()
    tests=bool(re.search(r'(\btest(s|ing)?\b|pytest|go test|npm test|vitest|cargo test)',p))
    build=bool(re.search(r'(\bbuild\b|go build|tsc)',p)); lint=bool(re.search(r'(\blint\b|golangci)',p))
    row={
      'task':task,'rep':rep,'reward':t['r'].get('reward_binary'),'partial':t['r'].get('reward_partial'),
      'timeout':t['r'].get('agent_timed_out'),'agent_wall_s':t['r'].get('agent_wall_s'),'turns':t['r'].get('turns'),'tool_calls':t['r'].get('tool_calls'),
      'baseline_reward':b['r'].get('reward_binary'),'baseline_partial':b['r'].get('reward_partial'),'baseline_timeout':b['r'].get('agent_timed_out'),
      'baseline_wall_s':b['r'].get('agent_wall_s'),'baseline_turns':b['r'].get('turns'),'baseline_tool_calls':b['r'].get('tool_calls'),
      'create_calls':len(t['create']),'create_turn':t['cturn'],'turns_before_create':(t['cturn']-1 if t['cturn'] else None),
      'turns_after_create':(len(t['assistants'])-t['cturn'] if t['cturn'] else None),'get_calls':len(t['get']),'update_calls':len(t['update']),
      'complete_sets':len(t['completed']),'continuations':len(t['hidden']),'budget_limits':len(t['budget']),
      'treatment_initial_literal_slash_command':t['literal_create_goal_command'],
      'treatment_initial_expanded_adapter_prompt':t['expanded_adapter_prompt'],
      'treatment_create_goal_activation':len(t['create'])==1,
      'treatment_goal_event_activation':bool(t['customs']),
      'baseline_initial_expanded_adapter_prompt':b['expanded_adapter_prompt'],
      'baseline_create_goal_calls':len(b['create']),
      'baseline_goal_event_activation':bool(b['customs']),
      'cross_side_goal_leakage':bool(b['expanded_adapter_prompt'] or b['create'] or b['customs']),
      'treatment_delivery_classification':('delivered' if t['expanded_adapter_prompt'] and len(t['create'])==1 and t['customs'] else 'ambiguous'),
      'precomplete_test_signal':tests,'precomplete_build_signal':build,'precomplete_lint_signal':lint,
      'session':str(t['sf'])
    }; rows.append(row)
    if ur:
        pos=t['es'].index(ur); lo=max(0,pos-5); hi=min(len(t['es']),pos+6)
        contexts.append(f"## {task}/rep{rep} — update at entry {ur['id']} line {ur['_line']}\n")
        for x in t['es'][lo:hi]:
            if x.get('type')=='message':
                role=x.get('message',{}).get('role'); tx=text(x.get('message',{}).get('content')).replace('\n',' ')
                names=[c.get('name') for c in x.get('message',{}).get('content',[]) if isinstance(c,dict) and c.get('type')=='toolCall']
                contexts.append(f"- `{x['_line']} {x.get('id')}` **{role}** tools={names}: {tx[:900]}\n")
            elif x.get('customType')=='pi-codex-goal':
                contexts.append(f"- `{x['_line']} {x.get('id')}` **goal event**: {str(x.get('data') or x.get('details'))[:500]}\n")
        contexts.append('\n')
with open(OUT/'goal_mechanics_cells.tsv','w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys(),delimiter='\t');w.writeheader();w.writerows(rows)
(OUT/'completion_contexts.md').write_text(''.join(contexts))
print(json.dumps({'cells':len(rows),'creates':sum(r['create_calls'] for r in rows),'updates':sum(r['update_calls'] for r in rows),'gets':sum(r['get_calls'] for r in rows),'completes':sum(r['complete_sets'] for r in rows),'continuations':sum(r['continuations'] for r in rows),'budget_limits':sum(r['budget_limits'] for r in rows),'timeouts':sum(bool(r['timeout']) for r in rows),'reward_minus1':sum(r['reward']==-1 for r in rows)},indent=2))

#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
BASE=ROOT/'results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b'
TREAT=ROOT/'results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal'
TASKS=ROOT.parent/'deep-swe/tasks'
SUBSET=ROOT/'subsets/12_v2.txt'
DIFFICULTY=ROOT/'data/deepswe-v1.1-task-difficulty.tsv'
URL='http://100.77.237.75:8090/v1/embeddings'
MODEL='octen-embed'


def load(p): return json.loads(p.read_text())
def solved(d): return d.get('reward_binary') == 1

def status(d):
    if d.get('agent_timed_out'): return 'timeout'
    r=d.get('reward_binary')
    if isinstance(r,(int,float)) and r < 0: return 'negative_reward'
    return 'solved' if r == 1 else 'failed'

def outcome(b,t):
    bs,ts=solved(b),solved(t)
    if not bs and ts: return 'gain'
    if bs and not ts: return 'loss'
    if bs and ts: return 'stable_solved'
    return 'stable_failed'

def concise(b,t):
    return (f"Paired rep outcome: {outcome(b,t)}. Baseline {status(b)}, treatment {status(t)}. "
            f"Baseline reward={b.get('reward_binary')}, partial={b.get('reward_partial')}; "
            f"treatment reward={t.get('reward_binary')}, partial={t.get('reward_partial')}. "
            f"Baseline wall={b.get('agent_wall_s')}s, treatment wall={t.get('agent_wall_s')}s; "
            f"baseline turns={b.get('turns')}, treatment turns={t.get('turns')}; "
            f"baseline patch bytes={b.get('patch_bytes')}, treatment patch bytes={t.get('patch_bytes')}."
    )

def embed(texts):
    req=urllib.request.Request(URL,data=json.dumps({'model':MODEL,'input':texts}).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(req,timeout=240) as r: data=json.load(r)
    return [x['embedding'] for x in data['data']],data.get('usage',{})

def cos(a,b):
    dot=sum(x*y for x,y in zip(a,b)); na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(y*y for y in b))
    return dot/(na*nb) if na and nb else 0

def main():
    tasks=[x.strip() for x in SUBSET.read_text().splitlines() if x.strip()]
    with DIFFICULTY.open() as f:
        difficulty={r['slug']:r for r in csv.DictReader(f,delimiter='\t')}
    rows=[]; docs=[]
    for task in tasks:
        prompt=(TASKS/task/'instruction.md').read_text()
        for rep in range(3):
            bp=BASE/task/f'rep{rep}'/'result.json'; tp=TREAT/task/f'rep{rep}'/'result.json'
            b,t=load(bp),load(tp); summary=concise(b,t)
            structural_label = 'treatment_timeout' if status(t) == 'timeout' else ('treatment_negative_reward' if status(t) == 'negative_reward' else outcome(b,t))
            row={'id':f'{task}/rep{rep}','task':task,'rep':rep,'language':b.get('language'),'category':b.get('category'),
                 'outcome':outcome(b,t),'structural_label':structural_label,'baseline_status':status(b),'treatment_status':status(t),
                 'difficulty_pass_rate':float(difficulty[task]['pass_rate']),'repository':difficulty[task]['repository'],'title':difficulty[task]['title'],
                 'baseline_reward':b.get('reward_binary'),'treatment_reward':t.get('reward_binary'),
                 'baseline_partial':b.get('reward_partial'),'treatment_partial':t.get('reward_partial'),
                 'baseline_agent_wall_s':b.get('agent_wall_s'),'treatment_agent_wall_s':t.get('agent_wall_s'),
                 'prompt_chars':len(prompt),'summary':summary}
            rows.append(row); docs.append(prompt+'\n\n'+summary)
    vecs=[]; usages=[]
    for i in range(0,len(docs),8):
        v,u=embed(docs[i:i+8]); vecs.extend(v); usages.append(u)
    dim=len(vecs[0])
    # Cross-task kNN avoids the trivial near-duplicates created by three reps of each prompt.
    for i,row in enumerate(rows):
        nn=sorted(((cos(vecs[i],vecs[j]),j) for j in range(len(rows)) if rows[j]['task']!=row['task']),reverse=True)[:5]
        row['cross_task_neighbors']=[{'id':rows[j]['id'],'structural_label':rows[j]['structural_label'],'cosine':round(s,6)} for s,j in nn]
        row['nearest_same_label_cross_task']=next((round(s,6) for s,j in nn if rows[j]['structural_label']==row['structural_label']),None)
        row['nearest_different_label_cross_task']=next((round(s,6) for s,j in nn if rows[j]['structural_label']!=row['structural_label']),None)
    labels=sorted({r['structural_label'] for r in rows})
    pairs=[]
    for a in labels:
      for b in labels:
       if a>b: continue
       sims=[cos(vecs[i],vecs[j]) for i in range(len(rows)) for j in range(i+1,len(rows)) if rows[i]['task']!=rows[j]['task'] and {rows[i]['structural_label'],rows[j]['structural_label']}=={a,b} and (a!=b or rows[i]['structural_label']==a==rows[j]['structural_label'])]
       if sims: pairs.append({'label_a':a,'label_b':b,'n_cross_task_pairs':len(sims),'mean_cosine':sum(sims)/len(sims),'min_cosine':min(sims),'max_cosine':max(sims)})
    vote_ok=0
    for i,r in enumerate(rows):
        nearest=max(((cos(vecs[i],vecs[j]),j) for j in range(len(rows)) if rows[j]['task']!=r['task']),key=lambda x:x[0])[1]
        vote_ok += rows[nearest]['structural_label']==r['structural_label']
    meta={'endpoint':URL,'model':MODEL,'dimensions':dim,'documents':len(rows),
          'preprocessing':'instruction.md verbatim + deterministic concise paired result summary; no truncation; one document per exact task/rep pair; difficulty metadata joined by TSV slug but not embedded',
          'method':'cosine 5-nearest-neighbor analysis excluding same-task reps; descriptive cross-task within/between structural-label cosine distributions; cross-task nearest-neighbor label agreement',
          'outcome_policy':'reward_binary == 1 only is solved; timeout and reward < 0 remain treatment outcomes; no infrastructure exclusions; results/_contaminated excluded by fixed roots',
          'cross_task_nearest_neighbor_label_agreement':vote_ok/len(rows),'usage':usages,'pair_distributions':pairs}
    (OUT/'embedding_rows.json').write_text(json.dumps({'metadata':meta,'rows':rows},indent=2))
    with (OUT/'embedding_rows.csv').open('w',newline='') as f:
        fields=[k for k in rows[0] if k not in {'neighbors','summary'}]
        w=csv.DictWriter(f,fieldnames=fields); w.writeheader(); w.writerows(({k:r[k] for k in fields} for r in rows))
    (OUT/'embedding_vectors.json').write_text(json.dumps({'model':MODEL,'dimensions':dim,'ids':[r['id'] for r in rows],'vectors':vecs}))
    print(json.dumps(meta,indent=2))
if __name__=='__main__': main()

#!/usr/bin/env python3
from __future__ import annotations
import csv, json, math, random, statistics
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'quantitative.json'
BASE=ROOT/'results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b'
TREAT=ROOT/'results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal'
PRIOR=ROOT/'results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-contract-checkpoints'
TASKS=[x.strip() for x in (ROOT/'subsets/12_v2.txt').read_text().splitlines() if x.strip() and not x.startswith('#')]
REPS=range(3)
METRICS=['reward_partial','f2p','p2p','patch_bytes','turns','tool_calls','total_tokens','combined_total_tokens','cost_usd','combined_cost_usd','agent_wall_s']

def mean(xs):
    ys=[x for x in xs if x is not None]
    return sum(ys)/len(ys) if ys else None

def median(xs):
    ys=[x for x in xs if x is not None]
    return statistics.median(ys) if ys else None

def quantile(xs,q):
    ys=sorted(xs); p=(len(ys)-1)*q; lo=math.floor(p); hi=math.ceil(p)
    return ys[lo] if lo==hi else ys[lo]+(ys[hi]-ys[lo])*(p-lo)

def bootstrap_mean_ci(ds, seed, n=10000):
    vals=[x for x in ds if x is not None]
    if not vals:return None
    rng=random.Random(seed); means=[]; m=len(vals)
    for _ in range(n): means.append(sum(vals[rng.randrange(m)] for _ in range(m))/m)
    return [quantile(means,.025),quantile(means,.975)]

def exact_sign_p(losses,gains):
    n=losses+gains
    if not n:return None
    k=min(losses,gains)
    return min(1.0,2*sum(math.comb(n,i) for i in range(k+1))/(2**n))

def metadata():
    out={}
    with (ROOT/'data/deepswe-v1.1-task-difficulty.tsv').open() as f:
        for r in csv.DictReader(f,delimiter='\t'):
            if r['slug'] in TASKS:
                pr=float(r['pass_rate'])
                out[r['slug']]={'pass_rate':pr,'difficulty':'hard' if pr<33 else 'medium' if pr<66 else 'easy','language':r['language'],'slug':r['slug'],'repository':r['repository'],'title':r['title']}
    if set(out)!=set(TASKS): raise RuntimeError('difficulty join incomplete')
    return out

def load(root):
    out={}
    for task in TASKS:
        for rep in REPS:
            p=root/task/f'rep{rep}'/'result.json'
            if not p.exists(): raise RuntimeError(f'missing {p}')
            r=json.loads(p.read_text())
            if r.get('task')!=task or r.get('rep')!=rep: raise RuntimeError(f'identity mismatch {p}')
            if '_contaminated' in p.parts: raise RuntimeError(f'contaminated {p}')
            out[(task,rep)]=r|{'result_path':str(p.relative_to(ROOT))}
    if len(out)!=36: raise RuntimeError(f'expected 36 cells, got {len(out)}')
    return out

def rate_summary(rows):
    def weighted(prefix):
        passed=sum(r.get(prefix+'_passed') or 0 for r in rows); total=sum(r.get(prefix+'_total') or 0 for r in rows)
        return {'passed':passed,'total':total,'rate':passed/total if total else None,'graded_cells':sum(r.get(prefix) is not None for r in rows)}
    result={'n':len(rows),'solves':sum(r.get('reward_binary')==1 for r in rows),'solve_rate':sum(r.get('reward_binary')==1 for r in rows)/len(rows),
      'reward_minus_one':sum(r.get('reward_binary')==-1 or r.get('reward_partial')==-1 for r in rows),
      'agent_timeouts':sum(bool(r.get('agent_timed_out')) for r in rows),
      'any_timeout':sum(bool(r.get('agent_timed_out')) or r.get('agent_exit')=='timeout' or r.get('verifier_exit')=='timeout' for r in rows),
      'f2p_weighted':weighted('f2p'),'p2p_weighted':weighted('p2p')}
    for m in METRICS:
        vals=[r.get(m) for r in rows]
        result[m]={'available_n':sum(x is not None for x in vals),'mean':mean(vals),'median':median(vals),'sum':sum(x for x in vals if x is not None)}
    return result

def paired(a,b,label):
    cells=[]
    for i,key in enumerate((t,r) for t in TASKS for r in REPS):
        ar,br=a[key],b[key]; task,rep=key
        c={'task':task,'rep':rep,'baseline_solved':ar.get('reward_binary')==1,'comparison_solved':br.get('reward_binary')==1,
           'baseline_reward_binary':ar.get('reward_binary'),'comparison_reward_binary':br.get('reward_binary'),
           'baseline_timeout':bool(ar.get('agent_timed_out')) or ar.get('agent_exit')=='timeout' or ar.get('verifier_exit')=='timeout',
           'comparison_timeout':bool(br.get('agent_timed_out')) or br.get('agent_exit')=='timeout' or br.get('verifier_exit')=='timeout'}
        for m in METRICS:
            av,bv=ar.get(m),br.get(m); c[m]={'baseline':av,'comparison':bv,'delta':bv-av if av is not None and bv is not None else None}
        cells.append(c)
    gains=sum(c['comparison_solved'] and not c['baseline_solved'] for c in cells); losses=sum(c['baseline_solved'] and not c['comparison_solved'] for c in cells)
    deltas={}
    for j,m in enumerate(METRICS):
        ds=[c[m]['delta'] for c in cells if c[m]['delta'] is not None]
        deltas[m]={'paired_n':len(ds),'mean':mean(ds),'median':median(ds),'sum':sum(ds),'bootstrap_95_ci_mean':bootstrap_mean_ci(ds,8675309+j)}
    return {'label':label,'n_pairs':36,'baseline':rate_summary(list(a.values())),'comparison':rate_summary(list(b.values())),
      'solve_churn':{'both_solved':sum(c['baseline_solved'] and c['comparison_solved'] for c in cells),'neither_solved':sum(not c['baseline_solved'] and not c['comparison_solved'] for c in cells),'baseline_only_losses':losses,'comparison_only_gains':gains,'net_solve_delta':gains-losses,'exact_mcnemar_p_two_sided':exact_sign_p(losses,gains)},
      'paired_deltas_comparison_minus_baseline':deltas,'cells':cells}

def group_view(cells,keyfn):
    out={}
    for c in cells: out.setdefault(str(keyfn(c)),[]).append(c)
    return {k:{'n':len(cs),'baseline_solves':sum(c['baseline_solved'] for c in cs),'comparison_solves':sum(c['comparison_solved'] for c in cs),'solve_delta':sum(c['comparison_solved']-c['baseline_solved'] for c in cs),'mean_partial_delta':mean([c['reward_partial']['delta'] for c in cs])} for k,cs in out.items()}

def main():
    meta=metadata(); base=load(BASE); treat=load(TREAT); primary=paired(base,treat,'pi-codex-goal vs clean stock Pi')
    for c in primary['cells']: c.update(meta[c['task']])
    primary['per_rep']=group_view(primary['cells'],lambda c:c['rep'])
    primary['by_difficulty']=group_view(primary['cells'],lambda c:c['difficulty'])
    primary['by_language']=group_view(primary['cells'],lambda c:c['language'])
    primary['task_level']=group_view(primary['cells'],lambda c:c['task'])
    primary['solve_flips']=[c for c in primary['cells'] if c['baseline_solved']!=c['comparison_solved']]
    complete=[c for c in primary['cells'] if not c['baseline_timeout'] and not c['comparison_timeout'] and c['baseline_reward_binary']!=-1 and c['comparison_reward_binary']!=-1]
    primary['sensitivity']={'primary_policy':'All 36 pairs retained; timeout and reward=-1 are observed outcomes.',
      'complete_pair_view_non_primary':{'n':len(complete),'excluded_n':36-len(complete),'excluded_cells':[{'task':c['task'],'rep':c['rep'],'baseline_timeout':c['baseline_timeout'],'comparison_timeout':c['comparison_timeout'],'baseline_reward_binary':c['baseline_reward_binary'],'comparison_reward_binary':c['comparison_reward_binary']} for c in primary['cells'] if c not in complete],
      'baseline_solves':sum(c['baseline_solved'] for c in complete),'comparison_solves':sum(c['comparison_solved'] for c in complete),'mean_partial_delta':mean([c['reward_partial']['delta'] for c in complete])}}
    prior=None
    try:
        p=load(PRIOR); prior=paired(base,p,'prompt-only contract-checkpoints vs clean stock Pi (secondary)')
        prior={'artifact_status':'complete_clean_36_cell_join','summary':{k:v for k,v in prior.items() if k!='cells'}}
    except Exception as e: prior={'artifact_status':'not_used','reason':str(e)}
    doc={'schema_version':1,'comparison':{'model':'local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4','thinking':'high','subset':'12_v2','reps':[0,1,2],'baseline_root':str(BASE.relative_to(ROOT)),'comparison_root':str(TREAT.relative_to(ROOT)),'join_keys':['task slug','rep'],'expected_pairs':36,'actual_pairs':36,'contaminated_excluded':True,'wall_field':'agent_wall_s'},
      'methods':{'bootstrap':'paired cell resampling, 10000 draws, deterministic Python random seeds 8675309+metric index, percentile 95% CI','binary_test':'exact two-sided McNemar/binomial test over discordant solve pairs','missing_rates':'f2p/p2p aggregate weighted rates use passed/total only where graded; missing timeout rates stay visible via graded_cells and failure counts','delta_direction':'comparison minus baseline'},
      'primary':primary,'secondary_context':prior}
    OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(doc,indent=2,sort_keys=True)+'\n'); print(OUT)
if __name__=='__main__': main()

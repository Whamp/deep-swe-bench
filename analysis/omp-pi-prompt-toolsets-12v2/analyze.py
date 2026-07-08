#!/usr/bin/env python3
from __future__ import annotations

import csv, json, math, statistics as st, sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
RESULT_ROOT = ROOT / 'results/gpt-5.5/low'
SUBSET = '12_v2'
TASKS = [x.strip() for x in (ROOT / f'subsets/{SUBSET}.txt').read_text().splitlines() if x.strip() and not x.startswith('#')]
REPS = [0,1,2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'analysis/harness-forensics'))
from extract_session import extract  # type: ignore

CONFIGS = [
    'baseline',
    'baseline-omp',
    'baseline-omp-bash-only',
    'baseline-omp-ast',
    'baseline-omp-pi-prompt-bash-only',
    'baseline-omp-pi-prompt-grepglob',
    'baseline-omp-pi-prompt-ast',
]
LABEL = {
    'baseline': 'Pi clean baseline',
    'baseline-omp': 'OMP default · grep/glob',
    'baseline-omp-bash-only': 'OMP default · bash-only',
    'baseline-omp-ast': 'OMP default · AST',
    'baseline-omp-pi-prompt-bash-only': 'OMP Pi-like · bash-only',
    'baseline-omp-pi-prompt-grepglob': 'OMP Pi-like · grep/glob',
    'baseline-omp-pi-prompt-ast': 'OMP Pi-like · AST',
}
NEW_CONFIGS = [
    'baseline-omp-pi-prompt-bash-only',
    'baseline-omp-pi-prompt-grepglob',
    'baseline-omp-pi-prompt-ast',
]

DIFF = {}
with open(ROOT / 'data/deepswe-v1.1-task-difficulty.tsv') as f:
    for r in csv.DictReader(f, delimiter='\t'):
        pr = float(r['pass_rate'])
        bucket = 'hard' if pr < 33 else 'medium' if pr < 66 else 'easy'
        DIFF[r['slug']] = {'pass_rate': pr, 'bucket': bucket, 'language': r['language'], 'title': r['title']}

def median(xs):
    xs=[x for x in xs if x is not None]
    return st.median(xs) if xs else None

def mean(xs):
    xs=[x for x in xs if x is not None]
    return st.mean(xs) if xs else None

def load_result(config, task, rep):
    p=RESULT_ROOT/config/task/f'rep{rep}'/'result.json'
    if not p.exists():
        return None
    r=json.load(open(p))
    r['_path']=str(p)
    r['_config']=config
    r['_task']=task
    r['_rep']=rep
    return r

def session_path(config, task, rep):
    d=RESULT_ROOT/config/task/f'rep{rep}'/'session'
    files=sorted(d.glob('*.jsonl'))
    return files[0] if files else None

def load_cell(config, task, rep):
    r=load_result(config, task, rep)
    if not r: return None
    sp=session_path(config, task, rep)
    sx={}
    if sp:
        try: sx=extract(str(sp))
        except Exception as e: sx={'extract_error': str(e)}
    return {'result': r, 'session': sx, 'config': config, 'task': task, 'rep': rep, 'difficulty': DIFF.get(task,{})}

cells=[]
by_key={}
missing=[]
for c in CONFIGS:
    for t in TASKS:
        for rep in REPS:
            cell=load_cell(c,t,rep)
            if cell is None:
                missing.append((c,t,rep))
            else:
                cells.append(cell); by_key[(c,t,rep)]=cell

NUM_RESULT_KEYS=['reward_partial','combined_total_tokens','combined_cost_usd','agent_wall_s','turns','tool_calls','patch_bytes','f2p_total','f2p_passed','p2p_total','p2p_passed']
SESSION_SUM_KEYS=['sum_cacheRead','sum_input','sum_output','sum_reasoningTokens','total_result_bytes','tool_failures','assistant_turns','tool_call_count']

def summarize(config):
    cs=[by_key[(config,t,r)] for t in TASKS for r in REPS if (config,t,r) in by_key]
    rs=[c['result'] for c in cs]
    ss=[c['session'] for c in cs]
    out={
        'config':config,'label':LABEL[config], 'n': len(cs), 'distinct_tasks': len({c['task'] for c in cs}),
        'solves': sum(1 for r in rs if r.get('reward_binary')==1),
        'reward_minus_1': sum(1 for r in rs if r.get('reward_binary')==-1),
        'timeouts': sum(1 for r in rs if r.get('agent_timed_out')),
        'empty_patches': sum(1 for r in rs if (r.get('patch_bytes') or 0)==0),
        'mean_partial': mean([r.get('reward_partial') for r in rs]),
        'median_partial': median([r.get('reward_partial') for r in rs]),
        'total_cost': sum(r.get('combined_cost_usd') or r.get('cost_usd') or 0 for r in rs),
    }
    for k in NUM_RESULT_KEYS:
        vals=[r.get(k) for r in rs]
        out[f'median_{k}']=median(vals)
        out[f'mean_{k}']=mean(vals)
        if k in ['combined_total_tokens','combined_cost_usd','agent_wall_s','turns','tool_calls','patch_bytes','f2p_total','f2p_passed','p2p_total','p2p_passed']:
            out[f'sum_{k}']=sum(v or 0 for v in vals)
    # Derived f2p/p2p rates.
    out['f2p_rate']=(out['sum_f2p_passed']/out['sum_f2p_total']) if out.get('sum_f2p_total') else None
    out['p2p_rate']=(out['sum_p2p_passed']/out['sum_p2p_total']) if out.get('sum_p2p_total') else None
    for k in SESSION_SUM_KEYS:
        out[f'sum_{k}']=sum(s.get(k) or 0 for s in ss)
        out[f'median_{k}']=median([s.get(k) for s in ss])
    out['median_non_message_tokens_t1']=median([s.get('non_message_tokens_t1') for s in ss])
    out['non_message_tokens_values']=sorted(set(s.get('non_message_tokens_t1') for s in ss if s.get('non_message_tokens_t1') is not None))
    tool_counts=Counter()
    custom_counts=Counter()
    for s in ss:
        tool_counts.update(s.get('tool_counts') or {})
        custom_counts.update(s.get('custom_events') or {})
    out['tool_counts']=dict(sorted(tool_counts.items()))
    out['custom_events']=dict(sorted(custom_counts.items()))
    out['omp_tools']=rs[0].get('omp_tools') if rs else None
    out['omp_system_prompt_override']=rs[0].get('omp_system_prompt_override') if rs else None
    out['omp_system_prompt_chars']=rs[0].get('omp_system_prompt_chars') if rs else None
    out['agent']=rs[0].get('agent') or 'pi'
    return out

try:
    from scipy.stats import wilcoxon, ttest_rel
except Exception:
    wilcoxon=ttest_rel=None

def exact_mcnemar(b_only, o_only):
    # two-sided exact binomial over discordant cells
    n=b_only+o_only
    if n==0: return 1.0
    from math import comb
    k=min(b_only,o_only)
    p=2*sum(comb(n,i)*(0.5**n) for i in range(k+1))
    return min(1.0,p)

def paired(base, other):
    pairs=[]
    for t in TASKS:
        for rep in REPS:
            a=by_key.get((base,t,rep)); b=by_key.get((other,t,rep))
            if a and b: pairs.append((a,b))
    def rv(c,k): return c['result'].get(k)
    deltas=[(rv(b,'reward_partial') or 0)-(rv(a,'reward_partial') or 0) for a,b in pairs]
    cost_d=[(rv(b,'combined_cost_usd') or rv(b,'cost_usd') or 0)-(rv(a,'combined_cost_usd') or rv(a,'cost_usd') or 0) for a,b in pairs]
    tok_d=[(rv(b,'combined_total_tokens') or rv(b,'total_tokens') or 0)-(rv(a,'combined_total_tokens') or rv(a,'total_tokens') or 0) for a,b in pairs]
    wall_d=[(rv(b,'agent_wall_s') or 0)-(rv(a,'agent_wall_s') or 0) for a,b in pairs]
    turns_d=[(rv(b,'turns') or 0)-(rv(a,'turns') or 0) for a,b in pairs]
    base_sol=sum(1 for a,b in pairs if rv(a,'reward_binary')==1)
    oth_sol=sum(1 for a,b in pairs if rv(b,'reward_binary')==1)
    both=sum(1 for a,b in pairs if rv(a,'reward_binary')==1 and rv(b,'reward_binary')==1)
    base_only=sum(1 for a,b in pairs if rv(a,'reward_binary')==1 and rv(b,'reward_binary')!=1)
    other_only=sum(1 for a,b in pairs if rv(a,'reward_binary')!=1 and rv(b,'reward_binary')==1)
    neither=sum(1 for a,b in pairs if rv(a,'reward_binary')!=1 and rv(b,'reward_binary')!=1)
    out={
        'base':base,'other':other,'base_label':LABEL[base],'other_label':LABEL[other], 'n':len(pairs),
        'base_solves':base_sol,'other_solves':oth_sol,'solve_delta':oth_sol-base_sol,
        'both_solved':both,'base_only':base_only,'other_only':other_only,'neither':neither,
        'mean_delta_partial':mean(deltas),'median_delta_partial':median(deltas),
        'median_delta_cost':median(cost_d),'mean_delta_cost':mean(cost_d),
        'median_delta_tokens':median(tok_d),'mean_delta_tokens':mean(tok_d),
        'median_delta_wall_s':median(wall_d),'median_delta_turns':median(turns_d),
        'improved_cells':sum(1 for d in deltas if d>1e-9),'worsened_cells':sum(1 for d in deltas if d<-1e-9),'tied_cells':sum(1 for d in deltas if abs(d)<=1e-9),
        'mcnemar_p':exact_mcnemar(base_only, other_only),
    }
    if wilcoxon and any(abs(d)>1e-12 for d in deltas):
        try: out['wilcoxon_partial_p']=float(wilcoxon(deltas, zero_method='wilcox').pvalue)
        except Exception: out['wilcoxon_partial_p']=None
    else: out['wilcoxon_partial_p']=None
    if ttest_rel:
        # rep-level solve and partial deltas (3 samples), useful directional hints only.
        rep_solve=[]; rep_partial=[]
        for rep in REPS:
            ps=[(by_key[(other,t,rep)]['result'].get('reward_partial') or 0) - (by_key[(base,t,rep)]['result'].get('reward_partial') or 0) for t in TASKS if (base,t,rep) in by_key and (other,t,rep) in by_key]
            rep_partial.append(mean(ps))
            rep_solve.append(sum(1 for t in TASKS if by_key.get((other,t,rep),{}).get('result',{}).get('reward_binary')==1) - sum(1 for t in TASKS if by_key.get((base,t,rep),{}).get('result',{}).get('reward_binary')==1))
        out['rep_solve_delta']=rep_solve; out['rep_partial_delta']=rep_partial
        try: out['rep_partial_ttest_p']=float(ttest_rel(rep_partial,[0]*len(rep_partial)).pvalue)
        except Exception: out['rep_partial_ttest_p']=None
    # difficulty
    diff={}
    for bucket in ['hard','medium','easy']:
        sub=[(a,b) for a,b in pairs if (a['difficulty'] or {}).get('bucket')==bucket]
        ds=[(rv(b,'reward_partial') or 0)-(rv(a,'reward_partial') or 0) for a,b in sub]
        diff[bucket]={
            'n':len(sub),'base_solves':sum(1 for a,b in sub if rv(a,'reward_binary')==1),'other_solves':sum(1 for a,b in sub if rv(b,'reward_binary')==1),
            'solve_delta':sum(1 for a,b in sub if rv(b,'reward_binary')==1)-sum(1 for a,b in sub if rv(a,'reward_binary')==1),
            'mean_delta_partial':mean(ds),'median_delta_cost':median([(rv(b,'combined_cost_usd') or 0)-(rv(a,'combined_cost_usd') or 0) for a,b in sub]),
        }
    out['difficulty']=diff
    movers=[]
    for a,b in pairs:
        d=(rv(b,'reward_partial') or 0)-(rv(a,'reward_partial') or 0)
        movers.append({'task':a['task'],'rep':a['rep'],'title':(a['difficulty'] or {}).get('title',a['task']),'difficulty':(a['difficulty'] or {}).get('bucket'),'base_partial':rv(a,'reward_partial'),'other_partial':rv(b,'reward_partial'),'delta_partial':d,'base_solved':rv(a,'reward_binary')==1,'other_solved':rv(b,'reward_binary')==1,'delta_cost':(rv(b,'combined_cost_usd') or 0)-(rv(a,'combined_cost_usd') or 0),'delta_tokens':(rv(b,'combined_total_tokens') or 0)-(rv(a,'combined_total_tokens') or 0)})
    out['top_wins']=sorted(movers,key=lambda x:x['delta_partial'], reverse=True)[:12]
    out['top_losses']=sorted(movers,key=lambda x:x['delta_partial'])[:12]
    return out

summaries={c:summarize(c) for c in CONFIGS}
pairs={
    'pi_prompt_bash_vs_pi': paired('baseline','baseline-omp-pi-prompt-bash-only'),
    'pi_prompt_grepglob_vs_pi': paired('baseline','baseline-omp-pi-prompt-grepglob'),
    'pi_prompt_ast_vs_pi': paired('baseline','baseline-omp-pi-prompt-ast'),
    'pi_prompt_grepglob_vs_bash': paired('baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-grepglob'),
    'pi_prompt_ast_vs_bash': paired('baseline-omp-pi-prompt-bash-only','baseline-omp-pi-prompt-ast'),
    'pi_prompt_grepglob_vs_default_omp': paired('baseline-omp','baseline-omp-pi-prompt-grepglob'),
    'pi_prompt_bash_vs_default_bash': paired('baseline-omp-bash-only','baseline-omp-pi-prompt-bash-only'),
    'pi_prompt_ast_vs_default_ast': paired('baseline-omp-ast','baseline-omp-pi-prompt-ast'),
}

# Task-level solve table for configs of interest.
task_rows=[]
for t in TASKS:
    row={'task':t, **DIFF.get(t,{})}
    for c in CONFIGS:
        vals=[by_key[(c,t,r)]['result'].get('reward_binary') for r in REPS if (c,t,r) in by_key]
        parts=[by_key[(c,t,r)]['result'].get('reward_partial') for r in REPS if (c,t,r) in by_key]
        row[f'{c}_solves']=sum(1 for v in vals if v==1)
        row[f'{c}_mean_partial']=mean(parts)
    task_rows.append(row)

# Health checks.
health={
    'run_id':'omp-pi-prompt-toolsets-12v2-r3-w24',
    'missing': missing,
    'new_result_count': sum(summaries[c]['n'] for c in NEW_CONFIGS),
    'new_expected': len(NEW_CONFIGS)*len(TASKS)*len(REPS),
    'new_failures': {c:{'reward_minus_1':summaries[c]['reward_minus_1'], 'timeouts':summaries[c]['timeouts'], 'empty_patches':summaries[c]['empty_patches']} for c in NEW_CONFIGS},
}

out={'subset':SUBSET,'tasks':TASKS,'configs':CONFIGS,'new_configs':NEW_CONFIGS,'labels':LABEL,'summaries':summaries,'pairs':pairs,'task_rows':task_rows,'health':health}
(OUT/'summary.json').write_text(json.dumps(out,indent=2))
print(json.dumps({c:{k:summaries[c][k] for k in ['n','solves','mean_partial','median_combined_cost_usd','median_combined_total_tokens','median_agent_wall_s','median_tool_calls','reward_minus_1']} for c in CONFIGS}, indent=2))

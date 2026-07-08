#!/usr/bin/env python3
"""Run a full harness-vs-harness forensic comparison between two result trees.

Deterministic, pure-Python, no model calls. This is STAGE 1 of the repeatable
harness-forensics pipeline. STAGE 2 (qualitative characterization) is the
workflow in harness_forensics.workflow.mjs, which consumes this script's output.

Given two configs (e.g. baseline vs baseline-omp) under a results root and a
subset task list, this:
  1. extracts per-cell forensics (extract_session.extract) for every cell of
     both configs whose task is in the subset,
  2. writes all_cells.json + per_pair.json to --out,
  3. prints an aggregate comparison table (turns, tool calls, failures, cacheRead,
     tokens, solves) and per-task rows,
  4. writes workflow_args.json so the characterization workflow can be re-run with
     matching parameters.

Result-path convention: <root>/<config>/<task>/rep<N>/  with session/*.jsonl
and result.json. ``--root`` typically encodes model + thinking, e.g.
results/gpt-5.5/low.

Usage:
  python3 run_analysis.py \
      --a baseline --label-a Pi \
      --b baseline-omp --label-b OMP \
      --root results/gpt-5.5/low \
      --subset 36_v2 \
      --out analysis/omp-vs-pi-36v2
"""
import argparse, json, glob, os, sys
from collections import defaultdict
import statistics as st

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_session import extract

NUM_KEYS = ('assistant_turns', 'tool_call_count', 'tool_failures', 'retries_approx',
            'read_rereads_approx', 'sum_cacheRead', 'sum_input', 'sum_output',
            'sum_reasoningTokens', 'max_result_bytes', 'median_result_bytes', 'total_result_bytes')
SUM_KEYS = ('assistant_turns', 'tool_call_count', 'tool_failures', 'sum_cacheRead',
            'sum_input', 'sum_output', 'sum_reasoningTokens', 'total_result_bytes', 'retries_approx')


def load_subset(name, repo_root='.'):
    p = os.path.join(repo_root, 'subsets', f'{name}.txt')
    with open(p) as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.startswith('#')]


def cells_for(root, config, tasks, max_reps=None):
    """Return list of (task, rep, summary_dict, result_json) for cells whose task is in tasks."""
    out = []
    for task in tasks:
        rep_dirs = sorted(glob.glob(os.path.join(root, config, task, 'rep*')))
        if max_reps is not None:
            rep_dirs = rep_dirs[:max_reps]
        for rd in rep_dirs:
            sessions = sorted(glob.glob(os.path.join(rd, 'session', '*.jsonl')))
            rj_path = os.path.join(rd, 'result.json')
            result_json = json.load(open(rj_path)) if os.path.exists(rj_path) else {}
            if not sessions:
                continue
            try:
                d = extract(sessions[0])
            except Exception as e:
                d = {'error': str(e)}
            rep = os.path.basename(rd)
            d.update({'config': config, 'task': task, 'rep': rep})
            d['result'] = {k: result_json.get(k) for k in
                           ('reward_binary', 'reward_partial', 'apply_failed', 'total_tokens',
                            'turns', 'tool_calls', 'patch_bytes', 'agent_wall_s')}
            out.append(d)
    return out


def median_map(cells, key):
    vals = [c[key] for c in cells if 'error' not in c and key in c and c[key] is not None]
    return st.median(vals) if vals else 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True, help='config A result dir name (e.g. baseline)')
    ap.add_argument('--b', required=True, help='config B result dir name (e.g. baseline-omp)')
    ap.add_argument('--label-a', default=None)
    ap.add_argument('--label-b', default=None)
    ap.add_argument('--root', default='results/gpt-5.5/low')
    ap.add_argument('--subset', required=True)
    ap.add_argument('--reps', type=int, default=None, help='cap reps per task')
    ap.add_argument('--out', required=True)
    ap.add_argument('--repo-root', default='.')
    args = ap.parse_args()

    labelA = args.label_a or args.a
    labelB = args.label_b or args.b
    tasks = load_subset(args.subset, args.repo_root)
    os.makedirs(args.out, exist_ok=True)
    summaries_dir = os.path.join(args.out, 'summaries')
    os.makedirs(summaries_dir, exist_ok=True)

    cells_a = cells_for(args.root, args.a, tasks, args.reps)
    cells_b = cells_for(args.root, args.b, tasks, args.reps)
    all_cells = cells_a + cells_b
    json.dump(all_cells, open(os.path.join(summaries_dir, 'all_cells.json'), 'w'), indent=1)

    # per-pair medians
    pairs = {}
    for t in tasks:
        ca = [c for c in cells_a if c['task'] == t and 'error' not in c]
        cb = [c for c in cells_b if c['task'] == t and 'error' not in c]
        pairs[t] = {
            args.a: {k: median_map(ca, k) for k in NUM_KEYS},
            args.b: {k: median_map(cb, k) for k in NUM_KEYS},
            f'{args.b}_overhead_tokens': median_map(cb, 'non_message_tokens_t1'),
            f'{args.a}_overhead_tokens': median_map(ca, 'non_message_tokens_t1'),
        }
    json.dump(pairs, open(os.path.join(summaries_dir, 'per_pair.json'), 'w'), indent=1)

    # aggregate totals + solves
    def agg(cells):
        solves = sum(1 for c in cells if c.get('result', {}).get('reward_binary') == 1)
        crashes = sum(1 for c in cells if c.get('result', {}).get('reward_binary') == -1)
        partials = [c.get('result', {}).get('reward_partial') for c in cells if c.get('result', {}).get('reward_partial') is not None]
        return {
            'n': len(cells),
            'solves': solves,
            'crashes': crashes,
            'mean_partial': st.mean(partials) if partials else 0,
            **{k: sum(c.get(k, 0) or 0 for c in cells if 'error' not in c) for k in SUM_KEYS},
        }
    A, B = agg(cells_a), agg(cells_b)

    # per-task table
    print(f"\n{'='*100}\n{labelA} ({args.a}) vs {labelB} ({args.b}) on subset {args.subset} ({len(tasks)} tasks)\n{'='*100}")
    print(f"\n{'task':42s} {'trn A/B':>9s} {'tc A/B':>9s} {'fail A/B':>9s} {'cacheRead A/B':>17s} {'overhd B':>8s}")
    for t in tasks:
        pa, pb = pairs[t].get(args.a, {}), pairs[t].get(args.b, {})
        oh = pairs[t].get(f'{args.b}_overhead_tokens') or '?'
        print(f"{t[:42]:42s} {int(pa.get('assistant_turns',0))}/{int(pb.get('assistant_turns',0)):>3d}   "
              f"{int(pa.get('tool_call_count',0))}/{int(pb.get('tool_call_count',0)):>3d}   "
              f"{int(pa.get('tool_failures',0))}/{int(pb.get('tool_failures',0)):>3d}   "
              f"{int(pa.get('sum_cacheRead',0)):>7,}/{int(pb.get('sum_cacheRead',0)):>7,}   {str(oh):>8s}")

    # tool mix
    def toolmix(cells):
        tc = defaultdict(int)
        for c in cells:
            if 'error' in c: continue
            for k, v in (c.get('tool_counts') or {}).items(): tc[k] += v
        return tc
    ta, tb = toolmix(cells_a), toolmix(cells_b)
    tools = sorted(set(ta) | set(tb))

    print(f"\n--- AGGREGATE ({args.reps or 'all'} reps) ---")
    print(f"{'metric':28s} {labelA:>16s} {labelB:>16s} {'ratio':>7s}")
    def row(name, va, vb, fmt='{:,.0f}'):
        r = (vb / va) if va else float('inf')
        print(f"  {name:26s} {fmt.format(va):>16s} {fmt.format(vb):>16s} {r:>6.2f}x")
    row('cells', A['n'], B['n'], '{:d}')
    row('solves', A['solves'], B['solves'], '{:d}')
    row('crashes (reward=-1)', A['crashes'], B['crashes'], '{:d}')
    print(f"  {'mean_partial':26s} {A['mean_partial']:>16.4f} {B['mean_partial']:>16.4f}")
    row('assistant_turns', A['assistant_turns'], B['assistant_turns'], '{:d}')
    row('tool_calls', A['tool_call_count'], B['tool_call_count'], '{:d}')
    row('tool_failures', A['tool_failures'], B['tool_failures'], '{:d}')
    row('cacheRead_tokens', A['sum_cacheRead'], B['sum_cacheRead'])
    row('input_tokens', A['sum_input'], B['sum_input'])
    row('output_tokens', A['sum_output'], B['sum_output'])
    row('reasoning_tokens', A['sum_reasoningTokens'], B['sum_reasoningTokens'])
    row('tool_result_bytes', A['total_result_bytes'], B['total_result_bytes'])

    print(f"\n--- TOOL MIX ({labelA} / {labelB}) ---")
    for tk in tools:
        print(f"  {tk:8s} {ta[tk]:>8d} / {tb[tk]:<8d} (delta {tb[tk]-ta[tk]:+d})")

    print(f"\noutputs: {summaries_dir}/{{all_cells,per_pair}}.json")

    # emit workflow args so STAGE 2 can be run with matching parameters
    wargs = {
        'configA': args.a, 'configB': args.b, 'labelA': labelA, 'labelB': labelB,
        'root': args.root, 'subset': args.subset, 'reps': args.reps,
        'out': os.path.abspath(args.out), 'tasks': tasks,
        'perPairPath': os.path.abspath(os.path.join(summaries_dir, 'per_pair.json')),
    }
    json.dump(wargs, open(os.path.join(summaries_dir, 'workflow_args.json'), 'w'), indent=2)
    print(f"workflow args: {summaries_dir}/workflow_args.json (pass to harness_forensics.workflow.mjs)")


if __name__ == '__main__':
    main()

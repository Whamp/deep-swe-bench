#!/usr/bin/env python3
"""Extract compact per-cell forensic summary from a Pi/OMP session JSONL.

Outputs JSON with: turns, per-tool call counts, tool failures (isError),
retries (same tool+approx-args repeats), file reads + re-reads, background /
extra model calls, per-turn usage, harness-overhead (nonMessageTokens) trajectory.

Handles both the Pi baseline (no contextSnapshot/providerPayload) and the OMP
baseline (rich providerPayload/contextSnapshot) session formats.
"""
import json, sys, glob, os, hashlib
from collections import Counter, defaultdict

def extract(session_path):
    turns = []
    tool_calls = []          # (name, args_str, toolCallId)
    tool_results = []        # dict(name, isError, size, toolCallId)
    custom_events = Counter()
    custom_tool_intents = []
    non_msg_tokens = []
    usage_per_turn = []
    models_seen = set()
    assistant_count = 0
    has_context_snapshot = False
    has_provider_payload = False
    # background / extra call detection
    extra_model_events = 0   # any assistant-like call not part of main loop

    for line in open(session_path):
        line = line.strip()
        if not line:
            continue
        try:
            e = json.loads(line)
        except Exception:
            continue
        t = e.get('type')
        if t == 'custom':
            ct = e.get('customType', '?')
            custom_events[ct] += 1
            if ct == 'tool_execution_start':
                d = e.get('data', {})
                custom_tool_intents.append({'tool': d.get('toolName'), 'intent': d.get('intent')})
            continue
        if t != 'message':
            continue
        m = e.get('message', e)
        role = m.get('role')
        if role == 'assistant':
            assistant_count += 1
            models_seen.add(m.get('model', '?'))
            cs = m.get('contextSnapshot')
            if cs is not None:
                has_context_snapshot = True
                non_msg_tokens.append(cs.get('nonMessageTokens'))
            if m.get('providerPayload'):
                has_provider_payload = True
            u = m.get('usage', {})
            usage_per_turn.append({
                'input': u.get('input'), 'cacheRead': u.get('cacheRead'),
                'cacheWrite': u.get('cacheWrite'), 'output': u.get('output'),
                'reasoningTokens': u.get('reasoningTokens'),
            })
            c = m.get('content')
            if isinstance(c, list):
                for b in c:
                    if isinstance(b, dict) and b.get('type') == 'toolCall':
                        tool_calls.append({
                            'name': b.get('name'),
                            'args': json.dumps(b.get('arguments', {}))[:2000],
                            'id': b.get('id'),
                        })
        elif role == 'toolResult':
            size = len(json.dumps(m.get('content', '')))
            tool_results.append({
                'name': m.get('toolName'),
                'isError': m.get('isError', False),
                'size': size,
                'id': m.get('toolCallId'),
            })

    # match results to calls
    res_by_id = {r['id']: r for r in tool_results if r.get('id')}
    failures = [r for r in tool_results if r['isError']]
    # retries: consecutive same-tool calls (rough)
    retries = 0
    prev = None
    for c in tool_calls:
        key = (c['name'], hashlib.md5(c['args'].encode()).hexdigest()[:8])
        if key == prev:
            retries += 1
        prev = key
    # file reads + re-reads (read/glob targets)
    read_targets = []
    for c in tool_calls:
        if c['name'] in ('read', 'grep', 'glob'):
            # try to extract a path from args
            a = c['args']
            read_targets.append(a[:120])
    re_read_same = 0
    if read_targets:
        rc = Counter(read_targets)
        re_read_same = sum(v - 1 for v in rc.values() if v > 1)

    # aggregate per-tool
    tool_counts = Counter(c['name'] for c in tool_calls)
    tool_fail_counts = Counter(r['name'] for r in failures)
    result_sizes = [r['size'] for r in tool_results]

    sums = {k: sum(t[k] or 0 for t in usage_per_turn) for k in ('input', 'cacheRead', 'cacheWrite', 'output', 'reasoningTokens')}
    return {
        'assistant_turns': assistant_count,
        'tool_call_count': len(tool_calls),
        'tool_counts': dict(tool_counts),
        'tool_failures': len(failures),
        'tool_fail_counts': dict(tool_fail_counts),
        'retries_approx': retries,
        'read_rereads_approx': re_read_same,
        'total_result_bytes': sum(result_sizes),
        'median_result_bytes': sorted(result_sizes)[len(result_sizes)//2] if result_sizes else 0,
        'max_result_bytes': max(result_sizes) if result_sizes else 0,
        'custom_events': dict(custom_events),
        'has_context_snapshot': has_context_snapshot,
        'has_provider_payload': has_provider_payload,
        'non_message_tokens_t1': non_msg_tokens[0] if non_msg_tokens else None,
        'non_message_tokens_all_same': len(set(non_msg_tokens)) == 1 if non_msg_tokens else None,
        'sum_input': sums['input'],
        'sum_cacheRead': sums['cacheRead'],
        'sum_cacheWrite': sums['cacheWrite'],
        'sum_output': sums['output'],
        'sum_reasoningTokens': sums['reasoningTokens'],
        'models_seen': sorted(models_seen),
        'background_or_extra_calls': extra_model_events,
    }

def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--arm', required=True)
    ap.add_argument('--task', required=True)
    ap.add_argument('--rep', required=True)
    args = ap.parse_args()
    base = f"results/gpt-5.5/low/{args.arm}/{args.task}/{args.rep}"
    files = sorted(glob.glob(f"{base}/session/*.jsonl"))
    if not files:
        print(json.dumps({'error': 'no session', 'path': base})); return
    out = extract(files[0])
    out['arm'] = args.arm; out['task'] = args.task; out['rep'] = args.rep
    print(json.dumps(out, indent=2))

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
"""Per-session forensic extractor for a Pi/OMP (or any pi-headless) session JSONL.

Generalized and importable. ``extract(session_path)`` returns a dict of forensic
metrics for one cell. Handles both the plain Pi session format (usage only) and
the richer OMP format (contextSnapshot.nonMessageTokens, providerPayload).

Metrics captured:
  - assistant_turns, tool_call_count, per-tool counts
  - tool_failures (isError) + per-tool fail counts
  - retries_approx (consecutive same-tool + same-args), read_rereads_approx
  - tool result sizes (total/median/max bytes) — these accumulate into context
  - custom_events histogram (OMP writes tool_execution_start + session_exit)
  - non_message_tokens_t1 + whether it is constant across turns (harness wrapper)
  - per-turn usage sums: input, cacheRead, cacheWrite, output, reasoningTokens
  - models_seen, background_or_extra_calls (always 0 for these arms)

Usage:
  python3 extract_session.py --session <path/to/session.jsonl>
"""
import json, glob, hashlib
from collections import Counter


def extract(session_path):
    tool_calls = []
    tool_results = []
    custom_events = Counter()
    custom_tool_intents = []
    non_msg_tokens = []
    usage_per_turn = []
    models_seen = set()
    assistant_count = 0
    has_context_snapshot = False
    has_provider_payload = False

    with open(session_path) as f:
        for line in f:
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

    failures = [r for r in tool_results if r['isError']]
    retries = 0
    prev = None
    for c in tool_calls:
        key = (c['name'], hashlib.md5(c['args'].encode()).hexdigest()[:8])
        if key == prev:
            retries += 1
        prev = key
    read_targets = [c['args'][:120] for c in tool_calls if c['name'] in ('read', 'grep', 'glob')]
    re_read_same = sum(v - 1 for v in Counter(read_targets).values() if v > 1)

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
        'median_result_bytes': sorted(result_sizes)[len(result_sizes) // 2] if result_sizes else 0,
        'max_result_bytes': max(result_sizes) if result_sizes else 0,
        'custom_events': dict(custom_events),
        'has_context_snapshot': has_context_snapshot,
        'has_provider_payload': has_provider_payload,
        'non_message_tokens_t1': non_msg_tokens[0] if non_msg_tokens else None,
        'non_message_tokens_all_same': (len(set(non_msg_tokens)) == 1) if non_msg_tokens else None,
        'sum_input': sums['input'],
        'sum_cacheRead': sums['cacheRead'],
        'sum_cacheWrite': sums['cacheWrite'],
        'sum_output': sums['output'],
        'sum_reasoningTokens': sums['reasoningTokens'],
        'models_seen': sorted(models_seen),
        'background_or_extra_calls': 0,
    }


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--session', required=True)
    args = ap.parse_args()
    files = sorted(glob.glob(args.session)) if '*' in args.session else [args.session]
    print(json.dumps(extract(files[0]), indent=2))


if __name__ == '__main__':
    main()

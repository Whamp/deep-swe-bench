# Paired trajectory packet schema

Use this schema for deterministic benchmark-churn evidence packets.

## Directory layout

Recommended output path:

```text
analysis/<comparison-name>/churn_deep_dive/
  extract_packets.py
  loss_packets_index.json
  win_packets_index.json
  classification.json
  <task>__rep<rep>.json
  <task>__rep<rep>.md
  review_<task-short>.md        # optional independent reviewer note
  render_report.py
  index.html
```

## Packet JSON shape

```json
{
  "pair": {
    "task": "slug",
    "rep": 0,
    "title": "Display title",
    "difficulty": "hard|medium|easy",
    "language": "Python|Go|TypeScript|...",
    "left_config": "baseline",
    "right_config": "treatment"
  },
  "left": {
    "result": {
      "reward_binary": 1,
      "reward_partial": 1.0,
      "f2p_passed": 0,
      "f2p_total": 0,
      "p2p_passed": 0,
      "p2p_total": 0,
      "combined_total_tokens": 0,
      "combined_cost_usd": 0,
      "agent_wall_s": 0,
      "turns": 0,
      "tool_calls": 0,
      "patch_bytes": 0,
      "agent_timed_out": false,
      "verifier_exit": 0
    },
    "session": "results/.../session/*.jsonl",
    "patch_stats": {
      "bytes": 0,
      "files": [],
      "files_count": 0,
      "adds": 0,
      "dels": 0,
      "changed_lines": 0
    },
    "trace": {
      "assistant_turns": 0,
      "tool_counts": {},
      "bash_cmds": [],
      "config_specific_cmds": []
    },
    "verifier": {}
  },
  "right": { "...": "same as left" },
  "classification": {
    "primary_bucket": "missing invariant/guard",
    "secondary_bucket": "validation gap",
    "mechanism": "Concrete patch behavior that explains the verifier delta.",
    "evidence": ["short evidence bullet"],
    "guidance_implication": "Checkable skill/prompt change hypothesis."
  }
}
```

## Markdown packet sections

Each `.md` packet should include:

1. **Header:** task, rep, title, difficulty, language.
2. **Outcome delta:** partial, binary, f2p/p2p, tokens, cost, wall, turns, tool calls.
3. **Metrics JSON block:** compact left/right result metrics.
4. **Patch stats:** changed files, add/del counts, patch bytes.
5. **Tool summary:** total tool counts and config-specific tool calls.
6. **Timelines:** bash/test/validation commands for both sides.
7. **Patch excerpts:** bounded diff excerpts for both sides.
8. **Verifier evidence:** failing test names and relevant log/XML/reward excerpts.
9. **Classification:** primary bucket, mechanism, and confidence.

## Bucket vocabulary

Prefer the most specific bucket:

- **wrong seam/layer** — patch chose a lower/global/wrong abstraction when an existing choke point was safer.
- **under-implementation** — patch is in the right area but omits required behavior, lifecycle, wiring, or edge case.
- **over-implementation** — patch adds extra behavior or normalization beyond task expectations.
- **missing invariant/guard** — patch misses a fallback, bound, dialect guard, order invariant, size invariant, or compatibility guard.
- **protocol/interface drift** — patch changes observable event/API/schema/CLI behavior that tests or users rely on.
- **cross-scope regression** — target feature works but another dialect/package/config path regresses.
- **validation gap** — local checks passed but did not cover the failing hidden behavior.
- **resource exhaustion** — timeout, budget exhaustion, or early stop changed outcome.
- **likely variance** — only after patch and verifier evidence fail to support a stronger mechanism.

## Report requirements

A report should show:

- net solve delta and flip counts
- aggregate buckets with counts
- one row per flip with mechanism, not just metrics
- links to packets
- skill/prompt/tool guidance implications separated from proven facts
- clear caveats about subset/model/thinking/reps

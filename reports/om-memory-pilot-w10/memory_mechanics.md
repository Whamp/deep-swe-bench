# OM memory mechanics

Scope: `runs/om-memory-pilot-w10/reports/paired_manifest.json` plus 113 debug streams under `runs/om-memory-pilot-w10/pi-observational-memory/*/rep0/pi-agent/observational-memory/debug/*.ndjson`.

I treat a positive `om.reward_partial - baseline.reward_partial` as a win, a negative delta as a loss, and zero as a tie.

## Run-wide activity

| metric | total | per-task mean | median |
|---|---:|---:|---:|
| `observer.start` | 774 | 6.85 | 6 |
| `observer.records` | 773 | 6.84 | 6 |
| `observer.appended` | 764 | 6.76 | 6 |
| `reflector.agent_start` | 799 | 7.07 | 6 |
| `reflector.result` | 799 | 7.07 | 6 |
| `dropper.waiting_for_reflection` | 698 | 6.18 | 5 |
| `dropper.not_ready` | 462 | 4.09 | 4 |

Run-level outcome summary:

- partial wins/losses/ties: 69 / 33 / 11
- binary score improved / regressed: 13 / 2
- OM solved 10 rows vs 2 for baseline
- mean debug span per task: 948.4s; median: 806.0s
- mean OM wall time: 1053.5s; median: 929.2s
- mean OM turns: 89.9; median: 80
- mean OM tool calls: 105.0; median: 96

## What the memory loop was doing

- Every task had observer + reflector + dropper activity.
- `reflector.agent_start` and `reflector.result` matched exactly overall (799 each), so reflection work generally completed once started.
- `observer.appended` lagged `observer.records` by 9 total batches.
- That gap is explained by the 9 `observer.error` tasks; each of those dropped exactly one appended batch.
- The only `observer.empty` was `runs/om-memory-pilot-w10/pi-observational-memory/happy-dom-deterministic-intersectionobserver/rep0/pi-agent/observational-memory/debug/019f00cf-e851-7ecc-9972-6ee814d46006.ndjson:12`.

## Stale-context errors

There were 22 unique tasks with a stale-context error event (19.5% of the run): 13 `reflector.error` and 9 `observer.error`.

The message was the same each time:

> "This extension ctx is stale after session replacement or reload. Do not use a captured pi or command ctx after ctx.newSession(), ctx.fork(), ctx.switchSession(), or ctx.reload()."

Examples from raw logs:

- observer-side: `runs/om-memory-pilot-w10/pi-observational-memory/actionlint-action-pinning-lint/rep0/pi-agent/observational-memory/debug/019f0069-1079-7264-bef3-b4927100afeb.ndjson:33`
- reflector-side: `runs/om-memory-pilot-w10/pi-observational-memory/mashumaro-flattened-dataclass-fields/rep0/pi-agent/observational-memory/debug/019f00ea-32d7-7194-929f-bc845d7b0f43.ndjson:79`
- loss example: `runs/om-memory-pilot-w10/pi-observational-memory/cattrs-partial-structuring-recovery/rep0/pi-agent/observational-memory/debug/019f00bd-bfb5-7de9-962a-7f434443588b.ndjson:39`

Outcome mix for the 22 error rows:

- 15 wins
- 5 losses
- 2 ties
- mean partial delta on error rows: `+0.078`
- mean partial delta on no-error rows: `+0.083`

So the stale-context bug is real, but it is not a strong predictor of failure here.

## Timing / records vs outcome

| group | n | mean wall_s | mean turns | mean tool_calls | mean starts | mean reflector starts |
|---|---:|---:|---:|---:|---:|---:|
| wins | 69 | 1164.9 | 97.5 | 113.4 | 7.4 | 8.0 |
| losses | 33 | 810.1 | 73.8 | 87.4 | 5.8 | 5.1 |
| ties | 11 | 1085.3 | 90.5 | 104.7 | 6.6 | 7.5 |

Positive rows were roughly:

- 1.44x longer wall time
- 1.32x more turns
- 1.30x more tool calls
- 1.29x more observer batches
- 1.57x more reflector batches

That same signal shows up as a positive correlation with partial delta:

- Pearson: wall `+0.324`, turns `+0.363`, tool calls `+0.347`, observer starts `+0.290`, reflector starts `+0.311`, debug span `+0.301`
- Spearman: wall `+0.396`, turns `+0.383`, tool calls `+0.391`, observer starts `+0.351`, reflector starts `+0.387`, debug span `+0.390`

The effect is strongest on hard rows; medium rows are much weaker. On hard rows, Spearman still stayed positive (`+0.332` to `+0.414`). That looks like "more iterative memory work helped when the task was already hard," not "more time always wins."

Counterexamples:

- `runs/om-memory-pilot-w10/pi-observational-memory/boa-hierarchical-evaluation-cancellation/rep0/pi-agent/observational-memory/debug/019f00bd-c23d-7acc-a15f-cb9e34885405.ndjson` spent 2335s and 156 turns but stayed at `+0.000` delta.
- `runs/om-memory-pilot-w10/pi-observational-memory/effect-sse-httpapi-streaming/rep0/pi-agent/observational-memory/debug/019f00bd-c294-7bb0-b284-8ac48dd615f0.ndjson` spent 2193s and 194 turns but also stayed flat.

## Bottom line

- The OM memory loop was active and fairly regular: about 7 observer batches and 7 reflector batches per task.
- Stale-context errors were common, but usually recoverable; they mostly cost one observer batch when they hit the observer side.
- Better outcomes correlate with longer, denser runs, especially on hard tasks.
- The memory system seems to buy persistence and coverage, not guaranteed correctness.

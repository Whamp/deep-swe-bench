# pi-observational-memory DeepSWE issue #1 investigation

Status: in progress  
Last updated: 2026-07-01

This report consolidates what we know so far about GitHub issue #1 against the published pi-observational-memory DeepSWE results.

## Short version

The original DeepSWE OM run showed a real **OM-config effect**, but it did not prove an executor-visible memory-content effect.

The key reason: in non-projected, non-compacted one-shot `pi -p` benchmark runs, OM observations and reflections were recorded in the session ledger, but they usually did not reach the task executor's model context. In normal long Pi sessions, they reach the executor after compaction creates a `compactionSummary`. The published DeepSWE OM sessions had no such compaction summaries.

We built and launched a four-arm isolation test to separate the effects:

| config | isolates |
|---|---|
| `baseline` | unmodified Pi |
| `recall-placebo` | recall tool/schema/system-prompt surface only; workers disabled |
| `observational-memory` | current OM behavior: workers write ledger entries, but no guaranteed executor projection |
| `projected-om` | OM workers plus explicit provider-payload memory projection |

The 12-task `12_v2` pilot is currently running with 3 reps per config.

## Updates from later benchmark work

Later GPT-5.5 and Qwen experiments strengthen the need for the four-arm isolation test. They show that OM configs can change benchmark outcomes, but they still do not prove that executor-visible memory content caused the change.

- **GPT-5.5 low, `36_v1`:** non-projected OM observer configs improved solve rate over baseline. `observational-memory-gpt54mini-low` gained +0.093 solve rate, and `observational-memory-glm52-off` gained +0.074. Both solve-rate confidence intervals excluded zero. Because these cells used the normal, non-projected OM path, treat this as an OM-config effect until visibility is classified cell by cell.
- **GPT-5.5 xhigh, `36_v1`:** `observational-memory-gpt54mini-low` was directionally positive: solve rate 0.657 versus 0.602 for baseline, with robust partial tied at 0.997. The solve-rate confidence interval crossed zero. Across 108 OM cells, compaction happened once and the dropper never ran, so compaction and pruning did not drive this result.
- **Qwen3.6 off observer, GPT-5.5 low, `12_v0`:** Qwen-off OM gained solves but introduced catastrophic failures and poor worker health. A content audit found mostly grounded memories; the main problems were stale-context failures, long observer latency, and trajectory lock-in from premature completion claims. This supports the mechanical-side-effect hypothesis more than a simple hallucination hypothesis.
- **Split-stage OM, GPT-5.5 low, `12_v0`:** `gpt-5.4-mini:low` observer plus `glm-5.2:off` reflector was clean but weak: solve rate 0.306 versus 0.250 for baseline, robust partial 0.991, and zero catastrophic cells. It underperformed the simpler `gpt-5.4-mini:low` observer config and the `glm-5.2:off` config. A stronger or different reflector alone does not explain the earlier OM gains.

## Issue claims and current verdict

### Claim 1: OM memory does not reach the task agent in headless `pi -p` runs

Current verdict: **verified for the published DeepSWE OM run, with an important qualification.**

OM records observations and reflections as session entries of type `custom`:

- `om.observations.recorded`
- `om.reflections.recorded`

Pi's normal session-context builder does not send `type:"custom"` entries to the executor. It only turns these entry types into model context:

- `message`
- `custom_message`
- `branch_summary`
- `compaction` as `compactionSummary`

So OM ledger entries are persisted and foldable by OM, but they are not directly executor-visible.

The qualification: OM can become executor-visible through compaction. During compaction, OM's compaction hook folds observations/reflections and adds them to the generated `compactionSummary`. That summary is visible to later executor turns.

### Claim 2: Neither compaction nor recall fired in the published run

Current verdict: **verified for the published DeepSeek high OM run.**

Observed in `results/deepseek-v4-flash/high/observational-memory`:

- `0/113` cells had compaction entries.
- `0/113` cells called the `recall` tool.
- Session files contained OM custom ledger records but no executor-visible OM summaries.

Additional scans strengthened this:

- String scan: almost no observation/reflection text appeared after recording.
- Memory-ID scan: `0` hits for observation/reflection IDs in executor message entries across DeepSeek OM and GPT-5.5 low observer-grid sessions.

Because OM `renderSummary()` includes memory IDs, the zero-ID result is strong evidence that compaction summary projection did not fire in those benchmark sessions.

### Claim 3: The old result may be caused by persistence/scaffolding, not executor-visible memory content

Current verdict: **plausible and now under test.**

The current executor-visible differences between baseline and current OM in one-shot runs are mainly:

1. The `recall` tool is registered.
2. The recall tool adds tool text and behavioral guidelines to Pi's system prompt.
3. OM workers run in the background and can affect timing, load, or turn scheduling.
4. The config orchestration text differs slightly.

The old data show OM sessions usually worked longer:

- more turns,
- more tool calls,
- fewer empty patches in some runs.

That supports a persistence/scaffolding confound. It does not prove that executor-visible memory content helped.

## What a known working OM session looks like

We inspected this long real Pi session:

```txt
~/.pi/agent/sessions/--home-will-evals-deep-swe-bench--/
2026-06-30T02-29-50-441Z_019f165c-86e9-74bb-a89a-4231468bf1be.jsonl
```

Structural summary:

| metric | value |
|---|---:|
| session lines | 6,543 |
| file size | 62.8 MB |
| message entries | 4,306 |
| OM observation records | 183 |
| OM reflection records | 127 |
| OM drop records | 115 |
| compaction entries | 32 |
| custom_message entries | 112 |

Every compaction after the early session contained OM memory content. Pi's own `buildSessionContext()` on the final branch returned:

```txt
first context message role: compactionSummary
contains OM header: yes
contains ## Observations: yes
contains ## Reflections: yes
```

This is the reference shape for OM working as executor-visible semantic memory in a long session: custom ledger entries accumulate, compaction folds them, and future turns see a `compactionSummary`.

## What a published DeepSWE OM session looked like

Representative old OM cell:

```txt
results/deepseek-v4-flash/high/observational-memory/goreleaser-retry-publish-auditing/rep0/session/*.jsonl
```

Structural summary:

| metric | value |
|---|---:|
| entries | 219 |
| messages | 206 |
| OM observation records | 6 |
| OM reflection records | 4 |
| compaction entries | 0 |
| executor context has OM header | no |
| executor context has observations/reflections | no |

Pi's `buildSessionContext()` returned normal task messages only. The OM ledger existed, but no semantic OM summary reached the executor.

## Why `projected-om` needs different evidence

`projected-om` injects folded OM memory in a `before_provider_request` hook. That happens after Pi builds the normal session context and right before the provider request is sent.

Therefore:

- the memory projection is visible to the model;
- the projection does **not** appear in the session tree;
- session-tree analysis alone would falsely report no memory visibility.

For `projected-om`, the right evidence is the projection trace:

```txt
pi-agent/observational-memory/projection/projection.ndjson
```

A smoke cell showed:

| metric | value |
|---|---:|
| projection rows | 81 |
| injected rows | 61 |
| final observations projected | 44 |
| final reflections projected | 5 |
| final summary chars | 11,805 |

## Smoke tests completed

### OM visibility smoke

Path:

```txt
analysis/om-visibility-smoke/run-smoke.mjs
```

This smoke uses a local fake OpenAI-compatible provider, so it does not spend model credits.

It verified:

1. The `before_provider_request` capture sees the actual outbound executor payload.
2. A sentinel in `--append-system-prompt` appears in the provider payload.
3. A seeded OM `type:"custom"` observation does not appear before projection/compaction.
4. After projection, the next executor payload contains:
   - the sentinel,
   - OM summary header,
   - observation ID.

Latest result:

```txt
positive control: true
projection: true
phase-one sentinel: false
phase-two sentinel: true
summary header: true
observation id: true
```

### `recall-placebo` smoke

Representative smoke task:

```txt
goreleaser-retry-publish-auditing / rep0
```

Result:

| field | value |
|---|---:|
| agent_exit | 0 |
| agent_timed_out | false |
| passive | true |
| OM worker calls | 0 |
| OM worker tokens | 0 |

This confirms the placebo has the recall tool surface but no OM worker activity.

### `projected-om` smoke

Same smoke task:

```txt
goreleaser-retry-publish-auditing / rep0
```

Result:

| field | value |
|---|---:|
| agent_exit | 0 |
| agent_timed_out | false |
| OM worker calls | 21 |
| observer calls | 12 |
| OM worker tokens | 323,981 |
| projection rows | 81 |
| injected rows | 61 |

This confirms workers ran and projected memory reached executor provider payloads.

## Four-arm isolation design

The pilot uses `12_v2`, a dataset-neutral subset selected only by language and official DeepSWE cross-model pass-rate tercile.

Configs:

1. `baseline`
   - plain Pi,
   - no OM extension,
   - no recall tool.

2. `recall-placebo`
   - loads OM extension,
   - `passive: true`,
   - recall tool and guidelines present,
   - no OM workers.

3. `observational-memory`
   - current OM behavior,
   - workers run,
   - ledger entries are written,
   - no guaranteed executor memory projection in one-shot tasks.

4. `projected-om`
   - current OM behavior,
   - workers run,
   - folded memory is injected into executor provider payloads.

Interpretation:

| delta | interpretation |
|---|---|
| `recall-placebo - baseline` | recall tool/schema/system-prompt scaffold effect |
| `observational-memory - recall-placebo` | worker/timing/side-effect effect without guaranteed memory content |
| `projected-om - observational-memory` | semantic memory projection effect |
| `projected-om - recall-placebo` | net memory machinery plus projected content effect |

## Current pilot status

Command:

```bash
python3 harness/run_batch.py \
  --configs baseline,recall-placebo,observational-memory,projected-om \
  --subset 12_v2 \
  --model openrouter/deepseek/deepseek-v4-flash \
  --thinking high \
  --runs 3 \
  --workers 8
```

Tracking:

```txt
tmux pane: %36
log: results/deepseek-v4-flash/high/logs/om-isolation-12v2-4arm-w8.out
```

Status is a live operational detail. Before analysis, recompute the result count from `results/deepseek-v4-flash/high/{baseline,recall-placebo,observational-memory,projected-om}` and verify all `12_v2 × 3` cells exist for each config.

Do not interpret partial results.

## What to report publicly right now

Do not claim the original OM DeepSWE result proved an executor-visible memory-content effect.

A safe correction is:

> We found that the original DeepSWE OM run measured an OM-config effect, not a clean executor-visible memory-content effect. In non-projected, non-compacted one-shot `pi -p` runs, OM ledger entries were recorded but generally did not reach executor context because compaction did not occur before useful work. We are rerunning a four-arm isolation test with a recall-tool placebo and an explicit projected-memory arm.

Avoid these claims until the four-arm run finishes:

- OM memory content caused the original gain.
- Dropper/pruning caused the gain.
- Observer model quality caused the gain through executor-visible memory.
- Later GPT-5.5 or Qwen observer wins prove that semantic memory helped without projection or compaction visibility evidence.

## Next analysis steps

When the 4-arm run completes:

1. Build a paired manifest over `12_v2 × 3 reps`.
2. Report reward separately by config:
   - binary solve rate,
   - mean partial,
   - f2p and p2p counts separately,
   - empty patch rate,
   - turns/tool calls,
   - main tokens/cost,
   - worker tokens/cost.
3. Classify each cell's memory visibility:
   - `placebo_only`,
   - `ledger_only`,
   - `compaction_visible`,
   - `payload_projected`.
4. Report mechanism evidence:
   - recall calls,
   - compaction count,
   - projection injected rows,
   - observer and reflector calls,
   - observer and reflector errors,
   - append success rate,
   - dropper calls and drops.
5. Compare the four key deltas listed above.
6. Inspect large movers before making causal claims.

## Evidence artifacts

Committed:

```txt
ab3e832 Add neutral DeepSWE subsets and OM visibility smoke
75624aa Add OM placebo and projected-memory configs
```

Important files:

```txt
analysis/om-visibility-smoke/README.md
analysis/om-visibility-smoke/run-smoke.mjs
configs/recall-placebo/
configs/projected-om/
subsets/12_v2.txt
subsets/36_v2.txt
subsets/make_stratified.py
reports/om-issue-1-investigation/README.md
```

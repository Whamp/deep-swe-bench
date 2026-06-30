# OM reflector/dropper mechanics

Source code:
- `configs/observational-memory*/extensions/pi-observational-memory/src/hooks/consolidation-trigger.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/agents/reflector/agent.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/agents/dropper/agent.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/agents/dropper/coverage.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/agents/dropper/pool.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/session-ledger/*.ts`
- `configs/observational-memory*/extensions/pi-observational-memory/src/config.ts`

## How the stages work

### 1) Trigger order
`registerConsolidationTrigger()` hooks `agent_start` and `turn_end`. When config is active and no consolidation is already in flight, it runs:

1. observer
2. reflector
3. dropper

The same resolved OM model is reused for all three stages (`runtime.resolveModel()`), with `thinkingLevel` taken from `config.model.thinking` or `low` by default.

### 2) Reflector
Reflector runs only when:
- `rawTokensSinceReflectionCoverage(entries) >= reflectAfterTokens`
- there is at least one observation coverage marker

It builds a prompt from current reflections + current observations, then exposes one tool:
`record_reflections({ reflections: [{content, supportingObservationIds}] })`

Guardrails:
- content is trimmed/truncated and must stay single-line
- every support id must be one of the current active observation ids
- duplicate reflection ids are ignored
- empty/invalid proposals are rejected

Accepted reflections are appended as `customType == 'om.reflections.recorded'` with `coversUpToId` set to the latest covered source entry.

### 3) Dropper
Dropper runs only if all of these are true:
- reflector just produced reflections in the same consolidation run
- those reflections were appended successfully
- the active observation pool is over target (`observationsPoolTargetTokens`)

`observationPoolMetrics()` computes:
- `tokensOverTarget`
- `fullness`
- `maxDropsAllowed = ceil(tokensOverTarget / avgObservationTokens)`
- `ready = overTarget && maxDropsAllowed > 0`

If `ready` is false, the stage logs `dropper.not_ready` and returns.

When it does run, the tool is `drop_observations({ ids, reason? })`. Final selection is deterministic:
1. stronger reflection coverage first (`strong` > `partial` > `none` as droppable priority)
2. lower relevance first (`low` → `critical`)
3. older timestamp first
4. earlier proposal order last

Accepted drops are appended as `customType == 'om.observations.dropped'`.

## What the current runs show

### Named current trees
- `results/deepseek-v4-flash/high/observational-memory`
- `results/gpt-5.5/low/observational-memory-gpt55-low`

Both trees recorded observations and reflections, but neither recorded any drops.

| tree | sessions | obs batches / session | ref batches / session | drop batches | max active obs tokens | over 10k target |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek-v4-flash high | 113 | 6.76 | 4.09 | 0 | 6279 | 0 |
| GPT-5.5 low | 36 | 1.61 | 0.69 | 0 | 1846 | 0 |

The hard gate is the pool target: both trees stayed well under 10k active observation tokens, so the dropper never got a chance to enter `dropper.stage_start`, let alone emit `om.observations.dropped`.

### GPT-5.5 low config family
Across all current GPT-5.5 low OM configs, dropper never fired either. The more active workers were GPT-5.4-mini low/off and GLM-5.2 off; xhigh configs were much sparser.

| config | sessions | obs / session | ref / session | drops | max active obs tokens |
|---|---:|---:|---:|---:|---:|
| observational-memory-gpt54mini-low | 185 | 1.98 | 0.90 | 0 | 1566 |
| observational-memory-gpt54mini-off | 185 | 2.00 | 0.91 | 0 | 1505 |
| observational-memory-glm52-off | 185 | 1.72 | 0.77 | 0 | 3080 |
| observational-memory-gpt55-off | 108 | 1.74 | 0.79 | 0 | 1971 |
| observational-memory-gpt55-low | 36 | 1.61 | 0.69 | 0 | 1846 |
| observational-memory-gpt54mini-xhigh | 36 | 0.50 | 0.22 | 0 | 946 |

## Debug-event evidence
In the GPT-5.5 low debug stream, the typical sequence is:
- `observer.start`
- `observer.records`
- `observer.appended`
- `dropper.waiting_for_reflection`
- `reflector.agent_start`
- `reflector.result`
- `dropper.not_ready`

There are no `dropper.stage_start` or `dropper.append` events in the named current trees.

## Model comparison

The model choice affects how much observer/reflection work gets produced, but not the drop gate itself.

From the 36-task GPT-5.5 observer grid:
- GPT-5.4-mini low is the best single observer config on solve rate and is also mechanically clean.
- GLM-5.2 off is close on solve rate, but noisier and more verbose.
- GPT-5.5 off is safer on catastrophic cells than GPT-5.4-off, but weaker overall.
- xhigh configs tend to be sparser and more abstract.

That matches the embedding follow-up: GLM-off tends to broaden context, while GPT-5.4-mini low tends to preserve live verification and test state. The dropper still never runs there because the active pool stays below target.

## Bottom line

- Reflector is active and model-sensitive.
- Dropper is threshold-gated, not just model-gated.
- In the named current runs, the pool never reaches the 10k target, so dropper is effectively idle.
- If you want real dropper behavior, you need a run that accumulates a much larger active observation pool.

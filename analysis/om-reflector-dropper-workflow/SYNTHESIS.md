# OM reflector/dropper synthesis

Scope:
- DeepSeek-v4-flash high full run: `results/deepseek-v4-flash/high/observational-memory` vs `results/deepseek-v4-flash/high/baseline`.
- GPT-5.5 low observer grid/config family: `results/gpt-5.5/low/analysis-36v1-observer-grid`, `results/gpt-5.5/low/observational-memory-*`, and `results/gpt-5.5/low/baseline`.
- Earlier embedding screen remains separate: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/FOLLOWUP_ANALYSIS_SUMMARY.md`.

## 1. Clear answer

**Reflector: yes, now analyzed beyond observer outputs.**

We have direct reflector evidence from:
- session JSONL `customType == "om.reflections.recorded"`, and
- GPT-5.5 low debug NDJSON `reflector.agent_start`, `reflector.result`, and `reflector.error`.

That is enough to say the reflector is active, model-sensitive, and materially different across worker models/thinking settings.

**Dropper: yes for activation status; no for drop-quality claims.**

We analyzed whether the dropper actually ran. In these result trees it did **not** meaningfully activate:
- no `dropper.stage_start`, `dropper.result`, or drop append events;
- no `customType == "om.observations.dropped"`;
- GPT-5.5 low debug payloads only show `dropper.waiting_for_reflection` and `dropper.not_ready`.

So we can publishably say the current positive OM effects are **not caused by active dropping**. We cannot yet claim the dropper chooses good/bad observations because it never reached that path.

## 2. New facts this workflow found

1. **DeepSeek high OM has reflection volume but no debug action trace.** The full 113-task DeepSeek run has session-level observation/reflection records, including 969 recorded reflection entries in the inventory/model-difference scan, but no observer/reflector/dropper debug NDJSON under `results/`. That prevents direct runtime-action comparison for reflector/dropper on DeepSeek.
2. **GPT-5.5 low OM configs expose the action trace.** All event-bearing GPT-5.5 low OM configs show observer, reflector, and dropper events; baseline and the grid-summary artifact folder do not.
3. **Reflector yield varies sharply by worker.** `gpt55-off` and `gpt54-off` often return `no_tool_call` (~47% and 50%). `gpt54mini-*` and `glm52-*` more often produce accepted nonempty reflections.
4. **Reflection content quality differs, not just count.** GLM-5.2 reflections are longer and more support-backed; GPT-5.4-mini-low is more concise but more process/self-report heavy; GPT-5.4-mini-off has high volume but also the clearest duplicate/reject noise.
5. **Dropper never dropped.** Across GPT-5.5 low debug streams, every `dropper.not_ready` had `maxDropsAllowed = 0` and `tokensOverTarget = 0`; every `dropper.waiting_for_reflection` had `sameRunReflections = 0`.
6. **The gate is token pressure, not model identity.** The active observation pool stayed far below the 10k target: max observed fullness in the low-grid audit was 27.41% (`glm52-max`). Named-tree mechanics also found max active pool 6,279 tokens for DeepSeek high and 1,846 for GPT-5.5-low, still below target.
7. **Outcome linkage is descriptive but useful.** DeepSeek 113-task OM gains correlate modestly with more observation/reflection volume and cost. GPT-5.5 low 36_v1 gains are mostly near-miss-to-solve conversions, not broad mean-partial lift.

## 3. Reflector differences by worker model / thinking setting

| worker/config | reflector read |
|---|---|
| `glm52-off/high/max` | Strongest evidence-backed style. Longer reflections, more supporting observation IDs, fuller pools, and more `none→strong` / `partial→strong` coverage transitions. Best for “rich memory,” but more verbose and error-prone. |
| `gpt54mini-low` | Best 36_v1 solve lift and mechanically clean, but content audit shows shallower, more process/self-report-heavy reflections than GLM. Likely useful because it preserves concrete live state without overthinking. |
| `gpt54mini-off` | High reflector throughput and strong coverage transitions, but also the main duplicate/reject/noise mass. Good mechanical yield, less clean semantically. |
| `gpt55-off/low` | More shallow/inert reflector behavior. `gpt55-off` has many `no_tool_call` reflector results; safer tail profile than some alternatives, but weaker solve lift. |
| `gpt54-off` | High `no_tool_call` rate and weakest 36_v1 read among the main configs; more tail risk. |
| `xhigh` variants | Fewer reflections; individual records can be denser/longer, but throughput drops. In this dataset, “more thinking” often means sparser memory, not better memory. |
| DeepSeek-v4-flash high OM | Session-level reflections exist and outcome linkage is positive, but no debug NDJSON means no direct `reflector.result`/error/no-tool comparison. Treat it as full-run outcome + session-record evidence, not a runtime-action trace. |

Short version: **GLM-5.2 is the deepest reflector; GPT-5.4-mini-low is the best observed solve-rate worker in the GPT-5.5 low grid; GPT-5.4-mini-off is productive but noisier; xhigh is usually too sparse.**

## 4. Dropper differences, or why there are none yet

There is no meaningful model comparison for active dropping because no config triggered active dropping.

Observed differences are only pre-drop pressure:
- GLM configs build the fullest pools and more `not_ready` checks.
- GPT-5.4-mini / GPT-5.5 configs stay lower.
- xhigh configs are sparsest.

But all share the same final state:
- active drops: **0**;
- `om.observations.dropped`: **0**;
- `tokensOverTarget`: **0**;
- `maxDropsAllowed`: **0**.

Mechanically, dropper is hard-gated by:
1. same-run reflections appended successfully, and
2. active observation pool over `observationsPoolTargetTokens`.

Current runs do not cross the token target, so the dropper is effectively idle.

## 5. Best next analysis / experiment to make claims publishable

Run one forced-over-target dropper experiment before making any claim about dropper quality.

Minimum experiment:
1. Use one small task set with two workers: `gpt54mini-low` and `glm52-off`.
2. Lower `observationsPoolTargetTokens` from 10k to a few hundred tokens, or preseed enough observations to exceed 10k.
3. Require evidence of all activation signals:
   - `dropper.stage_start`,
   - `dropper.result`,
   - `customType == "om.observations.dropped"`.
4. Audit dropped IDs against reflection coverage/relevance and final outcome.
5. Keep the published claim narrow: “dropper activation test,” not benchmark efficacy.

For reflector publication, the best next step is lighter:
- freeze the 36_v1 table,
- add 6–10 concrete reflection examples per top config,
- separate full-run DeepSeek evidence from GPT-5.5 low 36-task/3-rep grid evidence.

## 6. Public-thread-worthy vs internal-only

### Public-thread-worthy now

- **Reflector is model-sensitive.** Different worker models produce visibly different reflection volume, support density, and style.
- **Best GPT-5.5 low observer-grid result is not “biggest/deepest model wins.”** GPT-5.4-mini-low led solve lift; GLM-5.2-off was close and richer but not clearly superior.
- **Current OM gains are not from dropping.** In these runs, dropper did not actively remove observations.
- **Cautionary mechanism claim:** more worker volume/coverage is not automatically better; the effect looks like near-miss-to-solve conversion in the GPT-5.5 low 36_v1 grid.

### Internal-only for now

- Any claim that the dropper selects good/bad observations. It never activated.
- Any DeepSeek runtime-action comparison for reflector/dropper. We only have session records, not debug events.
- Any leaderboard-style claim from the GPT-5.5 low observer grid. It is a 36-task / 3-rep mechanism screen, not a 113-task full benchmark.
- Any causal claim that reflection volume caused the DeepSeek improvement. The correlation is descriptive and cost-linked.

## Bottom line

Reflector is real, active, and model-sensitive. Dropper is real in code but inert in these datasets. For publication: lead with reflector/model-choice findings and explicitly say the positive OM results happened **without active dropping**. To publish dropper behavior, force the pool over target and capture actual dropped records.

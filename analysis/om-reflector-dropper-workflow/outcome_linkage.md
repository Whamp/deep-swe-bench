# OM reflector/dropper outcome linkage

Scope:
- DeepSeek v4 flash high full run: `results/deepseek-v4-flash/high/baseline` vs `results/deepseek-v4-flash/high/observational-memory`
- GPT-5.5 low 36_v1 grid: `results/gpt-5.5/low/analysis-36v1-observer-grid` plus `results/gpt-5.5/low/observational-memory-*`

Correlation is descriptive only; it is not causation.

## 1) DeepSeek high OM full run (113 tasks)

DeepSeek has session-level `om.observations.recorded` / `om.reflections.recorded` data, but no reflector/dropper debug stream. So the join is: reflection/observation volume ↔ `result.json` outcome.

Headline:
- 69 wins / 33 losses / 11 ties on `reward_partial`
- +13 binary solve gains / 2 losses / net **+11 solves**
- mean `reward_partial` delta: **+0.082**
- median `reward_partial` delta: **+0.003**
- mean token delta: **+3.16M**

| metric | Pearson vs Δpartial | Spearman vs Δpartial | Pearson vs Δbinary |
|---|---:|---:|---:|
| reflection tokens | +0.293 | +0.218 | +0.090 |
| observation entries | +0.287 | +0.289 | +0.112 |
| observation tokens | +0.283 | +0.286 | +0.125 |
| reflection records | +0.268 | +0.285 | +0.081 |
| reflection entries | +0.259 | +0.161 | +0.037 |

Takeaway: more reflection/observation volume is associated with better outcomes and higher cost. Reflection token mass is the clearest single signal here.

### Examples

| case | task | Δpartial | reflection snippet |
|---|---|---:|---|
| win | `fastapi-implicit-head-options` | +0.997 | `User specified adding auto_head and auto_options parameters to FastAPI and APIRouter constructors, decorators, api_route, add_api_route, and include_router; implicit HEAD preserves GET route behavior returning no body; implicit OPTIONS returns 200 JSON with path, methods, and operations; ...` |
| win | `mashumaro-flattened-dataclass-fields` | +1.000 | `Project is mashumaro, a Python dataclass serialization/deserialization library.` |
| loss | `cattrs-partial-structuring-recovery` | -0.816 | `No existing partial_structure or PartialResult implementation found in the cattrs codebase.` |
| loss | `etree-xml-diff-patch` | -0.537 | `User requested XML diffing and patching capabilities for the existing etree library, specified in /task/instruction.md.` |

The bad cases are usually not obviously false; they’re thin or generic and don’t move from “what the task is” to “what to do next.”

## 2) GPT-5.5 low 36_v1 grid (5 OM worker models)

Here the task-level effect is different: solve rate improves, but mean `reward_partial` is slightly negative for every OM config. The effect is mainly **near-miss to binary-solve conversion**.

| config | Δ solve rate | extra solves | Δ mean partial | catastrophic cells | mean tokens | accepted nonempty | no tool call | observer append | reflector error | dropper not ready |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| `gpt54mini-low` | +0.093 | +10 | -0.014 | 2 | 958k | 87.7% | 11.4% | 96.8% | 4.4% | 34.7% |
| `glm52-off` | +0.074 | +8 | -0.009 | 1 | 923k | 88.6% | 11.4% | 87.9% | 13.3% | 33.9% |
| `gpt54mini-off` | +0.056 | +6 | -0.011 | 1 | 962k | 92.5% | 3.3% | 98.2% | 5.0% | 37.6% |
| `gpt55-off` | +0.046 | +5 | -0.014 | 0 | 940k | 53.3% | 46.7% | 89.1% | 3.0% | 28.3% |
| `gpt54-off` | +0.037 | +4 | -0.028 | 3 | 944k | 50.0% | 50.0% | 95.6% | 1.5% | 27.2% |

Read on the workers:
- **Best solve lift:** `gpt54mini-low`
- **Best mechanical health:** `gpt54mini-off`
- **Most tail risk:** `gpt54-off`
- **Safest but weaker:** `gpt55-off`
- **Most verbose / highest observation volume:** `glm52-off`

### Correlations across task-config rows (180 rows)

All signals are weak; none are strong enough to claim a clean linear mechanism.

| metric | Pearson vs Δpartial | Spearman vs Δpartial | Pearson vs Δsolve | Spearman vs Δsolve |
|---|---:|---:|---:|---:|
| mean tokens | -0.161 | -0.093 | -0.010 | -0.059 |
| mean observation entries | -0.152 | -0.145 | -0.002 | -0.019 |
| mean OM tokens | -0.145 | -0.117 | -0.016 | -0.046 |
| observer append rate | -0.116 | -0.094 | +0.050 | +0.023 |
| accepted nonempty rate | +0.113 | -0.021 | -0.054 | -0.018 |
| dropper not-ready rate | +0.007 | -0.098 | -0.064 | -0.035 |

Takeaway: on this grid, more worker volume does **not** translate into better mean partial. The useful effect is mostly solve conversion, and model choice matters more than any single worker-health metric.

## 3) Dropper was passive everywhere in GPT-5.5 low

Across the five OM configs in the 36_v1 grid:
- `dropper.waiting_for_reflection`: 1333 events
- `dropper.not_ready`: 658 events
- active drop events: **0**

Every sampled payload had:
- `sameRunReflections = 0`
- `tokensOverTarget = 0`
- `maxDropsAllowed = 0`

Representative payload:

```json
{
  "event": "dropper.not_ready",
  "data": {
    "observationTokens": 422,
    "targetTokens": 10000,
    "tokensOverTarget": 0,
    "fullness": 0.0422,
    "activeObservationCount": 12,
    "droppableCount": 12,
    "maxDropsAllowed": 0
  }
}
```

So the dropper never actually dropped anything in these datasets; it only reported waiting / not-ready states.

## 4) Caveats

- Correlation is not causation.
- DeepSeek is a 113-task full run; GPT is a 36_v1 / 3-rep grid.
- Different executors and worker models mean the two sections are only comparable at the mechanism level, not as a leaderboard.
- On GPT, solve gains coexist with slightly worse mean partial; the main effect is conversion of near-misses into solves.

## Artifacts

- `analysis/om-reflector-dropper-workflow/outcome_linkage.json`
- `analysis/om-reflector-dropper-workflow/deepseek_task_rows.csv`
- `analysis/om-reflector-dropper-workflow/gpt36v1_task_config_rows.csv`

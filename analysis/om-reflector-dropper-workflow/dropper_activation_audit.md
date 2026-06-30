# Dropper activation audit

Scope:
- `results/deepseek-v4-flash/high/observational-memory`
- `results/gpt-5.5/low/observational-memory-*`
- `results/gpt-5.5/low/baseline`

## Verdict
No run actually dropped observations or reflections.

- No `dropper.stage_start`, `dropper.result`, or `dropper.append` events appeared anywhere.
- No session emitted `customType == "om.observations.dropped"`.
- DeepSeek high has **no debug NDJSON** under `results/`; only session custom records.
- Baseline has no OM debug stream and no OM custom records.

## Event counts by config

| config | session files | debug files | om.observations.recorded | om.reflections.recorded | dropper.waiting | dropper.not_ready | dropped records | max not_ready obs tokens | max not_ready fullness |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| deepseek-v4-flash/high/observational-memory | 113 | 0 | 764 | 462 | 0 | 0 | 0 | — | — |
| gpt55-low | 36 | 36 | 58 | 25 | 50 | 25 | 0 | 1846 | 0.1846 |
| gpt55-off | 108 | 103 | 188 | 85 | 215 | 85 | 0 | 1707 | 0.1707 |
| gpt54-off | 108 | 106 | 217 | 97 | 260 | 97 | 0 | 2261 | 0.2261 |
| gpt54-low | 36 | 36 | 73 | 36 | 54 | 36 | 0 | 2117 | 0.2117 |
| gpt54-xhigh | 36 | 36 | 44 | 17 | 30 | 17 | 0 | 1351 | 0.1351 |
| gpt54mini-low | 185 | 180 | 367 | 166 | 311 | 166 | 0 | 1469 | 0.1469 |
| gpt54mini-off | 185 | 181 | 370 | 168 | 289 | 168 | 0 | 1309 | 0.1309 |
| gpt54mini-xhigh | 36 | 36 | 18 | 8 | 4 | 8 | 0 | 669 | 0.0669 |
| glm52-off | 185 | 183 | 319 | 142 | 258 | 142 | 0 | 2702 | 0.2702 |
| glm52-high | 36 | 36 | 66 | 32 | 50 | 32 | 0 | 2598 | 0.2598 |
| glm52-max | 82 | 82 | 125 | 44 | 91 | 44 | 0 | 2741 | 0.2741 |
| baseline | 185 | 0 | 0 | 0 | 0 | 0 | 0 | — | — |

## Why the dropper stayed inert

- `dropper.waiting_for_reflection` always had `sameRunReflections = 0`.
- Every `dropper.not_ready` had `maxDropsAllowed = 0` and `tokensOverTarget = 0`.
- In the low grid, the active pool never crossed the target (`observationsPoolTargetTokens = 10000`).
- The fullest observed pool in the low grid was `glm52-max` at `2741` tokens (`27.41%` fullness), still far below target.

## Reflector contrast

Recorded reflections are a subset of reflector completions, and that gap varies by model:

- `gpt55-low`: `reflector.result 38` vs `om.reflections.recorded 25`
- `gpt54mini-off`: `190` vs `168`
- `glm52-off`: `180` vs `142`

So worker model changes reflector yield, but it does **not** change the drop outcome here because the pool never becomes over-target.

## Model/config differences

- `glm52-*` builds the fullest pools and the most not-ready checks.
- `gpt54mini-*` and `gpt55-*` produce more modest pools.
- `xhigh` configs are smallest/least reflective.
- None of them reach the drop threshold.

## Make dropper behavior observable

Run a forced-over-target experiment:

1. Lower `observationsPoolTargetTokens` to a few hundred tokens, or preseed a synthetic run with enough observations to exceed 10k.
2. Ensure the reflector appends at least one same-run reflection.
3. Assert all three downstream signals appear:
   - `dropper.stage_start`
   - `dropper.result` with `selected_nonempty` or `all_filtered`
   - `om.observations.dropped`

That would turn the dropper from a silent gate into a testable path.

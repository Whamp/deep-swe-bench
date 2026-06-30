# OM Reflector/Dropper Inventory (deepseek-v4-flash + gpt-5.5 low)

Scope paths:
- `results/deepseek-v4-flash/high/observational-memory`
- `results/gpt-5.5/low/observational-memory-gpt55-low`
- `results/gpt-5.5/low/observational-memory-gpt54mini-low`
- `results/gpt-5.5/low/observational-memory-gpt54-off`
- `results/gpt-5.5/low/observational-memory-gpt55-off`
- `results/gpt-5.5/low/observational-memory-gpt54mini-off`
- `results/gpt-5.5/low/observational-memory-gpt54mini-xhigh`
- `results/gpt-5.5/low/observational-memory-glm52-off`
- `results/gpt-5.5/low/analysis-36v1-observer-grid`
- `results/gpt-5.5/low/baseline`

Artifacts:
- `analysis/om-reflector-dropper-workflow/inventory_metrics.json`
- `analysis/om-reflector-dropper-workflow/inventory_metrics.csv`

## 1) Presence/volume by dataset

| config | tasks | session files | obs records | reflection records | observer events | reflector events | dropper events |
|---|---:|---:|---:|---:|---:|---:|---:|
| DeepSeek v4 flash OM | 113 | 113 | 5462 | 969 | 0 | 0 | 0 |
| gpt55-low | 12 | 36 | 554 | 94 | 74 / 74 | 38 / 38 | 75 |
| gpt55-off | 36 | 108 | 1468 | 332 | 211 / 211 | 169 / 169 | 300 |
| gpt54mini-off | 113 | 185 | 2788 | 673 | 378 / 378 | 190 / 190 | 457 |
| gpt54mini-low | 113 | 185 | 2314 | 426 | 381 / 381 | 198 / 198 | 477 |
| glm52-off | 113 | 185 | 3789 | 737 | 358 / 358 | 180 / 180 | 400 |
| gpt54-off | 36 | 108 | 1408 | 268 | 227 / 227 | 200 / 200 | 357 |
| gpt54mini-xhigh | 12 | 36 | 206 | 33 | 46 / 46 | 17 / 17 | 12 |
| gpt5.5 low baseline | 113 | 185 | 0 | 0 | 0 | 0 | 0 |
| gpt5.5 36_v1 baseline+observers artifacts | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

**Format note:** `observer events` = `observer.appended / observer.records`; `reflector events` = `reflector.result / reflector.agent_start`.

## 2) Reflector outcomes by run

| config | reflector reasons | no_tool_call / reflector_result | accepted / total | filtered / total |
|---|---|---:|---:|---:|
| gpt55-low | accepted_nonempty: 29, no_tool_call: 9 | 9 / 38 (23.7%) | 29 / 38 (76.3%) | 0 |
| gpt55-off | accepted_nonempty: 90, no_tool_call: 79 | 79 / 169 (46.7%) | 90 / 169 (53.2%) | 0 |
| gpt54mini-off | accepted_nonempty: 181, all_filtered: 5, no_tool_call: 4 | 4 / 190 (2.1%) | 181 / 190 (95.3%) | 5 / 190 (2.6%) |
| gpt54mini-low | accepted_nonempty: 173, all_filtered: 2, no_tool_call: 23 | 23 / 198 (11.6%) | 173 / 198 (87.4%) | 2 / 198 (1.0%) |
| glm52-off | accepted_nonempty: 166, no_tool_call: 14 | 14 / 180 (7.8%) | 166 / 180 (92.2%) | 0 |
| gpt54-off | accepted_nonempty: 100, no_tool_call: 100 | 100 / 200 (50.0%) | 100 / 200 (50.0%) | 0 |
| gpt54mini-xhigh | accepted_nonempty: 16, no_tool_call: 1 | 1 / 17 (5.9%) | 16 / 17 (94.1%) | 0 |

## 3) Dropper behavior (requested direct check)

Observed event names:
- `dropper.waiting_for_reflection`
- `dropper.not_ready`

Observed event names that would indicate active dropping:
- **none** (`dropper.drop`, `dropper.dropped`, etc. never appeared in these paths).

For all runs where `dropper.not_ready` appeared:
- `maxDropsAllowed` = 0 in every payload
- `tokensOverTarget` = 0 in every payload
- `sameRunReflections` = 0 in every `dropper.waiting_for_reflection`

This means the dropper path was not actually dropping records in these datasets; it only reported “waiting”/not-ready states.

### Dropper-not-ready mix

| config | waiting | not_ready | not_ready share |
|---|---:|---:|---:|
| gpt55-low | 50 | 25 | 33.3% |
| gpt55-off | 215 | 85 | 28.3% |
| gpt54mini-off | 289 | 168 | 36.8% |
| gpt54mini-low | 311 | 166 | 34.8% |
| glm52-off | 258 | 142 | 35.5% |
| gpt54-off | 260 | 97 | 27.2% |
| gpt54mini-xhigh | 4 | 8 | 66.7% |

## 4) Key contrasts

- **DeepSeek high (observational-memory)**: has OM record streams (`om.observations.recorded`, `om.reflections.recorded`) but **no debug/event stream** under results, so no direct runtime reflector/dropper event metrics available there.
- **GPT-5.5 low configs** all produce complete observer/reflector/dropper debug event streams at run scope.
- Within GPT-5.5 low, the only difference across workers is event frequency/quality mix (`accepted_nonempty` vs `no_tool_call`, append/error/error-like behavior), not the existence of an actual drop mechanism.

## 5) Raw evidence files touched

- `results/deepseek-v4-flash/high/observational-memory/abs-module-cache-flags/rep0/session/2026-06-25T20-11-53-026Z_019f0069-0f42-781a-987b-efbf65bfa68f.jsonl` (contains `om.observations.recorded` and `om.reflections.recorded`)
- `results/gpt-5.5/low/observational-memory-gpt54mini-low/obsidian-linter-auto-table-of-contents/rep2/pi-agent/observational-memory/debug/019f0c9f-a8da-76ae-a784-c385024587f4.ndjson` (contains reflector/dropper/observer event stream)
- `analysis/om-reflector-dropper-workflow/inventory_metrics.json`
- `analysis/om-reflector-dropper-workflow/inventory_metrics.csv`

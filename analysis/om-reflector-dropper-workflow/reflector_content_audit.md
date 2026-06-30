# Reflector content audit

Scope: `om.reflections.recorded` inside `session/*.jsonl` for DeepSeek high OM and the GPT-5.5 low OM variants present in `results/`.
Machine-readable summary: `analysis/om-reflector-dropper-workflow/reflector_content_audit.json`.

## 1) Volume / depth

| config | reflection records | avg tokens | avg supporting obs | exact dupes |
|---|---:|---:|---:|---:|
| DeepSeek v4 flash high OM | 343 | 54.88 | 1.44 | 4 |
| gpt55-low | 85 | 58.01 | 1.53 | 0 |
| gpt55-off | 271 | 56.23 | 1.35 | 3 |
| gpt55-xhigh | 75 | 76.67 | 2.63 | 0 |
| gpt54-low | 80 | 71.75 | 1.59 | 1 |
| gpt54-off | 228 | 53.46 | 1.35 | 9 |
| gpt54-xhigh | 53 | 105.26 | 1.85 | 0 |
| gpt54mini-low | 361 | 51.38 | 1.92 | 19 |
| gpt54mini-off | 541 | 47.74 | 1.61 | 28 |
| gpt54mini-xhigh | 33 | 71.52 | 1.70 | 0 |
| glm52-off | 650 | 86.38 | 2.27 | 2 |
| glm52-high | 114 | 99.16 | 2.46 | 0 |
| glm52-max | 160 | 123.35 | 3.13 | 0 |
| baseline | 0 | 0 | 0 | 0 |

Notes:
- `avg supporting obs` = mean `supportingObservationIds.length`.
- `exact dupes` = duplicate `content` strings within the same config.
- I did not find a first-class rejection field inside `om.reflections.recorded`; rejection-ish outcomes only show up in the separate reflector debug stream (`accepted_nonempty`, `no_tool_call`, `all_filtered`).

## 2) Style buckets

Heuristic buckets: requirement/constraint, implementation plan, test/failure state, completion/self-report, repo survey, noise.

- **DeepSeek high** skews toward repo survey + implementation plan, with relatively balanced coverage and low duplication. It is the cleanest “spec + architecture” style of the group.
- **gpt54mini-low/off** skew hard toward completion/self-report and implementation-plan chatter. They have the highest exact-duplicate counts; many reflections are just prompt/process restatements.
- **gpt54/gpt55 xhigh** produce fewer reflections, but the ones they do emit are denser: more tokens per reflection and more supporting observations.
- **glm52-off/high/max** are the most verbose and evidence-heavy. They lean toward repo survey + implementation plan, and max is the deepest setting overall.

A few useful vs harmful examples:
- Useful: `ConsistentHash runtime behavior invariants: empty {} produces hash_policy entries ... header regexRewrite rewrites value before hashing.`
- Useful: `TrafficPolicy code architecture: API type definitions in ... consistentHash is applied as hash_policy on RouteAction, not as a separate HTTP filter.`
- Harmful: `User wants the work done on a new branch from main and committed when finished.`
- Harmful: `Work should be done on the branch add-trafficpolicy-consistent-hash created from main, and the user wants it committed when finished.`

## 3) Head-to-head: gpt54mini-low vs glm52-off on the shared kgateway task

| config | reflection records | avg tokens | avg supporting obs | style mix |
|---|---:|---:|---:|---|
| gpt54mini-low | 7 | 48.86 | 1.14 | 4 completion/self-report, 3 repo survey |
| glm52-off | 20 | 95.50 | 2.15 | 11 repo survey, 4 completion/self-report, 2 implementation plan, 2 test/failure, 1 noise |

Takeaway: `gpt54mini-low` mostly repeats process-level reminders plus a little repo surveying; `glm52-off` records more task-specific, support-backed, and implementation-aware reflections.

## 4) Dropper note

For the GPT-5.5 low runs, the dropper never actually dropped anything: the inventory still shows only `dropper.waiting_for_reflection` / `dropper.not_ready`, with `maxDropsAllowed=0`, `tokensOverTarget=0`, and no `dropper.drop`/`dropper.dropped` events. DeepSeek high OM does not expose the same debug stream under `results/`, so that part is only directly confirmable for the GPT-5.5 low configs.

## 5) Commands used

- `python` scan of `results/**/session/*.jsonl`, filtering `customType == "om.reflections.recorded"`.
- Aggregation script that wrote `analysis/om-reflector-dropper-workflow/reflector_content_audit.json`.
- Spot-checks with `python` against `results/gpt-5.5/low/observational-memory-gpt54mini-low/kgateway-consistent-hash-policy` and `results/gpt-5.5/low/observational-memory-glm52-off/kgateway-consistent-hash-policy`.

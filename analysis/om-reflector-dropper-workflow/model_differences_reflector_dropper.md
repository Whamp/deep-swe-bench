# OM reflector / dropper model differences

Scope:
- `results/gpt-5.5/low/observational-memory-*`
- `results/deepseek-v4-flash/high/observational-memory`

Sources:
- session JSONL (`om.reflections.recorded`)
- debug NDJSON (`reflector.*`, `dropper.*`)

## Bottom line

- **The dropper never actually drops records** in these runs: `drop_actual = 0` everywhere, `maxDropsAllowed = 0` everywhere, and `sameRunReflections = 0` on every `dropper.waiting_for_reflection` payload.
- **GLM-5.2 is the strongest coverage family**: it has the highest support density, the highest fullness pressure, and the most `none→strong` / `partial→strong` transitions.
- **GPT-5.4-mini off is the noisiest reflector**: it has the most accepted reflections, but also the only meaningful reject/duplicate mass.
- **GPT-5.5 low/off are shallow**; `xhigh` shrinks reflector throughput further instead of improving depth.

## Main comparison

`coverage strong` = total `none→strong + partial→strong` transitions across all relevance buckets.

| config | cells | refl/cell | tok/ref | reflector start/result/error | accepted/rejected/dup | support ids total / avg-ref | drop wait/not_ready/act | fullness mean/p90 | coverage none→partial / strong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| gpt55-low | 36 | 2.61 | 58.3 | 38/38/4 | 120/1/0 | 213 / 1.47 | 50/25/0 | 0.081 / 0.123 | 208 / 3 |
| gpt55-off | 108 | 3.07 | 55.7 | 169/169/5 | 356/1/0 | 581 / 0.98 | 215/85/0 | 0.072 / 0.118 | 556 / 13 |
| gpt55-xhigh | 36 | 2.14 | 76.7 | 19/19/3 | 97/0/0 | 253 / 2.36 | 18/15/0 | 0.090 / 0.150 | 247 / 3 |
| gpt54-low | 36 | 2.50 | 71.0 | 40/40/1 | 95/0/0 | 159 / 1.70 | 54/36/0 | 0.071 / 0.123 | 157 / 1 |
| gpt54-off | 108 | 2.48 | 53.2 | 200/200/3 | 278/0/0 | 457 / 0.95 | 260/97/0 | 0.071 / 0.139 | 423 / 22 |
| gpt54-xhigh | 36 | 1.53 | 105.9 | 32/32/8 | 85/0/0 | 174 / 1.73 | 30/17/0 | 0.063 / 0.099 | 174 / 0 |
| gpt54mini-low | 185 | 2.30 | 50.8 | 198/198/7 | 439/23/0 | 906 / 1.96 | 311/166/0 | 0.048 / 0.082 | 852 / 38 |
| gpt54mini-off | 185 | 3.64 | 47.9 | 190/190/13 | 734/41/45 | 1276 / 1.76 | 289/168/0 | 0.057 / 0.094 | 1057 / 157 |
| gpt54mini-xhigh | 36 | 0.92 | 71.5 | 17/17/8 | 63/5/1 | 125 / 1.93 | 4/8/0 | 0.046 / 0.057 | 119 / 3 |
| glm52-off | 185 | 3.98 | 87.4 | 180/180/24 | 863/3/0 | 2102 / 2.40 | 258/142/0 | 0.120 / 0.188 | 1842 / 140 |
| glm52-max | 82 | 2.23 | 124.9 | 74/74/28 | 300/1/0 | 965 / 3.23 | 91/44/0 | 0.132 / 0.220 | 920 / 24 |
| glm52-high | 36 | 3.83 | 98.4 | 36/36/4 | 157/1/0 | 420 / 2.79 | 50/32/0 | 0.112 / 0.197 | 356 / 32 |

## Notes

- Debug metrics are from the available NDJSON files; a few cells are missing debug logs in `gpt55-off`, `gpt54mini-*`, and `glm52-off`.
- `gpt54mini-off` is the only config with meaningful `all_filtered` + duplicate mass (`41` rejected, `45` duplicates).
- `gpt55-off` and `gpt54-off` spend a lot of time in `no_tool_call` mode; both still keep dropper fullness low and never trigger actual drops.
- Strong transitions are concentrated in `gpt54mini-off` and `glm52-off`; `xhigh` variants mostly stay in `none→partial`.

## DeepSeek context

`results/deepseek-v4-flash/high/observational-memory` has **113 cells**, **969 recorded reflections** (`8.58` reflections/cell), and **56,162 reflection tokens** (`58.0` tokens/reflection). It has **no debug NDJSON in results**, so reflector/dropper runtime metrics are unavailable there.

Baseline comparison (`results/gpt-5.5/low/baseline`) has zero OM activity.

# DeepSWE agentic inference workload profile

## Verdict

A single average request is not a faithful coding-agent benchmark. The corpus starts near 2k prompt tokens, reaches a median 45k context by turn 40, and ends at a median 41k context. The recommended benchmark is therefore a 41-request progression: one cold request, then eight requests in each of five normalized conversation stages.

## Denominator and method

- 9,236 canonical root trajectories across 113 tasks
- 481,152 nonzero assistant requests
- 8,249 trajectories with direct cache usage; 987 with cache-friendly shape estimated from context growth
- 18 result cells lacked a root session and were excluded
- Excluded every underscore-prefixed result tree, including `_contaminated/` and `_archives/`
- Mapping: `depth = cacheRead`, `pp = input + cacheWrite`, `context = depth + pp`, `tg = output`

## Request-weighted distribution

| Metric | Mean | Mean below p99 | p25 | p50 | p75 | p90 | p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Cached depth | 45,676 | 43,934 | 16,896 | 32,768 | 65,024 | 104,448 | 181,760 |
| New prompt / pp | 3,067 | 2,225 | 422 | 872 | 1,845 | 4,972 | 55,540 |
| Generated / tg | 326 | 257 | 54 | 100 | 268 | 692 | 3,432 |
| Total input context | 48,743 | 47,002 | 19,879 | 35,593 | 68,253 | 106,011 | 183,506 |

The median trajectory has 41 requests, reaches 41,018 tokens, and generates 8,474 tokens in total. Context shrank on 1,434 of 471,919 follow-up transitions (0.3%), usually because of compaction or reset.

## Recommended 41-request trajectory

Run each row separately; llama-benchy takes a Cartesian product when several values are passed together.

| Phase | Repetitions | `--depth` | `--pp` | `--tg` |
|---|---:|---:|---:|---:|
| Cold start | 1 | 0 | 2,048 | 64 |
| Stage 1 · 0-20% | 8 | 9,216 | 2,304 | 160 |
| Stage 2 · 20-40% | 8 | 26,624 | 1,792 | 224 |
| Stage 3 · 40-60% | 8 | 35,072 | 1,536 | 192 |
| Stage 4 · 60-80% | 8 | 43,008 | 1,792 | 160 |
| Stage 5 · 80-100% | 8 | 50,688 | 2,048 | 160 |

Use `--enable-prefix-caching` for the five staged rows. The cold row uses depth 0. These generated-token counts represent balanced per-trajectory stage averages, not fixed completion caps observed in production; `--exact-tg` is appropriate only when you intentionally want fixed-length throughput comparability.

## Absolute progression

| Turn | Trajectories reaching turn | Median context | Median depth | Median pp | Median tg |
|---:|---:|---:|---:|---:|---:|
| 1 | 9,233 (100.0%) | 1,950 | 0 | 1,793 | 58 |
| 2 | 9,204 (99.7%) | 3,443 | 1,536 | 1,631 | 57 |
| 5 | 9,112 (98.7%) | 9,904 | 5,632 | 2,824 | 58 |
| 10 | 9,073 (98.2%) | 18,510 | 15,872 | 1,402 | 88 |
| 20 | 8,485 (91.9%) | 26,866 | 25,088 | 944 | 125 |
| 40 | 4,965 (53.8%) | 44,927 | 42,496 | 729 | 97 |
| 60 | 2,549 (27.6%) | 71,164 | 68,096 | 611 | 104 |
| 100 | 908 (9.8%) | 107,040 | 105,472 | 357 | 134 |
| 150 | 286 (3.1%) | 133,964 | 133,498 | 180 | 116 |
| final | 9,233 (100.0%) | 40,878 | 37,376 | 561 | 149 |

## Caveats

- This is the empirical result corpus, not a balanced sample of configs or models. GPT-5.5 contributes 4,831 of 9,236 trajectories.
- Request weighting describes serving demand but overweights long trajectories. The normalized recipe first gives every trajectory equal weight within each stage.
- Cache shape is derived for APIs that report no cache tokens. Context totals and output tokens remain provider-reported; only the depth/pp split is estimated.
- A static llama-benchy request measures a slice of the trajectory. It does not reproduce persistent KV residency, compaction, scheduler contention, or tool latency across a live 41-turn session.

## Reproduction

```bash
python3 analysis/agentic-inference-profile/build_profile.py
python3 analysis/agentic-inference-profile/render_report.py
```

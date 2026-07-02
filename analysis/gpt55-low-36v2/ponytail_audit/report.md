# GPT-5.5 low 36_v2 ponytail audit

All four configs are complete: 36 tasks × 3 reps = 108 cells each. Task-weighted means equal cell-level means here because every task has 3 complete reps.

## Quality / effort
| config | cells solved | tasks solved any | mean partial | wall s/cell | turns/cell | tool calls/cell | patch bytes/cell |
|---|---:|---:|---:|---:|---:|---:|---:|
| baseline | 33/108 | 17/36 | 0.9675 | 252.2 | 39.89 | 38.97 | 13,842 |
| ponytail-lite | 28/108 | 13/36 | 0.9684 | 321.3 | 43.27 | 42.77 | 13,810 |
| ponytail-full | 30/108 | 14/36 | 0.9729 | 311.7 | 44.61 | 43.98 | 14,089 |
| ponytail-ultra | 30/108 | 17/36 | 0.9717 | 298.1 | 42.12 | 41.52 | 13,452 |

## Token / cost breakdown
| config | input tokens/cell | cache read/cell | output tokens/cell | total/combined/cell | cost/cell |
|---|---:|---:|---:|---:|---:|
| baseline | 82.9k | 659.0k | 6.7k | 748.6k | $0.945 |
| ponytail-lite | 97.4k | 926.9k | 7.1k | 1.03M | $1.164 |
| ponytail-full | 100.1k | 933.5k | 7.1k | 1.04M | $1.179 |
| ponytail-ultra | 99.6k | 861.6k | 6.8k | 967.9k | $1.132 |

## Baseline deltas (per cell)
| config | Δ total tokens | Δ output tokens | Δ input tokens | Δ cache read | Δ turns | Δ tool calls | Δ wall s | Δ cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| ponytail-lite | 282.8k (+37.8%) | 442 (+6.6%) | 14.5k (+17.5%) | 267.9k (+40.6%) | 3.38 | 3.80 | 69.1 | $+0.220 |
| ponytail-full | 292.0k (+39.0%) | 377 (+5.6%) | 17.2k (+20.8%) | 274.4k (+41.6%) | 4.72 | 5.01 | 59.5 | $+0.235 |
| ponytail-ultra | 219.3k (+29.3%) | 93 (+1.4%) | 16.7k (+20.1%) | 202.5k (+30.7%) | 2.23 | 2.55 | 45.9 | $+0.188 |

### Interpretation
- Yes: all Ponytail configs use more total tokens than baseline; `combined_total_tokens == total_tokens` in these runs because advisor/OM worker counts are zero.
- Output tokens rise only slightly (+1% to +7%), while cache-read tokens rise +31% to +42% and explain ~92% to ~95% of the total-token delta.
- Ponytail also adds ~2.2 to ~4.7 turns and ~2.5 to ~5.0 tool calls per cell, so the extra cache reads line up with longer/more tool-heavy trajectories.
- Final patch size is basically flat; patch bytes are not the cost driver.

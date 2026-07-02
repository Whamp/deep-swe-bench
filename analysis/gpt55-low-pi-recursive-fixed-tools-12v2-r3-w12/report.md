# GPT-5.5 low pi-recursive fixed-tools analysis — 12_v2 × 3 reps

Run: `results/gpt-5.5/low/pi-recursive`  
Track: `results/gpt-5.5/low/logs/pi-recursive-fixed-tools-12v2-r3-w12.out`  
Baseline: `results/gpt-5.5/low/baseline` on the same 12_v2 task/rep cells.

## Verdict

The fixed read-only tools changed pi-recursive from a compromised negative result into a small positive result on this 36-cell slice, but it is still an expensive intervention.

- Solves: baseline 11/36 → pi-recursive 13/36 (`+2`).
- Mean partial: baseline 0.973871 → pi-recursive 0.981620 (`+0.007749`).
- Mean f2p: baseline 0.864094 → pi-recursive 0.894301 (`+0.030208`).
- Mean p2p: baseline 0.996808 → pi-recursive 0.998227 (`+0.001419`).
- Median combined tokens: baseline 591,340 → pi-recursive 1,119,740.
- Median combined cost: baseline $0.840 → pi-recursive $1.541.
- Median wall: baseline 198.7s → pi-recursive 330.1s.

Compared with the compromised read-only-tools run, fixed-tools gained +4 solves, +0.0067 mean partial, and lowered median combined cost from $1.912 to $1.541.

The partial lift is not statistically secure at this sample size: paired mean delta +0.0077, bootstrap 95% CI [-0.0128, 0.0313], Wilcoxon p=0.239. Solve flips were 7 positive vs 5 negative, binomial p=0.774.

## Recursive overhead

- Every cell made at least one child call.
- Total recursive child calls: 66.
- Median child calls/cell: 1.0.
- Total child tokens: 16,451,068.
- Total child cost: $26.6653.
- Child share of combined tokens: 26.9%.
- Child share of combined cost: 35.4%.

Largest child-cost outlier: `goreleaser-retry-publish-auditing/rep2` with 9 child calls, 6.69M child tokens, and $8.57 child cost.

## Task-level movement

| task | baseline solves | recursive solves | Δ mean partial | mean Δ combined cost | child calls |
|---|---:|---:|---:|---:|---:|
| `superjson-error-stack-serialization` | 0 | 2 | +0.022 | $+0.750 | 4 |
| `obsidian-linter-link-format-conversion` | 2 | 2 | +0.000 | $+0.653 | 3 |
| `participle-grammar-conflict-analysis` | 0 | 0 | +0.101 | $+1.486 | 7 |
| `dateutil-rfc5545-timezone-interop` | 0 | 0 | -0.001 | $+0.496 | 6 |
| `langchain-request-coalescing` | 1 | 0 | -0.002 | $+0.768 | 4 |
| `claude-code-by-agents-recursive-delegation` | 2 | 0 | -0.096 | $+0.727 | 4 |
| `go-critic-doc-link-checker` | 2 | 2 | +0.000 | $+0.682 | 9 |
| `mobly-grouped-test-barriers` | 0 | 1 | +0.012 | $+0.832 | 5 |
| `tengo-callable-instance-isolation` | 0 | 1 | +0.055 | $+0.429 | 3 |
| `adaptix-name-mapping-aliases` | 0 | 1 | +0.002 | $+2.330 | 3 |
| `goreleaser-retry-publish-auditing` | 3 | 3 | +0.000 | $+3.575 | 13 |
| `sql-formatter-bigquery-pipe-formatting` | 1 | 1 | +0.000 | $+1.745 | 5 |

## Interpretation

The read-only-tool fix appears meaningful: no smoke-contract failures, no missing `rg`/`fd` strings in fixed results, no `Max calls exceeded`, no extension debug marker pollution, and all top-level child launches reported `readOnly=true`, `jj=none`, `exitCode=0`.

The main positive signal is f2p/near-miss conversion on a few tasks (`superjson`, `participle`, `tengo`, `mobly`, `adaptix`). The main negative signal is threshold loss on `claude-code-by-agents-recursive-delegation` and one `go-critic-doc-link-checker` rep.

This is promising enough to keep pi-recursive in the comparison set, but not enough to call it a win generally. It needs a larger neutral subset or a cheaper policy because the median combined cost and wall time increased materially.

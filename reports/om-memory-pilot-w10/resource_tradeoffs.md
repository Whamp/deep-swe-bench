# Resource tradeoffs: OM vs baseline

Sources:
- `runs/om-memory-pilot-w10/reports/paired_manifest.json`
- `runs/om-memory-pilot-w10/reports/initial_summary.md`
- `runs/om-memory-pilot-w10/reports/pair_7_expensive_wins.md`
- `runs/om-memory-pilot-w10/reports/pair_1_top_losses.md`
- OM patch files under `runs/om-memory-pilot-w10/pi-observational-memory/*/rep0/artifacts/model.patch`

## Bottom line
OM improved quality, but the extra spend is mostly **main-session iteration/context**, not raw patch breadth.

Across 113 pairs, the median delta was:
- `+1,830,763` tokens
- `+$0.059`
- `+144s`
- `+20` turns
- `+21` tool calls
- `+5,025` patch bytes
- `6` files changed (`model.patch` median)
- `15` hunks (`model.patch` median)

Quality moved the right way overall:
- mean partial `0.774 -> 0.856`
- solves `2/113 -> 10/113`

Because OM worker model calls are excluded from totals, this token gap is not hidden worker inference. It is the main session doing more turns, more tool calls, and carrying more accumulated context.

## What actually tracks the token gap
Computed from `runs/om-memory-pilot-w10/reports/paired_manifest.json`:

| metric | Pearson r vs token delta | Spearman ρ | median delta |
|---|---:|---:|---:|
| turns | `0.96` | `0.95` | `+20` |
| tool calls | `0.95` | `0.93` | `+21` |
| file count | `0.21` | `0.22` | `+6` |
| hunks | `0.27` | `0.25` | `+15` |
| patch bytes | `0.09` | `0.38` | `+5,025` |

Token growth also rises sharply with iteration depth:
- `0-9` turns: median `+0.73M` tokens
- `10-19` turns: median `+1.60M`
- `20-39` turns: median `+2.59M`
- `40-99` turns: median `+7.10M`
- `100+` turns: median `+16.72M`

File breadth moves the median much less:
- `0-4` files: median `+1.65M` tokens
- `5-7` files: median `+1.83M`
- `8-12` files: median `+2.31M`
- `13+` files: median `+3.07M`

## Interpretation
Patch breadth matters when it forces extra tests, fixtures, or cross-file wiring, but it does **not** explain most of the token burn.

The expensive wins in `runs/om-memory-pilot-w10/reports/pair_7_expensive_wins.md` are mostly expensive because they loop through many turns/tests:
- `koota-pair-relation-tracking`: `+35.5M` tokens, `+212` turns, `+216` tool calls
- `fastapi-implicit-head-options`: `+20.6M` tokens, `+196` turns, `+203` tool calls
- `yaegi-go-embed-directives`: `+17.6M` tokens, `+127` turns, `+129` tool calls

But breadth alone is not enough to predict cost. Two counterexamples from OM patch files:
- `runs/om-memory-pilot-w10/pi-observational-memory/dynamodb-toolbox-lazy-recursive-schemas/rep0/artifacts/model.patch`: `39` files, `+2` turns, `-887,590` tokens
- `runs/om-memory-pilot-w10/pi-observational-memory/sqlfmt-create-table-ddl-formatting/rep0/artifacts/model.patch`: `3` files, `+80` turns, `+11,599,323` tokens

So the cleanest read is:
- **primary driver:** more main-session turns/tool calls, i.e. exploration + verification + context growth
- **secondary driver:** patch breadth when the fix genuinely spans files or needs generated artifacts

## Caveats
- Correlation is observational, not causal.
- `file count`, `hunks`, and `patch bytes` are proxies for breadth, not semantic complexity.
- OM worker-model calls are excluded from the totals, so this report only explains main-session spend.

## Recommended next assets
- `runs/om-memory-pilot-w10/reports/pair_7_expensive_wins.md`
- `runs/om-memory-pilot-w10/reports/pair_1_top_losses.md`
- `runs/om-memory-pilot-w10/reports/pair_3_pathology_rescues.md`
- `runs/om-memory-pilot-w10/reports/paired_manifest.json`
- `runs/om-memory-pilot-w10/reports/initial_summary.md`

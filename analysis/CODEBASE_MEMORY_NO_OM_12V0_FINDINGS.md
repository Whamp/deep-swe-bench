# Codebase-memory no-OM 12_v0 findings

Date: 2026-07-01

Context: rerun requested after GitHub issue #1 reported that pi-observational-memory (OM) observations/reflections do not reach the headless task agent in the tested regime. These configs remove OM entirely and keep only the local codebase-memory-mcp instrumentation.

## Configs

All runs: `openai-codex/gpt-5.5`, thinking `low`, subset `12_v0`, 3 reps, no OM workers.

- `baseline`: no codebase-memory.
- `codebase-memory`: read augmentation, initial index only.
- `codebase-memory-reindex`: read augmentation + background reindex after edits/writes.
- `codebase-memory-bash-hook`: bash search/discovery augmentation + background reindex after edits/writes; no read augmentation.

## Health

| config | cells | bad cells | OM worker cells | median CMB blocks | median reindexes |
|---|---:|---:|---:|---:|---:|
| baseline | 36 | 0 | 0 | 0.0 | 0.0 |
| codebase-memory | 36 | 0 | 0 | 9.5 | 0.0 |
| codebase-memory-reindex | 36 | 0 | 0 | 10.5 | 12.0 |
| codebase-memory-bash-hook | 36 | 0 | 0 | 5.0 | 10.0 |

## Headline results

| config | solves | solve rate | mean partial | median tokens | median cost |
|---|---:|---:|---:|---:|---:|
| baseline | 9/36 | 0.250 | 0.990 | 742,821 | $0.92 |
| codebase-memory | 13/36 | 0.361 | 0.941 | 906,126 | $1.10 |
| codebase-memory-reindex | 12/36 | 0.333 | 0.951 | 1,001,974 | $1.21 |
| codebase-memory-bash-hook | 9/36 | 0.250 | 0.932 | 879,661 | $1.14 |

## Paired deltas vs baseline

Bootstrap CI over the 36 matched task/rep cells.

| config | solve delta | solve 95% CI | partial delta | partial 95% CI | median token delta | median cost delta |
|---|---:|---:|---:|---:|---:|---:|
| codebase-memory | +0.111 | [-0.028, +0.250] | -0.049 | [-0.120, -0.002] | +141,895 | +$0.19 |
| codebase-memory-reindex | +0.083 | [-0.028, +0.194] | -0.039 | [-0.093, -0.000] | +222,278 | +$0.20 |
| codebase-memory-bash-hook | +0.000 | [-0.167, +0.167] | -0.058 | [-0.136, -0.004] | +107,629 | +$0.08 |

## Per-task summary

Each cell is `solves/3 mean_partial`.

| task | baseline | codebase-memory | reindex | bash-hook |
|---|---:|---:|---:|---:|
| actionlint-action-pinning-lint | 2/3 0.998 | 3/3 1.000 | 3/3 1.000 | 3/3 1.000 |
| anko-default-function-arguments | 0/3 0.986 | 0/3 0.989 | 0/3 0.972 | 0/3 0.986 |
| awilix-async-container-initialization | 1/3 0.996 | 3/3 1.000 | 1/3 0.996 | 2/3 0.998 |
| boa-hierarchical-evaluation-cancellation | 0/3 0.944 | 0/3 0.708 | 0/3 0.514 | 0/3 0.931 |
| cattrs-partial-structuring-recovery | 3/3 1.000 | 3/3 1.000 | 3/3 1.000 | 1/3 0.978 |
| dynamodb-toolbox-lazy-recursive-schemas | 0/3 0.983 | 0/3 0.984 | 0/3 0.986 | 0/3 0.987 |
| fastapi-implicit-head-options | 0/3 0.994 | 0/3 0.935 | 0/3 0.966 | 0/3 0.938 |
| httpx-streaming-json-iteration | 1/3 0.999 | 1/3 0.998 | 1/3 0.999 | 0/3 0.998 |
| kgateway-consistent-hash-policy | 0/3 0.991 | 0/3 0.991 | 0/3 0.991 | 0/3 0.991 |
| mashumaro-flattened-dataclass-fields | 0/3 0.999 | 0/3 1.000 | 0/3 0.999 | 0/3 0.999 |
| ts-pattern-match-each | 1/3 0.993 | 1/3 0.685 | 2/3 0.996 | 1/3 0.377 |
| yjs-map-conflict-detection | 1/3 0.997 | 2/3 0.999 | 2/3 0.997 | 2/3 0.997 |

## Interpretation

- The clean no-OM read hook is the best full-solve result among these no-OM CMB variants: 13/36 vs baseline 9/36.
- That solve gain is not stable enough at 36 cells to call decisive: bootstrap CI includes zero.
- All CMB variants hurt mean partial, with CIs below zero. This is the same pattern as earlier graph-tool experiments: occasional full-solve wins, but context/tooling noise can damage near-complete patches.
- Reindexing does not clearly help on this subset. It costs the most tokens and lands between read-only and bash-hook on solves.
- The bash-search hook did not beat baseline on full solves and had the worst partial. The targeted earlier-discovery idea did not pay off in this implementation on 12_v0.
- The dominant damage is task-specific: read-hook hurts `ts-pattern` and `boa`; reindex badly hurts `boa`; bash-hook badly hurts `ts-pattern` and loses `cattrs` solves.

## Bottom line

Without OM, codebase-memory has a weak solve-rate signal only for the read-hook variant, but no variant clears the bar as a reliable improvement because partial score drops and token cost rises. The result supports treating CMB as an experimental tool, not a replacement for baseline/OM claims.

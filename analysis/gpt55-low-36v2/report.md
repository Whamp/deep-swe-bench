# GPT-5.5 low on 36_v2 summary
Complete configs: baseline, baseline-wf, codebase-memory, codebase-memory-max, codegraph-skill, ponytail-full, ponytail-lite, ponytail-ultra. 36 tasks × 3 reps = 108 cells/config.
## Config ranking
| config | solves/108 | tasks solved | mean partial | median tokens | total cost | median wall | median patch | empty/crash |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| codebase-memory-max | 34/108 (31.5%) | 16/36 | 0.9701 | 0.81M | $126.04 | 247s | 12.9KiB | 0 |
| baseline | 33/108 (30.6%) | 17/36 | 0.9675 | 0.61M | $102.03 | 206s | 12.7KiB | 0 |
| baseline-wf | 31/108 (28.7%) | 14/36 | 0.9793 | 0.65M | $110.15 | 247s | 13.5KiB | 0 |
| codebase-memory | 31/108 (28.7%) | 15/36 | 0.9695 | 0.77M | $121.69 | 229s | 12.7KiB | 0 |
| ponytail-full | 30/108 (27.8%) | 14/36 | 0.9729 | 0.90M | $127.36 | 263s | 12.5KiB | 0 |
| ponytail-ultra | 30/108 (27.8%) | 17/36 | 0.9717 | 0.79M | $122.28 | 245s | 12.2KiB | 0 |
| ponytail-lite | 28/108 (25.9%) | 13/36 | 0.9684 | 0.84M | $125.76 | 256s | 12.3KiB | 0 |
| codegraph-skill | 28/108 (25.9%) | 17/36 | 0.9618 | 0.73M | $118.74 | 248s | 16.9KiB | 0 |

## Paired vs baseline
| config | Δsolves | Δpartial mean | wins/losses/ties | big wins/losses | median Δtokens | median Δcost | median Δwall | median Δpatch | p_wilcoxon |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| codebase-memory-max | +1 | +0.0026 | 38/33/37 | 8/8 | +0.18M | $+0.183 | +29s | +0.3KiB |  |
| baseline-wf | -2 | +0.0119 | 38/35/35 | 11/5 | +0.05M | $+0.069 | +31s | +1.0KiB |  |
| codebase-memory | -2 | +0.0021 | 36/35/37 | 6/6 | +0.17M | $+0.189 | +16s | +0.4KiB |  |
| ponytail-full | -3 | +0.0055 | 41/28/39 | 8/6 | +0.21M | $+0.212 | +36s | -0.1KiB |  |
| ponytail-ultra | -3 | +0.0043 | 34/37/37 | 9/4 | +0.19M | $+0.153 | +24s | -0.6KiB |  |
| ponytail-lite | -5 | +0.0009 | 35/39/34 | 10/8 | +0.20M | $+0.182 | +40s | -0.2KiB |  |
| codegraph-skill | -5 | -0.0056 | 43/34/31 | 6/9 | +0.13M | $+0.138 | +29s | +1.7KiB |  |

## Difficulty bucket means
| config | hard solves/partial | medium solves/partial | easy solves/partial |
|---|---:|---:|---:|
| codebase-memory-max | 4/36 / 0.977 | 10/42 / 0.946 | 20/30 / 0.995 |
| baseline | 6/36 / 0.979 | 11/42 / 0.939 | 16/30 / 0.993 |
| baseline-wf | 6/36 / 0.986 | 8/42 / 0.966 | 17/30 / 0.989 |
| codebase-memory | 6/36 / 0.976 | 10/42 / 0.955 | 15/30 / 0.981 |
| ponytail-full | 4/36 / 0.989 | 9/42 / 0.946 | 17/30 / 0.991 |
| ponytail-ultra | 4/36 / 0.981 | 11/42 / 0.957 | 15/30 / 0.981 |
| ponytail-lite | 4/36 / 0.976 | 7/42 / 0.946 | 17/30 / 0.990 |
| codegraph-skill | 5/36 / 0.979 | 7/42 / 0.942 | 16/30 / 0.969 |

## codebase-memory-max: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.214, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.062, solves 0→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial +0.053, solves 2→3
- tengo-callable-instance-isolation (medium): Δpartial +0.021, solves 0→0
- updo-policy-alerting (hard): Δpartial +0.017, solves 0→0
Top losses:
- go-git-worktree-merge-conflicts (medium): Δpartial -0.211, solves 0→0
- go-critic-doc-link-checker (medium): Δpartial -0.035, solves 2→1
- happy-dom-deterministic-intersectionobserver (hard): Δpartial -0.029, solves 3→2
- superjson-error-stack-serialization (hard): Δpartial -0.012, solves 0→0
- eicrud-keyset-pagination-cursor (medium): Δpartial -0.007, solves 0→0

## baseline-wf: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.306, solves 0→0
- participle-grammar-conflict-analysis (hard): Δpartial +0.098, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.046, solves 0→0
- go-critic-doc-link-checker (medium): Δpartial +0.035, solves 2→3
- tengo-callable-instance-isolation (medium): Δpartial +0.021, solves 0→0
Top losses:
- etree-xml-diff-patch (easy): Δpartial -0.040, solves 0→0
- go-git-worktree-merge-conflicts (medium): Δpartial -0.018, solves 0→0
- superjson-error-stack-serialization (hard): Δpartial -0.012, solves 0→0
- fd-deterministic-multi-key-sorting (medium): Δpartial -0.009, solves 0→0
- koota-query-predicates (hard): Δpartial -0.008, solves 0→0

## codebase-memory: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.263, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.042, solves 0→0
- go-critic-doc-link-checker (medium): Δpartial +0.035, solves 2→3
- vulture-persistent-analysis-cache (hard): Δpartial +0.020, solves 1→1
- updo-policy-alerting (hard): Δpartial +0.010, solves 0→0
Top losses:
- goreleaser-retry-publish-auditing (easy): Δpartial -0.098, solves 3→2
- go-git-worktree-merge-conflicts (medium): Δpartial -0.070, solves 0→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial -0.044, solves 2→1
- koota-query-predicates (hard): Δpartial -0.022, solves 0→0
- superjson-error-stack-serialization (hard): Δpartial -0.020, solves 0→0

## ponytail-full: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.226, solves 0→0
- participle-grammar-conflict-analysis (hard): Δpartial +0.097, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.062, solves 0→1
- vulture-persistent-analysis-cache (hard): Δpartial +0.018, solves 1→0
- updo-policy-alerting (hard): Δpartial +0.017, solves 0→0
Top losses:
- go-git-worktree-merge-conflicts (medium): Δpartial -0.123, solves 0→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial -0.088, solves 2→0
- etree-xml-diff-patch (easy): Δpartial -0.025, solves 0→0
- katex-multicolumn-array-spans (hard): Δpartial -0.015, solves 0→0
- koota-query-predicates (hard): Δpartial -0.008, solves 0→0

## ponytail-ultra: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.239, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.100, solves 0→1
- participle-grammar-conflict-analysis (hard): Δpartial +0.094, solves 0→0
- tengo-callable-instance-isolation (medium): Δpartial +0.034, solves 0→0
- updo-policy-alerting (hard): Δpartial +0.019, solves 0→0
Top losses:
- goreleaser-retry-publish-auditing (easy): Δpartial -0.126, solves 3→2
- go-git-worktree-merge-conflicts (medium): Δpartial -0.070, solves 0→0
- katex-multicolumn-array-spans (hard): Δpartial -0.044, solves 0→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial -0.044, solves 2→1
- koota-query-predicates (hard): Δpartial -0.031, solves 0→0

## ponytail-lite: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.274, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.088, solves 0→0
- vulture-persistent-analysis-cache (hard): Δpartial +0.021, solves 1→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial +0.009, solves 2→2
- wazero-multi-module-snapshots (easy): Δpartial +0.008, solves 2→3
Top losses:
- go-git-worktree-merge-conflicts (medium): Δpartial -0.246, solves 0→0
- etree-xml-diff-patch (easy): Δpartial -0.030, solves 0→0
- httpx-multipart-response-parsing (medium): Δpartial -0.029, solves 3→2
- koota-query-predicates (hard): Δpartial -0.017, solves 0→0
- katex-multicolumn-array-spans (hard): Δpartial -0.013, solves 0→0

## codegraph-skill: biggest task partial deltas vs baseline
Top wins:
- tengo-destructuring-bindings (medium): Δpartial +0.263, solves 0→0
- textual-kitty-key-phases (medium): Δpartial +0.071, solves 0→0
- updo-policy-alerting (hard): Δpartial +0.017, solves 0→0
- vulture-persistent-analysis-cache (hard): Δpartial +0.016, solves 1→1
- eicrud-keyset-pagination-cursor (medium): Δpartial +0.007, solves 0→0
Top losses:
- etree-xml-diff-patch (easy): Δpartial -0.224, solves 0→1
- go-git-worktree-merge-conflicts (medium): Δpartial -0.175, solves 0→0
- go-critic-doc-link-checker (medium): Δpartial -0.070, solves 2→0
- claude-code-by-agents-recursive-delegation (medium): Δpartial -0.035, solves 2→1
- tengo-callable-instance-isolation (medium): Δpartial -0.030, solves 0→0

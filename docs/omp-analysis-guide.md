# OMP analysis guide: Pi comparison, tool ablations, and harness forensics

This repository contains a controlled evaluation of Oh My Pi (OMP) against the Pi coding agent, followed by OMP prompt and toolset ablations. The comparisons use DeepSWE tasks, `openai-codex/gpt-5.5`, and fixed thinking levels. Each main `36_v2` result covers 36 tasks with 3 reps per task, or 108 reps per config.

## Start here

The best entry point is the [cleaned 36_v2 OMP comparison](../analysis/omp-pi-prompt-no-project-36v2/index.html). Its [machine-readable summary](../analysis/omp-pi-prompt-no-project-36v2/summary.json) contains the paired statistics, task-level results, tool counts, provider-payload audit, and solve flips.

The short version:

- OMP with a Pi-like prompt and its hidden project message removed solved 33 to 35 of 108 reps at low thinking. Clean Pi low solved 28.
- The OMP configs still used 1.47M to 1.57M median tokens per rep, compared with 599k for clean Pi low.
- Clean Pi medium solved 50 reps at 1.55M median tokens. At roughly the same token budget, raising Pi's thinking level beat every low-thinking OMP config by 15 to 17 solves.
- OMP's dedicated `grep`/`glob` and `ast_grep`/`ast_edit` tools did not produce a decisive winner. The cleaned grep/glob and AST configs each solved 35 reps; bash-only solved 33. Their paired solve differences were small and not statistically decisive.
- The AST config made 64 `ast_grep` calls and only 2 `ast_edit` calls across 108 reps. The model mostly used AST support as another search tool, not as a structural editing system.

This is a real but expensive tradeoff on this subset, not evidence that OMP broadly dominates Pi.

## Main results

| Config | Thinking | Solves | Mean partial | Median tokens | Median cost |
|---|---:|---:|---:|---:|---:|
| Clean Pi | low | 28/108 | 0.9574 | 599k | $0.83 |
| OMP Pi-like, bash-only, no project message | low | 33/108 | 0.9690 | 1.47M | $1.48 |
| OMP Pi-like, grep/glob, no project message | low | 35/108 | 0.9731 | 1.55M | $1.53 |
| OMP Pi-like, AST, no project message | low | 35/108 | 0.9728 | 1.57M | $1.46 |
| Clean Pi | medium | 50/108 | 0.9803 | 1.55M | $1.62 |

Source: [`analysis/omp-pi-prompt-no-project-36v2/summary.json`](../analysis/omp-pi-prompt-no-project-36v2/summary.json).

The provider audit matters. The final OMP configs remove an OMP-injected project developer message and an unintended `generate_image` tool from all 324 OMP reps. Use these `*-no-project` configs for future prompt and toolset claims.

## What the tool ablations found

Two rounds tested OMP's tool choices.

### Default OMP prompt on 36_v2

The [default-prompt toolset ablation](../analysis/omp-toolset-36v2/index.html) compared:

- `read,bash,edit,write,grep,glob`
- `read,bash,edit,write`
- `read,bash,edit,write,ast_grep,ast_edit`

Removing grep/glob recovered about 10% of median tokens, but solves fell from 36 to 32. Adding AST tools also produced 32 solves, increased median tokens to 2.25M, and increased median cost to $2.02. Across 108 reps, OMP made 386 `ast_grep` calls but only 7 `ast_edit` calls.

The [mechanism deep dive](../analysis/omp-toolset-36v2/deep_dive.html) found that changing the whitelist moved the exploration work rather than removing it. Bash-only OMP replaced dedicated search calls with more bash and read calls.

### Pi-like prompt with project-message cleanup on 36_v2

The [cleaned comparison](../analysis/omp-pi-prompt-no-project-36v2/index.html) narrowed the spread:

- grep/glob: 35 solves
- AST: 35 solves
- bash-only: 33 solves

Grep/glob and AST each gained 2 solves over bash-only, but the paired McNemar p-values were 0.84 and 0.86. Median token differences were only 71k to 79k. This does not support a strong claim that one OMP toolset is better.

Taken together, the ablations say that OMP's token cost is not mainly caused by choosing grep/glob instead of bash or AST. Tool selection changes the workflow, but the larger OMP prompt, more turns, and accumulated tool history dominate the cost.

## Why OMP used more tokens

The [12_v2 harness forensics](../analysis/omp-vs-pi-harness/DEEP_ANALYSIS.md) and [36_v2 mechanism report](../analysis/omp-toolset-36v2/deep_dive.html) point to the same causes:

1. OMP replayed a much larger non-message wrapper on every turn. The default OMP comparison measured 7,968 wrapper tokens per turn for most reps, versus about 1,891 tokens for Pi's first-turn prompt proxy.
2. OMP took more turns and made more tool calls. In the default 36_v2 comparison, it used about 1.4 times as many turns and 1.5 times as many tool calls as Pi.
3. OMP read more files and retained more tool output. Later turns replayed that larger history through the provider cache.
4. Edit confirmations were much larger under OMP's hashline editing mode. That content compounded across subsequent turns.

The 12_v2 decomposition attributed roughly one quarter to one third of the token gap to the direct wrapper, about one sixth to extra turns as a pure multiplier, and the remaining half or more to broader exploration and replayed history. Treat those percentages as a mechanism estimate from the 36-rep pilot, not universal constants.

The investigation ruled out broken prompt caching, hidden advisors, background subagents, and tool failures as primary causes.

## Repository map

Read these in order:

1. [Cleaned OMP prompt/toolset comparison on 36_v2](../analysis/omp-pi-prompt-no-project-36v2/index.html). This is the final result and the right source for current claims.
2. [Machine-readable final summary](../analysis/omp-pi-prompt-no-project-36v2/summary.json). Use this for new statistics or task-level analysis.
3. [Default OMP vs Pi on 36_v2](../analysis/omp-vs-pi-36v2/report.md). This established the stable token-efficiency gap before prompt cleanup.
4. [Default-prompt OMP toolset ablation](../analysis/omp-toolset-36v2/index.html), plus its [deep dive](../analysis/omp-toolset-36v2/deep_dive.html) and [evidence appendix](../analysis/omp-toolset-36v2/evidence_appendix.html).
5. [Pi-like prompt and toolset pilot on 12_v2](../analysis/omp-pi-prompt-toolsets-12v2/index.html). This motivated the larger cleaned comparison.
6. [Initial OMP vs Pi report on 12_v2](../analysis/omp-gpt55-low-12v2/report.md) and [root-cause forensics](../analysis/omp-vs-pi-harness/DEEP_ANALYSIS.md). These explain how the investigation started and why it expanded.

For reproduction or extension:

- [`docs/omp-gpt55-low-baseline.md`](omp-gpt55-low-baseline.md) documents OMP v16.3.5, the provider-qualified model path, credential isolation, RPC proof, and baseline smoke contract.
- [`docs/omp-toolset-variants.md`](omp-toolset-variants.md) documents the tool whitelist and overlays.
- [`harness/run_omp.py`](../harness/run_omp.py) is the OMP subject runner.
- [`configs/baseline-omp/`](../configs/baseline-omp/) is the default OMP config.
- [`configs/baseline-omp-pi-prompt-bash-only-no-project/`](../configs/baseline-omp-pi-prompt-bash-only-no-project/), [`configs/baseline-omp-pi-prompt-grepglob-no-project/`](../configs/baseline-omp-pi-prompt-grepglob-no-project/), and [`configs/baseline-omp-pi-prompt-ast-no-project/`](../configs/baseline-omp-pi-prompt-ast-no-project/) are the cleaned prompt/toolset configs.
- [`analysis/omp-pi-prompt-no-project-36v2/analyze.py`](../analysis/omp-pi-prompt-no-project-36v2/analyze.py) rebuilds the final comparison from result artifacts.
- [`analysis/omp-toolset-36v2/analyze.py`](../analysis/omp-toolset-36v2/analyze.py), [`compounding.py`](../analysis/omp-toolset-36v2/compounding.py), and [`tool_result_sizes.py`](../analysis/omp-toolset-36v2/tool_result_sizes.py) contain the tool and token analyses.

## A note on the two Pi baseline counts

The older [36_v2 report](../analysis/omp-vs-pi-36v2/report.md) records 33 Pi solves. The later cleaned comparison records 28, which matches the current result tree. The older report is a frozen analysis of an earlier baseline snapshot; the cleaned comparison used the later clean baseline corpus and added a fresh clean-medium reference.

Do not combine the older report's Pi count with the cleaned report's OMP rows. Each report is internally paired. Use the cleaned report for new comparisons and the older report for its OMP overhead and mechanism findings.

## Scope and limits

These results describe OMP v16.3.5 with GPT-5.5 at low thinking on DeepSWE `12_v2` and `36_v2`. They do not establish how current OMP versions, other models, other thinking levels, OMP subagents, browser tools, LSP support, or different task distributions behave. The binary solve differences among the low-thinking OMP toolsets are small relative to rep-level churn. The token and cost differences are much larger and reproduced across both subsets.

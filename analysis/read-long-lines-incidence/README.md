# Read long-line incidence in DeepSWE sessions

## Decision

The original clean-stock estimate covered 36 tasks, not the complete 113-task
DeepSWE corpus. The complete-corpus scan changes the target set, but not the
budget decision: do not fund a broad paired comparison when only two tasks
reliably exercise the behavior.

Use these two tasks for targeted behavioral validation:

1. `fd-deterministic-multi-key-sorting`
2. `abs-module-cache-flags`

Both activated in all three matched `deepseek-v4-flash/high` rep-0 configs that
cover every DeepSWE task: `baseline-preamble-orchestration`, `advisor`, and
`ponytail-extension`. The matched matrix is evidence of task-trigger reliability
across three agent configurations, not a clean-stock incidence estimate.

If high-magnitude or repository-source stress cases are useful, add
`pest-character-class-coalescing` and
`meriyah-explicit-resource-declarations`. Neither is a reliable natural
activator in the available trajectories.

## Complete-corpus result

The matched complete-corpus scope contains 339 reps: 113 tasks × three
`deepseek-v4-flash/high` configs at rep 0.

- 9,475 read results
- 11 read results with at least one line over 2,000 characters
- 10 activating reps across 6 tasks
- 11,241 source characters omitted by the cap
- 9,742 net characters removed after recovery notices

Two tasks activated in all three configs:

| Task | Activating reps | Affected reads | Long lines | Omitted characters | Long-line source |
| --- | ---: | ---: | ---: | ---: | --- |
| `abs-module-cache-flags` | 3/3 | 3 | 3 | 1,845 | `evaluator/stdlib.go:82`, generated gzip byte literal |
| `fd-deterministic-multi-key-sorting` | 3/3 | 3 | 6 | 5,316 | `src/main.rs:57-58`, dense color/config fixtures |

Four tasks activated in only one of the three configs:

- `goreleaser-retry-publish-auditing`
- `kgateway-consistent-hash-policy`
- `koota-deferred-mutation-buffer`
- `tengo-callable-instance-isolation`

The first three were read after an agent had created a malformed, serialized edit
payload inside a source line. `tengo-callable-instance-isolation` read a native
embedded source-module string, but only in the advisor trajectory.

## All-results discovery

The broad discovery scope scans every available result record, regardless of
config behavior. It covers 7,779 reps, 7,761 readable sessions, all 113 tasks,
78 observed config identities, and 127,599 read results.

- 14 tasks activate anywhere
- 85 reps activate (1.09%)
- 92 read results activate (0.0721%)
- 235,879 source characters would be omitted
- 218,714 net characters would be removed (0.0377% of read-result characters)

Only two tasks activate repeatedly:

- `fd-deterministic-multi-key-sorting`: 67/164 reps
- `abs-module-cache-flags`: 5/7 reps

The other twelve tasks activate in one or two reps. Their long lines divide into
native but rarely-read source (`pest`, `meriyah`, `obsidian`, `tengo`, and one
`node_modules` declaration) and workflow-created artifacts or malformed edits
(`dateutil`, `actionlint`, `boa`, `goreleaser`, `kgateway`, `koota`, and
`textual`). This scope is for discovery only; config and model heterogeneity make
its aggregate rate unsuitable as a clean-stock estimate.

## Why malformed long lines matter

In several saved trajectories, the agent accidentally wrote an edit payload or
part of its own transcript into a source file. A later `read` returned that
malformed line. For example, the `textual` trajectory returned one corrupted
27,549-character source line.

Stock Pi puts the complete returned line into that turn's tool result. The
extension would put the first 2,000 characters plus a recovery notice into the
tool result. It would not prevent or repair the bad edit. It would only keep the
remaining 25,549 characters out of that read result unless the agent explicitly
requested the full line with `limit=1`.

The corpus contains eight such artifact or corruption exposures:

- 12 affected read results
- 52,808 net characters removable after notices
- 180 subsequent assistant messages
- 18,910,581 recorded executor tokens after the first exposure

The last number is **not** an estimate of tokens the extension would save. It
only proves that the trajectories continued after reading the oversized payload,
so the payload had opportunities to remain in later context and prompt-cache
prefixes. A paired run is required to measure actual token savings.

Five corrupted-source reps were unsolved, but this does not show that the long
line caused failure or that truncation would fix it. The tasks, models, and
configs differ. Truncation could also hide the evidence an agent needs to notice
and repair corruption. The human-reviewed classification is in
`context-pollution-classifications.csv`; compact rep evidence is under
`data/context-pollution-opportunity/`.

## Recommended paired evaluation

Use `fd-deterministic-multi-key-sorting` and `abs-module-cache-flags` as the
core task set. Compare stock Pi with a versioned config containing only the
`read-long-lines` extension; add no config-authored prompt text.

Recommended three-rep pilot:

- `openai-codex/gpt-5.6-sol` at `low`
- `openai-codex/gpt-5.6-terra` at `low`
- `openai-codex/gpt-5.6-luna` at `low`
- `openrouter/deepseek/deepseek-v4-flash-0731` at `low`
- `zai/glm-5.2` at `max` through the direct Z.ai subscription route

This is 60 reps: 2 tasks × 2 configs × 5 model/thinking leaves × 3 reps. GLM's
`max` leaf is a deliberate subscription-model contrast, not part of a
reasoning-level sweep. Establish fresh stock-Pi baseline cells for all five
leaves under the same subject version and locks as the extension cells. Existing
results either lack modern provenance, use a different Pi version, omit the two
target tasks, or use Flash 0731 at `max` instead of `low`.

Do not run medium or high thinking yet. First inspect activation rates, token
deltas, recovery reads, and behavioral flips at the chosen levels. Add another
thinking level only if the low-thinking result leaves a specific question that
reasoning effort could answer. Keep intention-to-treat results primary and show
activation-conditioned results as a secondary view.

Separate deterministic payload reduction from realized trajectory efficiency:

- characters omitted and notice overhead
- exact executor input, cache-read, cache-write, output, and total tokens
- usage from the first activation onward
- turns, read calls, repeated reads, and `offset=N, limit=1` recoveries
- reward, partial reward, f2p, p2p, timeout, wall time, and tool errors
- paired trajectory packets for every solve flip, material grading change, or
  suspected missed-tail failure

For context-pollution resilience, use a separate noncanonical diagnostic rather
than hoping rare corruption recurs naturally. Pre-seed the exact observed
`goreleaser` serialized-edit line and `textual` transcript line into disposable
task workspaces, retain the original task prompts, and compare baseline against
the extension. Measure whether the model reads, propagates, diagnoses, or repairs
the corruption. Keep those results outside normal DeepSWE efficacy totals.

## Original clean-stock estimate

`data/primary/` contains config identities `baseline` and `baseline@1.0.0`:

- 648 reps with 648 readable newest-root sessions
- 36 tasks
- 10,325 read results
- 15 affected read results
- 12 activating reps across 3 tasks
- 42,553 source characters omitted by the cap
- 39,891 net characters removed, 0.0818% of all read-result characters

The original three activating tasks were `fd-deterministic-multi-key-sorting`,
`dateutil-rfc5545-timezone-interop`, and
`meriyah-explicit-resource-declarations`. The 36-task scope could not discover
`abs-module-cache-flags` because that task is outside the subset.

## Evidence scopes

- `data/primary/`: 36-task clean-stock incidence estimate.
- `data/model-adapter-sensitivity/`: 36-task baseline variants that preserve the
  stock read tool.
- `data/historical-control/`: prompt-bearing historical baseline across all 113
  tasks.
- `data/full-corpus-deepseek-triplet/`: matched rep-0 matrix across all 113 tasks
  and three `deepseek-v4-flash/high` configs.
- `data/all-results-discovery/`: every available result record; discovery only.
- `data/context-pollution-opportunity/`: compact post-exposure usage and outcome
  evidence for human-classified temporary/tool artifacts and corrupted source.

Each directory contains `summary.json`, `by-task.csv`,
`by-model-thinking-config.csv`, and `activations.csv`. Raw session text remains
in the canonical results tree.

## Method

`scan_read_long_lines.py` reads each rep's newest non-recursive root session,
matching the selection rule in `harness/parse_usage.py`. It pairs assistant
`read` tool calls with `toolResult` records by tool-call id.

For every returned text line, the scanner counts Unicode code points, matching
the extension's `Array.from(line)` implementation. An ordinary read line of
length `L > 2,000` contributes
`L - 2,000` omitted characters. A read with `limit=1` is exempt because the
active read implementation returns that line in full.

The active implementation keeps the first 2,000 characters and appends this
notice:

```text
[Line N shortened: showing 2,000 of L characters. Use offset=N, limit=1 to read the complete line.]
```

Net characters removed subtract the exact notice length, separators, and the two
newlines before the notice block from omitted source characters.

## Reproduce

Run from the repository root. Point `--results` at the primary checkout because
ignored benchmark results are not duplicated into this worktree.

```sh
# Every available result record.
python3 analysis/read-long-lines-incidence/scan_read_long_lines.py \
  --results /home/will/evals/deep-swe-bench/results \
  --all-configs \
  --out /tmp/read-long-lines-all-results

# Matched all-113 DeepSeek matrix.
python3 analysis/read-long-lines-incidence/scan_read_long_lines.py \
  --results /home/will/evals/deep-swe-bench/results \
  --configs baseline-preamble-orchestration advisor ponytail-extension \
  --model-leaves deepseek-v4-flash \
  --thinking-levels high \
  --rep-numbers 0 \
  --out /tmp/read-long-lines-full-corpus-triplet

# Human-classified context-pollution exposure.
python3 analysis/read-long-lines-incidence/analyze_context_pollution.py \
  --results /home/will/evals/deep-swe-bench/results \
  --activations analysis/read-long-lines-incidence/data/all-results-discovery/activations.csv \
  --classifications analysis/read-long-lines-incidence/context-pollution-classifications.csv \
  --out /tmp/read-long-lines-context-pollution
```

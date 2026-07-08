# OMP vs Pi Harness Deep Analysis

Comparison: same executor model (`openai-codex/gpt-5.5`), same thinking level (`low`), same 12-task `12_v2` DeepSWE subset, 3 reps per task, 36 cells per arm.

Arms:

- **Pi `baseline`**: plain pi agent.
- **OMP `baseline-omp`**: Oh My Pi v16.3.5 wrapping pi with its own system prompt and six tools (`read`, `bash`, `edit`, `write`, `grep`, `glob`).

Data sources used:

- `analysis/omp-vs-pi-harness/summaries/per_pair.json`
- `analysis/omp-vs-pi-harness/summaries/all_cells.json`
- Spot checks of representative `rep0/session/*.jsonl` traces for OMP custom events, tool-call shapes, repeated reads/tests, and tool-result sizes.

## Executive conclusion

OMP burns roughly **3x total model-accounted tokens** not because the model is different, caching is broken, tools fail more often, or hidden advisors run. Those are ruled out.

The token gap is caused by two interacting facts:

1. **OMP makes every turn much fatter.** Its non-message harness payload is constant at **7,968 tokens per turn** for 33/36 cells and **10,685 tokens per turn** for the 3 LangChain cells. Pi's entire turn-1 prompt is only about **1,891 tokens**. This OMP payload is cached, but it is still counted as `cacheRead` on every turn.
2. **OMP causes the same model to behave more serially and broadly.** It takes **510 more assistant turns** across 36 cells (+36.9%), uses **583 more tool calls** (+43.3%), does far more `read`/`grep`/`glob` mapping, edits in smaller patches, and reruns targeted/full verification more often. The extra tool outputs then stay in history and inflate later cached context.

The direct harness overhead is large, but it is not the whole story. A matched-cell decomposition of total tokens (`cacheRead + input + output + reasoningTokens`) gives:

| Component | Estimated gap share | Evidence |
|---|---:|---|
| Behavior-driven context bloat: broader exploration, larger tool results, redundant reads/tests, patch churn | **~52-59%** | Residual after turn-count and direct wrapper estimates; OMP raw tool-result bytes are 5.45M vs Pi 3.16M (+72.5%); OMP has 672 reads vs 355, 130 greps vs 0, 52 globs vs 0, 480 edits vs 324. |
| Bigger OMP per-turn harness wrapper | **~24-31%** | OMP non-message payload contributes 15.49M tokens gross across turns (~30.5% of the 50.73M token gap). Relative to Pi's ~1,891-token turn-1 prompt as a proxy, the incremental wrapper is ~11.91M tokens (~23.5%). |
| More turns as a pure multiplicative effect | **~17%** | Applying each Pi cell's average tokens/turn to OMP's extra turns explains ~8.66M of the 50.73M total gap. |
| Direct output/reasoning delta | **small** | OMP output + reasoning exceeds Pi by ~107.5k tokens, <1% of the total gap. |

These components are not perfectly independent: OMP's extra turns also replay the larger wrapper, and OMP's extra exploration both creates extra turns and fattens later turns. The safest high-level attribution is: **about one quarter to one third direct wrapper overhead, about one sixth pure extra-turn multiplication, and the remaining roughly half-plus from the OMP-induced exploratory/serial workflow and its larger replayed tool history.**

OMP also solves fewer cells on this 36-cell slice: **9/36 solved** (`reward_binary == 1`) vs Pi **11/36 solved**. One OMP Mobly cell has `reward_binary = -1` due to verifier timeout. The solve-rate gap is modest, but directionally consistent with the trace evidence: OMP's prompt/tooling makes the same model spend more context and steps on mapping, micro-edits, test-file work, and validation loops without reliably improving final correctness.

## Aggregate deterministic metrics across all 72 cells

| Metric | Pi baseline | OMP baseline-omp | OMP / Pi | Delta |
|---|---:|---:|---:|---:|
| Cells | 36 | 36 | 1.00x | 0 |
| Assistant turns / completions | 1,383 | 1,893 | 1.37x | +510 |
| Tool calls | 1,347 | 1,930 | 1.43x | +583 |
| Tool failures | 188 | 203 | 1.08x | +15 |
| Tool failure rate | 14.0% | 10.5% | lower in OMP | -3.5 pp |
| Raw tool-result bytes | 3,157,465 | 5,447,873 | 1.73x | +2,290,408 |
| `cacheRead` tokens | 22,138,880 | 70,906,368 | 3.20x | +48,767,488 |
| uncached `input` tokens | 2,787,054 | 4,646,328 | 1.67x | +1,859,274 |
| output tokens | 233,059 | 294,036 | 1.26x | +60,977 |
| session `reasoningTokens` | 0 | 46,571 | n/a | +46,571 |
| Total counted tokens above | 25,159,993 | 75,893,303 | 3.02x | +50,733,310 |
| Solves (`reward_binary == 1`) | 11/36 | 9/36 | worse | -2 solves |
| Mean partial reward | 0.9739 | 0.9537 | worse | -0.0202 |

Tool mix:

| Tool | Pi calls | OMP calls | Delta | Interpretation |
|---|---:|---:|---:|---|
| `bash` | 613 | 545 | -68 | OMP does not simply run more shell commands. |
| `read` | 355 | 672 | +317 | OMP reads many more files/slices. |
| `grep` | 0 | 130 | +130 | OMP-specific repo mapping/search pass. |
| `glob` | 0 | 52 | +52 | OMP-specific repo mapping/search pass. |
| `edit` | 324 | 480 | +156 | OMP patches in smaller/more iterative steps. |
| `write` | 55 | 51 | -4 | Similar. |

## Required root-cause questions

### 1. Are tool-call failures a cause?

**No.** Tool failures are not a meaningful differentiator.

- Across all cells: OMP has **203** tool failures vs Pi **188**, only **+15** failures.
- Because OMP makes many more calls, its failure rate is actually lower: **10.5%** vs Pi **14.0%**.
- Many task pairs have identical or near-identical failure counts.
- OMP has some retry-ish churn (given deterministic fact: OMP 13 vs Pi 0 approximate retries), but that is minor against **+583 tool calls**, **+510 turns**, and **+50.7M tokens**.

Conclusion: tool failures may explain local edit retries in a few traces, but they do **not** explain the overall token gap or solve-rate gap.

### 2. Is prompt caching broken?

**No. Caching is working; OMP just has a much larger prompt to cache-read every turn.**

Evidence:

- OMP's largest token delta is `cacheRead`, not uncached `input`.
- `cacheRead`: OMP **70.91M** vs Pi **22.14M** = **3.20x**, delta **48.77M**.
- Uncached `input`: OMP **4.65M** vs Pi **2.79M** = **1.67x**, delta **1.86M**.
- OMP's `nonMessageTokens` are constant inside cells: **7,968** for 33 cells, **10,685** for the 3 LangChain cells.
- Constant repeated non-message tokens landing in `cacheRead` is the signature of a stable cached prefix, not a broken cache.

Conclusion: the cache is doing what it should, but OMP sends a much bigger harness prefix, and token accounting still reports those tokens as cache reads.

### 3. Are background advisors/subagents present?

**No.** There are no hidden model workers in either arm.

Evidence:

- `models_seen` is only `gpt-5.5` in both arms.
- `background_or_extra_calls` is **0** in all extracted cells.
- `advisor_calls` in `result.json` is **0** in both arms.
- OMP custom events are exactly **1,930 `tool_execution_start`** events plus **36 `session_exit`** events, matching its 1,930 tool calls and 36 cells.
- These custom events are not assistant completions or extra model calls.

Conclusion: the comparison is single-session/single-model in both arms. The token gap is not caused by advisors, subagents, background agents, or secondary LLM roles.

### 4. What are the extra harness-related tokens, and how much do they explain?

OMP's direct non-message harness payload is the most concrete harness tax:

- **7,968 tokens per OMP turn** in 33/36 cells.
- **10,685 tokens per OMP turn** in the 3 LangChain cells.
- Across 1,893 OMP turns, this is **15,493,691 gross non-message tokens**.
- The total token gap is **50,733,310**, so gross OMP non-message overhead is **~30.5%** of the gap.
- If Pi's entire turn-1 prompt (~1,891 tokens) is used as a conservative baseline proxy, OMP's incremental wrapper is **~11,914,028 tokens**, **~23.5%** of the gap.

The wrapper is multiplied by OMP's extra turns:

- If OMP had taken Pi's number of turns, its OMP non-message payload would have been **11,329,482** tokens.
- OMP's extra 510 turns add another **4,164,209** OMP non-message tokens.
- So extra turns alone account for **~8.2%** of the total gap just by replaying the OMP wrapper.

The rest comes from behavior and replayed history: more reads/searches/edits/tests and larger tool outputs, which become part of future cached context.

## Additive token-gap estimate

Total gap basis: `cacheRead + input + output + reasoningTokens` across all 72 cells.

- Pi: **25,159,993**
- OMP: **75,893,303**
- Gap: **50,733,310**
- Ratio: **3.02x**

Matched-cell decomposition:

| Estimate | Tokens | Share of gap | Meaning |
|---|---:|---:|---|
| More turns at Pi-sized average context | 8,664,487 | 17.1% | What OMP would add if its extra turns looked like Pi turns. |
| Fatter OMP turns beyond Pi-sized average context | 42,069,823 | 82.9% | Bigger wrapper + larger replayed tool/message history. |
| Gross OMP non-message wrapper inside fatter-turn effect | 15,493,691 | 30.5% | Direct OMP harness payload. |
| Incremental wrapper vs Pi turn-1 prompt proxy | 11,914,028 | 23.5% | More conservative direct harness-tax estimate. |
| Residual behavioral/history bloat after gross wrapper | ~26.6M | ~52.4% | Broad exploration, tool-result bloat, repeated reads/tests/edits, context history. |
| Residual behavioral/history bloat after incremental wrapper | ~30.2M | ~59.4% | Same, using conservative incremental wrapper estimate. |

Recommended causal ranking by token impact:

1. **OMP-induced behavior and replayed context bloat** (~52-59%). The harness changes how the model works: more repo mapping, more reads, more micro-edits, more verification loops, larger tool results, and more accumulated history.
2. **Direct larger OMP harness prefix** (~24-31%). Constant 7,968/10,685 non-message tokens per turn; cached but counted.
3. **More turns as a pure multiplier** (~17%). OMP takes +510 turns (+36.9%); this replays both ordinary history and the large wrapper.
4. **Tool failures/retries and direct output deltas** (minor). Failures are nearly identical; output/reasoning deltas are <1% of the token gap.

## Qualitative per-task characterization

| Task | Aggregate turn ratio | Aggregate token ratio | Primary OMP turn/token driver |
|---|---:|---:|---|
| `adaptix-name-mapping-aliases` | 1.27x | 2.51x | OMP shards the fix into more micro-steps: many more reads/edits plus OMP-only `grep`/`glob` across tests and internals. It repeatedly edits the new test file and expands verification. |
| `tengo-callable-instance-isolation` | 1.66x | 5.42x | OMP broadens into compiler/test internals, repeatedly edits `script_test.go`, and reruns `go test ./...` many times. Large test outputs and reads make later turns much fatter. |
| `mobly-grouped-test-barriers` | 1.66x | 3.84x | OMP performs many small map/read/edit/test loops around `mobly/base_test.py` and `tests/mobly/base_test_test.py`, reopening nearby slices and rerunning targeted pytest several times plus full tests. One OMP cell times out in verification. |
| `sql-formatter-bigquery-pipe-formatting` | 1.39x | 2.69x | OMP front-loads parser/lexer/formatter/test discovery, then runs repeated grammar/test/format/lint/generated-grammar validation passes after the core patch is in place. |
| `langchain-request-coalescing` | 1.32x | 3.07x | OMP does broader code archaeology (`base.py`, `__init__.py`, `coalesce.py`, tests) and more edit-pytest-fix loops; it also has the larger 10,685-token OMP overhead variant. |
| `goreleaser-retry-publish-auditing` | 1.21x | 3.04x | OMP widens repo scan around `http`/`blob` paths and test files, then reruns go test/gofmt loops. Token gap is more fatter-turn/tool-output driven than turn-count driven. |
| `go-critic-doc-link-checker` | 1.29x | 3.04x | OMP glob/grep reconnaissance (`**/*.go`, type/package/import patterns), more reads of checker/linter internals, and repeated narrow brokenDocLink tests. |
| `obsidian-linter-link-format-conversion` | 1.06x | 2.10x | Turn count is nearly flat; token gap is mostly fatter turns from broad `glob`/`grep`/read dumps and larger test/lint output. This is the clearest case where wrapper + tool-result bloat dominate without many extra turns. |
| `participle-grammar-conflict-analysis` | 1.40x | 2.96x | OMP is more serialized: map/search first, then parser/options/nodes/ebnf reads in separate turns, followed by repeated `go test -tags analyze ./...`. |
| `superjson-error-stack-serialization` | 1.35x | 3.25x | OMP loops around `src/transformer.ts`, patching tiny slices and rerunning `npm test`/build. It also hits edit-anchor retries and missing test path probes. |
| `dateutil-rfc5545-timezone-interop` | 1.27x | 2.85x | OMP spends extra turns on discovery and split reads over `rrule.py`; Pi actually does more bash validation, but OMP's larger prompt and read/search workflow make its turns much fatter. |
| `claude-code-by-agents-recursive-delegation` | 1.84x | 3.21x | OMP performs a wider repo-map pass, reads more files, applies a larger delegation/test patch, then runs format/typecheck/retests. |

## Harness-specific waste observed in traces

OMP-specific trace artifacts:

- Every OMP tool call is preceded by a `customType: tool_execution_start` event with a short `intent` string.
- The assistant tool-call arguments also include that intent (`i: "..."`) in the sampled logs.
- OMP has one `session_exit` custom event per cell.
- OMP often starts with explicit branch/status mapping, e.g. `git status --short --branch`, `git checkout -b ...`, `glob`, and `grep` mapping.

Impact assessment:

- The custom event stream itself is not an extra model call.
- Intent strings and branch/status scaffolding are real harness-specific tokens, but they are small compared with the 7,968/10,685-token repeated wrapper and the large replayed tool outputs.
- The important harness effect is behavioral: OMP's prompt/tool API induces a more cautious, serialized, repo-mapping workflow.

## Why solve rate is worse despite more work

OMP does more work, but much of it is not productive work.

Observed failure modes:

1. **More context, lower signal density.** The model sees a much larger wrapper plus more search/test output every turn. Even with caching, the model attends over a noisier history.
2. **More micro-edits and patch churn.** OMP often edits in narrower slices and iterates on tests or scaffolding. This increases opportunities to drift from the minimal fix.
3. **Broader exploration can become dead-end exploration.** OMP frequently reads support/test/compiler/framework internals that Pi does not need for the final patch.
4. **Verification does not equal correctness.** OMP often runs more checks, but traces show repeated targeted tests, formatting, linting, and generated-file checks after the solution approach is already chosen. These consume context and time without reliably improving hidden-test behavior.
5. **Timeout/overrun risk rises.** The Mobly OMP verifier timeout is one concrete example. Even when the agent itself does not time out, larger patches and longer loops increase the chance of hidden-test or verifier failure.

The solve-rate delta is not huge on 36 cells (Pi 11 solves, OMP 9), so it should not be overclaimed statistically. But the direction is explainable: OMP's harness causes the same model to spend more of its budget on broad, serial, noisy process instead of compact problem-solving.

## Bottom line

The OMP vs Pi gap is a **harness-behavior and prompt-size effect**, not a model, cache, tool-failure, or hidden-agent effect.

- Same model: yes.
- Same thinking level: yes.
- No advisors/subagents/background calls: yes.
- Tool failures: not causal.
- Cache: not broken.
- Direct OMP wrapper: large, roughly one quarter to one third of the token gap.
- OMP-induced extra exploration/verification/history bloat: largest cause, roughly half or more of the token gap.
- Extra turns: important multiplier, roughly one sixth as a pure effect and also the mechanism that replays the large wrapper and bloated history.

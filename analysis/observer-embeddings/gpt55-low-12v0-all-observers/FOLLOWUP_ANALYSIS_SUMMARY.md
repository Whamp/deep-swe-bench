# Observer embedding follow-up analysis summary

Source artifact: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/`.

The embedding store was refreshed after the remaining GPT-5.5 observer cells finished. The current zvec/manifest set contains **7,112 observations** across 12 observer configs and 12 `12_v0` tasks. The follow-up suite clusters these into **1,514 task-local semantic topics** using greedy centroid clustering at cosine threshold `0.84`.

Main generated index: `followup-analysis/FOLLOWUP_ANALYSIS_INDEX.md`.

## Key findings

### 1. GLM-5.2 off and GPT-5.4-mini low really are complementary

Unique-observation mining between the two best configs shows large asymmetric novelty:

| direction | observations | unique <0.80 | unique rate | substantive unique rate |
|---|---:|---:|---:|---:|
| GLM-5.2 off -> GPT-5.4-mini low | 738 | 298 | 0.404 | 0.396 |
| GPT-5.4-mini low -> GLM-5.2 off | 462 | 129 | 0.279 | 0.280 |

GLM-off writes more observations and covers more of the combined gold topic set, but GPT-5.4-mini low still has the better solve/partial outcome. More coverage is not automatically better.

Artifact: `followup-analysis/unique-observations-glm52-off-vs-gpt54mini-low/examples.md`.

### 2. Topic coverage confirms GLM-off covers more, GPT-mini-low wins quality

Deduplicated topic coverage avoids rewarding repeated near-duplicate observations.

| config | topic recall | gold topic recall | solve | robust partial |
|---|---:|---:|---:|---:|
| GLM-5.2 off | 0.256 | 0.717 | 0.417 | 0.993 |
| GPT-5.4-mini low | 0.194 | 0.542 | 0.444 | 0.996 |
| GLM-5.2 max | 0.354 | 0.495 | 0.306 | 0.984 |

GLM max has the highest raw topic recall but worse quality, which reinforces that topic coverage needs helpfulness/style/timeliness context.

Artifact: `followup-analysis/topic-clusters/summary.md`.

### 3. The GLM-off + GPT-mini-low pair has low overlap and useful oracle headroom

Pairwise complementarity for GLM-off + GPT-5.4-mini low:

| pair | union topic recall | Jaccard overlap | unique topics A | unique topics B | oracle solve | oracle robust partial |
|---|---:|---:|---:|---:|---:|---:|
| GLM-off + GPT-mini-low | 0.357 | 0.259 | 248 | 153 | 0.500 | 0.997 |

This supports the hypothesis that they are not just stylistically different; they cover different semantic topics. The pair is also among the strongest low-overlap/high-quality combinations.

Artifact: `followup-analysis/pairwise-complementarity/summary.md`.

### 4. Unique examples suggest a content-style difference

Substantive GLM-off-unique examples skew toward repository/codebase survey details, tool/environment notes, and implementation structure. GPT-5.4-mini-low-unique examples skew toward targeted validation/test outcomes and concrete run results.

Examples from the mined output:

- GLM-off unique: actionlint pass/visitor structure, kgateway duration handling pattern, cattrs Python compatibility/import details.
- GPT-mini-low unique: FastAPI/httpx test collection failures, TypeScript build failure details, successful/failed test-run observations.

This points to a plausible difference: GLM-off may broaden context, while GPT-5.4-mini low records more live verification state.

### 5. Observation type split supports the “xhigh gets abstract” hypothesis

The heuristic type classifier is not a substitute for human review, but the aggregate pattern is informative:

| thinking level | requirement share | implementation share | test/failure share | self-report share |
|---|---:|---:|---:|---:|
| off | 0.078 | 0.299 | 0.256 | 0.228 |
| low | 0.090 | 0.295 | 0.255 | 0.227 |
| xhigh | 0.233 | 0.347 | 0.159 | 0.083 |

xhigh records many more requirement-like observations and fewer test/failure observations. That supports the earlier hypothesis that high thinking can over-focus on abstract requirements and under-record live verification state.

Artifact: `followup-analysis/observation-type-classification/summary.md`.

### 6. Timeliness shows xhigh often records early but covers few topics overall

Some xhigh configs have high early observation share but low final topic recall:

| config | early+mid topic recall | final topic recall | early obs share | solve |
|---|---:|---:|---:|---:|
| GPT-5.4-mini xhigh | 0.102 | 0.102 | 0.956 | 0.278 |
| GPT-5.4 xhigh | 0.104 | 0.114 | 0.737 | 0.222 |
| GPT-5.5 xhigh | 0.205 | 0.213 | 0.833 | 0.306 |

This is a sharper version of the catch-up hypothesis: the failure mode is not merely “late memories”; for some xhigh configs the observer records mostly early snapshots and then does not keep enough topic coverage through later implementation/verification phases.

Artifact: `followup-analysis/timeliness-adjusted-coverage/summary.md`.

### 7. Helpful/harmful topic correlation is dominated by Boa and should be treated as exploratory

Topic-presence correlations surface useful examples but are noisy on 12_v0. Many strongest positive and negative topics come from `boa-hierarchical-evaluation-cancellation`, which has high variance and many observations.

The analysis still surfaces plausible poison-memory patterns, especially self-reported completion or premature implementation-state topics with negative partial deltas. This needs human review before strong claims.

Artifact: `followup-analysis/topic-correlation/summary.md`.

### 8. Self-consistency is not the same as quality

Refreshed rep-to-rep self-consistency still shows worse configs can be more self-consistent:

| config | rep-pair semantic F1 | solve | robust partial |
|---|---:|---:|---:|
| GPT-5.4 xhigh | 0.840 | 0.222 | 0.934 |
| GLM-5.2 off | 0.832 | 0.417 | 0.993 |
| GPT-5.4-mini low | 0.800 | 0.444 | 0.996 |

Best quality may require trajectory-sensitive observations, not repeated stable summaries.

Artifact: `followup-analysis/rep-self-consistency/summary.md`.

## Caveats

- Topic clustering is deterministic greedy clustering. Threshold `0.84` is a pragmatic default, not a validated universal cutoff.
- Correlations are descriptive, not causal.
- Type classification is heuristic; use it for pattern finding, not final labels.
- Timeliness uses OM `coversUpToId` source-entry watermarks, not direct wall-clock latency.
- `12_v0` is a screening subset; conclusions should guide the next experiment, not settle final model choice.

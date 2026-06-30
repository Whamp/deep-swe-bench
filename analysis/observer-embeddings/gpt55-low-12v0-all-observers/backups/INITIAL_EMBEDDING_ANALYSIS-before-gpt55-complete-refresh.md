# Observer embedding analysis pause notes

Date: 2026-06-28

## Scope

This snapshot analyzes observational-memory observer outputs for the GPT-5.5 low executor on `12_v0`, combining GLM-5.2 and Codex observer configs in one comparison.

Important user preference: analyze GLM-5.2 and GPT observer models together; the point is cross-observer comparison, not separate GLM vs GPT sections.

## Main artifacts

- Script: `scripts/observer_embedding_distance.py`
- Embedding store: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/observer-observations.zvec/`
- Observation manifest: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/observer-observations.jsonl`
- Single-reference summary: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/semantic-distance-summary.md`
- Per-task single-reference distances: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/semantic-distance-per-task.csv`
- Dual-gold summary: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/dual-gold-gpt54mini-low-glm52-off/summary.md`
- Rep self-consistency summary: `analysis/observer-embeddings/gpt55-low-12v0-all-observers/rep-self-consistency/summary.md`

## Method

- Extracted final recorded observer memories from `session/*.jsonl` entries with `customType == "om.observations.recorded"`.
- Embedded each individual observation with the endurance Octen embedding endpoint:
  - URL: `http://100.77.237.75:8090/v1/embeddings`
  - model: `octen-embed`
  - dimension: `2560`
- Stored embeddings and metadata in zvec.
- Verified zvec API docs: `Collection.destroy()` permanently deletes the collection; use `flush()` for durability. The script was corrected accordingly.
- Verified the rebuilt zvec store reopens successfully with `doc_count = 6896`.

## Completeness snapshot

Completed configs in this artifact set:

- `observational-memory-glm52-off`: 36 cells / 12 tasks
- `observational-memory-glm52-high`: 36 cells / 12 tasks
- `observational-memory-glm52-max`: 82 consolidated cells / 12 tasks
- `observational-memory-gpt54-off`: 36 cells / 12 tasks
- `observational-memory-gpt54-low`: 36 cells / 12 tasks
- `observational-memory-gpt54-xhigh`: 36 cells / 12 tasks
- `observational-memory-gpt54mini-off`: 36 cells / 12 tasks
- `observational-memory-gpt54mini-low`: 36 cells / 12 tasks
- `observational-memory-gpt54mini-xhigh`: 36 cells / 12 tasks
- `observational-memory-gpt55-off`: 36 cells / 12 tasks
- `observational-memory-gpt55-low`: 36 cells / 12 tasks
- `observational-memory-gpt55-xhigh`: 30 cells / 12 tasks at the time of this snapshot; interpret with caveat.

## Single-reference semantic distance

Reference config: `observational-memory-gpt54mini-low`, because it was the best completed observer config by quality so far.

Top of `semantic-distance-summary.md`:

| rank | config | semantic F1 vs gpt54mini-low | quality solve | robust partial | no-obs tasks |
|---:|---|---:|---:|---:|---:|
| 1 | `observational-memory-gpt54mini-low` | 1.000 | 0.444 | 0.996 | 0 |
| 2 | `observational-memory-gpt54mini-off` | 0.849 | 0.389 | 0.992 | 0 |
| 3 | `observational-memory-gpt54-xhigh` | 0.844 | 0.222 | 0.934 | 1 |
| 4 | `observational-memory-gpt54-low` | 0.836 | 0.333 | 0.983 | 0 |
| 5 | `observational-memory-gpt55-off` | 0.835 | 0.389 | 0.986 | 0 |
| 10 | `observational-memory-glm52-off` | 0.823 | 0.417 | 0.993 | 0 |

Important interpretation: GLM-5.2 off and GPT-5.4-mini low are both high-quality configs, but GLM-off is fairly distant from GPT-mini-low. This likely means they observe different things, not that one is simply worse.

## Dual-gold analysis

Gold/reference set = per-task union of:

- `observational-memory-gpt54mini-low`
- `observational-memory-glm52-off`

Artifact: `dual-gold-gpt54mini-low-glm52-off/summary.md`

Key table:

| rank | config | F1 vs dual gold | recall | precision | obs ratio | solve | robust partial | no-obs tasks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | `observational-memory-glm52-off` | 0.965 | 0.932 | 1.000 | 0.594 | 0.417 | 0.993 | 0 |
| 2 | `observational-memory-gpt54mini-low` | 0.940 | 0.887 | 1.000 | 0.406 | 0.444 | 0.996 | 0 |
| 3 | `observational-memory-glm52-max` | 0.885 | 0.882 | 0.890 | 1.355 | 0.306 | 0.984 | 0 |
| 4 | `observational-memory-glm52-high` | 0.870 | 0.855 | 0.886 | 0.546 | 0.333 | 0.991 | 0 |

Interpretation:

- GLM-off covers more of the dual-gold set than GPT-5.4-mini-low, partly because it records more observations.
- GPT-5.4-mini-low still has the best quality result.
- More semantic coverage is not automatically better. We need topic/cluster-level analysis to distinguish useful extra coverage from redundant/noisy coverage.

## Rep-to-rep self-consistency

Artifact: `rep-self-consistency/summary.md`

Metric: for each config/task, compare every pair of reps by nearest-neighbor semantic overlap between their recorded observations.

Key table:

| rank | config | rep-pair semantic F1 | close F1 @ .85 | solve | robust partial |
|---:|---|---:|---:|---:|---:|
| 1 | `observational-memory-gpt54-xhigh` | 0.840 | 0.603 | 0.222 | 0.934 |
| 2 | `observational-memory-glm52-max` | 0.832 | 0.507 | 0.306 | 0.984 |
| 3 | `observational-memory-glm52-off` | 0.832 | 0.494 | 0.417 | 0.993 |
| 11 | `observational-memory-gpt54mini-low` | 0.800 | 0.384 | 0.444 | 0.996 |
| 12 | `observational-memory-gpt54mini-off` | 0.794 | 0.370 | 0.389 | 0.992 |

Interpretation:

- Self-consistency is informative but not itself a target.
- The best config, GPT-5.4-mini low, is less self-consistent than several worse configs.
- Hypothesis: GPT-5.4-mini low is more trajectory-sensitive and records live implementation/test state, while some worse configs may repeat stable task requirements more consistently.

## Existing observer-health context to keep in mind

Previously computed health table: `results/gpt-5.5/low/observer-health-complete-so-far.md`

High-signal metrics:

- append success rate
- no-observation cells
- coverage of session source entries
- uncovered source entries
- observer duration mean/p95
- observation yield: observation tokens appended per worker token spent

Earlier interpretation:

- Codex xhigh configs often fail mechanically: slower calls, more stale-context errors, fewer observations, worse coverage.
- GLM-5.2 high vs off is less mechanically explained; high has decent coverage, so quality loss may come from content/style rather than failure to append.

## Next analyses to pursue

1. **Unique-observation mining between GLM-5.2 off and GPT-5.4-mini low**
   - For each observation in one config, find nearest observation in the other.
   - Surface observations below a cosine threshold, e.g. `< 0.80` or bottom quantile.
   - Answer: what does GLM-off catch that GPT-mini-low misses, and vice versa?

2. **Topic clustering across all observer outputs**
   - Cluster observations per task or globally using embeddings.
   - Measure topic coverage per config.
   - This avoids rewarding verbose configs for near-duplicate observations.

3. **Dual-gold cluster coverage**
   - Use clusters from the union of GLM-off + GPT-mini-low as the reference topic set.
   - Score each config by topic recall, not raw observation recall.
   - This should be more robust than raw nearest-neighbor F1.

4. **Helpful vs harmful topic correlation**
   - For each topic/cluster, correlate presence with partial/solve improvements.
   - Look for poison topics, especially premature self-reported completion or unverified implementation claims.

5. **Observation type classifier**
   - Classify observations into requirement, code structure, implementation state, test/failure, self-report, constraint, etc.
   - Test hypothesis: best observers record more live implementation/test state; weaker or high-thinking observers over-record abstract requirements.

6. **Timeliness-adjusted semantic coverage**
   - Use session/source coverage and observer timestamps/coverage watermarks.
   - Score whether important observations land early enough to help the main executor.

7. **Pairwise complementarity matrix**
   - For each pair of configs, compute overlap, unique coverage, union topic coverage, and quality.
   - Identify whether GLM-off + GPT-mini-low are genuinely complementary.

8. **Rep trajectory sensitivity**
   - Compare self-consistency against quality variance by task.
   - Distinguish good adaptive variation from bad randomness.

## Pause state

Work is paused here. The data, script, zvec store, and summary artifacts above are saved and can be resumed without recomputing embeddings unless new observer cells finish or configs are added.

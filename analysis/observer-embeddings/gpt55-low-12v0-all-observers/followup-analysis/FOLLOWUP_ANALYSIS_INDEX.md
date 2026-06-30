# Observer embedding follow-up analysis index

Source embedding directory: `analysis/observer-embeddings/gpt55-low-12v0-all-observers`

Observations loaded: 7112. Topics clustered: 1514. Cluster threshold: `0.84`. Unique threshold: `0.8`.

## Generated analyses

1. `unique-observations-glm52-off-vs-gpt54mini-low/` — task-local nearest-neighbor uniqueness between the two best configs.
2. `topic-clusters/` — per-task semantic topic clusters plus deduplicated config coverage.
3. `topic-correlation/` — correlational topic presence vs solve/partial outcomes.
4. `observation-type-classification/` — deterministic heuristic requirement/code/implementation/test/self-report split.
5. `timeliness-adjusted-coverage/` — source-watermark phase and early/mid/final topic coverage.
6. `pairwise-complementarity/` — pairwise topic union, overlap, unique additions, and quality oracle.
7. `rep-self-consistency/` — refreshed rep-to-rep semantic consistency with all completed cells.

## Caveats

- Topic clustering is deterministic greedy centroid clustering; thresholds affect topic granularity.
- Topic-quality correlations are descriptive, not causal, and are noisy on 12_v0.
- Observation type labels are heuristic and should be spot-checked before strong claims.
- Timeliness uses OM coverage watermarks over source entries, not raw wall-clock observer latency.

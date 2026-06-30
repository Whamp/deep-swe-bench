# Observer semantic distance to best config

Best/reference config: `observational-memory-gpt54mini-low`. Distances use Octen embeddings stored in zvec.

Nearest-neighbor metrics treat the best config's observation set for each task as the semantic reference. `recall` asks whether the candidate covers best observations; `precision` asks whether candidate observations are close to best observations.

| rank | config | semantic F1 | recall vs best | precision vs best | centroid distance | obs ratio | quality solve | robust partial | no-obs tasks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | observational-memory-gpt54mini-low | 1.000 | 1.000 | 1.000 | 0.000 | 1.000 | 0.500 | 0.995 | 0 |
| 2 | observational-memory-glm52-off | 0.823 | 0.864 | 0.785 | 0.032 | 1.856 | 0.500 | 0.995 | 0 |

Outputs:
- `observer-observations.zvec/` zvec collection with every observation embedding.
- `observer-observations.jsonl` metadata for each embedded observation.
- `semantic-distance-per-task.csv/jsonl` per-task distances.
- `semantic-distance-summary.csv` aggregate ranking.

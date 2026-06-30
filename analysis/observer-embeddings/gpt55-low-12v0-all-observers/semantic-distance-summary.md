# Observer semantic distance to best config

Best/reference config: `observational-memory-gpt54mini-low`. Distances use Octen embeddings stored in zvec.

Nearest-neighbor metrics treat the best config's observation set for each task as the semantic reference. `recall` asks whether the candidate covers best observations; `precision` asks whether candidate observations are close to best observations.

| rank | config | semantic F1 | recall vs best | precision vs best | centroid distance | obs ratio | quality solve | robust partial | no-obs tasks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | observational-memory-gpt54mini-low | 1.000 | 1.000 | 1.000 | -0.000 | 1.000 | 0.444 | 0.996 | 0 |
| 2 | observational-memory-gpt54mini-off | 0.849 | 0.861 | 0.838 | 0.019 | 1.323 | 0.389 | 0.992 | 0 |
| 3 | observational-memory-gpt54-xhigh | 0.844 | 0.828 | 0.861 | 0.032 | 0.768 | 0.222 | 0.934 | 1 |
| 4 | observational-memory-gpt54-low | 0.836 | 0.842 | 0.831 | 0.026 | 0.993 | 0.333 | 0.983 | 0 |
| 5 | observational-memory-gpt55-off | 0.835 | 0.841 | 0.831 | 0.026 | 1.145 | 0.389 | 0.986 | 0 |
| 6 | observational-memory-gpt54-off | 0.835 | 0.841 | 0.829 | 0.028 | 1.112 | 0.306 | 0.936 | 0 |
| 7 | observational-memory-glm52-max | 0.833 | 0.853 | 0.815 | 0.030 | 3.423 | 0.306 | 0.984 | 0 |
| 8 | observational-memory-gpt55-low | 0.829 | 0.839 | 0.819 | 0.029 | 1.184 | 0.333 | 0.992 | 0 |
| 9 | observational-memory-glm52-high | 0.824 | 0.833 | 0.815 | 0.033 | 1.419 | 0.333 | 0.991 | 0 |
| 10 | observational-memory-glm52-off | 0.823 | 0.835 | 0.812 | 0.035 | 1.575 | 0.417 | 0.993 | 0 |
| 11 | observational-memory-gpt54mini-xhigh | 0.816 | 0.786 | 0.851 | 0.038 | 0.441 | 0.278 | 0.934 | 2 |
| 12 | observational-memory-gpt55-xhigh | 0.809 | 0.815 | 0.805 | 0.034 | 1.235 | 0.306 | 0.931 | 2 |

Outputs:
- `observer-observations.zvec/` zvec collection with every observation embedding.
- `observer-observations.jsonl` metadata for each embedded observation.
- `semantic-distance-per-task.csv/jsonl` per-task distances.
- `semantic-distance-summary.csv` aggregate ranking.

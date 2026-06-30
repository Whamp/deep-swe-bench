# Dual-gold observer semantic coverage

Gold/reference observation set is the per-task union of `observational-memory-gpt54mini-low` and `observational-memory-glm52-off`.

| rank | config | F1 vs dual gold | recall | precision | obs ratio | solve | robust partial | no-obs tasks |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | observational-memory-glm52-off | 0.965 | 0.932 | 1.000 | 0.594 | 0.417 | 0.993 | 0 |
| 2 | observational-memory-gpt54mini-low | 0.940 | 0.887 | 1.000 | 0.406 | 0.444 | 0.996 | 0 |
| 3 | observational-memory-glm52-max | 0.885 | 0.882 | 0.890 | 1.355 | 0.306 | 0.984 | 0 |
| 4 | observational-memory-glm52-high | 0.870 | 0.855 | 0.886 | 0.546 | 0.333 | 0.991 | 0 |
| 5 | observational-memory-gpt54-xhigh | 0.856 | 0.818 | 0.897 | 0.293 | 0.222 | 0.934 | 1 |
| 6 | observational-memory-gpt55-off | 0.855 | 0.838 | 0.873 | 0.454 | 0.389 | 0.986 | 0 |
| 7 | observational-memory-gpt55-low | 0.851 | 0.837 | 0.866 | 0.467 | 0.333 | 0.992 | 0 |
| 8 | observational-memory-gpt54mini-off | 0.849 | 0.834 | 0.864 | 0.518 | 0.389 | 0.992 | 0 |
| 9 | observational-memory-gpt54-low | 0.848 | 0.828 | 0.869 | 0.392 | 0.333 | 0.983 | 0 |
| 10 | observational-memory-gpt54-off | 0.846 | 0.828 | 0.866 | 0.431 | 0.306 | 0.936 | 0 |
| 11 | observational-memory-gpt55-xhigh | 0.834 | 0.821 | 0.850 | 0.333 | 0.361 | 0.990 | 5 |
| 12 | observational-memory-gpt54mini-xhigh | 0.826 | 0.776 | 0.885 | 0.162 | 0.278 | 0.934 | 2 |

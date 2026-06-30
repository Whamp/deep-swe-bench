# Observer rep-to-rep self-consistency

For each config/task, this compares every pair of reps by nearest-neighbor semantic overlap between recorded observations. Higher F1 means more similar memory content across independent reps of the same task; it is not necessarily better.

| rank | config | rep pairs | semantic F1 | close F1 @ .85 | centroid distance | mean obs/side | solve | robust partial |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | observational-memory-gpt54-xhigh | 29 | 0.840 | 0.603 | 0.042 | 10.879 | 0.222 | 0.934 |
| 2 | observational-memory-glm52-max | 235 | 0.832 | 0.507 | 0.029 | 19.251 | 0.306 | 0.984 |
| 3 | observational-memory-glm52-off | 34 | 0.832 | 0.494 | 0.031 | 21.426 | 0.417 | 0.993 |
| 4 | observational-memory-gpt55-low | 31 | 0.831 | 0.503 | 0.037 | 17.016 | 0.333 | 0.992 |
| 5 | observational-memory-glm52-high | 36 | 0.830 | 0.501 | 0.032 | 18.611 | 0.333 | 0.991 |
| 6 | observational-memory-gpt55-xhigh | 21 | 0.826 | 0.427 | 0.038 | 21.833 | 0.306 | 0.931 |
| 7 | observational-memory-gpt54-off | 36 | 0.826 | 0.523 | 0.045 | 13.972 | 0.306 | 0.936 |
| 8 | observational-memory-gpt54-low | 36 | 0.823 | 0.488 | 0.051 | 12.389 | 0.333 | 0.983 |
| 9 | observational-memory-gpt55-off | 34 | 0.820 | 0.473 | 0.053 | 15.324 | 0.389 | 0.986 |
| 10 | observational-memory-gpt54mini-xhigh | 12 | 0.819 | 0.465 | 0.042 | 11.667 | 0.278 | 0.934 |
| 11 | observational-memory-gpt54mini-low | 36 | 0.800 | 0.384 | 0.051 | 12.833 | 0.444 | 0.996 |
| 12 | observational-memory-gpt54mini-off | 36 | 0.794 | 0.370 | 0.048 | 16.778 | 0.389 | 0.992 |

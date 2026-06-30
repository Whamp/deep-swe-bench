# Topic clustering and coverage

Observations were clustered separately per task using greedy centroid clustering at cosine threshold `0.84`. Coverage counts each topic at most once per config/task/rep, so duplicate verbosity does not increase topic coverage.

Total topics: 1514 across 12 tasks.

| config | topics covered | topic recall | gold topic recall | mean task topic recall | obs/topic | solve | robust partial |
|---|---:|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-off | 388 | 0.256 | 0.717 | 0.267 | 1.902 | 0.417 | 0.993 |
| observational-memory-gpt54mini-low | 293 | 0.194 | 0.542 | 0.207 | 1.577 | 0.444 | 0.996 |
| observational-memory-glm52-max | 536 | 0.354 | 0.495 | 0.369 | 2.860 | 0.306 | 0.984 |
| observational-memory-glm52-high | 366 | 0.242 | 0.403 | 0.247 | 1.831 | 0.333 | 0.991 |
| observational-memory-gpt55-low | 318 | 0.210 | 0.370 | 0.213 | 1.742 | 0.333 | 0.992 |
| observational-memory-gpt55-off | 284 | 0.188 | 0.355 | 0.191 | 1.856 | 0.389 | 0.986 |
| observational-memory-gpt54mini-off | 369 | 0.244 | 0.346 | 0.251 | 1.637 | 0.389 | 0.992 |
| observational-memory-gpt55-xhigh | 323 | 0.213 | 0.322 | 0.195 | 1.666 | 0.306 | 0.931 |
| observational-memory-gpt54-low | 256 | 0.169 | 0.296 | 0.184 | 1.742 | 0.333 | 0.983 |
| observational-memory-gpt54-off | 272 | 0.180 | 0.287 | 0.180 | 1.849 | 0.306 | 0.936 |
| observational-memory-gpt54-xhigh | 173 | 0.114 | 0.251 | 0.115 | 1.913 | 0.222 | 0.934 |
| observational-memory-gpt54mini-xhigh | 154 | 0.102 | 0.183 | 0.093 | 1.338 | 0.278 | 0.934 |

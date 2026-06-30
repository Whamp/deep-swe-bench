# Observation type split

Classification is deterministic and heuristic. It is meant to surface patterns for inspection, not replace human review. Multi-label flags are retained, while `primary_type` is a single highest-priority bucket.

| config | obs | requirement | code structure | implementation | test/failure | self-report | solve | robust partial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-high | 670 | 0.066 | 0.128 | 0.525 | 0.216 | 0.030 | 0.333 | 0.991 |
| observational-memory-glm52-max | 1533 | 0.101 | 0.121 | 0.477 | 0.226 | 0.022 | 0.306 | 0.984 |
| observational-memory-glm52-off | 738 | 0.080 | 0.133 | 0.461 | 0.221 | 0.050 | 0.417 | 0.993 |
| observational-memory-gpt54-low | 446 | 0.070 | 0.083 | 0.309 | 0.296 | 0.213 | 0.333 | 0.983 |
| observational-memory-gpt54-off | 503 | 0.052 | 0.105 | 0.203 | 0.326 | 0.276 | 0.306 | 0.936 |
| observational-memory-gpt54-xhigh | 331 | 0.178 | 0.100 | 0.420 | 0.211 | 0.048 | 0.222 | 0.934 |
| observational-memory-gpt54mini-low | 462 | 0.110 | 0.106 | 0.249 | 0.234 | 0.262 | 0.444 | 0.996 |
| observational-memory-gpt54mini-off | 604 | 0.096 | 0.061 | 0.180 | 0.238 | 0.396 | 0.389 | 0.992 |
| observational-memory-gpt54mini-xhigh | 206 | 0.354 | 0.131 | 0.296 | 0.112 | 0.087 | 0.278 | 0.934 |
| observational-memory-gpt55-low | 554 | 0.090 | 0.106 | 0.321 | 0.240 | 0.209 | 0.333 | 0.992 |
| observational-memory-gpt55-off | 527 | 0.082 | 0.083 | 0.302 | 0.258 | 0.239 | 0.389 | 0.986 |
| observational-memory-gpt55-xhigh | 538 | 0.219 | 0.145 | 0.322 | 0.145 | 0.102 | 0.306 | 0.931 |

## By observer thinking level

| level | obs | configs | requirement | code structure | implementation | test/failure | self-report |
|---|---:|---:|---:|---:|---:|---:|---:|
| high | 670 | 1 | 0.066 | 0.128 | 0.525 | 0.216 | 0.030 |
| low | 1462 | 3 | 0.090 | 0.099 | 0.295 | 0.255 | 0.227 |
| max | 1533 | 1 | 0.101 | 0.121 | 0.477 | 0.226 | 0.022 |
| off | 2372 | 4 | 0.078 | 0.098 | 0.299 | 0.256 | 0.228 |
| xhigh | 1075 | 3 | 0.233 | 0.128 | 0.347 | 0.159 | 0.083 |

# Pairwise topic complementarity

Complementarity uses deduplicated topic coverage, not raw observation counts. `oracle_*` is a per-task quality oracle over the two configs' task-level medians/solve rates; it is descriptive and not an achievable combined-agent score by itself.

## GLM-5.2 off + GPT-5.4-mini low

| pair | union topic recall | jaccard overlap | unique topics A | unique topics B | oracle solve | oracle robust partial |
|---|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-off + observational-memory-gpt54mini-low | 0.357 | 0.259 | 248 | 153 | 0.500 | 0.997 |

## Top pairs by union topic recall

| config A | config B | union recall | overlap | unique A | unique B | oracle solve | oracle partial |
|---|---|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-max | observational-memory-gpt54mini-off | 0.494 | 0.210 | 379 | 212 | 0.417 | 0.992 |
| observational-memory-glm52-max | observational-memory-gpt55-xhigh | 0.454 | 0.249 | 365 | 152 | 0.389 | 0.988 |
| observational-memory-glm52-max | observational-memory-gpt54mini-low | 0.451 | 0.214 | 390 | 147 | 0.468 | 0.996 |
| observational-memory-glm52-high | observational-memory-glm52-max | 0.446 | 0.334 | 140 | 310 | 0.417 | 0.992 |
| observational-memory-glm52-max | observational-memory-glm52-off | 0.443 | 0.379 | 282 | 134 | 0.431 | 0.993 |
| observational-memory-glm52-max | observational-memory-gpt55-low | 0.440 | 0.282 | 348 | 130 | 0.417 | 0.992 |
| observational-memory-glm52-max | observational-memory-gpt54-off | 0.439 | 0.217 | 392 | 128 | 0.375 | 0.989 |
| observational-memory-glm52-max | observational-memory-gpt54-low | 0.427 | 0.224 | 391 | 111 | 0.375 | 0.988 |
| observational-memory-glm52-max | observational-memory-gpt55-off | 0.422 | 0.283 | 355 | 103 | 0.477 | 0.989 |
| observational-memory-glm52-off | observational-memory-gpt54mini-off | 0.403 | 0.241 | 241 | 222 | 0.444 | 0.994 |
| observational-memory-glm52-high | observational-memory-gpt54mini-off | 0.398 | 0.219 | 234 | 237 | 0.444 | 0.993 |
| observational-memory-glm52-max | observational-memory-gpt54mini-xhigh | 0.387 | 0.177 | 432 | 50 | 0.347 | 0.988 |
| observational-memory-glm52-max | observational-memory-gpt54-xhigh | 0.381 | 0.229 | 404 | 41 | 0.361 | 0.989 |
| observational-memory-gpt54mini-off | observational-memory-gpt55-xhigh | 0.380 | 0.201 | 253 | 207 | 0.417 | 0.992 |
| observational-memory-glm52-off | observational-memory-gpt55-xhigh | 0.369 | 0.272 | 236 | 171 | 0.444 | 0.993 |

## Low-overlap high-quality pairs

| config A | config B | union recall | overlap | unique A | unique B | oracle solve | oracle partial |
|---|---|---:|---:|---:|---:|---:|---:|
| observational-memory-gpt54mini-low | observational-memory-gpt55-off | 0.289 | 0.317 | 154 | 145 | 0.583 | 0.997 |
| observational-memory-glm52-off | observational-memory-gpt54mini-low | 0.357 | 0.259 | 248 | 153 | 0.500 | 0.997 |
| observational-memory-gpt54-xhigh | observational-memory-gpt54mini-low | 0.237 | 0.298 | 66 | 186 | 0.500 | 0.997 |
| observational-memory-gpt54-off | observational-memory-gpt54mini-low | 0.293 | 0.275 | 150 | 171 | 0.500 | 0.997 |
| observational-memory-gpt54mini-low | observational-memory-gpt54mini-off | 0.338 | 0.295 | 142 | 218 | 0.528 | 0.996 |
| observational-memory-gpt54mini-low | observational-memory-gpt54mini-xhigh | 0.250 | 0.183 | 224 | 85 | 0.472 | 0.996 |
| observational-memory-glm52-high | observational-memory-gpt54mini-low | 0.351 | 0.241 | 238 | 165 | 0.500 | 0.996 |
| observational-memory-gpt54mini-low | observational-memory-gpt55-xhigh | 0.337 | 0.208 | 187 | 217 | 0.500 | 0.996 |
| observational-memory-gpt54-low | observational-memory-gpt54mini-low | 0.278 | 0.304 | 128 | 165 | 0.472 | 0.996 |
| observational-memory-glm52-max | observational-memory-gpt54mini-low | 0.451 | 0.214 | 390 | 147 | 0.468 | 0.996 |
| observational-memory-gpt54mini-low | observational-memory-gpt55-low | 0.311 | 0.297 | 153 | 178 | 0.472 | 0.996 |
| observational-memory-gpt54-off | observational-memory-gpt54mini-off | 0.339 | 0.247 | 145 | 242 | 0.472 | 0.994 |
| observational-memory-glm52-off | observational-memory-gpt54mini-off | 0.403 | 0.241 | 241 | 222 | 0.444 | 0.994 |
| observational-memory-glm52-off | observational-memory-gpt54-low | 0.338 | 0.260 | 255 | 123 | 0.417 | 0.993 |
| observational-memory-glm52-off | observational-memory-gpt54mini-xhigh | 0.295 | 0.213 | 293 | 59 | 0.417 | 0.993 |

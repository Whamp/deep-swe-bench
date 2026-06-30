# Timeliness-adjusted semantic coverage

Timeliness uses the observational-memory `coversUpToId` watermark mapped onto the final source-entry sequence in each session. Early/mid/late are thirds of final source-entry coverage. This measures whether memories landed early enough in the run, not wall-clock latency directly.

| config | early topic recall | early+mid topic recall | final topic recall | early obs share | late obs share | mean source coverage | solve | robust partial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-max | 0.178 | 0.286 | 0.354 | 0.511 | 0.164 | 0.381 | 0.306 | 0.984 |
| observational-memory-glm52-off | 0.137 | 0.209 | 0.256 | 0.484 | 0.167 | 0.405 | 0.417 | 0.993 |
| observational-memory-gpt55-xhigh | 0.187 | 0.205 | 0.213 | 0.833 | 0.052 | 0.250 | 0.306 | 0.931 |
| observational-memory-glm52-high | 0.125 | 0.182 | 0.242 | 0.476 | 0.255 | 0.437 | 0.333 | 0.991 |
| observational-memory-gpt55-low | 0.094 | 0.176 | 0.210 | 0.453 | 0.162 | 0.407 | 0.333 | 0.992 |
| observational-memory-gpt54mini-off | 0.090 | 0.167 | 0.244 | 0.348 | 0.326 | 0.489 | 0.389 | 0.992 |
| observational-memory-gpt54mini-low | 0.083 | 0.138 | 0.194 | 0.420 | 0.314 | 0.473 | 0.444 | 0.996 |
| observational-memory-gpt55-off | 0.080 | 0.138 | 0.188 | 0.391 | 0.239 | 0.435 | 0.389 | 0.986 |
| observational-memory-gpt54-low | 0.085 | 0.129 | 0.169 | 0.448 | 0.303 | 0.462 | 0.333 | 0.983 |
| observational-memory-gpt54-off | 0.067 | 0.122 | 0.180 | 0.302 | 0.348 | 0.518 | 0.306 | 0.936 |
| observational-memory-gpt54-xhigh | 0.085 | 0.104 | 0.114 | 0.737 | 0.079 | 0.293 | 0.222 | 0.934 |
| observational-memory-gpt54mini-xhigh | 0.096 | 0.102 | 0.102 | 0.956 | 0.000 | 0.197 | 0.278 | 0.934 |

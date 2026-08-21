## DeepSWE results for local DeepSeek V4 Flash 0731

The local IQ2_XXS model solved **6 of 12 coding tasks** at max reasoning. The API averaged **5.3 of 12** at the same reasoning level across three passes.

The local result is inside the API's observed range of 5–6 solves and slightly above its average. That is strong evidence that the quantized model kept its coding ability, but one local pass is not enough to prove parity.

### How I counted the API result

Each pass uses the same 12 tasks. The API ran three passes and produced 16 full solves, so the average is 16 ÷ 3 = **5.3 solves per 12-task pass**. The three passes solved 6, 5, 5 tasks. One other API result had a negative reward; I list it separately instead of subtracting it from the solve count.

| Run | Reasoning | Passes | Full solves per 12 tasks | Feature tests passed | Existing tests kept passing | Average score | Tokens per pass | Agent time per pass |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| API | `max` | 3 | **5.3/12** | 89.9% | 99.4% | 0.950 | 2.14M | 4h 38m |
| Local IQ2_XXS | `low` | 1 | **5/12** | 85.5% | 99.5% | 0.955 | 2.55M | 12h 14m |
| Local IQ2_XXS | `max` | 1 | **6.0/12** | 89.1% | 100.0% | 0.966 | 3.21M | 19h 51m |

“Feature tests passed” measures whether the model implemented the requested change. “Existing tests kept passing” measures whether it broke working code. Token totals exclude cached input.

### Setup and speed

- All three runs used Pi `0.84.0`.
- The API used max reasoning, DeepSeek's FP8 endpoint, and no fallback provider.
- The local runs used low and max reasoning as shown above.
- The API finished 36 attempts in 2h 45m with 12 workers. Its average task took 23.2 minutes.
- The local low pass used one worker. It took 12h 17m, or 61.2 minutes per task—2.6× slower than the API.
- The local max pass took 21h 57m from start to finish, including the unrelated host-memory pause. The tasks themselves used 19h 51m, or 99.3 minutes each—4.3× slower than the API. It used 1.50× as many non-cached tokens. One task timed out.

### Compared with other local models

These runs use the same 12 tasks. The older models ran three passes each; local DeepSeek ran once.

| Local model | Reasoning | Passes | Full solves per 12 tasks | Feature tests passed | Existing tests kept passing |
|---|---|---:|---:|---:|---:|
| DeepSeek IQ2_XXS | `max` | 1 | **6.0/12** | 89.1% | 100.0% |
| DeepSeek IQ2_XXS | `low` | 1 | **5.0/12** | 85.5% | 99.5% |
| Qwen3.6 27B AWQ | `high` | 3 | **0.0/12** | 62.5% | 99.2% |
| ThinkingCap Qwen3.6 27B | `high` | 3 | **0.3/12** | 57.3% | 99.4% |
| Qwen AgentWorld 35B A3B | `high` | 3 | **0.0/12** | 35.9% | 98.7% |
| Gemma 4 31B | `high` | 3 | **0.0/12** | 10.2% | 55.2% |

ThinkingCap solved one of its 36 attempts, which works out to 0.3 solves per 12-task pass. Qwen3.6, AgentWorld, and Gemma had no full solves. Qwen3.6's older result does not record the current task revision, so treat that row as a rough comparison.

### What benchlocal tells us

The patched DeepSeek server scored 121/150 at low reasoning and 123/150 at max. Stock `b10200` scored 122/150 at low. That is good evidence that the server changes did not damage the model.

The published benchlocal scores for these strong local models sit in a narrow range: Qwen3.6 has 109/150, ThinkingCap has 120/150, and the AgentWorld BF16 reference has 125/150. DeepSWE separates them much more sharply. This suggests benchlocal is becoming saturated as a model-ranking test. It is still useful as a quick check that a server works correctly.

Gemma 4 has no published full 8-pack score, so I left it out of that comparison. The exact AgentWorld AWQ profile has only a 29/30 quick check; 125/150 comes from its BF16 reference.

### Takeaway

The PR's quality claim holds up: the patched server scored almost exactly like stock on benchlocal, and the local 2-bit model matched the API's coding-task range at max reasoning. The remaining cost is speed and verbosity, not an obvious loss of capability. I would still avoid claiming proven parity because the local result has one pass while the API has three.

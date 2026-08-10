# Local llama.cpp — DeepSeek V4 Flash 0731 (Antirez IQ2_XXS, q8 KV, fast-prefill)

Provider/model evidence note for config
`baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0`. This is the local
llama.cpp baseline used to compare an IQ2_XXS quantized deployment of DeepSeek
V4 Flash 0731 against the OpenRouter API fp8 baseline
(`baseline-openrouter-deepseek-v4-flash-0731@1.0.0`).

## Server

| | |
| --- | --- |
| Endpoint | `http://100.92.238.117:8033/v1` (server60 tailnet; `localhost:8033` only resolves on server60 itself and is NOT reachable from benchmark containers) |
| Server | llama.cpp llama-server, build `b1-0379cf4` |
| Served model id | `deepseek-v4-flash-0731-q8-fast-prefill` (`owned_by: llamacpp`) |
| Weights | Antirez `DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ` (IQ2_XXS 2-bit weights, q8_0 KV cache, shared-expert + attention-proj 8-bit) |
| Context window | 430,080 tokens |
| Parallel slots | 1 → benchmark **concurrency must be 1** |
| Hardware | 4× RTX 3090 @ 230W each |

The `q8` in the served id refers to the **q8_0 KV cache**, not the weights; the
weights are IQ2_XXS (2-bit). The name is preserved verbatim because the
`model_change` smoke assertion must match it exactly.

## Reasoning

Reasoning is off by default (`reasoning_format: "none"` in `/props`). It is
enabled per request via `chat_template_kwargs`:

```json
{ "enable_thinking": true, "reasoning_effort": "low" }
```

Note the key is **`enable_thinking`**, not the `thinking` key used by the older
server60:8200 deployment. `reasoning_effort` accepts **`low`, `high`, `max`**
(proven in `analysis/llamacpp-deepseek-v4-flash-0731-q8-reasoning-probe.json`).
All three emit a `reasoning` field. The model leaf maps Pi thinking levels
`low→low`, `high→high`, `max→max`.

## Sampling

The official DeepSeek-V4-Flash-0731 model card
(<https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731#how-to-run-locally>)
states:

> For local deployment, we recommend `temperature = 1.0`, with `top_p = 0.95`
> for **agentic scenarios** and `top_p = 1.0` otherwise.

DeepSeek's own published V4-Flash coding-agent benchmark numbers use exactly
`max` reasoning effort with `temperature = 1.0, top_p = 0.95`. This benchmark is
agentic, so the config pins **`temperature 1.0 / top_p 0.95`** and disables the
unspecified knobs (`top_k 0`, `min_p 0.0`, `repeat_penalty 1.0`) for a clean,
reproducible profile that matches the OpenRouter API baseline.

The local model declaration sets `maxTokens: 65536`. Completed OpenRouter API
baseline request captures contain `max_completion_tokens: 65536`, so this keeps
the per-response completion ceiling aligned rather than using the older local
config's 81,920-token cap. The local server's 430,080-token context window still
differs from OpenRouter's larger advertised context; that deployment constraint
is explicit and cannot be normalized in this comparison.

The server's own defaults (`temperature 1.0 / top_p 1.0`, with llama.cpp-stock
`top_k 40 / min_p 0.05 / repeat_penalty 1.0`) correspond to the card's
"otherwise" (non-agentic) recommendation and are therefore **overridden** by the
`local-llamacpp-deepseek-v4-request.ts` request extension. `temperature 1.0` and
`top_p 1.0` are NOT llama.cpp stock defaults (stock is `0.80 / 0.95`); only
`top_k 40 / min_p 0.05 / repeat_penalty 1.0` are stock.

## Bash-timeout safety extension

Local models (agentworld, gemma-4, thinking-cap) have been observed to omit the
`timeout` argument on `bash` tool calls and get permanently blocked. The config
loads `local-llamacpp-deepseek-v4-bash-timeout.ts`, which hooks `tool_call` on
`bash` and injects a default `timeout` of 360s when the model omits one,
auditing each call to `/out/llamacpp-deepseek-v4-bash-timeout.ndjson`.

## Subject version

`pi@0.84.0`, matching the completed OpenRouter API baseline and eliminating the
subject-version confound. The 0.84.1 "terminating blocked tool calls" feature is
not needed here: this config's extension injects a timeout before Bash execution
rather than terminating an active tool batch. The pi 0.84.x `samplingParams`
capability is available, but sampling is instead pinned via the proven request
extension for this provider.

## Evidence

- `analysis/llamacpp-deepseek-v4-flash-0731-q8-server-gate.json` — reachability,
  `/props` defaults, served model id, build info.
- `analysis/llamacpp-deepseek-v4-flash-0731-q8-reasoning-probe.json` —
  `enable_thinking:true` with `reasoning_effort` low/high/max all accepted.
- `analysis/llamacpp-deepseek-v4-flash-0731-q8-pi-request-probe.jsonl` —
  expected pi request shape, confirmed by the smoke `provider_request` assertion
  at run time.
- `analysis/llamacpp-deepseek-v4-flash-0731-q8-image-probe.json` — the rebuilt
  v4-pi0840-tools task image contains `pi --version 0.84.0` plus `rg`/`fd`.

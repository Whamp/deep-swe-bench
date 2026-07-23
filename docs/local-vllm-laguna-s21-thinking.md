# Local vLLM Poolside Laguna S 2.1 thinking control

This note records the provider path and request shape for the server60 model
`poolside/Laguna-S-2.1-INT4`. It is the reference for the unlaunched clean Pi
baseline `configs/baseline-laguna-s21/`.

## Provider/API path

- Endpoint: `http://100.92.238.117:30000/v1`
- Provider: `local-vllm`
- API: `openai-completions`
- Auth: dummy local key (`local`); no secret is required
- Model id: `poolside/Laguna-S-2.1-INT4`
- Live `/v1/models` response: `max_model_len: 262144`
- Live server fingerprint: `vllm-0.25.1-tp4-8d20902f`

Pi metadata for this model uses `thinkingFormat: "chat-template"` and:

```json
"chatTemplateKwargs": {
  "enable_thinking": { "$var": "thinking.enabled" }
}
```

A small config extension adds `preserve_thinking: true` to the same
`chat_template_kwargs` object on every Laguna request. The model card recommends
`temperature: 0.7` and `top_p: 0.95`; the baseline applies those values through a
model-scoped request extension.

## Official/provider docs

- https://huggingface.co/poolside/Laguna-S-2.1-INT4
- https://huggingface.co/poolside/Laguna-S-2.1
- https://recipes.vllm.ai/poolside/Laguna-S-2.1
- https://docs.vllm.ai/en/stable/features/tool_calling/

The Laguna card documents native interleaved reasoning, preserved thinking,
per-request `chat_template_kwargs.enable_thinking`, and vLLM deployment with
`--tool-call-parser poolside_v1`, `--reasoning-parser poolside_v1`, and
auto tool choice. The live server already returns structured tool calls, so this
config does not add a parser or prompt workaround.

## Live/provider-response evidence

Artifacts:

- `analysis/local-vllm-laguna-s21-models-probe.json`
- `analysis/local-vllm-laguna-s21-tool-probe.json`
- `analysis/local-vllm-laguna-s21-thinking-tool-probe.json`

The live endpoint returned a structured `tool_calls` response for a `bash`
function with `finish_reason: "tool_calls"`. The request using:

```json
{
  "chat_template_kwargs": {
    "enable_thinking": true,
    "preserve_thinking": true
  },
  "temperature": 0.7,
  "top_p": 0.95
}
```

returned model id `poolside/Laguna-S-2.1-INT4`, a valid bash tool call, and
usage fields `prompt_tokens`, `completion_tokens`, and `total_tokens`.

## Config rules

Use the model-bearing leaf:

```text
configs/baseline-laguna-s21/Laguna-S-2.1-INT4/high/
```

The config has no `system_preamble.md`, no `orchestration.md`, and no
config-authored prompt text. It does not copy the Qwen-specific
`qwen-chat-template` compatibility or ThinkingCap's hard thinking budget.

The requested benchmark is documented but deliberately not launched:

```bash
PYTHONPATH=. python3 harness/run_batch.py \
  --configs baseline-laguna-s21 \
  --subset 12_v2 \
  --runs 3 \
  --workers 2 \
  --model local-vllm/poolside/Laguna-S-2.1-INT4 \
  --thinking high \
  --run-id laguna-s21-high-12v2-r3-w2 \
  --progress-interval 15
```

## Stale patterns to avoid

- Do not use `thinkingFormat: "qwen-chat-template"`; Laguna's documented
  control is generic `chat_template_kwargs.enable_thinking`.
- Do not assume Qwen's `thinking_token_budget` is a Laguna setting; no such
  field was needed in the live probe or documented by the model card.
- Do not treat the live provider probe as a benchmark smoke pass. The config's
  leaf-local `smoke.json` remains pending until Will explicitly launches it.

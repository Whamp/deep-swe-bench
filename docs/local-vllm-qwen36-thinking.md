# Local vLLM Qwen3.6 thinking control

This note is the project reference for using Will's server60 Qwen3.6 local-vLLM endpoint in benchmark configs.

Validated on 2026-06-30 from three sources:

1. Qwen/vLLM documentation for Qwen thinking and non-thinking modes.
2. Pi's OpenAI-compatible request-shape behavior for `compat.thinkingFormat: "qwen-chat-template"`.
3. A tiny live call against server60's OpenAI-compatible vLLM endpoint.

## Provider/API path

Pi config shape:

```json
{
  "providers": {
    "local-vllm": {
      "baseUrl": "http://100.92.238.117:30000/v1",
      "api": "openai-completions",
      "apiKey": "local",
      "compat": {
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false,
        "thinkingFormat": "qwen-chat-template"
      },
      "models": [
        {
          "id": "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4",
          "reasoning": true,
          "contextWindow": 262144,
          "maxTokens": 16384,
          "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 }
        }
      ]
    }
  }
}
```

Auth uses a dummy local API key (`local`); no provider secret is required.

## Official/provider docs

Fetched 2026-06-30:

- `https://docs.qwencloud.com/developer-guides/text-generation/thinking`
- `https://qwen.readthedocs.io/en/stable/deployment/vllm.html`

Qwen Cloud documents Qwen3.6 as a hybrid thinking model where thinking can be toggled per request with `enable_thinking`. It also documents `preserve_thinking` for multi-turn reasoning preservation.

The Qwen vLLM deployment guide documents OpenAI-compatible local serving through vLLM and says Qwen3 thinking can be disabled with:

```json
"chat_template_kwargs": { "enable_thinking": false }
```

The vLLM guide explicitly notes this is not standard OpenAI API behavior; it is an extra server/framework parameter.

## Pi request-shape evidence

Artifact: `analysis/local-vllm-qwen-thinking-request-probe.jsonl`.

A mock OpenAI-compatible server captured Pi's request body for the configured local-vLLM model.

Relevant rows:

- Pi thinking `off` clamps to `off` and sends:

```json
"chat_template_kwargs": { "enable_thinking": false, "preserve_thinking": true }
```

- Pi thinking `low` clamps to `low` and sends:

```json
"chat_template_kwargs": { "enable_thinking": true, "preserve_thinking": true }
```

Pi sends no top-level `enable_thinking` and no `reasoning_effort` for this model. The controlling field is `chat_template_kwargs.enable_thinking`.

The benchmark `baseline-qwen36-xhigh` leaf deliberately adds:

```json
"thinkingLevelMap": { "xhigh": "xhigh" }
```

This exposes `xhigh` as a named Pi level for the local model. It is still not a provider-side reasoning-effort level: Qwen/vLLM receives binary `enable_thinking: true` plus a top-level `thinking_token_budget` injected by `configs/baseline-qwen36-xhigh/extensions/local-vllm-preserve-thinking.ts`.

The current request-shape artifact includes `xhigh` and shows:

```json
"requestedThinking": "xhigh",
"clampedThinking": "xhigh",
"sentChatTemplateKwargs": { "enable_thinking": true, "preserve_thinking": true },
"sentReasoningEffort": null
```

## server60 vLLM serving evidence

Validated 2026-07-04 from `server60:~/inference/serving/vllm/compose.yaml`.

The active service is `vllm/vllm-openai:nightly` on port `30000`, serving:

```text
cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4
```

Important compose fields:

- `--reasoning-parser=qwen3`
- `--reasoning-config {"reasoning_start_str":"<think>","reasoning_end_str":"</think>"}`
- `--default-chat-template-kwargs {"preserve_thinking": true}`
- comment documents that hard budget is per-request top-level `thinking_token_budget`, not server default

For benchmark configs, the vendored extension injects:

- `chat_template_kwargs.preserve_thinking = true`
- `thinking_token_budget` by Pi thinking level for this model:
  - minimal: 4096
  - low: 8192
  - medium: 16384
  - high: 32768
  - xhigh: 65536

## Live endpoint evidence

Artifacts:

- `analysis/local-vllm-qwen-server60-compose-20260704.txt`
- `analysis/local-vllm-qwen-off-live-probe.jsonl`
- `analysis/local-vllm-qwen-budget-live-probe.jsonl`

The off live probe checked:

- `/v1/models` contained `cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`.
- A tiny `/v1/chat/completions` request with:

```json
"chat_template_kwargs": { "enable_thinking": false, "preserve_thinking": true }
```

returned:

- `responseModel`: `cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`
- `content`: `OK`
- `reasoningContent`: `null`
- `hasReasoningContent`: `false`
- usage tokens present

The budgeted-thinking live probe checked the same endpoint with:

```json
{
  "chat_template_kwargs": { "enable_thinking": true, "preserve_thinking": true },
  "thinking_token_budget": 64
}
```

It returned visible content (`OK`), non-empty `reasoningContent`, and usage tokens in 9.154s, proving the current server accepts the top-level budget field and does not hang indefinitely when thinking is budgeted.

## Config rules

Use this provider through a model-bearing config leaf, for example:

```text
configs/<config>/Qwen3.6-27B-AWQ-BF16-INT4/xhigh/models.json
configs/<config>/Qwen3.6-27B-AWQ-BF16-INT4/xhigh/settings.json
```

For the plain local-Qwen executor benchmark, use `configs/baseline-qwen36-xhigh/Qwen3.6-27B-AWQ-BF16-INT4/xhigh/` with `thinkingLevelMap.xhigh`, `thinkingBudgets.xhigh = 65536`, and the budgeted `local-vllm-preserve-thinking.ts` extension copied from server60.

For GPT executor + Qwen observational-memory worker configs, use:

```text
configs/<config>/gpt-5.5/low/models.json
configs/<config>/gpt-5.5/low/settings.json
```

When Qwen is an observational-memory worker while the executor is `openai-codex/gpt-5.5`, the leaf still needs `models.json` so Pi can resolve the `local-vllm` worker model inside the container.

For observational-memory worker usage accounting, load `extensions/om-worker-usage-trace.ts` before `extensions/pi-observational-memory/src/index.ts` and require `pi-agent/observational-memory/worker-usage/usage.ndjson` in smoke contracts.

## Nested-worker note

Config-level `before_provider_request` hooks do not see observational-memory worker `agentLoop` calls. For this Qwen-off config that is acceptable because no custom hook is needed to disable thinking: Pi's core OpenAI-compatible adapter applies `compat.thinkingFormat: "qwen-chat-template"` in the worker's own model stream path.

The existing `local-vllm-preserve-thinking.ts` extension may still be loaded for consistency with local-Qwen configs, but it is not the proof that worker requests are off. The proof is Pi's core request-shape probe plus worker smoke evidence showing `provider: local-vllm`, model `cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, and `thinkingLevel: off` in the worker-usage trace.

## Smoke expectations

A benchmark config using Qwen as an observational-memory worker should require:

- main executor session markers for `openai-codex/gpt-5.5` and `thinkingLevel: low` when that is the selected executor;
- `arm_settings.observational-memory.model.provider == "local-vllm"`;
- `arm_settings.observational-memory.model.thinking == "off"`;
- `om_worker_provider == "local-vllm"`;
- `om_worker_model == "cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4"`;
- nonzero `om_worker_calls`, `om_observer_calls`, `om_worker_total_tokens`, and `combined_total_tokens`;
- worker trace text containing `"provider":"local-vllm","model":"cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4","api":"openai-completions","thinkingLevel":"off"`;
- no `model_unavailable` text.

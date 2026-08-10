# OpenAI Codex GPT-5.6 Terra thinking validation

This note records the provider path for benchmark configs using Pi `0.84.1`,
`openai-codex/gpt-5.6-terra`, and Pi thinking `low`.

## Official model contract

OpenAI describes GPT-5.6 Terra as the GPT-5.6 model that balances intelligence
and cost. The official model page documents text and image input, text output,
reasoning tokens, streaming, function calling, the Responses API, a 1,050,000
context window, and 128,000 maximum output tokens:

- <https://developers.openai.com/api/docs/models/gpt-5.6-terra>
- <https://developers.openai.com/api/docs/guides/latest-model>

## Pi and credential route

Pi `0.84.1` resolves the benchmark executor as:

| Field | Value |
| --- | --- |
| Provider | `openai-codex` |
| Model | `gpt-5.6-terra` |
| API adapter | `openai-codex-responses` |
| Billing | Codex OAuth subscription quota |
| Credential route | `OPENAI_CODEX_OAUTH` |
| Pi context window | 272,000 tokens |
| Pi maximum output | 128,000 tokens |
| Thinking | `low` |

The benchmark uses Pi's effective limits for the Codex route rather than the
larger public API context window.

## Request-shape validation

The local mock probe in
`analysis/read-long-lines-pilot/provider-evidence/request-probe.jsonl` exercises Pi `0.84.1`'s
real Codex Responses adapter with one tool. It records:

```json
{"provider":"openai-codex","model":"gpt-5.6-terra","requestedThinking":"low","clampedThinking":"low","request":{"model":"gpt-5.6-terra","reasoning":{"effort":"low","summary":"auto"},"stream":true,"store":false,"toolCount":1}}
```

This proves that Pi preserves `low` and sends an explicit low reasoning effort.
The probe uses a local HTTP server and makes no provider call.

## Live validation and smoke requirement

No standalone paid Terra generation was made while preparing this config. The
confirmed benchmark preflight must be the first live end-to-end call. It must
leave native session usage, RPC lifecycle evidence, a `low` thinking record,
and a captured provider request with `model: "gpt-5.6-terra"` and
`reasoning.effort: "low"` before conditional fan-out begins.

Each Terra leaf must pin `defaultThinkingLevel: "low"`, use the
`OPENAI_CODEX_OAUTH` route, require the local request-shape artifact, and assert
the live preflight evidence above. Do not substitute the OpenRouter model or
infer thinking behavior from `pi --list-models` alone.

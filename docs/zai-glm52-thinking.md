# Z.ai GLM-5.2 thinking modes

This note is the project reference for configuring direct Z.ai GLM-5.2 calls in
benchmark configs. Do not copy old `models.json` compatibility blocks without
checking them against this document.

Primary Z.ai docs:

- GLM-5.2 guide: <https://docs.z.ai/guides/llm/glm-5.2>
- Chat completion API: <https://docs.z.ai/api-reference/llm/chat-completion>

## API endpoints

Pi's built-in `zai/glm-5.2` model uses the coding endpoint:

```text
https://api.z.ai/api/coding/paas/v4/chat/completions
```

A direct probe on 2026-06-28 found the general docs endpoint
`https://api.z.ai/api/paas/v4/chat/completions` returned HTTP 429 for the local
account, while the coding endpoint succeeded. Use the endpoint configured by Pi
unless deliberately testing another Z.ai product path.

## Provider parameters

GLM-5.2 thinking is controlled by two request fields:

```json
{
  "thinking": { "type": "enabled" },
  "reasoning_effort": "high"
}
```

- `thinking.type`: `enabled` or `disabled`.
- `reasoning_effort`: only applies when thinking is enabled.
- Z.ai documents valid `reasoning_effort` values as `max`, `xhigh`, `high`,
  `medium`, `low`, `minimal`, and `none`.
- Z.ai documents these effective mappings:
  - `none` and `minimal` skip thinking.
  - `low` and `medium` map to `high`.
  - `xhigh` maps to `max`.
  - omitted `reasoning_effort` defaults to `max` when thinking is enabled.

## Pi mapping

Pi's maintained built-in `zai/glm-5.2` metadata currently uses:

```json
{
  "compat": {
    "supportsReasoningEffort": true,
    "thinkingFormat": "zai",
    "zaiToolStream": true
  },
  "thinkingLevelMap": {
    "minimal": null,
    "low": "high",
    "medium": "high",
    "high": "high",
    "xhigh": "max"
  }
}
```

Expected Pi-to-Z.ai request shape:

| Pi thinking level | Z.ai request effect |
| --- | --- |
| `off` | `thinking: {"type":"disabled"}` and no `reasoning_effort` |
| `low` | `thinking: {"type":"enabled"}`, `reasoning_effort: "high"` |
| `medium` | `thinking: {"type":"enabled"}`, `reasoning_effort: "high"` |
| `high` | `thinking: {"type":"enabled"}`, `reasoning_effort: "high"` |
| `xhigh` | `thinking: {"type":"enabled"}`, `reasoning_effort: "max"` |

Therefore, for GLM-5.2, `low`, `medium`, and `high` are not independent provider
modes. The meaningful direct-ZAI comparison is usually `off` vs `high` vs
`xhigh`/`max`, unless a test intentionally sends literal provider values outside
Pi's mapping.

## Config rules

Prefer Pi's built-in direct ZAI model entry when possible:

```text
zai/glm-5.2
```

If a benchmark config must define a custom direct-ZAI `models.json` leaf, it must
not use stale compatibility data. At minimum, GLM-5.2 needs:

```json
{
  "providers": {
    "zai": {
      "apiKey": "$ZAI_API_KEY",
      "compat": {
        "maxTokensField": "max_tokens",
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": true,
        "supportsStore": false,
        "thinkingFormat": "zai",
        "zaiToolStream": true
      },
      "models": [
        {
          "id": "glm-5.2",
          "name": "GLM-5.2",
          "reasoning": true,
          "thinkingLevelMap": {
            "minimal": null,
            "low": "high",
            "medium": "high",
            "high": "high",
            "xhigh": "max"
          },
          "input": ["text"],
          "contextWindow": 1000000,
          "maxTokens": 131072
        }
      ]
    }
  }
}
```

Do **not** set `supportsReasoningEffort: false` for GLM-5.2. With Pi's
`thinkingFormat: "zai"`, that collapses all non-off Pi thinking levels into
`thinking: {"type":"enabled"}` with no explicit `reasoning_effort`; Z.ai then
uses its default effort instead of the requested level.

## Validation requirement

Before launching a benchmark where GLM-5.2 thinking level is part of the
experimental condition, validate both layers:

1. **Request-shape validation:** prove what Pi will send for each configured
   thinking level. A local mock OpenAI-compatible server is enough for this and
   avoids spending provider tokens. Check for the exact `thinking` and
   `reasoning_effort` fields.
2. **Provider-response validation:** run a tiny direct Z.ai probe against the
   same endpoint and verify returned `usage.completion_tokens_details.reasoning_tokens`
   plus streamed `delta.reasoning_content` when streaming matters.
3. **Smoke-cell validation:** for benchmark configs using GLM-5.2 as an
   extension worker, run the harness smoke cell and verify worker traces and
   `result.json` fields show the intended worker provider/model/thinking.

Validation artifacts from the 2026-06-28 incident are kept under `analysis/`:

- `analysis/pi-zai-request-shape-probe.jsonl` — local mock proof that the old
  config sent no `reasoning_effort`, while the corrected config sends `high` or
  `max`.
- `analysis/zai-glm52-reasoning-probe-coding-endpoint.jsonl` — direct non-stream
  Z.ai coding-endpoint probe.
- `analysis/zai-glm52-reasoning-repeat-probe.jsonl` — repeated direct probe with
  a reasoning-forcing prompt.
- `analysis/zai-glm52-streaming-probe.jsonl` — streaming probe proving
  `delta.reasoning_content` and `reasoning_tokens` are available.

Treat results produced with stale `supportsReasoningEffort: false` configs as
"thinking enabled with provider-default effort" for non-off modes, not as valid
low/high/xhigh comparisons.

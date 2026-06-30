# Z.ai GLM-5.1 thinking modes

This note is the project reference for configuring direct Z.ai GLM-5.1 calls in
benchmark configs. Do not infer GLM-5.1 behavior from GLM-5.2 without checking
these docs and request/response probes.

Primary Z.ai docs:

- GLM-5.1 guide: <https://docs.z.ai/guides/llm/glm-5.1>
- Chat completion API: <https://docs.z.ai/api-reference/llm/chat-completion>
- Thinking mode: <https://docs.z.ai/guides/capabilities/thinking-mode>
- Deep thinking: <https://docs.z.ai/guides/capabilities/thinking>
- Core parameters: <https://docs.z.ai/guides/overview/concept-param>

## Model and endpoint

Pi's built-in `zai/glm-5.1` model currently uses:

```text
https://api.z.ai/api/coding/paas/v4/chat/completions
```

Pi metadata says GLM-5.1 is text-only in Pi:

```json
{
  "id": "glm-5.1",
  "provider": "zai",
  "input": ["text"],
  "contextWindow": 200000,
  "maxTokens": 131072,
  "compat": {
    "supportsReasoningEffort": false,
    "thinkingFormat": "zai",
    "zaiToolStream": true
  },
  "reasoning": true
}
```

## Provider parameters

Z.ai documents GLM-5.1 thinking with the `thinking` object:

```json
{
  "thinking": { "type": "enabled" }
}
```

- `thinking.type`: `enabled` or `disabled`.
- Z.ai documents thinking as enabled by default for GLM-5.1.
- Z.ai's GLM-5.1 guide examples do **not** include `reasoning_effort`.
- Z.ai's parameter docs say `reasoning_effort` is only supported by GLM-5.2 and
  above; do not treat GLM-5.1 low/high/xhigh as real provider effort levels.

## Pi mapping

Because Pi marks `supportsReasoningEffort: false` for built-in `zai/glm-5.1`,
all non-off Pi thinking levels collapse to the same provider request:

| Pi thinking level | Z.ai request effect |
| --- | --- |
| `off` | `thinking: {"type":"disabled"}` and no `reasoning_effort` |
| `low` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `medium` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `high` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `xhigh` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |

Therefore, for GLM-5.1, benchmark conditions should be named as **thinking off**
vs **thinking enabled**, not low/high/xhigh. If a config label says
`glm51-low`, `glm51-high`, or `glm51-xhigh`, those labels are misleading unless a
separate provider probe proves a real distinction.

## Config rules

Prefer Pi's built-in direct ZAI model entry when possible:

```text
zai/glm-5.1
```

If a benchmark config must define a custom direct-ZAI `models.json` leaf for
GLM-5.1, it should match the provider docs and Pi behavior:

```json
{
  "providers": {
    "zai": {
      "apiKey": "$ZAI_API_KEY",
      "compat": {
        "maxTokensField": "max_tokens",
        "supportsDeveloperRole": false,
        "supportsReasoningEffort": false,
        "supportsStore": false,
        "thinkingFormat": "zai",
        "zaiToolStream": true
      },
      "models": [
        {
          "id": "glm-5.1",
          "name": "GLM-5.1",
          "reasoning": true,
          "input": ["text"],
          "contextWindow": 200000,
          "maxTokens": 131072
        }
      ]
    }
  }
}
```

Do **not** add a GLM-5.2-style `thinkingLevelMap` to GLM-5.1 unless Z.ai updates
its documentation and a provider-response probe confirms distinct effort levels.

## Validation notes

Artifacts from the 2026-06-28 validation:

- `analysis/pi-zai-51-5v-request-shape-probe.jsonl` — local mock proof that Pi
  sends only `thinking.type` for GLM-5.1; no `reasoning_effort` is emitted for
  off/low/high/xhigh under current Pi metadata.
- `analysis/zai-glm51-5v-probe.jsonl` — direct Z.ai coding-endpoint probe.

Important caveat: the direct coding-endpoint probe requested `model: "glm-5.1"`
but Z.ai returned `response_model: "glm-5.2"` for the local account. That proves
thinking-on/off mechanics on the endpoint, but it does **not** prove we reached a
distinct GLM-5.1 backend. Before using GLM-5.1 as a benchmark condition where the
model identity matters, run a fresh provider-response smoke and verify the
returned model id and usage fields.

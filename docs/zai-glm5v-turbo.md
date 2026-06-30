# Z.ai GLM-5V-Turbo interaction modes

This note is the project reference for configuring direct Z.ai GLM-5V-Turbo calls
in benchmark configs. GLM-5V-Turbo is a vision-language model, not a drop-in text
worker for ordinary benchmark roles.

Primary Z.ai docs:

- GLM-5V-Turbo guide: <https://docs.z.ai/guides/vlm/glm-5v-turbo>
- Chat completion API: <https://docs.z.ai/api-reference/llm/chat-completion>
- Thinking mode: <https://docs.z.ai/guides/capabilities/thinking-mode>
- Deep thinking: <https://docs.z.ai/guides/capabilities/thinking>
- Core parameters: <https://docs.z.ai/guides/overview/concept-param>
- Model overview: <https://docs.z.ai/guides/overview/overview>

## Model role

Z.ai describes GLM-5V-Turbo as a multimodal coding foundation model for
vision-based coding and agent workflows.

Documented capabilities and limits:

| Property | Value |
| --- | --- |
| Input modality | Video / Image / Text / File |
| Output modality | Text |
| Context length | 200K |
| Maximum output tokens | 128K / 131072 |
| Typical use | screenshots, GUI agents, frontend recreation, visual grounding, visual debugging |

Pi's built-in `zai/glm-5v-turbo` metadata currently says:

```json
{
  "id": "glm-5v-turbo",
  "provider": "zai",
  "input": ["text", "image"],
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

Pi currently exposes text and image input for this model. The Z.ai guide also
mentions video and file inputs, but those are not proven through Pi's current
OpenAI-compatible converter in this repo; validate before use.

## Request shape

Z.ai examples use OpenAI-style multimodal message content:

```json
{
  "model": "glm-5v-turbo",
  "messages": [
    {
      "role": "user",
      "content": [
        {
          "type": "image_url",
          "image_url": { "url": "https://example.com/screenshot.png" }
        },
        {
          "type": "text",
          "text": "Describe the UI issue in this screenshot."
        }
      ]
    }
  ],
  "thinking": { "type": "enabled" }
}
```

Pi converts internal image blocks to data URLs:

```json
{
  "type": "image_url",
  "image_url": {
    "url": "data:image/png;base64,..."
  }
}
```

## Thinking and reasoning levels

GLM-5V-Turbo supports deep thinking via the same `thinking` object:

```json
{
  "thinking": { "type": "enabled" }
}
```

- `thinking.type`: `enabled` or `disabled`.
- Z.ai documents GLM-5V-Turbo as a deep-thinking model.
- The GLM-5V-Turbo guide examples include `thinking`, but do **not** include
  `reasoning_effort`.
- Z.ai's parameter docs say `reasoning_effort` is only supported by GLM-5.2 and
  above. Do not assume GLM-5V-Turbo has low/high/xhigh effort controls.

Pi mapping under current built-in metadata:

| Pi thinking level | Z.ai request effect |
| --- | --- |
| `off` | `thinking: {"type":"disabled"}` and no `reasoning_effort` |
| `low` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `medium` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `high` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |
| `xhigh` | `thinking: {"type":"enabled"}` and no `reasoning_effort` |

Therefore, for GLM-5V-Turbo, benchmark conditions should be named as
**thinking off** vs **thinking enabled**, not low/high/xhigh. Use it only when the
role actually benefits from visual input unless the user explicitly asks for a
text-only VLM comparison.

## Config rules

Prefer Pi's built-in direct ZAI model entry when possible:

```text
zai/glm-5v-turbo
```

If a benchmark config must define a custom direct-ZAI `models.json` leaf for
GLM-5V-Turbo, it should match the provider docs and Pi behavior:

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
          "id": "glm-5v-turbo",
          "name": "GLM-5V-Turbo",
          "reasoning": true,
          "input": ["text", "image"],
          "contextWindow": 200000,
          "maxTokens": 131072
        }
      ]
    }
  }
}
```

Do **not** add GLM-5.2-style `reasoning_effort` support or a `thinkingLevelMap`
unless Z.ai updates its documentation and a provider-response probe confirms the
model honors distinct effort levels.

## Validation notes

Artifacts from the 2026-06-28 validation:

- `analysis/pi-zai-51-5v-request-shape-probe.jsonl` — local mock proof that Pi
  sends `thinking.type` for GLM-5V-Turbo text and image requests and does not
  emit `reasoning_effort` for low/high/xhigh under current Pi metadata. It also
  confirms Pi serializes image blocks as `image_url` data URLs.
- `analysis/zai-glm51-5v-probe.jsonl` — direct Z.ai coding-endpoint probe.

Important caveat: the local Z.ai account currently cannot call GLM-5V-Turbo. The
direct probe returned HTTP 429 with code `1311` and message:

```text
Your current subscription plan does not yet include access to GLM-5V-Turbo
```

So we have validated Pi's request shape and Z.ai documentation, but not a
successful GLM-5V-Turbo provider response under the current account. Before any
benchmark use, run a one-call provider-response smoke that verifies:

1. access is enabled for `glm-5v-turbo`,
2. image input is accepted if the benchmark role uses vision,
3. streamed `delta.reasoning_content` or non-stream `message.reasoning_content`
   appears when thinking is enabled on a reasoning-worthy prompt,
4. `usage.completion_tokens_details.reasoning_tokens` behaves as expected, and
5. no unsupported `reasoning_effort` parameter is being sent.

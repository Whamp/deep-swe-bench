# observational-memory-glm52-high

Observational-memory config for GPT-5.5-low executor experiments where the OM
observer/reflector/dropper worker is direct ZAI `glm-5.2` with Pi
thinking `high`.

The leaf `models.json` uses corrected GLM-5.2 metadata:

- `supportsReasoningEffort: true`
- `thinkingFormat: "zai"`
- `thinkingLevelMap.high: "high"`
- `thinkingLevelMap.xhigh: "max"`

Therefore this config should send Z.ai:

```json
{"thinking":{"type":"enabled"},"reasoning_effort":"high"}
```

The smoke contract validates the configuration before fan-out by checking:

- main executor session records: `openai-codex/gpt-5.5` with Pi thinking `low`
- result metadata: OM worker provider `zai`, model `glm-5.2`, thinking `high`
- loaded `models.json`: `$ZAI_API_KEY`, `thinkingFormat: "zai"`, and
  `supportsReasoningEffort: true`
- worker trace: OM worker API `openai-completions`, provider `zai`, model
  `glm-5.2`, thinkingLevel `high`, and at least one assistant usage event
- no OpenRouter worker trace and no OM `model_unavailable` event

Do not confuse this with historical stale configs named
`observational-memory-glm52-low/high/xhigh`, which omitted `reasoning_effort` and
were consolidated into `observational-memory-glm52-max`.

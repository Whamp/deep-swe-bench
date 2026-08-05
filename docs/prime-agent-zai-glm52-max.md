# Prime Agent 0.7.0 with direct Z.ai GLM-5.2 max thinking

This note fixes the provider and thinking contract for the
`prime-agent@1.0.0` benchmark config.

## Sources

- Prime Agent repository: <https://github.com/PrimeIntellect-ai/prime-agent>
- Prime Agent provider setup: <https://github.com/PrimeIntellect-ai/prime-agent/blob/main/packages/coding-agent/docs/providers.md>
- Z.ai GLM-5.2 guide: <https://docs.z.ai/guides/llm/glm-5.2>
- Z.ai chat completions API: <https://docs.z.ai/api-reference/llm/chat-completion>
- Project Z.ai reference and live probes: [`zai-glm52-thinking.md`](zai-glm52-thinking.md)

## Runtime identity

The subject is `prime-agent@0.7.0`, installed from Prime Intellect's versioned
release tarball:

```text
https://pub-728493de92a943e2a9b2d17b4719f318.r2.dev/releases/v0.7.0/prime-agent-0.7.0.tgz
```

The config uses Prime Agent's built-in `zai/glm-5.2` catalog entry. That entry
uses the OpenAI-compatible chat-completions API at:

```text
https://api.z.ai/api/coding/paas/v4
```

The model has a 1,000,000-token context window, a 131,072-token output limit,
and ZAI tool streaming support. `ZAI_API_KEY` is the only credential route.

## Max-thinking request shape

The runner passes all three explicit selections:

```text
--provider zai --model glm-5.2 --thinking max
```

Prime Agent 0.7.0's bundled ZAI adapter sends this request shape:

```json
{
  "enable_thinking": true,
  "reasoning_effort": null
}
```

Z.ai documents omitted `reasoning_effort` as `max` when thinking is enabled.
Therefore this path reaches the provider's strongest documented effort, but the
wire proof is **enabled thinking plus provider-default max**, not a literal
`"reasoning_effort":"max"` field.

The local request-shape probe used Prime Agent 0.7.0's bundled model catalog and
provider adapter against a localhost SSE server. It made no provider call:

- `analysis/prime_agent_zai_glm52_max_request_probe.mjs`
- `analysis/prime-agent-zai-glm52-max-request-probe.jsonl`

The provider-response probes in the project Z.ai reference exercised the same
coding endpoint and captured reasoning content and reasoning-token usage:

- `analysis/zai-glm52-reasoning-probe-coding-endpoint.jsonl`
- `analysis/zai-glm52-streaming-probe.jsonl`

## RLM and usage accounting

Prime Agent's shipped RLM maximum depth is one. The root may create direct
children; those children cannot create grandchildren. Child model selection
inherits direct `zai/glm-5.2` and max thinking from the root.

Prime Agent persists root assistant usage in `session/*.jsonl`. It also appends
one `child_usage_attributed` record for each completed child. The harness reads
those attribution records into `recursive_child_*` result fields. It does not
persist the raw RPC event stream.

The config declares two model roles:

1. `executor`: one root session, billed to Z.ai subscription quota.
2. `rlm-child`: inherited direct Z.ai GLM-5.2 max calls, billed to the same
   subscription quota and accounted from `child_usage_attributed` records.

Prime Agent 0.7.0 exposes no native total-child or live-child concurrency
setting. The benchmark runner therefore sends every ZAI call through a local
pass-through guard. Each cell admits at most 64 provider requests and runs at
most eight simultaneously. Request 65 receives HTTP 429 and the result records
that the limit was reached. The guard writes status and usage only; it does not
persist prompts, streamed text, tool calls, or responses.

The 64-request budget covers the root agent, RLM children, compaction, retries,
and auto-refine together. RLM children can consume at most 63 requests because
the root must make at least one. The normal subject timeout and container
resource policy remain additional outer boundaries.

## Config rules

The config keeps Prime Agent's shipped behavior except for explicit identity
pins:

- `defaultProvider: "zai"`
- `defaultModel: "glm-5.2"`
- `defaultThinkingLevel: "max"`
- `rlmMaxDepth: 1`

It leaves built-in skills, IPython, compaction, auto-refine, retries, and
non-autonomous execution at their shipped defaults. It adds no prompt text,
custom skills, custom model, autonomous continuation, or persistent goal. A
runtime-only provider override changes the built-in ZAI base URL to the local
pass-through guard; the guard forwards to the built-in coding endpoint.

Do not infer behavior from the operator's `~/.prime/agent/settings.json`; the
runner mounts an isolated per-rep config directory. Do not describe this path as
OpenRouter, metered API billing, literal `reasoning_effort: max`, or recursive
depth greater than one.

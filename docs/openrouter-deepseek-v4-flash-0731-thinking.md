# OpenRouter DeepSeek V4 Flash 0731 thinking

This note records the OpenRouter provider path for the stock Pi `baseline` config run
against `deepseek/deepseek-v4-flash-0731`. It exists to produce a clean API-level
token and correctness baseline that isolates provider/host from the matching local
llama.cpp run documented in
[`local-llamacpp-deepseek-v4-flash-0731-thinking.md`](./local-llamacpp-deepseek-v4-flash-0731-thinking.md)
(served from server60 at `max` thinking).

## Model and endpoint

- OpenRouter slug: `deepseek/deepseek-v4-flash-0731`
- Canonical slug: `deepseek/deepseek-v4-flash-20260731`
- HuggingFace id: `deepseek-ai/DeepSeek-V4-Flash-0731` (matches the local run exactly)
- Provider/API: `openrouter`, OpenAI-compatible chat completions
- Endpoint pinned: DeepSeek's own `deepseek/fp8` endpoint (fp8 quantization, 1M context,
  384K max completion, supports `reasoning`, `reasoning_effort`, `tools`)
- Billing: paid API. DeepSeek endpoint pricing $0.14 / $0.28 per M (input / output);
  the cross-endpoint floor is $0.09 / $0.18 per M.
- Credential route: `OPENROUTER_API_KEY` (the standing pre-approved
  `openrouter/deepseek/deepseek-v4-flash` route; this leaf uses the dated 0731 slug).

### Slug trap

The harness default model arg `openrouter/deepseek/deepseek-v4-flash` is a **generic
alias** whose `canonical_slug` resolves to `deepseek/deepseek-v4-flash-20260423` (the
**0423** version), not 0731. This config passes the explicit dated slug
`openrouter/deepseek/deepseek-v4-flash-0731` so the request reaches the 0731 weights.
See `analysis/openrouter-deepseek-v4-flash-0731-models-probe.json`.

## Thinking level map and the leaf override

pi-ai's shipped `openrouter.json` entry for `deepseek/deepseek-v4-flash-0731` declares:

```json
"thinkingLevelMap": { "minimal": null, "low": null, "medium": null, "high": "high", "max": null, "xhigh": "xhigh" }
```

A `null` value means **"this level is not natively mapped," not "send no reasoning."**
pi-ai's `clampThinkingLevel` resolves an unmapped request to the nearest supported
level, so with the shipped map:

- `--thinking max` → not supported → clamps to `xhigh` → Pi sends `reasoning.effort: "xhigh"`
- `--thinking high` → sends `reasoning.effort: "high"`
- `--thinking low` → not supported → clamps **up** to `high` → sends `reasoning.effort: "high"`

`"xhigh"` is a Pi/OpenRouter-level label, not a DeepSeek-native effort. DeepSeek's own
thinking mode exposes `low | high | max` (default `high`), and the local llama.cpp run
sends `reasoning_effort: "max"`. To make the API baseline send the same DeepSeek-native
effort as the local run, the leaf `models.json` applies a `modelOverrides` entry
(`provider-composer.js` merges `thinkingLevelMap` per-key as the topmost config layer):

```json
"thinkingLevelMap": { "low": "low", "high": "high", "xhigh": "max", "max": "max" }
```

With the override applied:

- `--thinking max` → sends `reasoning.effort: "max"` (matches local)
- `--thinking high` → sends `reasoning.effort: "high"`
- `--thinking low` → sends `reasoning.effort: "low"`

The override is provider-routing/model-compat metadata, not config-authored prompt
text; the `baseline` config remains stock Pi with no preamble, orchestration file, or
appended prompt. See
`analysis/openrouter-deepseek-v4-flash-0731-pi-request-probe.jsonl` for the mocked
request-shape proof of both the shipped and overridden behavior (no live generation).

## Provider routing

OpenRouter serves this model through 23 endpoints with widely varying quantization
(DeepInfra/Sail/Ionstream/Ambient at fp4; many at fp8; some unknown). A clean
local-vs-API comparison must use DeepSeek's own serving, so the leaf `models.json`
pins `compat.openRouterRouting` to the `deepseek` provider with `allow_fallbacks: false`
and `quantizations: ["fp8"]`. Fallbacks are intentionally disabled so a non-deepseek
provider (e.g. a lossier fp4 endpoint) cannot silently serve a rep and contaminate the
baseline. Re-enable fallbacks only as an explicit decision that trades baseline purity
for availability.

## Sampling

The official 0731 model card ran its coding-agent evaluation at `temperature=1.0`,
`top_p=0.95`, and the local llama.cpp run pins exactly that tuple. The DeepSeek
OpenRouter endpoint accepts `temperature` and `top_p` (but not `top_k`/
`min_p`/`repetition_penalty`). To make the API baseline sample identically to
the local run, the leaf `models.json` sets `samplingParams: { temperature: 1.0,
top_p: 0.95 }` on the model via `modelOverrides`.

Honoring `model.samplingParams` requires pi 0.84.0; pi 0.83.0's pi-ai does not
merge model-level sampling params into the request. This leaf therefore pins the
subject at `pi@0.84.0` (`harness/Dockerfile.pi-agent` `PI_VERSION=0.84.0`, image
rev `v4-pi0840-tools`). The mocked request-shape probe confirms the override
sends `reasoning.effort: "max"`, `temperature: 1`, `top_p: 0.95`; without the
override, sampling is unset (model defaults) and `max` resolves to `xhigh`.

## Max completion tokens

The DeepSeek endpoint advertises 384K max completion tokens; pi-ai pins the model's
`maxTokens` at 65536. Pi's request uses the model's `maxTokens` for `max_tokens`. This
is sufficient for benchmark reps and bounds per-call cost.

## Usage accounting

Main-executor usage comes only from native `session/*.jsonl` assistant `message.usage`
records, per project rules. No raw `--mode json` stream is persisted. OpenRouter also
returns per-provider usage in its response; the native session record is the single
source of truth for result accounting.

## Evidence

- `analysis/openrouter-deepseek-v4-flash-0731-models-probe.json` — live OpenRouter model
  record (slug, canonical, HF id, pricing, supported parameters) and the 23 endpoints,
  highlighting the selected `deepseek/fp8` endpoint with uptime/latency/throughput.
- `analysis/openrouter-deepseek-v4-flash-0731-pi-request-probe.jsonl` — mocked Pi
  request-shape proof (shipped map vs. leaf override) showing what `reasoning.effort`
  Pi sends for `max`/`high`/`low`. No live model generation.
- The confirmed benchmark preflight is the first live end-to-end Pi agent call. It must
  leave positive native-session usage, RPC lifecycle evidence, a `max` thinking session
  record, and an outgoing request with `model: deepseek/deepseek-v4-flash-0731` and
  `reasoning.effort: "max"` before the remaining cells start.

## Primary sources

- https://openrouter.ai/deepseek/deepseek-v4-flash-0731
- https://openrouter.ai/docs/api/reference/parameters (`reasoning.effort` enum:
  `max`, `xhigh`, `high`, `medium`, `low`, `minimal`, `none`)
- https://api-docs.deepseek.com/guides/thinking_mode/ (DeepSeek native
  `reasoning_effort: low | high | max`)
- https://modelparams.dev/parameters/reasoning_effort (DeepSeek-V4 Flash range
  `high | max`, default `high`)
- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731

## Config rules

Use `configs/baseline-openrouter-deepseek-v4-flash-0731@1.0.0/deepseek-v4-flash-0731/max/`. The config has no
system preamble, orchestration file, or appended prompt. Do not substitute the
generic `deepseek/deepseek-v4-flash` slug (it resolves to 0423), change the
thinking-level map away from DeepSeek-native `{low, high, max}`, drop the
`samplingParams` temperature/top_p pin, enable provider fallbacks, or increase
the model `maxTokens` without publishing a new leaf and revalidating the
provider path. The subject must be `pi@0.84.0` for `samplingParams` to take
effect.

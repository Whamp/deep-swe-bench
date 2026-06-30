# OpenAI Codex subscription thinking levels

This note is the project reference for using OpenAI Codex subscription models via
Pi's `openai-codex` provider in benchmark configs.

Validated on 2026-06-28 from three sources:

1. Official OpenAI API documentation for reasoning models and model pages.
2. Pi's `openai-codex` request-shape behavior.
3. Tiny live calls through Will's subscription auth in `~/.pi/agent/auth.json`.

## Provider/API path

Pi routes these models through:

```text
provider: openai-codex
api: openai-codex-responses
baseUrl: https://chatgpt.com/backend-api
endpoint: /codex/responses
transport: SSE or websocket via Pi; validation used SSE
```

Pi docs identify OpenAI Codex as the ChatGPT Plus/Pro subscription provider.
Auth is OAuth stored in `~/.pi/agent/auth.json`, not `OPENAI_API_KEY`.

## Official OpenAI API docs

Fetched 2026-06-28:

- `https://platform.openai.com/docs/guides/reasoning?api-mode=responses`
- `https://developers.openai.com/api/docs/models/gpt-5.5`
- `https://developers.openai.com/api/docs/models/gpt-5.4`
- `https://developers.openai.com/api/docs/models/gpt-5.4-mini`

OpenAI documents reasoning models as working best with the Responses API and
using a `reasoning.effort` parameter. Supported values are model-dependent and
can include `none`, `minimal`, `low`, `medium`, `high`, and `xhigh`.

The relevant model pages state:

| OpenAI model page | documented `reasoning.effort` support | documented default |
| --- | --- | --- |
| `gpt-5.5` | `none`, `low`, `medium`, `high`, `xhigh` | `medium` |
| `gpt-5.4` | `none`, `low`, `medium`, `high`, `xhigh` | `none` |
| `gpt-5.4-mini` | `none`, `low`, `medium`, `high`, `xhigh` | `none` |

Important: the official docs list `none`, not `off`. `off` is Pi vocabulary.
Whether Pi's `off` is equivalent to documented `none` depends on the request
payload Pi sends.

## Models checked in Pi

`pi --list-models` and Pi's `ModelRegistry` show all three are available in the
current subscription:

| Pi model | Pi context | Pi max output | input | reasoning |
| --- | ---: | ---: | --- | --- |
| `openai-codex/gpt-5.5` | 272K | 128K | text, image | yes |
| `openai-codex/gpt-5.4` | 272K | 128K | text, image | yes |
| `openai-codex/gpt-5.4-mini` | 272K | 128K | text, image | yes |

All three use the same Pi metadata shape:

```json
{
  "api": "openai-codex-responses",
  "baseUrl": "https://chatgpt.com/backend-api",
  "reasoning": true,
  "thinkingLevelMap": {
    "minimal": "low",
    "xhigh": "xhigh"
  }
}
```

## Effective Pi thinking levels

Pi's generic supported levels are:

```text
off, minimal, low, medium, high, xhigh
```

For these three Codex models, Pi treats all six as available. The model-level map
has two special cases:

- `minimal` is sent to the provider as effort `low`.
- `xhigh` is explicitly enabled and sent as effort `xhigh`.

`low`, `medium`, and `high` are not remapped; they are sent literally.
`off` sends no `reasoning` object.

That last point is critical: Pi's `off` currently means **omit the reasoning
object**, not **send documented OpenAI `reasoning.effort: "none"`**.

Expected Pi request shape:

| requested Pi thinking | request `reasoning` |
| --- | --- |
| `off` | omitted |
| `minimal` | `{ "effort": "low", "summary": "auto" }` |
| `low` | `{ "effort": "low", "summary": "auto" }` |
| `medium` | `{ "effort": "medium", "summary": "auto" }` |
| `high` | `{ "effort": "high", "summary": "auto" }` |
| `xhigh` | `{ "effort": "xhigh", "summary": "auto" }` |

Therefore `minimal` and `low` are not distinct provider-effort conditions
through Pi for these models.

Because official OpenAI defaults differ by model, Pi `off` must be interpreted
carefully:

| Pi model | Pi `off` request | official default when `reasoning` is omitted | interpretation |
| --- | --- | --- | --- |
| `openai-codex/gpt-5.5` | omit `reasoning` | `medium` | **not a documented no-reasoning condition**; likely default-medium unless the ChatGPT backend differs |
| `openai-codex/gpt-5.4` | omit `reasoning` | `none` | likely equivalent to documented no-reasoning |
| `openai-codex/gpt-5.4-mini` | omit `reasoning` | `none` | likely equivalent to documented no-reasoning |

A controlled live probe confirmed that omission is **not** equivalent to
`none` for `gpt-5.5` on the ChatGPT/Codex subscription backend. With the same
prompt over 3 reps:

| case | request `reasoning` | reasoning tokens |
| --- | --- | --- |
| Pi `off` / omitted | omitted | 724, 442, 435 |
| explicit OpenAI `none` | `{ "effort": "none", "summary": "auto" }` | 0, 0, 0 |
| explicit `low` | `{ "effort": "low", "summary": "auto" }` | 396, 376, 579 |
| explicit `medium` | `{ "effort": "medium", "summary": "auto" }` | 561, 410, 445 |

Artifact:

```text
analysis/openai-codex-gpt55-off-none-controlled-probe.jsonl
```

A matching controlled probe for `gpt-5.4` and `gpt-5.4-mini` confirmed their
provider-documented defaults: omitted reasoning and explicit `none` both used
zero reasoning tokens, while `low` and `xhigh` used nonzero reasoning tokens.

| model | omitted reasoning tokens | explicit `none` reasoning tokens | `low` reasoning tokens | `xhigh` reasoning tokens |
| --- | --- | --- | --- | --- |
| `gpt-5.4` | 0, 0, 0 | 0, 0, 0 | 426, 472, 516 | 952, 1251, 2021 |
| `gpt-5.4-mini` | 0, 0, 0 | 0, 0, 0 | 448, 516, 510 | 2921, 3588, 1203 |

Artifact:

```text
analysis/openai-codex-gpt54-off-none-controlled-probe.jsonl
```

Therefore Pi `off` for `openai-codex/gpt-5.5` is a default-reasoning condition,
not a no-reasoning condition. A true no-reasoning `gpt-5.5` condition requires
sending `reasoning: { "effort": "none" }`, which current Pi `--thinking off` /
`streamSimple(... reasoning: "off")` does not do. For benchmark configs that
need true Codex observer-off behavior, load an explicit request-mutation
extension and smoke-test its runtime audit file.

The meaningful benchmark choices through current Pi are:

- `gpt-5.5`: `low`, `medium`, `high`, `xhigh`; avoid interpreting `off` as true
  no-reasoning.
- `gpt-5.4` / `gpt-5.4-mini`: `off`/default-none, `low`, `medium`, `high`,
  `xhigh`; skip `minimal` because it aliases `low`.

## Request-shape validation

Artifact:

```text
analysis/openai-codex-thinking-request-probe.jsonl
```

Method: local mock `/codex/responses` server, fake OAuth JWT with a test account
id, Pi's real `openai-codex-responses` adapter, no provider tokens spent.

Result: for `gpt-5.5`, `gpt-5.4`, and `gpt-5.4-mini`, Pi sent exactly the
request shapes listed above.

## Live subscription validation

Artifact:

```text
analysis/openai-codex-thinking-live-probe.jsonl
```

Method: tiny live Codex subscription calls for each model × level with the prompt
"Reply OK", SSE transport, and current `openai-codex` OAuth auth.

All 18 combinations succeeded:

| model | off | minimal | low | medium | high | xhigh |
| --- | --- | --- | --- | --- | --- | --- |
| `gpt-5.5` | ok | ok | ok | ok | ok | ok |
| `gpt-5.4` | ok | ok | ok | ok | ok | ok |
| `gpt-5.4-mini` | ok | ok | ok | ok | ok | ok |

The live probe confirms these Pi levels are accepted by the current subscription
path. It does **not** prove qualitative monotonicity or that token counts from a
one-word prompt represent benchmark behavior. The controlled omit-vs-none probe
above proves Pi `off` for `gpt-5.5` does **not** mean OpenAI's documented
`reasoning.effort: "none"`.

## Config rules

- Use provider `openai-codex`, not OpenRouter, unless the user explicitly asks
  for OpenRouter.
- For benchmark launch confirmations, list exact role/model/thinking level, e.g.
  `openai-codex/gpt-5.4-mini` with thinking `low`.
- Treat `minimal` as an alias of provider effort `low` for these models.
- Do not label raw `openai-codex/gpt-5.5` thinking `off` as true no-reasoning. A
  controlled provider-response probe showed omitted reasoning still used
  reasoning tokens, while explicit `reasoning.effort: "none"` used zero.
- Codex observer-off benchmark configs should force explicit
  `reasoning.effort: "none"` and include a smoke contract requiring a runtime
  request-audit record with `codex_reasoning_forced_none` and
  `"reasoning":{"effort":"none"...}`.
- For `pi-observational-memory` observer/reflector/dropper workers, do not assume
  a normal config-level `before_provider_request` hook sees worker requests. OM
  workers call `agentLoop` directly, so request mutation/audit must be placed in
  the worker request path that actually runs (for example the worker config's
  `onPayload`) unless a smoke artifact proves otherwise.
- Smoke contracts must require the copied result artifact path, not an arbitrary
  in-container path. `harness/run.py` copies `/root/.pi/agent/observational-memory`
  to `pi-agent/observational-memory`, so OM Codex-off runtime audits should live
  under a preserved path such as
  `pi-agent/observational-memory/codex-thinking/requests.ndjson`.
- If a config's smoke test depends on Codex thinking behavior, include repo-level
  smoke checks requiring this doc and the two probe artifacts above.

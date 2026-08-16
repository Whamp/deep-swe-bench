# OpenAI Codex GPT-5.6 Luna thinking validation

Validated 2026-07-31 for benchmark configs using Pi `0.83.0` and
`openai-codex/gpt-5.6-luna`. The low route was revalidated with a local mock on
Pi `0.84.1` for the read-long-lines pilot on 2026-08-10, and the high route was
revalidated with a local mock on Pi `0.84.1` for `pi-fff@1.0.0` on 2026-08-16.

## Official model contract

OpenAI describes GPT-5.6 Luna as the cost-sensitive, high-volume member of the
GPT-5.6 family. The API model supports text and image input, text output,
reasoning tokens, streaming, function calling, the Responses API, a 1,050,000
model context window, and 128,000 maximum output tokens.

GPT-5.6 accepts reasoning efforts `none`, `low`, `medium`, `high`, `xhigh`, and
`max`. OpenAI recommends reserving `max` for difficult quality-first work and
comparing it with lower efforts on representative tasks.

Primary sources:

- <https://developers.openai.com/api/docs/models/gpt-5.6-luna>
- <https://developers.openai.com/api/docs/guides/latest-model>

## Pi and Codex route

Pi `0.83.0` resolves this benchmark route as:

| Field | Effective value |
| --- | --- |
| Provider | `openai-codex` |
| Model | `gpt-5.6-luna` |
| API adapter | `openai-codex-responses` |
| Billing | Codex OAuth subscription quota |
| Pi context window | 272,000 tokens |
| Pi maximum output | 128,000 tokens |
| Thinking levels under test | `low`, `high`, `max` |

The benchmark uses Pi's effective 272,000-token context limit, not the larger
public API limit. This avoids claiming context that the tested Codex route does
not expose.

The isolated registry artifact is
[`analysis/openai-codex-gpt56-luna/model-registry.json`](../analysis/openai-codex-gpt56-luna/model-registry.json).
It disables model-network refresh and custom `models.json` loading, so the
record reflects the pinned Pi package.

## Request-shape validation

The local mock-endpoint probe exercises Pi's real Codex Responses adapter with
one tool present. For each requested level, Pi preserved the level and sent the
matching `reasoning.effort`:

| Requested | Clamped | Sent `reasoning.effort` |
| --- | --- | --- |
| `low` | `low` | `low` |
| `high` | `high` | `high` |
| `max` | `max` | `max` |

Artifacts:

- [`analysis/openai-codex-gpt56-luna/low/request-probe.jsonl`](../analysis/openai-codex-gpt56-luna/low/request-probe.jsonl)
- [`analysis/openai-codex-gpt56-luna/high/request-probe.jsonl`](../analysis/openai-codex-gpt56-luna/high/request-probe.jsonl)
- [`analysis/openai-codex-gpt56-luna/max/request-probe.jsonl`](../analysis/openai-codex-gpt56-luna/max/request-probe.jsonl)
- Reproducer: [`analysis/openai-codex-gpt56-luna/request-probe.mjs`](../analysis/openai-codex-gpt56-luna/request-probe.mjs)

## Live validation

Three approved minimal calls reached the live Codex endpoint through Pi
`0.83.0`. All returned `OK` with `stopReason: "stop"`; each used 31 total tokens.
The records contain compact final usage only, not raw per-event streams.

Artifacts:

- [`analysis/openai-codex-gpt56-luna/low/live-probe.jsonl`](../analysis/openai-codex-gpt56-luna/low/live-probe.jsonl)
- [`analysis/openai-codex-gpt56-luna/high/live-probe.jsonl`](../analysis/openai-codex-gpt56-luna/high/live-probe.jsonl)
- [`analysis/openai-codex-gpt56-luna/max/live-probe.jsonl`](../analysis/openai-codex-gpt56-luna/max/live-probe.jsonl)
- Reproducer: [`analysis/openai-codex-gpt56-luna/live-probe.mjs`](../analysis/openai-codex-gpt56-luna/live-probe.mjs)

## Pi 0.84.1 pilot revalidation

`analysis/read-long-lines-pilot/provider-evidence/request-probe.jsonl` exercises
Pi `0.84.1`'s real Codex Responses adapter against a local mock. The low record
preserves `low` and sends `reasoning: {"effort":"low","summary":"auto"}` with
one tool.

`analysis/openai-codex-gpt56-luna/high/request-probe-pi-0.84.1.jsonl` performs
the same provider-free check for the `pi-fff@1.0.0` high leaf. It preserves
`high` and sends `reasoning: {"effort":"high","summary":"auto"}` with one
tool. No provider call was made for either Pi `0.84.1` revalidation.

The existing Pi `0.83.0` live probe proves the subscription route accepted
Luna. Each confirmed Pi `0.84.1` config preflight must prove its end-to-end route
before fan-out.

## Benchmark implication

The route is validated for `baseline@1.0.0` and `pi-check@1.0.1` comparisons
at `low`, `high`, and `max`. Each config leaf must pin its thinking level,
assert the native
session's `thinking_level_change` record, and assert captured provider requests
contain `model: "gpt-5.6-luna"` with the matching `reasoning.effort`.

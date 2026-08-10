# OpenAI Codex GPT-5.6-SOL thinking levels

This note validates `openai-codex/gpt-5.6-sol` at Pi thinking `low`, `medium`,
and `high` for DeepSWE benchmark configs.

Validated on 2026-07-23 against official OpenAI documentation, Pi model
metadata and request behavior, and tiny live calls through Will's Codex
subscription OAuth. The low route was revalidated locally on Pi `0.84.1` for
the read-long-lines pilot on 2026-08-10.

## Provider/API path

The benchmark uses:

```text
provider: openai-codex
model: gpt-5.6-sol
api: openai-codex-responses
baseUrl: https://chatgpt.com/backend-api
thinking: low | medium | high
```

OAuth comes from the `openai-codex` entry in `~/.pi/agent/auth.json` and is
copied into task containers with `--pass-openai-codex-oauth`.

## Official model semantics

OpenAI's model page identifies `gpt-5.6-sol` as the frontier GPT-5.6 model and
states that the `gpt-5.6` alias routes to it:

- <https://developers.openai.com/api/docs/models/gpt-5.6-sol>

OpenAI's GPT-5.6 model guidance says to use the Responses API and documents
`reasoning.effort` values `none`, `low`, `medium`, `high`, `xhigh`, and `max`.
It documents `medium` as the default when effort is omitted:

- <https://developers.openai.com/api/docs/guides/latest-model>

The benchmark still sends each requested effort explicitly. Model availability
or an accepted Pi CLI flag alone is not sufficient evidence.

## Required Pi version

Pi `0.80.2`, previously pinned in `harness/Dockerfile.pi-agent`, does not list
`gpt-5.6-sol`. Pi `0.81.1` first established this repository's provider,
thinking, and usage evidence for the model. Those historical artifacts remain
valid evidence for the earlier results that recorded Pi `0.81.1`.

The pi-fabric PR #10 refresh uses Pi `0.83.0`, matching the candidate package's
pinned Pi AI and development dependencies. The benchmark image and
`PI_IMAGE_REV` are pinned to `0.83.0`, so Pi `0.81.1` task images cannot be
reused. The candidate preflight must capture the live Pi `0.83.0` request shape
and native session usage before fan-out.

The read-long-lines pilot uses the repository's Pi `0.84.1` image. Its local
mock record in
`analysis/read-long-lines-pilot/provider-evidence/request-probe.jsonl` confirms
that Sol remains available and sends explicit `reasoning.effort: "low"` with
one tool. The pilot preflight must independently prove that Pi `0.84.1` reaches
the live Codex subscription route before its fan-out.

Artifacts:

```text
analysis/openai-codex-gpt56-sol-model-registry.json
analysis/pi-fabric-pr10-0da479f-package-validation.json
docs/pi-fabric-pr10-0da479f-validation.md
```

## Request-shape probes

The historical Pi `0.81.1` `before_provider_request` captures recorded these
request fields:

```json
{"model":"gpt-5.6-sol","reasoning":{"effort":"low","summary":"auto"},"stream":true,"store":false}
{"model":"gpt-5.6-sol","reasoning":{"effort":"medium","summary":"auto"},"stream":true,"store":false}
{"model":"gpt-5.6-sol","reasoning":{"effort":"high","summary":"auto"},"stream":true,"store":false}
```

Artifacts:

```text
analysis/openai-codex-gpt56-sol-low-request-probe.jsonl
analysis/openai-codex-gpt56-sol-medium-request-probe.jsonl
analysis/openai-codex-gpt56-sol-high-request-probe.jsonl
```

These captures prove Pi maps each setting to the corresponding explicit
provider effort. In particular, the low condition does not omit reasoning and
silently take the documented medium default. The Pi `0.84.1` pilot record
reproduces the same low payload shape.

## Live subscription probes

Tiny non-tool calls through the live `openai-codex` subscription path returned
the expected markers with stop reason `stop` and no provider error:

| Thinking | Expected and observed marker | Artifact |
| --- | --- | --- |
| `low` | `OK` | `analysis/openai-codex-gpt56-sol-low-live-probe.jsonl` |
| `medium` | `GPT56_SOL_MEDIUM_PROBE_OK` | `analysis/openai-codex-gpt56-sol-medium-live-probe.jsonl` |
| `high` | `GPT56_SOL_HIGH_PROBE_OK` | `analysis/openai-codex-gpt56-sol-high-live-probe.jsonl` |

Reasoning-token counts on trivial prompts do not define the configured effort.
The request artifacts prove the provider conditions; the live artifacts prove
those paths are accepted by the subscription backend.

## Usage shape

Pi's compact JSON events and native session records report input, output, cache
read, cache write, and total token usage for these calls. Main executor usage in
benchmark results must continue to come from native `session/*.jsonl` records,
not persisted raw `--mode json` streams.

## Config and smoke requirements

Each config needs a leaf at `gpt-5.6-sol/<thinking>/` containing:

- `settings.json` with `defaultThinkingLevel` set to that leaf's thinking level;
- a leaf-local `smoke.json` requiring model, thinking, exact subject version,
  request-shape, and native session evidence;
- session evidence containing the exact `"thinkingLevel":"<thinking>"` value;
- captured provider-request evidence containing the matching explicit effort.

Launches must use `openai-codex/gpt-5.6-sol`, the matching `--thinking` value,
and the declared `OPENAI_CODEX_OAUTH` credential route. A Pi `0.83.0` launch
must not claim compatibility from the older Pi `0.81.1` version alone; its
preflight supplies the live version-specific request and usage evidence.

## Stale patterns to avoid

- Do not use Pi `0.80.2`; it lacks this model registry entry.
- Do not infer thinking semantics from `pi --list-models` or CLI acceptance.
- Do not omit effort for a `medium` benchmark merely because the provider's
  documented default is medium; the benchmark requires explicit evidence.
- Do not reuse low-thinking smoke evidence for medium or high leaves.

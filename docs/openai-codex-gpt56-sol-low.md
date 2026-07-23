# OpenAI Codex GPT-5.6-SOL low thinking

This note validates `openai-codex/gpt-5.6-sol` at Pi thinking `low` for
DeepSWE benchmark configs.

Validated on 2026-07-23 against official OpenAI documentation, Pi model
metadata and request behavior, and a tiny live call through Will's Codex
subscription OAuth.

## Provider/API path

The benchmark uses:

```text
provider: openai-codex
model: gpt-5.6-sol
api: openai-codex-responses
baseUrl: https://chatgpt.com/backend-api
thinking: low
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

Therefore this config must send explicit effort `low`; model availability or an
accepted Pi CLI flag alone is not sufficient evidence.

## Required Pi version

Pi `0.80.2`, previously pinned in `harness/Dockerfile.pi-agent`, does not list
`gpt-5.6-sol`. Pi `0.81.1` does list it under `openai-codex` with reasoning
support. The benchmark image is pinned to `0.81.1`, and `PI_IMAGE_REV` includes
that version so existing per-task images cannot be reused accidentally.

Artifact:

```text
analysis/openai-codex-gpt56-sol-model-registry.json
```

## Request-shape probe

A Pi `0.81.1` `before_provider_request` capture for
`openai-codex/gpt-5.6-sol` at thinking `low` recorded:

```json
{"model":"gpt-5.6-sol","reasoning":{"effort":"low","summary":"auto"},"stream":true,"store":false}
```

Artifact:

```text
analysis/openai-codex-gpt56-sol-low-request-probe.jsonl
```

This proves Pi maps its `low` setting to the provider's explicit low-effort
condition rather than omitting reasoning and taking the documented medium
default.

## Live subscription probe

A tiny non-tool call through the live `openai-codex` subscription path used the
prompt `Reply exactly OK.` The response was `OK`, with stop reason `stop` and no
provider error.

Artifact:

```text
analysis/openai-codex-gpt56-sol-low-live-probe.jsonl
```

The tiny response reported zero reasoning tokens. That does not contradict the
request capture: low effort permits the model to use little or no reasoning on
a trivial prompt. The request artifact, not token count on this prompt, proves
the configured effort.

## Config and smoke requirements

Each config needs a leaf at `gpt-5.6-sol/low/` containing:

- `settings.json` with `defaultThinkingLevel` set to `low`;
- a leaf-local `smoke.json` requiring model, thinking, Pi-version, request-probe,
  and live-probe evidence;
- session evidence containing `"thinkingLevel":"low"`.

Launches must use `openai-codex/gpt-5.6-sol`, `--thinking low`, and
`--pass-openai-codex-oauth`.

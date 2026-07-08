# OMP GPT-5.5 low baseline validation

Status: validated 2026-07-04 for a DeepSWE baseline config using `omp` v16.3.5.

## Purpose

This note validates using `omp` (Oh My Pi) as the benchmark executor while keeping the run as close as possible to the Pi baseline:

- same DeepSWE task container and verifier harness,
- historical runs used the then-global `harness/system_preamble.md` plus `configs/baseline-omp/orchestration.md`; current harness behavior no longer applies a global preamble unless a config carries `system_preamble.md`,
- same executor model family: OpenAI Codex subscription `gpt-5.5`,
- same requested thinking level: `low`,
- no skills, no extensions, and no OMP rules,
- only basic code-editing/discovery tools enabled.

The intended config is `configs/baseline-omp` and the intended model argument is explicit:

```text
--model openai-codex/gpt-5.5 --thinking low
```

Do **not** use bare `--model gpt-5.5` for this benchmark. A tiny probe with a filtered auth profile showed OMP can fuzzy-select another provider (Azure) for the bare name. The benchmark must use the explicit provider-qualified model id.

## Provider/API path

OMP model catalog output for the explicit model is stored at:

```text
analysis/omp-gpt55-low-probes/model-catalog.txt
```

It identifies:

```text
provider: openai-codex
model: gpt-5.5
thinking: low, medium, high, xhigh
context: 272K
max-out: 128K
```

Live OMP session metadata from the tiny RPC probe is stored at:

```text
analysis/omp-gpt55-low-probes/tiny-session-summary.json
analysis/omp-gpt55-low-probes/session/*.jsonl
analysis/omp-gpt55-low-probes/tiny-rpc-runner.jsonl
```

The session records show:

```json
{"type":"model_change","model":"openai-codex/gpt-5.5"}
{"type":"thinking_level_change","thinkingLevel":"low"}
```

The assistant message used:

```json
{"api":"openai-codex-responses","provider":"openai-codex","model":"gpt-5.5"}
```

with nonzero usage.

## Official OpenAI reasoning docs

Official OpenAI reasoning/model behavior for GPT-5.5 is documented in the existing project note:

```text
docs/openai-codex-thinking.md
```

That note cites the official OpenAI Responses reasoning guide and GPT-5.5 model page. It records that GPT-5.5 supports `none`, `low`, `medium`, `high`, and `xhigh`, with `medium` as the documented default when reasoning is omitted.

This OMP config uses `low`, not `off`, so it avoids the Pi-specific off/none ambiguity documented there.

## Runtime request/response proof

OMP is distributed here as a standalone binary, not as project source. The available runtime proof is therefore the OMP catalog plus live OMP session metadata and usage, not a local source-level request-shape mock like the Pi adapter probes.

The live probe command used a filtered OMP auth DB containing only the `openai-codex` OAuth credential and ran:

```text
omp --mode rpc --model openai-codex/gpt-5.5 --thinking low \
  --no-skills --no-extensions --no-rules \
  --tools=read,bash,edit,write,grep,glob --no-lsp --no-pty \
  --approval-mode yolo
```

The RPC runner reached quiescence after `agent_end`, and the session produced the exact requested final text plus nonzero usage.

## Container availability and credential path

The benchmark container does not install OMP into the image. The OMP harness mounts the host standalone binary read-only into the task container:

```text
-v $(command -v omp):/usr/local/bin/omp:ro
```

The auth path is intentionally OMP-specific and filtered. The harness builds a temporary SQLite `agent.db` containing only the `openai-codex` row from `~/.omp/agent/agent.db`, mounts that temporary directory at `/root/.omp/agent`, and sets:

```text
PI_CODING_AGENT_DIR=/root/.omp/agent
```

A Docker proof using a real DeepSWE task image is stored at:

```text
analysis/omp-gpt55-low-probes/docker-omp-proof.txt
```

It shows `omp/16.3.5` runs in the task image and can list `openai-codex/gpt-5.5` with low/medium/high/xhigh thinking using the filtered auth DB.

## Tool and prompt isolation rules

The baseline OMP command must include:

```text
--no-skills --no-extensions --no-rules
--tools=read,bash,edit,write,grep,glob --no-lsp --no-pty
--append-system-prompt <config-local prompt layers when present>
```

Rationale:

- `--no-skills` satisfies the no-skills requirement.
- `--no-extensions` prevents OMP profile extensions from leaking into the run.
- `--no-rules` prevents OMP rules/managed instructions from adding prompt content beyond the benchmark prompt.
- The limited tool list avoids browser/web/subagent/notebook/Python/LSP tools that were not part of the plain Pi baseline comparison.
- OMP still has its own built-in tool descriptions and default agent prompt; that is the unavoidable agent/harness difference.

## Smoke contract expectations

The config smoke contract should verify:

- `result.json` has `agent == "omp"`, `model == "openai-codex/gpt-5.5"`, `thinking_level == "low"`, and nonzero token usage.
- `logs/pi-rpc-runner.jsonl` contains `prompt_sent`, `quiescent`, `transport":"rpc`, and `reason":"agent_end`.
- `session/*.jsonl` contains the model/thinking metadata and assistant `provider":"openai-codex","model":"gpt-5.5`.
- `logs/omp-version.txt` contains `omp/16.3.5`.
- No skills/extensions/rules are present in config files.

## Stale patterns to avoid

- Do not use bare `gpt-5.5`; use `openai-codex/gpt-5.5`.
- Do not mount the full host `~/.omp/agent` into containers. Use the filtered temporary auth DB.
- Do not leave OMP default skills/extensions/rules discovery enabled.
- Do not enable OMP browser/web/task subagent tools for this baseline.

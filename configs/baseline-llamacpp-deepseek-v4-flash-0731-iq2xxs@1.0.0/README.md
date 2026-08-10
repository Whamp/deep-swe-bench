# baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.0.0

Local llama.cpp baseline for **DeepSeek V4 Flash 0731** running on server60 as
an **Antirez IQ2_XXS** quantized GGUF (2-bit weights, q8_0 KV cache, fast
prefill), served at `http://100.92.238.117:8033/v1`.

Purpose: a local-quant comparison point against the OpenRouter API fp8 baseline
(`baseline-openrouter-deepseek-v4-flash-0731@1.0.0`) to quantify quantization
effects on quality and token verbosity on the 12_v2 subset.

## Key facts

- **Served model id:** `deepseek-v4-flash-0731-q8-fast-prefill` (the `q8` is the
  KV cache; weights are IQ2_XXS).
- **Context:** 430,080 tokens. **Parallel slots:** 1 → benchmark concurrency 1.
- **Completion cap:** 65,536 tokens, matching captured OpenRouter API baseline requests.
- **Reasoning:** `chat_template_kwargs.enable_thinking` + `reasoning_effort`
  (`low`/`high`/`max`); key is `enable_thinking`, not the older `thinking`.
- **Sampling:** agentic profile `temperature 1.0 / top_p 0.95` (+ disabled
  `top_k`/`min_p`/`repeat_penalty`), per the official DeepSeek-V4-Flash-0731
  model card, pinned by the request extension. Matches the API baseline.
- **Subject:** `pi@0.84.0`, matching the completed OpenRouter API baseline.
- **Cost:** all-zero (local compute).

## Extensions

Both loaded via `pi-flags`:

- `extensions/local-llamacpp-deepseek-v4-request.ts` — pins the agentic sampling
  profile into every provider request (overrides the server's non-agentic
  defaults).
- `extensions/local-llamacpp-deepseek-v4-bash-timeout.ts` — injects a 360s
  default `timeout` on `bash` tool calls when the model omits one, so a forgotten
  timeout can't permanently block the agent (the agentworld/gemma-4/thinking-cap
  failure mode). Audited to `/out/llamacpp-deepseek-v4-bash-timeout.ndjson`.

This config contains **no config-authored prompt text** (no system preamble,
orchestration, or `--append-system-prompt`).

## Leaves

Each thinking level is its own leaf under
`deepseek-v4-flash-0731-q8-fast-prefill/{low,high,max}/` with its own
`settings.json` (`defaultThinkingLevel`), `models.json`, `smoke.json`, and
`config-lock.json`. `thinkingLevelMap` maps `low→low`, `high→high`, `max→max`.

## Evidence

See `docs/llamacpp-deepseek-v4-flash-0731-q8-thinking.md` and the
`analysis/llamacpp-deepseek-v4-flash-0731-q8-*` artifacts.

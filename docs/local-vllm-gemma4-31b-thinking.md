# Local vLLM Gemma 4 31B thinking control

This note records the provider path for the clean Pi baseline
`baseline-gemma4-31b@1.0.0`.

## Model and endpoint

- Source checkpoint: `google/gemma-4-31B-it-qat-w4a16-ct`
- Served aliases: `gemma-4-31b` and `gemma-4-31b-google-qat-w4a16`
- Endpoint: `http://100.92.238.117:8034/v1`
- Provider/API: `local-vllm`, OpenAI-compatible chat completions
- vLLM: `0.25.1`
- Context window: 262,144 tokens
- Billing: local compute
- Credential route: `LOCAL_VLLM_API_KEY=local`; the server does not require a secret

The live service uses four RTX 3090 GPUs, Google QAT W4A16 weights, BF16 KV,
and the official Gemma assistant draft model with two speculative tokens. It
advertises at most two concurrent sequences, matching the requested two-worker
run.

## Thinking and tools

Official Gemma documentation enables thinking with
`enable_thinking=true` in the chat-template arguments. Pi's `high` thinking
level maps to:

```json
{"chat_template_kwargs":{"enable_thinking":true}}
```

The server's canonical Google chat template also accepts
`preserve_thinking=true`. The baseline sets it because Gemma's documentation
requires retaining thought content within a multi-step function-calling turn.
The server uses vLLM's `gemma4` reasoning and tool-call parsers with automatic
tool choice enabled.

The server pins the checkpoint's sampling profile: `temperature=1.0`,
`top_p=0.95`, `top_k=64`, `min_p=0.0`, and `repetition_penalty=1.0`. The config
repeats those values in the outgoing request so Pi cannot silently replace the
server defaults.

## Evidence

- `analysis/local-vllm-gemma4-31b-models-probe.json` records the live aliases,
  checkpoint path, vLLM ownership, and 262,144-token limit.
- `analysis/local-vllm-gemma4-31b-pi-request-probe.jsonl` proves Pi sends
  `enable_thinking=true` for `high` and does not send `reasoning_effort`.
- `analysis/local-vllm-gemma4-31b-tokenize-probe.json` proves the live server
  accepts the model alias, thinking arguments, preservation argument, and a
  function schema through its chat template without generating tokens.
- `analysis/local-vllm-gemma4-31b-server-gate.json` pins the server repository
  commit and source-file hashes behind its existing chat, reasoning, streaming
  tool-call, long-context, and soak validation. The server reports 80/80
  streamed two-tool calls and 100/100 soak responses with no errors.

The confirmed benchmark preflight remains the first end-to-end Pi agent call.
It must leave a native session with standard OpenAI-compatible usage fields,
structured tool activity, an outgoing request containing the pinned thinking
and sampling fields, and no model-unavailable or structural tool errors before
the remaining jobs start.

## Official sources

- https://ai.google.dev/gemma/docs/core/model_card_4
- https://ai.google.dev/gemma/docs/capabilities/thinking
- https://ai.google.dev/gemma/docs/capabilities/text/function-calling-gemma4
- https://huggingface.co/google/gemma-4-31B-it-qat-w4a16-ct
- https://docs.vllm.ai/projects/recipes/en/stable/Google/Gemma4.html
- https://docs.vllm.ai/en/latest/api/vllm/tool_parsers/gemma4_tool_parser/

## Config rules

Use `configs/baseline-gemma4-31b@1.0.0/gemma-4-31b/high/`. The config has no
system preamble, orchestration file, or appended prompt. Do not substitute the
Qwen thinking format, send `reasoning_effort`, or remove thought preservation
from tool-call turns.

# Local vLLM Ornith 1.0 35B thinking control

This note records the provider path for the stock Pi baseline
`baseline-ornith-35b@1.0.0`.

## Model and endpoint

- Source checkpoint: `deepreinforce-ai/Ornith-1.0-35B`
- Local quantization: cyankiwi asymmetric AWQ INT4 group-size 32
- Served aliases: `ornith-1.0-35b` and `ornith-1.0-35b-awq-int4`
- Endpoint: `http://100.92.238.117:8082/v1`
- Provider/API: `local-vllm`, OpenAI-compatible chat completions
- vLLM: `0.25.1`
- Context window: 262,144 tokens
- Billing: local compute
- Credential route: `LOCAL_VLLM_API_KEY=local`; the server does not require a secret

The live profile uses two RTX 3090 GPUs with tensor parallelism 2, FP8 KV,
and `max_num_seqs=4`, matching the requested four-worker run. The server
profile is marked experimental: chat, reasoning separation, ordinary and
streamed tools, and vision passed its existing gate, while stress, benchmark,
and soak were intentionally deferred to this benchmark.

## Thinking and tools

Ornith is a reasoning model. Its official model card says assistant turns open
with a thinking block by default and recommends vLLM's `qwen3` reasoning parser
plus `qwen3_xml` tool-call parser. The live server uses exactly those parsers and
defaults `enable_thinking=true`.

Pi's `high` thinking level maps to:

```json
{"chat_template_kwargs":{"enable_thinking":true,"preserve_thinking":true}}
```

The mocked Pi request probe confirms those fields and confirms that Pi does not
send `reasoning_effort`. Here `high` is the supported binary thinking-on switch,
not a provider-side graded effort level. The checkpoint chat template itself
renders prior `reasoning_content` on assistant tool turns; the config therefore
does not add a Qwen/Gemma thought-preservation extension.

The live profile pins `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0`,
and `repetition_penalty=1.0`. The config repeats those values in outgoing
requests so Pi cannot silently replace the server profile.

## Evidence

- `analysis/local-vllm-ornith-35b-models-probe.json` records the live aliases,
  checkpoint path, vLLM ownership, and context limit.
- `analysis/local-vllm-ornith-35b-pi-request-probe.jsonl` proves Pi's high
  request shape against a mock OpenAI-compatible endpoint without generating.
- `analysis/local-vllm-ornith-35b-tokenize-probe.json` proves the live endpoint
  accepts tools and distinct thinking-on/off chat-template arguments without
  generating tokens, and proves benchmark-container reachability.
- `analysis/local-vllm-ornith-35b-server-gate.json` pins the live image, server
  source, checkpoint/template hashes, runtime arguments, and existing server
  validation status.

The confirmed benchmark preflight remains the first end-to-end Pi agent call.
It must leave a native session with positive usage, RPC lifecycle evidence, and
an outgoing request containing the approved model, thinking, and sampling
fields before the remaining 35 cells start.

## Official sources

- https://huggingface.co/deepreinforce-ai/Ornith-1.0-35B
- https://github.com/deepreinforce-ai/Ornith-1
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/

## Config rules

Use `configs/baseline-ornith-35b@1.0.0/ornith-1.0-35b/high/`. The config has no
system preamble, orchestration file, or appended prompt. Do not send
`reasoning_effort`, substitute another tool parser, disable thinking, or replace
the live profile's sampling tuple without publishing a new config release.

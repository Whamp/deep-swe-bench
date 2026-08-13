# Local vLLM DeepSeek V4 Flash 0731 WNA16 on server60 port 8034

This note records the provider, reasoning, tool-calling, usage, and runtime path
for `baseline-vllm-deepseek-v4-flash-0731-wna16@1.0.0`.

## Model and endpoint

- Artifact: `hampsonw/DeepSeek-V4-Flash-0731-WNA16`, immutable snapshot
  `75d9286c37f3037f3ab390cfbc10747466eac714`.
- Served model: `deepseek-v4-flash-0731-wna16`.
- Endpoint: `http://100.92.238.117:8034/v1`.
- Provider/API: `local-vllm`, OpenAI-compatible chat completions.
- Image: `club-3090/deepseek-v4-wna16-sm86:aeb62948-rope-cu130` pinned by
  digest in `analysis/deepseek-v4-wna16-concurrency/server-gate.json`.
- Context window: 215,000 tokens per request.
- Maximum output: 65,536 tokens.
- Billing: local compute.
- Credential route: `LOCAL_VLLM_API_KEY=local`; the endpoint accepts this
  non-secret placeholder.

The active server uses four RTX 3090 GPUs, tensor parallelism 4,
`max_num_seqs=4`, FP8 DeepSeek MLA KV cache, chunked prefill, automatic tool
choice, and the `deepseek_v4` reasoning and tool parsers. Startup logs report
233,817 aggregate GPU KV-cache tokens. Four sequences are schedulable, but four
full 215,000-token contexts cannot coexist.

## Reasoning and request shape

Pi 0.84.1 is the tested subject. The model maps Pi `max` directly to the
OpenAI-compatible top-level request field:

```json
{
  "reasoning_effort": "max",
  "max_tokens": 65536,
  "temperature": 1.0,
  "top_p": 0.95
}
```

The config uses `thinkingFormat: "openai"` rather than DeepSeek's legacy
`thinking: {"type":"enabled"}` shape. Pi's mocked request probe proves that
only the accepted top-level `reasoning_effort` field is emitted. The live probe
accepted max reasoning and returned reasoning text plus a JSON-decodable tool
call.

Pi is configured to replay `reasoning_content` on assistant messages when the
provider requires it. This is the OpenAI-compatible DeepSeek continuation
contract used by Pi's provider adapter.

## Sampling, tools, and usage

DeepSeek's agentic recommendation is temperature 1.0 and top-p 0.95. A
`before_provider_request` extension pins those two values without adding prompt
text or forcing tool choice. The server has `--enable-auto-tool-choice` and the
`deepseek_v4` tool parser.

Executor usage comes from native `session/*.jsonl` assistant `message.usage`
records. The live endpoint returned positive `prompt_tokens`,
`completion_tokens`, and `total_tokens`. No secondary model roles exist.

The bash-timeout extension defaults omitted bash timeouts to 360 seconds,
preserves model-selected values, and writes compact audit evidence to
`local-vllm-deepseek-v4-wna16-bash-timeout.ndjson`.

## Evidence artifacts

- `analysis/deepseek-v4-wna16-concurrency/server-gate.json` records the served
  model, image, command, tailnet-only binding, scheduler limit, KV type and
  capacity, and idle metrics.
- `analysis/deepseek-v4-wna16-concurrency/pi-request-probe.jsonl` records Pi's
  final request shape against a mock endpoint without generation.
- `analysis/deepseek-v4-wna16-concurrency/live-provider-probe.json` records the
  approved live max-reasoning and tool-call probe.

## Official sources

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
- https://docs.vllm.ai/en/latest/design/metrics/

## Config rules

Use
`configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.0.0/deepseek-v4-flash-0731-wna16/max/`.
Do not substitute the llama.cpp IQ2_XXS endpoint, change the reasoning level,
output cap, sampling pair, parser, or server scheduler limits under this release.
Do not add config-authored prompt text. A concurrency comparison must use the
same tasks and config for both conditions, disable harness preflight, reset the
server between conditions, and record server metrics around each run.

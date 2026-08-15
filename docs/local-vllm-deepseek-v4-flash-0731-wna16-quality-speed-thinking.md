# Local vLLM DeepSeek V4 WNA16 quality artifact on speed runtime

This note records the provider, thinking, tool-calling, usage, and runtime path
for `baseline-vllm-deepseek-v4-flash-0731-wna16@1.2.0`.

## Model and endpoint

- Artifact: `hampsonw/DeepSeek-V4-Flash-0731-WNA16` revision
  `12035985bf555d0ddc603c6305586a8fa915589c`.
- Served model: `deepseek-v4-flash-0731-wna16-quality-12035985`.
- Endpoint: `http://100.92.238.117:8034/v1`.
- Provider/API: `local-vllm`, OpenAI-compatible chat completions.
- Runtime image:
  `sha256:eb2884fc60ee332d7adb9d5e424e35acf8817dad0f93c8bb7ea7095cb8f58a0e`.
- Canonical runtime commit: `b7766cfe4d15d9b68acea43097ceff221e8a739f`.
- Context window: 230,144 tokens.
- Maximum output: 65,536 tokens.
- Billing: local compute.
- Credential route: `LOCAL_VLLM_API_KEY`; the endpoint accepts a non-secret
  placeholder.

The server uses four RTX 3090 GPUs, tensor parallelism 4, `max_num_seqs=2`,
277,675 GPU KV-cache tokens, 16 GiB CPU KV offload, FP8 DeepSeek MLA KV,
chunked prefill, automatic tool choice, and the `deepseek_v4` reasoning and tool
parsers. At the full 230,144-token request limit the GPU KV pool provides 1.21×
concurrency, so two deep trajectories may rely on offload or scheduling.

## Thinking and request shape

Pi 0.84.1 is the tested subject. Pi `max` sends:

```json
{
  "reasoning_effort": "max",
  "max_tokens": 65536,
  "temperature": 1.0,
  "top_p": 0.95
}
```

The config uses `thinkingFormat: "openai"` and replays `reasoning_content` on
assistant messages. The model-free Pi probe confirms the final request shape.
The same artifact/model identity passed a prior live provider probe with
reasoning, positive usage, and a JSON-decodable automatic tool call. Because the
runtime image changed, release 1.2.0 requires a new atomic benchmark preflight
before batch fan-out.

## Sampling, tools, and usage

The request extension pins temperature 1.0 and top-p 0.95 without adding prompt
text or forcing tool choice. The bash-timeout extension defaults omitted bash
timeouts to 360 seconds, preserves model-selected values, and writes compact
audit evidence. Executor usage comes from native `session/*.jsonl`; no secondary
model roles exist.

## Evidence

- `analysis/deepseek-v4-wna16-quality-12035985-speed-b7766cfe/server-gate.json`
- `analysis/deepseek-v4-wna16-quality-12035985-speed-b7766cfe/pi-request-probe.jsonl`
- `analysis/deepseek-v4-wna16-quality-12035985/live-provider-probe.json`

## Sources

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731
- https://huggingface.co/hampsonw/DeepSeek-V4-Flash-0731-WNA16/tree/12035985bf555d0ddc603c6305586a8fa915589c
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/

## Config rule

Use
`configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.2.0/deepseek-v4-flash-0731-wna16-quality-12035985/max/`.
Do not change the artifact revision, runtime image, model ID, context, thinking,
output cap, sampling pair, parser, or executor concurrency under this release.
Do not add config-authored prompt text.

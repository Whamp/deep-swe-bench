# Local vLLM DeepSeek V4 WNA16 quality candidate

This note records the provider, thinking, tool-calling, usage, and runtime path
for `baseline-vllm-deepseek-v4-flash-0731-wna16@1.1.0`.

## Model and endpoint

- Repository: `hampsonw/DeepSeek-V4-Flash-0731-WNA16`.
- Immutable artifact revision:
  `12035985bf555d0ddc603c6305586a8fa915589c`.
- Served model: `deepseek-v4-flash-0731-wna16-quality-12035985`.
- Endpoint: `http://100.92.238.117:8034/v1`.
- Provider/API: `local-vllm`, OpenAI-compatible chat completions.
- Runtime image:
  `sha256:7c943f434ec9f901c391d7bab00623534da101d628e428f44215ea10585efe94`.
- Runtime source: Whamp/vLLM commit
  `a7758f7436a713f042e245b3e0aaab64b3a2f2c6`.
- Context window: 131,072 tokens.
- Maximum output: 65,536 tokens.
- Billing: local compute.
- Credential route: `LOCAL_VLLM_API_KEY`; the local endpoint accepts a
  non-secret placeholder.

The runtime commit descends from the artifact's declared mixed-group integration
commit `dd2d1fd6779addccc73094f77fa4ada7d9106a41`. It additionally forwards
DeepSeek V4's SwiGLU alpha, beta, and clamp values into Humming and fixes the
fused-MoE group-axis convention. The candidate keeps down projections at W2
_group-128 except W4 group-128 on layers 26 and 37–42. Gate/up use W2 with
layer-specific group sizes 128, 256, or 512.

The server uses four RTX 3090 GPUs, tensor parallelism 4, `max_num_seqs=4`, FP8
DeepSeek MLA KV cache, chunked prefill, automatic tool choice, and the
`deepseek_v4` reasoning and tool parsers. The DeepSWE gate itself uses one
worker and one rep.

## Thinking and request shape

Pi 0.84.1 is the tested subject. Pi `max` maps to the OpenAI-compatible request
fields below:

```json
{
  "reasoning_effort": "max",
  "max_tokens": 65536,
  "temperature": 1.0,
  "top_p": 0.95
}
```

The config uses `thinkingFormat: "openai"` and replays
`reasoning_content` on assistant messages when required. The model-free Pi
probe confirms the final request shape. The live probe returned reasoning,
positive usage, and a JSON-decodable automatic tool call with
`finish_reason: "tool_calls"`.

## Sampling, tools, and usage

The request extension pins temperature 1.0 and top-p 0.95 without adding prompt
text or forcing tool choice. The bash-timeout extension defaults omitted bash
timeouts to 360 seconds, preserves model-selected values, and writes compact
audit evidence to `local-vllm-deepseek-v4-wna16-bash-timeout.ndjson`.

Executor usage comes from native `session/*.jsonl` assistant usage records. No
secondary model roles exist.

## Evidence

- `analysis/deepseek-v4-wna16-quality-12035985/server-gate.json`
- `analysis/deepseek-v4-wna16-quality-12035985/pi-request-probe.jsonl`
- `analysis/deepseek-v4-wna16-quality-12035985/live-provider-probe.json`
- `analysis/deepseek-v4-wna16-quality-12035985/runtime-dispatch.log`

## Sources

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731
- https://huggingface.co/hampsonw/DeepSeek-V4-Flash-0731-WNA16/tree/12035985bf555d0ddc603c6305586a8fa915589c
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/

## Config rule

Use
`configs/baseline-vllm-deepseek-v4-flash-0731-wna16@1.1.0/deepseek-v4-flash-0731-wna16-quality-12035985/max/`.
Do not change the artifact revision, runtime image, model ID, max thinking,
output cap, sampling pair, parser, context limit, or worker count under this
release. Do not add config-authored prompt text.

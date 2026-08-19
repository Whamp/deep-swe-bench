# Local vLLM DeepSeek V4 native GGUF-TP

This note records the provider, thinking, tool-calling, usage, and runtime path for `baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0`.

## Model and endpoint

- Source weights: Antirez `DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix-0731.gguf`, SHA-256 `ca22ae2f838e14077c22bc1c1417b71b45b5e5a3687bd96c2ac6e17fdb6261c0`.
- Served model: `deepseek-v4-flash-0731-gguf-tp`.
- Endpoint: `http://100.92.238.117:8034/v1`.
- Provider/API: `local-vllm`, OpenAI-compatible chat completions.
- Runtime image: `sha256:f91e8283e7ad116b8664b4a936dba88ebafcb8910a968dce2a3c34420f010adf`.
- Whamp/vLLM commit: `3ec20cebe` over the DSML/SwiGLU/FlashMLA/hierarchical-all-reduce speed stack.
- Context window: 148,000 tokens (post-acceptance production gate; live runtime reports `max_model_len` 148000).
- Maximum output: 65,536 tokens.
- Billing: local compute.
- Credential route: `LOCAL_VLLM_API_KEY`; the endpoint accepts a non-secret placeholder.

The server uses four RTX 3090 GPUs with tensor parallelism 4, `max_num_seqs=2`, 154,519 GPU KV-cache tokens (acceptance-gate figure), FP8 DeepSeek MLA KV, chunked prefill, automatic tool choice, and the `deepseek_v4` reasoning/tool parsers. It passed exact needle retrieval at 119,730 prompt tokens. This is the post-acceptance production baseline; the live gate observed on 2026-08-19 reports `max_model_len` 148000, and the acceptance profile retained only 71–73 MiB idle VRAM after long-context execution.

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

The config uses `thinkingFormat: "openai"` and replays `reasoning_content` on assistant messages. The model-free Pi probe confirms this request shape. Live probes returned a JSON-decodable automatic tool call and a coherent post-tool continuation with positive usage.

## Sampling, tools, and usage

The request extension pins temperature 1.0 and top-p 0.95. It adds no prompt text and does not force tool choice. The bash-timeout extension defaults omitted bash timeouts to 360 seconds, preserves explicit values, and writes compact audit evidence. Executor usage comes from native `session/*.jsonl`; no secondary model roles exist.

## Evidence

- `analysis/deepseek-v4-gguf-tp-3ec20ceb/server-gate.json`
- `analysis/deepseek-v4-gguf-tp-3ec20ceb/pi-request-probe.jsonl`
- `analysis/deepseek-v4-gguf-tp-3ec20ceb/live-tool-probe.json`
- `analysis/deepseek-v4-gguf-tp-3ec20ceb/live-post-tool-probe.json`

## Sources

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731
- https://huggingface.co/antirez/DeepSeek-V4-Flash-IQ2XXS-w2Q2K-AProjQ8-SExpQ8-OutQ8-chat-v2-imatrix-0731-GGUF
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/

## Config rule

Use `configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max/`. Do not change the GGUF, image, runtime commit, model ID, context, thinking, output cap, sampling pair, parser, or executor concurrency under this release. Do not add config-authored prompt text.

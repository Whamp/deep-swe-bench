# Local llama.cpp DeepSeek V4 Flash 0731 max thinking

This note records the provider path for the stock Pi baseline
`baseline-deepseek-v4-flash-0731@1.0.0`.

## Model and endpoint

- Source release: `deepseek-ai/DeepSeek-V4-Flash-0731`
- GGUF repository: `antirez/deepseek-v4-gguf` revision
  `88e011c80d9ec39458f5493ddacab57364143960`
- Quantization: 86,720,111,488-byte IQ2_XXS 2.0625 bpw GGUF with Q2_K routed
  expert down projections and Q8 attention/shared-expert/output projections
- Served alias: `deepseek-v4-flash-0731`
- Endpoint: `http://100.92.238.117:8200/v1`
- Provider/API: `local-llamacpp`, OpenAI-compatible chat completions
- llama.cpp: build `b10200-5f55650a7`
- Runtime context: 200,192 tokens; the source model was trained for a larger context
- Billing: local compute
- Credential route: `LOCAL_LLAMACPP_API_KEY=local`; the server does not require a secret

The live profile runs across four RTX 3090 GPUs and exposes one inference slot.
Benchmark concurrency must therefore remain one unless the server profile changes.

## Max thinking and tools

The official 0731 model card says its coding-agent evaluation used `max` reasoning
with `temperature=1.0` and `top_p=0.95`. The official DeepSeek thinking guide
exposes `low`, `high`, and `max` effort for OpenAI-compatible chat completions.

Pi 0.83.0 supports a native `max` thinking level. This config maps it to the
custom llama.cpp chat template through:

```json
{
  "chat_template_kwargs": {
    "thinking": true,
    "reasoning_effort": "max"
  }
}
```

The generic Pi `chat-template` compatibility path produces these values from
`thinking.enabled` and `thinking.effort`; no config-authored reasoning prompt is
added. The server's custom Jinja template owns the max-effort prefix and DSML
function-tool rendering. The config pins the serving profile's full sampling
tuple: `temperature=1.0`, `top_p=0.95`, `top_k=0`, `min_p=0.0`, and
`repeat_penalty=1.0`.

A non-generating `/apply-template` probe proved that the live template renders
its max-effort prefix, thinking start marker, system and user messages, and a
function-tool schema. A mocked Pi request proved the config emits the intended
chat-template kwargs and sampling fields. No live model generation or tool loop
was used while preparing this config.

## Evidence

- `analysis/local-llamacpp-deepseek-v4-flash-0731-models-probe.json` records the
  live alias, runtime context, parameter count, and quantization metadata.
- `analysis/local-llamacpp-deepseek-v4-flash-0731-pi-request-probe.jsonl` proves
  Pi's max request shape against a mock OpenAI-compatible endpoint.
- `analysis/local-llamacpp-deepseek-v4-flash-0731-template-probe.json` proves the
  live server renders max thinking and function tools without generating.
- `analysis/local-llamacpp-deepseek-v4-flash-0731-server-gate.json` pins the
  runtime image/build, checkpoint identity, custom template, serving command,
  context, slot count, and sampling defaults.
- `analysis/pi-0.83.0-max-thinking-image-probe.json` proves the representative
  DeepSWE subject image runs Pi 0.83.0 and exposes the `max` thinking type.

The confirmed benchmark preflight remains the first end-to-end Pi agent call.
It must leave positive native-session usage, RPC lifecycle evidence, a max
thinking session record, and an outgoing request with the approved model,
chat-template kwargs, and sampling fields before the remaining cells start.

## Primary sources

- https://huggingface.co/deepseek-ai/DeepSeek-V4-Flash-0731
- https://api-docs.deepseek.com/guides/thinking_mode/
- https://huggingface.co/antirez/deepseek-v4-gguf/tree/88e011c80d9ec39458f5493ddacab57364143960
- https://github.com/ggml-org/llama.cpp/tree/5f55650a78f92aff4d48d671423e888fac0469ff

## Config rules

Use
`configs/baseline-deepseek-v4-flash-0731@1.0.0/deepseek-v4-flash-0731/max/`.
The config has no system preamble, orchestration file, or appended prompt. Do
not substitute `xhigh`, change the custom template, alter the quantization,
change the sampling tuple, or increase concurrency without publishing a new
config release and revalidating the provider path.

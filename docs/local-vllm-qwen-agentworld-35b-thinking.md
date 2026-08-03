# Local vLLM Qwen-AgentWorld 35B thinking control

This note records the provider path for the Pi baseline
`baseline-qwen-agentworld-35b@1.0.0`.

## Model and endpoint

- Source checkpoint: `Qwen/Qwen-AgentWorld-35B-A3B`
- Local checkpoint: AWQ INT4 through `compressed-tensors`
- Served model: `qwen-agentworld-35b-a3b`
- Endpoint: `http://100.92.238.117:8080/v1`
- Provider/API: `local-vllm`, OpenAI-compatible chat completions
- vLLM: `0.25.1`
- Context window: 262,144 tokens
- Billing: local compute
- Credential route: `LOCAL_VLLM_API_KEY=local`; the server does not require a
  secret

The live profile uses two RTX 3090 GPUs, tensor parallelism 2, FP8 KV cache,
and `max_num_seqs=4`. That concurrency matches the requested four-worker run.
The server launches the checkpoint with `--language-model-only`, as Qwen
requires for this text-only checkpoint.

## Model purpose

Qwen describes AgentWorld as a language world model trained to predict an
environment's next state. The official card reports agent-transfer results but
does not present the model as a general coding assistant. This benchmark
intentionally tests it as Pi's coding executor without adding AgentWorld's
domain-specific simulation prompt.

## Thinking, output, and tools

The official card says the model uses thinking by default. The server uses
vLLM's `qwen3` reasoning parser and defaults `enable_thinking=true`. Pi's `high`
thinking level maps to binary thinking-on control rather than a provider-side
graded reasoning effort.

The model leaf sets `maxTokens` to 65,536. Qwen recommends 32,768 output tokens
for most AgentWorld requests; the operator approved the larger ceiling for this
DeepSWE run. The config sends no `reasoning_effort`.

The checkpoint chat template accepts `preserve_thinking`. The model-specific
provider hook forces:

```json
{
  "chat_template_kwargs": {
    "enable_thinking": true,
    "preserve_thinking": true
  }
}
```

The mocked Pi request probe confirms the final provider payload contains both
fields and `max_tokens=65536`. The live `/tokenize` endpoint accepts the same
chat-template arguments with a tool schema. The confirmed preflight must still
prove an end-to-end Pi tool turn and capture the outgoing request before batch
fan-out.

Qwen's official model card recommends `temperature=0.6`, `top_p=0.95`, and
`top_k=20`. The live checkpoint's `generation_config.json` matches those values,
and the server adds `min_p=0.0` and `repetition_penalty=1.0`. The config pins the
full live tuple so Pi cannot replace it.

## Evidence

- `analysis/local-vllm-qwen-agentworld-35b-models-probe.json` records the live
  model id, checkpoint path, vLLM ownership, and context limit.
- `analysis/local-vllm-qwen-agentworld-35b-pi-request-probe.jsonl` proves Pi's
  high-thinking request shape against a mock endpoint without generating.
- `analysis/local-vllm-qwen-agentworld-35b-tokenize-probe.json` proves the live
  endpoint accepts tools, thinking, and `preserve_thinking` without generating
  tokens.
- `analysis/local-vllm-qwen-agentworld-35b-server-gate.json` pins the server
  image, source profile, checkpoint/template hashes, and runtime arguments.

The confirmed preflight is the first model-generation call. It must leave a
native session with positive usage, RPC lifecycle evidence, and an initial
provider request containing the approved model, 65,536-token ceiling, thinking
fields, and sampling tuple before the remaining reps start.

## Official sources

- https://huggingface.co/Qwen/Qwen-AgentWorld-35B-A3B
- https://github.com/QwenLM/Qwen-AgentWorld
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/

## Config rules

Use
`configs/baseline-qwen-agentworld-35b@1.0.0/qwen-agentworld-35b-a3b/high/`.
The config has no system preamble, orchestration file, or appended prompt. Do
not add AgentWorld's environment-simulation prompts, disable thinking, remove
thought preservation, or change the output ceiling or sampling tuple without a
new config release.

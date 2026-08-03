# Local vLLM ThinkingCap Qwen3.6 on server60 port 8081

This note records the provider and thinking path for
`baseline-thinkingcap-qwen36@1.1.0`. It supersedes the port-30000 evidence for
this release; historical results keep their original config identity.

## Model and endpoint

- Source checkpoint: `bottlecapai/ThinkingCap-Qwen3.6-27B`
- Base checkpoint: `Qwen/Qwen3.6-27B`
- Local checkpoint: AWQ INT4 through `compressed-tensors`
- Served model: `thinkingcap-qwen3.6-27b-awq-int4`
- Endpoint: `http://100.92.238.117:8081/v1`
- Provider/API: `local-vllm`, OpenAI-compatible chat completions
- vLLM: `0.25.1`, build `752a3a504485790a2e8491cacbb35c137339ad34`
- Context window: 262,144 tokens
- Maximum output: 98,304 tokens
- Billing: local compute
- Credential route: `LOCAL_VLLM_API_KEY=local`; the server does not require a
  secret

The live server uses two RTX 3090 GPUs, tensor parallelism 2, FP8 KV cache,
`max_num_seqs=4`, and `--language-model-only`. The requested benchmark uses two
workers, below the server's sequence limit.

## Thinking and request shape

Pi `0.83.0` is the tested subject. The model leaf uses:

```json
{
  "reasoning": true,
  "maxTokens": 98304,
  "compat": {
    "supportsDeveloperRole": false,
    "supportsReasoningEffort": false,
    "maxTokensField": "max_tokens",
    "thinkingFormat": "qwen-chat-template"
  }
}
```

Pi's `high` level is binary thinking-on control for this provider; it is not a
provider-side graded effort. The final request contains:

```json
{
  "max_tokens": 98304,
  "chat_template_kwargs": {
    "enable_thinking": true,
    "preserve_thinking": true
  },
  "temperature": 1.0,
  "top_p": 0.95,
  "top_k": 20,
  "min_p": 0.0,
  "repetition_penalty": 1.0
}
```

The release deliberately omits top-level `thinking_token_budget`. Reasoning and
final output share the 98,304-token envelope. This avoids expiring a separate
reasoning budget while the model is emitting tool arguments, the failure shape
reported in vLLM issue #44676.

vLLM `0.25.1` emits reasoning in the OpenAI-compatible `reasoning` field. Pi
`0.83.0` recognizes `reasoning_content`, `reasoning`, and `reasoning_text`, stores
the selected field name as the thinking signature, and replays the text under
that field on later assistant messages. The live multi-turn probe replayed the
server's `reasoning` field across three tool-result turns.

## Tool calling and streaming

The active server has:

- `--enable-auto-tool-choice`
- `--reasoning-parser qwen3`
- `--tool-call-parser qwen3_coder`
- no MTP or other speculative decoding
- no strict-tool-calling environment override
- prefix caching and chunked prefill enabled

In this vLLM image, `qwen3_coder` and `qwen3_xml` both register the same
`Qwen3EngineToolParser`, so the configured parser uses the XML-capable engine
path recommended by the tool-calling reliability report. The client leaves
`tool_choice` as `auto` or omitted; it does not force `required` or a named tool.

The approved live suite passed all of these conditions against the exact
endpoint and image:

1. A streamed response ended with `finish_reason="tool_calls"`, one function
   name, and JSON-decodable non-empty arguments.
2. Three consecutive tool-result turns produced exact, non-empty arguments.
3. Prior reasoning was replayed on turns two and three.
4. Unicode, a newline, and XML-like text survived exactly inside arguments.
5. No raw `<tool_call>` leaked into reasoning or content.

Prefix caching remains experimental for vLLM's Mamba alignment mode, but the
specific MTP-plus-prefix-cache failure does not apply because the active command
has no speculative configuration. The required benchmark preflight still gates
fan-out on a real Pi tool call and successful tool result.

## Usage and smoke evidence

Executor usage comes from native `session/*.jsonl` assistant
`message.usage` records. The live API returned `prompt_tokens`,
`completion_tokens`, and `total_tokens` on every probe. The config declares no
secondary model roles.

The leaf-local smoke contract requires:

- Pi `high` and the exact local model identity in the native session;
- positive executor and combined token totals;
- RPC prompt and quiescence evidence;
- an assistant response whose raw stop reason is `tool_calls`;
- a non-error `toolResult` message;
- a captured provider request with the 98,304-token ceiling, thinking fields,
  and sampling tuple.

## Evidence artifacts

- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-models-probe.json` records the
  served model and context limit.
- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-server-gate.json` pins the image,
  build, checkpoint hashes, runtime arguments, and parser conditions.
- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-pi-request-probe.jsonl` records
  Pi's final request shape against a mock endpoint without generating.
- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-tool-probe.py` is the fail-closed
  live validation program.
- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-tool-probe.jsonl` records the
  passing streamed and multi-turn results.
- `analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-reasoning-diagnostic.json`
  records the server's `reasoning` response field.

## Official sources

- https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.6-27B
- https://docs.qwencloud.com/developer-guides/text-generation/thinking
- https://qwen.readthedocs.io/en/stable/deployment/vllm.html
- https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
- https://github.com/vllm-project/vllm/issues/44676
- https://github.com/vllm-project/vllm/pull/40915

## Config rules and stale patterns

Use
`configs/baseline-thinkingcap-qwen36@1.1.0/thinkingcap-qwen3.6-27b-awq-int4/high/`.
Do not reuse the old port-30000 model leaf, old served model id, 81,920-token
ceiling, or 32,768-token hard thinking budget for this release. Do not add
config-authored prompt text, force tool choice, strip assistant reasoning during
replay, enable MTP without renewed server evidence, or change the output ceiling
or sampling tuple without a new config release.

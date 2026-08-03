# ThinkingCap Qwen3.6 tool-calling reliability

This report records the client settings and server prerequisites for running
`bottlecapai/ThinkingCap-Qwen3.6-27B` as a multi-turn Pi coding agent. It
summarizes the 2026-08-02 research and separates client controls from vLLM
failure modes that the client cannot repair.

Qwen maintainers say they fixed the base Qwen3.6-27B failure that placed XML
calls in `reasoning_content`; see
[Qwen3.6 #125](https://github.com/QwenLM/Qwen3.6/issues/125). No later
ThinkingCap checkpoint revision explicitly claims that fix. Treat ThinkingCap's
model-side status as unverified and keep the client and server protections below.

## Recommended Pi client contract

The current released baseline is
[`baseline-thinkingcap-qwen36@1.1.0`](../configs/baseline-thinkingcap-qwen36@1.1.0/README.md).
It applies this contract:

| Setting | Value | Why |
| --- | --- | --- |
| Pi API adapter | `openai-completions` | Uses vLLM's OpenAI-compatible chat and tool-call surface. |
| `reasoning` | `true` | Keeps Pi's reasoning-aware message path active. |
| `compat.thinkingFormat` | `qwen-chat-template` | Makes Pi send Qwen's `chat_template_kwargs.enable_thinking`. |
| `supportsDeveloperRole` | `false` | Avoids sending a role rejected by unmodified Qwen3.6 templates. |
| `chat_template_kwargs.enable_thinking` | `true` for the `high` leaf | Enables Qwen3.6 reasoning explicitly. |
| `chat_template_kwargs.preserve_thinking` | `true` | Keeps prior reasoning available across tool turns; missing history can degrade later calls to empty `{}` arguments. |
| `maxTokens` | `98304` | Uses the operator-approved output ceiling while leaving a large reasoning and tool-call envelope. |
| `tool_choice` | `auto` or omitted | Uses the configured XML parser path. Do not force `required` or a named tool until that exact server build passes the same streaming and non-streaming probes. |
| Sampling | `temperature=1.0`, `top_p=0.95`, `top_k=20`, `min_p=0.0` | BottleCapAI's published ThinkingCap sampling tuple. |

Two parts are load-bearing:

1. The client must preserve each assistant message's `reasoning_content` and
   send it back with later tool results. Setting `preserve_thinking=true` is
   insufficient if an intermediary strips that field.
2. The client must leave enough output budget for the complete reasoning and
   tool-call envelope. A stream cut during arguments looks like a parser bug
   but cannot be recovered downstream.

Pi `0.83.0` is the tested subject recorded by the config lock. The config's
provider-request extension reinforces `preserve_thinking=true` and the sampling
tuple at the final payload boundary.

## Thinking-budget caveat

The historical `baseline-thinkingcap-qwen36@1.0.0` release set top-level
`thinking_token_budget=32768` for its `high` leaf. The current 1.1.0 release
omits that separate budget so reasoning and final output share the 98,304-token
envelope.

[vLLM #44676](https://github.com/vllm-project/vllm/issues/44676) shows that an
expiring budget can inject the reasoning-end sequence into tool arguments when
the model starts `<tool_call>` without first closing reasoning. The published
reproducer used a very small budget near 256 tokens; the report does not prove
that 32,768 is unsafe. For maximum tool reliability:

- confirm the served vLLM contains an equivalent fix; or
- remove the hard thinking budget; or
- keep 32,768 only after a long multi-turn probe reaches the budget boundary
  without malformed arguments.

Treat malformed or duplicated arguments near exactly 32,768 reasoning tokens as
a budget-boundary failure first, not a model-weight failure.

## Server prerequisites

These are not Pi settings, but the client contract depends on them:

- Enable automatic tool choice and Qwen's parsers. On current vLLM, use
  `--enable-auto-tool-choice`, `--reasoning-parser qwen3`, and
  `--tool-call-parser qwen3_xml` when the pinned release provides them. Recent
  vLLM parser rewrites incorporate the character-level XML handling tracked by
  [#40915](https://github.com/vllm-project/vllm/pull/40915).
- Run a vLLM release that recovers `<tool_call>` when Qwen emits it before
  `</think>` or inside the reasoning region. The relevant fixes and redesign are
  tracked by [#35687](https://github.com/vllm-project/vllm/pull/35687),
  [#39055](https://github.com/vllm-project/vllm/pull/39055), and the newer parser
  engine referenced there.
- If MTP speculative decoding is enabled, verify the strict-tool-calling path
  before enabling structural-tag enforcement. The conservative fallback for the
  FSM failure in [#44006](https://github.com/vllm-project/vllm/issues/44006) is
  `VLLM_ENFORCE_STRICT_TOOL_CALLING=0`.
- If MTP and prefix caching are both enabled on this hybrid Qwen architecture,
  retain the recurrent-state cache fix tracked by
  [vLLM #48375](https://github.com/vllm-project/vllm/pull/48375), or disable one
  side of that pair. Switching between `qwen3_coder` and `qwen3_xml` does not fix
  corrupted recurrent-state KV.
- Prefer a Qwen3.6-native or validated self-healing template. A useful fallback
  closes dangling reasoning before `<tool_call>` and handles agent roles, but a
  template override should not replace parser and cache fixes.

## Settings to avoid

- Do not use `tool_choice="required"` as a reliability workaround. Older and
  affected vLLM paths bypass the configured XML parser and can return
  `tool_calls=[]`; see [vLLM #35936](https://github.com/vllm-project/vllm/pull/35936).
- Do not use a tiny thinking budget. It can expire inside the tool-call argument
  stream.
- Do not lower Pi's output-token limit to a chat-sized value such as 4K or 8K.
- Do not assume `preserve_thinking=true` works if a proxy or client drops
  `reasoning_content` on replay.
- Do not force the model to emit generic JSON through prompt text. Qwen3.6's
  native tool format is XML-like; the server parser converts it into the OpenAI
  `tool_calls` array.
- Do not add `presence_penalty=0.2` to the baseline based only on community loop
  reports. That workaround was not validated for ThinkingCap agent use.

## Validation before the 12_v2 run

The exact port-8081 endpoint and vLLM 0.25.1 image passed the streamed and
three-turn live suite recorded in
`analysis/thinkingcap-qwen36-8081/local-vllm-thinkingcap-qwen36-8081-tool-probe.jsonl`:

- the streamed call ended with `finish_reason="tool_calls"`, one function name,
  and JSON-decodable arguments;
- three tool-result turns retained exact, non-empty arguments;
- the server's `reasoning` field was replayed between turns;
- Unicode, multiline text, and XML-like text survived inside arguments;
- no raw `<tool_call>` leaked into reasoning or content;
- the active server had neither MTP nor a strict-tool-calling override, so their
  intermittent failure paths did not apply.

The required benchmark preflight must still validate the complete Pi path before
fan-out. It captures Pi's provider request and requires thinking enabled,
thinking preserved, expected sampling, the 98,304-token ceiling, a parsed
assistant tool call, and a non-error tool result. The config injects no hard
thinking budget.

Only after that preflight passes should the remaining `12_v2`,
three-repetition cells start.

## Sources

- [BottleCapAI ThinkingCap model card](https://huggingface.co/bottlecapai/ThinkingCap-Qwen3.6-27B)
- [Qwen3.6 #125: base-model tool calls emitted inside reasoning](https://github.com/QwenLM/Qwen3.6/issues/125)
- [Qwen thinking and multi-turn preservation](https://docs.qwencloud.com/developer-guides/text-generation/thinking)
- [Pi #3325: empty tool arguments without preserved thinking](https://github.com/earendil-works/pi/issues/3325)
- [vLLM #35687: implicit reasoning end at `<tool_call>`](https://github.com/vllm-project/vllm/pull/35687)
- [vLLM #39055: recover tool calls from reasoning](https://github.com/vllm-project/vllm/pull/39055)
- [vLLM #40915: robust streaming XML parser redesign](https://github.com/vllm-project/vllm/pull/40915)
- [vLLM #44676: thinking budget can corrupt tool arguments](https://github.com/vllm-project/vllm/issues/44676)
- [vLLM #35936: `tool_choice=required` parser bypass](https://github.com/vllm-project/vllm/pull/35936)
- [vLLM #44006: strict tool calling with speculative decoding](https://github.com/vllm-project/vllm/issues/44006)
- [vLLM #48375: MTP and prefix-cache recurrent-state fix](https://github.com/vllm-project/vllm/pull/48375)

# baseline-openrouter-deepseek-v4-flash-0731@1.0.0

Stock Pi baseline for `openrouter/deepseek/deepseek-v4-flash-0731`, served by the
DeepSeek provider on OpenRouter and pinned to `order=["deepseek"]`,
`quantizations=["fp8"]`, `allow_fallbacks=false`. It is the API-token counterpart
to `baseline-deepseek-v4-flash-0731@1.0.0`, which runs the same dated model on
the local server60 llama.cpp endpoint.

This config has no `system_preamble.md`, no `orchestration.md`, no `pi-flags`,
and no other config-authored prompt text. Sampling is pinned via the leaf
`models.json` `samplingParams` to `temperature=1.0`, `top_p=0.95` — the two
parameters the DeepSeek OpenRouter endpoint accepts (it does not expose `top_k`,
`min_p`, or `repetition_penalty`). This requires pi `0.84.0`, which merged
model-level `samplingParams` into the request; the subject image
(`harness/Dockerfile.pi-agent`, `PI_VERSION=0.84.0`, image rev `v4-pi0840-tools`)
is pinned accordingly.

The sealed `max` leaf maps Pi's `max` thinking level to DeepSeek-native
`reasoning.effort=max`. The read-long-lines pilot adds a `low` leaf on Pi
`0.84.1`; the same override maps it to `reasoning.effort=low`. See
`docs/openrouter-deepseek-v4-flash-0731-thinking.md` for provider, routing,
sampling, and request-shape evidence.

# baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.1.0

Post-acceptance production baseline Pi config for the native tensor-parallel
DeepSeek V4 Flash 0731 GGUF runtime at `server60:8034`.

This release raises the context window from the 140,000-token acceptance cap to
the live production gate of **148,000 tokens**, so its version impact is `rerun`
over 1.0.0 (the acceptance-gate release, which remains sealed provenance). It
pins the same Antirez IQ2_XXS/Q2_K/Q8_0 GGUF (`ca22ae2f…`), runtime image
`sha256:f91e8283…`, Whamp/vLLM commit `3ec20cebe`, and served model
`deepseek-v4-flash-0731-gguf-tp`. The live runtime observed on 2026-08-19
reports `max_model_len` 148000.

The server exposes 148,000 tokens of context, two sequences, and FP8 DeepSeek
MLA KV. It passed exact retrieval at 119,730 prompt tokens, 76.70 decode tok/s,
and 551.89 cache-busted prefill tok/s (acceptance-gate figures; KV-cache and
idle-VRAM numbers in the analysis are the acceptance snapshot, not re-measured
on the production gate).

The config adds no prompt text. It keeps Pi 0.84.1, max thinking, a 65,536-token
output cap, temperature 1.0, top-p 0.95, and a 360-second default timeout for
bash calls that omit one. The required preflight validates the model identity,
thinking/request shape, tool round trip, native usage, and bash-timeout audit
before the 12_v2 batch (1 rep, 2 workers) can fan out.

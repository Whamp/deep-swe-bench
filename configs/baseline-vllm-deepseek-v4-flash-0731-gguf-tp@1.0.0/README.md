# baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0

Baseline Pi config for the native tensor-parallel DeepSeek V4 Flash 0731 GGUF runtime at `server60:8034`.

This new config has version impact `rerun`. It pins the exact Antirez IQ2_XXS/Q2_K/Q8_0 GGUF (`ca22ae2f…`), runtime image `sha256:f91e8283…`, Whamp/vLLM commit `3ec20cebe`, and served model `deepseek-v4-flash-0731-gguf-tp`.

The server exposes 140,000 tokens of context, two sequences, 154,519 GPU KV-cache tokens, and FP8 DeepSeek MLA KV. The profile passed exact retrieval at 119,730 prompt tokens, 76.70 decode tok/s, and 551.89 cache-busted prefill tok/s. It has only 71–73 MiB idle VRAM headroom after long-context JIT and is an acceptance profile, not release-safe.

The config adds no prompt text. It keeps Pi 0.84.1, max thinking, a 65,536-token output cap, temperature 1.0, top-p 0.95, and a 360-second default timeout for bash calls that omit one. The required preflight validates the model identity, thinking/request shape, tool round trip, native usage, and bash-timeout audit before the pilot can run.

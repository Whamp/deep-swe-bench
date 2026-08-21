# baseline-openrouter-deepseek-v4-flash-0731@1.0.1

Stock Pi baseline for the low-reasoning OpenRouter DeepSeek V4 Flash 0731 comparison.

This release preserves the 1.0.0 low request behavior while pinning Pi 0.84.0 so the result is directly comparable with the completed 1.0.0 max benchmark. It uses `openrouter/deepseek/deepseek-v4-flash-0731`, routes only to the DeepSeek FP8 endpoint, disables fallbacks, sends `reasoning.effort=low`, and pins `temperature=1.0` with `top_p=0.95`.

The config has no `system_preamble.md`, no `orchestration.md`, no `pi-flags`, and no config-authored prompt text.

Provider and request-shape evidence is documented in `docs/openrouter-deepseek-v4-flash-0731-thinking.md` and the probe artifacts it references.

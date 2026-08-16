# baseline-vllm-deepseek-v4-flash-0731-wna16@1.1.0

Baseline Pi configuration for the projection-sensitive WNA16 quality candidate
at Hugging Face revision `12035985bf555d0ddc603c6305586a8fa915589c`.

This release changes the model artifact and served model identity from 1.0.0,
so its version impact is `rerun`. It uses Whamp/vLLM commit
`a7758f7436a713f042e245b3e0aaab64b3a2f2c6`, which includes independent w13/w2
group sizes and forwards DeepSeek V4's SwiGLU alpha, beta, and clamp settings to
Humming. The server profile caps context at 131,072 tokens for this larger
artifact.

The release adds no config-authored prompt text. It keeps Pi 0.84.1, max
thinking, a 65,536-token output cap, temperature 1.0, top-p 0.95, and a
360-second default timeout for bash calls that omit one. The early gate runs one
SuperJSON rep with `coding-agent-early-gate-v1`; it does not establish broader
coding quality or concurrency behavior.

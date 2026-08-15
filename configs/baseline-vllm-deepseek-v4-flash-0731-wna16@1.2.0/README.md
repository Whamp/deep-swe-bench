# baseline-vllm-deepseek-v4-flash-0731-wna16@1.2.0

Baseline Pi configuration for the DeepSeek V4 Flash 0731 WNA16 quality artifact
at revision `12035985bf555d0ddc603c6305586a8fa915589c`, served by the speed runtime
at `server60:8034`.

This release changes runtime and context behavior from 1.1.0, so its version
impact is `rerun`. It pins runtime image
`sha256:eb2884fc60ee332d7adb9d5e424e35acf8817dad0f93c8bb7ea7095cb8f58a0e`
and canonical runtime commit `b7766cfe4d15d9b68acea43097ceff221e8a739f`.
The server exposes 230,144 tokens of context, two sequences, 277,675 GPU KV
cache tokens, and 16 GiB of CPU KV offload.

The release adds no config-authored prompt text. It keeps Pi 0.84.1, max
thinking, a 65,536-token output cap, temperature 1.0, top-p 0.95, and a
360-second default timeout for bash calls that omit one. The required preflight
validates the changed runtime before the 12_v2 batch can fan out.

# baseline-vllm-deepseek-v4-flash-0731-wna16@1.0.0

Baseline Pi configuration for the server60 vLLM deployment of
`hampsonw/DeepSeek-V4-Flash-0731-WNA16`.

The release adds no config-authored prompt text. It uses Pi 0.84.1, max
reasoning, a 65,536-token output cap, DeepSeek's agentic temperature 1.0 and
top-p 0.95 settings, and a 360-second default timeout for bash calls that omit
one.

The server supports four scheduled sequences, but its 233,817-token aggregate
KV cache cannot hold four simultaneous 215,000-token contexts. Concurrency
experiments must therefore record KV utilization, waiting requests, and
preemptions alongside four-task makespan.

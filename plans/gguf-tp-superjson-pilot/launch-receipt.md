LAUNCH RECEIPT
WARNINGS
- none

SUMMARY
Plan: sha256:7ac3e4c4992a0c2aea9b3b7e75e483b127d0a3f678fd235767899b02bd9a6859
Subject: pi pi@0.84.1
Model: local-vllm/deepseek-v4-flash-0731-gguf-tp (thinking=max)
Tasks: 1; configs: 1; reps: 1; concurrency: 1
Comparison baseline: baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0 (selected config)
Cells: 1 preflight; 1 batch
Reusable completed batch entries: 0
Remaining batch attempts: 1
Preflight-covered batch entries: 1; successful preflight makes no second subject call
Resources: subject memory=4.0 GiB; verifier memory=4.0 GiB; additional swap=0.0 GiB; host reserve=12.0 GiB; confirmed host memory=60.6 GiB
Execution: agent timeout=10800.0; RPC quiescence=2.0s; initial context=captured; cell retries=0; auto resume=disabled; max quota wait=21600.0s; quota poll=300.0s; rate-limit backoff=60.0s
Degeneration watchdog: disabled

TASK SELECTION
Kind: tasks
- superjson-error-stack-serialization

CONFIG RELEASES
- baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0
  Lock: sha256:8b553e2d059aad34d8a71c7b5e9f8370bb995349f5338b4d67cce35aba721494
  Leaf: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max
  Smoke contract: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max/smoke.json
  Smoke assertions: {"equalsResultValues":{"arm_models.providers.local-vllm.api":"openai-completions","arm_models.providers.local-vllm.baseUrl":"http://100.92.238.117:8034/v1","arm_models.providers.local-vllm.compat.thinkingFormat":"openai","arm_settings.defaultThinkingLevel":"max","config":"baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0","config_name":"baseline-vllm-deepseek-v4-flash-0731-gguf-tp","model":"local-vllm/deepseek-v4-flash-0731-gguf-tp","subject_version":"pi@0.84.1","thinking_level":"max"},"minResultValues":{"combined_total_tokens":1,"total_tokens":1},"requireFiles":["session/*.jsonl","logs/pi-rpc-runner.jsonl","initial_context/capture_meta.json","initial_context/provider_request_0001.json","local-vllm-deepseek-v4-gguf-tp-bash-timeout.ndjson"],"requireJsonRecords":[{"equals":{"thinkingLevel":"max","type":"thinking_level_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"modelId":"deepseek-v4-flash-0731-gguf-tp","provider":"local-vllm","type":"model_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"message.rawStopReason":"tool_calls","message.role":"assistant","type":"message"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"message.isError":false,"message.role":"toolResult","type":"message"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"event":"prompt_sent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"event":"quiescent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"max_tokens":65536,"model":"deepseek-v4-flash-0731-gguf-tp","reasoning_effort":"max","temperature":1.0,"top_p":0.95},"format":"json","globs":["initial_context/provider_request_*.json"],"minimum":1},{"equals":{"action":"defaulted","effectiveTimeout":360,"event":"local_vllm_deepseek_v4_gguf_tp_bash_timeout","toolName":"bash"},"format":"jsonl","globs":["local-vllm-deepseek-v4-gguf-tp-bash-timeout.ndjson"],"minimum":1}],"requireRepoFiles":["configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/README.md","configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/pi-flags","configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/extensions/local-vllm-deepseek-v4-gguf-tp-request.ts","configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/extensions/local-vllm-deepseek-v4-gguf-tp-bash-timeout.ts","configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max/models.json","configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max/settings.json","docs/local-vllm-deepseek-v4-flash-0731-gguf-tp-thinking.md","analysis/deepseek-v4-gguf-tp-3ec20ceb/server-gate.json","analysis/deepseek-v4-gguf-tp-3ec20ceb/pi-request-probe.jsonl","analysis/deepseek-v4-gguf-tp-3ec20ceb/live-tool-probe.json","analysis/deepseek-v4-gguf-tp-3ec20ceb/live-post-tool-probe.json"]}

MODEL ROLES
config | role | kind | selection | provider | model | thinking | credential | billing | usage | bounds | activation
baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0 | executor | executor | fixed | local-vllm | local-vllm/deepseek-v4-flash-0731-gguf-tp | max | LOCAL_VLLM_API_KEY | local compute | session/*.jsonl | 1 executor session/rep; max concurrency 2 | required

SUBJECT COMPATIBILITY
- baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0
  Tested subject versions: pi@0.84.1
  Required capabilities: native-session-usage, pi-extensions, pi-rpc

BEHAVIOR DIFFERENCES FROM baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0

PREFLIGHT CELLS
- superjson-error-stack-serialization | baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-gguf-tp/max/workers-1/deepseek-v4-flash-0731-gguf-tp/max/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/superjson-error-stack-serialization/rep0/result.json | smoke=/home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/deepseek-v4-flash-0731-gguf-tp/max/smoke.json

BATCH CELLS
- superjson-error-stack-serialization | baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-gguf-tp/max/workers-1/deepseek-v4-flash-0731-gguf-tp/max/baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0/superjson-error-stack-serialization/rep0/result.json

PATHS
Workspace: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe
Tasks root: /home/will/evals/deep-swe/tasks
Results root: /home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-gguf-tp/max/workers-1
Structured state: /home/will/evals/deep-swe-bench/results/_runs/dsv4-gguf-tp-max-superjson-pilot-r1-w1--9fca88681fce92a90f6e9f0f9b4bde380a79bec9594390ff392ba10fa819ad88

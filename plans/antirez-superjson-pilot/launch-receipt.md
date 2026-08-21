LAUNCH RECEIPT
WARNINGS
- none

SUMMARY
Plan: sha256:2fab5b9d289d4e9451222ad1648d5a00bdf6bca1275833fc8eaead705836a84f
Subject: pi pi@0.84.1
Model: local-llamacpp/deepseek-v4-flash-0731-q8-fast-prefill (thinking=max)
Tasks: 1; configs: 1; reps: 1; concurrency: 1
Comparison baseline: baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0 (selected config)
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
- baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0
  Lock: sha256:8001052da6276ffd6d08f726dff98403b20d2a22be5a5e869a29e4cf3261fafd
  Leaf: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/deepseek-v4-flash-0731-q8-fast-prefill/max
  Smoke contract: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/deepseek-v4-flash-0731-q8-fast-prefill/max/smoke.json
  Smoke assertions: {"equalsResultValues":{"arm_models.providers.local-llamacpp.api":"openai-completions","arm_models.providers.local-llamacpp.baseUrl":"http://100.92.238.117:8033/v1","arm_models.providers.local-llamacpp.compat.thinkingFormat":"chat-template","arm_settings.defaultThinkingLevel":"max","config":"baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0","model":"local-llamacpp/deepseek-v4-flash-0731-q8-fast-prefill","openai_codex_oauth_passed":false,"subject_version":"pi@0.84.1","thinking_level":"max"},"minResultValues":{"combined_total_tokens":1,"total_tokens":1},"requireFiles":["session/*.jsonl","logs/pi-rpc-runner.jsonl","logs/pi.stderr.txt","llamacpp-deepseek-v4-bash-timeout.ndjson","initial_context/capture_meta.json","initial_context/provider_request_0001.json"],"requireJsonRecords":[{"equals":{"thinkingLevel":"max","type":"thinking_level_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"modelId":"deepseek-v4-flash-0731-q8-fast-prefill","provider":"local-llamacpp","type":"model_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"event":"prompt_sent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"event":"quiescent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"action":"defaulted","effectiveTimeout":360,"event":"llamacpp_deepseek_v4_bash_timeout","toolName":"bash"},"format":"jsonl","globs":["llamacpp-deepseek-v4-bash-timeout.ndjson"],"minimum":1},{"equals":{"chat_template_kwargs.enable_thinking":true,"chat_template_kwargs.reasoning_effort":"max","max_tokens":65536,"min_p":0.0,"model":"deepseek-v4-flash-0731-q8-fast-prefill","repeat_penalty":1.0,"temperature":1.0,"top_k":0,"top_p":0.95},"format":"json","globs":["initial_context/provider_request_*.json"],"minimum":1}],"requireRepoFiles":["configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/README.md","configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/pi-flags","configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/extensions/local-llamacpp-deepseek-v4-request.ts","configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/extensions/local-llamacpp-deepseek-v4-bash-timeout.ts","docs/llamacpp-deepseek-v4-flash-0731-q8-thinking.md","analysis/llamacpp-deepseek-v4-flash-0731-q8-server-gate.json","analysis/llamacpp-deepseek-v4-flash-0731-q8-reasoning-probe.json","analysis/llamacpp-deepseek-v4-flash-0731-q8-pi-request-probe.jsonl","analysis/llamacpp-deepseek-v4-flash-0731-q8-image-probe.json","configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/deepseek-v4-flash-0731-q8-fast-prefill/max/models.json","configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/deepseek-v4-flash-0731-q8-fast-prefill/max/settings.json"]}

MODEL ROLES
config | role | kind | selection | provider | model | thinking | credential | billing | usage | bounds | activation
baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0 | executor | executor | fixed | local-llamacpp | local-llamacpp/deepseek-v4-flash-0731-q8-fast-prefill | max | LOCAL_LLAMACPP_API_KEY | local compute | session/*.jsonl | 1 executor session/rep; max concurrency 1 | required

SUBJECT COMPATIBILITY
- baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0
  Tested subject versions: pi@0.84.1
  Required capabilities: native-session-usage, pi-extensions, pi-rpc

BEHAVIOR DIFFERENCES FROM baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0

PREFLIGHT CELLS
- superjson-error-stack-serialization | baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-antirez-iq2xxs-pi0841/max/workers-1/deepseek-v4-flash-0731-q8-fast-prefill/max/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/superjson-error-stack-serialization/rep0/result.json | smoke=/home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe/configs/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/deepseek-v4-flash-0731-q8-fast-prefill/max/smoke.json

BATCH CELLS
- superjson-error-stack-serialization | baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-antirez-iq2xxs-pi0841/max/workers-1/deepseek-v4-flash-0731-q8-fast-prefill/max/baseline-llamacpp-deepseek-v4-flash-0731-iq2xxs@1.1.0/superjson-error-stack-serialization/rep0/result.json

PATHS
Workspace: /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe
Tasks root: /home/will/evals/deep-swe/tasks
Results root: /home/will/evals/deep-swe-bench/results/_throughput/deepseek-v4-antirez-iq2xxs-pi0841/max/workers-1
Structured state: /home/will/evals/deep-swe-bench/results/_runs/dsv4-antirez-iq2xxs-max-superjson-pilot-r1-w1--00e3a5b7ec88ceea9f4f100f0584debe5eab4e82d3651f1eb3057ca97308d48d

#!/usr/bin/env bash
set -euo pipefail
cd /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe
export PYTHONPATH=.
export LOCAL_VLLM_API_KEY=local
exec python3 harness/run_batch.py execute \
  --plan plans/gguf-tp-superjson-pilot/launch-plan-v2.json \
  --confirm sha256:da89441015ca6893b280380d70fc71a3673cbdf002717c6baeaad9aba7e5e942 \
  >> plans/gguf-tp-superjson-pilot/run/pilot-v2.log 2>&1

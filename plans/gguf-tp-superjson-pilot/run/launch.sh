#!/usr/bin/env bash
set -euo pipefail
cd /home/will/evals/deep-swe-bench/.worktrees/gguf-tp-deepswe
export PYTHONPATH=.
export LOCAL_VLLM_API_KEY=local
exec python3 harness/run_batch.py execute \
  --plan plans/gguf-tp-superjson-pilot/launch-plan.json \
  --confirm sha256:7ac3e4c4992a0c2aea9b3b7e75e483b127d0a3f678fd235767899b02bd9a6859 \
  >> plans/gguf-tp-superjson-pilot/run/pilot.log 2>&1

# APPROVAL — GGUF-TP one-cell DeepSWE pilot

**Approved by Will: 2026-08-18**

This receipt authorizes launching the GGUF-TP SuperJSON pilot under the locked
plan below. It does **not** authorize the cancelled ≥72-cell multi-seed grid.

| Field | Value |
|---|---|
| Plan identity | `sha256:7ac3e4c4992a0c2aea9b3b7e75e483b127d0a3f678fd235767899b02bd9a6859` |
| Config | `baseline-vllm-deepseek-v4-flash-0731-gguf-tp@1.0.0` |
| Task | `superjson-error-stack-serialization` |
| Cells | 1 (GGUF-TP rep0 only) |
| Baseline | Reuse existing llama.cpp result; do not re-run unless incompatible |
| Pass | Will's closeness judgment (see club-3090 `M8-DEEPSWE.md`) |

Canonical project spec: `club-3090/.worktrees/gguf-tp-engine/.research/gguf-tp-engine/M8-DEEPSWE.md`

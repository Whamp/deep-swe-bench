# Embedding structure: Qwen3.6 27B Pi Codex Goal, 12_v2

## Scope and identity

This is an exploratory **full-corpus wrapper analysis**, not a prompt-only comparison. The baseline is clean stock Pi. The compared config adds `pi-codex-goal` and the initial `/create-goal <task>` adapter, so any difference may arise from behavior, tools, state, or trajectory—not merely prompt semantics.

- Model under evaluation: `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4`, thinking `high`
- Subset: `subsets/12_v2.txt`; 12 tasks × 3 exact paired reps = 36 pairs
- Baseline root: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b`
- Compared-config root: `results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal`
- Embedding endpoint: Tailnet `http://100.77.237.75:8090/v1/embeddings`
- Live probes: `GET /health` returned `{"status":"ok"}`; `GET /v1/models` reported `octen-embed` with `n_embd: 2560`
- Embedding model: `octen-embed` (Octen-Embedding-4B Q8_0 per `~/.pi/agent/LOCAL-AI.md`)
- Vector dimension observed in responses: 2,560
- No credentials were required or recorded.

## Inputs and preprocessing

Each embedded document is one exact task/rep pair:

1. The task's `../deep-swe/tasks/<slug>/instruction.md`, verbatim and untruncated.
2. A deterministic concise paired summary containing outcome class, baseline/compared-config status, binary and partial rewards, `agent_wall_s`, turns, and patch bytes.

The analysis does **not** embed generated free-form interpretations. Difficulty metadata comes from `data/deepswe-v1.1-task-difficulty.tsv`, joined by its `slug` column using the documented columns `pass_rate, language, slug, repository, title`; it is retained as metadata but not embedded.

Solved means only `reward_binary == 1`. Timeouts and negative rewards remain compared-config outcomes. There were no infrastructure exclusions. Fixed result roots ensure `results/_contaminated/` is excluded. Wall time is always `agent_wall_s`, never `wall_seconds`.

## Method

The script computes cosine similarity over the 2,560-dimensional vectors. It reports five nearest neighbors **excluding all reps of the same task**, avoiding the trivial near-duplicates created by three reps sharing one instruction. It also summarizes cross-task within/between-label cosine distributions.

Structural labels separate `gain`, `loss`, `stable_solved`, `stable_failed`, `treatment_timeout`, and `treatment_negative_reward` where present. This comparison contains only three observed labels: 31 stable failures, 4 compared-config timeouts, and 1 gain. There are no losses, stable solves, or non-timeout compared-config negative-reward labels.

## Findings

- Baseline solved **0/36** pairs; the compared config solved **1/36**. The sole gain was `go-critic-doc-link-checker/rep1` (difficulty pass rate 51).
- The four compared-config timeouts occurred on `langchain-request-coalescing/rep0` and all three `mobly-grouped-test-barriers` reps. Each recorded about 5,400 seconds in `agent_wall_s`. These remain outcomes, including cells where baseline reward was also `-1`.
- Timeout vectors were unusually close across the two timeout-bearing tasks: mean cross-task timeout↔timeout cosine **0.4063** (range 0.4046–0.4071, 3 pairs). For comparison, stable-failure↔stable-failure mean cosine was **0.2909** (436 pairs), and stable-failure↔timeout was **0.2786** (122 pairs).
- This apparent timeout region is fragile: three timeout vectors come from one task, there are only two timeout-bearing tasks, and the embedded summaries explicitly contain timeout/status information. It therefore shows recoverable descriptive structure, not a latent prompt-semantic cause.
- The sole gain is not isolated cleanly. Its nearest cross-task neighbors are stable failures from `participle-grammar-conflict-analysis` (cosines 0.4131–0.4161). Gain↔stable-failure mean cosine is **0.2449** across 29 cross-task pairs; with one gain, no gain cluster can be estimated.
- Cross-task nearest-neighbor label agreement is **58.3% (21/36)**. This is not strong evidence of separation and is dominated by the 31/36 stable-failure majority. A majority-only prediction would achieve 86.1%, so the agreement metric provides no predictive support.

## Interpretation

The embeddings expose one candidate region worth manual inspection: the two concurrency/synchronization-flavored tasks carrying all four timeouts (`langchain-request-coalescing` and `mobly-grouped-test-barriers`). However, the documents combine task text with observed trajectory summaries, so similarity may reflect both domain language and the explicit timeout descriptors. The gain has no neighboring gain with which to form a semantic region. Loss and stable-solved regions cannot be assessed because those outcomes do not occur.

**Conclusion:** there is weak exploratory evidence that compared-config timeouts concentrate in a small semantic/trajectory neighborhood, but no evidence that gains occupy a distinct region. Embedding proximity is taxonomy for follow-up inspection, never causal proof that goal tracking produced either outcome.

## Reproducible artifacts

- `analysis/qwen36-27b-pi-codex-goal-12v2/build_embedding_analysis.py`
- `analysis/qwen36-27b-pi-codex-goal-12v2/embedding_rows.json` — metadata, labels, metrics, and cross-task neighbors
- `analysis/qwen36-27b-pi-codex-goal-12v2/embedding_rows.csv` — flat machine-readable rows
- `analysis/qwen36-27b-pi-codex-goal-12v2/embedding_vectors.json` — vectors keyed by row id

Reproduce with:

```bash
python3 analysis/qwen36-27b-pi-codex-goal-12v2/build_embedding_analysis.py
python3 -m json.tool analysis/qwen36-27b-pi-codex-goal-12v2/embedding_rows.json >/dev/null
```

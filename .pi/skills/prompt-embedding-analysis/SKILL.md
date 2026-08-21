---
name: prompt-embedding-analysis
description: Prompt embedding analysis. Use when clustering benchmark prompt/config text, comparing semantic neighbors, or separating prompt-shaped effects from behavioral wrappers in deep-swe-bench results.
---

# Prompt Embedding Analysis

Leading rule: **neighbors are questions, not answers**. Embedding closeness ranks what to inspect; paired benchmark cells decide what happened.

## Process

1. **Set the branch.**
   - **Prompt-shaped** branch: static top-of-context/system-prompt variants. Primary clean-Pi category is `prompt_or_orchestration_only`; show `omp_pi_like_prompt_or_tool_surface` separately as prompt-shaped but tool/harness-confounded.
   - **Full-corpus** branch: wrappers/extensions may be included, but effects stay labeled as behavior/tool/memory/trajectory, not prompt-only.
   - Demote `pi-codex-goal`, codebase-memory, projected/observational memory, recursive/workflow agents, advisor, codegraph, and ponytail from prompt-shaped conclusions unless the user asks for wrapper analysis.
   - Completion: the included, separated, and excluded config sets are listed with rationale.

2. **Ground the artifacts.**
   - Prefer existing reproducible inputs before re-embedding:
     - `analysis/gpt55-low-historical-corpus/corpus_overlap_vs_clean_low.json`
     - `analysis/gpt55-low-historical-corpus/prompt_embedding_analysis.json`
     - `analysis/gpt55-low-historical-corpus/prompt_embeddings.json`
   - For the current GPT-5.5:low reports, reuse or update:
     - `analysis/gpt55-low-historical-corpus/embed_prompts.py`
     - `analysis/gpt55-low-historical-corpus/build_prompt_shaped_divergence_report.py`
     - `analysis/gpt55-low-historical-corpus/build_neighbor_divergence_report.py`
   - If re-embedding, read `~/.pi/agent/TAILNET.md` for the current Octen endpoint, verify `/health` and `/v1/models`, and confirm vector dimensionality. Do not mix old 1024-dimensional vectors with Octen vectors.
   - Completion: every input file, endpoint, model, dimension, and result root used by the analysis is recorded in the output JSON/report.

3. **Build prompt documents.**
   - Explicit prompts: `system_preamble.md`, `orchestration.md`, `omp-system-prompt.md`.
   - Prompt surface: explicit prompts plus extension-owned files whose path/content names prompt, instruction, message, goal, memory, workflow, advisor, codebase, codegraph, recursive, ponytail, initial, or hook behavior.
   - Keep explicit-prompt and prompt-surface documents separate; they answer different questions.
   - Completion: every included config has an embedded document or a stated exclusion reason.

4. **Join embeddings to outcomes.**
   - Count solves only with `reward_binary == 1`; negative or invalid rewards are not truthy solves.
   - Pair by exact task/rep cell. Separate full 108-cell `36_v2` comparisons from partial overlaps.
   - Use `combined_cost_usd`/`combined_total_tokens` when present; otherwise fall back to main `cost_usd`/`total_tokens`.
   - Do not use `results/_contaminated/` for normal efficacy claims.
   - Completion: every numeric claim traces to a JSON artifact or direct `result.json` cells.

5. **Find semantic neighbors.**
   - Rank high-cosine pairs with large solve or cost gaps, cluster ranges, and high-outcome semantic singletons.
   - For prompt-shaped work, make the clean-Pi prompt-only neighbor table the primary output; keep OMP/tool-surface neighbors in a caveat table.
   - Completion: each highlighted neighbor has cosine similarity, direct paired solve counts, unique wins/losses, cost delta, and source prompt files.

6. **Interpret divergences.**
   - Treat a cluster as a search space, not causal evidence.
   - Explain likely differentiators from unique files, prompt text, tool schema/harness differences, context placement, and direct discordant cells.
   - Never call `pi-codex-goal` or other behavior-changing wrappers “prompt-shaped” just because their prompt surface embeds near another config.
   - Completion: every conclusion states both the evidence and the caveat that limits the claim.

7. **Report and verify.**
   - Deliver per [report-delivery](../../../docs/agents/report-delivery.md):
     self-contained HTML, project design system, canonical report home,
     tailnet serving.
   - Validate with builder execution, `py_compile`, `json.tool`, HTML parse,
     required-string checks, placeholder scan, and tailnet `curl` HTTP 200.
   - Completion: report URL, artifact paths, and validation evidence are handed off.

## Pitfalls

- Embedding similarity is taxonomy, not proof of efficacy.
- OMP prompt/tool-surface rows are not clean-Pi prompt-only rows.
- A strong wrapper result may be interesting while irrelevant to prompt-shape decomposition.
- Aggregate solve deltas are weaker than direct paired wins/losses on the same cells.

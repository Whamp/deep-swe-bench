---
name: paired-trajectory-analysis
description: Paired trajectory analysis for benchmark churn. Use when comparing two configs on matched task/rep cells, explaining solve flips, diagnosing why one config solved and another failed, separating net score from churn, or preparing evidence to improve a skill/prompt/tool from trajectory differences.
---

# Paired trajectory analysis

Use this when a benchmark delta hides churn: one config gains some cells and loses others. The unit is a **paired cell**: same task, same rep, same model/thinking unless the comparison explicitly changes them.

## Process

1. **Lock the comparison and verify delivery.** State left config, right config, subset, reps, model, thinking level, and result roots. Confirm both sides have the intended cells, then verify each config's expected prompt, tool, hook, memory, model-setting, or harness surface from session/config artifacts. Classify delivery as `delivered`, `missing`, `ambiguous`, or `leaked`; keep intention-to-treat results primary. Completion: every pair maps to exactly one left and right `result.json`, and every treatment cell has a delivery classification.

2. **Split net from churn.** Compute left-only solves, right-only solves, both solved, neither solved, mean/median partial delta, token/cost/wall/tool deltas, and difficulty/language splits. Predeclare packet triggers for timeout or negative-reward discordance and material partial/f2p/p2p movement, not only binary flips. Keep observed outcomes primary and add an explicit timeout sensitivity view. Completion: the report shows net solve delta, solve-flip counts, timeout discordance, and the reproducible packet-selection rule.

3. **Build trajectory packets and stage ledgers.** For every selected cell, gather the paired `result.json`, session JSONL, `model.patch`, verifier artifacts, changed-file list, patch stats, tool timeline, and config-specific traces. Add a stage ledger from initialization through contract representation, seam location, implementation, targeted and regression validation, completion audit, and termination. Corroborate model claims with commands, patch state, and verifier evidence. Completion: each selected cell has a Markdown or JSON packet that can be reviewed without re-running the benchmark, and the earliest paired stage divergence is named.

4. **Decompose grading before assigning a driver.** State f2p and p2p passed/total separately on both sides, including missing grading or denominator changes. Then connect each failing test or reward drop to the concrete patch behavior. Before labeling an outcome infrastructure-caused, require an independent infrastructure signature, treatment linkage, paired or neighboring counterfactual evidence, and a disposition; ambiguous or treatment-linked failures remain observed outcomes. Completion: every classified cell names the feature and preservation effects, failed invariant, exact patch behavior, and evidence-backed disposition; uncertainty is explicit.

5. **Classify the driver.** Use the smallest specific bucket that fits: wrong seam/layer, under-implementation, over-implementation, missing invariant/guard, protocol/interface drift, cross-scope regression, validation gap, resource exhaustion, or likely variance. Completion: every selected cell has one primary bucket, optional secondary bucket, and evidence bullets.

6. **Compare winning and losing patterns.** Do not infer skill guidance from losses alone. Run the same packet method on right-only wins, then compare recurring patterns in wins vs losses. Semantic embeddings may prioritize review only: separate prompt-only from outcome/trajectory inputs, exclude same-task reps, and require direct trajectory evidence before promoting a mechanism. Completion: the synthesis separates “keep” patterns from “prevent” patterns and labels embedding findings exploratory.

7. **Translate to skill-design hypotheses.** Use `writing-great-skills` principles: propose checkable process changes, not vague advice. Completion: each proposed guidance change has a trigger, an action, a completion criterion, observed cells it could have changed, and known counterexamples; single-case proposals remain hypotheses.

8. **Publish as an evidence-first report.** For this repo, produce a self-contained HTML report served on the Tailnet. Include the packet links, bucket table, concrete task examples, and a short conclusion. Separate direct session/harness evidence, patch/verifier evidence, statistical direction, exploratory structure, and interpretation/confidence. Completion: the URL works and readers can identify what was observed versus inferred without reconstructing the analysis.

## Packet checklist

For detailed packet fields and reusable artifact layout, see [`references/packet-schema.md`](references/packet-schema.md).

Minimum packet contents:

- task slug, title, rep, difficulty, language
- left/right reward, f2p, p2p, tokens, cost, wall, turns, tool calls, patch bytes
- changed files, added/deleted/changed lines, patch excerpt
- session tool timeline, including config-specific tool calls such as `codegraph`, `advisor`, `recursive`, or `workflow`
- verifier failure names and relevant run-log/XML/reward excerpts
- classification bucket, mechanism, and skill-guidance implication

## Rules

- Churn is not noise by default. Treat every solve flip as explainable until the packet fails to support a mechanism.
- Net score is not a mechanism. Always report flip counts beside aggregate metrics.
- Do not call a tool or skill harmful from aggregate deltas alone. Require trajectory evidence.
- Do not call a tool or skill helpful from wins alone. Compare wins and losses.
- Keep claims local to the compared configs, subset, model, thinking level, and reps.

---
name: paired-trajectory-analysis
description: Paired trajectory analysis for benchmark churn. Use when comparing two configs on matched task/rep cells, explaining solve flips, diagnosing why one config solved and another failed, separating net score from churn, or preparing evidence to improve a skill/prompt/tool from trajectory differences.
---

# Paired trajectory analysis

Use this when a benchmark delta hides churn: one config gains some cells and loses others. The unit is a **paired cell**: same task, same rep, same model/thinking unless the comparison explicitly changes them.

## Process

1. **Lock the comparison.** State left config, right config, subset, reps, model, thinking level, and result roots. Confirm both sides have the intended cells. Completion: every compared pair maps to exactly one left `result.json` and one right `result.json`.

2. **Split net from churn.** Compute left-only solves, right-only solves, both solved, neither solved, mean/median partial delta, token/cost/wall/tool deltas, and difficulty/language splits. Completion: the report shows both net solve delta and solve-flip counts.

3. **Build a trajectory packet for each flip.** For every solve flip, gather the paired `result.json`, session JSONL, `model.patch`, verifier artifacts, changed-file list, patch stats, tool timeline, and config-specific tool/extension traces. Completion: each flip has a Markdown or JSON packet that can be reviewed without re-running the benchmark.

4. **Map verifier failure to patch delta.** For each lost solve, identify whether failure is f2p-only, p2p regression, apply/timeout/empty-patch, or verifier artifact. Then connect the failing test or reward drop to the concrete patch difference. Completion: every classified loss names the failed test/invariant and the exact patch behavior that explains it; uncertainty is explicit.

5. **Classify the driver.** Use the smallest specific bucket that fits: wrong seam/layer, under-implementation, over-implementation, missing invariant/guard, protocol/interface drift, cross-scope regression, validation gap, resource exhaustion, or likely variance. Completion: every flip has one primary bucket, optional secondary bucket, and evidence bullets.

6. **Compare winning and losing patterns.** Do not infer skill guidance from losses alone. Run the same packet method on right-only wins, then compare recurring patterns in wins vs losses. Completion: the synthesis separates “keep” patterns from “prevent” patterns.

7. **Translate to skill-design hypotheses.** Use `writing-great-skills` principles: propose checkable process changes, not vague advice. Completion: each proposed guidance change has a trigger, an action, and a completion criterion that would have changed at least one observed trajectory.

8. **Publish as an evidence-first report.** For this repo, produce a self-contained HTML report served on the Tailnet. Include the packet links, bucket table, concrete task examples, and a short conclusion. Completion: the URL works and the report distinguishes direct session evidence, source/patch evidence, and inference.

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

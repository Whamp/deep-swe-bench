# Task for delegate

[Read from: /home/will/evals/deep-swe-bench/analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/claude-code-by-agents-recursive-delegation__rep0__seam_gain.md]

Read-only trajectory classification. Two GPT-5.5-low CodeGraph CLI benchmark runs differ ONLY in the CodeGraph skill markdown: OLD skill vs SEAM skill (the seam skill adds a pre-edit 'seam checkpoint' naming the behavioral seam + invariant + scope guard, a 'Choose the behavioral seam before editing' scout step, and a rule 'Let CodeGraph make the edit smaller, not more elaborate'). Same model, same tools, same one-line prompt, same vendored CLI. Read this packet fully: analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/claude-code-by-agents-recursive-delegation__rep0__seam_gain.md . You may also read the two session JSONL files it references (paths in the packet). The SEAM skill GAINED a solve here (f2p 2/7 -> 7/7, partial +0.13). Classify the driver: (1) primary failure-mode bucket for why OLD failed and SEAM solved — pick the smallest specific one from: wrong seam/layer, under-implementation, over-implementation, missing invariant/guard, protocol/interface drift, cross-scope regression, validation gap, likely-variance. (2) The concrete patch/behavior difference between the two patches that explains the 5 f2p recovery. (3) Whether the seam-checkpoint skill TEXT plausibly changed the outcome, or whether this is run-to-run variance (confidence low/medium/high + one sentence). (4) Map the failing f2p tests to the exact patch delta. Be evidence-grounded; cite session/patch specifics. Do NOT run any benchmark or container. Return ONLY a JSON object: {"task","rep","direction","primary_bucket","mechanism","seam_text_plausibly_mattered","confidence","evidence_bullets":[...],"f2p_mapping"}.

## Acceptance Contract
Acceptance level: attested
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Return concrete findings with file paths and severity when applicable

Required evidence: review-findings, residual-risks

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```
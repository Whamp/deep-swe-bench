# Task for delegate

[Read from: /home/will/evals/deep-swe-bench/analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/go-critic-doc-link-checker__rep0__seam_loss.md]

Read-only trajectory classification. Two GPT-5.5-low CodeGraph CLI benchmark runs differ ONLY in the CodeGraph skill markdown: OLD skill vs SEAM skill (seam skill adds pre-edit 'seam checkpoint' + 'Choose the behavioral seam before editing' scout step + 'Let CodeGraph make the edit smaller' rule). Same model/tools/prompt/CLI. Read fully: analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/go-critic-doc-link-checker__rep0__seam_loss.md . SEAM skill LOST a solve OLD had (f2p 3/3 -> 2/3, p2p 16/16 -> 15/16, partial -0.105). Classify: (1) primary bucket for why seam failed (wrong seam/layer, under-implementation, over-implementation, missing invariant/guard, protocol/interface drift, cross-scope regression, validation gap, likely-variance). (2) concrete patch difference. (3) did the seam-checkpoint text plausibly CAUSE this loss or is it variance? confidence low/medium/high + one sentence. (4) map the 1 failing f2p + 1 failing p2p test to the patch delta. Cite session/patch evidence. Do NOT run any benchmark. Return ONLY JSON: {"task","rep","direction","primary_bucket","mechanism","seam_text_plausibly_mattered","confidence","evidence_bullets":[],"f2p_mapping"}.

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
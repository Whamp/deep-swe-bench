# Task for delegate

[Read from: /home/will/evals/deep-swe-bench/analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/happy-dom-deterministic-intersectionobserver__rep1__seam_gain.md]

Read-only trajectory classification. Two GPT-5.5-low CodeGraph CLI benchmark runs differ ONLY in skill markdown: OLD skill vs SEAM skill (seam adds 'seam checkpoint' + 'Choose the behavioral seam before editing' + 'make the edit smaller' rule). Same model/tools/prompt/CLI. Read fully: analysis/codegraph-cli-seam-checkpoint-36v2/churn_deep_dive/happy-dom-deterministic-intersectionobserver__rep1__seam_gain.md . SEAM GAINED a solve (f2p 13/14 -> 14/14, partial +0.0435). Classify: (1) primary bucket. (2) concrete patch difference. (3) did seam text plausibly help or variance? confidence + reason. (4) map the 1 failing f2p test to patch delta. Cite evidence. Do NOT run any benchmark. Return ONLY JSON: {"task","rep","direction","primary_bucket","mechanism","seam_text_plausibly_mattered","confidence","evidence_bullets":[],"f2p_mapping"}.

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
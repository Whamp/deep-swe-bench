# Review: sql-formatter-bigquery-pipe-formatting rep1

- **Bucket:** regression from under-scoped/global lexer change; not CodeGraph over-exploration or random variance.
- **Outcome delta:** clean Pi solved fully (`reward_binary=1`, `p2p=5709/5709`), CodeGraph missed binary by only 2 p2p tests (`5707/5709`, partial `0.999651`) while passing all 26 f2p tests.
- **Verifier failures:** the two failures were PostgreSQL regressions, not BigQuery target failures: `[p2p] PostgreSqlFormatter supports |>> operator` and `[p2p] PostgreSqlFormatter supports |>> operator in dense mode`. Both parse errors show `|>` being consumed as `PIPE_OPERATOR`, leaving `>` as an unexpected `OPERATOR` and the parser expecting a `pipe_clause_keyword`.
- **Patch difference that explains it:** CodeGraph added `{ type: TokenType.PIPE_OPERATOR, regex: /\|>/uy }` unconditionally in `src/lexer/Tokenizer.ts` and included `PIPE_OPERATOR` in `isReserved()` in `src/lexer/token.ts`. Baseline instead added `TokenizerOptions.supportsPipeOperator?: boolean`, gated the token regex with `cfg.supportsPipeOperator ? /[|]>/uy : undefined`, and set `supportsPipeOperator: true` only in BigQuery.
- **Layer/scope issue:** CodeGraph implemented a BigQuery feature at the shared lexer/parser layer without dialect gating, so PostgreSQL’s existing `|>>` operator was re-tokenized as `|>` + `>` before operator matching could handle it.
- **Trajectory driver:** CodeGraph used fewer turns/tool calls/tokens and had a smaller patch (`45` turns vs `54`, `44` calls vs `53`, `7404` patch bytes vs `8660`), so this was not over-exploration. The loss came from a missing cross-dialect regression check/guard.
- **Validation gap:** CodeGraph ran BigQuery-focused tests plus `ts:check`, `codegraph diff-impact/check`, and `lint:changes`; it did **not** run the full `yarn test --runInBand` suite that baseline ran. The local BigQuery tests passed, masking the PostgreSQL operator regression.
- **CodeGraph-specific contribution:** CodeGraph navigation/checks did not appear to cause churn or wrong-file wandering, but the structural validation was insufficient: `codegraph check --staged --cycles --signatures` cannot catch behavioral tokenization collisions across dialects.
- **Classification:** under-implementation of dialect scoping causing cross-dialect regression; wrong-layer/global-tokenizer work was the immediate mechanism; not variance.

```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "Wrote only the requested review artifact at .pi-subagents/artifacts/outputs/d2ec5ce5/analysis/codegraph-cli-skill-36v2/churn_deep_dive/review_sql_formatter.md; no code, configs, or tests were modified."
    }
  ],
  "changedFiles": [
    ".pi-subagents/artifacts/outputs/d2ec5ce5/analysis/codegraph-cli-skill-36v2/churn_deep_dive/review_sql_formatter.md"
  ],
  "testsAddedOrUpdated": [],
  "commandsRun": [
    {
      "command": "read analysis/codegraph-cli-skill-36v2/churn_deep_dive/sql-formatter-bigquery-pipe-formatting__rep1.md",
      "result": "passed",
      "summary": "Read the evidence packet."
    },
    {
      "command": "read analysis/codegraph-cli-skill-36v2/churn_deep_dive/sql-formatter-bigquery-pipe-formatting__rep1.json",
      "result": "passed",
      "summary": "Read structured patch/session metrics."
    },
    {
      "command": "grep verifier CTRF reports for failed statuses",
      "result": "passed",
      "summary": "Identified the two failed p2p tests as PostgreSQL |>> operator cases."
    },
    {
      "command": "read codegraph and baseline artifacts/model.patch",
      "result": "passed",
      "summary": "Confirmed unconditional CodeGraph PIPE_OPERATOR tokenization versus baseline BigQuery-only support flag."
    },
    {
      "command": "git status --short && git diff --cached --name-only",
      "result": "passed",
      "summary": "Observed pre-existing unstaged worktree changes and no staged files."
    }
  ],
  "validationOutput": [
    "CTRF summary: 5735 tests, 5733 passed, 2 failed.",
    "Failed tests: [p2p] PostgreSqlFormatter supports |>> operator; [p2p] PostgreSqlFormatter supports |>> operator in dense mode.",
    "git diff --cached --name-only produced no output."
  ],
  "residualRisks": [
    "Review-only task; no runtime test rerun was performed beyond inspecting existing verifier artifacts.",
    "Repository had many pre-existing unstaged changes unrelated to this artifact."
  ],
  "noStagedFiles": true,
  "diffSummary": "Added a markdown review artifact classifying the CodeGraph loss as a cross-dialect lexer regression from missing BigQuery-only gating.",
  "reviewFindings": [
    "no blockers"
  ],
  "manualNotes": "The markdown packet's verifier tail was empty, so exact failed-test names were sourced from the run's verifier/ctrf.json artifact."
}
```

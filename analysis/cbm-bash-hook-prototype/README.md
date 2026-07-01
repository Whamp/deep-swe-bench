# CMB bash-hook prototype

Throwaway offline prototype for a future `codebase-memory-mcp` bash search hook.

Scope:
- Reads existing `results/*/session/*.jsonl` only.
- Writes only under this directory.
- Does **not** mutate configs, harness, or `~/.pi/agent/extensions/codebase-memory.ts`.

Question:
Can we parse the bash commands agents actually run well enough to decide when to inject CMB hints, and which search tokens / result files should guide those hints?

Run:

```bash
python3 analysis/cbm-bash-hook-prototype/eval_parser.py --write-fixtures
```

Outputs:
- `fixtures/sampled_commands.jsonl` — frozen real bash command/result samples.
- `fixtures/gold.jsonl` — brute-force labels from actual command+output.
- `eval_summary.md` — precision/recall and failure examples.

Prototype rule:
This is not production code. If it answers the question, port the smallest useful piece into a new config; otherwise delete it.

Current finding:
- Evaluated 2,944 real bash calls from 12_v0 sessions across baseline, OM, CMB+OM, and CMB+OM-reindex.
- The useful hook surface is broader than quoted grep tokens: single-file grep needs command file operands, and generic grep patterns sometimes need top result files instead of tokens.
- Broad `find`/`ls` remains capped: only small listings (`<=8` source files) are treated as useful file targets.
- Dependency-manifest greps like `go.sum` are skipped unless they also produce source-file evidence.
- Latest heuristic-vs-heuristic eval: command precision 1.000, recall 1.000; token F1 0.993; file F1 1.000.

Caveat:
The gold set is still heuristic, not human-labeled truth. The perfect command score means the parser now matches this offline referee, not that the future extension is proven.

Likely implementation shape if ported:
1. Hook `bash` tool results, not `read`.
2. Skip validation/build/mutation commands.
3. For grep/rg/git-grep/xargs-grep, extract code-like tokens from actual search patterns.
4. Also parse source-file operands and `path:line:` output paths.
5. If tokens exist, query `search_graph` by token and rank hits whose files appeared in command/output first.
6. If no tokens but grep output names files, query compact file summaries for the top files.
7. Append the copyable hint:
   `For more: codebase-memory-mcp cli trace_path '{"project":"app","function_name":"QualifiedName","direction":"both"}'`

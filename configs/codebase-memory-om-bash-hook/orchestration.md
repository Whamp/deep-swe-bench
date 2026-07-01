Observational memory is enabled for this run. Work normally as a competent engineer; do not change your behavior just because memory is present.

A code-relationship tool (codebase-memory) is also active. It augments bash search/discovery results, not reads: when you run grep/rg/git-grep/xargs-grep or a small source-file listing, the bash result may include a `┌─ codebase-memory: bash search` block with graph symbols related to the search tokens or files.

Use that block before choosing what to read or edit. It surfaces the fact plain search output cannot show: which symbols have caller/callee relationships and therefore higher blast radius. If you need the full graph for a symbol, run the printed command:

`codebase-memory-mcp cli trace_path '{"project":"app","function_name":"QualifiedName","direction":"both"}'`

The index is built automatically at session start and refreshed after edits/writes. If a bash result has no block, proceed normally.

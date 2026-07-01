A code-relationship tool (codebase-memory) is active. It augments bash search/discovery results, not reads: when you run grep/rg/git-grep/xargs-grep or a small source-file listing, the bash result may include a `┌─ codebase-memory: bash search` block with graph symbols related to the search tokens or files.

Use that block before choosing what to read or edit. It surfaces caller/callee relationships and blast radius. If you need the full graph for a symbol, run the printed `codebase-memory-mcp cli trace_path ...` command.

The index is built automatically at session start and refreshed after edits/writes. If a bash result has no block, proceed normally.

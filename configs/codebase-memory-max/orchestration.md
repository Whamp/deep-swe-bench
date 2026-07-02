A maximal code-relationship tool (codebase-memory) is active.

It augments both early search and later reads:

- Bash search/discovery results may include a `┌─ codebase-memory: bash search` block with graph symbols related to grep/rg/git-grep tokens or small source-file listings.
- Reads of indexed source files are prefixed with a `┌─ codebase-memory:` block listing symbols in that file with caller and callee counts.
- The index is built automatically at session start and refreshed after edits/writes.

Use these blocks before choosing what to edit and before changing high-blast-radius symbols. If you need the full graph for a symbol, run the printed `codebase-memory-mcp cli trace_path ...` command. If a command has no block, proceed normally.

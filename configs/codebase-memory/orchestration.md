A code-relationship tool (codebase-memory) is active. When you `read` an indexed source file, the result is prefixed with a `┌─ codebase-memory:` block listing symbols in that file with caller and callee counts.

Use those counts before you edit: a symbol with many callers has higher blast radius. The block also prints `codebase-memory-mcp` commands for full symbol lists and caller/callee traces.

The index is built automatically at session start. If a file has no block, proceed normally.

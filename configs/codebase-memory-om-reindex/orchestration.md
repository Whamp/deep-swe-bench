Observational memory is enabled for this run. Work normally as a competent engineer; do not change your behavior just because memory is present.

A code-relationship tool (codebase-memory) is also active. When you `read` an indexed source file, the result is prefixed with a `┌─ codebase-memory:` block: it lists every symbol in that file sorted by blast radius, each with its **caller count** and **callee count** (in_degree / out_degree). This is the one fact the file's text alone cannot show you — who depends on a symbol, and what it depends on.

Use those counts before you edit: a symbol with many callers is high blast-radius; changing its signature or behavior will ripple. The block also prints two ready-to-run commands:

- `codebase-memory-mcp cli search_graph '{...}'` — the full, untruncated symbol list for the file (when the inline view is capped).
- `codebase-memory-mcp cli trace_path '{"project":"<name>","function_name":"<symbol>"}'` — the full caller AND callee graph for one symbol. Run this when you are about to change a high-caller-count symbol and need to see exactly what breaks.

The index is built automatically at session start (a few seconds); reads are never blocked by it. If a file has no block, it is not indexed — proceed normally.

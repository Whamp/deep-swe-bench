You have access to codegraph: a local tool that builds a symbol-and-relationship
map of this repository (who calls what, what depends on what). Use it to
understand blast radius before you change code.

The codegraph binary is at `/arm/bin/cg` (not on PATH; call it by full path).

Start of task — build the graph once (it takes a second or two):

    /arm/bin/cg build .

Then, before editing a function, check who depends on it:

- File summary (symbols + caller counts + risk tier):
      /arm/bin/cg brief <file>
- Who calls a specific symbol (callers / fan-in, excluding tests):
      /arm/bin/cg where <SymbolName> -T
- What breaks if a symbol changes (transitive impact):
      /arm/bin/cg fn-impact <SymbolName>
- Full context for a function (source + deps + callers + tests):
      /arm/bin/cg context <SymbolName>

A symbol with many callers or a HIGH RISK tier has a large blast radius — review
those callers before editing. Do not change symbols blindly; let the graph tell
you what else depends on what you touch. Otherwise work normally as a competent
engineer.

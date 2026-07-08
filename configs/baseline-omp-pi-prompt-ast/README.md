# baseline-omp-pi-prompt-ast

OMP runner using the approved Pi-like baseline OMP prompt, with
`read,bash,edit,write,ast_grep,ast_edit` enabled. This compares against
`baseline-omp-pi-prompt-bash-only` to isolate the value and cost of OMP's
structural AST search/edit tools without OMP's default long behavioral prompt
or dedicated grep/glob tools.

No `orchestration.md` or `system_preamble.md` is present. The only config-authored
prompt is `omp-system-prompt.md`, passed to OMP via `--system-prompt`.

`ast_edit` is intentionally a companion to normal `edit`, not a replacement:
use `edit` for normal local file changes and `ast_edit` only for scoped
codemod-style structural rewrites.

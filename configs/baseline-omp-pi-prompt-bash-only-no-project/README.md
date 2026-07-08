# baseline-omp-pi-prompt-bash-only

OMP runner using a Pi-like baseline system prompt approved in-session, with only
`read,bash,edit,write` enabled. This isolates OMP's runtime/tool implementation
from OMP's default long behavioral prompt and from dedicated grep/glob/AST tools.

No `orchestration.md` or `system_preamble.md` is present. The only config-authored
prompt is `omp-system-prompt.md`, passed to OMP via `--system-prompt`.

## OMP project-message normalization

This config is the no-project-message rerun of `baseline-omp-pi-prompt-bash-only`. It loads `extensions/omp_strip_project_message.js` to remove OMP's provider-visible `PROJECT` developer/runtime message before the model request. The benchmark keeps the same OMP system prompt and tool whitelist as `baseline-omp-pi-prompt-bash-only`.

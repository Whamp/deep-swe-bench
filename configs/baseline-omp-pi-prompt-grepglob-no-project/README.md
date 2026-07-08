# baseline-omp-pi-prompt-grepglob

OMP runner using the approved Pi-like baseline OMP prompt, with
`read,bash,edit,write,grep,glob` enabled. This compares against
`baseline-omp-pi-prompt-bash-only` to isolate the value and cost of OMP's
native grep/glob tools without OMP's default long behavioral prompt.

No `orchestration.md` or `system_preamble.md` is present. The only config-authored
prompt is `omp-system-prompt.md`, passed to OMP via `--system-prompt`.

## OMP project-message normalization

This config is the no-project-message rerun of `baseline-omp-pi-prompt-grepglob`. It loads `extensions/omp_strip_project_message.js` to remove OMP's provider-visible `PROJECT` developer/runtime message before the model request. The benchmark keeps the same OMP system prompt and tool whitelist as `baseline-omp-pi-prompt-grepglob`.

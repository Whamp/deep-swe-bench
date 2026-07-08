# baseline-omp-pi-prompt-grepglob

OMP runner using the approved Pi-like baseline OMP prompt, with
`read,bash,edit,write,grep,glob` enabled. This compares against
`baseline-omp-pi-prompt-bash-only` to isolate the value and cost of OMP's
native grep/glob tools without OMP's default long behavioral prompt.

No `orchestration.md` or `system_preamble.md` is present. The only config-authored
prompt is `omp-system-prompt.md`, passed to OMP via `--system-prompt`.

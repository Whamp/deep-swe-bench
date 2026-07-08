# OMP toolset variants

How the OMP (Oh My Pi) harness's tool whitelist is configured, the current
baseline toolset, and the two toolset-variant configs for testing where OMP's
token bloat comes from.

## How the OMP toolset is configured

OMP's enabled tools are controlled per-config, not hardcoded:

- **`configs/<config>/omp-tools.txt`** — the `--tools` enable-whitelist passed to
  `omp`. One tool id per line (comma-separated also works); `#` comments allowed.
  Validated by `harness/run_omp.py:resolve_omp_tools` against OMP's known ids, so a
  typo fails fast. Absent file → falls back to the 6-tool basic set.
- **`configs/<config>/omp-overlay.yml`** — optional OMP config overlay passed via
  `omp --config /arm/omp-overlay.yml` (the config dir is mounted read-only at
  `/arm`). Use it to pin OMP settings per config (e.g. `bashInterceptor.enabled`,
  `astGrep.enabled`).
- The resolved tool list is recorded in every `result.json` as `omp_tools`, so
  each cell is self-documenting and the smoke contract asserts it.

### Relevant OMP built-in defaults (verified via a fresh profile)

| setting | default | meaning |
|---|---|---|
| `bashInterceptor.enabled` | **false** | bash `grep`/`find`/`cat`/`sed` are NOT redirected to dedicated tools; they run natively |
| `grep.enabled` | true | the `grep` tool is available (unless excluded by `--tools`) |
| `glob.enabled` | true | the `glob` tool is available (unless excluded by `--tools`) |
| `astGrep.enabled` | true | the `ast_grep` tool is gated on (unless excluded by `--tools`) |
| `astEdit.enabled` | true | the `ast_edit` tool is gated on (unless excluded by `--tools`) |

`--tools=<list>` is the **master whitelist**: a tool is enabled only if it is both
listed there AND its `.enabled` config flag is true. So listing only core tools
excludes the AST tools even though their config flags default on.

### Binaries available in the `deep-swe-pi` image

`rg`, `grep`, `find`, `fd`, and `sg` (the ast-grep CLI) are all present, so both
bash-based search (Config A) and AST tools (Config B) have working backends. The
`ast-grep` symlink is absent but `sg` is the canonical ast-grep binary.

## The three configs

| config | grep | glob | ast_grep | ast_edit | bash search | purpose |
|---|---|---|---|---|---|---|
| `baseline-omp` | ✅ | ✅ | ❌ | ❌ | available | current OMP baseline (the 36_v2 result) |
| `baseline-omp-bash-only` | ❌ | ❌ | ❌ | ❌ | **primary** | Config A — recover token efficiency |
| `baseline-omp-ast` | ❌ | ❌ | ✅ | ✅ | available | Config B — do AST tools compensate? |

All three run `gpt-5.5` low, `--no-skills --no-extensions --no-rules --no-lsp`,
filtered openai-codex OAuth, RPC mode, identical orchestration text, and
`bashInterceptor.enabled=false` (default for baseline; pinned in the overlay for A
and B). The **only** intended variable across the three is the tool whitelist.

### `baseline-omp` (current — documented)

`omp-tools.txt`: `read,bash,edit,write,grep,glob`. This is the config that produced
`analysis/omp-vs-pi-36v2`: equivalent solve quality to Pi at ~2.2× cost / ~3.5×
tokens. OMP leans on `read`/`grep`/`glob` (Pi leans on `bash`), which is the
motivation for the variants.

### `baseline-omp-bash-only` (Config A)

`omp-tools.txt`: `read,bash,edit,write`. Drops `grep` + `glob`, so the agent
searches via bash (`rg`/`grep`/`find`/`fd`) — the closest OMP analogue of the Pi
baseline. **Hypothesis:** OMP's token bloat is partly its dedicated grep/glob tools
+ larger tool schemas; removing them recovers efficiency. Measures how much, and
whether solve rate holds.

### `baseline-omp-ast` (Config B)

`omp-tools.txt`: `read,bash,edit,write,ast_grep,ast_edit` + overlay pinning
`astGrep.enabled`/`astEdit.enabled` on. Same plain grep/glob removed as Config A,
replaced by AST-aware search/edit (`sg`-backed). **Hypothesis:** AST tools may
compensate for losing grep/glob — recovering solve rate at lower token cost than
the dedicated plain tools, or merely adding another expensive surface.

## Launching

```bash
# Config A — bash-only (grep/glob off)
PYTHONPATH=. python3 harness/run_batch.py --agent omp --configs baseline-omp-bash-only \
    --subset 36_v2 --model openai-codex/gpt-5.5 --thinking low \
    --runs 3 --workers 12 --pass-openai-codex-oauth --rpc-quiescence 2 \
    --run-id gpt55-low-baseline-omp-bashonly-36v2-r3-w12 --progress-interval 15

# Config B — ast tools (grep/glob off, ast_grep/ast_edit on)
PYTHONPATH=. python3 harness/run_batch.py --agent omp --configs baseline-omp-ast \
    --subset 36_v2 --model openai-codex/gpt-5.5 --thinking low \
    --runs 3 --workers 12 --pass-openai-codex-oauth --rpc-quiescence 2 \
    --run-id gpt55-low-baseline-omp-ast-36v2-r3-w12 --progress-interval 15
```

Both reuse the existing `baseline-omp` 36_v2 cells and the Pi `baseline` 36_v2 cells
for comparison via `analysis/harness-forensics/run_analysis.py`.

## Validation status

Each config ships a `gpt-5.5/low/smoke.json` contract asserting `omp_tools`,
`agent=omp`, model/thinking, RPC runner events, and forbidding API-key/model errors.
A preflight smoke must pass before any full batch (run_batch does this automatically
for new configs unless `--no-smoke-new-configs`).

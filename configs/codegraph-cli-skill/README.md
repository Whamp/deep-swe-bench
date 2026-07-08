# codegraph-cli-skill

Soft CodeGraph config with the full refined CodeGraph skill directory and the
vendored CodeGraph CLI available on PATH as `codegraph`.

Prompt delta is intentionally only the user-approved sentence:

> You should use `codegraph` cli to assist you.

No auto-injection extension is loaded. The executor must choose to use the CLI or
invoke the `codegraph` skill.

## Files

- `orchestration.md` — the exact appended task guidance.
- `skills/codegraph/` — the full CodeGraph skill directory, including
  `COMMANDS.md`.
- `tools/codegraph` — PATH wrapper for `/arm/bin/codegraph/dist/cli.js`.
- `tools/codegraph-transformers-cache.mjs` — preloads Transformers.js with a writable `/tmp` cache so `codegraph embed .` works even though `/arm` is read-only.
- `node_modules/@huggingface/transformers/` — optional semantic-search peer dependency installed by `scripts/vendor_codegraph.sh`; required for `embed`/`search`.
- `bin/codegraph` and `bin/cg` — populated by `scripts/vendor_codegraph.sh`.

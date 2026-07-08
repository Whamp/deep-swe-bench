# codegraph-cli-skill-seam-checkpoint

Soft CodeGraph config with the refined CodeGraph skill copied in. This is a
versioned sibling of `codegraph-cli-skill` so runs can compare the updated skill
against earlier CodeGraph CLI treatment results without changing the old config
name.

Prompt delta remains intentionally only the previously approved sentence:

> You should use `codegraph` cli to assist you.

No auto-injection extension is loaded. The executor must choose to use the CLI or
invoke the `codegraph` skill.

## Files

- `orchestration.md` — the exact appended task guidance.
- `skills/codegraph/` — the refined CodeGraph skill directory, including
  `COMMANDS.md`.
- `tools/codegraph` — PATH wrapper for `/arm/bin/codegraph/dist/cli.js`.
- `tools/codegraph-transformers-cache.mjs` — preloads Transformers.js with a writable `/tmp` cache so `codegraph embed .` works even though `/arm` is read-only.
- `node_modules/@huggingface/transformers/` — optional semantic-search peer dependency installed by `scripts/vendor_codegraph.sh`; required for `embed`/`search`.
- `bin/codegraph` and `bin/cg` — populated by `scripts/vendor_codegraph.sh`.

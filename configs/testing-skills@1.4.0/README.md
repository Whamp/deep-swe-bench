# testing-skills@1.4.0

Versioned Pi config that exposes the complete `testing`, `fuzzing`, and
`property-based-testing` skill packages through Pi's model-invocable skill
mechanism.

The packages are vendored from `Whamp/skills` tag `testing-skills-exp-2026-08-pbt-commit` at exact commit
`18df568a63e4a36410823806906531691c21e9e8`. Relative to `testing-skills@1.3.0`, this cumulative release
adds property-based-testing Commit or Return admission plus concrete oracle, search, replay, and failure-handling contracts. The tag is an unevaluated experiment marker; this config exists to
measure that behavior.

No system preamble, orchestration file, appended system prompt, extension,
secondary model, nested model call, or forcing checkpoint is added. The only
model role is the main Pi executor. Executor usage comes from native
`session/*.jsonl` assistant messages.

The release has one leaf:

- `gpt-5.6-sol/low`

Subset and rep count belong to the launch plan rather than the config identity.

# testing-skills@1.3.0

Versioned Pi config that exposes the complete `testing`, `fuzzing`, and
`property-based-testing` skill packages through Pi's model-invocable skill
mechanism.

The packages are vendored from `Whamp/skills` tag `testing-skills-exp-2026-08-final-evidence` at exact commit
`ba9abfbb78ec1461dec157064e3de57fd3f9a33f`. Relative to `testing-skills@1.2.0`, this cumulative release
adds final-patch evidence closure, failure classification, information-gated reruns, and an explicit stopping rule. The tag is an unevaluated experiment marker; this config exists to
measure that behavior.

No system preamble, orchestration file, appended system prompt, extension,
secondary model, nested model call, or forcing checkpoint is added. The only
model role is the main Pi executor. Executor usage comes from native
`session/*.jsonl` assistant messages.

The release has one leaf:

- `gpt-5.6-sol/low`

Subset and rep count belong to the launch plan rather than the config identity.

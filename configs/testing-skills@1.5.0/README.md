# testing-skills@1.5.0

Versioned Pi config that exposes the complete `testing`, `fuzzing`, and
`property-based-testing` skill packages through Pi's model-invocable skill
mechanism.

The packages are vendored from `Whamp/skills` tag `testing-skills-exp-2026-08-fuzz-admission` at exact commit
`871c4c246fdf3b1ce1d9b747356be2adf84a8e69`. Relative to `testing-skills@1.4.0`, this cumulative release
adds fuzzing Commit or Return admission, generic engine routing, bounded campaign resources, and qualified conclusions. The tag is an unevaluated experiment marker; this config exists to
measure that behavior.

No system preamble, orchestration file, appended system prompt, extension,
secondary model, nested model call, or forcing checkpoint is added. The only
model role is the main Pi executor. Executor usage comes from native
`session/*.jsonl` assistant messages.

The release has one leaf:

- `gpt-5.6-sol/low`

Subset and rep count belong to the launch plan rather than the config identity.

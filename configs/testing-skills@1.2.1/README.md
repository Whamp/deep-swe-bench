# testing-skills@1.2.1

Versioned Pi config that exposes the complete `testing`, `fuzzing`, and
`property-based-testing` skill packages through Pi's model-invocable skill
mechanism.

The packages are vendored from the unevaluated `Whamp/skills` tag
`testing-skills-exp-2026-08-v1.2.1-routing-clarity` at exact commit
`7ffc9b4dc56744f7b3e9205bd13a94d4a8665220`. Relative to
`testing-skills@1.2.0`, this release clarifies plausible-failure thresholds,
explains generated-search value and oracle terminology, gates specialist
routing on post-inspection executable plans, makes the contract inventory
compact and groupable, requires interaction coverage, and narrows outer-boundary
evidence with implementation-scope guards.

The source edits affect only the three `SKILL.md` files. All references remain
byte-identical to `testing-skills@1.2.0`. Offline dependency installation and new
specialist ecosystem adapters are intentionally deferred to a separate v1.2.2
experiment.

No system preamble, orchestration file, appended system prompt, extension,
secondary model, nested model call, or forcing checkpoint is added. The only
model role is the main Pi executor. Executor usage comes from native
`session/*.jsonl` assistant messages.

The release has one leaf:

- `gpt-5.6-sol/low`

Subset and rep count belong to the launch plan rather than the config identity.

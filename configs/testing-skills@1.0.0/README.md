# testing-skills@1.0.0

Versioned Pi config that exposes three engineering skills to the executor through
Pi's model-invocable skill mechanism:

- `testing`
- `fuzzing`
- `property-based-testing`

The complete skill packages are vendored from
`Whamp/skills` commit `bd1e5819fda90320abd748b0f8323ead3c489a66` under
`engineering/`. Pi receives each package as an explicit `--skill` path, so its
name and description appear in the available-skills system-prompt inventory and
the model can load `SKILL.md` on demand. The supporting reference files remain
relative to each skill directory.

This config adds no system preamble, orchestration file, appended system prompt,
extension, secondary model, or nested model call. Its only model role is the
main Pi executor. Executor usage comes from native `session/*.jsonl` assistant
messages.

The release has one leaf:

- `gpt-5.6-sol/low`

The intended first comparison scope is `12_v2` with three reps per task. Subset
and rep count belong to the launch plan rather than the config identity.

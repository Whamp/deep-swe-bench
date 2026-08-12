# testing-skills@1.1.0

Versioned Pi config that exposes three engineering skills to the executor through
Pi's model-invocable skill mechanism:

- `testing`
- `fuzzing`
- `property-based-testing`

The complete skill packages are vendored from
`Whamp/skills` commit `9ebd4c43a88ca04986f87d346486ba903eed0070` under
`engineering/`. Pi receives each package as an explicit `--skill` path, so its
name and description appear in the available-skills system-prompt inventory and
the model can load `SKILL.md` on demand. The supporting reference files remain
relative to each skill directory.

Relative to `testing-skills@1.0.0`, this release gives the specialist skill
descriptions implementation-oriented triggers and makes the `testing` skill's
handoff to matching specialists more explicit. It adds no forcing checkpoint,
system preamble, orchestration file, appended system prompt, extension,
secondary model, or nested model call. Its only model role is the main Pi
executor. Executor usage comes from native `session/*.jsonl` assistant messages.

The release has one leaf:

- `gpt-5.6-sol/low`

The intended first comparison scope is `36_v2` with three reps per task. Subset
and rep count belong to the launch plan rather than the config identity.

# pi-fabric PR #10 commit 0da479f validation

This note establishes the exact candidate used for the requested DeepSWE
comparison refresh.

## Requested source

- Pull request: <https://github.com/monotykamary/pi-fabric/pull/10>
- Branch named by the maintainer: `fix/read-economy-guidance`
- Requested commit: `0da479fe267232115b3fbf0893067352622b0f29`
- Package identity at that commit: `pi-fabric@0.28.11`

At capture time the live PR head was
`8e91aea9a9fff8a29ad7c0849e98e82a2ed2fa5a`. The requested commit is its
ancestor. The two later commits modify only
`tests/output-budget.test.ts` and `tests/prewalk-prompt.test.ts`; a targeted diff
found no change under `package.json`, `src/`, `skills/`, or `dist/`.

The benchmark nevertheless uses a detached checkout of the requested full SHA,
not the moving branch or PR head.

## Package certification

A fresh clone ran:

```text
pnpm install --frozen-lockfile
pnpm run check
npm pack --ignore-scripts --json
```

Type checking, build, all 1,125 tests in 100 test files, and the dead-code check
passed. The packed runtime contains 692 files and has SHA-256:

```text
55c054734aad22b650150e1fe698c1bb7b580dd39bde1334d302503e09c6a8c5
```

Machine-readable evidence is in
`analysis/pi-fabric-pr10-0da479f-package-validation.json`.

## Subject and model path

The candidate package pins `@earendil-works/pi-ai` `0.83.0` and uses Pi coding
agent/TUI `0.83.0` for development. The benchmark subject image is therefore
pinned to Pi `0.83.0`, with a new image revision to prevent reuse of Pi `0.81.1`
layers.

A local image probe reported Pi `0.83.0` and imported the packaged Fabric
extension successfully without making a model call. The image identity and
probe output are recorded in
`analysis/pi-0830-pi-fabric-pr10-local-probe.json`.

The provider path remains the previously validated
`openai-codex/gpt-5.6-sol` path at `low` thinking through
`OPENAI_CODEX_OAUTH`. The preflight must record Pi `0.83.0`, an explicit
`reasoning.effort` of `low`, native session usage, Pi RPC transport evidence,
and the `fabric_exec` tool marker before the remaining reps may fan out.

## Model roles

The active DeepSWE launch path has one model role: the main executor. Fabric's
advanced agent, actor, workflow, and RLM capabilities require explicit
invocation and are not requested by the task prompt. The earlier 108-rep Fabric
comparison contained zero model-authored `agents.run`, `agents.spawn`,
`agents.handoff`, `agents.create`, or `rlm.query` calls. Any unexpected secondary
model activity discovered in the new preflight or batch evidence invalidates
executor-only usage accounting and must stop interpretation of affected reps.

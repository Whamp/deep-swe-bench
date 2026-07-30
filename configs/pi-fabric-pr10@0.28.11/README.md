# pi-fabric-pr10@0.28.11

This config runs stock Pi with the exact `pi-fabric` package requested for
[pi-fabric PR #10](https://github.com/monotykamary/pi-fabric/pull/10).

The runtime package is built from detached commit
`0da479fe267232115b3fbf0893067352622b0f29` on the requested
`fix/read-economy-guidance` branch. Its SHA-256 is
`55c054734aad22b650150e1fe698c1bb7b580dd39bde1334d302503e09c6a8c5`.
The PR later advanced by two test-only commits; the target and live PR head have
no differences under `package.json`, `src/`, `skills/`, or `dist/`.

The config adds no system preamble, orchestration text, environment override, or
unrelated extension. It loads the packaged extension from
`/arm/extensions/node_modules/pi-fabric` with upstream defaults. Advanced agent
and workflow surfaces remain upstream opt-in behavior; the DeepSWE task prompt
does not invoke them, and the executor's native session remains the sole active
model-usage source.

## Release decision

- Version impact: `rerun`
- Subject: Pi `0.83.0`
- Model: `openai-codex/gpt-5.6-sol`
- Thinking: `low`
- Credential route: `OPENAI_CODEX_OAUTH`
- Usage: native `session/*.jsonl`
- Historical comparison reference: legacy `baseline` results; the baseline is
  review-only and receives no new reps in this launch.

Exact package and upstream certification evidence is recorded in
`extensions/UPSTREAM.json` and
`analysis/pi-fabric-pr10-0da479f-package-validation.json`.

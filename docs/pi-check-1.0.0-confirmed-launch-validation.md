# `pi-check@1.0.0` confirmed-launch preflight record

`pi-check@1.0.0` completed one approved confirmed-launch preflight on 2026-07-26
with Pi 0.81.1 and `openai-codex/gpt-5.6-sol` at low thinking. The identical
batch entry reused that successful preflight result and made no second subject
call.

Final review found that the 1.0.0 smoke contract required provider-request and
session files but did not parse their model, reasoning effort, or thinking
level. The observed artifacts are internally consistent, but the reusable gate
was too shallow for production batch approval. Do not launch a production batch
with 1.0.0. `pi-check@1.0.1` supersedes it with structured JSON checks.

Compact evidence:

```text
analysis/pi-check-1.0.0-confirmed-launch-preflight.json
```

## Approved cell

| Field | Value |
| --- | --- |
| Config | `pi-check@1.0.0` |
| Config lock | `sha256:e7e71457812a79f79bc990e92bc511265825096489e8d09503352192246fc3df` |
| Plan | `sha256:a0ff0083a779e690c86053d4c093ab1a8749ec39e93c526db37834a36a600c1e` |
| Subject | `pi@0.81.1` |
| Model | `openai-codex/gpt-5.6-sol` |
| Thinking | `low` |
| Task | `fd-deterministic-multi-key-sorting` |
| Rep | `0` |
| Billing route | Codex subscription quota |
| Usage source | Native `session/*.jsonl` |

The operator reviewed the receipt and confirmed the exact plan digest before
execution. The receipt declared one executor role, no secondary model roles,
one worker, zero cell retries, no automatic quota resume, and stop-on-transient
behavior.

## First attempt: blocked before model use

The first approved plan failed before Docker created the subject container.
`harness/run.py` copied the versioned config identity into the container name,
and Docker rejected the `@` character. The run recorded a failed preflight,
started zero batch cells, wrote no result or session, made no model request, and
did not seal the config.

Commit `c278293` added one shared Docker-name sanitizer for the Pi and OMP
runners. The regression test covers `pi-check@1.0.0`; a property test checks
arbitrary input characters; and a model-free `docker create` check accepted the
fixed name. The operator then reviewed and approved a newly compiled plan.

The failed run remains under:

```text
results/_runs/confirmed-launch-pi-check-1.0.0-gpt56-sol-low-pr--037ec3eddc754319edf1f40b8a82f6d005c2da6546d463049f368516146e03ac/
```

## Successful preflight

The replacement run completed with this event sequence:

1. `run_started`
2. `preflight_started`
3. `preflight_finished` with outcome `ok` and no diagnostics
4. `cell_skipped` for the identical batch entry with reason
   `successful_preflight`
5. `run_completed`

The result recorded:

| Metric | Value |
| --- | ---: |
| Partial reward | `1.0` |
| Binary reward | `1` |
| Input tokens | `58,087` |
| Output tokens | `12,548` |
| Cache-read tokens | `706,048` |
| Total tokens | `776,683` |
| Cost | `$1.019899` |
| Agent wall time | `333.7s` |
| Turns | `30` |
| Tool calls | `34` |

An independent call to `harness.parse_usage.parse_session` reproduced every
native usage field in `result.json`.

## Evidence agreement

The plan, manifest, status, events, result, native session, RPC log, provider
request captures, smoke diagnostics, dashboard projection, and config seal
agree on the launch identity, config identity, model, thinking level, task, rep,
and final verdict.

Specific checks:

- `result.json` records the config lock, plan identity, harness revision, task
  revision, verifier identity, immutable image identities, and subject version.
- Both captured provider requests use `gpt-5.6-sol` with
  `reasoning.effort: low`.
- The native session records `thinkingLevel: low` and the Pi Check `Re-audit`
  marker.
- The RPC log records `started`, `prompt_sent`, `quiescent`, and `finished` on
  `transport: rpc`, with exit code 0.
- The smoke verdict has no diagnostics.
- The dashboard API returns HTTP 200, `state: completed`, `stage: done`, zero
  active cells, and zero stale cells.
- Successful preflight sealed the release under
  `results/_runs/_config-seals/pi-check@1.0.0/`.

Cell evidence paths in this note resolve from the confirmed-launch worktree.
Central run-state paths resolve from the primary checkout's `results/_runs/`.
The manifest records the absolute workspace and result path.

Successful run state:

```text
results/_runs/confirmed-launch-pi-check-1.0.0-gpt56-sol-low-pr--e86f6c24d262b60e0f7ad4cfcb24754ac2075731fe9de28767e6768e8065444d/
```

Result:

```text
results/gpt-5.6-sol/low/pi-check@1.0.0/fd-deterministic-multi-key-sorting/rep0/result.json
```

## Scope

This run proves the execution, failure-containment, provenance, registration,
and sealing paths for one versioned Pi config. It does not authorize a 1.0.0
production batch because the smoke contract did not parse the thinking evidence.
`pi-check@1.0.1` must pass its corrected structured contract before issue #22 is
complete. Each additional config release, subject version, model role, or
runtime surface still needs its own lock and smoke evidence before batch use.

# `pi-check@1.0.1` confirmed-launch validation

`pi-check@1.0.1` passed the confirmed-launch production preflight on 2026-07-26
with Pi 0.81.1 and `openai-codex/gpt-5.6-sol` at low thinking. The run executed
one explicitly approved preflight cell. The identical batch entry reused that
result and made no second subject call.

This patch release keeps the executor behavior of `pi-check@1.0.0`. It adds
structured smoke assertions that parse both provider-request captures and the
native session thinking-level record. The gate now fails before fan-out if the
model, reasoning effort, or thinking level differs from the approved plan.

Compact evidence:

```text
analysis/pi-check-1.0.1-confirmed-launch-preflight.json
```

## Approved cell

| Field | Value |
| --- | --- |
| Config | `pi-check@1.0.1` |
| Config lock | `sha256:09c816d793cc5093157e6bacc3a577f5e774445344ba3d04eb2a2e2b1c70d247` |
| Plan | `sha256:4489b49baed70f5e1b40952dc0000ad7c98b9939829b8b897374fba1b26a57d9` |
| Subject | `pi@0.81.1` |
| Model | `openai-codex/gpt-5.6-sol` |
| Thinking | `low` |
| Task | `fd-deterministic-multi-key-sorting` |
| Rep | `0` |
| Billing route | Codex subscription quota |
| Usage source | Native `session/*.jsonl` |

The operator confirmed the exact plan digest before execution. The receipt had
no warnings and declared one executor role, no secondary model roles, one
worker, zero cell retries, no automatic quota resume, and stop-on-transient
behavior. The executor bound means one Pi session per rep; that session produced
29 measured assistant completions and two captured provider requests.

## Result

The event sequence was:

1. `run_started`
2. `preflight_started`
3. `preflight_finished` with outcome `ok` and no diagnostics
4. `cell_skipped` for the identical batch entry with reason
   `successful_preflight`
5. `run_completed`

| Metric | Value |
| --- | ---: |
| Partial reward | `1.0` |
| Binary reward | `1` |
| Input tokens | `73,244` |
| Output tokens | `10,601` |
| Cache-read tokens | `622,592` |
| Total tokens | `706,437` |
| Cost | `$0.995546` |
| Agent wall time | `278.6s` |
| Turns | `29` |
| Tool calls | `31` |

`harness.parse_usage.parse_session` independently reproduced every native usage
field in `result.json`.

## Evidence agreement

The plan, manifest, status, events, result, native session, RPC log, provider
request captures, smoke diagnostics, dashboard projection, and config seal all
agree on the launch identity, config identity, model, thinking level, task, rep,
and final verdict.

Specific checks:

- Both provider request JSON objects match `model: gpt-5.6-sol` and
  `reasoning.effort: low`; the smoke contract requires at least two matches.
- The native JSONL session contains one `thinking_level_change` record with
  `thinkingLevel: low`; the smoke contract requires at least one match.
- The native session contains the extension-owned `Re-audit` marker.
- Generic and config-specific smoke evaluators return no diagnostics.
- The RPC log records `started`, `prompt_sent`, `quiescent`, and `finished` for
  RPC transport.
- `result.json` records the config lock, launch plan, harness revision, task
  revision, verifier identity, immutable image identities, and subject version.
- The dashboard API returns HTTP 200 with the exact config version, full launch
  identity, confirmed worktree path, `preflight: passed`, `1/1` batch progress,
  `state: completed`, no active cells, and no stale cells.
- Chromium rendered those same fields in the run-detail page with all requests
  returning 200 and no console errors. The review screenshot is
  `/tmp/issue22-confirmed-run-dashboard-final.png`.
- Successful preflight sealed `pi-check@1.0.1`; its lock now cannot be changed in
  place.

Cell evidence paths below resolve from the confirmed-launch worktree. Central
run-state paths resolve from the primary checkout's `results/_runs/`. The
manifest records the absolute workspace and result path.

Run state:

```text
results/_runs/confirmed-launch-pi-check-1.0.1-gpt56-sol-low-pr--f9adbc0c1229183bcd13a19d6370a51f2186b9401d6946ed0097c3e126449ab8/
```

Result:

```text
results/gpt-5.6-sol/low/pi-check@1.0.1/fd-deterministic-multi-key-sorting/rep0/result.json
```

Dashboard:

```text
http://100.112.72.93:5173/
```

## Verdict

The integrated confirmed-launch workflow is validated for this Pi release,
model, thinking level, config release, and task shape. Post-validation review
also proved that malformed JSON/JSONL smoke evidence produces an
artifact-specific failure instead of being skipped. Issue #22's production
preflight gate is satisfied. Other config releases, subject versions, model
roles, or runtime surfaces still require their own reviewed lock and smoke
evidence before batch use.

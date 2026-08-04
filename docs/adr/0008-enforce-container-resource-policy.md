# ADR-0008: Enforce container resource policy

- Status: accepted
- Date: 2026-08-04

## Context

The former host memory watchdog treated a configured cap as an alert threshold.
It killed one large child process at a time. A test command could spread memory
across many workers, keep every worker below the kill threshold, and consume
most of the host. Resetting the watchdog counter after each intervention gave
the remaining workers more time to allocate.

A confirmed launch did not record container memory limits. Pi and OMP created
subject and verifier containers without Docker cgroup limits. An executor crash
could also leave those containers running after its watchdog stopped.

## Decision

Launch-plan schema 2 includes a `resources` document:

- subject memory in GiB;
- verifier memory in GiB;
- additional swap in GiB;
- reserved host memory in GiB.

Planning records physical host RAM in runtime provenance. It rejects a launch
when `concurrency × max(subject memory, verifier memory) + host reserve` exceeds
host RAM. Runtime drift checks include physical host RAM.

Pi and OMP apply the same Docker controls to subject and verifier containers.
`--memory` limits aggregate cgroup memory. `--memory-swap` equals memory plus the
approved additional swap. Zero additional swap prevents a leaking rep from
moving its excess into host swap.

Managed containers carry labels for their run key, plan identity, cell identity,
role, state path, and host reserve. The host resource supervisor discovers
containers by label. It never kills individual processes. It fails closed when
a managed container lacks a hard limit. After sustained host pressure, it:

1. selects the run with the largest aggregate managed-container usage;
2. takes the run's exclusive container-start lock;
3. creates `<state-path>/resource-halt.json` without replacing earlier evidence;
4. re-enumerates and stops every managed container owned by that run.

Managed Docker creation takes the shared side of the same lock and checks the
halt before starting. Verifiers start detached while holding that lock, then
wait outside it so containment is never blocked by a long verifier. Confirmed
execution also checks the halt before every
preflight, new rep, and retry. A halt pauses the run before another subject
call. An operator must use
the supervisor's clearance command with a reason; clearance archives the halt
record before allowing resume.

The harness reads cgroup-v2 `memory.events`. A subject OOM kill records
`agent_resource_exhausted=true` while preserving its grade. Verifier containers
remain named until the harness captures their sidecar or Docker OOM state, then
are removed. Docker inspection failure remains an explicit unknown rather than
becoming a false no-OOM state. A verifier OOM kill records
`verifier_resource_exhausted=true`, sets `verifier_exit=memory_limit`, and makes
the grade infrastructure evidence that must be retried or excluded. Each such
attempt is recorded in `logs/verifier-resource-events.ndjson` without promoting
an invalid `result.json`.

The approved resource policy is part of normal result provenance as well as plan
identity. Automatic reuse rejects missing or changed policy; comparisons reject
mixing different recorded policies while retaining support for wholly historical
comparisons whose results all predate resource-policy recording. The supervisor
writes separate event logs and never edits canonical result files.

## Consequences

Schema-1 launch plans cannot execute under the new harness. Operators must
compile and approve a new plan; silently adding limits to an old approved plan
would change its execution behavior.

Hard cgroup limits protect the host even if the executor or supervisor exits.
The supervisor remains a second line of defense for aggregate host pressure and
misconfigured containers.

Host RAM now contributes to plan identity. Moving a plan to a different-size
host requires a new plan and approval.

Resource exhaustion becomes observable benchmark evidence. Subject exhaustion
is an outcome under the confirmed resource budget. Verifier exhaustion is not a
valid grade.

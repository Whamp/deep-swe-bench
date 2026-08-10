# Desktop OOM Incident Handoff

## Summary

On the current boot, the desktop entered prolonged global memory exhaustion that made SSH and the graphical session nearly unusable. The immediate workload was an unbounded Deep SWE / pi-check container running many Vitest workers. This appears related to the agent/database work being driven from Labrat, but the exact Labrat launch path has **not yet been traced in source**.

This looked like a memory leak from outside, but the available kernel evidence more specifically shows runaway aggregate memory from parallel test workers. Treat a true per-worker leak as unproven until the launcher and workload are reproduced under measurement.

The Qwen vision container was not running and was not responsible.

## Impact

- Desktop: 64 GB class machine (`free` reports about 60 GiB usable RAM).
- SSH mostly timed out, including during SSH banner exchange.
- The kernel repeatedly invoked global OOM handling for roughly 34 minutes.
- OOM selection killed unrelated user-session infrastructure, including user `systemd`, D-Bus, Hermes, Herdr, and ydotool processes, worsening remote recoverability.
- Swap reached about 16 GiB used (13.5 GiB swapfile plus 3.2 GiB zram observed after recovery).

## Offending container evidence

Docker container from the OOM cgroup:

```text
id=593e84d29ef589102ee027a8fc0c1d5be696c66417d258c17f1b9dd03020b281
name=dsw-pi-check-1.3.0-meriyah-explicit-resource-declarations-r0-2853486
image=deep-swe-pi:v4-pi0830-tools-kh7398skqnxqwg9hbmdj7ncmk1822aa0-v1.1
working_dir=/app
final_status=exited
oom_killed=true
```

`docker stats` reported every unrestricted container against the host-wide `60.6GiB` limit, so this workload did not have an effective container memory ceiling.

Kernel OOM records repeatedly named `node (vitest N)` processes in this container. Examples:

```text
12:33:04  vitest 10  anon RSS ~2.71 GiB  killed
12:36:10  vitest 10  anon RSS ~2.41 GiB  killed
12:38:29  vitest 8   anon RSS ~1.25 GiB  killed
12:41:56  vitest 12  anon RSS ~1.23 GiB  killed
13:06:33  vitest 15  anon RSS ~2.08 GiB  killed
```

The worker numbering and repeated multi-gigabyte RSS values indicate enough concurrent Vitest workers to exhaust the host in aggregate.

## Emergency action and why recovery was slow

From the laptop, SSH was retried until this command could run:

```bash
sudo sh -c 'echo f > /proc/sysrq-trigger'
```

The kernel confirms it worked:

```text
13:06:35 kernel: sysrq: Manual OOM execution
```

However, that manual OOM decision killed `node-MainThread` in `deep-swe-bench-vite.service`, with only tens of MiB resident at selection time. It did not immediately remove all large container workers. Earlier OOM decisions also selected small processes with positive `oom_score_adj` while large container workers continued running. Combined with reclaim and swap thrashing, this explains why successful SysRq execution did not restore responsiveness immediately.

## State after recovery

Read-only probe at approximately 13:08 on the same boot:

```text
RAM: 60 GiB total, 10 GiB used, 47 GiB free, 49 GiB available
Swap: 62 GiB total, 16 GiB used
Load average: 69.06, 140.19, 163.08
Process states: 3 runnable, 361 sleeping, 203 idle, 6 zombies, 0 D-state
Vitest/Labrat processes: none found
```

The high load averages were historical/decaying; there were no tasks stuck in uninterruptible I/O at that probe.

## Recommended investigation

1. Trace the code that creates containers named `dsw-pi-check-*` and determine how this run was initiated from Labrat or its agent/evaluation tooling.
2. Record the effective `docker create/run` options and Vitest command for the failed run.
3. Determine whether concurrency alone explains the footprint or whether individual Vitest workers grow without bound over time.
4. Check why worker processes in the container were less attractive OOM victims than unrelated user-session services.
5. Preserve enough run metadata to associate a container OOM with the originating Labrat task/session.

Useful evidence commands:

```bash
journalctl -k -b --no-pager | grep -Ei 'sysrq|oom|out of memory|killed process'
docker inspect 593e84d29ef589102ee027a8fc0c1d5be696c66417d258c17f1b9dd03020b281
docker events --since '<incident start>' --until '<incident end>'
```

## Recommended guardrails

Apply limits at the container boundary so failure remains local to the disposable workload rather than becoming a host-global OOM. Initial values to evaluate, not final requirements:

```text
memory: 16 GiB
memory+swap: 20 GiB
pids limit: 512
Vitest max workers: 4
```

Equivalent Docker flags would be:

```bash
--memory=16g --memory-swap=20g --pids-limit=512
```

Also pass an explicit Vitest worker limit (for example `--maxWorkers=4`) rather than relying on CPU-derived defaults.

Acceptance checks for a fix should include:

- A test proving every disposable evaluation container receives a finite memory and PID limit.
- A test proving Vitest concurrency is bounded.
- A stress/reproduction run where the workload exceeds its budget and only its container fails.
- Confirmation that SSH, the user session, and unrelated services remain responsive during that failure.
- Clear surfaced diagnostics that identify container OOM termination and the originating task/session.

## Repository state warning

Before this note was added, `AGENTS.md` was already modified. That existing work was not inspected as a diff or changed during this handoff. Preserve it.

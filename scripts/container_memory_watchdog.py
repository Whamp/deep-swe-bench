#!/usr/bin/env python3
"""Host-side memory watchdog for active DeepSWE benchmark containers.

Protects already-running benchmark cells by monitoring Docker containers whose
names start with ``dsw-``. When a container stays over an emergency memory cap
for several consecutive samples, the watchdog kills the largest non-protected
process inside the container (TERM, then KILL after a grace period). It does not
mutate result.json or any official benchmark artifacts.

Default policy is intentionally conservative:
  * target only dsw-* containers
  * protect pi/sleep/shell helper processes
  * alert-only if the biggest memory user is pi or no large killable child exists
  * require sustained over-cap samples before acting
  * write separate manual_interventions and peak logs under runs/

Use --dry-run first. In dry-run, the script logs what it would do but sends no
signals.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
import math
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

REPO = Path(__file__).resolve().parent.parent
DEFAULT_LOG_DIR = REPO / "runs" / "container-memory-watchdog"
PROTECTED_NAMES = {"pi", "sleep", "sh", "bash", "dash", "ps", "head", "tail", "cat", "grep", "awk", "sed"}
PROTECTED_STAT_PREFIXES = {"Z"}  # zombies have no memory to free
CONTAINER_RE = re.compile(r"^dsw-(?P<body>.+)-r(?P<rep>\d+)-(?P<runpid>\d+)$")


@dataclass
class ContainerStat:
    name: str
    mem_bytes: int
    mem_limit_bytes: int | None
    cpu_percent: float | None


@dataclass
class ProcessInfo:
    pid: int
    ppid: int
    stat: str
    etime: str
    pcpu: float
    pmem: float
    rss_kib: int
    command: str

    @property
    def rss_bytes(self) -> int:
        return self.rss_kib * 1024

    @property
    def exe_name(self) -> str:
        if not self.command:
            return ""
        first = self.command.split()[0]
        return Path(first).name.strip("[]")

    @property
    def protected(self) -> bool:
        if any(self.stat.startswith(prefix) for prefix in PROTECTED_STAT_PREFIXES):
            return True
        return self.exe_name in PROTECTED_NAMES


@dataclass
class PeakState:
    container: str
    first_seen: str
    last_seen: str
    samples: int = 0
    peak_container_mem_bytes: int = 0
    peak_process_rss_bytes: int = 0
    peak_process_pid: int | None = None
    peak_process_command: str = ""
    interventions: int = 0
    alerts: int = 0
    dry_run: bool = False
    cell: dict = field(default_factory=dict)

    def update(self, now: str, stat: ContainerStat, top_process: ProcessInfo | None) -> None:
        self.last_seen = now
        self.samples += 1
        if stat.mem_bytes > self.peak_container_mem_bytes:
            self.peak_container_mem_bytes = stat.mem_bytes
        if top_process and top_process.rss_bytes > self.peak_process_rss_bytes:
            self.peak_process_rss_bytes = top_process.rss_bytes
            self.peak_process_pid = top_process.pid
            self.peak_process_command = top_process.command


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def append_jsonl(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a") as f:
        f.write(json.dumps(obj, sort_keys=True) + "\n")


def run(cmd: list[str], timeout: float = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)


def parse_size_bytes(value: str) -> int:
    """Parse Docker-ish sizes such as '55.59MiB', '1.2GiB', or '1024kB'."""
    s = value.strip().replace(" ", "")
    m = re.match(r"^([0-9]+(?:\.[0-9]+)?)([A-Za-z]+)?$", s)
    if not m:
        raise ValueError(f"cannot parse size: {value!r}")
    amount = float(m.group(1))
    unit = (m.group(2) or "B").lower()
    factors = {
        "b": 1,
        "kb": 1000,
        "mb": 1000**2,
        "gb": 1000**3,
        "tb": 1000**4,
        "kib": 1024,
        "mib": 1024**2,
        "gib": 1024**3,
        "tib": 1024**4,
    }
    if unit not in factors:
        raise ValueError(f"unknown size unit {unit!r} in {value!r}")
    return int(amount * factors[unit])


def parse_cpu_percent(value: str) -> float | None:
    value = value.strip().rstrip("%")
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def list_container_names(pattern: str) -> list[str]:
    r = run(["docker", "ps", "--format", "{{.Names}}"])
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip() or "docker ps failed")
    return sorted(name for name in r.stdout.splitlines() if fnmatch.fnmatch(name, pattern))


def _parse_stats_output(stdout: str) -> list[ContainerStat]:
    stats: list[ContainerStat] = []
    for line in stdout.splitlines():
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        name, mem_usage, cpu = parts
        used_s, _, limit_s = mem_usage.partition("/")
        used = parse_size_bytes(used_s.strip())
        limit = parse_size_bytes(limit_s.strip()) if limit_s.strip() else None
        stats.append(ContainerStat(name=name, mem_bytes=used, mem_limit_bytes=limit, cpu_percent=parse_cpu_percent(cpu)))
    return stats


def read_container_stats(names: list[str]) -> list[ContainerStat]:
    if not names:
        return []
    # Use tab-separated fields because Docker's JSON formatting is not
    # consistent across installed versions. Containers can exit between
    # `docker ps` and `docker stats`; fall back to per-container reads and skip
    # vanished containers instead of failing the watchdog.
    fmt = "{{.Name}}\t{{.MemUsage}}\t{{.CPUPerc}}"
    r = run(["docker", "stats", "--no-stream", "--format", fmt, *names], timeout=60)
    if r.returncode == 0:
        return _parse_stats_output(r.stdout)
    stats: list[ContainerStat] = []
    for name in names:
        one = run(["docker", "stats", "--no-stream", "--format", fmt, name], timeout=20)
        if one.returncode != 0:
            continue
        stats.extend(_parse_stats_output(one.stdout))
    return stats


def parse_ps_line(line: str) -> ProcessInfo | None:
    parts = line.split(None, 7)
    if len(parts) < 8:
        return None
    try:
        return ProcessInfo(
            pid=int(parts[0]),
            ppid=int(parts[1]),
            stat=parts[2],
            etime=parts[3],
            pcpu=float(parts[4]),
            pmem=float(parts[5]),
            rss_kib=int(parts[6]),
            command=parts[7],
        )
    except ValueError:
        return None


def list_processes(container: str) -> list[ProcessInfo]:
    r = run(["docker", "exec", container, "ps", "-eo", "pid,ppid,stat,etime,pcpu,pmem,rss,args", "--sort=-rss"], timeout=20)
    if r.returncode != 0:
        return []
    processes: list[ProcessInfo] = []
    for line in r.stdout.splitlines()[1:]:
        p = parse_ps_line(line)
        if p is not None:
            processes.append(p)
    return processes


def infer_cell(container_name: str, config_names: Iterable[str]) -> dict:
    m = CONTAINER_RE.match(container_name)
    if not m:
        return {}
    body = m.group("body")
    rep = int(m.group("rep"))
    runpid = int(m.group("runpid"))
    best_config = ""
    task = ""
    for config in sorted(config_names, key=len, reverse=True):
        prefix = config + "-"
        if body.startswith(prefix):
            best_config = config
            task = body[len(prefix):]
            break
    return {"config": best_config, "task": task, "rep": rep, "container_run_pid": runpid}


def load_config_names() -> list[str]:
    configs_dir = REPO / "configs"
    if not configs_dir.exists():
        return []
    return sorted(p.name for p in configs_dir.iterdir() if p.is_dir())


def choose_kill_candidate(processes: list[ProcessInfo], min_rss_bytes: int) -> tuple[ProcessInfo | None, str]:
    if not processes:
        return None, "no_processes"
    top = max(processes, key=lambda p: p.rss_bytes)
    if top.exe_name == "pi":
        return None, "top_process_is_pi_alert_only"
    for p in sorted(processes, key=lambda p: p.rss_bytes, reverse=True):
        if p.protected:
            continue
        if p.rss_bytes < min_rss_bytes:
            return None, "largest_killable_below_min_rss"
        return p, "killable"
    return None, "no_killable_process"


def signal_process(container: str, pid: int, sig: str) -> tuple[bool, str]:
    r = run(["docker", "exec", container, "kill", sig, str(pid)], timeout=10)
    ok = r.returncode == 0
    return ok, (r.stdout + r.stderr).strip()


def process_alive(container: str, pid: int) -> bool:
    r = run(["docker", "exec", container, "sh", "-lc", f"kill -0 {pid} 2>/dev/null"], timeout=10)
    return r.returncode == 0


class Watchdog:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.cap_bytes = int(args.cap_gb * 1024**3)
        self.min_kill_rss_bytes = int((args.min_kill_rss_gb if args.min_kill_rss_gb is not None else args.cap_gb / 2) * 1024**3)
        self.config_names = load_config_names()
        self.over_counts: dict[str, int] = {}
        self.peaks: dict[str, PeakState] = {}
        self.seen_pids: set[tuple[str, int]] = set()
        self.stop_requested = False
        self.manual_log = Path(args.manual_log)
        self.peak_log = Path(args.peak_log)

    def log_event(self, event: str, **fields) -> None:
        obj = {"ts": now_iso(), "event": event, **fields}
        append_jsonl(self.manual_log, obj)

    def log_peak(self, peak: PeakState, event: str) -> None:
        append_jsonl(self.peak_log, {
            "ts": now_iso(),
            "event": event,
            "container": peak.container,
            "cell": peak.cell,
            "first_seen": peak.first_seen,
            "last_seen": peak.last_seen,
            "samples": peak.samples,
            "peak_container_mem_bytes": peak.peak_container_mem_bytes,
            "peak_process_rss_bytes": peak.peak_process_rss_bytes,
            "peak_process_pid": peak.peak_process_pid,
            "peak_process_command": peak.peak_process_command,
            "interventions": peak.interventions,
            "alerts": peak.alerts,
            "dry_run": peak.dry_run,
        })

    def update_peaks(self, names_seen: set[str], stats_by_name: dict[str, ContainerStat], processes_by_name: dict[str, list[ProcessInfo]]) -> None:
        now = now_iso()
        for name in names_seen:
            if name not in self.peaks:
                self.peaks[name] = PeakState(
                    container=name,
                    first_seen=now,
                    last_seen=now,
                    dry_run=self.args.dry_run,
                    cell=infer_cell(name, self.config_names),
                )
            top = max(processes_by_name.get(name, []), key=lambda p: p.rss_bytes, default=None)
            self.peaks[name].update(now, stats_by_name[name], top)
        gone = [name for name in self.peaks if name not in names_seen]
        for name in gone:
            self.log_peak(self.peaks.pop(name), "container_finished_or_disappeared")
            self.over_counts.pop(name, None)

    def sample_once(self) -> None:
        names = list_container_names(self.args.target)
        stats = read_container_stats(names)
        stats_by_name = {s.name: s for s in stats}
        processes_by_name = {name: list_processes(name) for name in stats_by_name}
        self.update_peaks(set(stats_by_name), stats_by_name, processes_by_name)

        for stat in stats:
            processes = processes_by_name.get(stat.name, [])
            over = stat.mem_bytes >= self.cap_bytes
            self.over_counts[stat.name] = self.over_counts.get(stat.name, 0) + 1 if over else 0
            if not over or self.over_counts[stat.name] < self.args.consecutive:
                continue
            candidate, reason = choose_kill_candidate(processes, self.min_kill_rss_bytes)
            top = max(processes, key=lambda p: p.rss_bytes, default=None)
            common = {
                "container": stat.name,
                "cell": infer_cell(stat.name, self.config_names),
                "container_mem_bytes": stat.mem_bytes,
                "cap_bytes": self.cap_bytes,
                "over_count": self.over_counts[stat.name],
                "top_pid": top.pid if top else None,
                "top_rss_bytes": top.rss_bytes if top else None,
                "top_command": top.command if top else "",
                "reason": reason,
                "dry_run": self.args.dry_run,
            }
            if candidate is None:
                if self.peaks.get(stat.name):
                    self.peaks[stat.name].alerts += 1
                self.log_event("over_cap_alert_only", **common)
                # Avoid logging the same alert every 5s forever.
                self.over_counts[stat.name] = 0
                continue

            pid_key = (stat.name, candidate.pid)
            if pid_key in self.seen_pids:
                self.log_event("over_cap_already_handled_pid", candidate_pid=candidate.pid, candidate_command=candidate.command, **common)
                self.over_counts[stat.name] = 0
                continue
            self.seen_pids.add(pid_key)
            if self.peaks.get(stat.name):
                self.peaks[stat.name].interventions += 1
            event_fields = {
                **common,
                "candidate_pid": candidate.pid,
                "candidate_rss_bytes": candidate.rss_bytes,
                "candidate_command": candidate.command,
                "min_kill_rss_bytes": self.min_kill_rss_bytes,
            }
            if self.args.dry_run:
                self.log_event("would_kill_process", **event_fields)
                self.over_counts[stat.name] = 0
                continue

            ok, output = signal_process(stat.name, candidate.pid, "-TERM")
            self.log_event("sent_term", term_ok=ok, term_output=output, **event_fields)
            time.sleep(self.args.grace)
            if process_alive(stat.name, candidate.pid):
                ok, output = signal_process(stat.name, candidate.pid, "-KILL")
                self.log_event("sent_kill", kill_ok=ok, kill_output=output, **event_fields)
            else:
                self.log_event("process_exited_after_term", **event_fields)
            self.over_counts[stat.name] = 0

    def flush_peaks(self, event: str = "watchdog_shutdown_peak") -> None:
        for peak in list(self.peaks.values()):
            self.log_peak(peak, event)

    def run(self) -> int:
        self.manual_log.parent.mkdir(parents=True, exist_ok=True)
        self.log_event(
            "watchdog_start",
            target=self.args.target,
            cap_bytes=self.cap_bytes,
            interval=self.args.interval,
            consecutive=self.args.consecutive,
            grace=self.args.grace,
            min_kill_rss_bytes=self.min_kill_rss_bytes,
            dry_run=self.args.dry_run,
            pid=os.getpid(),
        )
        if self.args.pidfile:
            Path(self.args.pidfile).parent.mkdir(parents=True, exist_ok=True)
            Path(self.args.pidfile).write_text(str(os.getpid()))
        try:
            iterations = 0
            while not self.stop_requested:
                self.sample_once()
                iterations += 1
                if self.args.once or (self.args.iterations and iterations >= self.args.iterations):
                    break
                time.sleep(self.args.interval)
        finally:
            self.flush_peaks()
            self.log_event("watchdog_stop", dry_run=self.args.dry_run, pid=os.getpid())
            if self.args.pidfile:
                Path(self.args.pidfile).unlink(missing_ok=True)
        return 0


def self_test() -> None:
    assert parse_size_bytes("1GiB") == 1024**3
    assert parse_size_bytes("1.5MiB") == int(1.5 * 1024**2)
    assert parse_size_bytes("1000kB") == 1_000_000
    p = parse_ps_line("75 74 R 16:27 95.7 76.6 49555192 python3 script.py")
    assert p and p.pid == 75 and p.rss_bytes == 49555192 * 1024 and not p.protected
    pi = parse_ps_line("25 0 Ssl 35:34 0.5 0.0 150000 pi")
    assert pi and pi.protected
    cand, reason = choose_kill_candidate([pi, p], min_rss_bytes=4 * 1024**3)
    assert cand and cand.pid == 75 and reason == "killable"
    cand, reason = choose_kill_candidate([pi], min_rss_bytes=1)
    assert cand is None and reason == "top_process_is_pi_alert_only"
    configs = ["baseline", "observational-memory", "observational-memory-gpt54mini-off"]
    cell = infer_cell("dsw-observational-memory-gpt54mini-off-effect-sse-httpapi-streaming-r2-3713", configs)
    assert cell["config"] == "observational-memory-gpt54mini-off"
    assert cell["task"] == "effect-sse-httpapi-streaming"
    assert cell["rep"] == 2
    print("self_test_ok")


def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--target", default="dsw-*", help="Docker container name glob to monitor (default: dsw-*)")
    ap.add_argument("--cap-gb", type=float, default=8.0, help="sustained container memory cap in GiB (default: 8)")
    ap.add_argument("--min-kill-rss-gb", type=float, default=None,
                    help="minimum RSS for a kill candidate in GiB (default: cap/2; prevents killing tiny processes when memory is cache)")
    ap.add_argument("--interval", type=float, default=5.0, help="sample interval seconds (default: 5)")
    ap.add_argument("--consecutive", type=int, default=3, help="samples over cap before action (default: 3)")
    ap.add_argument("--grace", type=float, default=10.0, help="seconds after TERM before KILL (default: 10)")
    ap.add_argument("--dry-run", action="store_true", help="log would-kill events but do not signal processes")
    ap.add_argument("--once", action="store_true", help="take one sample then exit")
    ap.add_argument("--iterations", type=int, default=0, help="run this many samples then exit (0 = until stopped)")
    ap.add_argument("--manual-log", default=str(DEFAULT_LOG_DIR / "manual_interventions.ndjson"),
                    help="separate intervention/alert log path")
    ap.add_argument("--peak-log", default=str(DEFAULT_LOG_DIR / "container_peaks.ndjson"),
                    help="separate peak memory summary log path")
    ap.add_argument("--pidfile", default=str(DEFAULT_LOG_DIR / "watchdog.pid"), help="pidfile path")
    ap.add_argument("--self-test", action="store_true", help="run built-in parser/policy tests and exit")
    args = ap.parse_args(argv)
    if args.consecutive < 1:
        ap.error("--consecutive must be >= 1")
    if args.interval <= 0:
        ap.error("--interval must be > 0")
    if args.cap_gb <= 0:
        ap.error("--cap-gb must be > 0")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    if args.self_test:
        self_test()
        return 0
    watchdog = Watchdog(args)

    def request_stop(signum, frame):  # noqa: ARG001
        watchdog.stop_requested = True

    signal.signal(signal.SIGTERM, request_stop)
    signal.signal(signal.SIGINT, request_stop)
    return watchdog.run()


if __name__ == "__main__":
    raise SystemExit(main())

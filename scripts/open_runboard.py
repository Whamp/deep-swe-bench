#!/usr/bin/env python3
"""Open or reuse a Herdr tab tailing a benchmark runboard.

The common case is a live harness/run_batch.py log at runs/<run>/track.out.
This helper owns the Herdr ceremony so the runboard skill can stay short:
verify Herdr, discover the current workspace, reuse an exact tail pane when one
exists, otherwise create a tab, run tail, and prove the pane is visibly live.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
RunCmd = Callable[[list[str]], subprocess.CompletedProcess[str]]

RUNBOARD_LINE_RE = re.compile(
    r"(?:^|\n)(?:"
    r"running\s+(?:\d+|\?)\s+cells:"
    r"|\[\d+/(?:\d+|\?)\]\s+.+?\s+/\s+.+?\s+/\s+rep\d+\s+(?:ok|empty|timeout|transient|exit=\d+)"
    r")"
)
_VALUE_OPTIONS = {
    "-n",
    "--lines",
    "-c",
    "--bytes",
    "-s",
    "--sleep-interval",
    "--pid",
    "--max-unchanged-stats",
}
_FLAG_OPTIONS = {
    "-f",
    "-F",
    "--follow",
    "--retry",
    "-q",
    "--quiet",
    "-v",
    "--verbose",
    "-z",
    "--zero-terminated",
}


class RunboardError(RuntimeError):
    pass


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, capture_output=True, text=True, check=False)


def _checked_json(cmd: list[str], run: RunCmd = _run) -> dict[str, Any]:
    proc = run(cmd)
    if proc.returncode != 0:
        raise RunboardError(f"command failed ({proc.returncode}): {' '.join(cmd)}\n{proc.stderr.strip()}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RunboardError(f"command did not return JSON: {' '.join(cmd)}") from exc


def current_workspace(run: RunCmd = _run) -> str:
    panes = _checked_json(["herdr", "pane", "list"], run)["result"]["panes"]
    for pane in panes:
        if pane.get("focused"):
            return str(pane["workspace_id"])
    raise RunboardError("no focused Herdr pane found")


def workspace_panes(workspace: str, run: RunCmd = _run) -> list[str]:
    panes = _checked_json(["herdr", "pane", "list", "--workspace", workspace], run)["result"]["panes"]
    return [str(pane["pane_id"]) for pane in panes]


def tab_root_pane(tab_json: dict[str, Any]) -> str:
    return str(tab_json["result"]["root_pane"]["pane_id"])


def tail_targets(argv: list[str]) -> list[str]:
    """Return path arguments from common `tail -n 60 -f path` forms."""
    if not argv or Path(argv[0]).name != "tail":
        return []
    targets: list[str] = []
    i = 1
    while i < len(argv):
        arg = argv[i]
        if arg in _VALUE_OPTIONS:
            i += 2
            continue
        if arg in _FLAG_OPTIONS:
            i += 1
            continue
        if any(arg.startswith(prefix + "=") for prefix in _VALUE_OPTIONS | _FLAG_OPTIONS if prefix.startswith("--")):
            i += 1
            continue
        if re.fullmatch(r"-[nc]\d+", arg):
            i += 1
            continue
        if arg.startswith("-") and arg != "-":
            i += 1
            continue
        targets.append(arg)
        i += 1
    return targets


def _resolve_from(cwd: str | None, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = Path(cwd or os.getcwd()) / path
    return path.resolve(strict=False)


def process_tails_track(process_info: dict[str, Any], track: Path) -> bool:
    target = track.resolve(strict=False)
    for proc in process_info.get("foreground_processes") or []:
        argv = proc.get("argv") or []
        cwd = proc.get("cwd")
        for candidate in tail_targets([str(part) for part in argv]):
            if _resolve_from(cwd, candidate) == target:
                return True
    return False


def pane_process_info(pane: str, run: RunCmd = _run) -> dict[str, Any] | None:
    proc = run(["herdr", "pane", "process-info", "--pane", pane])
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)["result"]["process_info"]
    except Exception:
        return None


def pane_visible(pane: str, lines: int, run: RunCmd = _run) -> str:
    proc = run(["herdr", "pane", "read", pane, "--source", "visible", "--lines", str(lines)])
    return proc.stdout if proc.returncode == 0 else ""


def visible_has_runboard(text: str) -> bool:
    return bool(RUNBOARD_LINE_RE.search(text))


def find_existing_runboard(workspace: str, track: Path, *, lines: int, run: RunCmd = _run) -> tuple[str, str] | None:
    for pane in workspace_panes(workspace, run):
        info = pane_process_info(pane, run)
        if not info or not process_tails_track(info, track):
            continue
        visible = pane_visible(pane, lines, run)
        if visible_has_runboard(visible):
            return pane, visible
    return None


def create_runboard_tab(
    *,
    workspace: str,
    track: Path,
    label: str,
    cwd: Path,
    lines: int,
    run: RunCmd = _run,
) -> str:
    tab_json = _checked_json(["herdr", "tab", "create", "--workspace", workspace, "--label", label], run)
    pane = tab_root_pane(tab_json)
    cmd = f"cd {shlex.quote(str(cwd))} && tail -n {lines} -f {shlex.quote(str(track))}"
    proc = run(["herdr", "pane", "run", pane, cmd])
    if proc.returncode != 0:
        raise RunboardError(f"failed to start tail in pane {pane}: {proc.stderr.strip()}")
    return pane


def wait_until_live(pane: str, track: Path, *, lines: int, timeout_s: float, run: RunCmd = _run) -> str:
    deadline = time.monotonic() + timeout_s
    last_visible = ""
    while True:
        info = pane_process_info(pane, run)
        last_visible = pane_visible(pane, lines, run)
        if info and process_tails_track(info, track) and visible_has_runboard(last_visible):
            return last_visible
        if time.monotonic() >= deadline:
            raise RunboardError(
                f"pane {pane} did not become a verified runboard for {track}; "
                "need exact tail process plus visible runboard header/progress"
            )
        time.sleep(0.2)


def default_label(track: Path) -> str:
    parts = track.parts
    if len(parts) >= 3 and parts[-1] == "track.out":
        return f"{parts[-2]} track"
    return f"{track.stem or 'run'} track"


def resolve_track(args: argparse.Namespace) -> Path:
    if bool(args.run) == bool(args.track):
        raise RunboardError("pass exactly one of --run or --track")
    track = ROOT / "runs" / args.run / "track.out" if args.run else Path(args.track)
    if not track.is_absolute():
        track = ROOT / track
    if not track.exists():
        raise RunboardError(f"track file not found: {track}")
    return track


def main(argv: list[str] | None = None, run: RunCmd = _run) -> int:
    parser = argparse.ArgumentParser(description="Open or reuse a Herdr tab tailing runs/<run>/track.out")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--run", help="run name under runs/<run>/track.out")
    group.add_argument("--track", help="track file path, usually runs/<run>/track.out")
    parser.add_argument("--label", help="Herdr tab label")
    parser.add_argument("--workspace", help="Herdr workspace id; default is focused pane's workspace")
    parser.add_argument("--cwd", default=str(ROOT), help="command cwd for tail tab")
    parser.add_argument("--lines", type=int, default=60, help="tail/read line count")
    parser.add_argument("--verify-timeout", type=float, default=3.0, help="seconds to wait for visible proof")
    args = parser.parse_args(argv)

    if os.environ.get("HERDR_ENV") != "1":
        raise RunboardError("not running inside a Herdr-managed pane (HERDR_ENV != 1)")

    track = resolve_track(args)
    workspace = args.workspace or current_workspace(run)
    label = args.label or default_label(track)

    reused = False
    existing = find_existing_runboard(workspace, track, lines=args.lines, run=run)
    if existing:
        pane, visible = existing
        reused = True
    else:
        cwd = Path(args.cwd).resolve(strict=False)
        tail_track = track.relative_to(cwd) if track.is_relative_to(cwd) else track
        pane = create_runboard_tab(
            workspace=workspace,
            track=tail_track,
            label=label,
            cwd=cwd,
            lines=args.lines,
            run=run,
        )
        visible = wait_until_live(pane, track, lines=args.lines, timeout_s=args.verify_timeout, run=run)

    print(json.dumps({
        "status": "live",
        "workspace": workspace,
        "pane": pane,
        "track": str(track.relative_to(ROOT) if track.is_relative_to(ROOT) else track),
        "label": label,
        "reused": reused,
        "visible_preview": "\n".join(visible.splitlines()[-8:]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RunboardError as exc:
        print(f"open_runboard: {exc}", file=sys.stderr)
        raise SystemExit(2)

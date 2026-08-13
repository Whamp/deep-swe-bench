#!/usr/bin/env python3
"""Finalize the preserved Kombu rep2 patch as a verifier-timeout failure."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from harness import parse_usage
from harness.container_resources import read_container_memory_events
from harness.launch_execution import _confirmed_result_record, _confirmed_subject_cell
from harness.launch_planning import parse_launch_plan_json
from harness.lib import load_task, result_record
from harness.run_state import atomic_write_json

PLAN_PATH = REPO / "analysis/testing-skills-1.2.0-full113-resume/launch-plan.json"
EXPECTED_PLAN_IDENTITY = (
    "sha256:bd70919645618f52ac446a18773ccc60a657d4737c10e49bd059947673503e71"
)
EXPECTED_PATCH_IDENTITY = (
    "sha256:c43e2100bca2e061f2dcd62bc683c773f95f37aa0f0844a686970067e5cbd284"
)
EXPECTED_SESSION_IDENTITY = (
    "sha256:5b31137b26d9ee7e9e7a591a0d1b01831901dbce567b5a9c59371aecbd6753c2"
)
TASK = "kombu-virtual-queue-dead-lettering"
CONFIG = "testing-skills@1.2.0"
REP = 2
FOCUSED_TEST = (
    "t/unit/transport/test_filesystem.py::"
    "test_FilesystemTransport::test_produce_consume_noack"
)


def file_identity(path: Path) -> str:
    """Return a SHA-256 artifact identity."""
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def selected_plan_cell(document: dict[str, Any]) -> tuple[dict[str, Any], Any]:
    """Return the exact approved Kombu candidate cell and resolved launch cell."""
    matches = [
        cell
        for cell in document["batchCells"]
        if cell["task"] == TASK and cell["config"] == CONFIG and cell["rep"] == REP
    ]
    if len(matches) != 1:
        raise ValueError(f"expected one approved recovery cell, found {len(matches)}")
    return matches[0], _confirmed_subject_cell(document, matches[0])


def validate_preserved_attempt(result_dir: Path) -> Path:
    """Require the exact saved patch/session and an absent canonical result."""
    result_path = result_dir / "result.json"
    if result_path.exists():
        raise FileExistsError(f"canonical result already exists: {result_path}")
    patch = result_dir / "artifacts/model.patch"
    if file_identity(patch) != EXPECTED_PATCH_IDENTITY:
        raise ValueError("preserved Kombu patch identity changed")
    sessions = sorted((result_dir / "session").glob("*.jsonl"))
    if len(sessions) != 1 or file_identity(sessions[0]) != EXPECTED_SESSION_IDENTITY:
        raise ValueError("preserved Kombu session identity changed")
    rpc_records = [
        json.loads(line)
        for line in (result_dir / "logs/pi-rpc-runner.jsonl").read_text().splitlines()
    ]
    finished = [record for record in rpc_records if record.get("event") == "finished"]
    if len(finished) != 1 or finished[0].get("exit_code") != 0:
        raise ValueError("preserved Kombu agent did not finish cleanly")
    return sessions[0]


def replay_hanging_filesystem_test(
    *,
    result_dir: Path,
    verifier_image: str,
    evidence_dir: Path,
) -> dict[str, object]:
    """Require the saved patch to time out in the named filesystem test."""
    container_name = f"dswb-kombu-timeout-recovery-{uuid.uuid4().hex[:12]}"
    patch = result_dir / "artifacts/model.patch"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = evidence_dir / "focused-verifier-timeout.stdout.txt"
    run = [
        "docker",
        "run",
        "-d",
        "--name",
        container_name,
        "--memory",
        "4g",
        "--memory-swap",
        "4g",
        "--network",
        "none",
        "--platform",
        "linux/amd64",
        "--entrypoint",
        "bash",
        verifier_image,
        "-lc",
        "sleep infinity",
    ]
    subprocess.run(run, capture_output=True, text=True, check=True)
    try:
        labels = json.loads(
            subprocess.run(
                [
                    "docker",
                    "inspect",
                    container_name,
                    "--format",
                    "{{json .Config.Labels}}",
                ],
                capture_output=True,
                text=True,
                check=True,
            ).stdout
        )
        if labels and labels.get("deep-swe-bench.managed") == "true":
            raise RuntimeError("recovery container unexpectedly has the managed label")
        subprocess.run(
            ["docker", "cp", str(patch), f"{container_name}:/tmp/model.patch"],
            capture_output=True,
            text=True,
            check=True,
        )
        subprocess.run(
            [
                "docker",
                "exec",
                container_name,
                "bash",
                "-lc",
                "cd /app && git apply /tmp/model.patch",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        command = (
            "cd /app && timeout 8s pytest "
            f"{FOCUSED_TEST} -vv -s -o faulthandler_timeout=3"
        )
        replay = subprocess.run(
            ["docker", "exec", container_name, "bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        stdout = replay.stdout + replay.stderr
        stdout_path.write_text(stdout)
        if replay.returncode != 124:
            raise RuntimeError(
                f"focused verifier did not time out: exit={replay.returncode}"
            )
        if FOCUSED_TEST not in stdout or "drain_events" not in stdout:
            raise RuntimeError(
                "focused verifier timeout did not reproduce the known hang"
            )
        memory_events = read_container_memory_events(container_name)
        if int(memory_events.get("oom", 0)) or int(memory_events.get("oom_kill", 0)):
            raise RuntimeError(
                f"focused verifier replay exhausted memory: {memory_events}"
            )
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_name],
            capture_output=True,
            check=False,
        )
    evidence = {
        "focusedTest": FOCUSED_TEST,
        "memoryLimitGiB": 4.0,
        "network": "none",
        "patchIdentity": EXPECTED_PATCH_IDENTITY,
        "replayExit": replay.returncode,
        "replayStdout": str(stdout_path.relative_to(REPO)),
        "verifierMemoryEvents": memory_events,
    }
    atomic_write_json(evidence_dir / "focused-verifier-timeout.json", evidence)
    return evidence


def session_wall_seconds(session_path: Path) -> float:
    """Derive agent wall time from the preserved native session timestamps."""
    records = [json.loads(line) for line in session_path.read_text().splitlines()]
    start = datetime.fromisoformat(records[0]["timestamp"])
    end = datetime.fromisoformat(records[-1]["timestamp"])
    return round((end - start).total_seconds(), 1)


def build_timeout_result(
    *,
    document: dict[str, Any],
    launch_cell: Any,
    result_dir: Path,
    session_path: Path,
    replay_evidence: dict[str, object],
) -> dict[str, object]:
    """Build the canonical timeout record from preserved native evidence."""
    task = load_task(TASK)
    usage = parse_usage.parse(session_dir=result_dir / "session")
    subject_events = json.loads(
        (result_dir / "logs/subject-memory-events.json").read_text()
    )
    settings = json.loads((launch_cell.config_leaf / "settings.json").read_text())
    bare = result_record(
        task,
        CONFIG,
        document["model"],
        REP,
        arm_pi_flags=[],
        system_preamble_chars=0,
        orchestration_chars=0,
        append_system_prompt_chars=0,
        arm_settings=settings,
        arm_advisor=None,
        arm_models=None,
        thinking_level=document["thinking"],
        openai_codex_oauth_passed=True,
        initial_context_capture_enabled=True,
        initial_context_capture_path="initial_context",
        reward_binary=-1,
        reward_partial=0.0,
        f2p=None,
        p2p=None,
        f2p_passed=None,
        f2p_total=None,
        p2p_passed=None,
        p2p_total=None,
        patch_bytes=(result_dir / "artifacts/model.patch").stat().st_size,
        agent_exit=0,
        agent_timed_out=False,
        verifier_exit="timeout",
        agent_wall_s=session_wall_seconds(session_path),
        subject_memory_events=subject_events,
        verifier_memory_events=replay_evidence["verifierMemoryEvents"],
        **usage,
    )
    result = _confirmed_result_record(launch_cell, bare)
    result["verifier_timeout_recovery"] = {
        "method": "saved-patch-focused-verifier-replay",
        "originalAttemptPlanIdentity": EXPECTED_PLAN_IDENTITY,
        "reason": (
            "The preserved candidate patch deterministically blocks the official "
            "filesystem transport test in drain_events; no model call was repeated."
        ),
        "replayEvidence": replay_evidence,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    return result


def append_recovery_manifest(result_path: Path, evidence: dict[str, object]) -> None:
    """Append auditable provenance for the in-place timeout finalization."""
    manifest = result_path.parents[5] / "_contaminated/manifest.jsonl"
    record = {
        "action": "finalize-verifier-timeout",
        "category": "recovery",
        "destination_path": str(result_path.parent),
        "patch_identity": EXPECTED_PATCH_IDENTITY,
        "plan_identity": EXPECTED_PLAN_IDENTITY,
        "published_result_identity": file_identity(result_path),
        "reason": "Preserved model patch deterministically hangs the official filesystem transport test.",
        "replay_evidence": evidence,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with manifest.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, sort_keys=True) + "\n")


def main() -> None:
    """Validate evidence and optionally publish the recovered timeout result."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    serialized = PLAN_PATH.read_text()
    plan = parse_launch_plan_json(serialized)
    if plan.identity != EXPECTED_PLAN_IDENTITY:
        raise ValueError(f"unexpected approved plan identity: {plan.identity}")
    document = cast(dict[str, Any], json.loads(serialized))
    cell_document, launch_cell = selected_plan_cell(document)
    result_dir = Path(cell_document["resultPath"]).parent
    session_path = validate_preserved_attempt(result_dir)
    if not args.apply:
        print(f"validated preserved timeout attempt: {result_dir}")
        return

    evidence_dir = PLAN_PATH.parent / "kombu-timeout-recovery"
    replay_evidence = replay_hanging_filesystem_test(
        result_dir=result_dir,
        verifier_image=launch_cell.immutable_image_identities["verifier"],
        evidence_dir=evidence_dir,
    )
    result = build_timeout_result(
        document=document,
        launch_cell=launch_cell,
        result_dir=result_dir,
        session_path=session_path,
        replay_evidence=replay_evidence,
    )
    result_path = result_dir / "result.json"
    atomic_write_json(result_path, result)
    append_recovery_manifest(result_path, replay_evidence)
    print(f"published verifier timeout: {result_path}")
    print(f"result identity: {file_identity(result_path)}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Build the canonical 108 feedback-uptake event packet files."""

from __future__ import annotations

import argparse
import json
import shutil
import uuid
from pathlib import Path
from typing import Any

from build_analysis import DEFAULT_SOURCE_ROOT, REPORT_ROOT, RESULT_ROOTS
from feedback_uptake_event_validation import validate_feedback_uptake_packets
from feedback_uptake_events import build_feedback_uptake_packet

FEEDBACK_UPTAKE_EVENT_ROOT = REPORT_ROOT / "feedback-uptake/events"


def canonical_feedback_uptake_tasks(source_root: Path) -> list[str]:
    """Return the canonical 12-task population from the ThinkingCap result root."""
    thinkingcap_root = source_root / RESULT_ROOTS["thinkingcap"]
    if not thinkingcap_root.is_dir():
        raise FileNotFoundError(
            f"Feedback uptake events: missing canonical task root {thinkingcap_root}"
        )
    tasks = sorted(path.name for path in thinkingcap_root.iterdir() if path.is_dir())
    if len(tasks) != 12:
        raise ValueError(
            "Feedback uptake events: expected 12 canonical tasks under "
            f"{thinkingcap_root}, found {len(tasks)}"
        )
    return tasks


def build_feedback_uptake_packets(source_root: Path) -> list[dict[str, Any]]:
    """Build and validate all 108 feedback-uptake trajectory packets in order."""
    tasks = canonical_feedback_uptake_tasks(source_root)
    packets = []
    for model_key, relative_root in RESULT_ROOTS.items():
        for task in tasks:
            for rep in range(3):
                cell_root = source_root / relative_root / task / f"rep{rep}"
                if not (cell_root / "result.json").is_file():
                    raise FileNotFoundError(
                        f"Feedback uptake events: missing trajectory cell {cell_root}"
                    )
                packets.append(
                    build_feedback_uptake_packet(
                        model_key=model_key,
                        task=task,
                        rep=rep,
                        cell_root=cell_root,
                    )
                )
    validate_feedback_uptake_packets(packets, expected_tasks=tasks)
    return packets


def load_feedback_uptake_event_files(event_root: Path) -> list[dict[str, Any]]:
    """Load feedback-uptake packet JSON files in canonical path order."""
    packets = []
    for packet_path in sorted(event_root.glob("*/*__rep[0-2].json")):
        packet = json.loads(packet_path.read_text())
        if not isinstance(packet, dict):
            raise TypeError(
                f"Feedback uptake events: packet is not an object at {packet_path}"
            )
        packets.append(packet)
    return packets


def write_feedback_uptake_event_files(
    packets: list[dict[str, Any]],
    *,
    expected_tasks: list[str],
    event_root: Path = FEEDBACK_UPTAKE_EVENT_ROOT,
) -> list[Path]:
    """Validate and atomically replace the complete 108-file event tree."""
    validate_feedback_uptake_packets(packets, expected_tasks=expected_tasks)
    event_parent = event_root.parent
    event_parent.mkdir(parents=True, exist_ok=True)
    temporary_root = event_parent / f".{event_root.name}.tmp-{uuid.uuid4().hex}"
    backup_root = event_parent / f".{event_root.name}.backup-{uuid.uuid4().hex}"
    written_paths: list[Path] = []
    try:
        for packet in packets:
            model_root = temporary_root / packet["model_key"]
            model_root.mkdir(parents=True, exist_ok=True)
            packet_path = model_root / f"{packet['task']}__rep{packet['rep']}.json"
            packet_path.write_text(
                json.dumps(packet, ensure_ascii=False, separators=(",", ":")) + "\n"
            )
            written_paths.append(packet_path)

        reloaded_packets = load_feedback_uptake_event_files(temporary_root)
        validate_feedback_uptake_packets(
            reloaded_packets, expected_tasks=expected_tasks
        )
        if event_root.exists():
            event_root.rename(backup_root)
        try:
            temporary_root.rename(event_root)
        except Exception:
            if backup_root.exists():
                backup_root.rename(event_root)
            raise
        if backup_root.exists():
            shutil.rmtree(backup_root)
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
    return [
        event_root / packet["model_key"] / f"{packet['task']}__rep{packet['rep']}.json"
        for packet in packets
    ]


def build_feedback_uptake_event_files(
    source_root: Path = DEFAULT_SOURCE_ROOT,
    event_root: Path = FEEDBACK_UPTAKE_EVENT_ROOT,
) -> list[Path]:
    """Build, validate, and write the canonical feedback-uptake event dataset."""
    tasks = canonical_feedback_uptake_tasks(source_root)
    packets = build_feedback_uptake_packets(source_root)
    return write_feedback_uptake_event_files(
        packets, expected_tasks=tasks, event_root=event_root
    )


def parse_feedback_uptake_arguments() -> argparse.Namespace:
    """Parse canonical source and output roots for event packet generation."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    parser.add_argument("--event-root", type=Path, default=FEEDBACK_UPTAKE_EVENT_ROOT)
    return parser.parse_args()


def main() -> None:
    """Build and report the complete feedback-uptake event packet tree."""
    arguments = parse_feedback_uptake_arguments()
    written_paths = build_feedback_uptake_event_files(
        source_root=arguments.source_root,
        event_root=arguments.event_root,
    )
    print(f"Wrote and validated {len(written_paths)} feedback-uptake packets")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent / "churn_deep_dive"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def main() -> None:
    classifications = load_json(HERE / "classification.json")
    counts: dict[str, int] = {}
    packet_paths = sorted(HERE.glob("*__rep*.json"))
    for path in packet_paths:
        packet = load_json(path)
        pair = packet["pair"]
        key = f"{pair['task']}__rep{pair['rep']}"
        classification = classifications["items"][key]
        packet["classification"] = classification
        packet["stage_ledger"] = {
            side: {
                "initialization": packet[side]["session"],
                "contract_representation": "initial_context/user_prompt.txt",
                "seam_location": packet[side]["patch_stats"]["files"],
                "implementation": {
                    name: packet[side]["patch_stats"][name]
                    for name in ["bytes", "adds", "dels"]
                },
                "targeted_and_regression_validation": packet[side]["trace"]["commands"][
                    -12:
                ],
                "completion_audit": [
                    command
                    for command in packet[side]["trace"]["commands"]
                    if "git diff" in command or "git status" in command
                ][-6:],
                "termination": packet[side]["result"],
            }
            for side in ["left", "right"]
        }
        path.write_text(json.dumps(packet, indent=2) + "\n")
        bucket = str(classification["primary_bucket"])
        counts[bucket] = counts.get(bucket, 0) + 1
    if counts != classifications["counts"]:
        raise ValueError(
            f"classification counts disagree: {counts} != {classifications['counts']}"
        )
    print(json.dumps({"packets": len(packet_paths), "counts": counts}, sort_keys=True))


if __name__ == "__main__":
    main()

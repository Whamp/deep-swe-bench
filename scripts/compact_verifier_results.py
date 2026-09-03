#!/usr/bin/env python3
"""Compact historical verifier evidence after a verified external archive."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from harness.results_retention import (  # noqa: E402
    collapse_quarantine_category,
    migrate_results_tree,
)


def _compact_results(arguments: argparse.Namespace) -> int:
    report = migrate_results_tree(
        arguments.results_root,
        apply=arguments.apply,
        retain_raw_verifier_evidence=arguments.retain_raw_verifier_evidence,
    )
    print(
        json.dumps(
            {
                "mode": "apply" if arguments.apply else "dry-run",
                "results_root": str(arguments.results_root),
                "examined": report.examined,
                "planned": report.planned,
                "compacted": report.compacted,
                "already_compact": report.already_compact,
                "raw_bytes": report.raw_bytes,
                "issues": [
                    {
                        "result_path": str(issue.result_path),
                        "error": issue.error,
                    }
                    for issue in report.issues
                ],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if report.issues else 0


def _collapse_quarantine(arguments: argparse.Namespace) -> int:
    report = collapse_quarantine_category(
        arguments.results_root,
        category=arguments.category,
        apply=arguments.apply,
        archive_uri=arguments.archive_uri,
    )
    print(
        json.dumps(
            {
                "mode": "apply" if arguments.apply else "dry-run",
                "results_root": str(arguments.results_root),
                "category": report.category,
                "result_count": report.result_count,
                "artifact_count": report.artifact_count,
                "source_bytes": report.source_bytes,
                "ledger_bytes": report.ledger_bytes,
                "applied": report.applied,
                "archive_uri": arguments.archive_uri,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


def parse_arguments(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse explicit compact or quarantine-collapse operator commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.set_defaults(handler=None)
    subparsers = parser.add_subparsers(dest="command", required=True)

    compact = subparsers.add_parser(
        "compact",
        help="validate or compact verifier evidence in every result cell",
    )
    compact.add_argument(
        "--results-root",
        type=Path,
        default=REPO / "results",
    )
    compact.add_argument(
        "--apply",
        action="store_true",
        help="write schema-v2 results and prune validated raw verifier evidence",
    )
    compact.add_argument(
        "--retain-raw-verifier-evidence",
        action="store_true",
        help="write compact summaries but keep full raw verifier files",
    )
    compact.set_defaults(handler=_compact_results)

    collapse = subparsers.add_parser(
        "collapse-quarantine",
        help="replace one compacted quarantine category with a JSONL ledger",
    )
    collapse.add_argument(
        "--results-root",
        type=Path,
        default=REPO / "results",
    )
    collapse.add_argument(
        "--category",
        default="om-no-executor-projection",
    )
    collapse.add_argument("--archive-uri", required=True)
    collapse.add_argument(
        "--apply",
        action="store_true",
        help="write the ledger, update the manifest, and remove the category tree",
    )
    collapse.set_defaults(handler=_collapse_quarantine)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the selected retention operation and return its process status."""
    arguments = parse_arguments(argv)
    return arguments.handler(arguments)


if __name__ == "__main__":
    raise SystemExit(main())

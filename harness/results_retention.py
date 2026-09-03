"""Migrate historical benchmark results to compact verifier evidence."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from harness.verifier_evidence import (
    is_compact_verifier_result,
    prune_raw_verifier_evidence,
    with_compact_verifier_evidence,
    write_compact_verifier_result,
)


@dataclass(frozen=True)
class ResultsRetentionIssue:
    """Describe one result cell that could not be compacted safely."""

    result_path: Path
    error: str


@dataclass(frozen=True)
class ResultsMigrationReport:
    """Summarize one dry-run or applied results-tree migration."""

    examined: int
    planned: int
    compacted: int
    already_compact: int
    raw_bytes: int
    issues: tuple[ResultsRetentionIssue, ...]


@dataclass(frozen=True)
class QuarantineCollapseReport:
    """Summarize one compact quarantine-ledger build."""

    category: str
    result_count: int
    artifact_count: int
    source_bytes: int
    ledger_bytes: int
    applied: bool


def _read_result_record(result_path: Path) -> dict[str, object]:
    document: object = json.loads(result_path.read_text())
    if not isinstance(document, dict):
        raise TypeError(f"Result migration requires a JSON object: {result_path}")
    return cast(dict[str, object], document)


def _summary_raw_bytes(result_record: Mapping[str, object]) -> int:
    summary = result_record.get("verifier_summary")
    if not isinstance(summary, Mapping):
        return 0
    raw_artifacts = summary.get("raw_artifacts")
    if not isinstance(raw_artifacts, Mapping):
        return 0
    raw_bytes = raw_artifacts.get("bytes")
    return raw_bytes if isinstance(raw_bytes, int) else 0


def _compact_result_has_pending_raw_evidence(
    cell: Path,
    result_record: Mapping[str, object],
) -> bool:
    summary = result_record.get("verifier_summary")
    if not isinstance(summary, Mapping) or summary.get("raw_evidence_retained") is True:
        return False
    return (cell / "verifier").exists() or (
        cell / "logs" / "verifier.stdout.txt"
    ).is_file()


def migrate_results_tree(
    results_root: Path,
    *,
    apply: bool,
    retain_raw_verifier_evidence: bool = False,
) -> ResultsMigrationReport:
    """Validate or apply compact verifier evidence across one results tree."""
    examined = 0
    planned = 0
    compacted = 0
    already_compact = 0
    raw_bytes = 0
    issues: list[ResultsRetentionIssue] = []
    for result_path in sorted(results_root.rglob("result.json")):
        examined += 1
        try:
            result_record = _read_result_record(result_path)
            if is_compact_verifier_result(result_record):
                already_compact += 1
                if _compact_result_has_pending_raw_evidence(
                    result_path.parent,
                    result_record,
                ):
                    planned += 1
                    raw_bytes += _summary_raw_bytes(result_record)
                    if apply:
                        prune_raw_verifier_evidence(result_path.parent)
                        compacted += 1
                continue
            compacted_record = with_compact_verifier_evidence(
                result_path.parent,
                result_record,
                retain_raw_verifier_evidence=retain_raw_verifier_evidence,
            )
            planned += 1
            raw_bytes += _summary_raw_bytes(compacted_record)
            if apply:
                write_compact_verifier_result(
                    result_path.parent,
                    result_record,
                    retain_raw_verifier_evidence=retain_raw_verifier_evidence,
                )
                compacted += 1
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as error:
            issues.append(
                ResultsRetentionIssue(
                    result_path=result_path,
                    error=f"{type(error).__name__}: {error}",
                )
            )
    return ResultsMigrationReport(
        examined=examined,
        planned=planned,
        compacted=compacted,
        already_compact=already_compact,
        raw_bytes=raw_bytes,
        issues=tuple(issues),
    )


def _read_json_lines(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        return []
    records: list[dict[str, object]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        record: object = json.loads(line)
        if not isinstance(record, dict):
            raise TypeError(
                f"Quarantine manifest record must be an object: {path}:{line_number}"
            )
        records.append(cast(dict[str, object], record))
    return records


def _atomic_write_json_lines(path: Path, records: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary_path = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w") as output:
            for record in records:
                output.write(json.dumps(record, allow_nan=False, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
        temporary_path.replace(path)
        directory_descriptor = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
    finally:
        temporary_path.unlink(missing_ok=True)


def _file_digest(path: Path) -> dict[str, object] | None:
    if not path.is_file():
        return None
    content = path.read_bytes()
    return {
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
    }


def _session_digest(cell: Path) -> dict[str, object] | None:
    session_root = cell / "session"
    session_files = sorted(path for path in session_root.rglob("*") if path.is_file())
    if not session_files:
        return None
    digest = hashlib.sha256()
    total_bytes = 0
    for path in session_files:
        content = path.read_bytes()
        total_bytes += len(content)
        digest.update(str(path.relative_to(cell)).encode())
        digest.update(b"\0")
        digest.update(content)
    return {
        "bytes": total_bytes,
        "file_count": len(session_files),
        "sha256": digest.hexdigest(),
    }


def _matching_quarantine_manifest(
    category: str,
    cell_relative_path: Path,
    manifest_records: list[dict[str, object]],
) -> dict[str, object]:
    cell_quarantine_path = (
        f"results/_contaminated/{category}/{cell_relative_path.as_posix()}"
    )
    matches = [
        record
        for record in manifest_records
        if record.get("category") == category
        and isinstance(record.get("quarantine_path"), str)
        and (
            cell_quarantine_path == record["quarantine_path"]
            or cell_quarantine_path.startswith(f"{record['quarantine_path']}/")
        )
    ]
    if not matches:
        raise ValueError(
            "Quarantine ledger manifest match missing: "
            f"category={category}; cell={cell_relative_path}"
        )
    return max(matches, key=lambda record: len(str(record["quarantine_path"])))


def _category_artifact_ledger_record(
    path: Path,
    category_root: Path,
    category: str,
    archive_uri: str,
) -> dict[str, object]:
    content = path.read_bytes()
    excerpt_limit = 32 * 1024
    truncation_marker = b"\n...[truncated]...\n"
    if len(content) <= excerpt_limit:
        excerpt_bytes = content
    else:
        retained_bytes = excerpt_limit - len(truncation_marker)
        prefix_bytes = retained_bytes // 2
        suffix_bytes = retained_bytes - prefix_bytes
        excerpt_bytes = (
            content[:prefix_bytes] + truncation_marker + content[-suffix_bytes:]
        )
    record: dict[str, object] = {
        "ledger_schema_version": 1,
        "record_type": "category_artifact",
        "quarantine_category": category,
        "path": path.relative_to(category_root).as_posix(),
        "bytes": len(content),
        "sha256": hashlib.sha256(content).hexdigest(),
        "raw_archive": archive_uri,
    }
    try:
        excerpt_text = excerpt_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return record
    record["text_excerpt"] = {
        "original_bytes": len(content),
        "truncated": len(excerpt_bytes) < len(content),
        "text": excerpt_text,
    }
    return record


def _build_quarantine_ledger_records(
    category_root: Path,
    category: str,
    manifest_records: list[dict[str, object]],
    archive_uri: str,
) -> list[dict[str, object]]:
    result_paths = sorted(category_root.rglob("result.json"))
    cell_roots = {path.parent for path in result_paths}

    def belongs_to_result_cell(path: Path) -> bool:
        parent = path.parent
        while parent != category_root:
            if parent in cell_roots:
                return True
            parent = parent.parent
        return False

    category_artifacts = [
        path
        for path in category_root.rglob("*")
        if path.is_file() and not belongs_to_result_cell(path)
    ]
    records: list[dict[str, object]] = []
    for result_path in result_paths:
        result_record = _read_result_record(result_path)
        if not is_compact_verifier_result(result_record):
            raise ValueError(
                f"Quarantine ledger requires compact result: {result_path}"
            )
        cell = result_path.parent
        cell_relative_path = cell.relative_to(category_root)
        manifest = _matching_quarantine_manifest(
            category,
            cell_relative_path,
            manifest_records,
        )
        records.append(
            {
                "ledger_schema_version": 1,
                "record_type": "result_cell",
                "quarantine_category": category,
                "cell_path": cell_relative_path.as_posix(),
                "result": result_record,
                "quarantine": {
                    key: manifest[key]
                    for key in (
                        "original_path",
                        "quarantine_path",
                        "reason",
                        "timestamp",
                    )
                    if key in manifest
                },
                "model_patch": _file_digest(cell / "artifacts" / "model.patch"),
                "session": _session_digest(cell),
                "raw_archive": archive_uri,
            }
        )
    records.extend(
        _category_artifact_ledger_record(
            path,
            category_root,
            category,
            archive_uri,
        )
        for path in category_artifacts
    )
    return records


def _quarantine_collapse_report(
    category: str,
    ledger_records: list[dict[str, object]],
    *,
    source_bytes: int,
    ledger_bytes: int,
    applied: bool,
) -> QuarantineCollapseReport:
    return QuarantineCollapseReport(
        category=category,
        result_count=sum(
            record.get("record_type") == "result_cell" for record in ledger_records
        ),
        artifact_count=sum(
            record.get("record_type") == "category_artifact"
            for record in ledger_records
        ),
        source_bytes=source_bytes,
        ledger_bytes=ledger_bytes,
        applied=applied,
    )


def _reuse_existing_quarantine_ledger(
    contaminated_root: Path,
    *,
    category: str,
    archive_uri: str,
    apply: bool,
) -> QuarantineCollapseReport:
    category_root = contaminated_root / category
    ledger_path = contaminated_root / f"{category}.jsonl"
    deletion_root = contaminated_root / f".{category}.compact-ledger-delete"
    ledger_records = _read_json_lines(ledger_path)
    if not ledger_records:
        raise FileNotFoundError(
            f"Quarantine category and compact ledger do not exist: {category_root}"
        )
    invalid_records = [
        record
        for record in ledger_records
        if record.get("ledger_schema_version") != 1
        or record.get("quarantine_category") != category
        or record.get("raw_archive") != archive_uri
        or record.get("record_type") not in {"result_cell", "category_artifact"}
    ]
    if invalid_records:
        raise ValueError(
            "Existing quarantine ledger does not match the requested category "
            f"and archive: {ledger_path}"
        )
    source_bytes = (
        sum(path.stat().st_size for path in deletion_root.rglob("*") if path.is_file())
        if deletion_root.is_dir()
        else 0
    )
    if apply and deletion_root.is_dir():
        shutil.rmtree(deletion_root)
    return _quarantine_collapse_report(
        category,
        ledger_records,
        source_bytes=source_bytes,
        ledger_bytes=ledger_path.stat().st_size,
        applied=apply,
    )


def _publish_quarantine_ledger(
    contaminated_root: Path,
    ledger_records: list[dict[str, object]],
    manifest_records: list[dict[str, object]],
    *,
    category: str,
    archive_uri: str,
) -> None:
    category_root = contaminated_root / category
    ledger_path = contaminated_root / f"{category}.jsonl"
    manifest_path = contaminated_root / "manifest.jsonl"
    deletion_root = contaminated_root / f".{category}.compact-ledger-delete"
    _atomic_write_json_lines(ledger_path, ledger_records)
    validated_records = _read_json_lines(ledger_path)
    if len(validated_records) != len(ledger_records):
        raise ValueError(
            "Quarantine ledger validation count mismatch: "
            f"expected={len(ledger_records)}; actual={len(validated_records)}"
        )
    relative_ledger = f"results/_contaminated/{category}.jsonl"
    for manifest_record in manifest_records:
        if manifest_record.get("category") == category:
            manifest_record["retention"] = "compact-ledger"
            manifest_record["compact_ledger"] = relative_ledger
            manifest_record["raw_archive"] = archive_uri
    _atomic_write_json_lines(manifest_path, manifest_records)
    if deletion_root.exists():
        raise FileExistsError(
            f"Quarantine source cleanup staging path already exists: {deletion_root}"
        )
    category_root.replace(deletion_root)
    try:
        shutil.rmtree(deletion_root)
    except PermissionError as error:
        raise PermissionError(
            "Quarantine source cleanup blocked by container-owned files: "
            f"path={deletion_root}; make the archived tree writable and remove it"
        ) from error


def collapse_quarantine_category(
    results_root: Path,
    *,
    category: str,
    apply: bool,
    archive_uri: str,
) -> QuarantineCollapseReport:
    """Replace one quarantined result category with a validated compact ledger."""
    if not archive_uri:
        raise ValueError("Quarantine ledger archive URI must not be empty")
    contaminated_root = results_root / "_contaminated"
    category_root = contaminated_root / category
    if not category_root.is_dir():
        return _reuse_existing_quarantine_ledger(
            contaminated_root,
            category=category,
            archive_uri=archive_uri,
            apply=apply,
        )
    manifest_path = contaminated_root / "manifest.jsonl"
    manifest_records = _read_json_lines(manifest_path)
    ledger_records = _build_quarantine_ledger_records(
        category_root,
        category,
        manifest_records,
        archive_uri,
    )
    source_bytes = sum(
        path.stat().st_size for path in category_root.rglob("*") if path.is_file()
    )
    rendered_ledger = "".join(
        json.dumps(record, allow_nan=False, sort_keys=True) + "\n"
        for record in ledger_records
    )
    if apply:
        _publish_quarantine_ledger(
            contaminated_root,
            ledger_records,
            manifest_records,
            category=category,
            archive_uri=archive_uri,
        )
    return _quarantine_collapse_report(
        category,
        ledger_records,
        source_bytes=source_bytes,
        ledger_bytes=len(rendered_ledger.encode()),
        applied=apply,
    )

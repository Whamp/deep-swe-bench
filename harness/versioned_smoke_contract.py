"""Validate durable smoke gates for versioned config launches."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from pathlib import Path
from typing import NoReturn, cast

_STRUCTURED_RESULT_ASSERTION_KINDS = (
    "equalsResultValues",
    "minResultValues",
)
_FILE_ASSERTION_KINDS = ("requireFiles", "requireRepoFiles")
_EXTENSION_MARKER_ASSERTION_KINDS = (
    "requireExtensionMarkers",
    "forbidExtensionMarkers",
)
_PROHIBITED_TEXT_ASSERTION_KINDS = (
    "requireText",
    "forbidText",
    "requireRepoText",
    "forbidRepoText",
)
_SUPPORTED_ASSERTION_KINDS = frozenset(
    {
        *_STRUCTURED_RESULT_ASSERTION_KINDS,
        *_FILE_ASSERTION_KINDS,
        *_EXTENSION_MARKER_ASSERTION_KINDS,
        *_PROHIBITED_TEXT_ASSERTION_KINDS,
        "requireJsonRecords",
        "requireUsageRecords",
    }
)
_EXTENSION_MACHINE_MARKER = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_.:-]*$")
_JSON_RECORD_FORMATS = frozenset({"json", "jsonl"})
_BRITTLE_OUTPUT_LENGTH_FIELD = re.compile(
    r"(?:chars?|characters?|char_count|character_count|length|"
    r"line_count|linecount)$"
)


def _reject_smoke_assertion(
    location: Path,
    assertion_kind: str,
    target: object,
    reason: str,
    *,
    pointer: str | None = None,
) -> NoReturn:
    """Raise one searchable versioned smoke-contract diagnostic."""
    contract_pointer = pointer or f"/{assertion_kind}"
    raise ValueError(
        "Smoke contract rejected: "
        f"location={location}#{contract_pointer}; "
        f"assertion_kind={assertion_kind!r}; "
        f"target={target!r}; "
        f"reason={reason}"
    )


def _is_relative_artifact_glob(value: object) -> bool:
    """Return whether a value is a safe repository or cell-relative glob."""
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def _validate_artifact_glob_list(
    location: Path,
    assertion_kind: str,
    value: object,
) -> list[str]:
    """Validate a list of safe artifact globs and return narrowed strings."""
    if not isinstance(value, list) or any(
        not _is_relative_artifact_glob(item) for item in value
    ):
        _reject_smoke_assertion(
            location,
            assertion_kind,
            "<contract>",
            "expected a list of relative file globs",
        )
    return cast(list[str], value)


def _is_json_number(value: object) -> bool:
    """Return whether a value is a finite JSON number rather than a boolean."""
    return (
        isinstance(value, int | float)
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _is_brittle_output_length_field(field: str) -> bool:
    """Return whether a result field encodes brittle output dimensions."""
    return _BRITTLE_OUTPUT_LENGTH_FIELD.search(field.lower()) is not None


def _validate_structured_result_assertions(
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Validate result fields and counters without allowing text metrics."""
    for assertion_kind in _STRUCTURED_RESULT_ASSERTION_KINDS:
        assertions = document.get(assertion_kind, {})
        if not isinstance(assertions, Mapping):
            _reject_smoke_assertion(
                location,
                assertion_kind,
                "<contract>",
                "expected an object keyed by dotted result fields",
            )
        normalized_assertions: dict[str, object] = {}
        for field, expected in assertions.items():
            if not isinstance(field, str) or not field:
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    field,
                    "expected an object keyed by dotted result fields",
                )
            normalized_assertions[field] = expected
        for field, expected in normalized_assertions.items():
            if _is_brittle_output_length_field(field):
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    field,
                    "output length and line counts are not durable launch "
                    "gates",
                    pointer=f"/{assertion_kind}/{field}",
                )
            if assertion_kind == "minResultValues" and not _is_json_number(
                expected
            ):
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    field,
                    "minimum result values must be finite numbers",
                    pointer=f"/{assertion_kind}/{field}",
                )


def _validate_file_assertions(
    repository_root: Path,
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Validate cell globs and resolve repository artifacts model-free."""
    for assertion_kind in _FILE_ASSERTION_KINDS:
        targets = _validate_artifact_glob_list(
            location,
            assertion_kind,
            document.get(assertion_kind, []),
        )
        if assertion_kind != "requireRepoFiles":
            continue
        for index, target in enumerate(targets):
            matches = repository_root.glob(target)
            if any(match.is_file() for match in matches):
                continue
            _reject_smoke_assertion(
                location,
                assertion_kind,
                target,
                "referenced repository artifact does not exist",
                pointer=f"/{assertion_kind}/{index}",
            )


def _expected_extension_prefix(location: Path) -> tuple[str, str, str] | None:
    """Return the repository-relative extension prefix for this config."""
    parts = location.parts
    if len(parts) < 3 or parts[0] != "configs":
        return None
    return (parts[0], parts[1], "extensions")


def _validate_extension_marker_assertions(
    repository_root: Path,
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Validate stable markers and their owning extension artifacts."""
    extension_prefix = _expected_extension_prefix(location)
    for assertion_kind in _EXTENSION_MARKER_ASSERTION_KINDS:
        assertions = document.get(assertion_kind, [])
        if not isinstance(assertions, list):
            _reject_smoke_assertion(
                location,
                assertion_kind,
                "<contract>",
                "expected a list of extension marker assertions",
            )
        for index, assertion in enumerate(assertions):
            pointer = f"/{assertion_kind}/{index}"
            if not isinstance(assertion, Mapping):
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    "<contract>",
                    "expected extension, globs, and marker fields",
                    pointer=pointer,
                )
            if set(assertion) != {"extension", "globs", "marker"}:
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    "<contract>",
                    "expected only extension, globs, and marker fields",
                    pointer=pointer,
                )
            owner = assertion.get("extension")
            owner_path = Path(owner) if isinstance(owner, str) else None
            if (
                owner_path is None
                or owner_path.is_absolute()
                or ".." in owner_path.parts
                or extension_prefix is None
                or owner_path.parts[:3] != extension_prefix
                or not (repository_root / owner_path).is_file()
            ):
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    owner,
                    "owning extension artifact does not exist in this config",
                    pointer=pointer,
                )
            _validate_artifact_glob_list(
                location,
                assertion_kind,
                assertion.get("globs"),
            )
            marker = assertion.get("marker")
            if (
                not isinstance(marker, str)
                or _EXTENSION_MACHINE_MARKER.fullmatch(marker) is None
            ):
                _reject_smoke_assertion(
                    location,
                    assertion_kind,
                    marker,
                    "extension machine markers must be one stable token",
                    pointer=pointer,
                )


def _validate_usage_record_assertions(
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Validate structured compact usage-record gates."""
    assertions = document.get("requireUsageRecords", [])
    if not isinstance(assertions, list):
        _reject_smoke_assertion(
            location,
            "requireUsageRecords",
            "<contract>",
            "expected a list of structured usage record assertions",
        )
    for index, assertion in enumerate(assertions):
        pointer = f"/requireUsageRecords/{index}"
        if not isinstance(assertion, Mapping):
            _reject_smoke_assertion(
                location,
                "requireUsageRecords",
                "<contract>",
                "expected equals, globs, and minimum fields",
                pointer=pointer,
            )
        globs = assertion.get("globs")
        targets = (
            globs
            if isinstance(globs, list)
            and all(_is_relative_artifact_glob(item) for item in globs)
            else []
        )
        target = targets[0] if targets else "<missing>"
        equals = assertion.get("equals")
        minimum = assertion.get("minimum")
        valid_equals = (
            isinstance(equals, Mapping)
            and bool(equals)
            and all(isinstance(field, str) and field for field in equals)
        )
        if (
            set(assertion) != {"equals", "globs", "minimum"}
            or not targets
            or not valid_equals
            or not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum <= 0
        ):
            _reject_smoke_assertion(
                location,
                "requireUsageRecords",
                target,
                "usage records require structured equals fields and a positive "
                "minimum",
                pointer=pointer,
            )


def _validate_json_record_assertions(
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Validate structured JSON and JSONL record gates."""
    assertions = document.get("requireJsonRecords", [])
    if not isinstance(assertions, list):
        _reject_smoke_assertion(
            location,
            "requireJsonRecords",
            "<contract>",
            "expected a list of structured JSON record assertions",
        )
    for index, assertion in enumerate(assertions):
        pointer = f"/requireJsonRecords/{index}"
        if not isinstance(assertion, Mapping):
            _reject_smoke_assertion(
                location,
                "requireJsonRecords",
                "<contract>",
                "expected equals, format, globs, and minimum fields",
                pointer=pointer,
            )
        globs = assertion.get("globs")
        targets = (
            globs
            if isinstance(globs, list)
            and all(_is_relative_artifact_glob(item) for item in globs)
            else []
        )
        target = targets[0] if targets else "<missing>"
        equals = assertion.get("equals")
        record_format = assertion.get("format")
        minimum = assertion.get("minimum")
        valid_equals = (
            isinstance(equals, Mapping)
            and bool(equals)
            and all(isinstance(field, str) and field for field in equals)
        )
        if (
            set(assertion) != {"equals", "format", "globs", "minimum"}
            or not targets
            or not valid_equals
            or record_format not in _JSON_RECORD_FORMATS
            or not isinstance(minimum, int)
            or isinstance(minimum, bool)
            or minimum <= 0
        ):
            _reject_smoke_assertion(
                location,
                "requireJsonRecords",
                target,
                "JSON records require structured equals fields, a json or "
                "jsonl format, and a positive minimum",
                pointer=pointer,
            )


def _prohibited_text_reason(
    assertion_kind: str,
    target: object,
    text: object,
) -> str:
    """Classify why an old text assertion is too brittle for approval."""
    if isinstance(target, str) and Path(target).name.lower() == "readme.md":
        return "README prose is not a durable launch gate"
    if isinstance(target, str) and target.startswith("docs/"):
        return "documentation wording is not a durable launch gate"
    if isinstance(text, str) and ("\n" in text or "\r" in text):
        return "newline placement is not a durable launch gate"
    if "RepoText" in assertion_kind:
        return "source prose or formatting is not a durable launch gate"
    return (
        "unstructured text is not a durable launch gate; use an explicitly "
        "owned extension machine marker"
    )


def _reject_prohibited_text_assertions(
    location: Path,
    document: Mapping[str, object],
) -> None:
    """Reject every legacy free-text assertion in a versioned contract."""
    for assertion_kind in _PROHIBITED_TEXT_ASSERTION_KINDS:
        if assertion_kind not in document:
            continue
        assertions = document[assertion_kind]
        if not isinstance(assertions, list) or not assertions:
            _reject_smoke_assertion(
                location,
                assertion_kind,
                "<contract>",
                "free-text assertion kinds are prohibited in versioned "
                "contracts",
            )
        assertion = assertions[0]
        if not isinstance(assertion, Mapping):
            target: object = "<contract>"
            text: object = None
        else:
            globs = assertion.get("globs")
            target = (
                globs[0] if isinstance(globs, list) and globs else "<missing>"
            )
            text = assertion.get("text")
        _reject_smoke_assertion(
            location,
            assertion_kind,
            target,
            _prohibited_text_reason(assertion_kind, target, text),
            pointer=f"/{assertion_kind}/0",
        )


def validate_versioned_smoke_contract(
    repository_root: Path,
    contract_path: Path | None,
) -> Mapping[str, object] | None:
    """Validate durable assertions before a versioned launch can be approved.

    Raises:
        ValueError: The contract is malformed, brittle, or references a missing
            repository artifact.

    """
    if contract_path is None:
        return
    location = contract_path.relative_to(repository_root)
    try:
        document_value: object = json.loads(contract_path.read_text())
    except (json.JSONDecodeError, OSError) as error:
        reason = (
            f"invalid JSON ({error.msg})"
            if isinstance(error, json.JSONDecodeError)
            else f"contract cannot be read ({error})"
        )
        _reject_smoke_assertion(
            location,
            "<syntax>",
            "<contract>",
            reason,
            pointer="/<contract>",
        )
    if not isinstance(document_value, Mapping):
        _reject_smoke_assertion(
            location,
            "<syntax>",
            "<contract>",
            "contract root must be a JSON object",
            pointer="/<contract>",
        )
    document = cast(Mapping[str, object], document_value)
    for assertion_kind in document:
        if assertion_kind not in _SUPPORTED_ASSERTION_KINDS:
            _reject_smoke_assertion(
                location,
                assertion_kind,
                "<contract>",
                "unsupported assertion kind",
            )
    _reject_prohibited_text_assertions(location, document)
    _validate_structured_result_assertions(location, document)
    _validate_file_assertions(repository_root, location, document)
    _validate_usage_record_assertions(location, document)
    _validate_json_record_assertions(location, document)
    _validate_extension_marker_assertions(
        repository_root,
        location,
        document,
    )
    return document

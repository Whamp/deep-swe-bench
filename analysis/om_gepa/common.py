from __future__ import annotations

import argparse
import csv
import difflib
import hashlib
import html
import json
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from . import ARTIFACT_ROOT, DEFAULT_CONFIG, REPO_ROOT

RELEVANCE_VALUES = {"low", "medium", "high", "critical"}
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$")
MEMORY_ID_RE = re.compile(r"^[a-f0-9]{12}$")


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_no}: invalid JSONL: {exc}") from exc
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count


def sha12(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:12]


def text_blocks(content: Any, *, include_thinking: bool = True) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return "[non-text content omitted]"
    parts: list[str] = []
    for block in content:
        if not isinstance(block, dict):
            parts.append("[non-text content omitted]")
            continue
        typ = block.get("type")
        if typ == "text" and isinstance(block.get("text"), str):
            parts.append(block["text"])
        elif typ == "thinking":
            if block.get("redacted") is True:
                continue
            if include_thinking and isinstance(block.get("thinking"), str):
                parts.append(f"[thinking: {block['thinking']}]")
            else:
                parts.append("[non-text content omitted]")
        elif typ == "toolCall" and isinstance(block.get("name"), str):
            parts.append(f"[{block['name']}({json.dumps(block.get('arguments', {}), sort_keys=True)})]")
        else:
            parts.append("[non-text content omitted]")
    return "\n".join(parts)


def text_only(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        block.get("text", "")
        for block in content
        if isinstance(block, dict) and block.get("type") == "text" and isinstance(block.get("text"), str)
    )


def fmt_timestamp(value: Any) -> str:
    # Session chunks already carry display timestamps. This fallback mirrors the
    # extension's tolerant behavior enough for offline replay case construction.
    if isinstance(value, str):
        # Keep ISO-ish timestamps readable without taking a timezone dependency.
        return value[:16].replace("T", " ") if len(value) >= 16 else value
    return "????-??-?? ??:??"


def serialize_entry(entry: dict[str, Any]) -> str:
    typ = entry.get("type")
    if typ == "message" and isinstance(entry.get("message"), dict):
        msg = entry["message"]
        time = fmt_timestamp(msg.get("timestamp") or entry.get("timestamp"))
        role = msg.get("role")
        if role == "user":
            return f"[User @ {time}]: {text_only(msg.get('content'))}"
        if role == "assistant":
            body = "\n".join(x for x in text_blocks(msg.get("content"), include_thinking=True).splitlines() if x)
            return f"[Assistant @ {time}]: {body}" if body else ""
        tool_name = msg.get("toolName", "unknown")
        return f"[Tool result for {tool_name} @ {time}]: {text_only(msg.get('content'))}"
    if typ == "custom_message":
        time = fmt_timestamp(entry.get("timestamp"))
        tag = f"Custom ({entry.get('customType')})" if entry.get("customType") else "Custom"
        return f"[{tag} @ {time}]: {text_only(entry.get('content'))}"
    if typ == "branch_summary" and isinstance(entry.get("summary"), str):
        return f"[Branch summary @ {fmt_timestamp(entry.get('timestamp'))}]: {entry['summary']}"
    return ""


def is_source_entry(entry: dict[str, Any]) -> bool:
    return entry.get("type") in {"message", "custom_message", "branch_summary"} and bool(entry.get("id"))


def serialize_source_entries(entries: list[dict[str, Any]]) -> tuple[str, list[str]]:
    blocks: list[str] = []
    ids: list[str] = []
    for entry in entries:
        if not is_source_entry(entry):
            continue
        rendered = serialize_entry(entry).strip()
        if not rendered:
            continue
        entry_id = str(entry["id"])
        ids.append(entry_id)
        blocks.append(f"[Source entry id: {entry_id}]\n{rendered}")
    return "\n\n".join(blocks), ids


def observation_line(obs: dict[str, Any]) -> str:
    return f"[{obs.get('id')}] {obs.get('timestamp')} [{obs.get('relevance')}] {obs.get('content')}"


def reflection_line(ref: dict[str, Any]) -> str:
    return f"[{ref.get('id')}] {ref.get('content')}"


def fold_memory(entries: list[dict[str, Any]], end_idx: int | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if end_idx is None:
        end_idx = len(entries) - 1
    observations: dict[str, dict[str, Any]] = {}
    reflections: dict[str, dict[str, Any]] = {}
    dropped: set[str] = set()
    for entry in entries[: max(0, end_idx + 1)]:
        if entry.get("type") != "custom":
            continue
        data = entry.get("data") if isinstance(entry.get("data"), dict) else {}
        if entry.get("customType") == "om.observations.recorded":
            for obs in data.get("observations", []) if isinstance(data.get("observations"), list) else []:
                if isinstance(obs, dict) and isinstance(obs.get("id"), str) and obs["id"] not in observations:
                    observations[obs["id"]] = obs
        elif entry.get("customType") == "om.reflections.recorded":
            for ref in data.get("reflections", []) if isinstance(data.get("reflections"), list) else []:
                if isinstance(ref, dict) and isinstance(ref.get("id"), str) and ref["id"] not in reflections:
                    reflections[ref["id"]] = ref
        elif entry.get("customType") == "om.observations.dropped":
            for oid in data.get("observationIds", []) if isinstance(data.get("observationIds"), list) else []:
                if isinstance(oid, str):
                    dropped.add(oid)
    active = [obs for oid, obs in observations.items() if oid not in dropped]
    return active, list(reflections.values())


def index_by_entry_id(entries: list[dict[str, Any]]) -> dict[str, int]:
    return {str(e["id"]): i for i, e in enumerate(entries) if e.get("id")}


def stable_split(case_id: str) -> str:
    bucket = int(hashlib.sha256(case_id.encode("utf-8")).hexdigest()[:8], 16) % 100
    if bucket < 70:
        return "train"
    if bucket < 85:
        return "val"
    return "test"


def prompt_file_for_role(config: Path, role: str) -> Path:
    if role not in {"observer", "reflector"}:
        raise ValueError("role must be observer or reflector")
    return config / "extensions" / "pi-observational-memory" / "src" / "agents" / role / "prompts.ts"


def read_prompt_constant(path: Path, constant_name: str) -> str:
    text = path.read_text(encoding="utf-8")
    marker = f"export const {constant_name} = `"
    start = text.find(marker)
    if start == -1:
        raise ValueError(f"{path}: cannot find {constant_name} template literal")
    body_start = start + len(marker)
    end = text.rfind("`;", body_start)
    if end == -1:
        raise ValueError(f"{path}: cannot find end of {constant_name}")
    return text[body_start:end]


def ts_template_literal(text: str) -> str:
    return "`" + text.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${") + "`"


def prompt_patch(role: str, candidate_prompt: str, base_config: Path = DEFAULT_CONFIG) -> str:
    constant = "OBSERVER_SYSTEM" if role == "observer" else "REFLECTOR_SYSTEM"
    base_path = prompt_file_for_role(base_config, role)
    old = base_path.read_text(encoding="utf-8").splitlines(keepends=True)
    new_text = f"export const {constant} = {ts_template_literal(candidate_prompt)};\n"
    new = new_text.splitlines(keepends=True)
    return "".join(difflib.unified_diff(old, new, fromfile=str(base_path), tofile=f"candidate/{base_path.name}"))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_changed_cases_html(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = []
    for row in rows:
        body.append("<section>")
        body.append(f"<h2>{html.escape(str(row.get('case_id', 'case')))}</h2>")
        body.append(f"<p>score={html.escape(str(row.get('score')))} valid={html.escape(str(row.get('valid')))}</p>")
        body.append(f"<pre>{html.escape(str(row.get('feedback', '')))}</pre>")
        body.append("</section>")
    path.write_text(
        "<!doctype html><meta charset='utf-8'><title>OM GEPA changed cases</title>"
        "<style>body{font-family:system-ui;max-width:1100px;margin:40px auto}pre{white-space:pre-wrap;background:#f6f6f6;padding:12px;border-radius:8px}</style>"
        + "\n".join(body),
        encoding="utf-8",
    )


def run_ts_runner(
    role: str,
    case_path: Path,
    candidate_prompt: Path | None,
    mock_mode: str,
    extension_src: Path | None = None,
    *,
    backend: str = "openai-compatible",
    model: str | None = None,
    thinking_level: str | None = None,
) -> dict[str, Any]:
    runner = ARTIFACT_ROOT / "runners" / f"{role}_replay.ts"
    cmd = ["npx", "-y", "tsx", str(runner), "--case", str(case_path), "--mock-mode", mock_mode, "--backend", backend]
    if model:
        cmd += ["--model", model]
    if thinking_level:
        cmd += ["--thinking-level", thinking_level]
    if candidate_prompt:
        cmd += ["--candidate-prompt", str(candidate_prompt)]
    if extension_src:
        cmd += ["--extension-src", str(extension_src)]
    proc = subprocess.run(cmd, cwd=REPO_ROOT, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"runner failed ({proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"runner did not emit JSON\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}") from exc


def role_arg(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--role", choices=["observer", "reflector"], required=True, help="Prompt role to operate on. Dropper is intentionally excluded.")

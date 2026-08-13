#!/usr/bin/env python3
"""Build the five-config testing-skills mechanism trajectory analysis."""

from __future__ import annotations

import html
import importlib.util
import json
import math
import re
import statistics
import tomllib
from collections import Counter, defaultdict
from itertools import pairwise
from pathlib import Path
from typing import Any, cast

REPO = Path(__file__).resolve().parents[2]
RESULTS = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")
SUBSET = REPO / "subsets/testing_skills_24_v0.txt"
OUT = REPO / "analysis/testing-skills-mechanism-pilot"
PACKETS = OUT / "packets"
REPORT = REPO / "reports/testing-skills-mechanism-pilot"
CONFIGS = tuple(f"testing-skills@1.{minor}.0" for minor in range(1, 6))
LOCKS = {
    "testing-skills@1.1.0": "sha256:fc27e36bb3e113548a12c958abbc5a7a4b08f1059cb9261d330b8160dc8bcf54",
    "testing-skills@1.2.0": "sha256:18aeac3ac63571b89844aa7f037eb6d4b7f21b983e6173f2fb0bf7b3593150f9",
    "testing-skills@1.3.0": "sha256:c7f892fba1a669b17969e58e816af0eaaf5e70c8e1d2d8706c21adac3acd282f",
    "testing-skills@1.4.0": "sha256:c31fe8e169a587e8d846869854f11b3cf2c5a2ee5542868fae1393abcf0ab2a4",
    "testing-skills@1.5.0": "sha256:03e28384e7b8520c9bfc8f9fc97ff7abde95791f5c787aee822589a0a66e2ca7",
}
STEP_NAMES = {
    (
        "testing-skills@1.1.0",
        "testing-skills@1.2.0",
    ): "Contract cards + outer-surface evidence",
    ("testing-skills@1.2.0", "testing-skills@1.3.0"): "Final-patch evidence + stopping",
    ("testing-skills@1.3.0", "testing-skills@1.4.0"): "Property-testing Commit/Return",
    (
        "testing-skills@1.4.0",
        "testing-skills@1.5.0",
    ): "Fuzzing admission + bounded completion",
}
SKILLS = ("testing", "property-based-testing", "fuzzing")
VALIDATION = re.compile(
    r"\b(test|pytest|cargo test|go test|npm test|pnpm test|yarn test|vitest|jest|ruff|mypy|pyright|tsc|lint|check|build)\b",
    re.IGNORECASE,
)
TEST_PATH = re.compile(
    r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.", re.IGNORECASE
)
PROPERTY_PATTERN = re.compile(
    r"\b(@given|hypothesis\.given|fc\.assert|proptest!|quickcheck!|rapid\.Check|testing/quick)\b",
    re.IGNORECASE,
)
FUZZ_PATTERN = re.compile(
    r"\b(func\s+Fuzz\w*\s*\([^)]*\*testing\.F|cargo[_ -]?fuzz|libfuzzer|afl\+\+)\b",
    re.IGNORECASE,
)

spec = importlib.util.spec_from_file_location(
    "full113_helpers", REPO / "analysis/testing-skills-1.1.0/full113_analysis.py"
)
assert spec and spec.loader
helpers = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helpers)


def tasks() -> list[str]:
    return [
        line.strip()
        for line in SUBSET.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def metadata(task: str) -> dict[str, str]:
    document = tomllib.loads((TASKS_ROOT / task / "task.toml").read_text())
    meta = document["metadata"]
    return {
        "title": meta.get("display_title") or meta.get("original_title") or task,
        "language": meta.get("language", "unknown"),
        "category": meta.get("category", "unknown"),
    }


def cell_path(config: str, task: str, rep: int) -> Path:
    return RESULTS / config / task / f"rep{rep}"


def load_cells(task_names: list[str]) -> dict[tuple[str, str, int], dict[str, Any]]:
    cells: dict[tuple[str, str, int], dict[str, Any]] = {}
    for config in CONFIGS:
        for task in task_names:
            for rep in range(3):
                path = cell_path(config, task, rep)
                result_path = path / "result.json"
                if not result_path.exists():
                    raise RuntimeError(f"Missing result: {result_path}")
                result = json.loads(result_path.read_text())
                expected = {
                    "config_lock_identity": LOCKS[config],
                    "model": "openai-codex/gpt-5.6-sol",
                    "thinking_level": "low",
                    "subject_version": "pi@0.84.1",
                    "agent_exit": 0,
                    "agent_timed_out": False,
                    "verifier_exit": 0,
                }
                for field, value in expected.items():
                    if result.get(field) != value:
                        raise RuntimeError(
                            f"{config}/{task}/rep{rep}: {field}={result.get(field)!r}, expected {value!r}"
                        )
                cells[(config, task, rep)] = {"path": path, "result": result}
    return cells


def assistant_text(path: Path) -> str:
    chunks: list[str] = []
    for record in helpers.read_session_records(path):
        message = record.get("message", {})
        if message.get("role") != "assistant":
            continue
        for part in message.get("content", []):
            if isinstance(part, dict) and part.get("type") in ("text", "thinking"):
                chunks.append(str(part.get("text", "")))
    return "\n".join(chunks)


def patch_excerpt(path: Path, limit: int = 140) -> str:
    lines = helpers.patch_text(path).splitlines()
    return "\n".join(lines[:limit]) + ("\n…" if len(lines) > limit else "")


def trajectory(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    timeline = helpers.compact_tool_timeline(path)
    mutations = [
        event["ordinal"]
        for event in timeline
        if event["tool"] in ("edit", "write") and event["is_error"] is not True
    ]
    first_mutation = min(mutations) if mutations else None
    last_mutation = max(mutations) if mutations else None
    validations = [
        event
        for event in timeline
        if event["tool"] == "bash" and VALIDATION.search(event["summary"])
    ]
    final_validations = [
        event
        for event in validations
        if last_mutation is None or event["ordinal"] > last_mutation
    ]
    audits = [
        event
        for event in timeline
        if event["tool"] == "bash" and re.search(r"git (diff|status)", event["summary"])
    ]
    final_audits = [
        event
        for event in audits
        if last_mutation is None or event["ordinal"] > last_mutation
    ]
    patch = helpers.patch_summary(path)
    added = "\n".join(helpers.added_patch_lines(path))
    text = assistant_text(path)
    reads = helpers.skill_reads(path)
    return {
        "skill_reads": reads,
        "assistant_contract_card": bool(
            re.search(r"(?m)^\s*(Contract|Preservation|Primary search):", text)
        ),
        "assistant_commit_or_return": bool(
            re.search(r"(?m)^\s*(Commit|Return):", text)
        ),
        "first_mutation_ordinal": first_mutation,
        "last_mutation_ordinal": last_mutation,
        "successful_reads_before_first_mutation": sum(
            event["tool"] == "read"
            and event["is_error"] is False
            and (first_mutation is None or event["ordinal"] < first_mutation)
            for event in timeline
        ),
        "validation_commands": len(validations),
        "final_patch_validation_commands": len(final_validations),
        "final_patch_validation_tail": [
            event["summary"] for event in final_validations[-6:]
        ],
        "completion_audits_after_final_mutation": len(final_audits),
        "test_patch": any(TEST_PATH.search(p) for p in patch["changed_paths"]),
        "property_test_patch": bool(PROPERTY_PATTERN.search(added)),
        "fuzz_target_patch": bool(FUZZ_PATTERN.search(added)),
        "patch": patch,
        "tool_calls": len(timeline),
        "tool_errors": sum(event["is_error"] is True for event in timeline),
        "successful_exact_reads": helpers.successful_exact_reads(path),
        "timeline": timeline,
        "termination": {
            "agent_exit": result.get("agent_exit"),
            "agent_timed_out": result.get("agent_timed_out"),
            "verifier_exit": result.get("verifier_exit"),
        },
    }


def metrics(result: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "combined_total_tokens",
        "combined_cost_usd",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_timed_out",
        "verifier_exit",
    )
    return {field: result.get(field) for field in fields}


def outcome_class(left: dict[str, Any], right: dict[str, Any]) -> str:
    ls = left["reward_binary"] == 1
    rs = right["reward_binary"] == 1
    if not ls and rs:
        return "gain"
    if ls and not rs:
        return "loss"
    if ls and rs:
        return "both"
    return "neither"


def driver(losing: dict[str, Any], reciprocal: bool) -> str:
    if reciprocal:
        return "likely variance"
    if losing.get("patch_bytes", 0) == 0:
        return "under-implementation"
    if (losing.get("p2p_total") or 0) > (losing.get("p2p_passed") or 0):
        return "cross-scope regression"
    missing = (losing.get("f2p_total") or 0) - (losing.get("f2p_passed") or 0)
    if missing > 3:
        return "under-implementation"
    if missing > 0:
        return "missing invariant/guard"
    return "likely variance"


def mechanism_text(loser_side: str, packet: dict[str, Any], bucket: str) -> str:
    losing = packet[loser_side]
    winning = packet["right" if loser_side == "left" else "left"]
    failed = packet[f"{loser_side}_failed_tests"]
    loser_paths = losing["trajectory"]["patch"]["changed_paths"]
    winner_paths = winning["trajectory"]["patch"]["changed_paths"]
    overlap = sorted(set(loser_paths) & set(winner_paths))
    failure = ", ".join(failed[:3]) if failed else "the remaining graded contract"
    seam = ", ".join(overlap[:3]) if overlap else "different changed-file seams"
    if bucket == "likely variance":
        return f"Rep outcomes reverse elsewhere on this task; patches reached {seam}, so the wording step is not a stable task-level cause."
    if bucket == "cross-scope regression":
        return f"The losing patch changed {', '.join(loser_paths[:3]) or 'no files'} and failed preservation evidence ({failure}); the winning patch passed it."
    if bucket == "under-implementation":
        return f"The losing patch left multiple feature checks unsatisfied ({failure}) at {seam}; the winning trajectory closed more of the requested behavior."
    return f"The losing patch missed a bounded feature invariant ({failure}) at {seam}; the winning trajectory satisfied it."


def exact_mcnemar(gains: int, losses: int) -> float:
    n = gains + losses
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(gains, losses) + 1))
    return min(1.0, 2 * tail / (2**n))


def mean(values: list[float]) -> float:
    return statistics.mean(values) if values else 0.0


def aggregate_config(config: str, task_names: list[str], cells: dict) -> dict[str, Any]:
    group = [cells[(config, task, rep)] for task in task_names for rep in range(3)]
    ts = [item["trajectory"] for item in group]
    rs = [item["result"] for item in group]
    advertised = Counter()
    for item in group:
        prompt = (item["path"] / "initial_context/system_prompt.txt").read_text(
            errors="replace"
        )
        for skill in SKILLS:
            advertised[skill] += f"<name>{skill}</name>" in prompt
    return {
        "cells": len(group),
        "solves": sum(r["reward_binary"] == 1 for r in rs),
        "mean_partial": mean([r["reward_partial"] for r in rs]),
        "mean_tokens": mean([r["combined_total_tokens"] for r in rs]),
        "mean_cost": mean([r["combined_cost_usd"] for r in rs]),
        "mean_wall_s": mean([r["agent_wall_s"] for r in rs]),
        "mean_tool_calls": mean([r["tool_calls"] for r in rs]),
        "advertised": dict(advertised),
        "skill_reads": {
            skill: sum(t["skill_reads"][skill] for t in ts) for skill in SKILLS
        },
        "contract_card_mentions": sum(t["assistant_contract_card"] for t in ts),
        "commit_or_return_mentions": sum(t["assistant_commit_or_return"] for t in ts),
        "test_patch_cells": sum(t["test_patch"] for t in ts),
        "property_test_patch_cells": sum(t["property_test_patch"] for t in ts),
        "fuzz_target_patch_cells": sum(t["fuzz_target_patch"] for t in ts),
        "mean_final_patch_validations": mean(
            [t["final_patch_validation_commands"] for t in ts]
        ),
        "final_patch_validation_cells": sum(
            t["final_patch_validation_commands"] > 0 for t in ts
        ),
        "completion_audit_cells": sum(
            t["completion_audits_after_final_mutation"] > 0 for t in ts
        ),
        "tool_results": sum(t["tool_calls"] for t in ts),
        "tool_errors": sum(t["tool_errors"] for t in ts),
        "resource_exhausted_cells": sum(
            bool(
                r.get("agent_resource_exhausted")
                or (r.get("subject_memory_events") or {}).get("oom_kill")
            )
            for r in rs
        ),
    }


def build() -> dict[str, Any]:
    task_names = tasks()
    metas = {task: metadata(task) for task in task_names}
    cells = load_cells(task_names)
    for item in cells.values():
        item["trajectory"] = trajectory(item["path"], item["result"])

    config_summary = {
        config: aggregate_config(config, task_names, cells) for config in CONFIGS
    }
    comparisons = []
    selected_packets = []
    full_ledger = []
    for left_config, right_config in pairwise(CONFIGS):
        raw_rows = []
        directions: dict[str, set[str]] = defaultdict(set)
        for task in task_names:
            for rep in range(3):
                left_cell = cells[(left_config, task, rep)]
                right_cell = cells[(right_config, task, rep)]
                left_metrics = metrics(left_cell["result"])
                right_metrics = metrics(right_cell["result"])
                outcome = outcome_class(left_metrics, right_metrics)
                if outcome in ("gain", "loss"):
                    directions[task].add(outcome)
                raw_rows.append(
                    (
                        task,
                        rep,
                        left_cell,
                        right_cell,
                        left_metrics,
                        right_metrics,
                        outcome,
                    )
                )
        reciprocal_tasks = {
            task for task, ds in directions.items() if ds == {"gain", "loss"}
        }
        rows = []
        for task, rep, left_cell, right_cell, lm, rm, outcome in raw_rows:
            partial_delta = rm["reward_partial"] - lm["reward_partial"]
            reasons = []
            if outcome in ("gain", "loss"):
                reasons.append("binary_solve_flip")
            if abs(partial_delta) >= 0.05:
                reasons.append("absolute_partial_delta_at_least_0.05")
            if bool(lm["agent_timed_out"]) != bool(rm["agent_timed_out"]):
                reasons.append("timeout_discordance")
            packet_id = f"{left_config.split('@')[1]}_to_{right_config.split('@')[1]}__{task}__rep{rep}"
            row = {
                "step": STEP_NAMES[(left_config, right_config)],
                "left_config": left_config,
                "right_config": right_config,
                "task": task,
                "rep": rep,
                "language": metas[task]["language"],
                "outcome": outcome,
                "left": lm,
                "right": rm,
                "partial_delta": partial_delta,
                "selection_reasons": reasons,
                "packet": f"packets/{packet_id}.json" if reasons else None,
            }
            rows.append(row)
            full_ledger.append(row)
            if reasons:
                reciprocal = task in reciprocal_tasks
                losing_side = (
                    "left" if lm["reward_partial"] < rm["reward_partial"] else "right"
                )
                losing = lm if losing_side == "left" else rm
                bucket = driver(losing, reciprocal)
                packet = {
                    **row,
                    "title": metas[task]["title"],
                    "category": metas[task]["category"],
                    "left": {
                        "metrics": lm,
                        "trajectory": left_cell["trajectory"],
                        "patch_excerpt": patch_excerpt(left_cell["path"]),
                    },
                    "right": {
                        "metrics": rm,
                        "trajectory": right_cell["trajectory"],
                        "patch_excerpt": patch_excerpt(right_cell["path"]),
                    },
                    "left_failed_tests": helpers.failed_verifier_tests(
                        left_cell["path"]
                    ),
                    "right_failed_tests": helpers.failed_verifier_tests(
                        right_cell["path"]
                    ),
                    "primary_driver": bucket,
                    "first_consequential_divergence": helpers.first_consequential_divergence(
                        left_cell["trajectory"]["patch"],
                        right_cell["trajectory"]["patch"],
                        lm,
                        rm,
                    ),
                    "mechanism": "",
                    "confidence": "grading- and trajectory-backed driver; wording causality is directional unless repeated across cells",
                }
                packet["mechanism"] = mechanism_text(losing_side, packet, bucket)
                selected_packets.append((packet_id, packet))
        gains = sum(row["outcome"] == "gain" for row in rows)
        losses = sum(row["outcome"] == "loss" for row in rows)
        comparisons.append(
            {
                "step": STEP_NAMES[(left_config, right_config)],
                "left": left_config,
                "right": right_config,
                "pairs": 72,
                "left_solves": config_summary[left_config]["solves"],
                "right_solves": config_summary[right_config]["solves"],
                "gains": gains,
                "losses": losses,
                "both": sum(row["outcome"] == "both" for row in rows),
                "neither": sum(row["outcome"] == "neither" for row in rows),
                "mean_partial_delta": mean(
                    [cast(float, row["partial_delta"]) for row in rows]
                ),
                "median_partial_delta": statistics.median(
                    cast(float, row["partial_delta"]) for row in rows
                ),
                "mcnemar_p": exact_mcnemar(gains, losses),
                "reciprocal_tasks": sorted(reciprocal_tasks),
                "selected_packets": sum(bool(row["selection_reasons"]) for row in rows),
                "language_splits": {
                    lang: {
                        "pairs": len(group),
                        "gains": sum(row["outcome"] == "gain" for row in group),
                        "losses": sum(row["outcome"] == "loss" for row in group),
                    }
                    for lang, group in sorted(
                        (
                            (lang, [r for r in rows if r["language"] == lang])
                            for lang in sorted({str(r["language"]) for r in rows})
                        ),
                        key=lambda item: item[0],
                    )
                },
            }
        )

    packet_index = []
    PACKETS.mkdir(parents=True, exist_ok=True)
    report_packets = REPORT / "packets"
    report_packets.mkdir(parents=True, exist_ok=True)
    for packet_id, packet in selected_packets:
        packet_text = json.dumps(packet, indent=2, sort_keys=True) + "\n"
        packet_path = PACKETS / f"{packet_id}.json"
        packet_path.write_text(packet_text)
        (report_packets / f"{packet_id}.json").write_text(packet_text)
        packet_index.append(
            {
                "id": packet_id,
                "step": packet["step"],
                "task": packet["task"],
                "rep": packet["rep"],
                "outcome": packet["outcome"],
                "driver": packet["primary_driver"],
                "mechanism": packet["mechanism"],
                "path": f"packets/{packet_id}.json",
            }
        )

    driver_counts = Counter(
        p["driver"] for p in packet_index if p["outcome"] in ("gain", "loss")
    )
    matrix = []
    for task in task_names:
        for rep in range(3):
            matrix.append(
                {
                    "task": task,
                    "rep": rep,
                    "language": metas[task]["language"],
                    "outcomes": {
                        config: cells[(config, task, rep)]["result"]["reward_binary"]
                        for config in CONFIGS
                    },
                    "partials": {
                        config: cells[(config, task, rep)]["result"]["reward_partial"]
                        for config in CONFIGS
                    },
                }
            )

    return {
        "scope": {
            "question": "Which cumulative testing-skill wording mechanisms changed same-model trajectories on the approved diagnostic cohort?",
            "roles": "All five sides are same-model config controls; no local model or frontier contrast is present.",
            "subset": "testing_skills_24_v0",
            "selection_caveat": "Mechanism-diagnostic and outcome-informed; not an unbiased full-corpus efficacy estimate.",
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "tasks": 24,
            "reps": 3,
            "configs": 5,
            "trajectories": 360,
            "adjacent_matched_pairs": 288,
        },
        "provenance": {
            "config_locks": LOCKS,
            "candidate_launch_plan": "sha256:9b6b17e2420df4cce1924ef56ba59eac5db2978535be7603749e18ae3a7da206",
            "all_cells_agent_exit_zero": True,
            "all_cells_verifier_exit_zero": True,
            "timeouts": 0,
            "resource_exhausted_cells": sum(
                v["resource_exhausted_cells"] for v in config_summary.values()
            ),
            "delivery": "All three skills advertised in all 72 cells per config; reads reported separately.",
        },
        "config_summary": config_summary,
        "comparisons": comparisons,
        "packet_rule": "Every adjacent pair with a binary flip, timeout discordance, or absolute partial-reward delta of at least 0.05.",
        "packet_count": len(packet_index),
        "flip_count": sum(p["outcome"] in ("gain", "loss") for p in packet_index),
        "driver_counts": dict(driver_counts),
        "packets": packet_index,
        "matrix": matrix,
        "ledger": full_ledger,
        "decision": {
            "recommendation": "Advance testing-skills@1.2.0 alone to the full 113-task comparison against the reused testing-skills@1.1.0 baseline.",
            "reason": "It led the diagnostic cohort at 25/72 versus 18/72, with 12 gains and 5 losses. Every later cumulative step reduced its score and did not show a stable compensating trajectory benefit.",
            "expected_reuse": "Reuse all 339 testing-skills@1.1.0 cells and the 72 completed testing-skills@1.2.0 pilot cells if the full-113 selector contains this cohort; execute only missing compatible candidate cells.",
            "do_not_advance": [
                "testing-skills@1.3.0",
                "testing-skills@1.4.0",
                "testing-skills@1.5.0",
            ],
        },
    }


def esc(value: Any) -> str:
    return html.escape(str(value))


def pill(outcome: int) -> str:
    return (
        '<span class="pill good">✓</span>'
        if outcome == 1
        else '<span class="pill bad">×</span>'
    )


def render(data: dict[str, Any]) -> str:
    summaries = data["config_summary"]
    steps = data["comparisons"]
    cards = "".join(
        f'<div class="stat"><span>{esc(c.split("@")[1])}</span><strong>{s["solves"]}/72</strong><small>{s["mean_partial"]:.3f} mean partial</small></div>'
        for c, s in summaries.items()
    )
    step_rows = "".join(
        f"<tr><td><strong>{esc(s['step'])}</strong><br><code>{esc(s['left'].split('@')[1])} → {esc(s['right'].split('@')[1])}</code></td>"
        f'<td>{s["left_solves"]} → {s["right_solves"]}</td><td class="good-text">+{s["gains"]}</td><td class="bad-text">−{s["losses"]}</td>'
        f"<td>{s['mean_partial_delta']:+.4f}</td><td>{s['mcnemar_p']:.3f}</td><td>{esc(', '.join(s['reciprocal_tasks']) or 'none')}</td></tr>"
        for s in steps
    )
    delivery_rows = "".join(
        f"<tr><td><code>{esc(c)}</code></td><td>{s['skill_reads']['testing']}</td><td>{s['skill_reads']['property-based-testing']}</td><td>{s['skill_reads']['fuzzing']}</td>"
        f"<td>{s['contract_card_mentions']}</td><td>{s['final_patch_validation_cells']}</td><td>{s['mean_final_patch_validations']:.2f}</td>"
        f"<td>{s['test_patch_cells']}</td><td>{s['property_test_patch_cells']}</td><td>{s['fuzz_target_patch_cells']}</td></tr>"
        for c, s in summaries.items()
    )
    packet_rows = "".join(
        f"<tr><td>{esc(p['step'])}</td><td><code>{esc(p['task'])}</code> / rep{p['rep']}</td>"
        f'<td><span class="tag {"good" if p["outcome"] == "gain" else "bad" if p["outcome"] == "loss" else "caution"}">{esc(p["outcome"])}</span></td>'
        f'<td>{esc(p["driver"])}</td><td>{esc(p["mechanism"])}</td><td><a href="{esc(p["path"])}">packet</a></td></tr>'
        for p in data["packets"]
        if p["outcome"] in ("gain", "loss")
    )
    config_headers = "".join(
        f"<th>{esc(config.split('@')[1])}</th>" for config in CONFIGS
    )
    matrix_rows = "".join(
        "<tr><td><code>{}</code></td><td>{}</td><td>{}</td>{}</tr>".format(
            esc(row["task"]),
            row["rep"],
            esc(row["language"]),
            "".join(
                f"<td>{pill(row['outcomes'][c])}<small>{row['partials'][c]:.3f}</small></td>"
                for c in CONFIGS
            ),
        )
        for row in data["matrix"]
    )
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Testing skills mechanism pilot</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#667085;--blue:#2563eb;--green:#16835b;--red:#c24141;--amber:#b7791f;--line:#dfe5ef}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 Inter,ui-sans-serif,system-ui,sans-serif}}main{{max-width:1500px;margin:auto;padding:32px}}.hero{{background:linear-gradient(135deg,#172554,#1d4ed8);color:white;border-radius:20px;padding:34px;margin-bottom:22px}}h1{{font-size:38px;line-height:1.05;margin:8px 0 12px}}h2{{margin-top:32px}}.hero p{{max-width:900px;font-size:18px}}.eyebrow{{text-transform:uppercase;letter-spacing:.12em;font-weight:800;font-size:12px}}.pills{{display:flex;gap:8px;flex-wrap:wrap}}.pill,.tag{{display:inline-block;border-radius:999px;padding:3px 9px;font-weight:700;font-size:12px}}.pill.good,.tag.good{{background:#d8f4e8;color:#08714a}}.pill.bad,.tag.bad{{background:#fee2e2;color:#a32020}}.tag.caution,.pill.caution{{background:#fff0c2;color:#8a5a00}}.pill.neutral{{background:#e9eef8;color:#344054}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}}.stat{{background:var(--surface);padding:18px;border:1px solid var(--line);border-radius:14px}}.stat span,.stat small{{display:block;color:var(--muted)}}.stat strong{{display:block;font-size:30px}}.callout{{background:var(--surface);border:1px solid var(--line);border-left:5px solid var(--blue);padding:18px 20px;border-radius:10px;margin:18px 0}}.callout.good{{border-left-color:var(--green)}}.callout.caution{{border-left-color:var(--amber)}}.table-wrap{{overflow:auto;background:var(--surface);border:1px solid var(--line);border-radius:12px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:10px 12px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eef3fa;z-index:1;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}code{{font-size:12px}}a{{color:var(--blue)}}.good-text{{color:var(--green);font-weight:800}}.bad-text{{color:var(--red);font-weight:800}}td small{{display:block;color:var(--muted)}}.matrix td{{white-space:nowrap}}@media(max-width:900px){{main{{padding:14px}}.stats{{grid-template-columns:1fr 1fr}}h1{{font-size:30px}}}}</style></head><body><main>
<section class="hero"><div class="eyebrow">24 tasks × 3 reps × 5 cumulative configs</div><h1>Keep the contract-card redesign. Stop the cumulative stack.</h1><p><strong>testing-skills@1.2.0</strong> rose from 18 to 25 solves on the diagnostic cohort. The next three wording additions fell back to 20, 21, and 19. Adjacent trajectories show heavy churn and weak activation of the later specialist protocols, not a stable compensating benefit.</p><div class="pills"><span class="pill good">Advance 1.2.0</span><span class="pill bad">Do not advance 1.3–1.5</span><span class="pill caution">Diagnostic cohort, not efficacy estimate</span><span class="pill neutral">360 trajectories · 288 adjacent pairs</span></div></section>
<div class="stats">{cards}</div>
<div class="callout good"><strong>Overnight decision:</strong> compile a full-113 plan for <code>testing-skills@1.2.0</code> against the already evaluated <code>testing-skills@1.1.0</code> baseline. Reuse all compatible baseline and pilot cells. Do not spend the night on the later cumulative versions.</div>
<h2>Each wording mechanism against its immediate predecessor</h2><div class="table-wrap"><table><thead><tr><th>Mechanism</th><th>Solves</th><th>Gains</th><th>Losses</th><th>Mean partial Δ</th><th>McNemar p</th><th>Reciprocal-flip tasks</th></tr></thead><tbody>{step_rows}</tbody></table></div>
<div class="callout caution"><strong>Interpretation:</strong> 1.2.0 has the strongest directional signal (12 gains, 5 losses), but the exact paired p-value is not decisive and the cohort was selected to expose mechanisms. A full-113 confirmation is the correct next experiment. Reciprocal task flips are classified as likely variance rather than forced into a wording story.</div>
<h2>Delivery and trajectory behavior</h2><div class="table-wrap"><table><thead><tr><th>Config</th><th>Testing reads</th><th>PBT reads</th><th>Fuzz reads</th><th>Explicit contract-card output</th><th>Cells validating final patch</th><th>Mean final validations</th><th>Test patches</th><th>Property patches</th><th>Fuzz targets</th></tr></thead><tbody>{delivery_rows}</tbody></table></div>
<div class="callout"><strong>Observed activation:</strong> all skills were advertised in every cell. Testing reads reached 72/72 from 1.2 onward. Property-testing reads fell 15 → 3 after its Commit/Return rewrite. In 1.5, neither specialist was read in any cell. The late mechanisms therefore did not reliably reach the behavior they were meant to improve.</div>
<h2>Every adjacent solve flip ({data["flip_count"]})</h2><p>Drivers come from patch, feature/preservation grading, failed-test, validation, and reciprocal-rep evidence. “Likely variance” means the same task flipped both ways across reps or no narrower grading-backed cause survived review.</p><div class="table-wrap"><table><thead><tr><th>Step</th><th>Cell</th><th>Direction</th><th>Primary driver</th><th>Evidence-backed mechanism</th><th>Evidence</th></tr></thead><tbody>{packet_rows}</tbody></table></div>
<h2>Complete task × rep outcome table</h2><p>Each cell shows binary outcome and partial reward. This table precedes no hidden filtering: 72 rows × 5 configs are all 360 trajectories.</p><div class="table-wrap"><table class="matrix"><thead><tr><th>Task</th><th>Rep</th><th>Language</th>{config_headers}</tr></thead><tbody>{matrix_rows}</tbody></table></div>
<h2>Conclusion</h2><div class="callout good"><strong>Keep:</strong> the 1.2 contract inventory, explicit primary-search choice, and outer-surface evidence requirement. It improved the diagnostic score while making testing guidance load consistently.</div><div class="callout caution"><strong>Do not keep yet:</strong> the 1.3 final-evidence rewrite, 1.4 property Commit/Return protocol, or 1.5 fuzzing admission protocol as cumulative releases. They need smaller, separately activated A/B designs; the current wording either added friction or failed to route into the specialist skill.</div><div class="callout"><strong>Scope:</strong> same GPT-5.6 Sol model, low thinking, Pi 0.84.1, 24 outcome-informed diagnostic tasks, three reps. No cell timed out. One 1.3 trajectory recorded an OOM kill but still solved; excluding it changes no score or flip. This report supports experiment selection, not a full-corpus product claim.</div>
</main></body></html>"""


def main() -> None:
    data = build()
    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.mkdir(parents=True, exist_ok=True)
    (OUT / "trajectory-analysis.json").write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n"
    )
    (REPORT / "index.html").write_text(render(data))
    print(
        json.dumps(
            {
                "trajectories": data["scope"]["trajectories"],
                "adjacent_pairs": data["scope"]["adjacent_matched_pairs"],
                "packets": data["packet_count"],
                "flips": data["flip_count"],
                "solves": {c: s["solves"] for c, s in data["config_summary"].items()},
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

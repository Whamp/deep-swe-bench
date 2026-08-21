#!/usr/bin/env python3
"""Build the testing-skills 1.2.0 versus 1.2.1 diagnostic analysis."""

from __future__ import annotations

import html
import importlib.util
import json
import math
import random
import re
import statistics
import tomllib
from collections import Counter
from pathlib import Path
from typing import Any

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
TASKS_ROOT = Path("/home/will/evals/deep-swe/tasks")
SELECTOR_PATH = REPOSITORY_ROOT / "subsets/testing_skills_24_v0.txt"
DESIGN_PATH = Path(__file__).with_name("diagnostic-design.json")
ANALYSIS_PATH = Path(__file__).with_name("diagnostic-analysis.json")
PACKETS_PATH = Path(__file__).with_name("packets")
REPORT_PATH = REPOSITORY_ROOT / "reports/testing-skills-1.2.1-diagnostic"
REPORT_PACKETS_PATH = REPORT_PATH / "packets"
LEFT_CONFIG = "testing-skills@1.2.0"
RIGHT_CONFIG = "testing-skills@1.2.1"
CONFIGS = (LEFT_CONFIG, RIGHT_CONFIG)
EXPECTED_LOCKS = {
    LEFT_CONFIG: "sha256:18aeac3ac63571b89844aa7f037eb6d4b7f21b983e6173f2fb0bf7b3593150f9",
    RIGHT_CONFIG: "sha256:f5821ae907594a5c7f73bbbbb943f76845b0745be18d3898178176d95f911730",
}
PLAN_IDENTITY = (
    "sha256:336967509df73073a0a2ea71aa2ae973b8f8d202f4005341d7e9dfbd88656319"
)
SKILL_NAMES = ("testing", "property-based-testing", "fuzzing")
SPECIALIST_SKILLS = ("property-based-testing", "fuzzing")
TEST_PATH_PATTERN = re.compile(
    r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.", re.IGNORECASE
)
PROPERTY_ARTIFACT_PATTERN = re.compile(
    r"\b(@given|hypothesis\.given|fc\.assert|proptest!|quickcheck!|rapid\.Check|testing/quick)\b",
    re.IGNORECASE,
)
FUZZ_ARTIFACT_PATTERN = re.compile(
    r"\b(func\s+Fuzz\w*\s*\([^)]*\*testing\.F|cargo[_ -]?fuzz|libfuzzer|afl\+\+)\b",
    re.IGNORECASE,
)
PACKET_PARTIAL_THRESHOLD = 0.05

FLIP_CLASSIFICATIONS: dict[tuple[str, int], dict[str, str]] = {
    ("textual-richlog-follow-state", 1): {
        "driver": "missing invariant/guard",
        "confidence": "medium",
        "mechanism": "v1.2.0 missed the expanded-write RichLog observation; v1.2.1 exercised the same outer journey and passed all 20 feature checks.",
    },
    ("task-task-graph-export", 2): {
        "driver": "missing invariant/guard",
        "confidence": "medium",
        "mechanism": "v1.2.0 missed the no-dependencies graph case; v1.2.1 covered it while changing the same five-file seam.",
    },
    ("drizzle-orm-window-function-builders", 0): {
        "driver": "under-implementation",
        "confidence": "medium",
        "mechanism": "v1.2.0 missed 26 frame and OVER-clause variants across dialects; v1.2.1 closed all 130 feature checks at the same cross-dialect seam.",
    },
    ("dynamodb-toolbox-lazy-recursive-schemas", 1): {
        "driver": "under-implementation",
        "confidence": "low",
        "mechanism": "v1.2.1 left 16 recursive DTO, parsing, formatting, finder, and JSON-schema checks unsatisfied; the task is unstable because its other reps favor neither config consistently.",
    },
    ("returns-validated-error-accumulation", 1): {
        "driver": "validation gap",
        "confidence": "medium",
        "mechanism": "v1.2.1 stopped with three ValidatedLikeN short-circuit laws failing after a broad-suite failure; v1.2.0 implemented and passed those interface laws.",
    },
    ("prometheus-typed-label-sorting", 1): {
        "driver": "likely variance",
        "confidence": "high",
        "mechanism": "Prometheus flips once in each direction across reps; both configs use the same typed-comparator seam and differ by one or two uncovered ordering cases.",
    },
    ("prometheus-typed-label-sorting", 2): {
        "driver": "likely variance",
        "confidence": "high",
        "mechanism": "Prometheus flips once in each direction across reps; v1.2.1 missed duration ordering while another v1.2.1 rep gained two related cases.",
    },
    ("psd-tools-blend-range-api", 0): {
        "driver": "protocol/interface drift",
        "confidence": "high",
        "mechanism": "v1.2.1 omitted the Layer.blend_ranges setter. All eight failed checks assign through that public property before checking persistence or compositing; two v1.2.0 reps supplied the setter and passed.",
    },
    ("psd-tools-blend-range-api", 2): {
        "driver": "protocol/interface drift",
        "confidence": "high",
        "mechanism": "v1.2.1 repeated the missing Layer.blend_ranges setter from rep0, causing the identical eight AttributeError failures across setter, save/reopen, and compositing journeys.",
    },
    ("tomlkit-toml-table-converters", 2): {
        "driver": "under-implementation",
        "confidence": "low",
        "mechanism": "v1.2.1 missed eight nested, dotted, inline, comment-placement, and round-trip conversions; the other two reps remained unsolved on both sides.",
    },
    ("dynamodb-toolbox-conditional-attribute-requirements", 0): {
        "driver": "likely variance",
        "confidence": "high",
        "mechanism": "The task flips once each way on the same anyOf DTO round-trip check, with a stable third rep; no config-level direction is supported.",
    },
    ("dynamodb-toolbox-conditional-attribute-requirements", 1): {
        "driver": "likely variance",
        "confidence": "high",
        "mechanism": "The task flips once each way on the same anyOf DTO round-trip check, with a stable third rep; no config-level direction is supported.",
    },
    ("termenv-preserve-ansi-resets", 2): {
        "driver": "missing invariant/guard",
        "confidence": "medium",
        "mechanism": "v1.2.1 missed width-zero OSC truncation. v1.2.0 added and ran a fuzz target and passed; v1.2.1 read property guidance instead and added no generated-search artifact, but the routing link remains correlational.",
    },
}

_helper_spec = importlib.util.spec_from_file_location(
    "full113_helpers",
    REPOSITORY_ROOT / "analysis/testing-skills-1.1.0/full113_analysis.py",
)
assert _helper_spec and _helper_spec.loader
helpers = importlib.util.module_from_spec(_helper_spec)
_helper_spec.loader.exec_module(helpers)


def selected_task_names() -> list[str]:
    """Read the ordered 24-task diagnostic selector."""
    return [
        line.strip()
        for line in SELECTOR_PATH.read_text().splitlines()
        if line.strip() and not line.startswith("#")
    ]


def task_metadata(task: str) -> dict[str, str]:
    """Read stable report labels for one benchmark task."""
    metadata = tomllib.loads((TASKS_ROOT / task / "task.toml").read_text())["metadata"]
    return {
        "title": metadata.get("display_title")
        or metadata.get("original_title")
        or task,
        "language": metadata.get("language", "unknown"),
        "category": metadata.get("category", "unknown"),
    }


def result_cell_path(config: str, task: str, rep: int) -> Path:
    """Return one canonical result-cell directory."""
    return RESULTS_ROOT / config / task / f"rep{rep}"


def resource_flagged(result: dict[str, Any]) -> bool:
    """Report subject or verifier resource exhaustion from canonical evidence."""
    subject_events = result.get("subject_memory_events") or {}
    verifier_events = result.get("verifier_memory_events") or {}
    return bool(
        result.get("agent_resource_exhausted")
        or result.get("verifier_resource_exhausted")
        or subject_events.get("oom_kill")
        or verifier_events.get("oom_kill")
    )


def load_and_verify_cells(
    tasks: list[str],
) -> dict[tuple[str, str, int], dict[str, Any]]:
    """Load all 144 trajectories and verify comparison provenance and delivery."""
    cells: dict[tuple[str, str, int], dict[str, Any]] = {}
    for config in CONFIGS:
        for task in tasks:
            for rep in range(3):
                path = result_cell_path(config, task, rep)
                result_path = path / "result.json"
                if not result_path.is_file():
                    raise FileNotFoundError(f"Missing diagnostic result: {result_path}")
                result = json.loads(result_path.read_text())
                expected = {
                    "config": config,
                    "config_lock_identity": EXPECTED_LOCKS[config],
                    "model": "openai-codex/gpt-5.6-sol",
                    "thinking_level": "low",
                    "subject_version": "pi@0.84.1",
                    "agent_exit": 0,
                    "agent_timed_out": False,
                    "verifier_exit": 0,
                }
                for field, value in expected.items():
                    if result.get(field) != value:
                        raise ValueError(
                            f"{config}/{task}/rep{rep}: {field}={result.get(field)!r}; expected {value!r}"
                        )
                prompt = (path / "initial_context/system_prompt.txt").read_text(
                    errors="replace"
                )
                advertised = {
                    skill: f"<name>{skill}</name>" in prompt for skill in SKILL_NAMES
                }
                if not all(advertised.values()):
                    raise ValueError(
                        f"Skill delivery missing for {config}/{task}/rep{rep}: {advertised}"
                    )
                cells[(config, task, rep)] = {
                    "path": path,
                    "result": result,
                    "advertised": advertised,
                }
    if len(cells) != 144:
        raise ValueError(f"Expected 144 trajectories, found {len(cells)}")
    return cells


def selected_result_metrics(result: dict[str, Any]) -> dict[str, Any]:
    """Select stable result metrics for ledgers and packets."""
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
        "tool_calls",
        "turns",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
    )
    metrics = {field: result.get(field) for field in fields}
    metrics["resource_flagged"] = resource_flagged(result)
    return metrics


def solved(result: dict[str, Any]) -> bool:
    """Count only binary reward 1 as solved."""
    return result.get("reward_binary") == 1


def paired_outcome(left: dict[str, Any], right: dict[str, Any]) -> str:
    """Classify one matched binary result pair."""
    if not solved(left) and solved(right):
        return "gain"
    if solved(left) and not solved(right):
        return "loss"
    if solved(left) and solved(right):
        return "both"
    return "neither"


def specialist_read_details(path: Path) -> dict[str, Any]:
    """Extract specialist read order and whether relevant inspection preceded it."""
    timeline = helpers.compact_tool_timeline(path)
    details: dict[str, Any] = {}
    for skill in SPECIALIST_SKILLS:
        matching = [
            event
            for event in timeline
            if event["tool"] == "read"
            and event["summary"] == f"/arm/skills/{skill}/SKILL.md"
            and event["is_error"] is False
        ]
        if not matching:
            details[skill] = {
                "read": False,
                "ordinal": None,
                "after_concrete_read": False,
            }
            continue
        ordinal = matching[0]["ordinal"]
        prior_concrete_reads = [
            event
            for event in timeline
            if event["ordinal"] < ordinal
            and event["tool"] == "read"
            and event["is_error"] is False
            and not event["summary"].startswith("/arm/skills/")
        ]
        details[skill] = {
            "read": True,
            "ordinal": ordinal,
            "after_concrete_read": bool(prior_concrete_reads),
            "prior_concrete_reads": [
                event["summary"] for event in prior_concrete_reads
            ],
        }
    return details


def trajectory_evidence(path: Path) -> dict[str, Any]:
    """Extract routing, patch, test, read, and tool-timeline evidence."""
    patch = helpers.patch_summary(path)
    added_text = "\n".join(helpers.added_patch_lines(path))
    timeline = helpers.compact_tool_timeline(path)
    return {
        "skill_reads": helpers.skill_reads(path),
        "specialist_read_details": specialist_read_details(path),
        "patch": patch,
        "test_patch": any(
            TEST_PATH_PATTERN.search(name) for name in patch["changed_paths"]
        ),
        "property_artifact": bool(PROPERTY_ARTIFACT_PATTERN.search(added_text)),
        "fuzz_artifact": bool(FUZZ_ARTIFACT_PATTERN.search(added_text)),
        "failed_verifier_tests": helpers.failed_verifier_tests(path),
        "successful_exact_reads": helpers.successful_exact_reads(path),
        "tool_calls_observed": len(timeline),
        "tool_errors_observed": sum(event["is_error"] is True for event in timeline),
        "timeline": timeline,
        "patch_excerpt": "\n".join(helpers.patch_text(path).splitlines()[:140]),
    }


def exact_mcnemar_p(gains: int, losses: int) -> float:
    """Return the exact two-sided McNemar p-value for discordant pairs."""
    discordant = gains + losses
    if discordant == 0:
        return 1.0
    tail = sum(math.comb(discordant, k) for k in range(min(gains, losses) + 1))
    return min(1.0, 2 * tail / (2**discordant))


def percentile_interval(values: list[float]) -> tuple[float, float]:
    """Return a deterministic empirical 95% interval."""
    ordered = sorted(values)
    return ordered[int(0.025 * len(ordered))], ordered[int(0.975 * len(ordered))]


def bootstrap_solve_intervals(
    cell_deltas: list[int], task_deltas: dict[str, list[int]], samples: int = 50_000
) -> dict[str, Any]:
    """Bootstrap paired cells and whole three-rep task clusters separately."""
    task_names = list(task_deltas)
    output: dict[str, Any] = {}
    for mode in ("paired_cells", "task_clusters"):
        rng = random.Random(20260813)
        estimates: list[float] = []
        for _ in range(samples):
            if mode == "paired_cells":
                draw = [rng.choice(cell_deltas) for _ in cell_deltas]
                estimate = statistics.mean(draw) * 100
            else:
                draw = [rng.choice(task_names) for _ in task_names]
                estimate = (
                    sum(sum(task_deltas[task]) for task in draw) / (len(draw) * 3) * 100
                )
            estimates.append(estimate)
        low, high = percentile_interval(estimates)
        output[mode] = {
            "samples": samples,
            "seed": 20260813,
            "low_points": low,
            "high_points": high,
            "probability_positive": sum(value > 0 for value in estimates) / samples,
            "probability_nonnegative": sum(value >= 0 for value in estimates) / samples,
        }
    return output


def aggregate_config(
    config: str, tasks: list[str], cells: dict[tuple[str, str, int], dict[str, Any]]
) -> dict[str, Any]:
    """Aggregate efficacy, efficiency, delivery, routing, and artifact metrics."""
    group = [cells[(config, task, rep)] for task in tasks for rep in range(3)]
    results = [item["result"] for item in group]
    return {
        "cells": len(group),
        "solves": sum(solved(result) for result in results),
        "mean_partial": statistics.mean(result["reward_partial"] for result in results),
        "tokens": sum(result["combined_total_tokens"] for result in results),
        "cost": sum(result["combined_cost_usd"] for result in results),
        "wall_s": sum(result["agent_wall_s"] for result in results),
        "tool_calls": sum(result["tool_calls"] for result in results),
        "turns": sum(result["turns"] for result in results),
        "patch_bytes": sum(result["patch_bytes"] for result in results),
        "advertised": {
            skill: sum(item["advertised"][skill] for item in group)
            for skill in SKILL_NAMES
        },
        "skill_reads": {
            skill: sum(item["trajectory"]["skill_reads"][skill] for item in group)
            for skill in SKILL_NAMES
        },
        "specialist_read_cells": sum(
            any(item["trajectory"]["skill_reads"][skill] for skill in SPECIALIST_SKILLS)
            for item in group
        ),
        "specialist_reads_after_concrete_inspection": sum(
            any(
                item["trajectory"]["specialist_read_details"][skill][
                    "after_concrete_read"
                ]
                for skill in SPECIALIST_SKILLS
            )
            for item in group
        ),
        "test_patch_cells": sum(item["trajectory"]["test_patch"] for item in group),
        "property_artifact_cells": sum(
            item["trajectory"]["property_artifact"] for item in group
        ),
        "fuzz_artifact_cells": sum(
            item["trajectory"]["fuzz_artifact"] for item in group
        ),
        "resource_flagged_cells": sum(resource_flagged(result) for result in results),
        "agent_failures": sum(result.get("agent_exit") != 0 for result in results),
        "verifier_failures": sum(
            result.get("verifier_exit") != 0 for result in results
        ),
    }


def stratum_task_names(design: dict[str, Any]) -> dict[str, list[str]]:
    """Flatten the predeclared diagnostic strata into ordered task lists."""
    strata: dict[str, list[str]] = {}
    for item in design["strata"]:
        tasks: list[str] = []
        for key, value in item.items():
            if key in {"name", "mechanism"} or not isinstance(value, list):
                continue
            tasks.extend(
                entry["task"] if isinstance(entry, dict) else entry for entry in value
            )
        strata[item["name"]] = tasks
    return strata


def aggregate_strata(
    design: dict[str, Any], cells: dict[tuple[str, str, int], dict[str, Any]]
) -> dict[str, Any]:
    """Aggregate solves, partial reward, feature misses, and routing by stratum."""
    output: dict[str, Any] = {}
    for name, tasks in stratum_task_names(design).items():
        configs: dict[str, Any] = {}
        for config in CONFIGS:
            group = [cells[(config, task, rep)] for task in tasks for rep in range(3)]
            configs[config] = {
                "pairs": len(group),
                "solves": sum(solved(item["result"]) for item in group),
                "mean_partial": statistics.mean(
                    item["result"]["reward_partial"] for item in group
                ),
                "missed_feature_checks": sum(
                    max(
                        0,
                        (item["result"].get("f2p_total") or 0)
                        - (item["result"].get("f2p_passed") or 0),
                    )
                    for item in group
                ),
                "specialist_read_cells": sum(
                    any(
                        item["trajectory"]["skill_reads"][skill]
                        for skill in SPECIALIST_SKILLS
                    )
                    for item in group
                ),
            }
        output[name] = {"tasks": tasks, "configs": configs}
    return output


def routing_gate_evidence(
    design: dict[str, Any], cells: dict[tuple[str, str, int], dict[str, Any]]
) -> dict[str, Any]:
    """Evaluate routing controls, qualified opportunities, and conversion artifacts."""
    routing = next(
        item for item in design["strata"] if item["name"] == "routing-discriminative"
    )
    qualified = {entry["task"] for entry in routing["qualifiedGeneratedSearch"]}
    controls = {entry["task"] for entry in routing["enumerableExampleControls"]}

    def cohort(config: str, tasks: set[str]) -> dict[str, Any]:
        group = [
            cells[(config, task, rep)] for task in sorted(tasks) for rep in range(3)
        ]
        return {
            "cells": len(group),
            "specialist_read_cells": sum(
                any(
                    item["trajectory"]["skill_reads"][skill]
                    for skill in SPECIALIST_SKILLS
                )
                for item in group
            ),
            "property_reads": sum(
                item["trajectory"]["skill_reads"]["property-based-testing"]
                for item in group
            ),
            "fuzz_reads": sum(
                item["trajectory"]["skill_reads"]["fuzzing"] for item in group
            ),
            "property_artifacts": sum(
                item["trajectory"]["property_artifact"] for item in group
            ),
            "fuzz_artifacts": sum(
                item["trajectory"]["fuzz_artifact"] for item in group
            ),
            "reads_after_concrete_inspection": sum(
                any(
                    item["trajectory"]["specialist_read_details"][skill][
                        "after_concrete_read"
                    ]
                    for skill in SPECIALIST_SKILLS
                )
                for item in group
            ),
        }

    changed_status: list[dict[str, Any]] = []
    for task in selected_task_names():
        for rep in range(3):
            left = cells[(LEFT_CONFIG, task, rep)]
            right = cells[(RIGHT_CONFIG, task, rep)]
            left_specialist = any(
                left["trajectory"]["skill_reads"][skill] for skill in SPECIALIST_SKILLS
            )
            right_specialist = any(
                right["trajectory"]["skill_reads"][skill] for skill in SPECIALIST_SKILLS
            )
            if left_specialist == right_specialist:
                continue
            changed_status.append(
                {
                    "task": task,
                    "rep": rep,
                    "left_specialist": left_specialist,
                    "right_specialist": right_specialist,
                    "outcome": paired_outcome(left["result"], right["result"]),
                }
            )
    return {
        "qualified": {config: cohort(config, qualified) for config in CONFIGS},
        "enumerable_controls": {config: cohort(config, controls) for config in CONFIGS},
        "changed_specialist_status": changed_status,
        "changed_status_binary_flips": sum(
            item["outcome"] in {"gain", "loss"} for item in changed_status
        ),
    }


def build_analysis() -> dict[str, Any]:
    """Build the complete diagnostic ledger and packet set."""
    tasks = selected_task_names()
    if len(tasks) != 24 or len(set(tasks)) != 24:
        raise ValueError("Diagnostic selector must contain exactly 24 unique tasks")
    design = json.loads(DESIGN_PATH.read_text())
    metadata = {task: task_metadata(task) for task in tasks}
    cells = load_and_verify_cells(tasks)
    for cell in cells.values():
        cell["trajectory"] = trajectory_evidence(cell["path"])

    config_summary = {
        config: aggregate_config(config, tasks, cells) for config in CONFIGS
    }
    ledger: list[dict[str, Any]] = []
    task_deltas: dict[str, list[int]] = {}
    selected_packet_rows: list[dict[str, Any]] = []
    outcomes = Counter()
    cell_deltas: list[int] = []
    for task in tasks:
        task_deltas[task] = []
        for rep in range(3):
            left = cells[(LEFT_CONFIG, task, rep)]
            right = cells[(RIGHT_CONFIG, task, rep)]
            outcome = paired_outcome(left["result"], right["result"])
            outcomes[outcome] += 1
            binary_delta = int(solved(right["result"])) - int(solved(left["result"]))
            partial_delta = (
                right["result"]["reward_partial"] - left["result"]["reward_partial"]
            )
            cell_deltas.append(binary_delta)
            task_deltas[task].append(binary_delta)
            row = {
                "task": task,
                "title": metadata[task]["title"],
                "language": metadata[task]["language"],
                "rep": rep,
                "outcome": outcome,
                "binary_delta": binary_delta,
                "partial_delta": partial_delta,
                "left": selected_result_metrics(left["result"]),
                "right": selected_result_metrics(right["result"]),
                "left_skill_reads": left["trajectory"]["skill_reads"],
                "right_skill_reads": right["trajectory"]["skill_reads"],
            }
            selected = (
                outcome in {"gain", "loss"}
                or abs(partial_delta) >= PACKET_PARTIAL_THRESHOLD
            )
            if selected:
                classification = FLIP_CLASSIFICATIONS.get((task, rep))
                if classification is None:
                    classification = {
                        "driver": "material partial-reward discordance",
                        "confidence": "low",
                        "mechanism": "Both cells remained unsolved; the packet preserves the material verifier-reward movement for review without assigning a binary-flip cause.",
                    }
                packet = {
                    **row,
                    "selection_rule": (
                        "binary flip"
                        if outcome in {"gain", "loss"}
                        else f"absolute partial delta >= {PACKET_PARTIAL_THRESHOLD}"
                    ),
                    "classification": classification,
                    "left_failed_tests": left["trajectory"]["failed_verifier_tests"],
                    "right_failed_tests": right["trajectory"]["failed_verifier_tests"],
                    "left_trajectory": left["trajectory"],
                    "right_trajectory": right["trajectory"],
                }
                packet_name = f"{task}__rep{rep}.json"
                packet["packet"] = f"packets/{packet_name}"
                selected_packet_rows.append(packet)
                row["packet"] = f"packets/{packet_name}"
                row["classification"] = classification
            ledger.append(row)

    task_direction = {
        task: {
            "rep_deltas": deltas,
            "net_solve_delta": sum(deltas),
            "direction": (
                "gain-only"
                if any(value > 0 for value in deltas)
                and not any(value < 0 for value in deltas)
                else "loss-only"
                if any(value < 0 for value in deltas)
                and not any(value > 0 for value in deltas)
                else "mixed-churn"
                if any(value > 0 for value in deltas)
                and any(value < 0 for value in deltas)
                else "stable"
            ),
        }
        for task, deltas in task_deltas.items()
    }
    solve_delta = (
        config_summary[RIGHT_CONFIG]["solves"] - config_summary[LEFT_CONFIG]["solves"]
    )
    statistics_summary = {
        "gains": outcomes["gain"],
        "losses": outcomes["loss"],
        "both": outcomes["both"],
        "neither": outcomes["neither"],
        "solve_delta": solve_delta,
        "solve_rate_delta_points": solve_delta / 72 * 100,
        "mcnemar_exact_two_sided_p": exact_mcnemar_p(
            outcomes["gain"], outcomes["loss"]
        ),
        "bootstrap": bootstrap_solve_intervals(cell_deltas, task_deltas),
        "task_directions": dict(
            Counter(item["direction"] for item in task_direction.values())
        ),
    }

    routing = routing_gate_evidence(design, cells)
    strata = aggregate_strata(design, cells)
    gate_results = [
        {
            "gate": "Delivery integrity",
            "status": "pass",
            "evidence": "144/144 trajectories exist; all 72 cells per config advertise all three skills; agent/verifier exits are clean and no cell is resource-flagged.",
        },
        {
            "gate": "Binary efficacy",
            "status": "fail",
            "evidence": "v1.2.1 has 5 gains and 8 losses (22 vs 25 solves), so gains are fewer than losses.",
        },
        {
            "gate": "Partial efficacy",
            "status": "fail",
            "evidence": f"Mean partial reward changes from {config_summary[LEFT_CONFIG]['mean_partial']:.4f} to {config_summary[RIGHT_CONFIG]['mean_partial']:.4f}.",
        },
        {
            "gate": "No repeated regression family",
            "status": "fail",
            "evidence": "PSD Blend Range reps 0 and 2 repeat the same missing public setter and identical eight AttributeError failures; v1.2.1 is 0/3 versus v1.2.0 at 2/3.",
        },
        {
            "gate": "Enumerable-control routing reduction",
            "status": "not demonstrated",
            "evidence": "The four enumerable controls had zero specialist reads under both configs (0/12 to 0/12); the cohort provides no positive baseline routing to reduce by 50%.",
        },
        {
            "gate": "Post-inspection specialist routing",
            "status": "fail",
            "evidence": f"0/{config_summary[RIGHT_CONFIG]['specialist_read_cells']} v1.2.1 specialist-read cells read a concrete source or test file before the specialist skill.",
        },
        {
            "gate": "Qualified campaign preservation",
            "status": "fail",
            "evidence": "Qualified tasks fell from two executed fuzz-target patches to zero; property-based artifacts remained zero.",
        },
        {
            "gate": "Interaction completeness",
            "status": "fail",
            "evidence": f"The coupled-contract stratum's missed feature checks rose from {strata['coupled-contract']['configs'][LEFT_CONFIG]['missed_feature_checks']} to {strata['coupled-contract']['configs'][RIGHT_CONFIG]['missed_feature_checks']} despite one more solve.",
        },
        {
            "gate": "Boundary discipline",
            "status": "pass with limited evidence",
            "evidence": "No repeated loss was traced to broadening an implementation seam from an observation path; boundary-risk tasks had no binary flips. This does not offset failures in other gates.",
        },
        {
            "gate": "Token efficiency",
            "status": "fail",
            "evidence": f"Tokens increased {(config_summary[RIGHT_CONFIG]['tokens'] / config_summary[LEFT_CONFIG]['tokens'] - 1) * 100:.1f}% instead of decreasing at least 5%.",
        },
        {
            "gate": "Cost efficiency",
            "status": "fail",
            "evidence": f"Cost increased {(config_summary[RIGHT_CONFIG]['cost'] / config_summary[LEFT_CONFIG]['cost'] - 1) * 100:.1f}% instead of remaining non-increasing.",
        },
    ]

    return {
        "schema_version": 1,
        "comparison": {
            "left": LEFT_CONFIG,
            "right": RIGHT_CONFIG,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "selector": "testing_skills_24_v0",
            "tasks": 24,
            "reps_per_task": 3,
            "matched_pairs": 72,
            "plan_identity": PLAN_IDENTITY,
            "interpretation": "Outcome-informed mechanism diagnostic; not an unbiased full-corpus efficacy estimate.",
        },
        "provenance": {
            "config_locks": EXPECTED_LOCKS,
            "delivery": "delivered",
            "resource_flagged_cells": 0,
            "agent_failures": 0,
            "verifier_failures": 0,
            "timeouts": 0,
        },
        "config_summary": config_summary,
        "statistics": statistics_summary,
        "routing": routing,
        "strata": strata,
        "task_direction": task_direction,
        "gate_results": gate_results,
        "decision": {
            "verdict": "reject v1.2.1; do not expand to full 113",
            "basis": "The candidate loses overall and creates a repeated regression family, satisfying the predeclared reject rule. Routing timing also fails, qualified artifacts decline, and efficiency worsens.",
            "next_step": "Keep v1.2.0 as the optimization base. Do not iterate another wording-only router immediately; move the deferred offline specialist-tooling experiment behind executable tool surfaces and preserve explicit public setter/assignment journeys in any later testing revision.",
        },
        "packet_selection": {
            "rule": f"Every binary flip or absolute partial-reward delta >= {PACKET_PARTIAL_THRESHOLD}",
            "packets": len(selected_packet_rows),
            "binary_flip_packets": sum(
                row["outcome"] in {"gain", "loss"} for row in selected_packet_rows
            ),
        },
        "ledger": ledger,
        "packets": selected_packet_rows,
    }


def escape(value: object) -> str:
    """HTML-escape one report value."""
    return html.escape(str(value))


def outcome_badge(outcome: str) -> str:
    """Render a stable paired-outcome badge."""
    kind = {"gain": "good", "loss": "bad", "both": "neutral", "neither": "neutral"}[
        outcome
    ]
    return f'<span class="pill {kind}">{escape(outcome)}</span>'


def render_report(data: dict[str, Any]) -> str:
    """Render the self-contained diagnostic HTML report."""
    left = data["config_summary"][LEFT_CONFIG]
    right = data["config_summary"][RIGHT_CONFIG]
    stats = data["statistics"]
    rows = []
    for row in data["ledger"]:
        packet = (
            f'<a href="{escape(row["packet"])}">packet</a>'
            if row.get("packet")
            else "—"
        )
        rows.append(
            "<tr>"
            f"<td><code>{escape(row['task'])}</code></td><td>{row['rep']}</td><td>{escape(row['language'])}</td>"
            f"<td>{outcome_badge(row['outcome'])}</td><td>{row['left']['reward_binary']}</td><td>{row['right']['reward_binary']}</td>"
            f"<td>{row['partial_delta']:+.4f}</td><td>{packet}</td></tr>"
        )
    gate_rows = []
    for gate in data["gate_results"]:
        status = gate["status"]
        kind = (
            "good"
            if status == "pass"
            else "caution"
            if "limited" in status or status == "not demonstrated"
            else "bad"
        )
        gate_rows.append(
            f'<tr><td>{escape(gate["gate"])}</td><td><span class="tag {kind}">{escape(status)}</span></td><td>{escape(gate["evidence"])}</td></tr>'
        )
    packet_rows = []
    for packet in data["packets"]:
        classification = packet["classification"]
        packet_rows.append(
            "<tr>"
            f'<td><a href="{escape(packet["packet"])}"><code>{escape(packet["task"])}/rep{packet["rep"]}</code></a></td>'
            f"<td>{outcome_badge(packet['outcome'])}</td><td>{escape(classification['driver'])}</td>"
            f"<td>{escape(classification['confidence'])}</td><td>{escape(classification['mechanism'])}</td></tr>"
        )
    task_rows = []
    for task, item in data["task_direction"].items():
        task_rows.append(
            f"<tr><td><code>{escape(task)}</code></td><td>{escape(item['direction'])}</td><td>{escape(item['rep_deltas'])}</td><td>{item['net_solve_delta']:+d}</td></tr>"
        )
    cluster = stats["bootstrap"]["task_clusters"]
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 16 16%22><circle cx=%228%22 cy=%228%22 r=%227%22 fill=%22%232f6feb%22/></svg>">
<title>Testing skills v1.2.1 diagnostic</title>
<style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#65708a;--blue:#2f6feb;--green:#14804a;--red:#c9362b;--amber:#a96700;--line:#dbe2ef}}*{{box-sizing:border-box}}html,body{{overflow-x:hidden}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 system-ui,sans-serif}}main{{max-width:1220px;margin:auto;padding:28px}}.hero{{background:linear-gradient(135deg,#14233d,#254f8f);color:white;padding:32px;border-radius:18px}}h1{{margin:0 0 10px;font-size:clamp(28px,5vw,48px);line-height:1.05}}h2{{margin-top:34px}}.hero p{{max-width:850px;color:#dce8ff}}.pills{{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}}.pill,.tag{{display:inline-block;padding:4px 9px;border-radius:999px;font-weight:700;font-size:12px}}.pill.good,.tag.good{{background:#d9f4e5;color:#096b3b}}.pill.bad,.tag.bad{{background:#ffe1de;color:#a3231b}}.pill.caution,.tag.caution{{background:#fff0c9;color:#815000}}.pill.neutral,.tag.neutral{{background:#e9eef7;color:#44506a}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:18px 0}}.stat,.callout,.panel{{background:var(--surface);border:1px solid var(--line);border-radius:14px;padding:18px}}.stat strong{{display:block;font-size:28px}}.stat span{{color:var(--muted)}}.callout.bad{{border-left:5px solid var(--red)}}.callout.good{{border-left:5px solid var(--green)}}table{{width:100%;border-collapse:collapse;background:var(--surface);border-radius:12px;overflow:hidden}}th,td{{padding:10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}th{{background:#edf2fa;font-size:12px;text-transform:uppercase;letter-spacing:.04em}}code{{overflow-wrap:anywhere}}.scroll{{overflow-x:auto;border:1px solid var(--line);border-radius:12px}}.bar{{height:10px;background:#dce4f1;border-radius:6px;overflow:hidden;margin:5px 0}}.bar>i{{display:block;height:100%;background:var(--blue)}}a{{color:var(--blue)}}small,.muted{{color:var(--muted)}}@media(max-width:600px){{main{{padding:14px}}.hero{{padding:22px}}th,td{{padding:8px;font-size:13px}}}}
</style></head><body><main>
<section class="hero"><h1>v1.2.1 does not earn expansion</h1><p>The clarity rewrite reduced speculative specialist loading, but it did not move routing after inspection, produced no specialist artifacts, lost 3 solves, and repeated one public-interface regression in two reps. This 24-task cohort is diagnostic, not a full-corpus efficacy estimate.</p><div class="pills"><span class="pill bad">Reject v1.2.1</span><span class="pill neutral">72 matched pairs</span><span class="pill neutral">3 reps × 24 tasks</span><span class="pill good">Clean delivery</span></div></section>
<div class="stats"><div class="stat"><strong>{left["solves"]} → {right["solves"]}</strong><span>binary solves</span></div><div class="stat"><strong>{stats["gains"]} / {stats["losses"]}</strong><span>gains / losses</span></div><div class="stat"><strong>{left["mean_partial"]:.3f} → {right["mean_partial"]:.3f}</strong><span>mean partial reward</span></div><div class="stat"><strong>{(right["tokens"] / left["tokens"] - 1) * 100:+.1f}%</strong><span>tokens</span></div><div class="stat"><strong>{(right["cost"] / left["cost"] - 1) * 100:+.1f}%</strong><span>cost</span></div><div class="stat"><strong>{right["specialist_read_cells"]}</strong><span>v1.2.1 specialist-read cells</span></div></div>
<section class="callout bad"><h2>Decision</h2><p><strong>Do not launch the remaining 267 full-set calls.</strong> The predeclared reject rule fires twice: the candidate loses overall, and PSD Blend Range repeats the same missing-setter regression in two reps. Keep v1.2.0 as the optimization base.</p></section>
<h2>What the small sample says</h2><div class="panel"><p>Five cells improved and eight regressed. Exact McNemar p={stats["mcnemar_exact_two_sided_p"]:.3f}; this does not prove a population-level loss. The task-cluster bootstrap is also wide ({cluster["low_points"]:.1f} to {cluster["high_points"]:.1f} solve-rate points) and gives only {cluster["probability_positive"] * 100:.1f}% probability of a positive delta. The decision does not depend on statistical significance: this was a predeclared mechanism screen, and its promotion gates failed.</p><p>At task level: {stats["task_directions"].get("gain-only", 0)} gain-only, {stats["task_directions"].get("loss-only", 0)} loss-only, {stats["task_directions"].get("mixed-churn", 0)} mixed-churn, and {stats["task_directions"].get("stable", 0)} stable tasks. Resampling whole tasks preserves correlation among each task's three reps.</p></div>
<h2>Routing result</h2><div class="stats"><div class="stat"><strong>{left["specialist_read_cells"]} → {right["specialist_read_cells"]}</strong><span>specialist-read cells</span></div><div class="stat"><strong>0 / {right["specialist_read_cells"]}</strong><span>routed after concrete file inspection</span></div><div class="stat"><strong>{left["fuzz_artifact_cells"]} → {right["fuzz_artifact_cells"]}</strong><span>fuzz-target patches</span></div><div class="stat"><strong>0 → 0</strong><span>property-test patches</span></div></div>
<section class="callout bad"><p>The wording reduced specialist reads, but not through the intended mechanism. All 13 v1.2.1 specialist reads still happened before a concrete source or test-file read. The 10 cells whose specialist-read status changed had zero binary flips, so reduced loading does not explain the −3 solve delta. The enumerable controls were already 0/12 under v1.2.0, making the planned “50% reduction” gate uninformative.</p></section>
<h2>Predeclared gates</h2><div class="scroll"><table><thead><tr><th>Gate</th><th>Status</th><th>Evidence</th></tr></thead><tbody>{"".join(gate_rows)}</tbody></table></div>
<h2>Trajectory diagnosis</h2><div class="scroll"><table><thead><tr><th>Cell</th><th>Outcome</th><th>Driver</th><th>Confidence</th><th>Evidence-backed mechanism</th></tr></thead><tbody>{"".join(packet_rows)}</tbody></table></div>
<section class="callout bad"><h3>Repeated regression: PSD Blend Range</h3><p>v1.2.1 converged on the same incomplete public interface in all three reps: it implemented a readable <code>Layer.blend_ranges</code> property but omitted its assignment setter. Reps 0 and 2 therefore flipped from solved to unsolved; all three v1.2.1 reps failed the same eight verifier checks with <code>AttributeError</code>. The failures cover direct assignment, save/reopen persistence, and compositing journeys. This is stronger than a single-rep score change.</p></section>
<section class="callout good"><h3>Keep these patterns</h3><p>The intended outer-observation behavior still has value. Textual rep1 fixed the previously missed expanded RichLog journey. Task Graph rep2 closed the no-dependencies case. Drizzle rep0 covered 26 missing cross-dialect frame variants. These are real gains, but they do not isolate a wording clause and do not compensate for the repeated PSD interface regression.</p></section>
<h2>Task-level directions</h2><div class="scroll"><table><thead><tr><th>Task</th><th>Direction</th><th>Rep deltas</th><th>Net</th></tr></thead><tbody>{"".join(task_rows)}</tbody></table></div>
<h2>Complete 72-pair ledger</h2><p class="muted">Packets are selected for every binary flip or absolute partial-reward movement of at least {PACKET_PARTIAL_THRESHOLD:.2f}; all other pairs remain visible here.</p><div class="scroll"><table><thead><tr><th>Task</th><th>Rep</th><th>Language</th><th>Outcome</th><th>v1.2.0</th><th>v1.2.1</th><th>Partial Δ</th><th>Evidence</th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>
<h2>Conclusion</h2><section class="callout bad"><p><strong>Reject v1.2.1 and stop this branch of wording-only optimization.</strong> Small-sample uncertainty means “v1.2.1 is globally worse” would be too strong. The narrower claim is well supported: v1.2.1 failed the diagnostic gates it was designed to pass. The next useful experiment is the deferred offline specialist-tooling design, where executable tool availability—not more routing prose—can test conversion into real property and fuzz artifacts.</p></section>
<p><small>Generated from canonical result, native session, patch, and verifier artifacts. Plan {escape(PLAN_IDENTITY)}. Report scope: same-model config control, openai-codex/gpt-5.6-sol at low thinking.</small></p>
</main></body></html>"""


def write_analysis_artifacts(data: dict[str, Any]) -> None:
    """Write deterministic JSON packets and the self-contained report."""
    PACKETS_PATH.mkdir(parents=True, exist_ok=True)
    REPORT_PACKETS_PATH.mkdir(parents=True, exist_ok=True)
    for old in PACKETS_PATH.glob("*.json"):
        old.unlink()
    for old in REPORT_PACKETS_PATH.glob("*.json"):
        old.unlink()
    for packet in data["packets"]:
        name = Path(packet["packet"]).name
        payload = json.dumps(packet, indent=2, sort_keys=True) + "\n"
        (PACKETS_PATH / name).write_text(payload)
        (REPORT_PACKETS_PATH / name).write_text(payload)
    ANALYSIS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.mkdir(parents=True, exist_ok=True)
    (REPORT_PATH / "index.html").write_text(render_report(data))


def main() -> None:
    """Build and publish all local analysis artifacts."""
    data = build_analysis()
    write_analysis_artifacts(data)
    print(
        json.dumps(
            {
                "analysis": str(ANALYSIS_PATH),
                "report": str(REPORT_PATH / "index.html"),
                "packets": data["packet_selection"]["packets"],
                "verdict": data["decision"]["verdict"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

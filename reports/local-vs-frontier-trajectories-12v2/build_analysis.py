#!/usr/bin/env python3
"""Build a local-model versus frontier trajectory comparison dataset."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import statistics
import tomllib
from pathlib import Path
from typing import Any

from trajectory_evidence import (
    classify_repository_file,
    extract_trajectory_evidence,
    load_result,
    parse_changed_files,
)

REPORT_ROOT = Path(__file__).resolve().parent
DEFAULT_SOURCE_ROOT = Path(
    os.environ.get("DEEP_SWE_BENCH_SOURCE_ROOT", "/home/will/evals/deep-swe-bench")
)
RESULT_ROOTS = {
    "frontier": Path("results/gpt-5.6-sol/high/baseline"),
    "agentworld": Path(
        "results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0"
    ),
    "thinkingcap": Path(
        "results/thinkingcap-qwen3.6-27b-awq-int4/high/"
        "baseline-thinkingcap-qwen36@1.1.0"
    ),
}
DISPLAY_NAMES = {
    "frontier": "GPT-5.6 SOL high",
    "agentworld": "Qwen-AgentWorld 35B-A3B",
    "thinkingcap": "ThinkingCap Qwen3.6 27B",
}
SELECTED_PACKET_CELLS = [
    ("adaptix-name-mapping-aliases", 0),
    ("claude-code-by-agents-recursive-delegation", 0),
    ("goreleaser-retry-publish-auditing", 2),
    ("langchain-request-coalescing", 0),
    ("mobly-grouped-test-barriers", 0),
    ("sql-formatter-bigquery-pipe-formatting", 0),
    ("sql-formatter-bigquery-pipe-formatting", 1),
    ("superjson-error-stack-serialization", 1),
    ("tengo-callable-instance-isolation", 0),
]
DECISION_DIVERGENCES = {
    ("adaptix-name-mapping-aliases", 0): {
        "stage": "repository seam selection",
        "frontier_behavior": "Mapped aliases through facade, crown, loader, trail, schema, public docs, and integration tests before finalizing the design.",
        "agentworld_divergence": "Repeatedly debugged a narrow name-layout path and one default-parameters test; it omitted loader, trail, schema, and integration surfaces and passed 2/44 feature tests.",
        "thinkingcap_divergence": "Reached the loader and schema seams but delayed validation until tool event 121; the fixed design missed conflict, trail, and non-mapping invariants and passed 37/44 feature tests.",
        "failure_layer": "repository understanding and execution control",
    },
    ("claude-code-by-agents-recursive-delegation", 0): {
        "stage": "repository seam selection",
        "frontier_behavior": "Integrated delegation into multiAgentChat, the Claude provider, and provider types, then tested the real orchestration path.",
        "agentworld_divergence": "Created a standalone delegate handler wired through chat.ts and never ran validation; all seven recursive-delegation tests failed.",
        "thinkingcap_divergence": "Also created a separate delegation module around chat.ts and validated self-authored tests rather than the multi-agent orchestration contract; all seven feature tests failed.",
        "failure_layer": "repository understanding",
    },
    ("goreleaser-retry-publish-auditing", 2): {
        "stage": "task contract representation",
        "frontier_behavior": "Separated retry policy from publish-attempt records and traced persistence through artifacts, metadata, docs, and generated schemas.",
        "agentworld_divergence": "Read no tests or docs and implemented a smaller retry/attempt surface that omitted metadata and schema persistence; it passed 9/29 feature tests.",
        "thinkingcap_divergence": "Concentrated on retry mechanics and ran many package tests, but omitted artifact attempt records, metadata sorting, docs, and schemas; it passed 2/29 feature tests.",
        "failure_layer": "task analysis and repository understanding",
    },
    ("langchain-request-coalescing", 0): {
        "stage": "execution control",
        "frontier_behavior": "Read wrapper patterns and tests, built focused sync/async/stream probes, added task-specific tests, and validated the runnable suite.",
        "agentworld_divergence": "Reached the correct three implementation files but recorded no validation command; backend protocol, result delivery, batch, and waiter-cancellation cases remained broken.",
        "thinkingcap_divergence": "Read only three source files, no tests or project guidance, then timed out without a validation cycle or completion summary.",
        "failure_layer": "execution control and resource exhaustion",
    },
    ("mobly-grouped-test-barriers", 0): {
        "stage": "implementation plan",
        "frontier_behavior": "Distributed group execution across base_test, controller management, expectations, and records, with dedicated grouped-execution tests and repeated race-sensitive validation.",
        "agentworld_divergence": "Put synchronization in a new global-registry module and changed only base_test plus that module, missing group lifecycle, record attribution, and barrier isolation.",
        "thinkingcap_divergence": "Put most behavior into base_test and self-authored tests, despite reading surrounding modules; hidden failures cluster around barrier lifecycle, group isolation, and per-participant records.",
        "failure_layer": "repository understanding and missing invariants",
    },
    ("sql-formatter-bigquery-pipe-formatting", 0): {
        "stage": "feature completeness",
        "frontier_behavior": "Read the parser, tokenizer, formatter, layout, and their unit tests before editing; it exercised the complete grammar-to-layout path.",
        "agentworld_divergence": "Skipped parser/tokenizer unit tests and several layout/adapter seams; the patch regressed 109 preservation tests and passed no feature tests.",
        "thinkingcap_divergence": "Covered most production seams and preserved existing behavior, but omitted parser/tokenizer unit-test surfaces and produced no passing pipe feature behavior in this rep.",
        "failure_layer": "feature completeness and validation gap",
    },
    ("sql-formatter-bigquery-pipe-formatting", 1): {
        "stage": "local success control",
        "frontier_behavior": "Read 24 files across the parser, tokenizer, formatter, layout, and tests before mutation and solved the task.",
        "agentworld_divergence": "Read 13 files and omitted parser/tokenizer tests and multiple layout seams; 14/26 feature tests failed.",
        "thinkingcap_divergence": "Read 21 files before mutation, including tokenizer engine, parser creation, layout, dialect, and BigQuery keywords, then solved all feature and preservation tests.",
        "failure_layer": "counterexample: the local model can solve when its architecture model is complete",
    },
    ("superjson-error-stack-serialization", 1): {
        "stage": "task contract representation",
        "frontier_behavior": "Represented the feature as a round-trip protocol, changing both transformer and plainer plus annotation, exports, causes, and focused tests.",
        "agentworld_divergence": "Implemented serialization helpers but did not change plainer; annotation, mode, cause restoration, and instance-isolation failures followed, including five preservation regressions.",
        "thinkingcap_divergence": "Read plainer but left it unchanged, treating most work as serialization; cause restoration, AggregateError, depth, and processing-order cases remained.",
        "failure_layer": "task analysis and missing invariant",
    },
    ("tengo-callable-instance-isolation", 0): {
        "stage": "repository seam selection",
        "frontier_behavior": "Traced callables through objects, runtime, script, VM, modules, evaluation, and recursive composite rebinding, then added callable-specific tests.",
        "agentworld_divergence": "Patched compiler, objects, and VM without runtime, script, module, or variable seams; closures, imports, recursion, globals, and returned callables remained broken.",
        "thinkingcap_divergence": "Started mutation after ten files and attached execution to compiled-function/VM paths while omitting runtime and module seams; nested callable rebinding and runtime-frame cases remained.",
        "failure_layer": "repository understanding and core abstraction",
    },
}
SCAFFOLDABILITY_LEDGER = [
    {
        "weakness": "Narrow repeated exploration without expanding the architecture map",
        "evidence": "AgentWorld made 808 read calls across 24 failed pairs but covered a median 11.5 exact files versus the frontier's 16.5, with 43% median frontier-file recall.",
        "failure_layer": "execution control",
        "candidate_support": "Visited-file ledger with a pre-mutation architecture checkpoint",
        "expected_mechanism": "Expose repeated reads and require the agent to name the public API, runtime/data-flow, test, config, and documentation seams before its first mutation.",
        "non_targets": "Does not fix an incorrect abstraction after the relevant files were already read.",
        "risk": "Can force unnecessary browsing on small tasks; gate it on task breadth and repeated-read signals.",
        "minimal_experiment": "AgentWorld same-model A/B on Adaptix, GoReleaser, and Tengo reps; no task-specific paths in the intervention.",
        "success_criterion": "Higher pre-mutation frontier-file recall, fewer repeated reads per unique file, and improved feature tests without higher invalid rate.",
    },
    {
        "weakness": "Requirements are implemented as local mechanics instead of end-to-end contracts",
        "evidence": "GoReleaser locals emphasized retry loops but missed attempt persistence; SuperJSON locals emphasized serialization but missed deserialization; Mobly locals emphasized barriers but missed lifecycle and records.",
        "failure_layer": "task analysis and repository understanding",
        "candidate_support": "Requirement-to-seam ledger",
        "expected_mechanism": "Before coding, map each prompt requirement to its producing seam, consuming seam, persistence or round-trip path, and one observable validation.",
        "non_targets": "Does not supply the correct implementation or reveal hidden tests.",
        "risk": "A verbose ledger can consume context without improving decisions; require concise evidence-backed entries.",
        "minimal_experiment": "Both local models on GoReleaser, SuperJSON, Mobly, and Tengo with the same serving contracts.",
        "success_criterion": "More complete changed-file seam coverage and fewer clustered feature failures in omitted subsystems while preserving p2p.",
    },
    {
        "weakness": "Validation starts after the implementation architecture is difficult to reverse",
        "evidence": "Median first validation occurred at tool event 59 for AgentWorld and 48.5 for ThinkingCap, versus 32 and 31.5 in aligned frontier solves. ThinkingCap ran more validations overall but still retained wrong seams.",
        "failure_layer": "execution control",
        "candidate_support": "Early discriminating-probe gate",
        "expected_mechanism": "Require one small probe for the riskiest invariant before broad implementation, then reopen the plan if it fails.",
        "non_targets": "Does not help when the repository lacks any observable test or probe surface.",
        "risk": "Premature probes can encode the wrong behavior; tie the probe to an explicit prompt invariant.",
        "minimal_experiment": "ThinkingCap same-model A/B on Adaptix, Mobly, SQL formatter, and SuperJSON.",
        "success_criterion": "Earlier validation, at least one plan revision when the probe fails, and higher f2p without more wall-clock time.",
    },
    {
        "weakness": "Long trajectories can spend their budget without reaching a feedback cycle",
        "evidence": "ThinkingCap LangChain rep0 read three exact files, never read a test, never validated, and timed out after 3,600 seconds.",
        "failure_layer": "execution control and resource exhaustion",
        "candidate_support": "Progress-aware timeout intervention",
        "expected_mechanism": "Detect long intervals without new file coverage, patch progress, or validation; interrupt with a compact state summary and require a new hypothesis or controlled stop.",
        "non_targets": "Does not justify blanket longer timeouts and should not interrupt trajectories making measurable progress.",
        "risk": "A noisy detector can break productive deep reasoning; use artifact-level progress signals and conservative thresholds.",
        "minimal_experiment": "ThinkingCap same-model reruns of LangChain with intervention-only changes and the current 3,600-second hard ceiling.",
        "success_criterion": "A completed validation cycle, fewer timeout outcomes, and no increase in early low-quality termination.",
    },
    {
        "weakness": "Completion claims overstate requirement coverage",
        "evidence": "Selected local trajectories repeatedly reported implementation complete or all tests passing while verifier failures covered entire requirement families.",
        "failure_layer": "execution control",
        "candidate_support": "Requirement-coverage completion gate",
        "expected_mechanism": "Before final response, require evidence for every prompt-derived requirement family and name any unvalidated family explicitly.",
        "non_targets": "Cannot use hidden tests or reference patches and does not guarantee the evidence is semantically correct.",
        "risk": "May encourage box-checking; require links to actual files and commands rather than self-attestation.",
        "minimal_experiment": "Both local models across the nine packet cells, using only the user prompt and normal repository tools.",
        "success_criterion": "Fewer unsupported completion claims, broader prompt-derived tests, and improved strict solves or f2p at similar p2p.",
    },
    {
        "weakness": "Local models sometimes call the edit tool with the wrong argument shape",
        "evidence": "Across all 36 cells, AgentWorld made 107 malformed edit calls and ThinkingCap made 19; GPT-5.6 made none. Most put path inside each edit or encoded the edits list as a JSON string.",
        "failure_layer": "tool-use mechanics",
        "candidate_support": "Conservative edit-argument normalizer",
        "expected_mechanism": "Lift one shared nested path to the required top level and decode a stringified edits list only when the transformation is unambiguous; otherwise preserve the current rejection.",
        "non_targets": "Does not repair wrong code, stale oldText, ambiguous multi-file edits, or failed shell commands.",
        "risk": "An over-permissive adapter could apply an edit the model did not intend; normalize only provably equivalent shapes and log every repair.",
        "minimal_experiment": "Same-model A/B for both locals with identical prompts and serving settings, recording normalized calls separately from ordinary edit failures.",
        "success_criterion": "Zero rejected calls for the two recoverable shapes, no increase in unintended edits, fewer wasted turns, and no regression in p2p.",
    },
]


def parse_arguments() -> argparse.Namespace:
    """Parse the source artifact root used to reproduce the report."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, default=DEFAULT_SOURCE_ROOT)
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest of one artifact file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def median(values: list[float]) -> float | None:
    """Return the median of a non-empty sequence or None."""
    return statistics.median(values) if values else None


def mean(values: list[float]) -> float | None:
    """Return the arithmetic mean of a non-empty sequence or None."""
    return statistics.mean(values) if values else None


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    """Keep outcome fields needed to interpret one trajectory."""
    keys = (
        "reward_binary",
        "reward_partial",
        "f2p",
        "f2p_passed",
        "f2p_total",
        "p2p",
        "p2p_passed",
        "p2p_total",
        "total_tokens",
        "output_tokens",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
        "model",
        "config",
        "thinking_level",
    )
    return {key: result.get(key) for key in keys}


def load_task_metadata(tasks_root: Path, task: str) -> dict[str, Any]:
    """Load stable task identity and prompt metadata."""
    task_root = tasks_root / task
    config = tomllib.loads((task_root / "task.toml").read_text())
    metadata = config["metadata"]
    return {
        "task": task,
        "title": metadata["display_title"],
        "description": metadata["display_description"],
        "language": metadata["language"],
        "category": metadata["category"],
        "repository_url": metadata["repository_url"],
        "base_commit_hash": metadata["base_commit_hash"],
        "user_prompt_sha256": sha256_file(task_root / "instruction.md"),
    }


def load_model_cells(
    source_root: Path, tasks: list[str]
) -> dict[str, dict[tuple[str, int], dict[str, Any]]]:
    """Load outcomes and trajectory evidence for all three model roles."""
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]] = {}
    for model_key, relative_root in RESULT_ROOTS.items():
        model_cells = {}
        root = source_root / relative_root
        for task in tasks:
            for rep in range(3):
                cell_root = root / task / f"rep{rep}"
                if not (cell_root / "result.json").exists():
                    raise FileNotFoundError(f"Missing trajectory cell: {cell_root}")
                result = load_result(cell_root)
                model_cells[(task, rep)] = {
                    "artifact_root": str(cell_root),
                    "result": compact_result(result),
                    "trace": extract_trajectory_evidence(cell_root),
                    "changed_files": parse_changed_files(cell_root),
                }
        cells[model_key] = model_cells
    return cells


def summarize_tool_result_delivery(
    model_cells: dict[tuple[str, int], dict[str, Any]],
) -> dict[str, Any]:
    """Aggregate tool-result failures across all 36 cells for one model."""
    summaries = [cell["trace"]["tool_results"] for cell in model_cells.values()]

    def merge_count_map(key: str) -> dict[str, int]:
        names = sorted({name for summary in summaries for name in summary[key]})
        return {
            name: sum(summary[key].get(name, 0) for summary in summaries)
            for name in names
        }

    total = sum(summary["total"] for summary in summaries)
    errors = sum(summary["errors"] for summary in summaries)
    by_tool_total = merge_count_map("by_tool_total")
    by_tool_errors = merge_count_map("by_tool_errors")
    return {
        "cells": len(model_cells),
        "cells_with_errors": sum(summary["errors"] > 0 for summary in summaries),
        "total": total,
        "errors": errors,
        "error_rate": errors / total if total else 0,
        "by_tool": {
            tool: {
                "total": by_tool_total[tool],
                "errors": by_tool_errors.get(tool, 0),
                "error_rate": by_tool_errors.get(tool, 0) / by_tool_total[tool],
            }
            for tool in by_tool_total
        },
        "error_categories": merge_count_map("error_categories"),
        "malformed_edit_shapes": merge_count_map("malformed_edit_shapes"),
    }


def build_outcomes_by_task(
    tasks: list[str], cells: dict[str, dict[tuple[str, int], dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Show solved, unsolved, and invalid outcomes for every task repetition."""
    rows = []
    for task in tasks:
        outcomes = {}
        for model_key in ("frontier", "agentworld", "thinkingcap"):
            outcomes[model_key] = [
                cells[model_key][(task, rep)]["result"]["reward_binary"]
                for rep in range(3)
            ]
        rows.append({"task": task, "outcomes": outcomes})
    return rows


def compare_file_coverage(
    local_trace: dict[str, Any], frontier_trace: dict[str, Any]
) -> dict[str, Any]:
    """Compare one local trajectory's exact file reads with its frontier peer."""
    local_paths = set(local_trace["content_read_paths"])
    frontier_paths = set(frontier_trace["content_read_paths"])
    shared_paths = local_paths & frontier_paths
    local_pre = set(local_trace["pre_mutation_paths"])
    frontier_pre = set(frontier_trace["pre_mutation_paths"])
    return {
        "local_content_files": len(local_paths),
        "frontier_content_files": len(frontier_paths),
        "shared_content_files": len(shared_paths),
        "frontier_file_recall": len(shared_paths) / len(frontier_paths)
        if frontier_paths
        else None,
        "local_file_precision": len(shared_paths) / len(local_paths)
        if local_paths
        else None,
        "local_only_paths": sorted(local_paths - frontier_paths),
        "frontier_only_paths": sorted(frontier_paths - local_paths),
        "shared_paths": sorted(shared_paths),
        "local_pre_mutation_files": len(local_pre),
        "frontier_pre_mutation_files": len(frontier_pre),
        "pre_mutation_frontier_recall": len(local_pre & frontier_pre)
        / len(frontier_pre)
        if frontier_pre
        else None,
    }


def build_frontier_gap_pairs(
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    task_metadata: dict[str, dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Select exact pairs where the frontier solved and one local subject failed."""
    cohorts = {"agentworld": [], "thinkingcap": []}
    for local_key, cohort in cohorts.items():
        for key, local_cell in cells[local_key].items():
            frontier_cell = cells["frontier"][key]
            if frontier_cell["result"]["reward_binary"] != 1:
                continue
            if local_cell["result"]["reward_binary"] == 1:
                continue
            task, rep = key
            cohort.append(
                {
                    "task": task,
                    "rep": rep,
                    "language": task_metadata[task]["language"],
                    "local_result": local_cell["result"],
                    "frontier_result": frontier_cell["result"],
                    "coverage": compare_file_coverage(
                        local_cell["trace"], frontier_cell["trace"]
                    ),
                }
            )
    return cohorts


def sum_category_counts(cells: list[dict[str, Any]], trace_key: str) -> dict[str, int]:
    """Sum per-cell unique file categories without merging paths across tasks."""
    return {
        category: sum(
            cell[trace_key]["content_read_categories"][category] for cell in cells
        )
        for category in ("source", "test", "docs", "config", "other")
    }


def summarize_model_side(cells: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize file focus and decision timing for one aligned cohort side."""
    traces = [cell["trace"] for cell in cells]
    category_counts = sum_category_counts(cells, "trace")
    category_total = sum(category_counts.values())
    return {
        "cells": len(cells),
        "median_content_files": median(
            [trace["content_read_count"] for trace in traces]
        ),
        "mean_content_files": mean([trace["content_read_count"] for trace in traces]),
        "median_pre_mutation_files": median(
            [trace["pre_mutation_count"] for trace in traces]
        ),
        "mean_pre_mutation_files": mean(
            [trace["pre_mutation_count"] for trace in traces]
        ),
        "file_category_counts": category_counts,
        "file_category_shares": {
            category: count / category_total if category_total else 0
            for category, count in category_counts.items()
        },
        "total_read_tool_calls": sum(
            trace["tool_counts"].get("read", 0) for trace in traces
        ),
        "total_successful_explicit_reads": sum(
            len(trace["explicit_read_events"]) for trace in traces
        ),
        "total_shell_content_targets": sum(
            len(trace["shell_content_events"]) for trace in traces
        ),
        "total_search_commands": sum(
            trace["command_counts"].get("search", 0) for trace in traces
        ),
        "total_discovery_commands": sum(
            trace["command_counts"].get("discovery", 0) for trace in traces
        ),
        "total_validation_commands": sum(
            trace["command_counts"].get("validation", 0) for trace in traces
        ),
        "cells_without_test_read": sum(
            trace["first_test_read_event"] is None for trace in traces
        ),
        "cells_without_validation": sum(
            trace["first_validation_event"] is None for trace in traces
        ),
        "cells_validating_before_mutation": sum(
            trace["first_validation_event"] is not None
            and trace["first_mutation_event"] is not None
            and trace["first_validation_event"] < trace["first_mutation_event"]
            for trace in traces
        ),
        "median_first_mutation_event": median(
            [
                trace["first_mutation_event"]
                for trace in traces
                if trace["first_mutation_event"] is not None
            ]
        ),
        "median_first_validation_event": median(
            [
                trace["first_validation_event"]
                for trace in traces
                if trace["first_validation_event"] is not None
            ]
        ),
        "median_changed_files": median([len(cell["changed_files"]) for cell in cells]),
        "cells_changing_tests": sum(
            any(
                classify_repository_file(path) == "test"
                for path in cell["changed_files"]
            )
            for cell in cells
        ),
        "cells_changing_docs": sum(
            any(
                classify_repository_file(path) == "docs"
                for path in cell["changed_files"]
            )
            for cell in cells
        ),
    }


def summarize_gap_cohort(
    local_key: str,
    pair_rows: list[dict[str, Any]],
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> dict[str, Any]:
    """Summarize local and frontier trajectories over one exact failure cohort."""
    keys = [(row["task"], row["rep"]) for row in pair_rows]
    local_cells = [cells[local_key][key] for key in keys]
    frontier_cells = [cells["frontier"][key] for key in keys]
    coverages = [row["coverage"] for row in pair_rows]
    return {
        "selection": "frontier strict solve and local non-solve at the same task/rep",
        "pairs": len(pair_rows),
        "local": summarize_model_side(local_cells),
        "frontier": summarize_model_side(frontier_cells),
        "median_frontier_file_recall": median(
            [
                coverage["frontier_file_recall"]
                for coverage in coverages
                if coverage["frontier_file_recall"] is not None
            ]
        ),
        "mean_frontier_file_recall": mean(
            [
                coverage["frontier_file_recall"]
                for coverage in coverages
                if coverage["frontier_file_recall"] is not None
            ]
        ),
        "median_pre_mutation_frontier_recall": median(
            [
                coverage["pre_mutation_frontier_recall"]
                for coverage in coverages
                if coverage["pre_mutation_frontier_recall"] is not None
            ]
        ),
        "local_reads_fewer_files": sum(
            coverage["local_content_files"] < coverage["frontier_content_files"]
            for coverage in coverages
        ),
        "local_reads_more_files": sum(
            coverage["local_content_files"] > coverage["frontier_content_files"]
            for coverage in coverages
        ),
        "same_file_count": sum(
            coverage["local_content_files"] == coverage["frontier_content_files"]
            for coverage in coverages
        ),
    }


def build_task_gap_summaries(
    local_key: str,
    pair_rows: list[dict[str, Any]],
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> list[dict[str, Any]]:
    """Summarize file coverage and feature gaps by task for one local subject."""
    summaries = []
    tasks = sorted({row["task"] for row in pair_rows})
    for task in tasks:
        rows = [row for row in pair_rows if row["task"] == task]
        keys = [(row["task"], row["rep"]) for row in rows]
        local_traces = [cells[local_key][key]["trace"] for key in keys]
        frontier_traces = [cells["frontier"][key]["trace"] for key in keys]
        summaries.append(
            {
                "task": task,
                "pairs": len(rows),
                "local_mean_content_files": mean(
                    [trace["content_read_count"] for trace in local_traces]
                ),
                "frontier_mean_content_files": mean(
                    [trace["content_read_count"] for trace in frontier_traces]
                ),
                "local_mean_test_files": mean(
                    [trace["content_read_categories"]["test"] for trace in local_traces]
                ),
                "frontier_mean_test_files": mean(
                    [
                        trace["content_read_categories"]["test"]
                        for trace in frontier_traces
                    ]
                ),
                "local_mean_docs_files": mean(
                    [trace["content_read_categories"]["docs"] for trace in local_traces]
                ),
                "frontier_mean_docs_files": mean(
                    [
                        trace["content_read_categories"]["docs"]
                        for trace in frontier_traces
                    ]
                ),
                "mean_frontier_file_recall": mean(
                    [row["coverage"]["frontier_file_recall"] for row in rows]
                ),
                "local_mean_f2p": mean(
                    [
                        row["local_result"]["f2p"]
                        for row in rows
                        if row["local_result"]["f2p"] is not None
                    ]
                ),
                "frontier_mean_f2p": mean(
                    [row["frontier_result"]["f2p"] for row in rows]
                ),
            }
        )
    return summaries


def parse_verifier_failures(cell_root: Path) -> dict[str, Any]:
    """Extract verifier summary and failed test names when grading completed."""
    ctrf_path = cell_root / "verifier/ctrf.json"
    if not ctrf_path.exists():
        return {"summary": None, "failed_tests": []}
    ctrf = json.loads(ctrf_path.read_text())
    tests = ctrf["results"]["tests"]
    return {
        "summary": ctrf["results"]["summary"],
        "failed_tests": [
            test["name"] for test in tests if test.get("status") == "failed"
        ],
    }


def compact_packet_trace(trace: dict[str, Any]) -> dict[str, Any]:
    """Keep reviewable trajectory detail for one selected cell."""
    thinking = trace["thinking_samples"]
    if len(thinking) > 12:
        thinking = thinking[:8] + thinking[-4:]
    return {
        key: trace[key]
        for key in (
            "assistant_turns",
            "tool_counts",
            "command_counts",
            "content_read_paths",
            "content_read_count",
            "content_read_categories",
            "pre_mutation_paths",
            "pre_mutation_count",
            "pre_mutation_categories",
            "first_mutation_event",
            "first_test_read_event",
            "first_validation_event",
            "validation_commands",
            "final_text",
        )
    } | {
        "tool_events": trace["tool_events"],
        "thinking_samples": thinking,
    }


def build_selected_packets(
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
    task_metadata: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build evidence packets for predeclared failure mechanisms and one control."""
    packets = []
    for task, rep in SELECTED_PACKET_CELLS:
        key = (task, rep)
        packet: dict[str, Any] = {
            "task": task,
            "rep": rep,
            "metadata": task_metadata[task],
            "decision_divergence": DECISION_DIVERGENCES[key],
            "models": {},
        }
        for model_key in ("frontier", "agentworld", "thinkingcap"):
            cell = cells[model_key][key]
            root = Path(cell["artifact_root"])
            packet["models"][model_key] = {
                "result": cell["result"],
                "trace": compact_packet_trace(cell["trace"]),
                "changed_files": cell["changed_files"],
                "verifier": parse_verifier_failures(root),
            }
        for local_key in ("agentworld", "thinkingcap"):
            packet["models"][local_key]["frontier_coverage"] = compare_file_coverage(
                cells[local_key][key]["trace"], cells["frontier"][key]["trace"]
            )
        packets.append(packet)
    return packets


def build_provenance(
    source_root: Path,
    tasks: list[str],
    cells: dict[str, dict[tuple[str, int], dict[str, Any]]],
) -> dict[str, Any]:
    """Record artifact compatibility and known limits of the frontier reference."""
    prompt_hashes: dict[str, set[str]] = {key: set() for key in RESULT_ROOTS}
    system_hashes: dict[str, set[str]] = {key: set() for key in RESULT_ROOTS}
    denominator_mismatches = []
    for task in tasks:
        for rep in range(3):
            key = (task, rep)
            for model_key in RESULT_ROOTS:
                root = Path(cells[model_key][key]["artifact_root"])
                prompt_hashes[model_key].add(
                    sha256_file(root / "initial_context/user_prompt.txt")
                )
                system_hashes[model_key].add(
                    sha256_file(root / "initial_context/system_prompt.txt")
                )
            for metric in ("f2p_total", "p2p_total"):
                values = {
                    model_key: cells[model_key][key]["result"].get(metric)
                    for model_key in RESULT_ROOTS
                }
                non_null = {value for value in values.values() if value is not None}
                if len(non_null) > 1:
                    denominator_mismatches.append(
                        {"task": task, "rep": rep, "metric": metric, "values": values}
                    )
    return {
        "reference_run": "gpt56-sol-high-baseline-36v2-r3-w24",
        "reference_model": "openai-codex/gpt-5.6-sol",
        "reference_role": "frontier capability reference",
        "local_roles": {
            "agentworld": "local subject",
            "thinkingcap": "local subject",
        },
        "matched_tasks": len(tasks),
        "matched_cells_per_model": len(tasks) * 3,
        "user_prompt_hashes": {
            key: sorted(values) for key, values in prompt_hashes.items()
        },
        "system_prompt_hashes": {
            key: sorted(values) for key, values in system_hashes.items()
        },
        "graded_denominator_mismatches": denominator_mismatches,
        "compatibility": (
            "All matched cells use identical user prompts. Every completed grading "
            "surface has matching f2p/p2p denominators. Frontier results predate "
            "embedded harness, task, verifier, and subject-version identities, so "
            "artifact compatibility is evidenced but not cryptographically sealed."
        ),
        "coverage_definition": (
            "Content coverage counts unique exact repository files opened by the read "
            "tool or named as exact targets of shell content commands. Directory "
            "listings and glob searches are counted separately and do not imply that "
            "every discovered file was read."
        ),
        "source_root": str(source_root),
    }


def validate_analysis(analysis: dict[str, Any]) -> None:
    """Fail closed when pairing or frontier-reference invariants do not hold."""
    if analysis["provenance"]["matched_cells_per_model"] != 36:
        raise ValueError("Frontier trajectory analysis: expected 36 cells per model")
    if analysis["provenance"]["graded_denominator_mismatches"]:
        raise ValueError("Frontier trajectory analysis: verifier denominators differ")
    if analysis["gap_cohorts"]["agentworld"]["pairs"] != 24:
        raise ValueError("Frontier trajectory analysis: expected 24 AgentWorld gaps")
    if analysis["gap_cohorts"]["thinkingcap"]["pairs"] != 23:
        raise ValueError("Frontier trajectory analysis: expected 23 ThinkingCap gaps")
    if len(analysis["selected_packets"]) != len(SELECTED_PACKET_CELLS):
        raise ValueError("Frontier trajectory analysis: packet selection is incomplete")
    if set(DECISION_DIVERGENCES) != set(SELECTED_PACKET_CELLS):
        raise ValueError(
            "Frontier trajectory analysis: divergence ledger is incomplete"
        )
    if len(analysis["scaffoldability_ledger"]) != 6:
        raise ValueError(
            "Frontier trajectory analysis: scaffoldability ledger is incomplete"
        )
    expected_tool_results = {
        "frontier": (2507, 223, 0),
        "agentworld": (3600, 339, 107),
        "thinkingcap": (3517, 369, 19),
    }
    for model_key, expected in expected_tool_results.items():
        summary = analysis["tool_results"][model_key]
        actual = (
            summary["total"],
            summary["errors"],
            summary["error_categories"].get("malformed edit arguments", 0),
        )
        if actual != expected:
            raise ValueError(
                f"Frontier trajectory analysis: unexpected {model_key} tool results "
                f"{actual}, expected {expected}"
            )


def build_analysis(source_root: Path) -> dict[str, Any]:
    """Build the complete three-model trajectory evidence dataset."""
    thinkingcap_root = source_root / RESULT_ROOTS["thinkingcap"]
    tasks = sorted(path.name for path in thinkingcap_root.iterdir() if path.is_dir())
    task_metadata = {
        task: load_task_metadata(source_root.parent / "deep-swe/tasks", task)
        for task in tasks
    }
    cells = load_model_cells(source_root, tasks)
    gap_pairs = build_frontier_gap_pairs(cells, task_metadata)
    analysis = {
        "schema_version": 2,
        "title": "Local-model trajectory gaps against GPT-5.6 SOL",
        "models": {
            key: {"display_name": DISPLAY_NAMES[key], "result_root": str(path)}
            for key, path in RESULT_ROOTS.items()
        },
        "task_metadata": task_metadata,
        "provenance": build_provenance(source_root, tasks, cells),
        "frontier_outcomes": {
            "cells": 36,
            "solves": sum(
                cell["result"]["reward_binary"] == 1
                for cell in cells["frontier"].values()
            ),
            "invalid": sum(
                (cell["result"]["reward_binary"] or 0) < 0
                for cell in cells["frontier"].values()
            ),
        },
        "outcomes_by_task": build_outcomes_by_task(tasks, cells),
        "tool_results": {
            model_key: summarize_tool_result_delivery(model_cells)
            for model_key, model_cells in cells.items()
        },
        "gap_pairs": gap_pairs,
        "gap_cohorts": {
            local_key: summarize_gap_cohort(local_key, rows, cells)
            for local_key, rows in gap_pairs.items()
        },
        "task_gap_summaries": {
            local_key: build_task_gap_summaries(local_key, rows, cells)
            for local_key, rows in gap_pairs.items()
        },
        "selected_packets": build_selected_packets(cells, task_metadata),
        "scaffoldability_ledger": SCAFFOLDABILITY_LEDGER,
    }
    validate_analysis(analysis)
    return analysis


def markdown_list(values: list[str], empty_message: str) -> str:
    """Render a compact Markdown list for packet evidence."""
    if not values:
        return f"- {empty_message}"
    return "\n".join(f"- `{value}`" for value in values)


def markdown_command_blocks(values: list[str], empty_message: str) -> str:
    """Render shell commands without interpreting their Markdown characters."""
    if not values:
        return f"- {empty_message}"
    return "\n\n".join(f"```sh\n{value}\n```" for value in values)


def render_packet_markdown(packet: dict[str, Any]) -> str:
    """Render one selected trajectory packet as auditable Markdown."""
    divergence = packet["decision_divergence"]
    models = packet["models"]

    def outcome_row(model_key: str) -> str:
        model = models[model_key]
        result = model["result"]
        trace = model["trace"]
        return (
            f"| {DISPLAY_NAMES[model_key]} | {result['reward_binary']} | "
            f"{result['reward_partial']:.3f} | "
            f"{result['f2p_passed']}/{result['f2p_total']} | "
            f"{result['p2p_passed']}/{result['p2p_total']} | "
            f"{trace['content_read_count']} | {trace['pre_mutation_count']} | "
            f"{len(trace['validation_commands'])} | {len(model['changed_files'])} |"
        )

    def model_section(model_key: str) -> str:
        label = DISPLAY_NAMES[model_key]
        model = models[model_key]
        trace = model["trace"]
        failures = model["verifier"]["failed_tests"]
        validation_commands = [
            event["command"] for event in trace["validation_commands"]
        ]
        return f"""## {label}

### {label} exact content-read files

{markdown_list(trace["content_read_paths"], "No successful exact file read was recorded.")}

### {label} files changed

{markdown_list(model["changed_files"], "No changed file was captured.")}

### {label} validation commands

{markdown_command_blocks(validation_commands, "No validation command was recorded.")}

### {label} verifier failures

{markdown_list(failures, "No verifier failure was recorded.")}"""

    return (
        f"""# {packet["metadata"]["title"]} · rep {packet["rep"]}

- Task: `{packet["task"]}`
- Language: `{packet["metadata"]["language"]}`
- Base commit: `{packet["metadata"]["base_commit_hash"]}`
- Earliest divergence stage: **{divergence["stage"]}**
- Failure layer: **{divergence["failure_layer"]}**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
{outcome_row("frontier")}
{outcome_row("agentworld")}
{outcome_row("thinkingcap")}

## Decision divergence

**Frontier reference:** {divergence["frontier_behavior"]}

**AgentWorld:** {divergence["agentworld_divergence"]}

**ThinkingCap:** {divergence["thinkingcap_divergence"]}

{model_section("frontier")}

{model_section("agentworld")}

{model_section("thinkingcap")}
""".rstrip()
        + "\n"
    )


def write_selected_packets(analysis: dict[str, Any]) -> None:
    """Write JSON and Markdown evidence packets for every selected cell."""
    packet_root = REPORT_ROOT / "packets"
    packet_root.mkdir(exist_ok=True)
    expected_names = set()
    for packet in analysis["selected_packets"]:
        stem = f"{packet['task']}__rep{packet['rep']}"
        expected_names.update({f"{stem}.json", f"{stem}.md"})
        (packet_root / f"{stem}.json").write_text(
            json.dumps(packet, indent=2, sort_keys=True) + "\n"
        )
        (packet_root / f"{stem}.md").write_text(render_packet_markdown(packet))
    for path in packet_root.iterdir():
        if path.is_file() and path.name not in expected_names:
            path.unlink()


def main() -> None:
    """Write the reproducible trajectory evidence dataset and packets."""
    arguments = parse_arguments()
    analysis = build_analysis(arguments.source_root.resolve())
    output_path = REPORT_ROOT / "analysis.json"
    output_path.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    write_selected_packets(analysis)
    print(output_path)


if __name__ == "__main__":
    main()

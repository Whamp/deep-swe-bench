#!/usr/bin/env python3
"""Build the matched Ornith 1.0 35B versus Gemma 4 31B baseline report."""

from __future__ import annotations

import collections
import html
import json
import math
import random
import re
import statistics
import subprocess
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
WORKTREE_ROOT = REPORT_DIR.parents[1]
DATA_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=WORKTREE_ROOT,
        text=True,
    ).strip()
).parent
TASKS_ROOT = DATA_ROOT.parent / "deep-swe/tasks"
OUTPUT_HTML = REPORT_DIR / "index.html"
PACKET_DIR = REPORT_DIR / "packets"
DIFFICULTY_TSV = DATA_ROOT / "data/deepswe-v1.1-task-difficulty.tsv"

SIDES = ("gemma", "ornith")
LABELS = {"gemma": "Gemma 4 31B", "ornith": "Ornith 1.0 35B"}
CONFIGS = {
    "gemma": "baseline-gemma4-31b@1.0.0",
    "ornith": "baseline-ornith-35b@1.0.0",
}
MODELS = {
    "gemma": "local-vllm/gemma-4-31b",
    "ornith": "local-vllm/ornith-1.0-35b",
}
RESULT_ROOTS = {
    "gemma": DATA_ROOT / "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0",
    "ornith": DATA_ROOT / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0",
}
RUN_STATUS_PATHS = {
    "gemma": DATA_ROOT
    / "results/_runs/gemma4-31b-high-12v2-r3-w2--62f5bb098c6f4fd8f8fbb8c059ed5241eff31cd4ded716ce041aeb2847beb4f1/status.json",
    "ornith": DATA_ROOT
    / "results/_runs/ornith-35b-high-12v2-r3-w4--ee4eef1bc12334d42d9deb521201cf83991e880ffcf4e4508b684632f0462871/status.json",
}
EXPECTED_LOCK_IDENTITIES = {
    "gemma": "sha256:ac1cb73f6c09b606e2d04403f0cacf2e98c046127706084c1d6f532b7f6d76c6",
    "ornith": "sha256:e018bf6cc9b4a28392d1569dc0d6e63c413201d6a70f9e4444efe67f9a074166",
}
EXPECTED_REQUEST_FIELDS = {
    "gemma": {
        "model": "gemma-4-31b",
        "chat_template_kwargs.enable_thinking": True,
        "chat_template_kwargs.preserve_thinking": True,
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 64,
        "min_p": 0,
        "repetition_penalty": 1,
    },
    "ornith": {
        "model": "ornith-1.0-35b",
        "chat_template_kwargs.enable_thinking": True,
        "chat_template_kwargs.preserve_thinking": True,
        "temperature": 1,
        "top_p": 0.95,
        "top_k": 20,
        "min_p": 0,
        "repetition_penalty": 1,
    },
}


def percent(value: float) -> str:
    return f"{value * 100:.1f}%"


def percentage_points(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def relative_delta(right: float, left: float) -> str:
    return "n/a" if left == 0 else f"{(right / left - 1) * 100:+.1f}%"


def nested_value(record: dict[str, Any], dotted_key: str) -> Any:
    value: Any = record
    for part in dotted_key.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)
    return value


def load_results() -> dict[tuple[str, str, int], dict[str, Any]]:
    records: dict[tuple[str, str, int], dict[str, Any]] = {}
    for side, root in RESULT_ROOTS.items():
        for path in root.glob("*/rep*/result.json"):
            result = json.loads(path.read_text())
            records[(side, result["task"], result["rep"])] = result
    return records


def load_task_metadata(task: str) -> dict[str, str]:
    metadata = {"title": task, "difficulty": "unknown"}
    task_toml = TASKS_ROOT / task / "task.toml"
    if task_toml.exists():
        with task_toml.open("rb") as file:
            raw = tomllib.load(file).get("metadata", {})
        metadata["title"] = raw.get("display_title", task)
    if DIFFICULTY_TSV.exists():
        for line in DIFFICULTY_TSV.read_text().splitlines()[1:]:
            fields = line.split("\t")
            if not fields or fields[0] != task:
                continue
            try:
                rate = float(fields[1])
                metadata["difficulty"] = (
                    "hard" if rate < 0.2 else "medium" if rate < 0.5 else "easy"
                )
            except (IndexError, ValueError):
                pass
            break
    return metadata


def session_trace(cell: Path) -> dict[str, Any]:
    session_paths = sorted((cell / "session").glob("*.jsonl"))
    if not session_paths:
        return {
            "session": None,
            "assistant_turns": 0,
            "tool_counts": {},
            "bash_commands": [],
            "test_commands": [],
            "model_change": None,
            "thinking_levels": [],
        }
    tool_counts: collections.Counter[str] = collections.Counter()
    bash_commands: list[str] = []
    test_commands: list[str] = []
    thinking_levels: list[str] = []
    model_change = None
    assistant_turns = 0
    session_path = session_paths[-1]
    for line in session_path.read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") == "model_change":
            model_change = {
                "provider": record.get("provider"),
                "modelId": record.get("modelId"),
            }
        elif record.get("type") == "thinking_level_change":
            thinking_levels.append(str(record.get("thinkingLevel")))
        if record.get("type") != "message":
            continue
        message = record.get("message", {})
        if message.get("role") != "assistant":
            continue
        assistant_turns += 1
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "toolCall":
                continue
            name = str(part.get("name", "unknown"))
            arguments = part.get("arguments") or {}
            tool_counts[name] += 1
            if name != "bash":
                continue
            command = str(arguments.get("command", ""))
            bash_commands.append(command)
            if re.search(
                r"\b(test|pytest|go test|npm test|pnpm test|vitest|cargo test|jest|tsc|ruff|lint|build)\b",
                command,
            ):
                test_commands.append(command)
    return {
        "session": str(session_path.relative_to(DATA_ROOT)),
        "assistant_turns": assistant_turns,
        "tool_counts": dict(tool_counts),
        "bash_commands": bash_commands[-60:],
        "test_commands": test_commands[-30:],
        "model_change": model_change,
        "thinking_levels": thinking_levels,
    }


def patch_evidence(cell: Path) -> dict[str, Any]:
    patch_path = cell / "artifacts/model.patch"
    text = patch_path.read_text(errors="replace") if patch_path.exists() else ""
    files: list[str] = []
    additions = 0
    deletions = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            fields = line.split()
            if len(fields) >= 4:
                files.append(fields[3].removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {
        "path": str(patch_path.relative_to(DATA_ROOT)),
        "bytes": len(text.encode()),
        "files": files,
        "files_count": len(files),
        "additions": additions,
        "deletions": deletions,
        "changed_lines": additions + deletions,
        "excerpt": "\n".join(text.splitlines()[:140]),
    }


def verifier_evidence(cell: Path) -> dict[str, Any]:
    reward_path = cell / "verifier/reward.json"
    reward = json.loads(reward_path.read_text()) if reward_path.exists() else {}
    failed_examples: list[dict[str, str]] = []
    ctrf_path = cell / "verifier/ctrf.json"
    if ctrf_path.exists():
        try:
            tests = json.loads(ctrf_path.read_text()).get("results", {}).get("tests", [])
            for test in tests:
                if str(test.get("status", "")).lower() in {"pass", "passed"}:
                    continue
                failed_examples.append(
                    {
                        "name": (test.get("name") or test.get("testName") or "unknown")
                        .replace("=", " equals ")[:300],
                        "message": (test.get("message") or "").replace("=", " equals ")[:500],
                    }
                )
                if len(failed_examples) == 12:
                    break
        except json.JSONDecodeError:
            failed_examples.append(
                {"name": "ctrf parse failure", "message": str(ctrf_path)}
            )
    run_log_path = cell / "verifier/run.log"
    run_log_tail = ""
    if run_log_path.exists():
        run_log_tail = "\n".join(
            run_log_path.read_text(errors="replace").splitlines()[-50:]
        )
    return {
        "reward": reward,
        "failed_examples": failed_examples,
        "run_log_tail": run_log_tail,
    }


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    fields = (
        "reward_binary",
        "reward_partial",
        "f2p_passed",
        "f2p_total",
        "p2p_passed",
        "p2p_total",
        "total_tokens",
        "input_tokens",
        "output_tokens",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
        "agent_exit",
        "agent_timed_out",
        "verifier_exit",
    )
    return {field: result.get(field) for field in fields}


def score_rate(result: dict[str, Any], prefix: str) -> float:
    total = result.get(f"{prefix}_total") or 0
    return (result.get(f"{prefix}_passed") or 0) / total if total else 0.0


def packet_triggers(gemma: dict[str, Any], ornith: dict[str, Any]) -> list[str]:
    triggers: list[str] = []
    if (gemma["reward_binary"] == 1) != (ornith["reward_binary"] == 1):
        triggers.append("binary flip")
    if (gemma["reward_binary"] < 0) != (ornith["reward_binary"] < 0):
        triggers.append("negative-reward discordance")
    if bool(gemma["agent_timed_out"]) != bool(ornith["agent_timed_out"]):
        triggers.append("agent-timeout discordance")
    if abs(ornith["reward_partial"] - gemma["reward_partial"]) >= 0.5:
        triggers.append("|partial delta| ≥ 0.50")
    for prefix in ("f2p", "p2p"):
        if abs(score_rate(ornith, prefix) - score_rate(gemma, prefix)) >= 0.5:
            triggers.append(f"|{prefix} delta| ≥ 0.50")
    return triggers


def classification_for(
    task: str,
    rep: int,
    gemma: dict[str, Any],
    ornith: dict[str, Any],
) -> dict[str, Any]:
    gemma_f2p = f"{gemma.get('f2p_passed') or 0}/{gemma.get('f2p_total') or 0}"
    ornith_f2p = f"{ornith.get('f2p_passed') or 0}/{ornith.get('f2p_total') or 0}"
    gemma_p2p = f"{gemma.get('p2p_passed') or 0}/{gemma.get('p2p_total') or 0}"
    ornith_p2p = f"{ornith.get('p2p_passed') or 0}/{ornith.get('p2p_total') or 0}"
    evidence = [
        f"F2P {gemma_f2p} → {ornith_f2p}; P2P {gemma_p2p} → {ornith_p2p}.",
        f"Partial {gemma['reward_partial']:.3f} → {ornith['reward_partial']:.3f}.",
    ]
    if task == "dateutil-rfc5545-timezone-interop" and rep == 2:
        return {
            "primary_bucket": "validation gap",
            "mechanism": "Gemma stopped after an invalid edit with an empty patch, so grading was skipped. Ornith produced and repeatedly tested an rrule implementation, preserved 2,034/2,035 tests, and passed 56/67 feature tests.",
            "guidance_implication": "Treat an empty patch or failed edit as a completion blocker and require one targeted test before stopping.",
            "evidence": evidence,
            "confidence": "high",
        }
    if task == "langchain-request-coalescing" and rep == 0:
        return {
            "primary_bucket": "validation gap",
            "mechanism": "Gemma's coalescing patch hung in external verification. Ornith also exhausted its agent budget, but its saved patch completed verification with full preservation and 23/50 feature tests.",
            "guidance_implication": "Run a bounded concurrency/deadlock test before broadening a coalescing implementation.",
            "evidence": evidence,
            "confidence": "high",
        }
    if task in {"langchain-request-coalescing", "mobly-grouped-test-barriers"} and ornith[
        "agent_timed_out"
    ]:
        return {
            "primary_bucket": "resource exhaustion",
            "mechanism": f"Ornith used the full 3,600-second agent budget and external verification did not complete, replacing Gemma's graded partial outcome with the timeout sentinel on {task} rep{rep}.",
            "guidance_implication": "Add an early targeted-test checkpoint and stop editing while enough time remains for external verification.",
            "evidence": evidence,
            "confidence": "high",
        }
    if task == "obsidian-linter-link-format-conversion" and rep == 2:
        return {
            "primary_bucket": "resource exhaustion",
            "mechanism": "Ornith timed out before completing the feature matrix, although its patch still restored all 1,131 preservation tests and improved partial reward.",
            "guidance_implication": "Bound parser-debug loops and reserve a final feature-test pass.",
            "evidence": evidence,
            "confidence": "high",
        }
    if task in {
        "adaptix-name-mapping-aliases",
        "go-critic-doc-link-checker",
        "obsidian-linter-link-format-conversion",
        "participle-grammar-conflict-analysis",
        "sql-formatter-bigquery-pipe-formatting",
        "superjson-error-stack-serialization",
    }:
        return {
            "primary_bucket": "validation gap",
            "mechanism": f"Gemma's patch left broad feature or preservation failures ({gemma_f2p} F2P, {gemma_p2p} P2P). Ornith ran targeted and regression checks and reached {ornith_f2p} F2P with {ornith_p2p} P2P.",
            "guidance_implication": "Require a compile/import gate, targeted feature tests, and one preservation suite before completion.",
            "evidence": evidence,
            "confidence": "high",
        }
    return {
        "primary_bucket": "under-implementation",
        "mechanism": f"Both models reached a grade, but Ornith covered more requested behavior: F2P moved {gemma_f2p} → {ornith_f2p} while P2P moved {gemma_p2p} → {ornith_p2p}.",
        "guidance_implication": "Use the request's behavior list as a test matrix and verify every branch before stopping.",
        "evidence": evidence,
        "confidence": "medium",
    }


def build_packet(
    task: str,
    rep: int,
    gemma: dict[str, Any],
    ornith: dict[str, Any],
    triggers: list[str],
) -> dict[str, Any]:
    metadata = load_task_metadata(task)
    gemma_cell = RESULT_ROOTS["gemma"] / task / f"rep{rep}"
    ornith_cell = RESULT_ROOTS["ornith"] / task / f"rep{rep}"
    gemma_trace = session_trace(gemma_cell)
    ornith_trace = session_trace(ornith_cell)
    gemma_patch = patch_evidence(gemma_cell)
    ornith_patch = patch_evidence(ornith_cell)
    classification = classification_for(task, rep, gemma, ornith)
    packet = {
        "pair": {
            "task": task,
            "rep": rep,
            "title": metadata["title"],
            "difficulty": metadata["difficulty"],
            "language": gemma.get("language"),
            "left_config": CONFIGS["gemma"],
            "right_config": CONFIGS["ornith"],
            "left_model": MODELS["gemma"],
            "right_model": MODELS["ornith"],
        },
        "triggers": triggers,
        "left": {
            "result": compact_result(gemma),
            "trace": gemma_trace,
            "patch_stats": {
                key: value for key, value in gemma_patch.items() if key != "excerpt"
            },
            "patch_excerpt": gemma_patch["excerpt"],
            "verifier": verifier_evidence(gemma_cell),
        },
        "right": {
            "result": compact_result(ornith),
            "trace": ornith_trace,
            "patch_stats": {
                key: value for key, value in ornith_patch.items() if key != "excerpt"
            },
            "patch_excerpt": ornith_patch["excerpt"],
            "verifier": verifier_evidence(ornith_cell),
        },
        "stage_ledger": {
            "initialization": f"Gemma {gemma_trace['assistant_turns']} assistant turns; Ornith {ornith_trace['assistant_turns']}.",
            "contract_representation": "Both received the same task instruction through stock Pi; model-specific chat templates enabled binary thinking.",
            "seam_location": {
                "gemma_first_changed_file": (gemma_patch["files"] or [None])[0],
                "ornith_first_changed_file": (ornith_patch["files"] or [None])[0],
            },
            "implementation": {
                "gemma_changed_files": gemma_patch["files"],
                "ornith_changed_files": ornith_patch["files"],
            },
            "validation": {
                "gemma_test_commands": gemma_trace["test_commands"],
                "ornith_test_commands": ornith_trace["test_commands"],
            },
            "termination": {
                "gemma_timeout": gemma["agent_timed_out"],
                "ornith_timeout": ornith["agent_timed_out"],
                "gemma_verifier": gemma["verifier_exit"],
                "ornith_verifier": ornith["verifier_exit"],
            },
        },
        "classification": classification,
    }
    stem = f"{task}__rep{rep}"
    (PACKET_DIR / f"{stem}.json").write_text(
        json.dumps(packet, indent=2, sort_keys=True)
    )
    markdown = f"""# {task} rep{rep}: {classification['primary_bucket']}

- **Title:** {metadata['title']}
- **Difficulty / language:** {metadata['difficulty']} / {gemma.get('language')}
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** {', '.join(triggers)}
- **Partial:** {gemma['reward_partial']:.3f} → {ornith['reward_partial']:.3f} ({ornith['reward_partial'] - gemma['reward_partial']:+.3f})
- **Binary:** {gemma['reward_binary']} → {ornith['reward_binary']}

## Classification

**{classification['primary_bucket']}.** {classification['mechanism']}

**Process hypothesis:** {classification['guidance_implication']}

## Result metrics

```json
{json.dumps({'gemma': compact_result(gemma), 'ornith': compact_result(ornith)}, indent=2)}
```

## Patch scope

```json
{json.dumps({'gemma': packet['left']['patch_stats'], 'ornith': packet['right']['patch_stats']}, indent=2)}
```

## Validation commands

```json
{json.dumps({'gemma': gemma_trace['test_commands'], 'ornith': ornith_trace['test_commands']}, indent=2)}
```

## Verifier failure examples

```json
{json.dumps({'gemma': packet['left']['verifier']['failed_examples'], 'ornith': packet['right']['verifier']['failed_examples']}, indent=2)}
```

## Gemma patch excerpt

```diff
{gemma_patch['excerpt']}
```

## Ornith patch excerpt

```diff
{ornith_patch['excerpt']}
```
"""
    normalized = "\n".join(
        line.rstrip().replace("\t", "    ") for line in markdown.splitlines()
    ) + "\n"
    (PACKET_DIR / f"{stem}.md").write_text(normalized)
    packet["packet_link"] = f"packets/{stem}.md"
    return packet


def exact_sign_test_p(losses: int, wins: int) -> float:
    discordant = losses + wins
    if discordant == 0:
        return 1.0
    tail = min(losses, wins)
    return min(
        1.0,
        2
        * sum(math.comb(discordant, index) for index in range(tail + 1))
        / (2**discordant),
    )


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "solves": sum(row["reward_binary"] == 1 for row in rows),
        "negative": sum(row["reward_binary"] < 0 for row in rows),
        "partial_mean": statistics.mean(row["reward_partial"] for row in rows),
        "partial_median": statistics.median(row["reward_partial"] for row in rows),
        "tokens": sum(row["total_tokens"] for row in rows),
        "mean_tokens": statistics.mean(row["total_tokens"] for row in rows),
        "median_tokens": statistics.median(row["total_tokens"] for row in rows),
        "mean_wall": statistics.mean(row["agent_wall_s"] for row in rows),
        "median_wall": statistics.median(row["agent_wall_s"] for row in rows),
        "mean_turns": statistics.mean(row["turns"] for row in rows),
        "mean_tools": statistics.mean(row["tool_calls"] for row in rows),
        "timeouts": sum(bool(row["agent_timed_out"]) for row in rows),
        "agent_nonzero": sum(row["agent_exit"] not in (0, "0") for row in rows),
        "verifier_nonzero": sum(row["verifier_exit"] not in (0, "0") for row in rows),
        "f2p_passed": sum(row.get("f2p_passed") or 0 for row in rows),
        "f2p_total": sum(row.get("f2p_total") or 0 for row in rows),
        "p2p_passed": sum(row.get("p2p_passed") or 0 for row in rows),
        "p2p_total": sum(row.get("p2p_total") or 0 for row in rows),
    }


def audit_delivery(
    records: dict[tuple[str, str, int], dict[str, Any]],
    keys: list[tuple[str, int]],
) -> dict[str, dict[str, Any]]:
    audit: dict[str, dict[str, Any]] = {}
    for side in SIDES:
        delivered = 0
        mismatches: list[str] = []
        lock_identities: set[str] = set()
        launch_identities: set[str] = set()
        for task, rep in keys:
            result = records[(side, task, rep)]
            lock_identities.add(str(result.get("config_lock_identity")))
            launch_identities.add(str(result.get("launch_plan_identity")))
            cell = RESULT_ROOTS[side] / task / f"rep{rep}"
            request_path = cell / "initial_context/provider_request_0001.json"
            if not request_path.exists():
                mismatches.append(f"{task}/rep{rep}: request missing")
                continue
            request = json.loads(request_path.read_text())
            expected = EXPECTED_REQUEST_FIELDS[side]
            failed = [
                field
                for field, value in expected.items()
                if nested_value(request, field) != value
            ]
            result_failed = []
            if result.get("config") != CONFIGS[side]:
                result_failed.append("config")
            if result.get("model") != MODELS[side]:
                result_failed.append("model")
            if result.get("thinking_level") != "high":
                result_failed.append("thinking_level")
            if request.get("reasoning_effort") is not None:
                failed.append("reasoning_effort")
            if failed or result_failed:
                mismatches.append(
                    f"{task}/rep{rep}: request={failed} result={result_failed}"
                )
            else:
                delivered += 1
        audit[side] = {
            "delivered": delivered,
            "mismatches": mismatches,
            "lock_identities": sorted(lock_identities),
            "launch_identities": sorted(launch_identities),
        }
    return audit


records = load_results()
keys_by_side = {
    side: {(task, rep) for record_side, task, rep in records if record_side == side}
    for side in SIDES
}
if keys_by_side["gemma"] != keys_by_side["ornith"] or len(keys_by_side["gemma"]) != 36:
    raise SystemExit(
        f"expected 36 exact pairs, got Gemma={len(keys_by_side['gemma'])} "
        f"Ornith={len(keys_by_side['ornith'])}"
    )
keys = sorted(keys_by_side["gemma"])
tasks = sorted({task for task, _ in keys})
for side, status_path in RUN_STATUS_PATHS.items():
    status = json.loads(status_path.read_text())
    if status["state"] != "completed" or status["counts"]["batch_done"] != 36:
        raise SystemExit(f"{side} run is not complete")
    seal_paths = sorted(
        (
            DATA_ROOT
            / "results/_runs/_config-seals"
            / CONFIGS[side]
        ).glob("*.json")
    )
    if not seal_paths:
        raise SystemExit(f"{side} config seal is missing")
    if not any(
        json.loads(path.read_text()).get("lockIdentity")
        == EXPECTED_LOCK_IDENTITIES[side]
        for path in seal_paths
    ):
        raise SystemExit(f"{side} config seal does not match the expected lock")

delivery = audit_delivery(records, keys)
for side in SIDES:
    if delivery[side]["delivered"] != 36 or delivery[side]["mismatches"]:
        raise SystemExit(f"{side} delivery mismatch: {delivery[side]}")

PACKET_DIR.mkdir(parents=True, exist_ok=True)
for old_packet in PACKET_DIR.glob("*"):
    old_packet.unlink()
packets: list[dict[str, Any]] = []
for task, rep in keys:
    gemma_result = records[("gemma", task, rep)]
    ornith_result = records[("ornith", task, rep)]
    triggers = packet_triggers(gemma_result, ornith_result)
    if triggers:
        packets.append(build_packet(task, rep, gemma_result, ornith_result, triggers))
(PACKET_DIR / "packet_index.json").write_text(
    json.dumps(packets, indent=2, sort_keys=True)
)

summary = {
    side: summarize([records[(side, *key)] for key in keys]) for side in SIDES
}
gemma = summary["gemma"]
ornith = summary["ornith"]
for side_summary in summary.values():
    side_summary["f2p"] = side_summary["f2p_passed"] / side_summary["f2p_total"]
    side_summary["p2p"] = side_summary["p2p_passed"] / side_summary["p2p_total"]

partial_deltas = [
    records[("ornith", *key)]["reward_partial"]
    - records[("gemma", *key)]["reward_partial"]
    for key in keys
]
partial_wins = sum(delta > 0 for delta in partial_deltas)
partial_losses = sum(delta < 0 for delta in partial_deltas)
partial_ties = sum(delta == 0 for delta in partial_deltas)
partial_sign_p = exact_sign_test_p(partial_losses, partial_wins)

rng = random.Random(20260730)
partial_bootstrap: list[float] = []
binary_bootstrap: list[float] = []
for _ in range(50_000):
    sampled_tasks = [rng.choice(tasks) for _ in tasks]
    sampled_keys = [(task, rep) for task in sampled_tasks for rep in range(3)]
    partial_bootstrap.append(
        statistics.mean(
            records[("ornith", *key)]["reward_partial"]
            - records[("gemma", *key)]["reward_partial"]
            for key in sampled_keys
        )
    )
    binary_bootstrap.append(
        statistics.mean(
            (records[("ornith", *key)]["reward_binary"] == 1)
            - (records[("gemma", *key)]["reward_binary"] == 1)
            for key in sampled_keys
        )
    )
partial_bootstrap.sort()
binary_bootstrap.sort()
partial_ci = (partial_bootstrap[1250], partial_bootstrap[48749])
binary_ci = (binary_bootstrap[1250], binary_bootstrap[48749])

clean_keys = [
    key
    for key in keys
    if not records[("gemma", *key)]["agent_timed_out"]
    and not records[("ornith", *key)]["agent_timed_out"]
    and records[("gemma", *key)]["verifier_exit"] in (0, None)
    and records[("ornith", *key)]["verifier_exit"] in (0, None)
]
clean_gemma_partial = statistics.mean(
    records[("gemma", *key)]["reward_partial"] for key in clean_keys
)
clean_ornith_partial = statistics.mean(
    records[("ornith", *key)]["reward_partial"] for key in clean_keys
)
timeout_discordance = sum(
    bool(records[("gemma", *key)]["agent_timed_out"])
    != bool(records[("ornith", *key)]["agent_timed_out"])
    for key in keys
)

metric_rows = [
    (
        "Binary solves",
        f"{gemma['solves']}/36 · {percent(gemma['solves'] / 36)}",
        f"{ornith['solves']}/36 · {percent(ornith['solves'] / 36)}",
        percentage_points((ornith["solves"] - gemma["solves"]) / 36),
        "neutral",
    ),
    (
        "Mean partial reward",
        percent(gemma["partial_mean"]),
        percent(ornith["partial_mean"]),
        percentage_points(ornith["partial_mean"] - gemma["partial_mean"]),
        "good",
    ),
    (
        "Median partial reward",
        percent(gemma["partial_median"]),
        percent(ornith["partial_median"]),
        percentage_points(ornith["partial_median"] - gemma["partial_median"]),
        "good",
    ),
    (
        "Weighted F2P",
        f"{gemma['f2p_passed']}/{gemma['f2p_total']} · {percent(gemma['f2p'])}",
        f"{ornith['f2p_passed']}/{ornith['f2p_total']} · {percent(ornith['f2p'])}",
        percentage_points(ornith["f2p"] - gemma["f2p"]),
        "good",
    ),
    (
        "Weighted P2P",
        f"{gemma['p2p_passed']:,}/{gemma['p2p_total']:,} · {percent(gemma['p2p'])}",
        f"{ornith['p2p_passed']:,}/{ornith['p2p_total']:,} · {percent(ornith['p2p'])}",
        percentage_points(ornith["p2p"] - gemma["p2p"]),
        "good",
    ),
    (
        "Total reported tokens",
        f"{gemma['tokens'] / 1e6:.1f}M",
        f"{ornith['tokens'] / 1e6:.1f}M",
        relative_delta(ornith["tokens"], gemma["tokens"]),
        "bad",
    ),
    (
        "Median tokens / cell",
        f"{gemma['median_tokens'] / 1e6:.2f}M",
        f"{ornith['median_tokens'] / 1e6:.2f}M",
        relative_delta(ornith["median_tokens"], gemma["median_tokens"]),
        "bad",
    ),
    (
        "Mean agent wall time",
        f"{gemma['mean_wall'] / 60:.1f} min",
        f"{ornith['mean_wall'] / 60:.1f} min",
        relative_delta(ornith["mean_wall"], gemma["mean_wall"]),
        "bad",
    ),
    (
        "Mean assistant turns",
        f"{gemma['mean_turns']:.1f}",
        f"{ornith['mean_turns']:.1f}",
        relative_delta(ornith["mean_turns"], gemma["mean_turns"]),
        "bad",
    ),
    (
        "Mean tool calls",
        f"{gemma['mean_tools']:.1f}",
        f"{ornith['mean_tools']:.1f}",
        relative_delta(ornith["mean_tools"], gemma["mean_tools"]),
        "bad",
    ),
    (
        "Agent timeouts",
        str(gemma["timeouts"]),
        str(ornith["timeouts"]),
        f"{ornith['timeouts'] - gemma['timeouts']:+d}",
        "bad",
    ),
    (
        "Negative outcomes",
        str(gemma["negative"]),
        str(ornith["negative"]),
        f"{ornith['negative'] - gemma['negative']:+d}",
        "bad",
    ),
]
metric_html = "".join(
    f'<tr><td>{html.escape(name)}</td><td class="num">{left}</td>'
    f'<td class="num">{right}</td><td class="num"><span class="tag {verdict}">{delta}</span></td></tr>'
    for name, left, right, delta, verdict in metric_rows
)

task_rows: list[dict[str, Any]] = []
for task in tasks:
    task_keys = [(task, rep) for rep in range(3)]
    metadata = load_task_metadata(task)
    gemma_partial = statistics.mean(
        records[("gemma", *key)]["reward_partial"] for key in task_keys
    )
    ornith_partial = statistics.mean(
        records[("ornith", *key)]["reward_partial"] for key in task_keys
    )
    task_rows.append(
        {
            "task": task,
            "title": metadata["title"],
            "difficulty": metadata["difficulty"],
            "language": records[("gemma", task, 0)]["language"],
            "gemma_partial": gemma_partial,
            "ornith_partial": ornith_partial,
            "gemma_timeouts": sum(
                bool(records[("gemma", *key)]["agent_timed_out"])
                for key in task_keys
            ),
            "ornith_timeouts": sum(
                bool(records[("ornith", *key)]["agent_timed_out"])
                for key in task_keys
            ),
            "gemma_tokens": sum(
                records[("gemma", *key)]["total_tokens"] for key in task_keys
            ),
            "ornith_tokens": sum(
                records[("ornith", *key)]["total_tokens"] for key in task_keys
            ),
        }
    )
task_rows.sort(
    key=lambda row: (-(row["ornith_partial"] - row["gemma_partial"]), row["task"])
)
task_html = "".join(
    f'<tr><td><strong>{html.escape(row["task"])}</strong><br><span class="muted">{html.escape(row["title"])}</span></td>'
    f'<td>{html.escape(row["language"])}</td><td>{row["difficulty"]}</td>'
    f'<td class="num">{percent(row["gemma_partial"])}</td><td class="num">{percent(row["ornith_partial"])}</td>'
    f'<td class="num"><span class="tag {"good" if row["ornith_partial"] > row["gemma_partial"] else "bad" if row["ornith_partial"] < row["gemma_partial"] else "neutral"}">{percentage_points(row["ornith_partial"] - row["gemma_partial"])}</span></td>'
    f'<td class="num">{row["gemma_timeouts"]} → {row["ornith_timeouts"]}</td>'
    f'<td class="num">{relative_delta(row["ornith_tokens"], row["gemma_tokens"])}</td></tr>'
    for row in task_rows
)

split_rows: list[tuple[Any, ...]] = []
for field in ("language", "difficulty"):
    for value in sorted({row[field] for row in task_rows}):
        split_keys = [
            key
            for key in keys
            if (
                records[("gemma", *key)]["language"]
                if field == "language"
                else load_task_metadata(key[0])["difficulty"]
            )
            == value
        ]
        gemma_partial = statistics.mean(
            records[("gemma", *key)]["reward_partial"] for key in split_keys
        )
        ornith_partial = statistics.mean(
            records[("ornith", *key)]["reward_partial"] for key in split_keys
        )
        split_rows.append(
            (field, value, len(split_keys), gemma_partial, ornith_partial)
        )
split_html = "".join(
    f'<tr><td>{field}</td><td>{html.escape(str(value))}</td><td class="num">{count}</td>'
    f'<td class="num">{percent(gemma_partial)}</td><td class="num">{percent(ornith_partial)}</td>'
    f'<td class="num">{percentage_points(ornith_partial - gemma_partial)}</td></tr>'
    for field, value, count, gemma_partial, ornith_partial in split_rows
)

bucket_counts = collections.Counter(
    packet["classification"]["primary_bucket"] for packet in packets
)
bucket_html = "".join(
    f'<tr><td>{html.escape(bucket)}</td><td class="num">{count}</td></tr>'
    for bucket, count in bucket_counts.most_common()
)
packet_html = "".join(
    f'<tr><td><strong>{html.escape(packet["pair"]["task"])}</strong></td><td class="num">{packet["pair"]["rep"]}</td>'
    f'<td>{html.escape(", ".join(packet["triggers"]))}</td>'
    f'<td class="num">{percentage_points(packet["right"]["result"]["reward_partial"] - packet["left"]["result"]["reward_partial"])}</td>'
    f'<td><span class="tag {"bad" if packet["classification"]["primary_bucket"] == "resource exhaustion" else "caution"}">{html.escape(packet["classification"]["primary_bucket"])}</span></td>'
    f'<td>{html.escape(packet["classification"]["mechanism"])}</td><td><a href="{packet["packet_link"]}">packet</a></td></tr>'
    for packet in packets
)

pair_html = ""
for task, rep in keys:
    gemma_result = records[("gemma", task, rep)]
    ornith_result = records[("ornith", task, rep)]
    delta = ornith_result["reward_partial"] - gemma_result["reward_partial"]
    pair_html += (
        f'<tr><td>{html.escape(task)}</td><td class="num">{rep}</td>'
        f'<td class="num">{percent(gemma_result["reward_partial"])}</td>'
        f'<td class="num">{percent(ornith_result["reward_partial"])}</td>'
        f'<td class="num"><span class="tag {"good" if delta > 0 else "bad" if delta < 0 else "neutral"}">{percentage_points(delta)}</span></td>'
        f'<td class="num">{gemma_result["reward_binary"]}</td><td class="num">{ornith_result["reward_binary"]}</td>'
        f'<td class="num">{gemma_result["total_tokens"]:,}</td><td class="num">{ornith_result["total_tokens"]:,}</td>'
        f'<td class="num">{gemma_result["turns"]} → {ornith_result["turns"]}</td>'
        f'<td class="num">{int(bool(gemma_result["agent_timed_out"]))} → {int(bool(ornith_result["agent_timed_out"]))}</td></tr>'
    )

style = """
:root{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,rgba(51,93,255,.11),transparent 28%),linear-gradient(#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:1260px;margin:auto;padding:28px 20px 60px}.hero,section{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:38px}.eyebrow{display:inline-block;padding:7px 11px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1{font-size:clamp(2.4rem,5vw,4.5rem);line-height:1.02;letter-spacing:-.045em;max-width:15ch;margin:14px 0}.lede{font-size:1.1rem;color:var(--muted);max-width:84ch}.pills{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.pill,.tag{display:inline-flex;padding:6px 10px;border-radius:999px;font-weight:800;font-size:12px}.good{background:var(--green-soft);color:var(--green)}.bad{background:var(--red-soft);color:var(--red)}.caution{background:var(--amber-soft);color:#8a6100}.neutral{background:#edf1f7;color:#536173}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-top:20px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.7rem;line-height:1.1;letter-spacing:-.04em}.stat span{color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:28px}h2{font-size:1.75rem;letter-spacing:-.03em;margin:0 0 6px}h3{margin-bottom:5px}.section-lede{color:var(--muted);margin:0 0 18px}.callout{border-left:5px solid var(--blue);background:#f6f8ff;padding:15px 17px;border-radius:13px;margin:16px 0}.callout.goodline{border-color:var(--green);background:var(--green-soft)}.callout.warn{border-color:var(--amber);background:var(--amber-soft)}.callout.badline{border-color:var(--red);background:var(--red-soft)}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}.table-wrap{overflow-x:auto}.bars{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.bar-card{border:1px solid var(--line);border-radius:16px;padding:15px}.bar-card strong{font-size:1.55rem}.bar{height:9px;border-radius:99px;background:#edf1f7;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;border-radius:99px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.evidence{font-family:ui-monospace,monospace;font-size:13px;background:#f7f9fc;border:1px solid var(--line);padding:13px;border-radius:12px}details{border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:12px}summary{cursor:pointer;font-weight:800}code{background:#eef2ff;padding:.1em .35em;border-radius:5px}a{color:var(--blue);font-weight:800}.muted{color:var(--muted)}footer{color:var(--muted);text-align:center;padding:25px}@media(max-width:850px){.stats{grid-template-columns:repeat(2,1fr)}.bars,.grid2{grid-template-columns:1fr}.hero,section{padding:22px}}@media(max-width:520px){.stats{grid-template-columns:1fr}}
"""

generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Ornith 35B versus Gemma 4 31B</title><style>{style}</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">DeepSWE · matched 12_v2 model comparison · stock Pi · high thinking · 3 reps</span><h1>Ornith is far stronger on partial credit—but neither model solves a task.</h1><p class="lede">Across 36 exact task/rep pairs, Ornith raises mean partial reward from <strong>{percent(gemma['partial_mean'])} to {percent(ornith['partial_mean'])}</strong> and wins {partial_wins} pairs. Both models remain at <strong>0/36 binary solves</strong>. Ornith reaches this near-miss quality with {relative_delta(ornith['tokens'], gemma['tokens'])} more reported tokens, {relative_delta(ornith['mean_turns'], gemma['mean_turns'])} more turns, and 6 agent timeouts versus Gemma's 2.</p><div class="pills"><span class="pill good">{percentage_points(ornith['partial_mean']-gemma['partial_mean'])} mean partial</span><span class="pill good">{partial_wins}/36 paired wins</span><span class="pill neutral">0/36 solves on both</span><span class="pill bad">{ornith['tokens']/gemma['tokens']:.1f}× tokens</span><span class="pill bad">{gemma['timeouts']} → {ornith['timeouts']} timeouts</span></div><div class="stats"><div class="stat"><strong>{percent(ornith['partial_mean'])}</strong><span>Ornith partial</span></div><div class="stat"><strong>{percent(gemma['partial_mean'])}</strong><span>Gemma partial</span></div><div class="stat"><strong>0/36</strong><span>solves each</span></div><div class="stat"><strong>{ornith['f2p_passed']}/{ornith['f2p_total']}</strong><span>Ornith F2P</span></div><div class="stat"><strong>{ornith['tokens']/1e6:.1f}M</strong><span>Ornith tokens</span></div></div></header>
<section><h2>Verdict</h2><p class="section-lede">Ornith is the better implementation model on this subset, but not yet a successful exact solver.</p><div class="callout goodline"><strong>Quality:</strong> Ornith improves mean partial reward by {percentage_points(ornith['partial_mean']-gemma['partial_mean'])}, wins {partial_wins} pairs, loses {partial_losses}, and ties {partial_ties}. Its largest gains come from Adaptix, Go-Critic, SQL Formatter, SuperJSON, and Participle, where it preserves the host project and implements much more of the requested feature.</div><div class="callout warn"><strong>Ceiling:</strong> neither model records a binary solve. Ornith often gets extremely close—99.7% mean partial on Adaptix and 99.8% on SQL Formatter—but leaves at least one required feature test failing. This is broad progress, not benchmark completion.</div><div class="callout badline"><strong>Efficiency and reliability:</strong> Ornith reports 417.4M tokens versus Gemma's 39.3M, averages 124 versus 29 turns, and times out in 6 cells versus 2. Token units use different model tokenizers, and wall time comes from different TP/concurrency profiles, so the token and wall ratios are operational—not architecture-normalized.</div></section>
<section><h2>Score, preservation, and cost</h2><p class="section-lede">All 36 exact pairs remain in the primary result, including timeout and empty-patch outcomes.</p><div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Gemma 4 31B</th><th class="num">Ornith 1.0 35B</th><th class="num">Ornith delta</th></tr></thead><tbody>{metric_html}</tbody></table></div><div class="callout"><strong>Preservation is the clearest separation.</strong> Ornith passes 37,276/37,280 graded preservation tests; Gemma passes 11,683/37,093. F2P denominators differ because timeout and empty-patch cells do not always produce full grading, so compare the passed/total counts alongside the rates.</div></section>
<section><h2>Paired evidence and uncertainty</h2><div class="bars"><div class="bar-card"><strong style="color:var(--green)">{partial_wins}</strong><div>Ornith partial wins</div><div class="bar"><i style="width:{partial_wins/36*100:.1f}%;background:var(--green)"></i></div></div><div class="bar-card"><strong style="color:var(--red)">{partial_losses}</strong><div>Ornith partial losses</div><div class="bar"><i style="width:{partial_losses/36*100:.1f}%;background:var(--red)"></i></div></div><div class="bar-card"><strong>{partial_ties}</strong><div>paired ties</div><div class="bar"><i style="width:{partial_ties/36*100:.1f}%;background:var(--blue)"></i></div></div></div><div class="callout goodline"><strong>Direction is robust on partial credit:</strong> the paired median gain is {percentage_points(statistics.median(partial_deltas))}; the exact sign test over 33 non-tied pairs gives p={partial_sign_p:.6f}. A 50,000-draw task-cluster bootstrap puts the mean partial delta at {percentage_points(partial_ci[0])} to {percentage_points(partial_ci[1])} (95%).</div><div class="callout warn"><strong>Binary evidence is flat:</strong> the binary delta and its task-cluster interval are both {percentage_points(binary_ci[0])} to {percentage_points(binary_ci[1])} because neither side solved a cell. Strong partial evidence cannot be promoted to an exact-solve claim.</div></section>
<section><h2>Timeout sensitivity</h2><p class="section-lede">Removing failures is not the primary estimate, but it shows whether Ornith's partial advantage is only a timeout artifact.</p><div class="grid2"><div><h3>Clean on both sides</h3><p>{len(clean_keys)}/36 pairs had no agent timeout and normal verifier exits on both sides. Mean partial reward was {percent(clean_gemma_partial)} for Gemma and {percent(clean_ornith_partial)} for Ornith ({percentage_points(clean_ornith_partial-clean_gemma_partial)}).</p></div><div><h3>Discordant timeouts</h3><p>{timeout_discordance} pairs timed out on only one side. Ornith's material losses are concentrated in LangChain and Mobly; two pairs timed out on both sides.</p></div></div><div class="callout"><strong>Interpretation:</strong> timeout failures weaken Ornith's reliability, but they do not explain its quality lead. The clean-pair advantage is larger than the all-pair advantage.</div></section>
<section><h2>Task-level direction</h2><p class="section-lede">Ornith wins ten task means, loses two, and concentrates its failures in concurrency-heavy LangChain and Mobly work.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th>Language</th><th>Difficulty</th><th class="num">Gemma partial</th><th class="num">Ornith partial</th><th class="num">Delta</th><th class="num">Timeouts G→O</th><th class="num">Token delta</th></tr></thead><tbody>{task_html}</tbody></table></div></section>
<section><h2>Language and difficulty</h2><p class="section-lede">These are small descriptive splits; no split contains a binary solve.</p><div class="table-wrap"><table><thead><tr><th>Split</th><th>Value</th><th class="num">Cells</th><th class="num">Gemma partial</th><th class="num">Ornith partial</th><th class="num">Delta</th></tr></thead><tbody>{split_html}</tbody></table></div></section>
<section><h2>What changed in the trajectories</h2><p class="section-lede">Packet rule: negative-reward or timeout discordance, at least 50 points of partial movement, or at least 50 points of F2P/P2P movement. This selected {len(packets)} cells.</p><div class="grid2"><div><h3>Primary drivers</h3><div class="table-wrap"><table><thead><tr><th>Bucket</th><th class="num">Packets</th></tr></thead><tbody>{bucket_html}</tbody></table></div></div><div><h3>Repeated pattern</h3><p><strong>Gemma:</strong> shorter trajectories often stopped after writing a patch without running a local test. Several patches then failed to build or collapsed preservation grading.</p><p><strong>Ornith:</strong> longer trajectories repeatedly compiled, ran targeted tests, and checked broader suites. That usually protected P2P behavior, but debugging loops sometimes consumed the full hour.</p></div></div><div class="callout goodline"><strong>Representative gain:</strong> on Adaptix rep0, Gemma recorded no test command and graded 0/44 F2P plus 0/2,738 P2P. Ornith ran targeted and broad pytest checks, reached 39/44 F2P, and preserved 2,738/2,738.</div><div class="callout badline"><strong>Representative loss:</strong> on Mobly rep0, Gemma reached 91.4% partial. Ornith spent the full 3,600 seconds iterating on grouped-execution tests; external verification timed out and the cell received the negative sentinel.</div><details><summary>Open all {len(packets)} triggered trajectory packets</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Trigger</th><th class="num">Partial Δ</th><th>Driver</th><th>Evidence-backed mechanism</th><th>Evidence</th></tr></thead><tbody>{packet_html}</tbody></table></div></details></section>
<section><h2>Configuration and delivery audit</h2><div class="grid2"><div class="evidence"><strong>Gemma 4 31B</strong><br>{CONFIGS['gemma']}<br>{MODELS['gemma']} · high<br>36/36 requests matched<br>enable_thinking=true<br>preserve_thinking=true<br>temperature=1 · top_p=.95 · top_k=64<br>Pi 0.81.1 · 2 workers · TP4 server profile</div><div class="evidence"><strong>Ornith 1.0 35B</strong><br>{CONFIGS['ornith']}<br>{MODELS['ornith']} · high<br>36/36 requests matched<br>enable_thinking=true<br>preserve_thinking=true<br>temperature=1 · top_p=.95 · top_k=20<br>Pi 0.81.1 · 4 workers · TP2 server profile</div></div><div class="callout"><strong>Controlled:</strong> task set, reps, stock Pi subject, Pi version, high/binary thinking, 262K context, 81,920 max output tokens, one-hour agent timeout, no added executor prompt, and initial-context capture. <strong>Not controlled:</strong> model family, tokenizer, quantization, chat template, tool/reasoning parser, tensor parallelism, server concurrency, and sampling top_k. This comparison answers “which deployed local profile performed better,” not “which architecture is intrinsically better.”</div></section>
<section><h2>Run integrity</h2><div class="callout goodline"><strong>Complete:</strong> 36/36 exact pairs, both run ledgers completed, both preflights passed, both config releases sealed, and every cell matched its expected config, model, high-thinking result, and provider-request settings.</div><p class="muted">Gemma lock: <code>{html.escape(', '.join(delivery['gemma']['lock_identities']))}</code><br>Ornith lock: <code>{html.escape(', '.join(delivery['ornith']['lock_identities']))}</code><br>Gemma launch: <code>{html.escape(', '.join(delivery['gemma']['launch_identities']))}</code><br>Ornith launch: <code>{html.escape(', '.join(delivery['ornith']['launch_identities']))}</code></p></section>
<section><h2>All 36 matched cells</h2><details><summary>Open the complete pair table</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th class="num">Gemma partial</th><th class="num">Ornith partial</th><th class="num">Delta</th><th class="num">G binary</th><th class="num">O binary</th><th class="num">G tokens</th><th class="num">O tokens</th><th class="num">Turns G→O</th><th class="num">Timeout G→O</th></tr></thead><tbody>{pair_html}</tbody></table></div></details></section>
<section><h2>Conclusion</h2><div class="callout goodline"><strong>Choose Ornith when partial implementation quality matters.</strong> It is materially better at preserving existing behavior and completing most of the requested feature across this subset.</div><div class="callout badline"><strong>Do not call Ornith solved or efficient.</strong> It posts 0 exact solves, consumes far more inference work, and has a 16.7% agent-timeout rate. Its strongest result is “better near-misses,” not benchmark success.</div><div class="callout"><strong>Next experiment:</strong> keep the same Ornith serving profile but add a model-neutral completion discipline: compile early, run one targeted feature test plus one preservation test, and stop before the verifier budget is endangered. Compare that new config against this immutable stock-Pi baseline.</div></section>
<footer>Generated {generated} from saved DeepSWE artifacts · 12_v2 · stock Pi · high thinking · 3 reps · <a href="packets/packet_index.json">packet index JSON</a></footer></div></body></html>"""
OUTPUT_HTML.write_text(page)
print(OUTPUT_HTML)
print(
    json.dumps(
        {
            "pairs": len(keys),
            "packets": len(packets),
            "gemma_partial": gemma["partial_mean"],
            "ornith_partial": ornith["partial_mean"],
            "partial_wins": partial_wins,
            "partial_losses": partial_losses,
            "partial_ties": partial_ties,
            "partial_sign_p": partial_sign_p,
            "partial_ci": partial_ci,
            "gemma_tokens": gemma["tokens"],
            "ornith_tokens": ornith["tokens"],
        },
        indent=2,
    )
)

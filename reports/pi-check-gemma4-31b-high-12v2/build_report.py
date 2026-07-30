#!/usr/bin/env python3
"""Build the final matched Gemma 4 pi-check comparison and trajectory packets."""

from __future__ import annotations

import collections
import html
import json
import math
import random
import re
import statistics
import tomllib
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUT = Path(__file__).with_name("index.html")
PACKET_DIR = Path(__file__).with_name("packets")
CONFIGS = ("baseline", "pi-check")
ROOTS = {
    "baseline": REPO / "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0",
    "pi-check": REPO / "results/gemma-4-31b/high/pi-check@1.1.0",
}
CHECK_PROMPT = "Re-audit every requirement in the original request with fresh, independent evidence"
DIFFICULTY_TSV = REPO / "data/deepswe-v1.1-task-difficulty.tsv"
RUN_STATUS = REPO / "results/_runs/pi-check-gemma4-31b-high-12v2-r3-w2--80fe7664d0a62031d13d4006bfe322623205779a5b049935bbda9e3d4e12dcf4/status.json"

CLASSIFICATIONS: dict[tuple[str, int], tuple[str, str, str]] = {
    ("adaptix-name-mapping-aliases", 0): ("resource exhaustion", "The delivered follow-up used 21 more turns and timed out without changing the zero score.", "Bound the follow-up by remaining wall time and stop when tests still cannot execute."),
    ("adaptix-name-mapping-aliases", 1): ("under-implementation", "The baseline patch caused the grader suite not to run; the follow-up restored 2,667/2,738 preservation tests and passed 3/44 feature tests.", "Require a full-suite execution check before declaring the original implementation complete."),
    ("adaptix-name-mapping-aliases", 2): ("resource exhaustion", "The delivered follow-up used 24 more turns and timed out with the same zero score.", "Bound the follow-up by remaining wall time and stop when tests still cannot execute."),
    ("claude-code-by-agents-recursive-delegation", 0): ("under-implementation", "The follow-up completed circular-delegation, tool-result, empty-result, unknown-agent, and multi-level behavior; F2P moved 0/7 to 7/7.", "Use the request's behavior list as a completion checklist and test every branch before stopping."),
    ("claude-code-by-agents-recursive-delegation", 1): ("under-implementation", "The follow-up repaired the five remaining recursive-delegation behaviors; F2P moved 2/7 to 7/7.", "Re-run the explicit behavior matrix after implementation and repair every failed branch."),
    ("dateutil-rfc5545-timezone-interop", 0): ("resource exhaustion", "The follow-up produced a larger patch, but the external verifier timed out, turning a 98.1% partial outcome into the timeout sentinel.", "Reserve enough time for the external validation path; do not keep editing once validation budget is endangered."),
    ("dateutil-rfc5545-timezone-interop", 2): ("under-implementation", "Baseline made no patch after an invalid edit; the follow-up delivered a substantial implementation and reached 82.5% partial.", "Treat an empty patch or failed edit as an explicit completion blocker."),
    ("go-critic-doc-link-checker", 0): ("validation gap", "Baseline grading could not run; the follow-up reached 2/3 F2P and 15/16 P2P, but also captured a 9.1 MB nested repository diff.", "Run the real package suite and audit patch scope before finalizing."),
    ("go-critic-doc-link-checker", 1): ("validation gap", "Baseline grading could not run; the follow-up reached 2/3 F2P and 15/16 P2P with one false-positive case left.", "Run the real package suite and inspect remaining negative fixtures before finalizing."),
    ("goreleaser-retry-publish-auditing", 1): ("resource exhaustion", "The delivered follow-up timed out after 17 additional turns and reduced F2P from 3/29 to 1/29.", "Stop the audit when remaining time cannot cover implementation plus targeted tests."),
    ("goreleaser-retry-publish-auditing", 2): ("resource exhaustion", "The delivered follow-up timed out after 28 additional turns; preservation improved but feature coverage remained 0/29.", "Require an early feature-test signal before spending the rest of the budget on broad repair."),
    ("langchain-request-coalescing", 0): ("resource exhaustion", "Both verifiers timed out; pi-check additionally exhausted the agent budget after nine follow-up turns.", "Detect blocking or deadlock signatures early and reserve time for a bounded concurrency test."),
    ("langchain-request-coalescing", 1): ("under-implementation", "The follow-up turned a non-running suite into full P2P preservation and 41/50 feature tests.", "Exercise sync, async, streaming, cancellation, and stats paths as one protocol matrix."),
    ("langchain-request-coalescing", 2): ("cross-scope regression", "The pi-check patch replaced a core pipe method and the grader suite did not run, falling from 89.4% to zero.", "Reject edits that displace an existing public method and require a full import/suite smoke test."),
    ("mobly-grouped-test-barriers", 1): ("resource exhaustion", "The follow-up exhausted both agent and verifier budgets, replacing a 90.1% partial result with the timeout sentinel.", "Prefer targeted barrier tests and stop before the external verifier budget is consumed."),
    ("mobly-grouped-test-barriers", 2): ("resource exhaustion", "Baseline timed out; pi-check finished and improved preservation from 679/808 to 761/808.", "A bounded follow-up can help when it converges quickly; retain an explicit stop condition."),
    ("obsidian-linter-link-format-conversion", 0): ("under-implementation", "The follow-up restored all 1,131 preservation tests and passed 48/60 feature tests, up from a non-running feature suite.", "Test image links, angle brackets, whitespace, and escaped delimiters as a conversion matrix."),
    ("participle-grammar-conflict-analysis", 2): ("validation gap", "The follow-up restored all 153 preservation tests, though only 2/91 feature tests passed.", "Require the existing suite to run before trusting narrow feature tests."),
    ("sql-formatter-bigquery-pipe-formatting", 0): ("resource exhaustion", "The agent timed out before the check prompt was delivered; preservation fell from 2,396/5,709 to 221/5,709.", "Classify pre-check timeouts as missing treatment and add a launch-level completion budget guard."),
    ("superjson-error-stack-serialization", 1): ("under-implementation", "The follow-up moved F2P from 0/80 to 38/80 and P2P from 21/116 to 111/116.", "Audit option defaults, cause restoration, class filters, and sanitization independently."),
    ("superjson-error-stack-serialization", 2): ("under-implementation", "The follow-up moved F2P from 0/80 to 70/80 and P2P from 21/116 to 105/116.", "Add a compatibility matrix for legacy defaults, causes, stack opt-in, and custom errors."),
    ("tengo-callable-instance-isolation", 0): ("under-implementation", "The follow-up added Call but did not wire constants and globals into compiled functions; the repository no longer built and partial fell from 71.0% to zero.", "Require a compile gate immediately after changing VM object state and execution wiring."),
    ("tengo-callable-instance-isolation", 1): ("resource exhaustion", "The check prompt was never delivered; 395 pre-check turns consumed 42.3M tokens before timeout.", "Cap turns and repeated tool loops before the follow-up stage."),
    ("tengo-callable-instance-isolation", 2): ("resource exhaustion", "The check prompt was never delivered and the agent timed out; this is a missing-treatment cell.", "Cap the original attempt so the configured follow-up has a chance to run."),
}


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def pp(value: float) -> str:
    return f"{value * 100:+.1f} pp"


def ratio_delta(right: float, left: float) -> str:
    return "n/a" if left == 0 else f"{(right / left - 1) * 100:+.1f}%"


def load_results() -> dict[tuple[str, str, int], dict[str, Any]]:
    records = {}
    for config, root in ROOTS.items():
        for path in root.glob("*/rep*/result.json"):
            result = json.loads(path.read_text())
            records[(config, result["task"], result["rep"])] = result
    return records


def load_task_metadata(task: str) -> dict[str, str]:
    metadata = {"title": task, "difficulty": "unknown"}
    path = REPO.parent / "deep-swe/tasks" / task / "task.toml"
    if path.exists():
        with path.open("rb") as file:
            raw = tomllib.load(file).get("metadata", {})
        metadata["title"] = raw.get("display_title", task)
    if DIFFICULTY_TSV.exists():
        for line in DIFFICULTY_TSV.read_text().splitlines()[1:]:
            fields = line.split("\t")
            if fields and fields[0] == task:
                try:
                    rate = float(fields[1])
                    metadata["difficulty"] = "hard" if rate < 0.2 else "medium" if rate < 0.5 else "easy"
                except (ValueError, IndexError):
                    pass
                break
    return metadata


def session_trace(cell: Path) -> dict[str, Any]:
    session_paths = sorted((cell / "session").glob("*.jsonl"))
    if not session_paths:
        return {"session": None, "prompt_count": 0, "tool_counts": {}, "post_check_tool_counts": {}, "bash_commands": [], "test_commands": [], "assistant_turns": 0, "post_check_turns": 0, "post_check_tokens": 0}
    tool_counts: collections.Counter[str] = collections.Counter()
    post_tools: collections.Counter[str] = collections.Counter()
    bash_commands: list[str] = []
    test_commands: list[str] = []
    prompt_count = assistant_turns = post_turns = post_tokens = 0
    after_check = False
    for line in session_paths[-1].read_text(errors="replace").splitlines():
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("type") != "message":
            continue
        message = record.get("message", {})
        content = message.get("content")
        text = content if isinstance(content, str) else " ".join(part.get("text", "") for part in (content or []) if isinstance(part, dict))
        if message.get("role") == "user" and CHECK_PROMPT in text:
            prompt_count += 1
            after_check = True
            continue
        if message.get("role") != "assistant":
            continue
        assistant_turns += 1
        if after_check:
            post_turns += 1
            usage = message.get("usage") or {}
            post_tokens += int(usage.get("totalTokens") or usage.get("total_tokens") or 0)
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "toolCall":
                continue
            name = part.get("name", "unknown")
            arguments = part.get("arguments") or {}
            tool_counts[name] += 1
            if after_check:
                post_tools[name] += 1
            if name == "bash":
                command = str(arguments.get("command", ""))
                bash_commands.append(command)
                if re.search(r"\b(test|pytest|go test|npm test|pnpm test|vitest|cargo test|tsc|ruff|lint)\b", command):
                    test_commands.append(command)
    return {
        "session": str(session_paths[-1].relative_to(REPO)),
        "prompt_count": prompt_count,
        "tool_counts": dict(tool_counts),
        "post_check_tool_counts": dict(post_tools),
        "bash_commands": bash_commands[-80:],
        "test_commands": test_commands[-40:],
        "assistant_turns": assistant_turns,
        "post_check_turns": post_turns,
        "post_check_tokens": post_tokens,
    }


def patch_evidence(cell: Path) -> dict[str, Any]:
    path = cell / "artifacts/model.patch"
    text = path.read_text(errors="replace") if path.exists() else ""
    files: list[str] = []
    additions = deletions = 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3].removeprefix("b/"))
        elif line.startswith("+") and not line.startswith("+++"):
            additions += 1
        elif line.startswith("-") and not line.startswith("---"):
            deletions += 1
    return {
        "path": str(path.relative_to(REPO)),
        "bytes": len(text.encode()),
        "files": files,
        "files_count": len(files),
        "additions": additions,
        "deletions": deletions,
        "excerpt": "\n".join(text.splitlines()[:180]),
    }


def verifier_evidence(cell: Path) -> dict[str, Any]:
    reward_path = cell / "verifier/reward.json"
    reward = json.loads(reward_path.read_text()) if reward_path.exists() else {}
    failed: list[dict[str, str]] = []
    ctrf_path = cell / "verifier/ctrf.json"
    if ctrf_path.exists():
        try:
            tests = json.loads(ctrf_path.read_text()).get("results", {}).get("tests", [])
            for test in tests:
                if str(test.get("status", "")).lower() in {"pass", "passed"}:
                    continue
                failed.append({
                    "name": (test.get("name") or test.get("testName") or "unknown").replace("API behavior >", "API behavior:").replace("=", " equals "),
                    "message": (test.get("message") or "")[:500],
                })
                if len(failed) == 12:
                    break
        except json.JSONDecodeError:
            failed.append({"name": "ctrf parse failure", "message": str(ctrf_path)})
    run_log = cell / "verifier/run.log"
    tail = ""
    if run_log.exists():
        tail = "\n".join(run_log.read_text(errors="replace").splitlines()[-60:])
    return {"reward": reward, "failed_examples": failed, "run_log_tail": tail}


def compact_result(result: dict[str, Any]) -> dict[str, Any]:
    fields = ["reward_binary", "reward_partial", "f2p_passed", "f2p_total", "p2p_passed", "p2p_total", "total_tokens", "combined_total_tokens", "agent_wall_s", "turns", "tool_calls", "patch_bytes", "agent_exit", "agent_timed_out", "verifier_exit"]
    return {field: result.get(field) for field in fields}


def packet_trigger(left: dict[str, Any], right: dict[str, Any]) -> list[str]:
    reasons = []
    if (left["reward_binary"] == 1) != (right["reward_binary"] == 1):
        reasons.append("binary flip")
    if (left["reward_binary"] < 0) != (right["reward_binary"] < 0):
        reasons.append("negative-reward discordance")
    if bool(left["agent_timed_out"]) != bool(right["agent_timed_out"]):
        reasons.append("agent-timeout discordance")
    if abs(right["reward_partial"] - left["reward_partial"]) >= 0.5:
        reasons.append("|partial delta| ≥ 0.50")
    for prefix in ("f2p", "p2p"):
        left_total = left.get(f"{prefix}_total") or 0
        right_total = right.get(f"{prefix}_total") or 0
        left_rate = (left.get(f"{prefix}_passed") or 0) / left_total if left_total else 0
        right_rate = (right.get(f"{prefix}_passed") or 0) / right_total if right_total else 0
        if abs(right_rate - left_rate) >= 0.5:
            reasons.append(f"|{prefix} delta| ≥ 0.50")
    return reasons


def build_packet(task: str, rep: int, left: dict[str, Any], right: dict[str, Any], reasons: list[str]) -> dict[str, Any]:
    metadata = load_task_metadata(task)
    left_cell = ROOTS["baseline"] / task / f"rep{rep}"
    right_cell = ROOTS["pi-check"] / task / f"rep{rep}"
    left_trace = session_trace(left_cell)
    right_trace = session_trace(right_cell)
    bucket, mechanism, implication = CLASSIFICATIONS[(task, rep)]
    packet = {
        "pair": {"task": task, "rep": rep, "title": metadata["title"], "difficulty": metadata["difficulty"], "language": left.get("language"), "left_config": "baseline-gemma4-31b@1.0.0", "right_config": "pi-check@1.1.0"},
        "triggers": reasons,
        "left": {"result": compact_result(left), "trace": left_trace, "patch": patch_evidence(left_cell), "verifier": verifier_evidence(left_cell)},
        "right": {"result": compact_result(right), "trace": right_trace, "patch": patch_evidence(right_cell), "verifier": verifier_evidence(right_cell)},
        "stage_ledger": {
            "initialization": f"baseline {left_trace['assistant_turns']} assistant turns; pi-check {right_trace['assistant_turns']}",
            "contract_representation": "task prompt plus repository evidence; pi-check follow-up " + ("delivered" if right_trace["prompt_count"] == 1 else "missing"),
            "seam_location": {"baseline_first_changed_file": (patch_evidence(left_cell)["files"] or [None])[0], "pi_check_first_changed_file": (patch_evidence(right_cell)["files"] or [None])[0]},
            "implementation": {"baseline_changed_files": patch_evidence(left_cell)["files"], "pi_check_changed_files": patch_evidence(right_cell)["files"]},
            "validation": {"baseline_test_commands": left_trace["test_commands"], "pi_check_test_commands": right_trace["test_commands"]},
            "completion_audit": {"pi_check_prompt_count": right_trace["prompt_count"], "post_check_tools": right_trace["post_check_tool_counts"]},
            "termination": {"baseline_timeout": left["agent_timed_out"], "pi_check_timeout": right["agent_timed_out"], "baseline_verifier": left["verifier_exit"], "pi_check_verifier": right["verifier_exit"]},
        },
        "classification": {"primary_bucket": bucket, "mechanism": mechanism, "guidance_implication": implication, "confidence": "high" if bucket != "resource exhaustion" or right["agent_timed_out"] else "medium"},
    }
    stem = f"{task}__rep{rep}"
    (PACKET_DIR / f"{stem}.json").write_text(json.dumps(packet, indent=2, sort_keys=True))
    markdown = f"""# {task} rep{rep}: {bucket}

- **Title:** {metadata['title']}
- **Difficulty / language:** {metadata['difficulty']} / {left.get('language')}
- **Triggers:** {', '.join(reasons)}
- **Delivery:** {'delivered' if right_trace['prompt_count'] == 1 else 'missing'}
- **Partial:** {left['reward_partial']:.3f} → {right['reward_partial']:.3f} ({right['reward_partial']-left['reward_partial']:+.3f})
- **Binary:** {left['reward_binary']} → {right['reward_binary']}

## Classification

**{bucket}.** {mechanism}

**Guidance hypothesis:** {implication}

## Result metrics

```json
{json.dumps({'baseline': compact_result(left), 'pi-check': compact_result(right)}, indent=2)}
```

## Patch scope

```json
{json.dumps({'baseline': {key: value for key, value in packet['left']['patch'].items() if key != 'excerpt'}, 'pi-check': {key: value for key, value in packet['right']['patch'].items() if key != 'excerpt'}}, indent=2)}
```

## Tool and validation summary

```json
{json.dumps({'baseline': left_trace, 'pi-check': right_trace}, indent=2)}
```

## Verifier failure examples

```json
{json.dumps({'baseline': packet['left']['verifier']['failed_examples'], 'pi-check': packet['right']['verifier']['failed_examples']}, indent=2)}
```

## Baseline patch excerpt

```diff
{packet['left']['patch']['excerpt']}
```

## pi-check patch excerpt

```diff
{packet['right']['patch']['excerpt']}
```
"""
    normalized_markdown = "\n".join(line.rstrip().replace("\t", "    ") for line in markdown.splitlines()) + "\n"
    (PACKET_DIR / f"{stem}.md").write_text(normalized_markdown)
    packet["packet_link"] = f"packets/{stem}.md"
    return packet


records = load_results()
baseline_keys = {(task, rep) for config, task, rep in records if config == "baseline"}
check_keys = {(task, rep) for config, task, rep in records if config == "pi-check"}
if baseline_keys != check_keys or len(baseline_keys) != 36:
    raise SystemExit(f"expected 36 exact pairs, got baseline={len(baseline_keys)} pi-check={len(check_keys)}")
keys = sorted(baseline_keys)
tasks = sorted({task for task, _ in keys})
status = json.loads(RUN_STATUS.read_text())
if status["state"] != "completed" or status["counts"]["batch_done"] != 36:
    raise SystemExit("pi-check run is not complete")

PACKET_DIR.mkdir(parents=True, exist_ok=True)
for old_packet in PACKET_DIR.glob("*"):
    old_packet.unlink()
packets = []
for task, rep in keys:
    left = records[("baseline", task, rep)]
    right = records[("pi-check", task, rep)]
    reasons = packet_trigger(left, right)
    if reasons:
        packets.append(build_packet(task, rep, left, right, reasons))
(PACKET_DIR / "packet_index.json").write_text(json.dumps(packets, indent=2, sort_keys=True))

summary: dict[str, dict[str, Any]] = {}
for config in CONFIGS:
    rows = [records[(config, *key)] for key in keys]
    summary[config] = {
        "solves": sum(row["reward_binary"] == 1 for row in rows),
        "partial_mean": statistics.mean(row["reward_partial"] for row in rows),
        "partial_median": statistics.median(row["reward_partial"] for row in rows),
        "tokens": sum(row["total_tokens"] for row in rows),
        "mean_tokens": statistics.mean(row["total_tokens"] for row in rows),
        "median_tokens": statistics.median(row["total_tokens"] for row in rows),
        "mean_wall": statistics.mean(row["agent_wall_s"] for row in rows),
        "mean_turns": statistics.mean(row["turns"] for row in rows),
        "mean_tools": statistics.mean(row["tool_calls"] for row in rows),
        "timeouts": sum(bool(row["agent_timed_out"]) for row in rows),
        "verifier_nonzero": sum(row["verifier_exit"] not in (0, None) for row in rows),
        "f2p_passed": sum(row.get("f2p_passed") or 0 for row in rows),
        "f2p_total": sum(row.get("f2p_total") or 0 for row in rows),
        "p2p_passed": sum(row.get("p2p_passed") or 0 for row in rows),
        "p2p_total": sum(row.get("p2p_total") or 0 for row in rows),
    }
base = summary["baseline"]
check = summary["pi-check"]
base["f2p"] = base["f2p_passed"] / base["f2p_total"]
check["f2p"] = check["f2p_passed"] / check["f2p_total"]
base["p2p"] = base["p2p_passed"] / base["p2p_total"]
check["p2p"] = check["p2p_passed"] / check["p2p_total"]

both = baseline_only = check_only = neither = 0
partial_deltas = []
for task, rep in keys:
    left = records[("baseline", task, rep)]
    right = records[("pi-check", task, rep)]
    left_solved = left["reward_binary"] == 1
    right_solved = right["reward_binary"] == 1
    both += left_solved and right_solved
    baseline_only += left_solved and not right_solved
    check_only += right_solved and not left_solved
    neither += not left_solved and not right_solved
    partial_deltas.append(right["reward_partial"] - left["reward_partial"])
partial_wins = sum(delta > 0 for delta in partial_deltas)
partial_losses = sum(delta < 0 for delta in partial_deltas)
partial_ties = sum(delta == 0 for delta in partial_deltas)


def exact_sign_p(left_only_count: int, right_only_count: int) -> float:
    discordant = left_only_count + right_only_count
    if discordant == 0:
        return 1.0
    tail = min(left_only_count, right_only_count)
    return min(1.0, 2 * sum(math.comb(discordant, index) for index in range(tail + 1)) / (2**discordant))


rng = random.Random(20260729)
binary_bootstrap = []
partial_bootstrap = []
for _ in range(50_000):
    sampled_tasks = [rng.choice(tasks) for _ in tasks]
    sampled_keys = [(task, rep) for task in sampled_tasks for rep in range(3)]
    binary_bootstrap.append(statistics.mean((records[("pi-check", *key)]["reward_binary"] == 1) - (records[("baseline", *key)]["reward_binary"] == 1) for key in sampled_keys))
    partial_bootstrap.append(statistics.mean(records[("pi-check", *key)]["reward_partial"] - records[("baseline", *key)]["reward_partial"] for key in sampled_keys))
binary_bootstrap.sort()
partial_bootstrap.sort()
binary_ci = (binary_bootstrap[1250], binary_bootstrap[48749])
partial_ci = (partial_bootstrap[1250], partial_bootstrap[48749])

nonzero_partial = [delta for delta in partial_deltas if delta != 0]
partial_sign_p = exact_sign_p(sum(delta < 0 for delta in nonzero_partial), sum(delta > 0 for delta in nonzero_partial))

traces = {(task, rep): session_trace(ROOTS["pi-check"] / task / f"rep{rep}") for task, rep in keys}
delivered_keys = [key for key in keys if traces[key]["prompt_count"] == 1]
missing_keys = [key for key in keys if traces[key]["prompt_count"] == 0]
post_check_tokens = sum(traces[key]["post_check_tokens"] for key in delivered_keys)
post_check_turns = sum(traces[key]["post_check_turns"] for key in delivered_keys)
post_check_tools = sum(sum(traces[key]["post_check_tool_counts"].values()) for key in delivered_keys)
mutated_after_check = sum(traces[key]["post_check_tool_counts"].get("edit", 0) + traces[key]["post_check_tool_counts"].get("write", 0) > 0 for key in delivered_keys)

clean_keys = [key for key in keys if not records[("baseline", *key)]["agent_timed_out"] and not records[("pi-check", *key)]["agent_timed_out"] and records[("baseline", *key)]["verifier_exit"] in (0, None) and records[("pi-check", *key)]["verifier_exit"] in (0, None)]
clean_base_partial = statistics.mean(records[("baseline", *key)]["reward_partial"] for key in clean_keys)
clean_check_partial = statistics.mean(records[("pi-check", *key)]["reward_partial"] for key in clean_keys)
delivered_base_partial = statistics.mean(records[("baseline", *key)]["reward_partial"] for key in delivered_keys)
delivered_check_partial = statistics.mean(records[("pi-check", *key)]["reward_partial"] for key in delivered_keys)
outlier_key = ("tengo-callable-instance-isolation", 1)
base_tokens_no_outlier = sum(records[("baseline", *key)]["total_tokens"] for key in keys if key != outlier_key)
check_tokens_no_outlier = sum(records[("pi-check", *key)]["total_tokens"] for key in keys if key != outlier_key)

metric_rows = [
    ("Binary solves", f'{base["solves"]}/36 · {pct(base["solves"]/36)}', f'{check["solves"]}/36 · {pct(check["solves"]/36)}', pp((check["solves"]-base["solves"])/36), "good"),
    ("Mean partial reward", pct(base["partial_mean"]), pct(check["partial_mean"]), pp(check["partial_mean"]-base["partial_mean"]), "good"),
    ("Median partial reward", pct(base["partial_median"]), pct(check["partial_median"]), pp(check["partial_median"]-base["partial_median"]), "good"),
    ("Weighted F2P", f'{base["f2p_passed"]}/{base["f2p_total"]} · {pct(base["f2p"])}', f'{check["f2p_passed"]}/{check["f2p_total"]} · {pct(check["f2p"])}', pp(check["f2p"]-base["f2p"]), "good"),
    ("Weighted P2P", f'{base["p2p_passed"]:,}/{base["p2p_total"]:,} · {pct(base["p2p"])}', f'{check["p2p_passed"]:,}/{check["p2p_total"]:,} · {pct(check["p2p"])}', pp(check["p2p"]-base["p2p"]), "good"),
    ("Total tokens", f'{base["tokens"]/1e6:.1f}M', f'{check["tokens"]/1e6:.1f}M', ratio_delta(check["tokens"], base["tokens"]), "bad"),
    ("Median tokens / cell", f'{base["median_tokens"]/1000:.0f}K', f'{check["median_tokens"]/1000:.0f}K', ratio_delta(check["median_tokens"], base["median_tokens"]), "bad"),
    ("Mean agent wall time", f'{base["mean_wall"]:.0f}s', f'{check["mean_wall"]:.0f}s', ratio_delta(check["mean_wall"], base["mean_wall"]), "bad"),
    ("Mean turns", f'{base["mean_turns"]:.1f}', f'{check["mean_turns"]:.1f}', ratio_delta(check["mean_turns"], base["mean_turns"]), "bad"),
    ("Mean tool calls", f'{base["mean_tools"]:.1f}', f'{check["mean_tools"]:.1f}', ratio_delta(check["mean_tools"], base["mean_tools"]), "bad"),
    ("Agent timeouts", str(base["timeouts"]), str(check["timeouts"]), f'{check["timeouts"]-base["timeouts"]:+d}', "bad"),
    ("Nonzero verifier exits", str(base["verifier_nonzero"]), str(check["verifier_nonzero"]), f'{check["verifier_nonzero"]-base["verifier_nonzero"]:+d}', "bad"),
]
metric_html = "".join(f'<tr><td>{html.escape(name)}</td><td class="num">{left}</td><td class="num">{right}</td><td class="num"><span class="tag {verdict}">{delta}</span></td></tr>' for name, left, right, delta, verdict in metric_rows)

task_rows: list[dict[str, Any]] = []
for task in tasks:
    task_keys = [(task, rep) for rep in range(3)]
    metadata = load_task_metadata(task)
    left_partial = statistics.mean(records[("baseline", *key)]["reward_partial"] for key in task_keys)
    right_partial = statistics.mean(records[("pi-check", *key)]["reward_partial"] for key in task_keys)
    task_rows.append({"task": task, "title": metadata["title"], "difficulty": metadata["difficulty"], "language": records[("baseline", task, 0)]["language"], "left_solves": sum(records[("baseline", *key)]["reward_binary"] == 1 for key in task_keys), "right_solves": sum(records[("pi-check", *key)]["reward_binary"] == 1 for key in task_keys), "left_partial": left_partial, "right_partial": right_partial, "left_timeouts": sum(records[("baseline", *key)]["agent_timed_out"] for key in task_keys), "right_timeouts": sum(records[("pi-check", *key)]["agent_timed_out"] for key in task_keys)})
task_rows.sort(key=lambda row: (-(row["right_partial"] - row["left_partial"]), row["task"]))
task_html = "".join(f'<tr><td><strong>{html.escape(row["task"])}</strong><br><span class="muted">{html.escape(row["title"])}</span></td><td>{html.escape(row["language"])}</td><td>{row["difficulty"]}</td><td class="num">{row["left_solves"]}</td><td class="num">{row["right_solves"]}</td><td class="num">{pct(row["left_partial"])}</td><td class="num">{pct(row["right_partial"])}</td><td class="num"><span class="tag {"good" if row["right_partial"] > row["left_partial"] else "bad" if row["right_partial"] < row["left_partial"] else "neutral"}">{pp(row["right_partial"]-row["left_partial"])}</span></td><td class="num">{row["left_timeouts"]} → {row["right_timeouts"]}</td></tr>' for row in task_rows)

split_rows = []
for field in ("language", "difficulty"):
    values = sorted({row[field] for row in task_rows})
    for value in values:
        split_keys = [key for key in keys if (records[("baseline", *key)]["language"] if field == "language" else load_task_metadata(key[0])["difficulty"]) == value]
        left_partial = statistics.mean(records[("baseline", *key)]["reward_partial"] for key in split_keys)
        right_partial = statistics.mean(records[("pi-check", *key)]["reward_partial"] for key in split_keys)
        split_rows.append((field, value, len(split_keys), sum(records[("baseline", *key)]["reward_binary"] == 1 for key in split_keys), sum(records[("pi-check", *key)]["reward_binary"] == 1 for key in split_keys), left_partial, right_partial))
split_html = "".join(f'<tr><td>{field}</td><td>{html.escape(value)}</td><td class="num">{count}</td><td class="num">{left_solve}</td><td class="num">{right_solve}</td><td class="num">{pct(left_partial)}</td><td class="num">{pct(right_partial)}</td><td class="num">{pp(right_partial-left_partial)}</td></tr>' for field, value, count, left_solve, right_solve, left_partial, right_partial in split_rows)

bucket_counts = collections.Counter(packet["classification"]["primary_bucket"] for packet in packets)
bucket_html = "".join(f'<tr><td>{html.escape(bucket)}</td><td class="num">{count}</td></tr>' for bucket, count in bucket_counts.most_common())
packet_html = "".join(f'<tr><td><strong>{html.escape(packet["pair"]["task"])}</strong></td><td class="num">{packet["pair"]["rep"]}</td><td>{html.escape(", ".join(packet["triggers"]))}</td><td class="num">{pp(packet["right"]["result"]["reward_partial"]-packet["left"]["result"]["reward_partial"])}</td><td><span class="tag {"bad" if packet["classification"]["primary_bucket"] in {"resource exhaustion", "cross-scope regression"} else "caution"}">{html.escape(packet["classification"]["primary_bucket"])}</span></td><td>{html.escape(packet["classification"]["mechanism"])}</td><td><a href="{packet["packet_link"]}">packet</a></td></tr>' for packet in packets)

pair_html = ""
for task, rep in keys:
    left = records[("baseline", task, rep)]
    right = records[("pi-check", task, rep)]
    delta = right["reward_partial"] - left["reward_partial"]
    delivery = "delivered" if traces[(task, rep)]["prompt_count"] == 1 else "missing"
    pair_html += f'<tr><td>{html.escape(task)}</td><td class="num">{rep}</td><td class="num">{left["reward_binary"]}</td><td class="num">{right["reward_binary"]}</td><td class="num">{pct(left["reward_partial"])}</td><td class="num">{pct(right["reward_partial"])}</td><td class="num"><span class="tag {"good" if delta > 0 else "bad" if delta < 0 else "neutral"}">{pp(delta)}</span></td><td>{delivery}</td><td class="num">{left["total_tokens"]:,}</td><td class="num">{right["total_tokens"]:,}</td></tr>'

style = """
:root{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08)}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,rgba(51,93,255,.11),transparent 28%),linear-gradient(#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:1260px;margin:auto;padding:28px 20px 60px}.hero,section{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:38px}.eyebrow{display:inline-block;padding:7px 11px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1{font-size:clamp(2.4rem,5vw,4.5rem);line-height:1.02;letter-spacing:-.045em;max-width:14ch;margin:14px 0}.lede{font-size:1.1rem;color:var(--muted);max-width:80ch}.pills{display:flex;gap:9px;flex-wrap:wrap;margin-top:20px}.pill,.tag{display:inline-flex;padding:6px 10px;border-radius:999px;font-weight:800;font-size:12px}.good{background:var(--green-soft);color:var(--green)}.bad{background:var(--red-soft);color:var(--red)}.caution{background:var(--amber-soft);color:#8a6100}.neutral{background:#edf1f7;color:#536173}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:13px;margin-top:20px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.7rem;line-height:1.1;letter-spacing:-.04em}.stat span{color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:28px}h2{font-size:1.75rem;letter-spacing:-.03em;margin:0 0 6px}h3{margin-bottom:5px}.section-lede{color:var(--muted);margin:0 0 18px}.callout{border-left:5px solid var(--blue);background:#f6f8ff;padding:15px 17px;border-radius:13px;margin:16px 0}.callout.goodline{border-color:var(--green);background:var(--green-soft)}.callout.warn{border-color:var(--amber);background:var(--amber-soft)}.callout.badline{border-color:var(--red);background:var(--red-soft)}table{width:100%;border-collapse:collapse;font-size:14px}th,td{text-align:left;padding:11px 10px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:11px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}td.num,th.num{text-align:right;font-variant-numeric:tabular-nums}.table-wrap{overflow-x:auto}.bars{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.bar-card{border:1px solid var(--line);border-radius:16px;padding:15px}.bar-card strong{font-size:1.55rem}.bar{height:9px;border-radius:99px;background:#edf1f7;overflow:hidden;margin-top:10px}.bar i{display:block;height:100%;border-radius:99px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:18px}.evidence{font-family:ui-monospace,monospace;font-size:13px;background:#f7f9fc;border:1px solid var(--line);padding:13px;border-radius:12px}details{border:1px solid var(--line);border-radius:14px;padding:12px 14px;margin-top:12px}summary{cursor:pointer;font-weight:800}code{background:#eef2ff;padding:.1em .35em;border-radius:5px}a{color:var(--blue);font-weight:800}.muted{color:var(--muted)}footer{color:var(--muted);text-align:center;padding:25px}@media(max-width:850px){.stats{grid-template-columns:repeat(2,1fr)}.bars,.grid2{grid-template-columns:1fr}.hero,section{padding:22px}}@media(max-width:520px){.stats{grid-template-columns:1fr}}
"""

generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Gemma 4 pi-check final comparison</title><style>{style}</style></head><body><div class="wrap">
<header class="hero"><span class="eyebrow">DeepSWE · final matched 12_v2 comparison · Gemma 4 31B high · 3 reps</span><h1>Two solves—but not a convincing win.</h1><p class="lede">pi-check moved Gemma 4 from <strong>0/36 to 2/36 binary solves</strong> and raised mean partial reward by <strong>{pp(check['partial_mean']-base['partial_mean'])}</strong>. Both solves came from one task, the uncertainty intervals include no effect, token use rose {ratio_delta(check['tokens'],base['tokens'])}, and agent timeouts rose from {base['timeouts']} to {check['timeouts']}.</p><div class="pills"><span class="pill good">+2 solves</span><span class="pill good">{pp(check['partial_mean']-base['partial_mean'])} partial</span><span class="pill bad">{ratio_delta(check['tokens'],base['tokens'])} tokens</span><span class="pill bad">{base['timeouts']} → {check['timeouts']} timeouts</span><span class="pill caution">33/36 treatment delivered</span></div><div class="stats"><div class="stat"><strong>{check['solves']}/36</strong><span>pi-check solves</span></div><div class="stat"><strong>{base['solves']}/36</strong><span>baseline solves</span></div><div class="stat"><strong>{pct(check['partial_mean'])}</strong><span>pi-check partial</span></div><div class="stat"><strong>{pct(base['partial_mean'])}</strong><span>baseline partial</span></div><div class="stat"><strong>{check['tokens']/1e6:.1f}M</strong><span>pi-check tokens</span></div></div></header>
<section><h2>Verdict</h2><p class="section-lede">Promising efficacy signal, weak certainty, unacceptable efficiency and timeout behavior in this form.</p><div class="callout goodline"><strong>What worked:</strong> pi-check solved two recursive-delegation cells that baseline nearly solved, moving F2P from 0/7 and 2/7 to 7/7 while preserving 31/31 P2P. It also produced large partial gains on Go-Critic, SuperJSON, Adaptix, and Participle.</div><div class="callout warn"><strong>Why this is not a clear win:</strong> the two-sided exact discordant-cell test is p={exact_sign_p(baseline_only,check_only):.3f}. The task-cluster bootstrap 95% interval is {pp(binary_ci[0])} to {pp(binary_ci[1])} for binary solve rate and {pp(partial_ci[0])} to {pp(partial_ci[1])} for partial reward. Both include zero.</div><div class="callout badline"><strong>Operational cost:</strong> pi-check used {check['tokens']/1e6:.1f}M tokens versus {base['tokens']/1e6:.1f}M, doubled mean wall time, and timed out in 9/36 cells versus 2/36. The current Gemma pi-check configuration should not be adopted unchanged.</div></section>
<section><h2>Score and efficiency</h2><p class="section-lede">Intention-to-treat: all 36 exact task/rep pairs remain in the primary result, including missing treatment and timeout sentinels.</p><div class="table-wrap"><table><thead><tr><th>Metric</th><th class="num">Baseline</th><th class="num">pi-check</th><th class="num">Delta</th></tr></thead><tbody>{metric_html}</tbody></table></div><div class="callout"><strong>Partial movement:</strong> {partial_wins} pairs improved, {partial_losses} regressed, and {partial_ties} tied. The median paired movement was only {pp(statistics.median(partial_deltas))}; the mean was pulled up by several large repairs. Ignoring ties, the unclustered sign test is p={partial_sign_p:.3f}.</div><div class="callout warn"><strong>Outlier sensitivity:</strong> Tengo rep1 consumed 42.3M pi-check tokens before timing out—31.8% of all treatment tokens—and never received the check prompt. Excluding that pair still leaves {check_tokens_no_outlier/1e6:.1f}M versus {base_tokens_no_outlier/1e6:.1f}M tokens, a {ratio_delta(check_tokens_no_outlier,base_tokens_no_outlier)} increase.</div></section>
<section><h2>Delivery: what pi-check actually did</h2><div class="grid2"><div class="evidence"><strong>Configuration lock</strong><br>baseline-gemma4-31b@1.0.0<br>vs pi-check@1.1.0<br>local-vllm/gemma-4-31b · high<br>12_v2 · reps 0–2<br>36/36 exact matched results<br>72/72 requests per side match Gemma thinking + sampling</div><div class="evidence"><strong>Follow-up behavior</strong><br>{len(delivered_keys)}/36 sessions: delivered exactly once<br>{len(missing_keys)}/36: missing because original attempt timed out<br>{mutated_after_check}/{len(delivered_keys)} delivered cells used edit/write after the prompt<br>{post_check_turns} post-check assistant turns<br>{post_check_tools} post-check tool calls<br>{post_check_tokens/1e6:.1f}M post-check tokens</div></div><div class="callout warn"><strong>pi-check is an intervention, not a passive audit.</strong> Every delivered follow-up changed files. The median delivered follow-up took {statistics.median(traces[key]['post_check_turns'] for key in delivered_keys):.0f} assistant turns and consumed {statistics.median(traces[key]['post_check_tokens'] for key in delivered_keys)/1e6:.2f}M tokens. Three cells—Tengo reps 1/2 and SQL Formatter rep0—timed out before treatment delivery; they remain in the intention-to-treat result as <em>missing</em>.</div></section>
<section><h2>Net versus churn</h2><p class="section-lede">Binary churn was one-directional but narrow; partial churn was broad in both directions.</p><div class="bars"><div class="bar-card"><strong>{both}</strong><div>both solved</div><div class="bar"><i style="width:{both/36*100:.1f}%;background:var(--blue)"></i></div></div><div class="bar-card"><strong style="color:var(--green)">{check_only}</strong><div>pi-check only</div><div class="bar"><i style="width:{check_only/36*100:.1f}%;background:var(--green)"></i></div></div><div class="bar-card"><strong style="color:var(--red)">{baseline_only}</strong><div>baseline only</div><div class="bar"><i style="width:{baseline_only/36*100:.1f}%;background:var(--red)"></i></div></div><div class="bar-card"><strong>{neither}</strong><div>neither solved</div><div class="bar"><i style="width:{neither/36*100:.1f}%;background:var(--amber)"></i></div></div></div><div class="callout"><strong>Concentration:</strong> both binary gains were <code>claude-code-by-agents-recursive-delegation</code> reps 0 and 1. No other task produced a solve on either side, so the +2 result does not yet show broad task generalization.</div></section>
<section><h2>Timeout sensitivity</h2><p class="section-lede">Sensitivity views are descriptive because removing post-treatment failures changes the estimand.</p><div class="grid2"><div><h3>Clean on both sides</h3><p>{len(clean_keys)}/36 pairs had no agent timeout and a normal verifier exit on either side. Within them, partial reward was {pct(clean_base_partial)} baseline versus {pct(clean_check_partial)} pi-check ({pp(clean_check_partial-clean_base_partial)}), with 0 versus 2 solves.</p></div><div><h3>Delivered treatment only</h3><p>Across the {len(delivered_keys)} cells where the prompt arrived, partial reward was {pct(delivered_base_partial)} baseline versus {pct(delivered_check_partial)} pi-check ({pp(delivered_check_partial-delivered_base_partial)}), again 0 versus 2 solves.</p></div></div><div class="callout warn"><strong>Interpret carefully:</strong> the favorable clean-pair view does not erase the timeout penalty. Six delivered follow-ups timed out after the prompt, and three more original attempts timed out before it.</div></section>
<section><h2>Task direction</h2><p class="section-lede">The partial gain is concentrated: Go-Critic +59.6 pp, SuperJSON +42.7 pp, and Adaptix +32.0 pp; Mobly and Tengo moved backward.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th>Language</th><th>Difficulty</th><th class="num">Base solves</th><th class="num">Check solves</th><th class="num">Base partial</th><th class="num">Check partial</th><th class="num">Delta</th><th class="num">Timeouts</th></tr></thead><tbody>{task_html}</tbody></table></div></section>
<section><h2>Language and difficulty direction</h2><p class="section-lede">These splits are small and descriptive. The two solves are both TypeScript cells from one task.</p><div class="table-wrap"><table><thead><tr><th>Split</th><th>Value</th><th class="num">Cells</th><th class="num">Base solves</th><th class="num">Check solves</th><th class="num">Base partial</th><th class="num">Check partial</th><th class="num">Delta</th></tr></thead><tbody>{split_html}</tbody></table></div></section>
<section><h2>Trajectory findings</h2><p class="section-lede">Packet rule: every binary flip, negative-reward discordance, agent-timeout discordance, ≥50 pp partial movement, or ≥50 pp F2P/P2P movement. This selected {len(packets)} cells.</p><div class="grid2"><div><h3>Driver buckets</h3><div class="table-wrap"><table><thead><tr><th>Primary bucket</th><th class="num">Packets</th></tr></thead><tbody>{bucket_html}</tbody></table></div></div><div><h3>Winning and losing pattern</h3><p><strong>Keep:</strong> the fresh pass often rescued implementations whose grader suite did not run or whose explicit behavior matrix was incomplete.</p><p><strong>Prevent:</strong> the same pass always edited code, sometimes displaced public behavior, broke compilation, expanded patch scope, or consumed the remaining execution budget.</p></div></div><div class="callout"><strong>Mechanism read:</strong> pi-check helps when the first attempt is a near-miss and the follow-up can run focused validation. It hurts when the first attempt has already consumed most of the budget or when the follow-up edits architecture without a fast compile/import gate. This is supported by session, patch, and verifier artifacts, but sampling variance remains a possible contributor.</div><details><summary>Open all {len(packets)} triggered trajectory packets</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th>Trigger</th><th class="num">Partial Δ</th><th>Driver</th><th>Evidence-backed mechanism</th><th>Evidence</th></tr></thead><tbody>{packet_html}</tbody></table></div></details></section>
<section><h2>Run integrity</h2><div class="callout goodline"><strong>Complete and internally consistent:</strong> 36/36 final pi-check results, no active cells or containers, passed preflight, sealed config, matching model/thinking/provider request evidence, and dashboard state <code>completed / done</code>. The two power-interrupted partial baseline cells were quarantined and rerun before this comparison.</div><p class="muted">Result roots: <code>{ROOTS['baseline']}</code> and <code>{ROOTS['pi-check']}</code>. Launch plan: <code>sha256:0706143246a00cbf07593530a41322a1aecc0702fe13c978cf61b2c187661a4e</code>.</p></section>
<section><h2>All 36 matched cells</h2><details><summary>Open the complete pair table</summary><div class="table-wrap"><table><thead><tr><th>Task</th><th class="num">Rep</th><th class="num">Base binary</th><th class="num">Check binary</th><th class="num">Base partial</th><th class="num">Check partial</th><th class="num">Delta</th><th>Delivery</th><th class="num">Base tokens</th><th class="num">Check tokens</th></tr></thead><tbody>{pair_html}</tbody></table></div></details></section>
<section><h2>Conclusion and next decision</h2><div class="callout goodline"><strong>Observed upside:</strong> pi-check can rescue Gemma implementations. It produced two complete solves and several large partial repairs that the original attempt missed.</div><div class="callout badline"><strong>Observed downside:</strong> the current unbounded follow-up is too expensive and too failure-prone: 3.39× tokens, 2.09× wall time, 25% agent timeouts, and three cells where the follow-up never ran.</div><div class="callout"><strong>Recommendation:</strong> do not use <code>pi-check@1.1.0</code> unchanged as the Gemma default. The next experiment should test a bounded variant: run a fast compile/import and targeted-test audit first, edit only when it identifies a concrete unmet requirement, and stop when remaining wall time cannot cover validation. That is a new config hypothesis requiring approved prompt/tool behavior—not a reinterpretation of this result.</div></section>
<footer>Generated {generated} from saved DeepSWE artifacts · 12_v2 · local-vllm/gemma-4-31b high · 3 reps · packet index <a href="packets/packet_index.json">JSON</a></footer></div></body></html>"""
OUT.write_text(page)
print(OUT)
print(f"packets={len(packets)} delivered={len(delivered_keys)} missing={len(missing_keys)}")

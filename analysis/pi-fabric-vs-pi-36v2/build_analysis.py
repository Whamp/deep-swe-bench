#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import math
import random
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
RESULTS = REPO / "results/gpt-5.6-sol/low"
RUN_ID = "gpt56-sol-low-pi-fabric-36v2-r3-w16-20260724"
MANIFEST = REPO / "results/_runs" / RUN_ID / "manifest.json"
METRICS = [
    "reward_binary",
    "reward_partial",
    "f2p",
    "p2p",
    "combined_total_tokens",
    "combined_cost_usd",
    "agent_wall_s",
    "turns",
    "tool_calls",
    "patch_bytes",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def load_metadata() -> dict[str, dict[str, Any]]:
    with (REPO / "data/deepswe-v1.1-task-difficulty.tsv").open() as handle:
        out = {}
        for row in csv.DictReader(handle, delimiter="\t"):
            rate = int(row["pass_rate"])
            row["difficulty"] = (
                "hard" if rate < 33 else "medium" if rate < 66 else "easy"
            )
            row["pass_rate"] = rate
            out[row["slug"]] = row
        return out


def exact_mcnemar(left_only: int, right_only: int) -> float:
    n = left_only + right_only
    if n == 0:
        return 1.0
    k = min(left_only, right_only)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2 * tail)


def cluster_bootstrap(
    pairs: list[dict[str, Any]], iterations: int = 100_000
) -> list[float]:
    by_task: dict[str, list[float]] = defaultdict(list)
    for pair in pairs:
        by_task[pair["task"]].append(pair["delta"]["reward_partial"])
    task_means = [statistics.mean(by_task[task]) for task in sorted(by_task)]
    rng = random.Random(20260724)
    draws = sorted(
        statistics.mean(rng.choices(task_means, k=len(task_means)))
        for _ in range(iterations)
    )
    return [draws[int(iterations * 0.025)], draws[int(iterations * 0.975)]]


def patch_stats(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"bytes": 0, "files": [], "adds": 0, "dels": 0, "excerpt": ""}
    text = path.read_text(errors="replace")
    files = re.findall(r"^diff --git a/(.+?) b/", text, re.MULTILINE)
    adds = sum(
        1
        for line in text.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    dels = sum(
        1
        for line in text.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    return {
        "bytes": len(text.encode()),
        "files": files,
        "adds": adds,
        "dels": dels,
        "excerpt": "\n".join(text.splitlines()[:180]),
    }


def trace(path: Path) -> dict[str, Any]:
    tools: Counter[str] = Counter()
    inner: Counter[str] = Counter()
    commands: list[str] = []
    skill_reads: list[str] = []
    for session in path.glob("session/*.jsonl"):
        for line in session.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = record.get("message", {}).get("content", [])
            if not isinstance(content, list):
                continue
            for item in content:
                if item.get("type") != "toolCall":
                    continue
                name = item.get("name", "unknown")
                tools[name] += 1
                args = item.get("arguments", {})
                body = str(args.get("code", "")) if name == "fabric_exec" else str(args)
                if name == "fabric_exec":
                    for operation in re.findall(
                        r"(?:pi|mcp|tools|memory|state|schema|compact)\.([A-Za-z_][A-Za-z0-9_]*)",
                        body,
                    ):
                        inner[operation] += 1
                if name == "bash":
                    commands.append(str(args.get("command", args.get("cmd", ""))))
                commands.extend(
                    re.findall(r"(?:command|cmd)\s*:\s*['\"]([^'\"]+)", body)
                )
                if "SKILL.md" in body:
                    skill_reads.append(body[:500])
    return {
        "tool_counts": dict(tools),
        "inner_counts": dict(inner),
        "commands": commands[:80],
        "skill_reads": skill_reads[:20],
    }


def verifier(path: Path) -> dict[str, Any]:
    ctrf_path = path / "verifier/ctrf.json"
    reward_path = path / "verifier/reward.json"
    failed = []
    summary = {}
    if ctrf_path.exists():
        results = load_json(ctrf_path).get("results", {})
        summary = results.get("summary", {})
        failed = [
            {"name": test.get("name"), "message": str(test.get("message", ""))[:800]}
            for test in results.get("tests", [])
            if test.get("status") == "failed"
        ]
    run_log = path / "verifier/run.log"
    return {
        "summary": summary,
        "failed_count": len(failed),
        "failed": failed[:30],
        "reward": load_json(reward_path) if reward_path.exists() else {},
        "run_log_tail": run_log.read_text(errors="replace")[-5000:]
        if run_log.exists()
        else "",
    }


def side(path: Path, result: dict[str, Any]) -> dict[str, Any]:
    session = next(path.glob("session/*.jsonl"), None)
    keys = METRICS + [
        "f2p_passed",
        "f2p_total",
        "p2p_passed",
        "p2p_total",
        "agent_timed_out",
        "agent_exit",
        "verifier_exit",
    ]
    return {
        "result": {key: result.get(key) for key in keys},
        "session": str(session.relative_to(REPO)) if session else None,
        "patch_stats": patch_stats(path / "artifacts/model.patch"),
        "trace": trace(path),
        "verifier": verifier(path),
    }


def delivery(path: Path) -> str:
    provider = path / "initial_context/provider_request_0001.json"
    options = path / "initial_context/system_prompt_options.json"
    system = path / "initial_context/system_prompt.txt"
    if not all(item.exists() for item in [provider, options, system]):
        return "missing"
    present = [
        '"name": "fabric_exec"' in provider.read_text(errors="replace"),
        '"name": "fabric-exec"' in options.read_text(errors="replace"),
        "<name>fabric-exec</name>" in system.read_text(errors="replace"),
    ]
    stderr = (path / "logs/pi.stderr.txt").read_text(errors="replace")
    if "Failed to load extension" in stderr or "Extension error" in stderr:
        return "ambiguous"
    return "delivered" if all(present) else "missing"


def numeric_values(rows: list[dict[str, Any]], key: str) -> list[float]:
    return [float(row[key]) for row in rows if row.get(key) is not None]


def summarize(pairs: list[dict[str, Any]]) -> dict[str, Any]:
    out: dict[str, Any] = {"n": len(pairs)}
    for config in ["baseline", "pi-fabric"]:
        rows = [pair[config] for pair in pairs]
        f2p_values = numeric_values(rows, "f2p")
        p2p_values = numeric_values(rows, "p2p")
        out[config] = {
            "solves": sum(row["reward_binary"] == 1 for row in rows),
            "mean_partial": statistics.mean(
                float(row["reward_partial"]) for row in rows
            ),
            "mean_f2p": statistics.mean(f2p_values),
            "f2p_graded_n": len(f2p_values),
            "mean_p2p": statistics.mean(p2p_values),
            "p2p_graded_n": len(p2p_values),
            "median_tokens": statistics.median(
                float(row["combined_total_tokens"]) for row in rows
            ),
            "mean_tokens": statistics.mean(
                float(row["combined_total_tokens"]) for row in rows
            ),
            "median_cost": statistics.median(
                float(row["combined_cost_usd"]) for row in rows
            ),
            "total_cost": sum(float(row["combined_cost_usd"]) for row in rows),
            "median_wall_s": statistics.median(
                float(row["agent_wall_s"]) for row in rows
            ),
            "median_turns": statistics.median(float(row["turns"]) for row in rows),
            "median_tool_calls": statistics.median(
                float(row["tool_calls"]) for row in rows
            ),
            "median_patch_bytes": statistics.median(
                float(row["patch_bytes"]) for row in rows
            ),
        }
    out["delta"] = {}
    for key in [
        "reward_partial",
        "f2p",
        "p2p",
        "combined_total_tokens",
        "combined_cost_usd",
        "agent_wall_s",
        "turns",
        "tool_calls",
        "patch_bytes",
    ]:
        deltas = [
            pair["delta"][key] for pair in pairs if pair["delta"][key] is not None
        ]
        out["delta"][f"mean_{key}"] = statistics.mean(deltas)
        out["delta"][f"median_{key}"] = statistics.median(deltas)
        out["delta"][f"graded_n_{key}"] = len(deltas)
    return out


def main() -> None:
    HERE.mkdir(parents=True, exist_ok=True)
    metadata = load_metadata()
    pairs: list[dict[str, Any]] = []
    for cell in load_json(MANIFEST)["batch_cells"]:
        task, rep = cell["task"], int(cell["rep"])
        left_path = RESULTS / "baseline" / task / f"rep{rep}"
        right_path = RESULTS / "pi-fabric" / task / f"rep{rep}"
        left, right = (
            load_json(left_path / "result.json"),
            load_json(right_path / "result.json"),
        )
        meta = metadata[task]
        pairs.append(
            {
                "task": task,
                "rep": rep,
                "title": meta["title"],
                "difficulty": meta["difficulty"],
                "language": meta["language"],
                "pass_rate": meta["pass_rate"],
                "baseline": left,
                "pi-fabric": right,
                "delta": {
                    key: (
                        float(right[key]) - float(left[key])
                        if right.get(key) is not None and left.get(key) is not None
                        else None
                    )
                    for key in METRICS
                },
                "delivery": delivery(right_path),
                "left_path": str(left_path.relative_to(REPO)),
                "right_path": str(right_path.relative_to(REPO)),
            }
        )
    left_only = sum(
        p["baseline"]["reward_binary"] == 1 and p["pi-fabric"]["reward_binary"] != 1
        for p in pairs
    )
    right_only = sum(
        p["baseline"]["reward_binary"] != 1 and p["pi-fabric"]["reward_binary"] == 1
        for p in pairs
    )
    both = sum(
        p["baseline"]["reward_binary"] == p["pi-fabric"]["reward_binary"] == 1
        for p in pairs
    )
    selected = [
        p
        for p in pairs
        if (p["baseline"]["reward_binary"] == 1)
        != (p["pi-fabric"]["reward_binary"] == 1)
        or (
            p["delta"]["reward_partial"] is not None
            and abs(p["delta"]["reward_partial"]) >= 0.1
        )
        or (p["delta"]["f2p"] is not None and abs(p["delta"]["f2p"]) >= 0.1)
        or (p["delta"]["p2p"] is not None and abs(p["delta"]["p2p"]) >= 0.1)
        or p["baseline"]["agent_timed_out"] != p["pi-fabric"]["agent_timed_out"]
        or min(p["baseline"]["reward_partial"], p["pi-fabric"]["reward_partial"]) < 0
    ]
    summary = {
        "comparison": {
            "left": "baseline",
            "right": "pi-fabric",
            "subset": "36_v2",
            "reps": 3,
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
        },
        "aggregate": summarize(pairs),
        "agreement": {
            "both": both,
            "left_only": left_only,
            "right_only": right_only,
            "neither": len(pairs) - both - left_only - right_only,
            "net": right_only - left_only,
            "mcnemar_p": exact_mcnemar(left_only, right_only),
        },
        "cluster_bootstrap_partial_ci95": cluster_bootstrap(pairs),
        "delivery": dict(Counter(p["delivery"] for p in pairs)),
        "execution_audit": {
            "baseline_model_ok": sum(
                p["baseline"].get("model") == "openai-codex/gpt-5.6-sol" for p in pairs
            ),
            "fabric_model_ok": sum(
                p["pi-fabric"].get("model") == "openai-codex/gpt-5.6-sol" for p in pairs
            ),
            "baseline_thinking_ok": sum(
                p["baseline"].get("thinking_level") == "low" for p in pairs
            ),
            "fabric_thinking_ok": sum(
                p["pi-fabric"].get("thinking_level") == "low" for p in pairs
            ),
            "baseline_fabric_leakage": sum(
                "fabric_exec"
                in (
                    REPO / p["left_path"] / "initial_context/provider_request_0001.json"
                ).read_text(errors="replace")
                for p in pairs
            ),
        },
        "selected_packets": [
            f"churn_deep_dive/{p['task']}__rep{p['rep']}.json" for p in selected
        ],
        "by_difficulty": {
            d: summarize([p for p in pairs if p["difficulty"] == d])
            for d in ["hard", "medium", "easy"]
        },
        "by_language": {
            lang: summarize([p for p in pairs if p["language"] == lang])
            for lang in sorted({p["language"] for p in pairs})
        },
    }
    (HERE / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    fields = [
        "task",
        "rep",
        "title",
        "difficulty",
        "language",
        "pass_rate",
        "delivery",
    ] + [
        f"{prefix}_{key}"
        for prefix in ["baseline", "pi_fabric", "delta"]
        for key in METRICS
    ]
    with (HERE / "paired_cells.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for pair in pairs:
            row = {
                key: pair[key]
                for key in [
                    "task",
                    "rep",
                    "title",
                    "difficulty",
                    "language",
                    "pass_rate",
                    "delivery",
                ]
            }
            for key in METRICS:
                row[f"baseline_{key}"] = pair["baseline"].get(key)
                row[f"pi_fabric_{key}"] = pair["pi-fabric"].get(key)
                row[f"delta_{key}"] = pair["delta"][key]
            writer.writerow(row)
    packet_dir = HERE / "churn_deep_dive"
    packet_dir.mkdir(exist_ok=True)
    for stale in packet_dir.glob("*__rep*.json"):
        stale.unlink()
    index = []
    for pair in selected:
        packet = {
            "pair": {
                key: pair[key]
                for key in ["task", "rep", "title", "difficulty", "language"]
            }
            | {"left_config": "baseline", "right_config": "pi-fabric"},
            "left": side(REPO / pair["left_path"], pair["baseline"]),
            "right": side(REPO / pair["right_path"], pair["pi-fabric"]),
            "classification": {
                "primary_bucket": "pending",
                "secondary_bucket": None,
                "mechanism": "Pending evidence review.",
                "evidence": [],
                "guidance_implication": "Pending.",
            },
        }
        stem = f"{pair['task']}__rep{pair['rep']}"
        (packet_dir / f"{stem}.json").write_text(json.dumps(packet, indent=2) + "\n")
        index.append({"task": pair["task"], "rep": pair["rep"], "json": f"{stem}.json"})
    (packet_dir / "index.json").write_text(json.dumps(index, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

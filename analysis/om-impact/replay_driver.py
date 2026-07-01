"""P1/P2 live replay driver (run via `python3 -m analysis.om-impact.replay_driver`).

Loops over cases, resolves each task's codegraph dir, and calls the om-gepa
observer_replay.ts runner via the shared run_ts_runner helper.

  P1: --extension-src <p1-tool variant> + candidate prompt + OM_IMPACT_GRAPH_DIR
      (tests: will a cheap/low model CALL the graph_callers tool?)
  P2: enriched cases (digest already in chunk) + STOCK runner, no graph tool
      (tests: does injected context get distilled into observations?)

Both run in `live` mode against a real model via the pi-codex backend. Outputs
go to analysis/om-impact/runs/ — existing results are never touched.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from analysis.om_gepa.common import run_ts_runner  # noqa: E402

from .impact_common import RUNSDIR, case_task_id, ensure_graph


def write_case_file(case: dict) -> str:
    tf = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
    json.dump(case, tf)
    tf.close()
    return tf.name


def run_one(case: dict, *, mode: str, model: str, thinking: str,
            extension_src: str | None, candidate_prompt: str | None) -> tuple[dict | None, str]:
    tid = case_task_id(case)
    gdir = None
    env_patch: dict[str, str] = {}
    if mode == "p1":
        gdir, status, _ = ensure_graph(tid) if tid else (None, "no_task", {})
        if gdir is None:
            return None, f"graph:{status}"
        env_patch = {"OM_IMPACT_GRAPH_DIR": str(gdir)}
    case_path = write_case_file(case)
    trace_path: str | None = None
    if mode == "p1":
        tf = tempfile.NamedTemporaryFile(suffix=".trace.jsonl", delete=False)
        tf.close()
        trace_path = tf.name
        env_patch["OM_IMPACT_TRACE"] = trace_path
    try:
        old_env = {k: os.environ.get(k) for k in env_patch}
        os.environ.update(env_patch)
        result = run_ts_runner(
            role="observer",
            case_path=Path(case_path),
            candidate_prompt=Path(candidate_prompt) if candidate_prompt else None,
            mock_mode="live",
            extension_src=Path(extension_src) if extension_src else None,
            backend="pi-codex",
            model=model,
            thinking_level=thinking,
        )
        tool_calls: list[dict] = []
        if trace_path and Path(trace_path).exists():
            for line in Path(trace_path).read_text().splitlines():
                if line.strip():
                    try: tool_calls.append(json.loads(line))
                    except Exception: pass
        result = result or {}
        result["_p1_tool_calls"] = tool_calls
        return result, "ok"
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        Path(case_path).unlink(missing_ok=True)
        if trace_path:
            Path(trace_path).unlink(missing_ok=True)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mode", choices=["p1", "p2"], required=True)
    ap.add_argument("--cases", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="openai-codex/gpt-5.4-mini")
    ap.add_argument("--thinking", default="low")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--max-turns", type=int, default=4)
    a = ap.parse_args()

    VARIANTS = REPO / "analysis" / "om-impact" / "variants" / "p1-tool"
    ext_src = str(VARIANTS / "src") if a.mode == "p1" else None
    cand = str(VARIANTS / "p1_prompt.txt") if a.mode == "p1" else None

    rows = [json.loads(l) for l in Path(a.cases).read_text().splitlines() if l.strip()]
    if a.limit:
        rows = rows[:a.limit]
    opath = Path(a.out)
    opath.parent.mkdir(parents=True, exist_ok=True)
    statuses: dict[str, int] = {}
    with opath.open("w") as f:
        for i, c in enumerate(rows, 1):
            res, status = run_one(c, mode=a.mode, model=a.model, thinking=a.thinking,
                                  extension_src=ext_src, candidate_prompt=cand)
            statuses[status] = statuses.get(status, 0) + 1
            tool_calls = (res or {}).get("_p1_tool_calls", [])
            rec = {
                "mode": a.mode, "case_id": c.get("case_id"), "task": case_task_id(c),
                "model": a.model, "thinking": a.thinking, "status": status,
                "observations": (res or {}).get("observations", []),
                "tool_calls": tool_calls,
                "n_tool_calls": len(tool_calls),
                "mock_mode": (res or {}).get("mock_mode"),
            }
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            n_obs = len(rec["observations"])
            print(f"[{a.mode} {i}/{len(rows)}] {case_task_id(c)}: {status} obs={n_obs} tool_calls={len(tool_calls)}", flush=True)
    print(f"\n{a.mode} done. status counts:", statuses)
    print(f"-> {opath}")


if __name__ == "__main__":
    main()

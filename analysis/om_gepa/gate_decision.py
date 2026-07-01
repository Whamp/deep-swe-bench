#!/usr/bin/env python3
"""OM GEPA promotion gate-decision generator (step 7).

Pure reader: reads the step-5 manifest val_gate plus the four step-6 compare.py
summary.json files and emits a markdown gate-decision note tying each objective
gate to its evidence file. Zero model calls.

The goal's step-7 objective gates (automatable subset):
  1. In-distribution Codex test mean delta >= +0.02 with bootstrap lower bound > 0.
  2. valid_rate not lower on any set (all four compare summaries).
  3. Cross-model (Qwen) mean delta not materially worse (>= -0.02).

Manual gates NOT auto-checked here (require human / live run):
  - Worst-10 regression scan for scary behavior.
  - One live benchmark slice before promoting into a new config directory.

Usage:
  python3 -m analysis.om_gepa.gate_decision \
    --run-dir <step5 run dir> \
    --compare-in-dist <dir>/compare-in-dist/summary.json \
    --compare-glm     <dir>/compare-glm/summary.json \
    --compare-ds      <dir>/compare-ds/summary.json \
    --compare-qwen    <dir>/compare-qwen/summary.json \
    [--out <path>]   # default: <run-dir>/GATE_DECISION.md
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

IN_DIST_MIN_DELTA = 0.02
QWEN_MIN_DELTA = -0.02


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _gate_in_dist(summary: dict[str, Any]) -> dict[str, Any]:
    delta = float(summary.get("mean_delta", 0.0))
    ci = summary.get("bootstrap_ci_95") or {}
    lower = float(ci.get("lower", 0.0)) if isinstance(ci, dict) else 0.0
    passed = delta >= IN_DIST_MIN_DELTA and lower > 0.0
    return {
        "passed": passed,
        "mean_delta": delta,
        "ci_lower": lower,
        "rule": f"mean_delta {delta:+.4f} >= +{IN_DIST_MIN_DELTA:.2f} AND bootstrap lower {lower:+.4f} > 0",
    }


def _gate_valid_rate(summaries: dict[str, str, dict]) -> list[dict[str, Any]]:
    rows = []
    for label, s in summaries.items():
        d = float(s.get("valid_rate_delta", 0.0))
        rows.append({
            "set": label,
            "passed": d >= 0.0,
            "valid_rate_delta": d,
            "rule": f"valid_rate_delta {d:+.4f} >= 0",
        })
    return rows


def _gate_qwen(summary: dict[str, Any]) -> dict[str, Any]:
    delta = float(summary.get("mean_delta", 0.0))
    passed = delta >= QWEN_MIN_DELTA
    return {
        "passed": passed,
        "mean_delta": delta,
        "rule": f"mean_delta {delta:+.4f} >= {QWEN_MIN_DELTA:.2f}",
    }


def render(manifest: dict[str, Any], sums: dict[str, dict[str, Any]], out: Path) -> dict[str, Any]:
    run_dir = out.parent
    val_gate = manifest.get("val_gate", {})
    in_dist = _gate_in_dist(sums["in_dist"])
    vr_rows = _gate_valid_rate({k: v for k, v in sums.items()})
    qwen = _gate_qwen(sums["qwen"])
    valid_rate_all = all(r["passed"] for r in vr_rows)

    # Only the 3 automatable objective gates count toward promote/no-promote here.
    auto_pass = val_gate.get("cleared", False) and in_dist["passed"] and valid_rate_all and qwen["passed"]

    lines = [
        "# OM GEPA observer gate-decision (step 7)",
        "",
        f"- run: `{manifest.get('run_name', run_dir.name)}`",
        f"- generated from step-5 manifest + four step-6 compare summaries",
        "",
        "## Step-5 val gate (selection rule)",
        f"- cleared: **{val_gate.get('cleared', False)}**",
        f"- reason: {val_gate.get('reason', '(no val_gate in manifest)')}",
        "",
        "## Automatable objective gates",
        "",
        f"### 1. In-distribution Codex (mean delta >= +0.02, bootstrap lower > 0)",
        f"- evidence: `compare-in-dist/summary.json`",
        f"- {in_dist['rule']}",
        f"- **{'PASS' if in_dist['passed'] else 'FAIL'}**",
        "",
        "### 2. valid_rate not lower on any set",
    ]
    for r in vr_rows:
        lines.append(f"- {r['set']}: {r['rule']} -> **{'PASS' if r['passed'] else 'FAIL'}**")
    lines += [
        "",
        f"### 3. Cross-model Qwen (mean delta >= -0.02)",
        f"- evidence: `compare-qwen/summary.json`",
        f"- {qwen['rule']}",
        f"- **{'PASS' if qwen['passed'] else 'FAIL'}**",
        "",
        "## Manual gates (NOT auto-checked)",
        "- [ ] Worst-10 regression scan finds no scary behavior (see each compare `summary.json` `worst_regressions`).",
        "- [ ] One live benchmark slice before promoting into a new config directory.",
        "",
        "## Decision",
        f"- automatable gates: **{'ALL PASS' if auto_pass else 'NOT ALL PASS'}**",
        f"- **PROMOTE: no** — automatable gates incomplete; manual gates outstanding." ,
        "",
        "A promote=yes decision requires all automatable gates AND both manual gates to pass. "
        "Until then do not promote into a new config directory.",
    ]
    if not val_gate.get("cleared", False):
        lines += [
            "",
            "## Note",
            "Step-5 val gate did not clear, so step-6 validation should not have run per the goal. "
            "This is a valid outcome: no promote-worthy candidate (val delta < +0.02).",
        ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "val_gate_cleared": bool(val_gate.get("cleared", False)),
        "auto_gates_pass": bool(auto_pass),
        "in_dist": in_dist,
        "valid_rate_rows": vr_rows,
        "qwen": qwen,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--run-dir", type=Path, required=True, help="step-5 run directory (contains manifest.json)")
    ap.add_argument("--compare-in-dist", type=Path, required=True)
    ap.add_argument("--compare-glm", type=Path, required=True)
    ap.add_argument("--compare-ds", type=Path, required=True)
    ap.add_argument("--compare-qwen", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    manifest_path = args.run_dir / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(f"manifest.json not found in {args.run_dir}")
    manifest = _load(manifest_path)
    sums = {
        "in_dist": _load(args.compare_in_dist),
        "glm": _load(args.compare_glm),
        "ds": _load(args.compare_ds),
        "qwen": _load(args.compare_qwen),
    }
    out = args.out or (args.run_dir / "GATE_DECISION.md")
    result = render(manifest, sums, out)
    print(f"wrote {out}")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

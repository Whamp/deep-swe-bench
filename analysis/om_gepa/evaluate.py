from __future__ import annotations

import argparse
import json
from pathlib import Path
from statistics import mean
from tempfile import NamedTemporaryFile
from typing import Any

from . import ARTIFACT_ROOT
from .common import prompt_patch, read_jsonl, run_ts_runner, write_changed_cases_html, write_csv, write_jsonl
from .metrics import score_observer_output, score_reflector_output


def score(role: str, case: dict[str, Any], output: dict[str, Any]) -> dict[str, Any]:
    return score_observer_output(case, output) if role == "observer" else score_reflector_output(case, output)


def evaluate_cases(
    role: str,
    cases_path: Path,
    out_dir: Path,
    candidate_prompt: Path | None = None,
    mock_mode: str = "gold",
    limit: int | None = None,
    *,
    backend: str = "openai-compatible",
    model: str | None = None,
    thinking_level: str | None = None,
) -> dict[str, Any]:
    cases = read_jsonl(cases_path)
    if limit is not None:
        cases = cases[:limit]
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for idx, case in enumerate(cases):
        with NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as f:
            json.dump(case, f, ensure_ascii=False)
            tmp_case = Path(f.name)
        try:
            output = run_ts_runner(role, tmp_case, candidate_prompt, mock_mode, backend=backend, model=model, thinking_level=thinking_level)
        finally:
            tmp_case.unlink(missing_ok=True)
        scored = score(role, case, output)
        row = {
            "case_id": case.get("case_id"),
            "split": case.get("split"),
            "score": round(float(scored["score"]), 6),
            "valid": scored["valid"],
            "feedback": scored["feedback"],
            "output_count": len(output.get("observations", output.get("reflections", []))),
            "backend": output.get("backend", backend),
            "model": output.get("model", model),
            "thinking_level": output.get("thinking_level", thinking_level),
            "gold_count": len(case.get("goldObservations", case.get("goldReflections", []))),
        }
        rows.append(row)
        outputs.append({"case": case, "output": output, "score": scored})
        print(f"[{idx+1}/{len(cases)}] {row['case_id']} score={row['score']} valid={row['valid']}")

    write_csv(out_dir / "scores.csv", rows)
    write_jsonl(out_dir / "candidate_outputs.jsonl", outputs)
    write_changed_cases_html(out_dir / "changed_cases.html", rows)
    scores = [float(r["score"]) for r in rows]
    valid_rate = sum(1 for r in rows if r["valid"]) / max(1, len(rows))
    summary = {
        "role": role,
        "cases": len(rows),
        "mean_score": mean(scores) if scores else 0.0,
        "valid_rate": valid_rate,
        "mock_mode": mock_mode,
        "candidate_prompt": str(candidate_prompt) if candidate_prompt else None,
        "backend": backend,
        "model": model,
        "thinking_level": thinking_level,
    }
    report = [
        f"# OM GEPA {role} evaluation",
        "",
        f"- cases: {summary['cases']}",
        f"- mean_score: {summary['mean_score']:.4f}",
        f"- valid_rate: {summary['valid_rate']:.4f}",
        f"- mock_mode: {mock_mode}",
        f"- backend: {backend}",
        f"- model: {model or '(runner default)'}",
        f"- thinking_level: {thinking_level or '(runner default)'}",
        f"- candidate_prompt: {summary['candidate_prompt'] or '(incumbent prompt)'}",
        "",
        "Artifacts: `scores.csv`, `candidate_outputs.jsonl`, `changed_cases.html`.",
    ]
    if candidate_prompt:
        patch = prompt_patch(role, candidate_prompt.read_text(encoding="utf-8"))
        (out_dir / "best_prompt.ts.patch").write_text(patch, encoding="utf-8")
        report.append("- prompt patch: `best_prompt.ts.patch`")
    (out_dir / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate observer/reflector prompt candidates with TS replay runners and deterministic metrics.")
    parser.add_argument("--role", choices=["observer", "reflector"], required=True)
    parser.add_argument("--cases", type=Path, required=True)
    parser.add_argument("--candidate-prompt", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--mock-mode", choices=["gold", "empty", "live"], default="gold", help="Runner mode. gold exercises contract happy path; empty exercises no-tool-call path; live calls the selected backend.")
    parser.add_argument("--backend", choices=["openai-compatible", "pi-codex"], default="openai-compatible")
    parser.add_argument("--model", default=None, help="Worker model spec. For pi-codex use provider/id, e.g. openai-codex/gpt-5.4-mini.")
    parser.add_argument("--thinking-level", default=None, help="Worker thinking level, e.g. low for gpt-5.4-mini.")
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()
    out_dir = args.out or ARTIFACT_ROOT / "runs" / f"eval-{args.role}"
    summary = evaluate_cases(args.role, args.cases, out_dir, args.candidate_prompt, args.mock_mode, args.limit, backend=args.backend, model=args.model, thinking_level=args.thinking_level)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

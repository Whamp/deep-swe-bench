"""Paired incumbent-vs-candidate comparison from two evaluate.py scores.csv files.

Pure CSV join on case_id. No replay, no backend, no model calls. The win/loss/tie
counts ARE the sign test; no separate statistic is reimplemented.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean, median
from typing import Any

TIE_EPS = 1e-9


def read_scores(path: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cid = row.get("case_id")
            if not cid:
                continue
            rows[cid] = {
                "score": float(row["score"]),
                "valid": str(row.get("valid", "")).strip().lower() in ("true", "1", "yes"),
                "split": row.get("split", ""),
            }
    return rows


def bootstrap_ci(deltas: list[float], iterations: int = 2000, seed: int = 0) -> dict[str, float]:
    """Paired bootstrap 95% CI on the mean of deltas. Deterministic via LCG seed."""
    n = len(deltas)
    if n == 0:
        return {"lower": 0.0, "upper": 0.0, "iterations": iterations, "n": 0}
    # Deterministic LCG so repeated runs on the same deltas give identical CIs.
    state = seed ^ (n * 2654435761) & 0xFFFFFFFFFFFFFFFF
    means: list[float] = []
    for _ in range(iterations):
        state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
        total = 0.0
        for _ in range(n):
            state = (state * 6364136223846793005 + 1442695040888963407) & 0xFFFFFFFFFFFFFFFF
            idx = (state >> 32) % n
            total += deltas[idx]
        means.append(total / n)
    means.sort()
    lo = means[int(0.025 * iterations)]
    hi = means[int(0.975 * iterations)]
    return {"lower": lo, "upper": hi, "iterations": iterations, "n": n}


def compare(incumbent_csv: Path, candidate_csv: Path, out_dir: Path, iterations: int = 2000) -> dict[str, Any]:
    inc = read_scores(incumbent_csv)
    cand = read_scores(candidate_csv)
    out_dir.mkdir(parents=True, exist_ok=True)

    case_ids = sorted(set(inc) & set(cand))
    only_inc = sorted(set(inc) - set(cand))
    only_cand = sorted(set(cand) - set(inc))

    rows: list[dict[str, Any]] = []
    deltas: list[float] = []
    wins = losses = ties = 0
    valid_inc_n = valid_cand_n = 0
    for cid in case_ids:
        i_score = inc[cid]["score"]
        c_score = cand[cid]["score"]
        delta = c_score - i_score
        deltas.append(delta)
        if delta > TIE_EPS:
            wins += 1
        elif delta < -TIE_EPS:
            losses += 1
        else:
            ties += 1
        if inc[cid]["valid"]:
            valid_inc_n += 1
        if cand[cid]["valid"]:
            valid_cand_n += 1
        rows.append(
            {
                "case_id": cid,
                "split": inc[cid]["split"],
                "incumbent": round(i_score, 6),
                "candidate": round(c_score, 6),
                "delta": round(delta, 6),
                "valid_inc": inc[cid]["valid"],
                "valid_cand": cand[cid]["valid"],
            }
        )

    n = len(case_ids)
    valid_rate_inc = valid_inc_n / n if n else 0.0
    valid_rate_cand = valid_cand_n / n if n else 0.0
    mean_delta = mean(deltas) if deltas else 0.0
    median_delta = median(deltas) if deltas else 0.0
    ci = bootstrap_ci(deltas, iterations=iterations)

    # Worst 10 regressions by delta (most negative first).
    regressions = sorted([r for r in rows if r["delta"] < -TIE_EPS], key=lambda r: r["delta"])[:10]

    with (out_dir / "paired_deltas.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["case_id", "split", "incumbent", "candidate", "delta", "valid_inc", "valid_cand"])
        writer.writeheader()
        writer.writerows(rows)

    summary = {
        "cases_paired": n,
        "incumbent_only": only_inc,
        "candidate_only": only_cand,
        "mean_delta": mean_delta,
        "median_delta": median_delta,
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "valid_rate_incumbent": valid_rate_inc,
        "valid_rate_candidate": valid_rate_cand,
        "valid_rate_delta": valid_rate_cand - valid_rate_inc,
        "bootstrap_ci_95": ci,
        "worst_regressions": regressions,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")

    lines = [
        "# Paired comparison: incumbent vs candidate",
        "",
        f"- cases paired: {n}",
        f"- mean delta: {mean_delta:+.6f}",
        f"- median delta: {median_delta:+.6f}",
        f"- wins / losses / ties: {wins} / {losses} / {ties}",
        f"- valid_rate incumbent: {valid_rate_inc:.4f}",
        f"- valid_rate candidate: {valid_rate_cand:.4f}",
        f"- valid_rate delta: {valid_rate_cand - valid_rate_inc:+.4f}",
        f"- bootstrap 95% CI: [{ci['lower']:+.6f}, {ci['upper']:+.6f}] (B={iterations}, n={n})",
        "",
        "## Worst regressions (candidate worse than incumbent)",
        "",
        "| case_id | incumbent | candidate | delta |",
        "|---|---:|---:|---:|",
    ]
    for r in regressions:
        lines.append(f"| {r['case_id']} | {r['incumbent']:.6f} | {r['candidate']:.6f} | {r['delta']:+.6f} |")
    if not regressions:
        lines.append("| _(none)_ | | | |")
    if only_inc or only_cand:
        lines.append("")
        lines.append(f"- incumbent-only case_ids: {len(only_inc)}")
        lines.append(f"- candidate-only case_ids: {len(only_cand)}")
    (out_dir / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired incumbent-vs-candidate comparison from two scores.csv files. No replay, no model calls.")
    parser.add_argument("--incumbent-scores", type=Path, required=True, help="evaluate.py scores.csv for the incumbent prompt.")
    parser.add_argument("--candidate-scores", type=Path, required=True, help="evaluate.py scores.csv for the candidate prompt.")
    parser.add_argument("--out", type=Path, required=True, help="Output directory for paired_deltas.csv, summary.json, summary.md.")
    parser.add_argument("--bootstrap-iterations", type=int, default=2000, help="Bootstrap resample count for the 95%% CI (default 2000).")
    args = parser.parse_args()
    summary = compare(args.incumbent_scores, args.candidate_scores, args.out, args.bootstrap_iterations)
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

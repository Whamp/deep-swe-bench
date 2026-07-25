#!/usr/bin/env python3
"""Paired analysis for a DeepSWE/pi run.

Continuous success metric is DeepSWE reward.json `partial`; binary `reward` is
reported but not used as the main signal because most long-horizon tasks are
partial-progress regimes.
"""
from __future__ import annotations

import argparse
import statistics as st
from collections import defaultdict

from harness import result_provenance, results_tree

try:
    from scipy.stats import wilcoxon
except ImportError:  # analysis still prints summaries without scipy
    wilcoxon = None


def load_results(
    model: str,
    thinking: str,
    configs: list[str],
) -> list[dict[str, object]]:
    """Load only provenance-compatible results for one comparison."""
    tree = results_tree.Tree.of(model, thinking)
    loaded: list[result_provenance.ComparisonResult] = []
    for cell in tree.cells(configs=configs):
        record = dict(
            result_provenance.read_result_record(
                cell.result,
                error_prefix="Comparison result provenance mismatch",
            )
        )
        loaded.append(
            result_provenance.ComparisonResult(
                result_path=cell.result,
                config=cell.config,
                task=cell.task,
                rep=cell.rep,
                record=record,
            )
        )
    result_provenance.require_compatible_comparison_results(
        model,
        thinking,
        configs,
        loaded,
    )
    return [selected.record for selected in loaded]


def _numeric_result_value(
    record: dict[str, object],
    field: str,
    fallback_field: str | None = None,
) -> int | float:
    """Read a numeric result field, treating a missing or null value as zero."""
    value = record.get(field)
    if value is None and fallback_field is not None:
        value = record.get(fallback_field)
    if value is None:
        return 0
    if not isinstance(value, int | float):
        raise TypeError(
            f"Comparison numeric result invalid: field={field!r}; "
            f"recorded={value!r}"
        )
    return value


def median(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def mean(xs):
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def fmt(x, digits=3):
    if x is None:
        return "-"
    if isinstance(x, int):
        return str(x)
    return f"{x:.{digits}f}"


def holm(pvals: list[tuple[str, float]]) -> dict[str, float]:
    m = len(pvals)
    out = {}
    prev = 0.0
    for i, (name, p) in enumerate(sorted(pvals, key=lambda x: x[1])):
        adj = min(1.0, max(prev, p * (m - i)))
        out[name] = adj
        prev = adj
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--thinking", required=True)
    ap.add_argument("--comparison", required=True, help="label for the output analysis")
    ap.add_argument("--configs", required=True, help="baseline,ponytail-full")
    args = ap.parse_args()
    configs = [a.strip() for a in args.configs.split(",")]
    baseline = configs[0]
    rows = [r for r in load_results(args.model, args.thinking, configs) if r.get("config") in configs]
    if not rows:
        raise SystemExit(f"no results found for {args.model}/{args.thinking}/{args.configs}")

    print(f"# comparison {args.comparison} ({args.model} / {args.thinking})\n")
    print("## config summary")
    print("config,n,mean_partial,median_tokens,median_advisor_tokens,median_om_worker_tokens,median_combined_tokens,median_cost,median_advisor_cost,median_om_worker_cost,median_combined_cost,median_patch_bytes,solved,solved_rate,timeout_rate")
    by_config = defaultdict(list)
    for r in rows:
        by_config[r["config"]].append(r)
    for config in configs:
        rs = by_config[config]
        if not rs:
            continue
        print(",".join([
            config,
            str(len(rs)),
            fmt(mean([r.get("reward_partial") for r in rs])),
            fmt(median([r.get("total_tokens") for r in rs]), 0),
            fmt(median([r.get("advisor_total_tokens") for r in rs]), 0),
            fmt(median([r.get("om_worker_total_tokens") for r in rs]), 0),
            fmt(median([r.get("combined_total_tokens", r.get("total_tokens")) for r in rs]), 0),
            fmt(median([r.get("cost_usd") for r in rs]), 4),
            fmt(median([r.get("advisor_cost_usd") for r in rs]), 4),
            fmt(median([r.get("om_worker_cost_usd") for r in rs]), 4),
            fmt(median([r.get("combined_cost_usd", r.get("cost_usd")) for r in rs]), 4),
            fmt(median([r.get("patch_bytes") for r in rs]), 0),
            f"{sum(1 for r in rs if r.get('reward_binary') == 1)}/{len(rs)}",
            fmt(mean([1 if r.get("reward_binary") == 1 else 0 for r in rs])),
            fmt(mean([1 if r.get("agent_timed_out") else 0 for r in rs])),
        ]))

    print("\n## paired deltas (other - baseline, matched by task+rep)")
    print("config,n,delta_partial_mean,delta_tokens_median,delta_om_worker_tokens_median,delta_combined_tokens_median,delta_cost_median,delta_advisor_cost_median,delta_om_worker_cost_median,delta_combined_cost_median,delta_patch_bytes_median,wilcoxon_p,wilcoxon_p_holm")
    keyed = {(r["task"], r.get("rep", 0), r["config"]): r for r in rows}
    pvals = []
    deltas_by_config = {}
    for config in configs[1:]:
        pairs = []
        for (task, rep, c), b in keyed.items():
            if c != baseline:
                continue
            o = keyed.get((task, rep, config))
            if o:
                pairs.append((b, o))
        dp = [
            _numeric_result_value(o, "reward_partial")
            - _numeric_result_value(b, "reward_partial")
            for b, o in pairs
        ]
        dt = [
            _numeric_result_value(o, "total_tokens")
            - _numeric_result_value(b, "total_tokens")
            for b, o in pairs
        ]
        dowt = [
            _numeric_result_value(o, "om_worker_total_tokens")
            - _numeric_result_value(b, "om_worker_total_tokens")
            for b, o in pairs
        ]
        dct = [
            _numeric_result_value(
                o,
                "combined_total_tokens",
                "total_tokens",
            )
            - _numeric_result_value(
                b,
                "combined_total_tokens",
                "total_tokens",
            )
            for b, o in pairs
        ]
        dc = [
            _numeric_result_value(o, "cost_usd")
            - _numeric_result_value(b, "cost_usd")
            for b, o in pairs
        ]
        dac = [
            _numeric_result_value(o, "advisor_cost_usd")
            - _numeric_result_value(b, "advisor_cost_usd")
            for b, o in pairs
        ]
        dowc = [
            _numeric_result_value(o, "om_worker_cost_usd")
            - _numeric_result_value(b, "om_worker_cost_usd")
            for b, o in pairs
        ]
        dcc = [
            _numeric_result_value(o, "combined_cost_usd", "cost_usd")
            - _numeric_result_value(b, "combined_cost_usd", "cost_usd")
            for b, o in pairs
        ]
        db = [
            _numeric_result_value(o, "patch_bytes")
            - _numeric_result_value(b, "patch_bytes")
            for b, o in pairs
        ]
        p = None
        if wilcoxon and len(dp) >= 2 and any(x != 0 for x in dp):
            try:
                p = float(wilcoxon(dp, zero_method="wilcox").pvalue)
                pvals.append((config, p))
            except ValueError:
                p = None
        deltas_by_config[config] = (len(pairs), dp, dt, dowt, dct, dc, dac, dowc, dcc, db, p)
    adj = holm(pvals)
    for config, (n, dp, dt, dowt, dct, dc, dac, dowc, dcc, db, p) in deltas_by_config.items():
        print(",".join([config, str(n), fmt(mean(dp)), fmt(median(dt), 0), fmt(median(dowt), 0), fmt(median(dct), 0), fmt(median(dc), 4), fmt(median(dac), 4), fmt(median(dowc), 4), fmt(median(dcc), 4), fmt(median(db), 0), fmt(p), fmt(adj.get(config))]))

    print("\n## per-task rows")
    print("task,rep," + ",".join(f"{a}_partial,{a}_tokens,{a}_advisor_tokens,{a}_om_worker_tokens,{a}_combined_tokens,{a}_cost,{a}_advisor_cost,{a}_om_worker_cost,{a}_combined_cost,{a}_patch" for a in configs))
    keys = sorted({(r["task"], r.get("rep", 0)) for r in rows})
    for task, rep in keys:
        vals = [str(task), str(rep)]
        for config in configs:
            r = keyed.get((task, rep, config), {})
            vals += [fmt(r.get("reward_partial")), str(r.get("total_tokens", "")), str(r.get("advisor_total_tokens", "")), str(r.get("om_worker_total_tokens", "")), str(r.get("combined_total_tokens", r.get("total_tokens", ""))), fmt(r.get("cost_usd"), 4), fmt(r.get("advisor_cost_usd"), 4), fmt(r.get("om_worker_cost_usd"), 4), fmt(r.get("combined_cost_usd", r.get("cost_usd")), 4), str(r.get("patch_bytes", ""))]
        print(",".join(vals))


if __name__ == "__main__":
    main()

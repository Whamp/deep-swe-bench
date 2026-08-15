"""Render the stock-Pi sequence-aware trajectory analysis as self-contained HTML."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

ANALYSIS_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ANALYSIS_DIR / "artifacts"
OUTPUT_PATH = ANALYSIS_DIR / "index.html"


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _percent(numerator: int, denominator: int) -> str:
    return f"{100 * numerator / denominator:.1f}%"


def _metric(value: float, *, signed: bool = False) -> str:
    return f"{value:+.3f}" if signed else f"{value:.3f}"


def render_trajectory_process_report() -> str:
    """Build the report from committed stock-Pi baseline artifacts."""
    sessions = _load("session_schema_audit.json")
    features = _load("feature_summary.json")
    evaluation = _load("held_out_task_evaluation.json")
    forest = _load("random_forest_evaluation.json")
    task_effects = _load("task_controlled_feature_effects.json")
    manifest = _load("baseline_manifest.json")

    dataset = manifest["dataset"]
    metrics = evaluation["binary_metrics"]
    deltas = evaluation["specification_minus_length"]
    support = sessions["semantic_feature_support"]
    forest_metrics = forest["binary_metrics"]
    forest_deltas = forest["specification_minus_length"]
    forest_test_interval = forest_deltas["test_flow"][
        "task_bootstrap_log_loss_delta_95pct"
    ]
    forest_clean = forest["cohort_sensitivities"]["certain_first_source_mutation"]
    forest_clean_metrics = forest_clean["evaluation"]["binary_metrics"]
    forest_clean_delta = forest_clean["evaluation"]["specification_minus_length"][
        "test_flow"
    ]
    forest_rows = "".join(
        _metric_row(forest_metrics, key, label)
        for key, label in (
            ("length", "Forest: length + controls"),
            ("test_flow", "Forest: test and phase flow"),
            ("all_process", "Forest: compact process features"),
            ("all_measured", "Forest: all 91 measured features"),
        )
    )
    forest_delta_rows = "".join(
        _delta_row(forest_deltas, key, label)
        for key, label in (
            ("test_flow", "Test and phase flow"),
            ("all_process", "Compact process features"),
            ("all_measured", "All 91 measured features"),
        )
    )
    oob_rows = "".join(
        f"<tr><td>{_escape(label)}</td><td>{forest['oob_diagnostics']['mean_across_outer_training_partitions'][key]['log_loss']:.3f}</td>"
        f"<td>{forest_metrics[key]['log_loss']:.3f}</td></tr>"
        for key, label in (
            ("length", "Length + controls"),
            ("test_flow", "Test and phase flow"),
            ("all_process", "Compact process features"),
            ("all_measured", "All 91 measured features"),
        )
    )
    permutation_rows = "".join(
        _permutation_row(forest["permutation_family_importance"], key, label)
        for key, label in (
            ("length", "Length"),
            ("aggregate_process", "Aggregate process"),
            ("opening", "Opening behavior"),
            ("mutation_style", "Edit/write style"),
            ("test_flow", "Test and phase flow"),
            ("additional_sequence", "Additional sequence measures"),
        )
    )

    metric_rows = "".join(
        _metric_row(metrics, key, label)
        for key, label in (
            ("prevalence", "Training-fold success rate"),
            ("length", "Length + controls"),
            ("process", "Original aggregate counts"),
            ("opening", "Opening behavior"),
            ("mutation_style", "Edit/write style"),
            ("test_flow", "Test and phase flow"),
            ("sequence", "All ordered features"),
            ("all_process", "Aggregate + ordered features"),
        )
    )
    delta_rows = "".join(
        _delta_row(deltas, key, label)
        for key, label in (
            ("process", "Original aggregate counts"),
            ("opening", "Opening behavior"),
            ("mutation_style", "Edit/write style"),
            ("test_flow", "Test and phase flow"),
            ("sequence", "All ordered features"),
            ("all_process", "Aggregate + ordered features"),
        )
    )
    task_effect_rows = "".join(
        _task_effect_row(task_effects, key, label)
        for key, label in (
            (
                "tool_calls_before_first_source_mutation",
                "Calls before first source change",
            ),
            ("reads_before_first_source_mutation", "Reads before first source change"),
            (
                "unique_paths_read_before_first_source_mutation",
                "Unique paths read before first source change",
            ),
            (
                "first_source_mutation_call_fraction",
                "Share of trajectory before first source change",
            ),
            ("first_source_mutation_is_write", "First source change used write"),
            ("source_edit_calls", "Source edit calls"),
            ("source_write_calls", "Source write calls"),
            ("tests_after_first_source_mutation", "Tests after first source change"),
            (
                "has_passing_test_after_final_source_mutation",
                "Passing test after final source change",
            ),
            (
                "implementation_to_validation_transitions",
                "Implementation→validation transitions",
            ),
            (
                "validation_to_implementation_backtracks",
                "Validation→implementation cycles",
            ),
        )
    )
    model_rows = "".join(
        f"<tr><td><code>{_escape(row['model'])}</code></td><td>{row['reps']}</td>"
        f"<td>{row['tasks']}</td><td>{row['successes']}</td><td>{row['failures']}</td></tr>"
        for row in features["model_support"]
    )
    sensitivity_rows = "".join(
        _model_sensitivity_row(model, item)
        for model, item in evaluation["model_sensitivities"].items()
    )
    task_rows = "".join(
        f"<tr><td><code>{_escape(row['task'])}</code></td><td>{row['reps']}</td>"
        f"<td>{row['successes']}</td><td>{_percent(row['successes'], row['reps'])}</td></tr>"
        for row in features["by_task"]
    )

    first_write_successes = features["by_outcome"]["success"][
        "first_source_mutation_is_write"
    ]["nonzero"]
    first_write_failures = features["by_outcome"]["failure"][
        "first_source_mutation_is_write"
    ]["nonzero"]
    first_source_successes = features["by_outcome"]["success"][
        "has_successful_source_mutation"
    ]["nonzero"]
    first_source_failures = features["by_outcome"]["failure"][
        "has_successful_source_mutation"
    ]["nonzero"]
    first_edit_successes = first_source_successes - first_write_successes
    first_edit_failures = first_source_failures - first_write_failures

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stock-Pi sequence-aware trajectory analysis</title>
<style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}} *{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,#183e65,var(--bg) 42%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}} main{{max-width:1240px;margin:auto;padding:36px 22px 70px}} h1{{font-size:clamp(38px,6vw,72px);line-height:.94;letter-spacing:-.055em;margin:12px 0 18px}} h2{{margin:36px 0 12px;font-size:28px}} h3{{margin:18px 0 8px}} p,li{{color:#dbe7fb}} code{{color:#bfdbfe}} a{{color:#93c5fd}} .hero,.card,.callout{{background:rgba(15,29,49,.9);border:1px solid var(--line);border-radius:24px;padding:24px}} .hero{{padding:34px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.95) 48%,rgba(251,191,36,.09))}} .kicker{{color:var(--blue);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}} .pills{{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}} .pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728}} .good{{color:#b9f8da;border-color:rgba(52,211,153,.5);background:rgba(52,211,153,.12)}} .bad{{color:#fecdd3;border-color:rgba(251,113,133,.5);background:rgba(251,113,133,.12)}} .caution{{color:#fde68a;border-color:rgba(251,191,36,.55);background:rgba(251,191,36,.12)}} .neutral{{color:#bfdbfe;border-color:rgba(96,165,250,.45);background:rgba(96,165,250,.12)}} .stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0}} .stat{{background:rgba(15,29,49,.88);border:1px solid var(--line);border-radius:20px;padding:18px}} .stat b{{display:block;font-size:30px;line-height:1.05;letter-spacing:-.04em}} .stat span,.muted,.src{{color:var(--muted);font-size:12px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .callout{{margin:18px 0}} .callout.bad{{border-left:5px solid var(--red)}} .callout.caution{{border-left:5px solid var(--amber)}} .callout.good{{border-left:5px solid var(--green)}} .scroll{{overflow:auto}} table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68)}} th,td{{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:#bfdbfe;background:#0d1a2d}} tr:last-child td{{border-bottom:0}} @media(max-width:760px){{.stats,.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">DeepSWE retrospective · stock Pi only · nonlinear follow-up</div><h1>Forests improve the baseline.<br>Process signal still does not transfer.</h1><p>A random forest captures modest nonlinear structure in trajectory length and basic controls. Adding test flow, compact process features, or all 91 measured features makes predictions worse on wholly unseen tasks. On the clean-boundary cohort, test flow is tied with length.</p><div class="pills"><span class="pill good">forest length loss {forest_metrics["length"]["log_loss"]:.3f}</span><span class="pill bad">all-measured Δ {forest_deltas["all_measured"]["log_loss"]:+.3f}</span><span class="pill caution">test-flow Δ {forest_deltas["test_flow"]["log_loss"]:+.3f}</span><span class="pill neutral">clean test-flow Δ {forest_clean_delta["log_loss"]:+.3f}</span></div><div class="src">{dataset["modeling_reps"]} direct Pi sessions · {dataset["task_count"]} held-out tasks · <a href="report.md">full methods and results</a></div></section>
<div class="stats"><div class="stat"><b>{support["reps_with_source_mutations"]}</b><span>attempts with an observed source change</span></div><div class="stat"><b>{support["reps_with_write_as_first_source_mutation"]}</b><span>used write for the first source change</span></div><div class="stat"><b>{support["reps_with_uncertain_first_source_mutation"]}</b><span>possible earlier shell mutation</span></div><div class="stat"><b>{support["reps_with_observable_tests"]}</b><span>attempts with an observed test</span></div></div>
<section class="callout bad"><h2>Main result</h2><p>The forest length baseline reaches <b>{forest_metrics["length"]["log_loss"]:.3f}</b> log loss. Test flow worsens it by <b>{forest_deltas["test_flow"]["log_loss"]:+.3f}</b> with a task-bootstrap interval of <b>{forest_test_interval["low"]:+.3f} to {forest_test_interval["high"]:+.3f}</b>. All 91 measured features worsen it by <b>{forest_deltas["all_measured"]["log_loss"]:+.3f}</b>. The nonlinear model does not recover transferable process signal.</p></section>
<h2>Random-forest held-out-task comparison</h2><div class="scroll"><table><thead><tr><th>Predictors</th><th>Log loss ↓</th><th>Macro-task loss ↓</th><th>Brier ↓</th><th>AUROC ↑</th><th>Average precision ↑</th></tr></thead><tbody>{forest_rows}</tbody></table></div>
<h2>Forest difference from length-only</h2><div class="scroll"><table><thead><tr><th>Added feature family</th><th>Log-loss difference</th><th>95% task-bootstrap interval</th><th>AUROC difference</th><th>Average-precision difference</th></tr></thead><tbody>{forest_delta_rows}</tbody></table></div>
<section class="callout caution"><h2>OOB looks positive—and is wrong for this question</h2><p>Out-of-bag validation leaves individual attempts out, not whole tasks. It makes both process forests look better than length. When entire tasks are unseen, the ordering reverses.</p><div class="scroll"><table><thead><tr><th>Predictors</th><th>Mean OOB log loss</th><th>Task-held-out log loss</th></tr></thead><tbody>{oob_rows}</tbody></table></div></section>
<h2>Clean-boundary forest sensitivity</h2><p>After removing uncertain shell boundaries and no-source-change attempts, {forest_clean["reps"]} attempts remain. Test flow is tied with length: {forest_clean_metrics["length"]["log_loss"]:.3f} versus {forest_clean_metrics["test_flow"]["log_loss"]:.3f}, with log-loss difference {forest_clean_delta["log_loss"]:+.3f}. The all-measured forest reaches {forest_clean_metrics["all_measured"]["log_loss"]:.3f}.</p>
<h2>Held-out family permutation</h2><p class="muted">Positive means prediction worsens when the family is shuffled and therefore suggests useful held-out dependence. Negative means shuffling helps.</p><div class="scroll"><table><thead><tr><th>Family</th><th>Log-loss change after shuffle</th><th>95% task-bootstrap interval</th></tr></thead><tbody>{permutation_rows}</tbody></table></div>
<h2>Linear held-out-task comparison</h2><div class="scroll"><table><thead><tr><th>Predictors</th><th>Log loss ↓</th><th>Macro-task loss ↓</th><th>Brier ↓</th><th>AUROC ↑</th><th>Average precision ↑</th></tr></thead><tbody>{metric_rows}</tbody></table></div>
<h2>Linear difference from length-only</h2><div class="scroll"><table><thead><tr><th>Added feature family</th><th>Log-loss difference</th><th>95% task-bootstrap interval</th><th>AUROC difference</th><th>Average-precision difference</th></tr></thead><tbody>{delta_rows}</tbody></table></div>
<section class="callout good"><h2>What the ordering data does show</h2><p>Within the same task, successful attempts reach their first source change earlier as a share of the total trajectory. They are also more likely to finish with a passing test after the final source change and to make more implementation→validation and validation→implementation cycles. In other words, backtracking between code and tests is often productive iteration, not failure.</p></section>
<h2>Within-task descriptive effects</h2><p class="muted">Positive means higher in successful attempts. Standardized differences compare success and failure inside each contested task; intervals bootstrap whole tasks.</p><div class="scroll"><table><thead><tr><th>Measure</th><th>Mean raw difference</th><th>Mean standardized difference</th><th>95% task-bootstrap interval</th><th>Tasks higher in success</th></tr></thead><tbody>{task_effect_rows}</tbody></table></div>
<h2><code>edit</code> versus <code>write</code></h2><div class="grid"><section class="card"><h3>First source change: edit</h3><p><b>{first_edit_successes} successes / {first_edit_successes + first_edit_failures} attempts</b> ({_percent(first_edit_successes, first_edit_successes + first_edit_failures)}).</p><p>Across all runs, structured source edits were used 8,728 times.</p></section><section class="card"><h3>First source change: write</h3><p><b>{first_write_successes} successes / {first_write_successes + first_write_failures} attempts</b> ({_percent(first_write_successes, first_write_successes + first_write_failures)}).</p><p>Across all runs, whole-file source writes were used 1,094 times.</p></section></div><p>The raw first-action gap is only 1.9 percentage points, and the within-task interval includes zero. The data does not support calling either tool intrinsically better. Target and sequence matter more: 574 attempts wrote and later edited the same path.</p>
<h2>Model sensitivity: test/phase flow</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Status</th><th>Length log loss</th><th>Test-flow log loss</th><th>Difference</th><th>95% task-bootstrap interval</th></tr></thead><tbody>{sensitivity_rows}</tbody></table></div>
<h2>Model coverage</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Attempts</th><th>Tasks</th><th>Successes</th><th>Failures</th></tr></thead><tbody>{model_rows}</tbody></table></div>
<section class="callout caution"><h2>Important limits</h2><ul><li>Only 30 attempts ran a test before the first source change, so that specific behavior is too rare to judge.</li><li>Sixty-two attempts contain a possible shell mutation before the structured boundary. Excluding all uncertain/no-source cases leaves 925 attempts and does not create a clear test-flow improvement.</li><li>A successful test command is not proof that the relevant hidden or feature test passed.</li><li>The combined sequence models have many correlated measurements and overfit badly; the grouped comparisons are the reliable view.</li><li>These associations do not prove that forcing an agent to read more or test more would improve it.</li></ul></section>
<h2>All {features["tasks"]} tasks</h2><div class="scroll"><table><thead><tr><th>Task</th><th>Attempts</th><th>Successes</th><th>Success rate</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<section class="callout good"><h2>Conclusion</h2><p>The forest confirms that there is modest nonlinear signal in length and basic controls, but not in the current process counters. Successful runs still show meaningful behavioral differences—earlier proportional commitment and more validation cycles—but those patterns do not generalize into better unseen-task predictions. Manual trajectory labels are the next useful source of information.</p></section>
<p class="src">Evidence: <a href="artifacts/random_forest_evaluation.json">random forest</a> · <a href="artifacts/baseline_features.csv">features</a> · <a href="artifacts/task_controlled_feature_effects.json">within-task effects</a> · <a href="artifacts/held_out_task_evaluation.json">linear evaluation</a> · <a href="trajectory_analysis_research.md">research basis</a> · <a href="artifacts/baseline_manifest.json">manifest</a></p>
</main></body></html>"""


def _load(name: str) -> dict[str, Any]:
    return json.loads((ARTIFACTS_DIR / name).read_text())


def _metric_row(metrics: dict[str, Any], key: str, label: str) -> str:
    row = metrics[key]
    return (
        f"<tr><td>{_escape(label)}</td><td>{row['log_loss']:.3f}</td>"
        f"<td>{row['macro_task_log_loss']:.3f}</td><td>{row['brier']:.3f}</td>"
        f"<td>{row['auroc']:.3f}</td><td>{row['average_precision']:.3f}</td></tr>"
    )


def _delta_row(deltas: dict[str, Any], key: str, label: str) -> str:
    row = deltas[key]
    interval = row["task_bootstrap_log_loss_delta_95pct"]
    return (
        f"<tr><td>{_escape(label)}</td><td>{row['log_loss']:+.3f}</td>"
        f"<td>{interval['low']:+.3f} to {interval['high']:+.3f}</td>"
        f"<td>{row['auroc']:+.3f}</td><td>{row['average_precision']:+.3f}</td></tr>"
    )


def _permutation_row(importance: dict[str, Any], key: str, label: str) -> str:
    delta = importance[key]["permuted_minus_unpermuted"]
    interval = delta["task_bootstrap_log_loss_delta_95pct"]
    return (
        f"<tr><td>{_escape(label)}</td><td>{delta['log_loss']:+.3f}</td>"
        f"<td>{interval['low']:+.3f} to {interval['high']:+.3f}</td></tr>"
    )


def _task_effect_row(effects: dict[str, Any], key: str, label: str) -> str:
    row = effects[key]
    interval = row["task_bootstrap_standardized_mean_95pct"]
    raw = row["mean_success_minus_failure"]
    standardized = row["mean_within_task_standardized_delta"]
    return (
        f"<tr><td>{_escape(label)}</td><td>{raw:+.3f}</td>"
        f"<td>{standardized:+.3f}</td>"
        f"<td>{interval['low']:+.3f} to {interval['high']:+.3f}</td>"
        f"<td>{100 * row['fraction_tasks_higher_in_success']:.1f}%</td></tr>"
    )


def _model_sensitivity_row(model: str, item: dict[str, Any]) -> str:
    if item["status"] != "evaluated":
        return (
            f"<tr><td><code>{_escape(model)}</code></td>"
            f"<td><span class='tag caution'>too little data: {item['reps']} attempts / "
            f"{item['tasks']} tasks</span></td><td>—</td><td>—</td><td>—</td><td>—</td></tr>"
        )
    evaluation = item["evaluation"]
    metrics = evaluation["binary_metrics"]
    delta = evaluation["specification_minus_length"]["test_flow"]
    interval = delta["task_bootstrap_log_loss_delta_95pct"]
    return (
        f"<tr><td><code>{_escape(model)}</code></td><td>evaluated</td>"
        f"<td>{metrics['length']['log_loss']:.3f}</td>"
        f"<td>{metrics['test_flow']['log_loss']:.3f}</td>"
        f"<td>{delta['log_loss']:+.3f}</td>"
        f"<td>{interval['low']:+.3f} to {interval['high']:+.3f}</td></tr>"
    )


def main() -> None:
    """Write the rendered report beside the Markdown source."""
    OUTPUT_PATH.write_text(render_trajectory_process_report())
    print(f"wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

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
    task_effects = _load("task_controlled_feature_effects.json")
    manifest = _load("baseline_manifest.json")

    dataset = manifest["dataset"]
    metrics = evaluation["binary_metrics"]
    deltas = evaluation["specification_minus_length"]
    test_delta = deltas["test_flow"]
    test_interval = test_delta["task_bootstrap_log_loss_delta_95pct"]
    clean = evaluation["cohort_sensitivities"]["certain_first_source_mutation"]
    clean_test_delta = clean["evaluation"]["specification_minus_length"]["test_flow"]
    support = sessions["semantic_feature_support"]

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
<section class="hero"><div class="kicker">DeepSWE retrospective · stock Pi only · sequence-aware follow-up</div><h1>Ordering explains behavior better.<br>It still does not improve prediction.</h1><p>This follow-up measures what happened before the first source change, distinguishes <code>edit</code> from <code>write</code>, and tracks implementation/test cycles. Test flow comes closest to helping, but it remains tied with the length-only model.</p><div class="pills"><span class="pill good">{dataset["modeling_reps"]} direct Pi sessions</span><span class="pill neutral">{dataset["task_count"]} held-out tasks</span><span class="pill caution">test-flow log loss Δ {test_delta["log_loss"]:+.3f}</span><span class="pill neutral">clean-boundary Δ {clean_test_delta["log_loss"]:+.3f}</span></div><div class="src">Research basis: <a href="trajectory_analysis_research.md">trajectory-analysis methods</a> · Full methods: <a href="report.md">report.md</a></div></section>
<div class="stats"><div class="stat"><b>{support["reps_with_source_mutations"]}</b><span>attempts with an observed source change</span></div><div class="stat"><b>{support["reps_with_write_as_first_source_mutation"]}</b><span>used write for the first source change</span></div><div class="stat"><b>{support["reps_with_uncertain_first_source_mutation"]}</b><span>possible earlier shell mutation</span></div><div class="stat"><b>{support["reps_with_observable_tests"]}</b><span>attempts with an observed test</span></div></div>
<section class="callout caution"><h2>Main result</h2><p>The test/phase-flow model changes log loss from <b>{metrics["length"]["log_loss"]:.3f}</b> to <b>{metrics["test_flow"]["log_loss"]:.3f}</b>. Its task-bootstrap interval for the difference is <b>{test_interval["low"]:+.3f} to {test_interval["high"]:+.3f}</b>, which includes no difference. Opening behavior, edit/write style, and the combined sequence models all perform worse.</p></section>
<h2>Held-out-task comparison</h2><div class="scroll"><table><thead><tr><th>Predictors</th><th>Log loss ↓</th><th>Macro-task loss ↓</th><th>Brier ↓</th><th>AUROC ↑</th><th>Average precision ↑</th></tr></thead><tbody>{metric_rows}</tbody></table></div>
<h2>Difference from length-only</h2><div class="scroll"><table><thead><tr><th>Added feature family</th><th>Log-loss difference</th><th>95% task-bootstrap interval</th><th>AUROC difference</th><th>Average-precision difference</th></tr></thead><tbody>{delta_rows}</tbody></table></div>
<section class="callout good"><h2>What the ordering data does show</h2><p>Within the same task, successful attempts reach their first source change earlier as a share of the total trajectory. They are also more likely to finish with a passing test after the final source change and to make more implementation→validation and validation→implementation cycles. In other words, backtracking between code and tests is often productive iteration, not failure.</p></section>
<h2>Within-task descriptive effects</h2><p class="muted">Positive means higher in successful attempts. Standardized differences compare success and failure inside each contested task; intervals bootstrap whole tasks.</p><div class="scroll"><table><thead><tr><th>Measure</th><th>Mean raw difference</th><th>Mean standardized difference</th><th>95% task-bootstrap interval</th><th>Tasks higher in success</th></tr></thead><tbody>{task_effect_rows}</tbody></table></div>
<h2><code>edit</code> versus <code>write</code></h2><div class="grid"><section class="card"><h3>First source change: edit</h3><p><b>{first_edit_successes} successes / {first_edit_successes + first_edit_failures} attempts</b> ({_percent(first_edit_successes, first_edit_successes + first_edit_failures)}).</p><p>Across all runs, structured source edits were used 8,728 times.</p></section><section class="card"><h3>First source change: write</h3><p><b>{first_write_successes} successes / {first_write_successes + first_write_failures} attempts</b> ({_percent(first_write_successes, first_write_successes + first_write_failures)}).</p><p>Across all runs, whole-file source writes were used 1,094 times.</p></section></div><p>The raw first-action gap is only 1.9 percentage points, and the within-task interval includes zero. The data does not support calling either tool intrinsically better. Target and sequence matter more: 574 attempts wrote and later edited the same path.</p>
<h2>Model sensitivity: test/phase flow</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Status</th><th>Length log loss</th><th>Test-flow log loss</th><th>Difference</th><th>95% task-bootstrap interval</th></tr></thead><tbody>{sensitivity_rows}</tbody></table></div>
<h2>Model coverage</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Attempts</th><th>Tasks</th><th>Successes</th><th>Failures</th></tr></thead><tbody>{model_rows}</tbody></table></div>
<section class="callout caution"><h2>Important limits</h2><ul><li>Only 30 attempts ran a test before the first source change, so that specific behavior is too rare to judge.</li><li>Sixty-two attempts contain a possible shell mutation before the structured boundary. Excluding all uncertain/no-source cases leaves 925 attempts and does not create a clear test-flow improvement.</li><li>A successful test command is not proof that the relevant hidden or feature test passed.</li><li>The combined sequence models have many correlated measurements and overfit badly; the grouped comparisons are the reliable view.</li><li>These associations do not prove that forcing an agent to read more or test more would improve it.</li></ul></section>
<h2>All {features["tasks"]} tasks</h2><div class="scroll"><table><thead><tr><th>Task</th><th>Attempts</th><th>Successes</th><th>Success rate</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<section class="callout good"><h2>Conclusion</h2><p>The simple “too much exploration before acting” hypothesis is not supported. Successful runs often read more in absolute terms, but they commit earlier relative to their total trajectory and then perform more code/test cycles. Test discipline looks behaviorally meaningful, yet the current deterministic features still do not predict held-out-task success better than length and basic controls.</p></section>
<p class="src">Evidence: <a href="artifacts/baseline_features.csv">features</a> · <a href="artifacts/task_controlled_feature_effects.json">within-task effects</a> · <a href="artifacts/held_out_task_evaluation.json">evaluation</a> · <a href="artifacts/baseline_manifest.json">manifest</a></p>
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

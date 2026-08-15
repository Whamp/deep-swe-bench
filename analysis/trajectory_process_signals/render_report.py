"""Render the stock-Pi baseline trajectory analysis as self-contained HTML."""

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
    schema = json.loads((ARTIFACTS_DIR / "schema_audit.json").read_text())
    sessions = json.loads((ARTIFACTS_DIR / "session_schema_audit.json").read_text())
    features = json.loads((ARTIFACTS_DIR / "feature_summary.json").read_text())
    evaluation = json.loads(
        (ARTIFACTS_DIR / "held_out_task_evaluation.json").read_text()
    )
    manifest = json.loads((ARTIFACTS_DIR / "baseline_manifest.json").read_text())

    dataset = manifest["dataset"]
    metrics = evaluation["binary_metrics"]
    delta = evaluation["process_minus_length"]
    bootstrap = delta["task_bootstrap_log_loss_delta_95pct"]
    dispositions = schema["primary_disposition_counts"]
    support = sessions["semantic_feature_support"]
    modeling_reps = sessions["modeling_reps"]
    session_mib = dataset["session_bytes"] / (1024 * 1024)

    task_rows = "".join(
        f"<tr><td><code>{_escape(row['task'])}</code></td>"
        f"<td>{row['reps']}</td><td>{row['successes']}</td>"
        f"<td>{_percent(row['successes'], row['reps'])}</td></tr>"
        for row in features["by_task"]
    )
    model_rows = "".join(
        f"<tr><td><code>{_escape(row['model'])}</code></td><td>{row['reps']}</td>"
        f"<td>{row['tasks']}</td><td>{row['successes']}</td><td>{row['failures']}</td>"
        f"<td>{_escape(', '.join(row['thinking_levels']))}</td></tr>"
        for row in features["model_support"]
    )
    sensitivity_rows = "".join(
        _model_sensitivity_row(model, item)
        for model, item in evaluation["model_sensitivities"].items()
    )
    config_rows = "".join(
        f"<tr><td><code>{_escape(row['config'])}</code></td><td>{row['reps']}</td>"
        f"<td>{row['tasks']}</td><td>{row['successes']}</td>"
        f"<td>{_percent(row['reps_with_observable_tests'], row['reps'])}</td></tr>"
        for row in features["config_semantic_support"]
    )
    metric_rows = "".join(
        f"<tr><td>{_escape(label)}</td>"
        f"<td>{_metric(metrics[key]['log_loss'])}</td>"
        f"<td>{_metric(metrics[key]['macro_task_log_loss'])}</td>"
        f"<td>{_metric(metrics[key]['brier'])}</td>"
        f"<td>{_metric(metrics[key]['auroc'])}</td>"
        f"<td>{_metric(metrics[key]['average_precision'])}</td></tr>"
        for key, label in (
            ("prevalence", "Training-fold success rate"),
            ("length", "Length + controls"),
            ("process", "Length + process + controls"),
        )
    )
    feature_rows = "".join(
        _feature_row(features, name, label)
        for name, label in (
            ("total_tokens", "Mean total tokens"),
            ("turns", "Mean turns"),
            ("repeated_normalized_tool_actions", "Repeated normalized actions"),
            ("repeated_read_targets", "Repeated read targets"),
            ("direct_mutation_calls", "Direct mutations"),
            ("failed_direct_mutation_calls", "Failed direct mutations"),
            ("strategy_reset_turns", "Strategy-reset turns"),
            ("test_failure_to_pass_transitions", "Failure→pass transitions"),
        )
    )

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Stock-Pi baseline trajectory analysis</title>
<style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,#183e65,var(--bg) 42%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}} main{{max-width:1240px;margin:auto;padding:36px 22px 70px}} h1{{font-size:clamp(38px,6vw,72px);line-height:.94;letter-spacing:-.055em;margin:12px 0 18px}} h2{{margin:36px 0 12px;font-size:28px}} h3{{margin:22px 0 8px}} p,li{{color:#dbe7fb}} code{{color:#bfdbfe}} a{{color:#93c5fd}} .hero,.card,.callout{{background:rgba(15,29,49,.9);border:1px solid var(--line);border-radius:24px;padding:24px}} .hero{{padding:34px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.95) 48%,rgba(251,191,36,.09))}} .kicker{{color:var(--blue);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}} .pills{{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}} .pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728}} .good{{color:#b9f8da;border-color:rgba(52,211,153,.5);background:rgba(52,211,153,.12)}} .bad{{color:#fecdd3;border-color:rgba(251,113,133,.5);background:rgba(251,113,133,.12)}} .caution{{color:#fde68a;border-color:rgba(251,191,36,.55);background:rgba(251,191,36,.12)}} .neutral{{color:#bfdbfe;border-color:rgba(96,165,250,.45);background:rgba(96,165,250,.12)}} .stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0}} .stat{{background:rgba(15,29,49,.88);border:1px solid var(--line);border-radius:20px;padding:18px}} .stat b{{display:block;font-size:30px;line-height:1.05;letter-spacing:-.04em}} .stat span,.muted,.src{{color:var(--muted);font-size:12px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .callout{{margin:18px 0}} .callout.bad{{border-left:5px solid var(--red)}} .callout.caution{{border-left:5px solid var(--amber)}} .callout.good{{border-left:5px solid var(--green)}} .scroll{{overflow:auto}} table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68)}} th,td{{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line);white-space:nowrap}} th{{color:#bfdbfe;background:#0d1a2d}} tr:last-child td{{border-bottom:0}} @media(max-width:760px){{.stats,.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">DeepSWE retrospective · stock Pi only · 2026-08-14</div>
<h1>Process signals still did not beat trajectory length.</h1>
<p>This corrected analysis uses every eligible run from the three stock-Pi baseline releases. Fabric, workflow, memory, advisor, prompt, and other wrapper configs are excluded before session parsing.</p>
<div class="pills"><span class="pill good">100% direct Pi tool visibility</span><span class="pill neutral">{dataset["task_count"]} held-out tasks</span><span class="pill bad">log loss Δ {_metric(delta["log_loss"], signed=True)}</span><span class="pill bad">AUROC Δ {_metric(delta["auroc"], signed=True)}</span></div>
<div class="src">Configs: <code>{_escape(", ".join(dataset["allowed_configs"]))}</code> · branch <code>{_escape(manifest["git"]["branch"])}</code> · full methods in <a href="report.md">report.md</a></div></section>
<div class="stats"><div class="stat"><b>{modeling_reps}</b><span>usable stock-Pi attempts</span></div><div class="stat"><b>{features["successes"]} / {features["failures"]}</b><span>successes / failures</span></div><div class="stat"><b>{features["models"]}</b><span>models across {features["thinking_levels"]} thinking levels</span></div><div class="stat"><b>{session_mib:.1f} MiB</b><span>native session JSONL parsed</span></div></div>
<section class="callout bad"><h2>Result</h2><p>Adding process features increased held-out-task log loss from <b>{_metric(metrics["length"]["log_loss"])}</b> to <b>{_metric(metrics["process"]["log_loss"])}</b>. The task-bootstrap interval for process minus length was <b>{bootstrap["low"]:+.3f} to {bootstrap["high"]:+.3f}</b>; lower is better. The added features also reduced AUROC by <b>{abs(delta["auroc"]):.3f}</b>.</p></section>
<section class="callout good"><h2>The dataset is now the intended one</h2><p>All {modeling_reps} modeled sessions used only direct stock-Pi tool surfaces. No modeled run contained Fabric or another wrapper config, and all modeled sessions had complete semantic coverage under the extractor.</p></section>
<h2>Held-out-task comparison</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Log loss ↓</th><th>Macro-task log loss ↓</th><th>Brier ↓</th><th>AUROC ↑</th><th>Average precision ↑</th></tr></thead><tbody>{metric_rows}<tr><td><b>Process minus length</b></td><td><b>{delta["log_loss"]:+.3f}</b></td><td>{metrics["process"]["macro_task_log_loss"] - metrics["length"]["macro_task_log_loss"]:+.3f}</td><td>{delta["brier"]:+.3f}</td><td>{delta["auroc"]:+.3f}</td><td>{delta["average_precision"]:+.3f}</td></tr></tbody></table></div>
<h2>Model coverage</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Attempts</th><th>Tasks</th><th>Successes</th><th>Failures</th><th>Thinking levels</th></tr></thead><tbody>{model_rows}</tbody></table></div>
<h2>Results within each supported model</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Status</th><th>Length log loss</th><th>Process log loss</th><th>Difference</th><th>95% task-bootstrap interval</th></tr></thead><tbody>{sensitivity_rows}</tbody></table></div>
<section class="callout caution"><h2>Model-balance limitation</h2><p>GPT-5.6 Sol, GPT-5.5, and Luna supply nearly all observations. Terra and GLM-5.2 have six attempts each, so this analysis controls for their labels but cannot support reliable model-specific conclusions for them.</p></section>
<h2>Baseline releases</h2><div class="scroll"><table><thead><tr><th>Config</th><th>Attempts</th><th>Tasks</th><th>Successes</th><th>Attempts with observed tests</th></tr></thead><tbody>{config_rows}</tbody></table></div>
<h2>Raw feature direction</h2><p class="muted">Unadjusted means. These describe the baseline dataset; they are not independent causal effects.</p><div class="scroll"><table><thead><tr><th>Measure</th><th>Failures</th><th>Successes</th><th>Raw direction</th></tr></thead><tbody>{feature_rows}</tbody></table></div>
<h2>Dataset audit</h2><div class="grid"><section class="card"><h3>Scope</h3><ul><li><b>{schema["canonical_results_loaded"]:,}</b> stock-Pi baseline results loaded.</li><li><b>{schema["analysis_scope"]["excluded_canonical_results"]:,}</b> other canonical config results excluded.</li><li><b>{dispositions.get("eligible", 0):,}</b> verifier-complete baseline attempts.</li><li><b>{dispositions.get("verifier_skipped_empty_patch", 0)}</b> empty-patch outcomes excluded from binary modeling.</li></ul></section><section class="card"><h3>Session evidence</h3><ul><li><b>{sessions["record_types"].get("message", 0):,}</b> message records parsed.</li><li><b>{sum(sessions["tool_names"].values()):,}</b> top-level tool calls observed.</li><li><b>{support["reps_with_observable_tests"]:,}</b> attempts ran an observable test command.</li><li><b>{support["reps_with_direct_mutations"]:,}</b> attempts made a direct mutation.</li></ul></section></div>
<h2>Remaining measurement limits</h2><section class="callout caution"><ul><li>Native sessions preserve direct calls, but there are no intermediate patch snapshots, so true patch-size churn and partial reversions remain unavailable.</li><li>The strict unchanged-test-failure signature can miss semantically identical failures when incidental output changes.</li><li>The model compares held-out tasks, but task and model coverage are uneven.</li><li>These are predictive associations, not proof that a behavior causes failure.</li></ul></section>
<h2>All {features["tasks"]} tasks</h2><div class="scroll"><table><thead><tr><th>Task</th><th>Attempts</th><th>Successes</th><th>Success rate</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<section class="callout good"><h2>Conclusion</h2><p>On the corrected stock-Pi dataset, the measured process signals do not improve prediction beyond trajectory length and basic model/config controls. The negative result is smaller than in the mixed-config pilot, but the task-bootstrap interval still favors the length-only model.</p></section>
<p class="src">Evidence: <a href="artifacts/baseline_cohort.csv">cohort</a> · <a href="artifacts/baseline_features.csv">features</a> · <a href="artifacts/schema_audit.json">schema audit</a> · <a href="artifacts/held_out_task_evaluation.json">evaluation</a> · <a href="artifacts/baseline_manifest.json">manifest</a></p>
</main></body></html>"""


def _model_sensitivity_row(model: str, item: dict[str, Any]) -> str:
    if item["status"] != "evaluated":
        return (
            f"<tr><td><code>{_escape(model)}</code></td>"
            f"<td><span class='tag caution'>too little data: {item['reps']} attempts / "
            f"{item['tasks']} tasks</span></td><td>—</td><td>—</td><td>—</td><td>—</td></tr>"
        )
    evaluation = item["evaluation"]
    metrics = evaluation["binary_metrics"]
    delta = evaluation["process_minus_length"]
    interval = delta["task_bootstrap_log_loss_delta_95pct"]
    return (
        f"<tr><td><code>{_escape(model)}</code></td><td>evaluated</td>"
        f"<td>{metrics['length']['log_loss']:.3f}</td>"
        f"<td>{metrics['process']['log_loss']:.3f}</td>"
        f"<td>{delta['log_loss']:+.3f}</td>"
        f"<td>{interval['low']:+.3f} to {interval['high']:+.3f}</td></tr>"
    )


def _feature_row(data: dict[str, Any], name: str, label: str) -> str:
    failure = data["by_outcome"]["failure"][name]["mean"]
    success = data["by_outcome"]["success"][name]["mean"]
    direction = "higher in failures" if failure > success else "higher in successes"
    if name == "total_tokens":
        failure_text = f"{failure / 1_000_000:.2f}M"
        success_text = f"{success / 1_000_000:.2f}M"
    else:
        failure_text = f"{failure:.3f}"
        success_text = f"{success:.3f}"
    return (
        f"<tr><td>{_escape(label)}</td><td>{failure_text}</td>"
        f"<td>{success_text}</td><td><span class='tag neutral'>{direction}</span></td></tr>"
    )


def main() -> None:
    """Write the rendered report beside the Markdown source."""
    OUTPUT_PATH.write_text(render_trajectory_process_report())
    print(f"wrote {OUTPUT_PATH} ({OUTPUT_PATH.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

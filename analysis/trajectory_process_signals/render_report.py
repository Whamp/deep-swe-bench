"""Render the trajectory process-signal milestone as a self-contained HTML report."""

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
    """Build the complete HTML report from committed derived artifacts."""
    schema = json.loads((ARTIFACTS_DIR / "schema_audit.json").read_text())
    sessions = json.loads((ARTIFACTS_DIR / "session_schema_audit.json").read_text())
    features = json.loads((ARTIFACTS_DIR / "feature_summary.json").read_text())
    evaluation = json.loads(
        (ARTIFACTS_DIR / "held_out_task_evaluation.json").read_text()
    )
    manifest = json.loads((ARTIFACTS_DIR / "pilot_manifest.json").read_text())

    metrics = evaluation["binary_metrics"]
    delta = evaluation["process_minus_length"]
    bootstrap = delta["task_bootstrap_log_loss_delta_95pct"]
    dispositions = schema["primary_disposition_counts"]
    support = sessions["semantic_feature_support"]
    modeling_reps = sessions["modeling_reps"]

    task_rows = "".join(
        f"<tr><td><code>{_escape(row['task'])}</code></td>"
        f"<td>{row['reps']}</td><td>{row['successes']}</td>"
        f"<td>{_percent(row['successes'], row['reps'])}</td></tr>"
        for row in features["by_task"]
    )
    model_rows = "".join(
        f"<tr><td>{_escape(label)}</td>"
        f"<td>{_metric(metrics[key]['log_loss'])}</td>"
        f"<td>{_metric(metrics[key]['macro_task_log_loss'])}</td>"
        f"<td>{_metric(metrics[key]['brier'])}</td>"
        f"<td>{_metric(metrics[key]['auroc'])}</td>"
        f"<td>{_metric(metrics[key]['average_precision'])}</td></tr>"
        for key, label in (
            ("prevalence", "Fold-train prevalence"),
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
<title>Trajectory process signals · first milestone</title>
<style>
:root{{--bg:#07111f;--surface:#0f1d31;--ink:#eef5ff;--blue:#60a5fa;--green:#34d399;--red:#fb7185;--amber:#fbbf24;--muted:#9fb0c9;--line:#263850}}
*{{box-sizing:border-box}} body{{margin:0;background:radial-gradient(circle at top left,#183e65,var(--bg) 42%,#050913);color:var(--ink);font:15px/1.55 ui-sans-serif,system-ui}}
main{{max-width:1240px;margin:auto;padding:36px 22px 70px}} h1{{font-size:clamp(38px,6vw,72px);line-height:.94;letter-spacing:-.055em;margin:12px 0 18px}} h2{{margin:36px 0 12px;font-size:28px}} h3{{margin:22px 0 8px}} p,li{{color:#dbe7fb}} code{{color:#bfdbfe}} a{{color:#93c5fd}} .hero,.card,.callout{{background:rgba(15,29,49,.9);border:1px solid var(--line);border-radius:24px;padding:24px}} .hero{{padding:34px;background:linear-gradient(135deg,rgba(96,165,250,.18),rgba(15,29,49,.95) 48%,rgba(251,191,36,.09))}} .kicker{{color:var(--blue);text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:800}} .pills{{display:flex;gap:9px;flex-wrap:wrap;margin:18px 0}} .pill,.tag{{display:inline-flex;border-radius:999px;padding:5px 10px;font-size:12px;font-weight:800;border:1px solid var(--line);background:#0b1728}} .good{{color:#b9f8da;border-color:rgba(52,211,153,.5);background:rgba(52,211,153,.12)}} .bad{{color:#fecdd3;border-color:rgba(251,113,133,.5);background:rgba(251,113,133,.12)}} .caution{{color:#fde68a;border-color:rgba(251,191,36,.55);background:rgba(251,191,36,.12)}} .neutral{{color:#bfdbfe;border-color:rgba(96,165,250,.45);background:rgba(96,165,250,.12)}} .stats{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin:20px 0}} .stat{{background:rgba(15,29,49,.88);border:1px solid var(--line);border-radius:20px;padding:18px}} .stat b{{display:block;font-size:30px;line-height:1.05;letter-spacing:-.04em}} .stat span,.muted{{color:var(--muted);font-size:12px}} .grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .callout{{margin:18px 0}} .callout.bad{{border-left:5px solid var(--red)}} .callout.caution{{border-left:5px solid var(--amber)}} .callout.good{{border-left:5px solid var(--green)}} table{{width:100%;border-collapse:separate;border-spacing:0;border:1px solid var(--line);border-radius:18px;overflow:hidden;background:rgba(9,18,32,.68)}} th,td{{text-align:left;vertical-align:top;padding:10px 12px;border-bottom:1px solid var(--line)}} th{{color:#bfdbfe;background:#10233b;font-size:12px;text-transform:uppercase;letter-spacing:.06em}} tr:last-child td{{border-bottom:0}} .scroll{{overflow:auto}} .src{{color:var(--muted);font-size:12px;margin-top:16px}} ul{{padding-left:20px}} @media(max-width:850px){{.stats,.grid{{grid-template-columns:1fr 1fr}}}} @media(max-width:560px){{.stats,.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<section class="hero"><div class="kicker">DeepSWE retrospective · feasibility milestone · 2026-08-14</div>
<h1>The pipeline works.<br>The first process model does not.</h1>
<p>A deterministic 12-task pilot held out whole tasks and compared the same controls with and without event-semantic trajectory features. Process features worsened every primary predictive metric. Observability gaps make this a pipeline result, not a final rejection of the hypothesis.</p>
<div class="pills"><span class="pill caution">pilot, not final study</span><span class="pill bad">log loss Δ {_metric(delta["log_loss"], signed=True)}</span><span class="pill bad">AUROC Δ {_metric(delta["auroc"], signed=True)}</span><span class="pill neutral">raw results unchanged</span></div>
<div class="src">Branch <code>{_escape(manifest["git"]["branch"])}</code> · base <code>{_escape(manifest["git"]["base_revision"][:10])}</code> · full methods in <a href="report.md">report.md</a></div></section>
<div class="stats"><div class="stat"><b>{modeling_reps}</b><span>modeled reps across 12 held-out tasks</span></div><div class="stat"><b>{features["successes"]} / {features["failures"]}</b><span>successes / verifier-complete failures</span></div><div class="stat"><b>{_percent(support["fully_observable_reps"], modeling_reps)}</b><span>fully observable tool surfaces</span></div><div class="stat"><b>371 MB</b><span>session JSONL read under a 512 MiB cap</span></div></div>
<section class="callout bad"><h2>Measured verdict</h2><p>Adding process features increased held-out-task log loss from <b>{_metric(metrics["length"]["log_loss"])}</b> to <b>{_metric(metrics["process"]["log_loss"])}</b>. The 2,000-sample task-bootstrap interval for process minus length was <b>{bootstrap["low"]:+.3f} to {bootstrap["high"]:+.3f}</b>; lower is better. Partial-reward RMSE also worsened by {evaluation["partial_process_minus_length"]["rmse"]:+.3f}.</p></section>
<section class="callout caution"><h2>Why this is not a corpus-wide conclusion</h2><ul><li>{support["partially_observable_reps"] + support["opaque_only_reps"]} reps had incomplete or opaque semantic tool coverage.</li><li>True intermediate patch churn is unavailable; only direct mutation revisits and exact inverse edits are observable.</li><li>The strict unchanged-test-failure feature fired zero times.</li><li>Declared resource policy exists in only 17.9% of canonical results.</li><li>The pilot pools {features["models"]} models and {features["configs"]} configs.</li></ul></section>
<h2>Held-out-task models</h2><div class="scroll"><table><thead><tr><th>Model</th><th>Log loss ↓</th><th>Macro-task log loss ↓</th><th>Brier ↓</th><th>AUROC ↑</th><th>Avg precision ↑</th></tr></thead><tbody>{model_rows}<tr><td><b>Process minus length</b></td><td><b>{delta["log_loss"]:+.3f}</b></td><td>+{metrics["process"]["macro_task_log_loss"] - metrics["length"]["macro_task_log_loss"]:.3f}</td><td>{delta["brier"]:+.3f}</td><td>{delta["auroc"]:+.3f}</td><td>{delta["average_precision"]:+.3f}</td></tr></tbody></table></div>
<h2>Raw feature direction</h2><p class="muted">Unadjusted means. These describe the pilot; they do not estimate independent effects.</p><div class="scroll"><table><thead><tr><th>Measure</th><th>Failures</th><th>Successes</th><th>Raw direction</th></tr></thead><tbody>{feature_rows}</tbody></table></div>
<h2>Corpus schema audit</h2><div class="grid"><section class="card"><h3>Current snapshot</h3><ul><li><b>{schema["candidate_result_files"]:,}</b> result files total; <b>{schema["canonical_results_loaded"]:,}</b> canonical.</li><li><b>{schema["candidate_native_session_files"]:,}</b> native sessions total; <b>{schema["native_session_dispositions"]["attached_to_canonical_result"]:,}</b> attached to canonical results.</li><li><b>{schema["artifact_availability"]["has_verifier_reward"]["present"]:,}</b> verifier reward/CTRF pairs.</li><li><b>{schema["model_patch_schema"]["size_matches_result_patch_bytes"]:,}</b> present patches matched <code>patch_bytes</code>.</li></ul></section><section class="card"><h3>Primary dispositions</h3><ul><li>{dispositions["eligible"]:,} verifier-complete eligible reps</li><li>{dispositions["agent_timeout"]} agent timeouts; {dispositions["agent_infrastructure_error"]} infrastructure exits</li><li>{dispositions["ambiguous_multiple_sessions"]} ambiguous multi-session cells; {dispositions["missing_session"]} missing sessions</li><li>{dispositions["verifier_timeout"]} verifier timeouts; {dispositions["verifier_skipped_empty_patch"]} skipped empty patches</li></ul></section></div>
<h2>Pilot tasks</h2><div class="scroll"><table><thead><tr><th>Task</th><th>Reps</th><th>Successes</th><th>Success rate</th></tr></thead><tbody>{task_rows}</tbody></table></div>
<section class="callout good"><h2>Next decision</h2><p>Do not parse the full corpus yet. First rerun these same 12 tasks on a direct-tool sensitivity cohort, validate a normalized test-failure signature against hand labels, and add structured nested-operation extraction only where the trace proves the operation. Expand to 36 tasks only if process features improve both micro and macro-task log loss.</p></section>
<p class="src">Evidence: <a href="artifacts/schema_audit.json">schema audit</a> · <a href="artifacts/feature_summary.json">feature summary</a> · <a href="artifacts/held_out_task_evaluation.json">evaluation</a> · <a href="artifacts/pilot_manifest.json">manifest</a></p>
</main></body></html>"""


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

#!/usr/bin/env python3
"""Build the full-set OOM and igel verifier diagnosis report."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
RESULTS = Path("/home/will/evals/deep-swe-bench/results")
PROBES = REPO / "analysis/testing-skills-1.1.0/resource-exclusion-probes.json"
OUTPUT = REPO / "reports/testing-skills-full113-resource-diagnosis/index.html"
FULL_PLAN = "sha256:09147f80192428953f0211ff1f41b313e21c2ec9ca548fe48a0e09472a99c96a"
WAZERO_PLAN = "sha256:db03ca93ce1fd4e6dbeea77ba49cecae7974d74bc0a8fa9dd9d02f08d8eeea57"


def esc(value: object) -> str:
    return html.escape(str(value))


def load_exclusions() -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in (RESULTS / "_contaminated/manifest.jsonl").read_text().splitlines()
    ]
    selected = [
        row
        for row in rows
        if row.get("launch_plan_identity") in {FULL_PLAN, WAZERO_PLAN}
        and row.get("category") in {"resource-oom", "harness-failure"}
    ]
    assert len(selected) == 21, len(selected)
    assert sum(row["category"] == "resource-oom" for row in selected) == 15
    assert sum(row["category"] == "harness-failure" for row in selected) == 6
    return sorted(selected, key=lambda row: (row["category"], row["original_path"]))


def result_for(row: dict[str, Any]) -> dict[str, Any]:
    return json.loads((Path(row["quarantine_path"]) / "result.json").read_text())


def disposition(task: str) -> str:
    return {
        "effect-sse-httpapi-streaming": "Rerun · 8 GiB",
        "geo-shapeindex-serialization": "Rerun · 8 GiB",
        "pebble-durability-wait-apis": "Restore · no rerun",
        "wazero-multi-module-snapshots": "Rerun · 16 GiB",
        "igel-persist-feature-schema": "Verifier-only recompute",
    }[task]


def affected_rows(exclusions: list[dict[str, Any]]) -> str:
    rows = []
    for exclusion in exclusions:
        result = result_for(exclusion)
        task = result["task"]
        memory = result["resource_policy"]["subject_memory_gib"]
        memory_events = result.get("subject_memory_events")
        if memory_events is None:
            oom = 0
        elif isinstance(memory_events, dict):
            oom = memory_events["oom_kill"]
        else:
            raise TypeError(f"Invalid subject memory events for {task}")
        reward = (
            "invalid"
            if exclusion["category"] == "harness-failure"
            else result["reward_binary"]
        )
        rows.append(
            "<tr>"
            f"<td><code>{esc(task)}</code></td>"
            f"<td>{esc(result['config'])}</td><td>rep{result['rep']}</td>"
            f"<td>{memory:g} GiB</td><td>{oom}</td><td>{reward}</td>"
            f"<td><strong>{esc(disposition(task))}</strong></td>"
            "</tr>"
        )
    return "".join(rows)


def probe_rows(probes: dict[str, Any]) -> str:
    rows = []
    for probe in probes["subject_probes"]:
        cpu = "host-visible" if probe["cpu_limit"] is None else str(probe["cpu_limit"])
        status = "clean" if probe["oom_kills"] == 0 else "OOM"
        cls = "good" if status == "clean" else "bad"
        rows.append(
            "<tr>"
            f"<td><code>{esc(probe['task'])}</code></td>"
            f"<td>{probe['memory_gib']} GiB</td><td>{cpu}</td>"
            f"<td>{probe['peak_gib']:.3f} GiB</td>"
            f"<td><span class='pill {cls}'>{status}</span></td>"
            f"<td>{esc(probe['conclusion'])}</td>"
            "</tr>"
        )
    return "".join(rows)


def decision_rows(probes: dict[str, Any]) -> str:
    return "".join(
        "<tr>"
        f"<td><code>{esc(row['task'])}</code></td>"
        f"<td><strong>{esc(row['action'])}</strong></td>"
        f"<td>{row['cells']}</td><td>{esc(row['reason'])}</td>"
        "</tr>"
        for row in probes["recommended_disposition"]
    )


def build_report() -> None:
    exclusions = load_exclusions()
    probes = json.loads(PROBES.read_text())
    assert len(probes["igel_regrades"]) == 6
    assert all(row["reward"] == 1 for row in probes["igel_regrades"])
    html_doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Full-set resource and verifier diagnosis</title><link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg'><text y='.9em' font-size='90'>🔬</text></svg>"><style>
:root{{--bg:#eef3f8;--surface:#fff;--ink:#172238;--muted:#61708a;--blue:#24568f;--green:#167451;--red:#b23b35;--amber:#a26900;--line:#d6dfeb}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,sans-serif}}main{{max-width:1180px;margin:auto;padding:24px}}.hero{{padding:34px;border-radius:24px;background:linear-gradient(135deg,#17355d,#285b91);color:#fff}}h1{{font-size:clamp(2rem,5vw,3.5rem);line-height:1.05;margin:.2em 0}}h2{{margin-top:42px}}.hero p{{max-width:800px;font-size:1.15rem}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;margin:20px 0}}.stat,.callout{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:18px}}.stat strong{{display:block;font-size:1.8rem}}.muted{{color:var(--muted)}}.pill{{display:inline-block;border-radius:999px;padding:4px 9px;font-size:.82rem;font-weight:700}}.good{{background:#d9f2e8;color:var(--green)}}.bad{{background:#fae0de;color:var(--red)}}.caution{{background:#fff0c8;color:var(--amber)}}.neutral{{background:#e1eaf5;color:var(--blue)}}.table-wrap{{overflow-x:auto;background:#fff;border:1px solid var(--line);border-radius:16px}}table{{border-collapse:collapse;width:100%;min-width:760px}}th,td{{padding:11px 13px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}}th{{background:#f6f9fc}}code{{font-size:.87em}}.decision{{border-left:5px solid var(--blue)}}.warning{{border-left:5px solid var(--amber)}}footer{{color:var(--muted);padding:32px 0}}
</style></head><body><main>
<section class="hero"><div>FULL 113 · FAILURE DISPOSITION</div><h1>Three remedies, not one bigger memory limit</h1><p>The 21 excluded trajectories represent different failure classes. Pebble has valid grades and should be restored. Igel needs verifier-only recomputation after a fixed launch wrapper. Effect, Geo, and Wazero need clean paired reruns at measured limits.</p></section>
<div class="stats"><div class="stat"><strong>21</strong><span class="muted">excluded trajectories inspected</span></div><div class="stat"><strong>15</strong><span class="muted">subject OOM trajectories</span></div><div class="stat"><strong>6/6</strong><span class="muted">Igel patches regrade 1.0</span></div><div class="stat"><strong>18</strong><span class="muted">recommended new model calls</span></div><div class="stat"><strong>5</strong><span class="muted">Pebble cells to restore</span></div></div>
<section class="callout decision"><strong>Recommendation.</strong> Restore Pebble’s five quarantined cells; recompute Igel’s six grades from saved patches; rerun both configs for all three reps of Effect and Geo at 8 GiB and Wazero at 16 GiB. This uses 18 new model calls rather than rerunning all 21 excluded trajectories.</section>
<h2>All affected trajectories</h2><p>The complete denominator comes first: 15 subject-OOM trajectories and six invalid Igel grades.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th>Config</th><th>Rep</th><th>Original limit</th><th>OOM kills</th><th>Observed grade</th><th>Disposition</th></tr></thead><tbody>{affected_rows(exclusions)}</tbody></table></div>
<h2>Measured replay evidence</h2><p>Each probe reapplied a saved patch to its exact immutable image, disabled networking, and changed only the listed resource ceiling. No model was called.</p><div class="table-wrap"><table><thead><tr><th>Task</th><th>Limit</th><th>CPUs</th><th>Peak</th><th>Result</th><th>Meaning</th></tr></thead><tbody>{probe_rows(probes)}</tbody></table></div>
<h2>Why each task differs</h2><div class="stats"><div class="callout"><strong>Effect</strong><p>Repository-wide PNPM build and doc generation killed parallel TypeScript processes at 4 GiB. The same saved patch completes at 8 GiB with a 6.025 GiB peak.</p></div><div class="callout"><strong>Geo</strong><p>The agent’s Go fuzz command spawned 16 workers. Four died at 4 GiB although the fuzz coordinator returned PASS. At 8 GiB the same command peaks at 4.809 GiB with no kills.</p></div><div class="callout"><strong>Pebble</strong><p>The killed package contains upstream 64-bit stress tests that deliberately allocate multi-gigabyte blocks and explicitly skip in CI. It fills both 8 and 16 GiB. The official targeted verifier passed every required test in all five quarantined reps.</p></div><div class="callout"><strong>Wazero</strong><p>The full Go suite exceeded 12 GiB. Clean replays peak between 11.652 and 14.445 GiB, making 16 GiB the smallest evidenced ceiling with practical headroom.</p></div><div class="callout"><strong>Igel</strong><p>The verifier used <code>bash -lc</code>, which dropped <code>/opt/venv/bin</code> from the image PATH. Commit <code>524a84d</code> switches all runners to a non-login shell. All six saved patches then pass 24/24 feature and 2/2 preservation tests.</p></div></div>
<h2>Exact next actions</h2><div class="table-wrap"><table><thead><tr><th>Task</th><th>Action</th><th>Cells</th><th>Basis</th></tr></thead><tbody>{decision_rows(probes)}</tbody></table></div>
<section class="callout warning"><strong>Do not launch yet.</strong> Igel needs a sanctioned verifier-only recomputation artifact path, and the three rerun resource plans must be compiled and approved by exact hash. Clean existing Geo and Wazero cells should be preserved before replacement, not deleted.</section>
<footer>Built from <code>results/_contaminated/manifest.jsonl</code>, quarantined result/session artifacts, and <code>analysis/testing-skills-1.1.0/resource-exclusion-probes.json</code>.</footer>
</main></body></html>"""
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(html_doc)
    print(f"wrote {OUTPUT}")


if __name__ == "__main__":
    build_report()

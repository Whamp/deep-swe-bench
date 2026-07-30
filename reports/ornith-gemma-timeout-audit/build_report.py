#!/usr/bin/env python3
"""Build the Ornith and Gemma agent-timeout incident audit."""

from __future__ import annotations

import html
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPORT_DIR = Path(__file__).resolve().parent
WORKTREE_ROOT = REPORT_DIR.parents[1]
DATA_ROOT = Path(
    subprocess.check_output(
        ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
        cwd=WORKTREE_ROOT,
        text=True,
    ).strip()
).parent
OUTPUT_HTML = REPORT_DIR / "index.html"
OUTPUT_JSON = REPORT_DIR / "timeout-audit.json"

RESULT_ROOTS = {
    "Gemma": DATA_ROOT
    / "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0",
    "Ornith": DATA_ROOT
    / "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0",
}
RUN_EVENTS = {
    "Gemma": DATA_ROOT
    / "results/_runs/gemma4-31b-high-12v2-r3-w2--62f5bb098c6f4fd8f8fbb8c059ed5241eff31cd4ded716ce041aeb2847beb4f1/events.ndjson",
    "Ornith": DATA_ROOT
    / "results/_runs/ornith-35b-high-12v2-r3-w4--ee4eef1bc12334d42d9deb521201cf83991e880ffcf4e4508b684632f0462871/events.ndjson",
}
PI_CHECK_ROOT = DATA_ROOT / "results/gemma-4-31b/high/pi-check@1.1.0"
CHECK_MARKER = "Re-audit every requirement in the original request with fresh, independent evidence"

ASSESSMENTS: dict[tuple[str, str, int], dict[str, str]] = {
    (
        "Ornith",
        "langchain-request-coalescing",
        0,
    ): {
        "mechanism": "The final self-authored pytest suite blocked. The saved patch did not hang the external grader: it completed with 23/50 feature tests and 232/232 preservation tests.",
        "state": "Blocked in local validation; patch remained gradable",
        "extension": "No benefit from more wall time alone. With a bounded test command, further debugging could plausibly improve partial credit; an exact solve was still distant.",
        "confidence": "high",
    },
    (
        "Ornith",
        "langchain-request-coalescing",
        1,
    ): {
        "mechanism": "The final pytest suite blocked, and external verification independently stalled at test_abatch_per_item_coalescing after reaching 36% of the feature suite.",
        "state": "Patch-level async deadlock",
        "extension": "No benefit from more wall time alone. The model needed the local command to time out and return control before it could diagnose the deadlock.",
        "confidence": "high",
    },
    (
        "Ornith",
        "langchain-request-coalescing",
        2,
    ): {
        "mechanism": "The final two-thread reproducer blocked. External pytest reached a 19-fail/31-pass summary in 247 seconds but did not exit; thread-safety took 180 seconds and patch-created non-daemon work remained alive until the verifier cap.",
        "state": "Patch leaked or stranded concurrency work",
        "extension": "No benefit from more wall time alone. The hang was itself the bug; bounded execution and thread-state inspection were required.",
        "confidence": "high",
    },
    (
        "Ornith",
        "mobly-grouped-test-barriers",
        0,
    ): {
        "mechanism": "The final synchronization test blocked. External verification then blocked before producing suite artifacts for its full cap, corroborating a barrier or thread-lifecycle deadlock in the saved patch.",
        "state": "Patch-level synchronization deadlock",
        "extension": "No benefit from more wall time alone. A short command timeout plus thread dump or narrower barrier reproducer was needed.",
        "confidence": "high",
    },
    (
        "Ornith",
        "mobly-grouped-test-barriers",
        2,
    ): {
        "mechanism": "The final controller-manager test blocked immediately after a condition-variable edit. External verification also blocked before emitting suite artifacts for its full cap.",
        "state": "Patch-level condition-variable deadlock",
        "extension": "No benefit from more wall time alone. The model needed a bounded reproducer and lock-state diagnosis, not a longer global budget.",
        "confidence": "high",
    },
    (
        "Ornith",
        "obsidian-linter-link-format-conversion",
        2,
    ): {
        "mechanism": "The final Python inspection command should have been short but never returned. It followed five nearly identical byte/string inspections, and its old/new replacement literals were identical. External verification completed with perfect preservation but collected no feature-test records.",
        "state": "Tool hang plus unproductive literal-debugging loop",
        "extension": "More wall time alone was unlikely to help. If the command had been bounded and a fresh audit took over, this was the most salvageable Ornith timeout, but the saved score does not prove a one-line fix would solve it.",
        "confidence": "medium",
    },
    (
        "Gemma",
        "langchain-request-coalescing",
        2,
    ): {
        "mechanism": "No tool was pending. Gemma used almost the full hour, had just identified two concrete callback/future fixes, and was waiting in another model turn when killed. External verification completed with 20/50 feature and 232/232 preservation tests.",
        "state": "Genuine model-time exhaustion while still reasoning",
        "extension": "A modest extension plausibly would have improved partial credit because the next fixes were explicit. Exact completion remained uncertain with 30 feature tests still failing.",
        "confidence": "high",
    },
    (
        "Gemma",
        "mobly-grouped-test-barriers",
        2,
    ): {
        "mechanism": "No tool was pending. Gemma was waiting for another model response after repeated exact-edit failures and a full-file read. External verification completed, but only 1/79 feature tests passed and preservation had regressed to 679/808.",
        "state": "Genuine model-time exhaustion in a poor implementation state",
        "extension": "More time might have produced another edit, but a meaningful score rescue was unlikely without changing approach; further destructive rewriting was also plausible.",
        "confidence": "high",
    },
}


def parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value)


def load_run_events(model: str) -> dict[tuple[str, int], dict[str, datetime]]:
    events: dict[tuple[str, int], dict[str, datetime]] = {}
    for line in RUN_EVENTS[model].read_text().splitlines():
        record = json.loads(line)
        if record.get("event") not in {"cell_started", "cell_finished"}:
            continue
        key = (str(record["task"]), int(record["rep"]))
        times = events.setdefault(key, {})
        times[record["event"]] = parse_timestamp(record["ts"])
    return events


def first_text(content: Any) -> str:
    if not isinstance(content, list):
        return str(content or "")
    return "\n".join(
        str(part.get("text") or part.get("thinking") or "")
        for part in content
        if isinstance(part, dict)
    )


def parse_incident(
    model: str,
    result_path: Path,
    event_times: dict[tuple[str, int], dict[str, datetime]],
) -> dict[str, Any]:
    result = json.loads(result_path.read_text())
    task = str(result["task"])
    rep = int(result["rep"])
    cell = result_path.parent
    session_path = max((cell / "session").glob("*.jsonl"))
    records = [
        json.loads(line)
        for line in session_path.read_text(errors="replace").splitlines()
        if line.strip()
    ]
    messages = [record for record in records if record.get("type") == "message"]
    calls: list[dict[str, Any]] = []
    completed_call_ids: set[str] = set()
    for record in messages:
        message = record.get("message", {})
        if message.get("role") == "toolResult":
            completed_call_ids.add(str(message.get("toolCallId")))
        if message.get("role") != "assistant":
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict) or part.get("type") != "toolCall":
                continue
            calls.append(
                {
                    "timestamp": record["timestamp"],
                    "id": str(part.get("id")),
                    "name": str(part.get("name")),
                    "arguments": part.get("arguments") or {},
                }
            )
    pending = [call for call in calls if call["id"] not in completed_call_ids]
    rpc_records = [
        json.loads(line)
        for line in (cell / "logs/pi-rpc-runner.jsonl").read_text().splitlines()
        if line.strip()
    ]
    rpc_finished = next(
        record for record in reversed(rpc_records) if record.get("event") == "finished"
    )
    start = event_times[(task, rep)]["cell_started"]
    finish = event_times[(task, rep)]["cell_finished"]
    last_message_at = parse_timestamp(messages[-1]["timestamp"])
    first_message_at = parse_timestamp(messages[0]["timestamp"])
    pending_seconds = None
    if pending:
        pending_seconds = max(
            0.0,
            result["agent_wall_s"]
            - (parse_timestamp(pending[-1]["timestamp"]) - start).total_seconds(),
        )
    verifier_elapsed = max(
        0.0, (finish - start).total_seconds() - float(result["agent_wall_s"])
    )
    assessment = ASSESSMENTS[(model, task, rep)]
    return {
        "model": model,
        "task": task,
        "rep": rep,
        "result_path": str(result_path.relative_to(DATA_ROOT)),
        "agent_wall_s": result["agent_wall_s"],
        "session_span_s": (last_message_at - first_message_at).total_seconds(),
        "last_message_before_agent_deadline_s": max(
            0.0, result["agent_wall_s"] - (last_message_at - start).total_seconds()
        ),
        "pending_tool_calls": len(pending),
        "pending_tool": pending[-1]["name"] if pending else None,
        "pending_arguments": pending[-1]["arguments"] if pending else None,
        "pending_seconds_at_deadline": pending_seconds,
        "pending_has_timeout_argument": (
            "timeout" in pending[-1]["arguments"] if pending else None
        ),
        "last_completed_tool_calls": [
            {
                "timestamp": call["timestamp"],
                "name": call["name"],
                "arguments": call["arguments"],
            }
            for call in calls[-6:]
        ],
        "last_message_text": first_text(messages[-1].get("message", {}).get("content"))[
            :3000
        ],
        "rpc_event_counts": rpc_finished.get("event_counts"),
        "reward_binary": result["reward_binary"],
        "reward_partial": result["reward_partial"],
        "f2p": [result.get("f2p_passed"), result.get("f2p_total")],
        "p2p": [result.get("p2p_passed"), result.get("p2p_total")],
        "turns": result["turns"],
        "tool_calls": result["tool_calls"],
        "total_tokens": result["total_tokens"],
        "patch_bytes": result["patch_bytes"],
        "verifier_exit": result["verifier_exit"],
        "verifier_elapsed_s": verifier_elapsed,
        "assessment": assessment,
    }


def collect_pi_check_delivery() -> dict[str, Any]:
    timeout_cells: list[dict[str, Any]] = []
    for result_path in sorted(PI_CHECK_ROOT.glob("*/rep*/result.json")):
        result = json.loads(result_path.read_text())
        if not result.get("agent_timed_out"):
            continue
        session_text = "".join(
            path.read_text(errors="replace")
            for path in (result_path.parent / "session").glob("*.jsonl")
        )
        timeout_cells.append(
            {
                "task": result["task"],
                "rep": result["rep"],
                "check_delivered": CHECK_MARKER in session_text,
            }
        )
    return {
        "timeouts": len(timeout_cells),
        "delivered_before_timeout": sum(
            cell["check_delivered"] for cell in timeout_cells
        ),
        "not_delivered_before_timeout": sum(
            not cell["check_delivered"] for cell in timeout_cells
        ),
        "cells": timeout_cells,
    }


run_events = {model: load_run_events(model) for model in RESULT_ROOTS}
incidents: list[dict[str, Any]] = []
for model, root in RESULT_ROOTS.items():
    for result_path in sorted(root.glob("*/rep*/result.json")):
        result = json.loads(result_path.read_text())
        if result.get("agent_timed_out"):
            incidents.append(parse_incident(model, result_path, run_events[model]))

if len(incidents) != 8:
    raise SystemExit(f"expected 8 agent timeout incidents, found {len(incidents)}")
ornith_incidents = [incident for incident in incidents if incident["model"] == "Ornith"]
gemma_incidents = [incident for incident in incidents if incident["model"] == "Gemma"]
if not all(
    incident["pending_tool"] == "bash"
    and incident["pending_has_timeout_argument"] is False
    for incident in ornith_incidents
):
    raise SystemExit("every Ornith timeout must end in an unbounded bash call")
if any(incident["pending_tool_calls"] for incident in gemma_incidents):
    raise SystemExit("Gemma timeout classification changed: a tool is now pending")

pi_check_delivery = collect_pi_check_delivery()
verifier_only_path = (
    RESULT_ROOTS["Gemma"] / "langchain-request-coalescing/rep0/result.json"
)
verifier_only_result = json.loads(verifier_only_path.read_text())
verifier_only = {
    "task": verifier_only_result["task"],
    "rep": verifier_only_result["rep"],
    "agent_timed_out": verifier_only_result["agent_timed_out"],
    "agent_wall_s": verifier_only_result["agent_wall_s"],
    "verifier_exit": verifier_only_result["verifier_exit"],
    "evidence": "External feature verification stalled on test_invoke_returns_correct_result for the full 35-minute verifier cap. This was a patch-induced test deadlock, not an agent timeout.",
}

audit = {
    "schema_version": 1,
    "generated_at": datetime.now(UTC).isoformat(),
    "comparison": {
        "subset": "12_v2",
        "reps": 3,
        "thinking": "high",
        "agent_timeout_s": 3600,
        "verifier_timeout_s": 2100,
        "configs": {
            "Gemma": "baseline-gemma4-31b@1.0.0",
            "Ornith": "baseline-ornith-35b@1.0.0",
        },
    },
    "incidents": incidents,
    "verifier_only_gemma_incident": verifier_only,
    "prior_gemma_pi_check_delivery": pi_check_delivery,
    "conclusion": {
        "ornith_more_wall_time_alone": "would_not_help",
        "gemma_langchain_more_time": "plausibly_improves_partial",
        "gemma_mobly_more_time": "unlikely_material_rescue",
        "recommended_clean_comparison": "keep the 3600-second cap and run pi-check unchanged; report intention-to-treat and check-delivered cells separately",
        "recommended_practical_variant": "pair a baseline and pi-check release with the same automatic default timeout for unbounded bash calls",
    },
}
OUTPUT_JSON.write_text(json.dumps(audit, indent=2, sort_keys=True))


def minutes(seconds: float | None) -> str:
    return "—" if seconds is None else f"{seconds / 60:.1f} min"


def score_text(incident: dict[str, Any]) -> str:
    f2p = incident["f2p"]
    p2p = incident["p2p"]
    if f2p[0] is None:
        return "ungraded"
    return (
        f"partial {incident['reward_partial']:.3f}; "
        f"F2P {f2p[0]}/{f2p[1]}; P2P {p2p[0]}/{p2p[1]}"
    )


def short_command(incident: dict[str, Any]) -> str:
    arguments = incident["pending_arguments"] or {}
    command = str(arguments.get("command", ""))
    return command.replace("\n", " ")[:240]


ornith_rows = "".join(
    f"<tr><td><strong>{html.escape(i['task'])}</strong><br>rep{i['rep']}</td>"
    f"<td>{minutes(i['session_span_s'])}</td>"
    f"<td><code>{html.escape(short_command(i))}</code><br><span class='badtext'>{minutes(i['pending_seconds_at_deadline'])} blocked</span></td>"
    f"<td>{html.escape(i['assessment']['state'])}</td>"
    f"<td>{html.escape(score_text(i))}<br>verifier: {html.escape(str(i['verifier_exit']))} ({minutes(i['verifier_elapsed_s'])})</td>"
    f"<td>{html.escape(i['assessment']['extension'])}</td></tr>"
    for i in ornith_incidents
)
gemma_rows = "".join(
    f"<tr><td><strong>{html.escape(i['task'])}</strong><br>rep{i['rep']}</td>"
    f"<td>{minutes(i['session_span_s'])}</td>"
    f"<td>{minutes(i['last_message_before_agent_deadline_s'])}</td>"
    f"<td>{html.escape(i['assessment']['state'])}</td>"
    f"<td>{html.escape(score_text(i))}</td>"
    f"<td>{html.escape(i['assessment']['extension'])}</td></tr>"
    for i in gemma_incidents
)
incident_cards = "".join(
    f"<article class='incident'><div class='incident-head'><span class='pill {'ornith' if i['model']=='Ornith' else 'gemma'}'>{i['model']}</span><strong>{html.escape(i['task'])} rep{i['rep']}</strong></div>"
    f"<p><strong>Observed mechanism:</strong> {html.escape(i['assessment']['mechanism'])}</p>"
    f"<p><strong>At termination:</strong> {i['turns']} turns, {i['tool_calls']} tool calls, {i['total_tokens']:,} reported tokens, {i['patch_bytes']:,} patch bytes; {html.escape(score_text(i))}.</p>"
    f"<p><strong>Counterfactual:</strong> {html.escape(i['assessment']['extension'])}</p></article>"
    for i in incidents
)

style = """
:root{--bg:#f4f7fb;--surface:#fff;--ink:#102033;--muted:#607086;--line:#d9e1ec;--blue:#335dff;--green:#178a5b;--red:#d0473f;--amber:#c58a00;--green-soft:#e7f7ef;--red-soft:#fdeceb;--amber-soft:#fff4d8;--shadow:0 20px 55px rgba(14,30,62,.08)}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 10% 0,rgba(51,93,255,.11),transparent 28%),linear-gradient(#f8fbff,var(--bg));color:var(--ink);font:15px/1.55 Inter,system-ui,sans-serif}.wrap{max-width:1260px;margin:auto;padding:28px 20px 60px}.hero,section{background:rgba(255,255,255,.95);border:1px solid var(--line);border-radius:28px;box-shadow:var(--shadow)}.hero{padding:38px}.eyebrow{display:inline-block;padding:7px 11px;border-radius:999px;background:#eef3ff;color:#1d3fb8;font-size:12px;font-weight:800;letter-spacing:.08em;text-transform:uppercase}h1{font-size:clamp(2.3rem,5vw,4.3rem);line-height:1.02;letter-spacing:-.045em;max-width:17ch;margin:14px 0}.lede{font-size:1.1rem;color:var(--muted);max-width:88ch}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:13px;margin-top:20px}.stat{background:var(--surface);border:1px solid var(--line);border-radius:18px;padding:17px}.stat strong{display:block;font-size:1.7rem;line-height:1.1}.stat span{color:var(--muted);font-size:12px;font-weight:700;text-transform:uppercase}section{margin-top:20px;padding:28px}h2{font-size:1.75rem;letter-spacing:-.03em;margin:0 0 6px}.section-lede{color:var(--muted);margin:0 0 18px}.callout{border-left:5px solid var(--blue);background:#f6f8ff;padding:15px 17px;border-radius:13px;margin:16px 0}.goodline{border-color:var(--green);background:var(--green-soft)}.warn{border-color:var(--amber);background:var(--amber-soft)}.badline{border-color:var(--red);background:var(--red-soft)}table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:11px 9px;border-bottom:1px solid var(--line);vertical-align:top}th{font-size:10px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}.table-wrap{overflow-x:auto}.pill{display:inline-flex;padding:5px 9px;border-radius:999px;font-weight:800;font-size:11px}.ornith{background:#e7f7ef;color:var(--green)}.gemma{background:#eef3ff;color:#244bbd}.badtext{color:var(--red);font-weight:800}.incident-grid{display:grid;grid-template-columns:1fr 1fr;gap:13px}.incident{border:1px solid var(--line);border-radius:16px;padding:15px}.incident p{margin:9px 0}.incident-head{display:flex;gap:9px;align-items:center}code{font:12px/1.4 ui-monospace,monospace;background:#edf1f7;padding:2px 5px;border-radius:5px;overflow-wrap:anywhere}.decision{display:grid;grid-template-columns:1fr 1fr;gap:16px}.choice{border:1px solid var(--line);border-radius:18px;padding:18px}.choice h3{margin-top:0}.muted{color:var(--muted)}a{color:var(--blue);font-weight:800}footer{text-align:center;color:var(--muted);padding:25px}@media(max-width:850px){.stats,.incident-grid,.decision{grid-template-columns:1fr 1fr}}@media(max-width:600px){.stats,.incident-grid,.decision{grid-template-columns:1fr}.hero,section{padding:22px}}
"""

page = f"""<!doctype html><html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>Ornith and Gemma timeout audit</title><style>{style}</style></head><body><div class='wrap'>
<header class='hero'><span class='eyebrow'>DeepSWE · 12_v2 · timeout incident audit</span><h1>Ornith did not need more time. It needed its tests to stop.</h1><p class='lede'>All six Ornith agent timeouts ended inside an unfinished, unbounded <code>bash</code> call. The model had actively worked for only 5–9 minutes; the final command then consumed the remaining 51–55 minutes. Four saved patches independently hung external verification. Gemma's two agent timeouts were different: no tool was stuck, and the model was still iterating near the one-hour boundary.</p><div class='stats'><div class='stat'><strong>6/6</strong><span>Ornith stuck in bash</span></div><div class='stat'><strong>51–55m</strong><span>blocked at deadline</span></div><div class='stat'><strong>4/6</strong><span>verifier hangs reproduced</span></div><div class='stat'><strong>2/2</strong><span>Gemma still model-working</span></div></div></header>
<section><h2>Executive verdict</h2><div class='callout badline'><strong>Do not increase Ornith's global agent timeout.</strong> Because the six calls had no tool-level timeout, 90 minutes would have produced the same patches after 90 minutes. This is not evidence that Ornith needs a longer thinking budget.</div><div class='callout goodline'><strong>One Gemma timeout was plausibly salvageable.</strong> LangChain rep2 preserved all 232 regression tests, passed 20/50 feature tests, and had identified its next two fixes. A modest extension could have improved partial credit. Gemma Mobly rep2 was still responding, but its implementation state was poor and unlikely to become a solve merely with more time.</div><div class='callout warn'><strong>Pi-check cannot interrupt the initial hang.</strong> It queues its re-audit as a follow-up at <code>agent_start</code>. If the first pass never settles, that follow-up never runs. In the previous Gemma pi-check comparison, {pi_check_delivery['not_delivered_before_timeout']} of {pi_check_delivery['timeouts']} timed-out cells never received the check; {pi_check_delivery['delivered_before_timeout']} timed out after receiving it.</div></section>
<section><h2>Ornith's six incidents</h2><p class='section-lede'>“Active span” is the time from the first to last persisted session message. “Blocked” is the inferred time from the final unfinished tool call to the 3,600-second agent deadline.</p><div class='table-wrap'><table><thead><tr><th>Cell</th><th>Active span</th><th>Final unfinished command</th><th>Diagnosis</th><th>Saved-patch grade</th><th>Would more global time help?</th></tr></thead><tbody>{ornith_rows}</tbody></table></div><div class='callout'><strong>The concurrency tasks are conclusive.</strong> LangChain reps 1–2 and Mobly reps 0 and 2 did not merely suffer a harness timeout: their saved patches later hung a separate verifier process for the full 35-minute cap. LangChain rep2 even printed a complete test summary before refusing to exit, consistent with leaked non-daemon threads.</div></section>
<section><h2>Gemma's two incidents</h2><p class='section-lede'>Neither ended in a pending tool call. RPC counts show a new turn had started but had not ended.</p><div class='table-wrap'><table><thead><tr><th>Cell</th><th>Session span</th><th>Last message before deadline</th><th>Diagnosis</th><th>Saved-patch grade</th><th>Would more time help?</th></tr></thead><tbody>{gemma_rows}</tbody></table></div><div class='callout warn'><strong>Separate verifier-only failure:</strong> Gemma LangChain rep0 completed its agent pass in {verifier_only['agent_wall_s']/60:.1f} minutes, then external verification hung on <code>test_invoke_returns_correct_result</code> for 35 minutes. That is a patch-induced deadlock, not evidence that Gemma's agent needed more time.</div></section>
<section><h2>Per-cell evidence</h2><div class='incident-grid'>{incident_cards}</div></section>
<section><h2>What this means for the Ornith pi-check run</h2><div class='decision'><div class='choice'><h3>Clean causal comparison</h3><p>Run pi-check unchanged with the same 3,600-second cell cap. Keep intention-to-treat as primary and separately report cells where the Re-audit marker was delivered.</p><p><strong>Advantage:</strong> isolates the pi-check effect against the existing baseline.</p><p><strong>Risk:</strong> pi-check cannot rescue a pre-check hanging command, and its second pass can create additional post-delivery timeouts.</p></div><div class='choice'><h3>Best practical configuration</h3><p>Create both a timeout-guarded stock baseline and timeout-guarded pi-check release. Apply the same automatic default timeout to any <code>bash</code> call that omits one, then compare those two fresh runs.</p><p><strong>Advantage:</strong> directly prevents the failure mode seen in all six Ornith timeouts while preserving a fair treatment contrast.</p><p><strong>Cost:</strong> requires rerunning both sides; comparing a guarded pi-check only against the old unguarded baseline would confound pi-check with the guard.</p></div></div><div class='callout goodline'><strong>My recommendation:</strong> if the immediate goal is to measure pi-check, keep the timeout at one hour and run the unchanged treatment, but predeclare delivery-aware analysis. Do not respond to a timeout spike by raising the global cap. If the goal shifts to the strongest usable Ornith config, use a paired tool-timeout guard on both baseline and pi-check.</div><div class='callout'><strong>Guard shape to investigate:</strong> Pi's <code>tool_call</code> event permits extensions to mutate <code>bash</code> input, and the built-in tool accepts an optional <code>timeout</code> field with no default. A config-local guard could set a default—likely 600 seconds—only when the model omitted one. That exact behavior should be model-free tested and versioned before any run.</div></section>
<section><h2>Evidence boundary</h2><p>Direct evidence: native session JSONL, unmatched tool-call IDs, RPC event counts, run-state timestamps, saved patches, result metrics, and verifier logs. Inference: whether a bounded command would have led the model to a solve. The report labels that counterfactual per cell and does not recompute benchmark scores.</p><p class='muted'>Machine-readable audit: <a href='timeout-audit.json'>timeout-audit.json</a></p></section>
<footer>Generated {datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')} from saved benchmark artifacts; no model calls or reruns.</footer></div></body></html>"""
OUTPUT_HTML.write_text(page)
print(OUTPUT_HTML)
print(
    json.dumps(
        {
            "incidents": len(incidents),
            "ornith_pending_bash": sum(
                incident["pending_tool"] == "bash" for incident in ornith_incidents
            ),
            "gemma_pending_tools": sum(
                incident["pending_tool_calls"] for incident in gemma_incidents
            ),
            "pi_check_delivery": pi_check_delivery,
        },
        indent=2,
    )
)

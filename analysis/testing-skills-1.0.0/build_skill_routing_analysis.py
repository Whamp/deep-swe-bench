#!/usr/bin/env python3
"""Build the testing-skills routing analysis from canonical result artifacts."""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
RESULTS_ROOT = Path("/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low")
BASELINE_ROOT = RESULTS_ROOT / "baseline"
SKILLS_ROOT = RESULTS_ROOT / "testing-skills@1.0.0"
SUBSET_PATH = REPOSITORY_ROOT / "subsets/36_v2.txt"
ANALYSIS_PATH = Path(__file__).with_name("skill-routing-analysis.json")
REPORT_PATH = REPOSITORY_ROOT / "reports/testing-skills-routing-36v2/index.html"
EXCLUDED_TASKS = {"wazero-multi-module-snapshots"}
SKILL_NAMES = ("testing", "fuzzing", "property-based-testing")

# These are predeclared from task contracts, not inferred from outcome.
OPPORTUNITY_CLASSIFICATION = {
    "eicrud-keyset-pagination-cursor": {
        "fit": "strong-pbt",
        "property": "Generate ordered records, directions, page sizes, and insertions; traversing cursors must produce each eligible record once, in order, and stop without a final cursor.",
        "fuzz": "Malformed Base64/JSON cursors are a bounded parser surface, but examples cover the named rejection cases more directly.",
    },
    "fd-deterministic-multi-key-sorting": {
        "fit": "strong-pbt",
        "property": "Generate entries and sort-key combinations; assert comparator ordering, determinism, reverse symmetry, and seeded-random reproducibility.",
        "fuzz": "Comparator input is structured rather than byte-oriented; property generation is the better search mechanism.",
    },
    "dateutil-rfc5545-timezone-interop": {
        "fit": "strong-pbt",
        "property": "Generate supported recurrence/timezone combinations; string/repr reconstruction must preserve behavior and normalized fields.",
        "fuzz": "Text parsing exists, but the observed failures are semantic reconstruction invariants rather than crashes.",
    },
    "dynamodb-toolbox-conditional-attribute-requirements": {
        "fit": "strong-pbt",
        "property": "Generate nested schema variants; DTO and schema conversions must round-trip conditional requirements across every schema constructor.",
        "fuzz": "The domain is typed schema trees with a compact round-trip oracle, which favors property testing.",
    },
    "langchain-request-coalescing": {
        "fit": "strong-pbt",
        "property": "Generate operation schedules across sync/async invoke, stream, batch, clear, and completion; each active key executes once and all waiters settle consistently.",
        "fuzz": "Concurrency schedules need stateful generation, not coverage-guided byte mutation.",
    },
    "etree-xml-diff-patch": {
        "fit": "strong-pbt",
        "property": "Generate XML tree pairs; applying a diff must reconstruct the target, and merge conflict classification must preserve explicit modify/delete cases.",
        "fuzz": "Malformed XML is fuzzable, but the feature's strongest oracle is diff/patch equivalence.",
    },
    "superjson-error-stack-serialization": {
        "fit": "strong-pbt-counterexample",
        "property": "Generate option combinations, nested causes, containers, and newline/path forms; serialize/deserialize must preserve the configured normalized representation.",
        "fuzz": "Untrusted stack strings are fuzzable, but option-combination semantics dominate this contract.",
    },
    "yjs-map-conflict-detection": {
        "fit": "strong-pbt-counterexample",
        "property": "Generate interleaved map updates and replica orderings; conflict sets and convergence must be permutation-invariant.",
        "fuzz": "Operation sequences and convergence oracles favor stateful property testing.",
    },
    "participle-grammar-conflict-analysis": {
        "fit": "pbt-and-fuzz",
        "property": "Generate small grammar ASTs with known ambiguity classes; clean grammars must remain clean and injected overlaps must classify correctly.",
        "fuzz": "Grammar/parser infrastructure is coverage-guided-fuzzable, but the requested analyzer needs a semantic oracle to detect false positives.",
    },
    "httpx-multipart-response-parsing": {
        "fit": "fuzz-counterexample",
        "property": "Generate multipart parts and chunk boundaries; parse/re-encode observations must preserve headers and bodies under supported line endings.",
        "fuzz": "Malformed framing, split CRLF, boundary-like lines, and header continuations are a strong parser fuzz target.",
    },
    "katex-multicolumn-array-spans": {
        "fit": "pbt-and-fuzz",
        "property": "Generate bounded array shapes and spans; column accounting, separators, and delimiters must satisfy structural invariants.",
        "fuzz": "The TeX parser accepts untrusted syntax, though DOM structure needs a semantic oracle beyond no-crash fuzzing.",
    },
    "sql-formatter-bigquery-pipe-formatting": {
        "fit": "pbt-and-fuzz-counterexample",
        "property": "Generate supported pipe-query AST combinations; formatting should be idempotent and reparsing should preserve structure.",
        "fuzz": "Lexer/parser/formatter boundaries are suitable for coverage-guided malformed-input exploration.",
    },
    "meriyah-explicit-resource-declarations": {
        "fit": "pbt-and-fuzz",
        "property": "Generate valid and invalid declaration placements; parse results and errors must respect context and grammar invariants.",
        "fuzz": "A JavaScript parser is a classic fuzz surface, but feature-specific AST/error oracles are still required.",
    },
}


def read_result_cells(
    root: Path, tasks: set[str]
) -> dict[tuple[str, int], tuple[Path, dict]]:
    """Return canonical result cells keyed by task and rep."""
    cells: dict[tuple[str, int], tuple[Path, dict]] = {}
    for result_path in root.glob("*/rep*/result.json"):
        task = result_path.parts[-3]
        rep = int(result_path.parts[-2][3:])
        if task in tasks and rep < 3:
            cells[(task, rep)] = (
                result_path.parent,
                json.loads(result_path.read_text()),
            )
    expected = len(tasks) * 3
    if len(cells) != expected:
        raise RuntimeError(
            f"Expected {expected} cells under {root}, found {len(cells)}"
        )
    return cells


def session_text(cell_path: Path) -> str:
    """Return concatenated native Pi session records for one cell."""
    return "\n".join(
        path.read_text(errors="replace")
        for path in sorted((cell_path / "session").glob("*.jsonl"))
    )


def patch_paths(cell_path: Path) -> list[str]:
    """Return changed paths parsed from a model patch."""
    patch_path = cell_path / "artifacts/model.patch"
    if not patch_path.exists():
        return []
    return re.findall(
        r"^\+\+\+ b/(.+)$", patch_path.read_text(errors="replace"), re.MULTILINE
    )


def is_test_path(path: str) -> bool:
    """Return whether a changed path uses a conventional test filename or directory."""
    return bool(
        re.search(
            r"(^|/)(test|tests|spec)|[._-](test|tests|spec)\.", path, re.IGNORECASE
        )
    )


def failed_verifier_tests(cell_path: Path) -> list[str]:
    """Return failed CTRF test names for one cell."""
    ctrf_path = cell_path / "verifier/ctrf.json"
    if not ctrf_path.exists():
        return []
    report = json.loads(ctrf_path.read_text())
    results = report.get("results")
    if not isinstance(results, dict):
        raise TypeError(f"CTRF report has no results object: {ctrf_path}")
    tests = results.get("tests")
    if not isinstance(tests, list):
        raise TypeError(f"CTRF report has no tests list: {ctrf_path}")
    return [
        test.get("name", "unnamed test")
        for test in tests
        if test.get("status") == "failed"
    ]


def skill_tool_call_positions(cell_path: Path) -> dict[str, int | None]:
    """Return each skill's zero-based position in the session tool-call sequence."""
    positions = {name: None for name in SKILL_NAMES}
    tool_index = 0
    for session_path in sorted((cell_path / "session").glob("*.jsonl")):
        for line in session_path.read_text(errors="replace").splitlines():
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            message = record.get("message")
            if not isinstance(message, dict):
                continue
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for item in content:
                if item.get("type") != "toolCall":
                    continue
                arguments = str(item.get("arguments", {}))
                for name in SKILL_NAMES:
                    if (
                        positions[name] is None
                        and f"/arm/skills/{name}/SKILL.md" in arguments
                    ):
                        positions[name] = tool_index
                tool_index += 1
    return positions


def skill_reference_reads(session: str) -> Counter[str]:
    """Count testing-skill reference reads in a native session."""
    return Counter(re.findall(r"/arm/skills/testing/references/([^\"\\\s]+)", session))


def build_analysis() -> dict:
    """Build the complete routing-analysis data model."""
    tasks = set(SUBSET_PATH.read_text().split()) - EXCLUDED_TASKS
    baseline = read_result_cells(BASELINE_ROOT, tasks)
    skills = read_result_cells(SKILLS_ROOT, tasks)
    ledger = []
    skill_counts = Counter()
    advertised_counts = Counter()
    reference_counts = Counter()
    testing_positions = []
    baseline_test_patches = 0
    skills_test_patches = 0

    for task in sorted(tasks):
        for rep in range(3):
            baseline_path, baseline_result = baseline[(task, rep)]
            skills_path, skills_result = skills[(task, rep)]
            system_prompt = (
                skills_path / "initial_context/system_prompt.txt"
            ).read_text(errors="replace")
            session = session_text(skills_path)
            positions = skill_tool_call_positions(skills_path)
            for name in SKILL_NAMES:
                advertised_counts[name] += f"<name>{name}</name>" in system_prompt
                skill_counts[name] += positions[name] is not None
            if positions["testing"] is not None:
                testing_positions.append(positions["testing"])
            reference_counts.update(skill_reference_reads(session))
            baseline_test_paths = [
                path for path in patch_paths(baseline_path) if is_test_path(path)
            ]
            skills_test_paths = [
                path for path in patch_paths(skills_path) if is_test_path(path)
            ]
            baseline_test_patches += bool(baseline_test_paths)
            skills_test_patches += bool(skills_test_paths)
            baseline_solved = baseline_result.get("reward_binary") == 1
            skills_solved = skills_result.get("reward_binary") == 1
            ledger.append(
                {
                    "task": task,
                    "rep": rep,
                    "baseline_solved": baseline_solved,
                    "skills_solved": skills_solved,
                    "baseline_partial": baseline_result.get("reward_partial"),
                    "skills_partial": skills_result.get("reward_partial"),
                    "testing_position": positions["testing"],
                    "skills_test_paths": skills_test_paths,
                    "failed_tests": failed_verifier_tests(skills_path),
                    "opportunity": OPPORTUNITY_CLASSIFICATION.get(task),
                }
            )

    baseline_solves = sum(row[1].get("reward_binary") == 1 for row in baseline.values())
    skills_solves = sum(row[1].get("reward_binary") == 1 for row in skills.values())
    opportunity_tasks = set(OPPORTUNITY_CLASSIFICATION)
    opportunity_cells = [row for row in ledger if row["task"] in opportunity_tasks]
    opportunity_failures = [
        row for row in opportunity_cells if not row["skills_solved"]
    ]
    testing_positions.sort()
    return {
        "scope": {
            "model": "openai-codex/gpt-5.6-sol",
            "thinking": "low",
            "tasks": len(tasks),
            "reps": 3,
            "paired_cells": len(ledger),
            "excluded": sorted(EXCLUDED_TASKS),
            "roles": "same-model config control: legacy Pi baseline vs testing-skills@1.0.0",
        },
        "delivery": {
            "advertised": dict(advertised_counts),
            "read": dict(skill_counts),
            "testing_first_tool_calls": sum(
                position == 0 for position in testing_positions
            ),
            "testing_median_tool_position": testing_positions[
                len(testing_positions) // 2
            ],
            "testing_references": dict(reference_counts),
        },
        "behavior": {
            "baseline_cells_with_test_patch": baseline_test_patches,
            "skills_cells_with_test_patch": skills_test_patches,
            "baseline_solves": baseline_solves,
            "skills_solves": skills_solves,
            "net_solves": skills_solves - baseline_solves,
        },
        "opportunities": {
            "classified_tasks": len(opportunity_tasks),
            "classified_cells": len(opportunity_cells),
            "unsolved_classified_cells": len(opportunity_failures),
            "classification": OPPORTUNITY_CLASSIFICATION,
        },
        "ledger": ledger,
    }


def outcome_pill(baseline_solved: bool, skills_solved: bool) -> str:
    """Render a paired outcome label."""
    if not baseline_solved and skills_solved:
        return '<span class="pill good">gain</span>'
    if baseline_solved and not skills_solved:
        return '<span class="pill bad">loss</span>'
    return '<span class="pill neutral">same</span>'


def render_html(analysis: dict) -> str:
    """Render the self-contained skill-routing report."""
    delivery = analysis["delivery"]
    behavior = analysis["behavior"]
    ledger = analysis["ledger"]
    task_rows = []
    for task in sorted({row["task"] for row in ledger}):
        rows = [row for row in ledger if row["task"] == task]
        baseline_count = sum(row["baseline_solved"] for row in rows)
        skills_count = sum(row["skills_solved"] for row in rows)
        opportunity = OPPORTUNITY_CLASSIFICATION.get(task)
        fit = opportunity["fit"] if opportunity else "not preclassified"
        task_rows.append(
            f"<tr><td><code>{html.escape(task)}</code></td><td>{baseline_count}/3</td>"
            f"<td>{skills_count}/3</td><td>{skills_count - baseline_count:+d}</td>"
            f"<td>{html.escape(fit)}</td></tr>"
        )

    ledger_rows = []
    for row in ledger:
        failed = (
            "<br>".join(html.escape(name) for name in row["failed_tests"][:3]) or "—"
        )
        test_paths = (
            "<br>".join(
                f"<code>{html.escape(path)}</code>"
                for path in row["skills_test_paths"][:3]
            )
            or "—"
        )
        ledger_rows.append(
            f"<tr><td><code>{html.escape(row['task'])}</code></td><td>{row['rep']}</td>"
            f"<td>{int(row['baseline_solved'])}</td><td>{int(row['skills_solved'])}</td>"
            f"<td>{outcome_pill(row['baseline_solved'], row['skills_solved'])}</td>"
            f"<td>{row['testing_position'] if row['testing_position'] is not None else '—'}</td>"
            f"<td>{test_paths}</td><td class='failure'>{failed}</td></tr>"
        )

    opportunity_rows = []
    for task, opportunity in OPPORTUNITY_CLASSIFICATION.items():
        rows = [row for row in ledger if row["task"] == task]
        solved = sum(row["skills_solved"] for row in rows)
        failures = sorted({name for row in rows for name in row["failed_tests"]})
        failure_text = (
            "<br>".join(html.escape(name) for name in failures[:4])
            or "All treatment reps solved"
        )
        opportunity_rows.append(
            f"<tr><td><code>{html.escape(task)}</code><br><span class='tag'>{html.escape(opportunity['fit'])}</span></td>"
            f"<td>{solved}/3</td><td>{html.escape(opportunity['property'])}</td>"
            f"<td>{html.escape(opportunity['fuzz'])}</td><td class='failure'>{failure_text}</td></tr>"
        )

    references = delivery["testing_references"]
    reference_text = (
        ", ".join(
            f"{html.escape(name)} × {count}"
            for name, count in sorted(references.items())
        )
        or "none"
    )
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 32 32%22><rect width=%2232%22 height=%2232%22 rx=%228%22 fill=%22%232563eb%22/><path d=%22M8 16h16M16 8v16%22 stroke=%22white%22 stroke-width=%223%22/></svg>">
<title>Why fuzzing and property testing never activated</title><style>
:root{{--bg:#f4f7fb;--surface:#fff;--ink:#172033;--muted:#667085;--blue:#2563eb;--green:#138a5b;--red:#c43d4b;--amber:#b7791f;--line:#dce3ed}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:15px/1.5 ui-sans-serif,system-ui,-apple-system,sans-serif}}main{{max-width:1280px;margin:auto;padding:42px 24px 64px}}.hero{{background:linear-gradient(135deg,#15223b,#244b83);color:#fff;border-radius:22px;padding:38px;box-shadow:0 16px 45px #15223b22}}h1{{font-size:clamp(2rem,5vw,3.6rem);line-height:1.02;margin:.25rem 0 1rem;max-width:18ch}}h2{{margin:34px 0 14px}}h3{{margin:22px 0 8px}}.eyebrow{{text-transform:uppercase;letter-spacing:.14em;font-weight:800;color:#9cc2ff;font-size:.78rem}}.subtitle{{max-width:880px;color:#d9e7ff;font-size:1.12rem}}.pills{{display:flex;flex-wrap:wrap;gap:8px;margin-top:20px}}.pill,.tag{{display:inline-block;border-radius:999px;padding:4px 9px;font-size:.76rem;font-weight:800;white-space:nowrap}}.hero .pill{{background:#ffffff18;color:#fff;border:1px solid #ffffff30}}.pill.good{{background:#dcf7ea;color:#08734a}}.pill.bad{{background:#fee7ea;color:#a72f3d}}.pill.caution,.tag{{background:#fff0d2;color:#8b5b0c}}.pill.neutral{{background:#e8eef7;color:#475467}}.stats{{display:grid;grid-template-columns:repeat(5,1fr);gap:14px;margin:20px 0}}.stat{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px}}.stat b{{display:block;font-size:1.8rem;line-height:1.1}}.stat span{{color:var(--muted)}}.surface{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:8px 20px 18px;overflow:auto}}table{{border-collapse:collapse;width:100%}}th,td{{text-align:left;vertical-align:top;padding:10px 9px;border-bottom:1px solid var(--line)}}th{{font-size:.72rem;text-transform:uppercase;letter-spacing:.07em;color:var(--muted)}}code{{font-size:.8rem}}.callout{{margin-top:18px;border-left:5px solid var(--blue);background:var(--surface);padding:18px 20px;border-radius:8px}}.callout.caution{{border-color:var(--amber)}}.callout.bad{{border-color:var(--red)}}.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:16px}}.card{{background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:20px}}.card p:last-child{{margin-bottom:0}}.failure{{font-size:.8rem;color:#68404a;min-width:260px}}footer{{color:var(--muted);margin-top:28px;font-size:.84rem}}@media(max-width:900px){{.stats{{grid-template-columns:repeat(2,1fr)}}.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<section class="hero"><div class="eyebrow">Skill-routing diagnosis · 105 clean paired cells</div><h1>The router stopped at “testing”</h1><p class="subtitle">Fuzzing and property-based testing were delivered correctly. GPT-5.6 Sol low selected the broad testing skill early, then treated its specialized routes as optional reading rather than branches to evaluate.</p><div class="pills"><span class="pill">105/105 advertised</span><span class="pill">testing 103/105</span><span class="pill">fuzzing 0/105</span><span class="pill">property testing 0/105</span></div></section>
<section class="stats"><div class="stat"><b>49</b><span>cells read testing first</span></div><div class="stat"><b>2nd</b><span>median testing tool position</span></div><div class="stat"><b>35%→83%</b><span>cells changing test files</span></div><div class="stat"><b>{analysis["opportunities"]["classified_tasks"]}</b><span>preclassified opportunity tasks</span></div><div class="stat"><b>{behavior["baseline_solves"]}→{behavior["skills_solves"]}</b><span>clean solves, excluding wazero</span></div></section>
<div class="callout bad"><strong>Verdict:</strong> This is a routing-design failure, especially for property-based testing. The model saw every skill and repeatedly read <code>testing/SKILL.md</code>, but no mechanism required it to evaluate the specialized branches. The bundle increased test-file edits without increasing test-search diversity.</div>
<div class="callout caution"><strong>Causal limit:</strong> Zero invocation does not prove either specialized skill would improve score. Strong opportunity tasks include 3/3 wins such as SuperJSON, HTTPX, SQL Formatter, and Yjs. The evidence supports a missed activation mechanism and targeted A/B tests—not a claim of guaranteed solve gains.</div>
<h2>Why activation stopped</h2><div class="grid">
<div class="card"><h3>1. A broad skill captured the task</h3><p><code>testing</code> overlaps both specialist descriptions and appears first. It was the first tool call in 49 cells and the median second tool call across 103 reads. The model committed before inspecting dependencies or test architecture.</p></div>
<div class="card"><h3>2. “Routes” were prose, not control flow</h3><p>The testing skill says “Load” property testing for broad domains and fuzzing for parser/protocol risk. Pi does not auto-chain skills. The system prompt only asks the model to read matching skills, and no completion check asks which routes it considered.</p></div>
<div class="card"><h3>3. Language references won the tie</h3><p>After reading testing, the model read language or integration references but never a specialist: {reference_text}. These links are concrete file reads inside the chosen skill; the sibling skills require a second top-level selection.</p></div>
<div class="card"><h3>4. The benchmark rewards immediate examples</h3><p>The prompts request implementation, not a fuzz campaign or quantified property. The skills treatment changed test files in {behavior["skills_cells_with_test_patch"]}/105 cells versus {behavior["baseline_cells_with_test_patch"]}/105 baseline cells, but usually wrote examples matching named requirements.</p></div>
<div class="card"><h3>5. Specialist entry costs are conservative</h3><p>Property testing asks for a concrete domain, oracle, counterfeit, framework, and dependency policy. Fuzzing asks for target, engine, budget, corpus, and regression path. No trajectory surfaced an installed property/fuzz framework. Under time pressure, examples were cheaper.</p></div>
<div class="card"><h3>6. Fuzzing had fewer direct score opportunities</h3><p>Several tasks exposed parsers, but observed failures were mostly semantic invariants: pagination traversal, DTO round trips, reconstruction, and concurrency schedules. Property testing has the stronger immediate case; fuzzing needs a narrower parser-focused experiment.</p></div>
</div>
<h2>Opportunity matrix</h2><p>Classification was fixed from task contracts before considering each cell's result. “Counterexample” means the task solved despite non-use.</p><div class="surface"><table><thead><tr><th>Task / fit</th><th>Skills solves</th><th>Property-testing leverage</th><th>Fuzzing leverage</th><th>Observed verifier evidence</th></tr></thead><tbody>{"".join(opportunity_rows)}</tbody></table></div>
<h2>What the hidden tests reveal</h2><div class="grid">
<div class="card"><h3>Cursor pagination · 0/3</h3><p>Every rep passed only 8/14 feature tests. Failures required full traversal without gaps/duplicates, correct final-page termination, multi-column ordering, and insertion stability—the exact shape of a generated stateful property.</p></div>
<div class="card"><h3>DynamoDB schemas · 0/3</h3><p>Every rep passed 30/31 feature tests and failed the same <code>anyOf DTO round-trip</code>. The treatment wrote example tests but did not generalize the round-trip across schema constructors.</p></div>
<div class="card"><h3>LangChain coalescing · 0/3</h3><p>Failures clustered in batch, async batch, waiter cancellation, consecutive completion, and stats. The agent wrote hand-scheduled thread/async examples; a state-machine schedule model could search interactions systematically.</p></div>
<div class="card"><h3>Counterexamples matter</h3><p>HTTPX's malformed multipart parser, SQL Formatter's parser/formatter, SuperJSON's round trips, and Yjs's concurrent state all solved 3/3 without specialist reads. Specialist activation should be selective and measured.</p></div>
</div>
<h2>Recommended A/Bs before changing the release</h2><div class="surface"><table><thead><tr><th>Experiment</th><th>Trigger</th><th>Action</th><th>Completion criterion</th><th>Candidate tasks</th></tr></thead><tbody>
<tr><td><strong>PBT route checkpoint</strong></td><td>Task has a broad structured domain plus compact invariant</td><td>At the end of testing skill section 1, require one line: <code>PBT leverage: domain / risk / oracle</code>; read the specialist when all three are concrete.</td><td>Specialist is read and produces at least one discriminating property without adding an unauthorized dependency.</td><td>eicrud, DynamoDB Toolbox, dateutil, LangChain, fd</td></tr>
<tr><td><strong>Direct PBT description</strong></td><td>Prompt says round-trip, cursor traversal, ordering combinations, schedules, or convergence</td><td>Strengthen the top-level description with those exact trigger phrases and state that feature implementation counts as test work.</td><td>Higher specialist activation on predeclared tasks without activation on explicit-table counterexamples.</td><td>Same five tasks plus etree</td></tr>
<tr><td><strong>Parser fuzz checkpoint</strong></td><td>New parser/decoder consumes malformed or chunked untrusted input</td><td>Require a bounded fuzz-campaign decision: target, oracle, existing engine, and 30–60 second smoke budget; skip explicitly if any field is absent.</td><td>Fuzzing activates only when an existing engine and meaningful oracle exist.</td><td>HTTPX, Participle, KaTeX, Meriyah, SQL Formatter</td></tr>
</tbody></table></div>
<div class="callout"><strong>Decision:</strong> Do not simply make all three skills mandatory. First test a routing checkpoint on a small same-model subset containing both missed-leverage failures and solved counterexamples. The desired change is better test selection, not more test code.</div>
<h2>Task-level outcomes</h2><div class="surface"><table><thead><tr><th>Task</th><th>Baseline</th><th>Skills</th><th>Δ</th><th>Opportunity class</th></tr></thead><tbody>{"".join(task_rows)}</tbody></table></div>
<h2>Complete 105-cell ledger</h2><div class="surface"><table><thead><tr><th>Task</th><th>Rep</th><th>Baseline</th><th>Skills</th><th>Pair</th><th>Testing tool position</th><th>Treatment test paths</th><th>Failed verifier tests</th></tr></thead><tbody>{"".join(ledger_rows)}</tbody></table></div>
<h2>Evidence ledgers</h2><div class="grid"><div class="card"><h3>CodeGraph evidence</h3><p>The structural index identifies <code>harness/run.py:pi_cmd</code> as the skill-launch seam. It is called by <code>run_cell</code>. CodeGraph cannot observe runtime skill selection.</p></div><div class="card"><h3>Source-read interpretation</h3><p><code>pi_cmd</code> emits one explicit <code>--skill /arm/skills/&lt;name&gt;</code> per directory. The system prompt lists all three paths. The testing skill's route table points to sibling skills through prose.</p></div><div class="card"><h3>Artifact proof</h3><p>All 105 prompts advertise all three skills. Native sessions show 103 testing reads and zero specialist reads. CTRF reports supply the exact hidden-test failures in this report.</p></div><div class="card"><h3>Scope and exclusions</h3><p>Same model and thinking, 35 tasks × 3 reps. <code>wazero</code> is excluded because both 4 GiB and 8 GiB treatment attempts recorded OOM kills. Legacy baseline provenance is accepted per operator direction.</p></div></div>
<footer>Generated from canonical <code>result.json</code>, native sessions, model patches, prompts, and CTRF verifier reports. Data: <code>analysis/testing-skills-1.0.0/skill-routing-analysis.json</code>.</footer>
</main></body></html>"""


def main() -> None:
    """Write the JSON evidence model and self-contained HTML report."""
    analysis = build_analysis()
    ANALYSIS_PATH.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(render_html(analysis))
    print(f"wrote {ANALYSIS_PATH}")
    print(f"wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()

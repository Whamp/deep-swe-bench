# Task for delegate

DESIGN IT TWICE — you are ONE of four parallel agents each designing a DIFFERENT interface for the same new Python module. Produce ONE interface design per the CONSTRAINT at the bottom. Focus on the INTERFACE, not implementation; a usage sketch is enough.

=== DOMAIN VOCAB (CONTEXT.md — use exactly) ===
config (coding-agent setup; the variable a comparison changes); model (the LLM); model-leaf (path-identity of a model = last "/"-segment, e.g. openrouter/deepseek/deepseek-v4-flash → deepseek-v4-flash; EXECUTOR-ONLY in results, single-sourced by lib.model_leaf(model)); thinking (off/minimal/low/medium/high/xhigh); task (DeepSWE task id string); rep (numbered repetition; atomic unit = one agent run + one verifier grade); agent (OVERLOADED: the CLI binary pi, OR the subject under test pi|omp — BOTH write the SAME tree, so agent is ORTHOGONAL to the address; the interface must NOT take an agent param).

=== DESIGN VOCAB (codebase-design SKILL.md — use exactly) ===
module, interface (signature + invariants + ordering + error modes + perf), implementation, depth (leverage at the interface), seam, adapter, leverage, locality. Principles: deletion test (delete it — complexity vanishes = pass-through; reappears across N callers = earns its keep), the interface is the test surface, one adapter = hypothetical seam / two adapters = real.

=== THE MODULE'S JOB (decided; do not relitigate) ===
Pure-ADDRESS module: derives PATHS, checks EXISTENCE, ITERATES. Does NOT write files (result.json/results.jsonl writing stays in the cell runner). CONSUMES lib.model_leaf(model) one-way (results_tree → lib); does NOT re-expose leaf(); interface is path-shaped. Centralizes the grammar so all callers derive addresses identically.

=== ADDRESS GRAMMAR (leaf = lib.model_leaf(model)) ===
tree root: results/<leaf>/<thinking>/
tree file: results/<leaf>/<thinking>/results.jsonl
log file:  results/<leaf>/<thinking>/logs/{task}__{config}__rep{rep}.log
cell root: results/<leaf>/<thinking>/<config>/<task>/rep<N>/
cell files: <cell>/result.json , <cell>/transient_error.json
cell subdirs: <cell>/artifacts/ , <cell>/verifier/ , <cell>/logs/ , <cell>/session/

=== INVARIANTS THE INTERFACE MUST PROTECT (why the module exists) ===
1. resume-by-existence: the path a WRITER creates (cell/result.json) ≡ the path a READER existence-checks. (ADR-0001's incident: model-leaf divergence silently re-ran everything.)
2. model-leaf immutability: leaf derived one way everywhere.
3. executor-only in results: never +advisor.

=== CALL SITES ===
Writers (single-cell, fix all 5 keys): harness/run.py::run_cell (~L434), harness/run_omp.py::run_cell (~L254) — build cell dir+subdirs, write result.json, append results.jsonl.
Reader/batch (fix model+thinking): harness/run_batch.py — per-cell result.json existence (L75), per-cell log path (L79), config-level has-any-results glob (L83-84).
Reader/analysis (fix model+thinking, iterate): harness/analyze.py — root + glob over config/task/rep (L27,30).
Dashboard relative id: harness/run_state.py uses RELATIVE f"{task}/{config}/rep{rep}" (L108) — a different relative address; note it, interface need not own it but must not contradict it.

=== DEPENDENCY CATEGORIES ===
Path derivation = Category 1 (in-process, pure). Existence/iteration = Category 2 (local-substitutable: filesystem, pytest tmp_path). NO Category 3/4 → NO ports & adapters warranted.

=== STYLE ===
Python 3, pathlib.Path, plain functions + simple frozen dataclasses, REPO = HERE.parent. No frameworks.

You MAY read /home/will/evals/deep-swe-bench/harness/{run,run_omp,run_batch,analyze,lib,run_state}.py, CONTEXT.md, docs/adr/0001-*.md to verify — but the brief is self-contained.

=== OUTPUT (all 5, concisely) ===
1. Interface — types, methods, params, PLUS invariants, ordering, error modes.
2. Usage example — BOTH a single-cell writer (run.py style) AND a cross-cell reader (analyze.py style).
3. What the implementation hides behind the seam.
4. Dependency strategy & adapters (cite categories; argue no-port).
5. Trade-offs — where leverage is high/thin; apply the deletion test to YOUR interface.

=== YOUR CONSTRAINT (makes yours different) ===
RADICAL alternative — design the most radically different interface you can still justify to a pragmatic Python harness maintainer. Deliberately AVOID the obvious OOP ResultsTree→CellAddress shape. Candidates to consider (or better, your own): a DECLARATIVE path-grammar/template object where the grammar is data; a FUNCTIONAL approach over a frozen Cell NamedTuple with module-level pure functions; a fluent BUILDER DSL (Results.at(model,thinking).config(c).cell(task,rep).result_json); or a path-projection over a single RootSpec. Justify why your radical shape has MORE depth or better locality than the OOP default.

## Acceptance Contract
Acceptance level: checked
Completion is not accepted from prose alone. End with a structured acceptance report.

Criteria:
- criterion-1: Implement the requested change without widening scope

Required evidence: changed-files, tests-added, commands-run, residual-risks, no-staged-files

Finish with a fenced JSON block tagged `acceptance-report` in this shape:
Use empty arrays when no items apply; array fields contain strings unless object entries are shown.
```acceptance-report
{
  "criteriaSatisfied": [
    {
      "id": "criterion-1",
      "status": "satisfied",
      "evidence": "specific proof"
    }
  ],
  "changedFiles": [
    "src/file.ts"
  ],
  "testsAddedOrUpdated": [
    "test/file.test.ts"
  ],
  "commandsRun": [
    {
      "command": "command",
      "result": "passed",
      "summary": "short result"
    }
  ],
  "validationOutput": [
    "validation output or concise summary"
  ],
  "residualRisks": [
    "none"
  ],
  "noStagedFiles": true,
  "diffSummary": "short description of the diff",
  "reviewFindings": [
    "blocker: file.ts:12 - issue found, or no blockers"
  ],
  "manualNotes": "anything else the parent should know"
}
```
# 0005 — Legitimize `cell` as the rep's on-disk container

## Context

ADR-0001 retired "arm" and pruned "run" (as a noun) and also listed `cell` under
`rep`'s `_Avoid_` in CONTEXT.md, intending "rep" as the single term for the
atomic unit. The avoidance never reached the code: "cell" remains the
load-bearing word for a rep's *on-disk container* — `run_cell`,
`cell = REPO/"results"/...`, the `-v {cell}:/out` Docker mount — with roughly
140 uses across `harness/*.py`.

A 2026-07 architecture review (Candidate A: a results-tree address module)
crystallized a `Cell` type for the address of one rep. Naming it `Cell` collides
with CONTEXT's `_Avoid_: cell`, forcing a choice: honor the glossary (rename the
type and, for consistency, the code), or bring the glossary into line with the
code.

The review also made explicit a distinction CONTEXT had collapsed: **rep** is the
run (the logical, numbered unit); **cell** is that rep's on-disk container —
where its `result.json`, `artifacts/`, `logs/`, and `session/` live. They are
different concepts that share an identity `(model-leaf, thinking, config, task,
rep)`.

## Decision

Legitimize **cell** as a first-class CONTEXT.md term: the on-disk container of a
rep, distinct from rep (the unit). Trim `rep`'s `_Avoid_` from `cell, trial` to
`trial` only. Keep the code's `cell` / `run_cell` naming as-is and name the
results-tree address module's type `Cell`.

## Considered options

- **Keep `cell`; refine CONTEXT (chosen).** The code uses "cell" ~140× for
  exactly this concept; renaming is out of scope for the address module and
  would be large, risky churn. The rep-vs-cell distinction is real and worth a
  term, and "cell" matches upstream Pier.
- **Rename the type `Rep`.** Rejected: `rep` is already an `int` parameter
  throughout (`--rep`, `rep=3`); a `Rep` type clashes with the count.
- **Rename the type `RepAddress` / `RepDir`.** Rejected: CONTEXT-safe, but
  splits one concept across two words — the module says `RepAddress` while the
  code keeps `cell` / `run_cell`. That half-rename is the same anti-pattern
  ADR-0004 rejected for `arm` (`config_cfg` in code, `arm_*` on disk).
- **Full codebase rename `cell` → some `rep`-derived term.** Rejected: enormous
  churn for a word that is, on the merits, the right term for the container.

## Consequences

- "cell" is no longer an avoided term; new code may use it freely for the
  container/address concept.
- The distinction is now explicit: rep = the unit (the run), cell = its
  container. Don't call the unit a "cell"; don't call the container a "rep."
- The results-tree address module's `Cell` type is this concept.
- `trial` remains avoided (synonym for the rep unit).

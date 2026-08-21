# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase.

## Layout

This is a **single-context** repo.

- Read `CONTEXT.md` at the repo root for project vocabulary.
- Read relevant ADRs under `docs/adr/` before changing architecture, harness behavior, result layout, vocabulary, or config conventions.

## Before exploring, read these

- **`CONTEXT.md`** at the repo root.
- **`docs/adr/`** — read ADRs that touch the area you're about to work in.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The `/domain-modeling` skill creates them lazily when terms or decisions actually get resolved.

## File structure

```text
/
├── CONTEXT.md
├── docs/
│   ├── adr/          (numbered sequentially; the directory is the index)
│   └── agents/
└── ...
```

## Use the glossary's vocabulary

When your output names a domain concept — in an issue title, refactor proposal, hypothesis, test name, report, or analysis — use the term as defined in `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal: either you're inventing language the project doesn't use, or there's a real gap to resolve with `/domain-modeling`.

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0001 (directory and vocabulary reorganization) — but worth reopening because…_

## Freshness note

If `CONTEXT.md` appears stale, prefer the latest repo state plus accepted ADRs as evidence, and note the discrepancy. Do not silently introduce new domain language; update `CONTEXT.md` deliberately when vocabulary changes.

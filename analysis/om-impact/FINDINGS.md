# om-impact prototypes: P1 / P2 / P4 — findings & recommendation

**Question:** Can codegraph blast-radius signal be carried into the observational-memory
stream, and which mechanism survives best? Three prototypes, one shared metric
(`impact_capture_rate` = fraction of a task's gold caller/edge set named in the
memory output), scored on a matched 21-case subset (12 DeepSWE tasks, go/py/ts).

**Status:** eval-only. No session/ledger/result mutated. All artifacts under
`analysis/om-impact/`.

## Prototypes

| ID | Mechanism | LLM? | Cost |
|----|-----------|------|------|
| **P1** | Observer + 2nd tool `graph_callers` (codegraph `where <sym> -T -j`); prompt invites use | yes (gpt-5.4-mini:low) | per-call |
| **P2** | Hook computes a `batch fn-impact`-style digest of touched files, appends to observer input; STOCK observer, no new tool | yes (gpt-5.4-mini:low) | digest + per-call |
| **P4** | Deterministic: hook emits terse graph-derived impact records straight into the memory stream | **no** | graph only |

Shared infrastructure reuses the PROVEN `attention_edges.py` checkout + codegraph
helpers (`ensure_checkout`, per-task `cache/codegraph-repos/<slug>`). Gold callers
ground-truth = `analysis/attention-edges/subgraphs/<task>.json`.

## Result (matched 21-case subset)

| prototype | caller_capture | edge_capture | symbol_capture | mean records | notes |
|-----------|---------------|--------------|----------------|--------------|-------|
| **P4 deterministic** | **0.399** | **0.239** | **0.412** | 104.8 | zero model cost |
| P1 tool | 0.096 | 0.056 | 0.106 | 6.9 | model called tool on 8/21 cases (38%) |
| P2 injected | 0.050 | 0.002 | 0.062 | 6.4 | digest was in context; still not carried |

Per-task: P4 wins or ties on **10/11** tasks (the lone "loss" is adaptix 0.04 vs 0.06).

## What the data says

1. **The cheap low-thinking model DOES call a secondary codegraph tool.**
   gpt-5.4-mini:low called `graph_callers` on 8/21 clean cases (14 calls total),
   querying the *right* symbols (e.g. arktype: `jsonSchemaToType`,
   `parseCompositionJsonSchema`, `parseObjectJsonSchema`). The inherited
   "cheap models won't call secondary tools" assumption (from codegraph-auto's
   README) is **falsified** for this model/tool.

2. **But calling the tool didn't help, because distillation destroys the signal.**
   P1 (0.096) barely beats P2 (0.050), and both are ~4–8x below P4 (0.399). The
   model queries callers, then writes observations that paraphrase task
   requirements instead of recording the caller relationships it just looked up
   (see the arktype sample). Passing graph facts through an observer/reflector
   LLM loses 75–90% of the signal.

3. **P2 (inject the digest) is the worst** — 0.050 caller / 0.002 edge capture.
   The caller names were placed directly in the observer's input and the model
   still did not carry them into observations. "Inject and let the observer
   distill" does not work for blast-radius signal.

4. **Deterministic graph facts (P4) survive at 4–8x the rate of any LLM path** —
   and at zero model cost. The LLM distillation step is the bottleneck, not the
   enabler, for relationship signal.

## Honest caveats

- **Rate limit:** P1 hit the OpenAI-codex 5h limit at case 22; cases 22–24
  (`bandit-*`) emitted empty output and were dropped. P2 ran clean (24/24). P4
  uses no model. Comparison is on the 21 clean P1 cases so all three are scored
  on the identical set.
- **Metric scope:** `impact_capture_rate` measures signal *in the memory stream*,
  not downstream executor solve-rate. P4 emits graph edges as text and is scored
  against those same edges — this is not bias (it measures exactly "does the
  memory carry the signal"), but it does not yet prove P4 helps the executor
  *solve* tasks. That is the next eval.
- **P4 volume:** ~105 records/case is impractical for a real memory block. A
  curated P4 (top-k by caller count, or symbols actually edited in the chunk) is
  the shippable shape and likely retains most of the capture rate.
- **Sample:** 21 cases, 11 tasks, 1 model (gpt-5.4-mini:low). Not a full cell.

## Recommendation

**Pursue P4 (deterministic impact memory), curated. Do not build P3.**

- The dedicated impact agent (P3) was deferred pending whether LLM distillation
  matters. It does not — it destroys signal. P3 would be strictly worse than P4
  at higher cost. Drop it.
- The next step is a **curated P4**: limit records to symbols the executor
  actually edited (derived from chunk edit-tool args, not all touched files),
  cap per-file, and emit as a distinct memory block (`om.impact.recorded` or
  appended to the compaction summary) rather than 100+ observation records.
- Then run the **decisive test**: a full DeepSWE cell with curated-P4 vs
  baseline-vs-current-OM, scored on `reward_partial`/`reward_binary`, segmented
  by whether the task crossed a compaction boundary (where durable blast-radius
  memory should matter most). If curated-P4 lifts solve rate without inflating
  tokens, it earns a place in the shipped extension.
- Keep the `graph_callers` tool finding on record: even though it lost here, it
  falsifies a stale assumption and may matter for the *executor* (where the
  model has more turns and a stronger edit-task signal) — a separate question.

## Artifacts

- shared lib + digest + gold loaders: `impact_common.py`
- metric: `metrics/impact_capture.py` (self-test passes)
- P4: `p4_deterministic.py` -> `runs/p4-deterministic.jsonl`
- P2 prep: `p2_enrich.py` -> `cases/p2_enriched.jsonl`; replay: `runs/p2-live.jsonl`
- P1 variant extension: `variants/p1-tool/` (typechecks clean); replay: `runs/p1-live.jsonl`
- driver: `replay_driver.py`; scoring: `score_run.py`; comparison: `compare.py`,
  `runs/comparison.json`; per-task: `per_task.py`

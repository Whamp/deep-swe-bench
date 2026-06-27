# Rename plan

Target layout (see `docs/adr/0001-...` and `CONTEXT.md` for rationale):

```
configs/<config>/{orchestration.md, pi-flags, env, extensions/, skills/}
configs/<config>/<model>[+<advisor>]/<thinking>/{models.json[, advisor.json]}

subsets/12_v0.txt  subsets/36_v1.txt  subsets/113_v0.txt   # <size>_v<iter>; 36_v1=current fast-iter-v1, 12_v0=new 12-task seed nested in 36_v1

results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/result.json
results/<model-leaf>/<thinking>/comparisons/<name>/{manifest.json, analysis.md}
results/<model-leaf>/<thinking>/logs/                                  # batch/monitor logs
```

**`<model-leaf>` is executor-only** (the last `/`-segment of the executor
`model`, e.g. `deepseek-v4-flash`, never `deepseek-v4-flash+glm-5.2`). The
`<exec>+<advisor>` form lives ONLY in the configs leaf below, never in the
results path. This keeps a resumed `run_batch` — which receives only `--model`
(the executor) — able to compute the same results path migrate wrote. See ADR-0001.

```
configs/<config>/{orchestration.md, pi-flags, env, extensions/, skills/}
configs/<config>/<model-leaf>/<thinking>/models.json                 # non-advisor
configs/<config>/<exec>+<advisor>/<thinking>/{models.json,advisor.json}  # advisor only

harness/run.py            # --arm -> --config ; --run-name removed (path-derived)
harness/run_batch.py      # --arms -> --configs ; --subsample -> --subset
harness/analyze.py        # --run -> --comparison (+ --model + --thinking)
```

(Note: the literal `<model>` / `<model-leaf>` tokens above are placeholders for
`model_leaf(model)`; never embed a raw `--model` string — it contains slashes.)

## Phase 0 — Prep (no renames yet)

1. Snapshot: `git add -A && git commit -m "wip: pre-rename snapshot"`.
2. Inventory existing results that are worth migrating (not all `runs/` are).
   Source of truth: `runs/*/results.jsonl` and `runs/*/*/rep*/result.json`.

## Phase 0.5 — parse_usage native-session rewrite (standalone, lands BEFORE the rename)

**Operator decision (review round):** decouple the highest-risk logic change
(parse_usage rewrite) from the mechanical rename. Land it as its own change with
its own smoke-test and revert, so a parse bug is discovered on one cell, not
after the tree is moved. This phase touches only `harness/parse_usage.py` and
the `pi.jsonl` write/read lines in `harness/run.py`; it does NOT rename anything.

**Why standalone:** ADR-0002 retires `pi.jsonl` and switches to the native
`session/*.jsonl`. If the `type:"message"` parsing is wrong, every future run
silently reports `cost_usd=0` / `total_tokens=0`. Bundling that with the tree
move couples the riskiest change to the most mechanical one. Smoke-testing
native-session parsing on one real cell *before* the rename gives a clean
rollback point that does not unwind the restructure.

14a. **`parse_usage` is REWRITTEN, not just re-pointed.** The native session
     uses `type:"message"` records (NOT the `turn_end`/`message_end`/
     `tool_execution_end` events the stream uses). Pointing the current
     `parse_stream` at a session file returns all-zeros — verified:
     `parse_stream(session_file)` yields `total_tokens=0, cost_usd=0, turns=0`
     because it keys on event types that don't exist in the session. The
     rewrite:
     - Iterate `type:"message"` records where the message is an assistant
       turn; sum `message.usage.{input,output,cacheRead,cacheWrite,totalTokens}`
       and `message.usage.cost.total`; count `toolCall` content blocks for
       `tool_calls`; count assistant messages for `turns`.
     - **Remove the `except Exception: raw=""` silent-zero fallback** in
       `parse_stream` (parse_usage.py:34-35). A missing/empty/unreadable source
       must RAISE, not return a zero dict — the silent-zero path is the
       corruption vector if the `pi.jsonl` write-removal and session-read
       switch land out of sync.
     - **Per-config exceptions** (see AGENTS.md "Usage capture"):
       - `advisor` — advisor LLM usage is absent from the native session
         entirely, so it is captured at RUN time, not just for migrated old
         cells. For advisor configs, pipe `--mode json` stdout through
         `jq -c 'select(.type=="tool_execution_end" and .toolName=="advisor")'`
         -> `tool-usage.jsonl` (tiny; NOT the full `pi.jsonl`). `parse_usage`
         then reads BOTH the native session (executor usage) and this
         `tool-usage.jsonl` (advisor usage). Without this, new advisor runs
         silently report `advisor_cost_usd=0`.
       - `observational-memory` worker usage is a known unmeasured gap (not
         recoverable from session or stream).
14b. **Couple the edit atomically:** remove the `pi.jsonl` write (run.py:286)
     and the `pi.jsonl` read (run.py:350) in the same commit, and add a
     post-edit smoke-test asserting a one-cell run writes non-zero
     `cost_usd` / `total_tokens`.
14c. **Parity check (gate):** before committing, run the new parser on a real
     cell that still has both its `pi.jsonl` AND its `session/*.jsonl`, and
     assert the new native-session-derived `{total_tokens, cost_usd, turns}`
     matches the old `pi.jsonl`-derived numbers for that same cell within a
     tight tolerance. This is the proof the rewrite did not silently change
     accounting. If parity fails, the rename (Phase 1+) does NOT proceed until
     it is resolved — a parse_usage bug discovered after the tree move is much
     harder to localize.

This phase's commit is independently revertable (`git revert` restores
`pi.jsonl` capture) without touching the directory layout.

## Phase 1 — Subsets (independent, do first, trivial)

3. `git mv harness/subsamples subsets`.
4. Rename both existing files to `<size>_v<iteration>`: `git mv
   subsets/fast-iter-v1.txt subsets/36_v1.txt` (current 36-task set) and
   `git mv subsets/fast-iter-v0.txt subsets/12_v0.txt` (the 12-task seed the
   operator created, fully set-contained in 36_v1).
5. Create `subsets/113_v0.txt` = all 113 task ids (sorted, from `~/evals/deep-swe/tasks/`).
6. **Nesting is set-containment, NOT file-order prefix.** 12_v0's tasks are
   scattered through 36_v1 (verified: all 12 appear in 36_v1, but not as its
   first 12 lines), so do not reorder either file to force a prefix —
   `run_batch` skips by task-id existence, not position. Update
   `subsets/README.md`.
7. Grep `subsample` / `fast-iter-v1` / `fast-iter-v0` across the repo and
   update references (harness, docs).

## Phase 2 — Configs (the directory split)

8. `git mv arms configs`.
9. For each config, split into constant files vs model leaves. Constant
   (config-wide): `orchestration.md`, `pi-flags`, `env`, `extensions/`,
   `skills/`. These stay at `configs/<config>/`.
   **`settings.json` is NOT always config-level.** It is read by `run.py:135,281`
   (copied into the container at `/root/.pi/agent/settings.json`) and by the OM
   extension (`config.ts:117`). For most configs it is behavioral (e.g.
   `pi-advisor-glm52/settings.json` is just a `retry` policy) and stays
   config-level. **But for `observational-memory` it carries the WORKER MODEL
   identity** (`observational-memory.model.{provider,id}`), which VARIES by leaf
   — verified: the two OM arms carry different worker models (Qwen vs
   `gpt-5.4-mini`). A model-identity-bearing `settings.json` is a leaf file for
   the same reason `models.json`/`advisor.json` are: placing it config-level lets
   one leaf's worker model silently overwrite the other (the ADR-0001 mutation
   bug). So: behavioral-only `settings.json` → config-level; model-identity
   `settings.json` → leaf (see §10 leaf contents + §11 OM fold note).
10. Materialize model leaves `configs/<config>/<model-leaf>/<thinking>/`
    using **`result.json` as the source of truth, never the current
    `arms/*/models.json`** (which was mutated mid-history — the resume bug from
    ADR-0001). Provenance rules:
    - The model id for the path comes from `result.json`'s top-level `model`
      field (present in 100% of cells — verified across all 962 `result.json`
      as of plan authoring; live count grows as the qwen batch runs).
    - **`arm_models` consistency check (mandatory):** `result.json`'s
      `arm_models` field is a snapshot of `models.json` taken at run time, but if
      the snapshot was taken AFTER the file was already mutated it carries the
      WRONG model. **`arm_models` is a providers-dict, NOT a flat model record**
      — it has NO top-level `.model` key (verified: non-null `arm_models` is
      `{providers: {<provider>: {models: [{id: ...}]}}}`; `.arm_models.model` is
      ABSENT). Verified: 8 of 18 `codex-spark-baseline-sub` cells have
      `arm_models` present but its provider model id is not `gpt-5.3-codex-spark`
      (the result.json `model`) — it is stale (carries the local-vllm Qwen
      config from the mutation incident). Rule: **extract the model id from
      `arm_models.providers.<provider>.models[].id`; discard `arm_models` if
      none of those ids equals `result.json`'s top-level `model` leaf**; log
      every discard to `migrate-models-audit.jsonl`.
    - The leaf's `models.json`/`advisor.json` content comes from a `result.json`
      `arm_models`/`arm_advisor` field that PASSES the consistency check; fall
      back when the field is absent OR fails the check. **Fold routing for the
      fallback:** resolve the old `<arm>` to the folded `<config>` via the §11
      map, then read `arms/<folded-config>/models.json` (e.g. `baseline-codex` ->
      `arms/baseline/models.json`, since `arms/baseline-codex/` has none). If
      that also lacks `models.json`, materialize the leaf path-only (no
      `models.json`), logged.
    - **Fallback-file provider consistency check (mandatory — closes the
      arm_models-absent leak):** the fallback `arms/<folded-config>/models.json`
      may itself be MUTATED (the incident left `arms/baseline/models.json` as the
      local-vllm Qwen config). Before trusting it, extract its provider model id
      (`providers.<provider>.models[].id`) and compare its leaf to
      `result.json`'s top-level `model` leaf. **If they disagree (e.g. fallback
      is Qwen but the cell is `gpt-5.3-codex-spark`), materialize the leaf
      PATH-ONLY with no `models.json`, logged** — same as the file-absent branch.
      This is correct, not a loss: codex models run via pi's built-in
      `openai-codex` provider (verified: `baseline-codex` ran `codex-spark` with
      NO `models.json`), so an absent `models.json` is right for those cells; a
      present-but-wrong one is the bug. Verified scope: this leak hits
      `arm_models=null` cells in BOTH codex-spark runs (28/36 in sub, 22/45 in
      w2).
    - **Mixed-presence leaves:** when reps sharing a leaf have mixed
      `arm_models` presence, use the `arm_models` from any rep that passes the
      consistency check; fall back to `arms/<config>/models.json` only when ALL
      reps in the leaf lack the field or all fail the check.
    - If two reps of the same `(config, task, rep)` disagree on `model`, fail
      loud — that is the mutation bug surfacing and must not be silently folded.
    Leaf contents:
    - non-advisor: `models.json` [+ `settings.json` if this config's
      `settings.json` carries a worker model identity — see §9; e.g.
      `observational-memory`].
    - advisor: `models.json` + `advisor.json` under `<exec>+<advisor>/<thinking>/`
      (behavioral-only `settings.json`, e.g. the retry policy, stays config-level).
11. Rename configs (model now lives in the leaf, so config names drop model
    suffixes). **Complete map — all 10 `arms/` dirs covered:**
    - `baseline` -> **`baseline`** (unchanged; the clean name is reserved for the
      true no-prompt control).
    - `baseline-codex` -> **folds into `baseline`**. `arms/baseline-codex/`
      contains only `orchestration.md` (byte-identical to `baseline`'s); it has no
      `extensions/`, `pi-flags`, or `models.json` of its own, so its reps inherit
      `baseline`'s config-level files. The `local-vllm-preserve-thinking.ts`
      extension in `baseline` is a no-op for codex models, so behavior is
      unchanged. Its reps land under `baseline`'s codex model leaf.
      **Collision note:** `codex-spark-baseline-sub` (arm=`baseline-codex`) and
      `codex-spark-baseline-w2` (arm=`baseline`) are both `gpt-5.3-codex-spark` /
      `high` / `rep0` and share 18 `(task, rep)` pairs — see §19's collision
      policy for the keep/renumber decision; do NOT silently merge.
    - `baseline-codex-wf` -> **`baseline-wf`**, a distinct config. Per the
      operator: `baseline` is plain pi with no extra prompt (the true baseline —
      what a real user gets with an empty AGENTS.md); `baseline-wf` adds the
      mini-swe-agent step-by-step workflow prompt, which is benchmark-specific
      (wouldn't exist in a user's standing instructions) and therefore genuinely
      additional config. Both coexist; the comparison between them answers which
      to standardize on. `baseline` keeps the clean name; wf is the variant with
      the suffix.
    - `pi-advisor-glm52` -> **`advisor`** (configs leaf
      `deepseek-v4-flash+glm-5.2/high/`; results path uses executor-only
      `deepseek-v4-flash/high/advisor/...` — the `+glm-5.2` is configs-leaf-only).
    - `pi-observational-memory` -> **`observational-memory`**.
    - `pi-observational-memory-codex54mini` -> **folds into `observational-memory`**
      as another model leaf. **Leaf name is DERIVED from `result.json` `.model`,
      NOT the dir name** — the dir says "codex54mini" but the actual recorded
      model is `openai-codex/gpt-5.5`, so the leaf is `gpt-5.5/<thinking>/`
      (verified against the 113 cells in `codex55-medium-om54mini-w2`).
      **`settings.json` worker-model collision (the ADR-0001 bug pattern):** the
      two OM arms carry DIFFERENT worker models in their `settings.json`
      (Qwen `local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4` vs
      `openai-codex/gpt-5.4-mini`, verified). Folding both into one config with
      a single config-level `settings.json` would silently overwrite one leaf's
      worker model with the other. Fix: each arm's `settings.json` lands in ITS
      OWN model leaf (`<model-leaf>/<thinking>/settings.json`), so the two leaves
      keep their distinct worker models. (This is the OM analog of advisor's
      leaf-level `advisor.json`.)
    - `ponytail-full` -> **`ponytail-full`** (unchanged).
    - `ponytail-lite` -> **`ponytail-lite`** (unchanged).
    - `ponytail-pi-extension` -> **`ponytail-extension`** (drops the redundant
      `pi-` segment; everything in this repo is a pi config, so the prefix
      carries no information).
    - `ponytail-ultra` -> **`ponytail-ultra`** (unchanged).
12. Update `arms/README.md` -> `configs/README.md`: drop the arm framing, document
    the constant-vs-leaf split and the immutable-leaf rule.

## Phase 3 — Code changes (CLI + paths)

Single edit each file. All references: `grep -rnE "\barm|\barms\b|run_name|run-name|subsample|slice|DEEP_SWE_TASKS"` harness/ scripts/ README.md configs/README.md.
(The pattern includes `slice`: `run_batch.py` has a `--slice` flag for
`0:10`-style task-id ranges. `slice` is a banned term per CONTEXT.md — rename it
to `--range` in the same pass, since it is a contiguous-index selector, not a
subset.)

13. `harness/lib.py`:
    - `tasks_root()` default `~/evals/deep-swe/tasks` stays.
    - `result_record()` `arm=` -> `config=`.
    - **Add the single shared `model_leaf(model, advisor_model=None) -> str`
      normalization** used by BOTH `migrate_results.py` and the new `run.py` /
      `run_batch.py` path derivation. Rule: take the last `/`-segment of `model`
      (e.g. `openrouter/deepseek/deepseek-v4-flash` -> `deepseek-v4-flash`), and
      if `advisor_model` is set, append `+` + the advisor's last segment (e.g.
      `deepseek-v4-flash+glm-5.2`). This is the ONLY place the path segment is
      derived; migrate and harness import it so they cannot diverge (the resume-
      re-runs-everything failure mode).
14. `harness/run.py`:
    - `--arm` -> `--config`; `--run-name` removed (output path derived from
      `model`/`thinking`/`config`).
    - Output root `runs/<run_name>/<arm>/<task>/rep<N>` ->
      `results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`, where
      `<model-leaf>` = `lib.model_leaf(model)` (executor-only; never the raw
      `--model` string, which contains slashes and would create wrong nested
      dirs). `--slice` -> `--range` (see §13 grep note).
    - Load constant files from `configs/<config>/`; model leaf from
      `configs/<config>/<model-leaf>/<thinking>/`.
    - **parse_usage native-session switch is already landed in Phase 0.5**
      (standalone, pre-rename). §14 here only ensures `run.py` no longer
      references the retired `pi.jsonl` path after the rename; the parser
      logic itself is settled by Phase 0.5's parity gate. See Phase 0.5 and
      ADR-0002.
15. `harness/run_batch.py`:
    - `--arms` -> `--configs`; `--subsample` -> `--subset` (reads `subsets/<size>_v<iter>.txt`, e.g. `12_v0.txt`).
    - Resume = existence-check `result.json` per `(task, rep)`; run missing only.
    - `--run-name` removed; batch/monitor logs land under
      `results/<model>/<thinking>/logs/`.
16. `harness/analyze.py`:
    - `--run` -> `--comparison` (+ `--model` `--thinking`, or read from manifest).
    - Read reps from `results/<model>/<thinking>/<config>/` restricted to a
      subset; write `analysis.md` into the comparison folder.
    - Drop the "arm" column/word everywhere; use "config".
17. `scripts/track_run.py`: update path glob to new results tree.
18. `harness/Dockerfile.pi-agent`, `harness/system_preamble.md`: path/wording only.

## Phase 4 — Migrate existing results

19. Write `scripts/migrate_results.py`. It MUST be run with `--dry-run` first;
    dry-run reports every destination tuple and every collision, and writes
    NOTHING. Only after the user approves the dry-run output does the real move
    run.

    **Walker / symlink handling (mandatory):** `runs/` contains 3 `baseline/`
    symlinks pointing at `../ponytail-full-pilot-w2/baseline`
    (`runs/om-memory-pilot-w10/baseline`, `runs/advisor-glm52-full-w4/baseline`,
    `runs/advisor-glm52-reliability-rerun/baseline`). A naive `rglob`/
    `Path.glob` (followlinks) double-counts those 113 cells 4x (1305 paths vs
    966 real files — verified). The walker MUST use `os.walk(followlinks=False)`
    or dedup by `os.path.realpath`; the symlinked `baseline/` dirs are NOT
    walked independently. After the move, remove the now-dead symlinks.

    **`--runs <list>` scoping (optional optimization):** the walker accepts a
    `--runs baseline,advisor-glm52-full-w4,…` flag bounding `os.walk` to the
    named run roots, so a static paused run (e.g. `codex-spark`) could migrate
    during the wait without traversing live sibling run dirs. **Safest default:
    do NOT use this — migrate only after the full freeze gate passes.** If used,
    the walker is bounded to those roots AND each `result.json` read is wrapped
    in `try/except json.JSONDecodeError → skip+log` to tolerate any concurrent
    write on a sibling (defense in depth).

    **Excluded runs (do NOT migrate):**
    - smoke-test throwaways: `diag`, `validate`, `validate-fixed` (4 cells total,
      pre-pilot scaffolding). Excluding them resolves a real collision: all three
      hold `(deepseek-v4-flash, baseline, adaptix-name-mapping-aliases, rep0)`
      which would otherwise collide with `ponytail-full-pilot-w2`'s real cell
      (`reward_partial=0.998` vs the throwaways' `0.0`). Verify: they carry no
      `thinking_level` and no `arm_models` either.
    - aborted/empty runs (0 `result.json`, would otherwise trip the "uncovered
      collision → fail loud" path): `codex54mini-high-wf-sub`,
      `codex54mini-xhigh-wf-sub`, `ponytail-full-pilot` (distinct from the real
      `ponytail-full-pilot-w2`).

    For each surviving `result.json`, read `model` + `arm`, derive
    `(config, model-leaf, thinking)` via the shared `lib.model_leaf()` (executor-
    only — the results path NEVER carries `+advisor`), and compute the
    destination `results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/`.

    **In-file rewrite (mandatory):** `analyze.py:114` keys rows on the IN-FILE
    `(task, rep, arm)` fields, not the path. So the move alone is not enough:
    - Every migrated cell gets its in-file `arm` field RENAMED to the new
      `config` value via the §11 map (e.g. `pi-advisor-glm52` -> `advisor`).
    - Every renumbered cell (advisor `rep1`, codex-spark `rep1`) gets its in-file
      `rep` field SET to the new N.
    - Post-migrate assertion (fail-loud if violated): for every
      `rep<N>/result.json`, `rec["rep"] == N` and `rec` has a `config` key whose
      value matches the path's `<config>` segment.

    **`thinking_level` provenance — corrected (prior plan text was wrong):**
    the field is NOT written by `lib.py:result_record`; it is passed in as a
    kwarg from `run.py` (`thinking_level=thinking`). 253 older cells LACK the
    field entirely (verified across all 962 `result.json` as of authoring;
    minus the 4 excluded throwaways = 249 real): `ponytail-full-pilot-w2` = 249.
    **Rule: if `thinking_level` is missing, use `DEFAULT_THINKING` (`high`)
    unconditionally; log every imputation to `migrate-thinking-audit.jsonl`.
    NEVER fail-loud on a missing `thinking_level`.** (The prior text said
    "fail-loud if no batch log" — that was self-contradictory, because `diag`/
    `validate` have no `.out`; and `ponytail-full-pilot-w2`'s `command:` header
    omits `--thinking` anyway, so the default `high` is the only source. All 253
    missing cells used `high` — verified by cross-checking sibling cells that do
    carry the field.)
    **The 249/253 count is a plan-authoring snapshot, not an invariant.**
    `migrate_results.py` MUST recompute the actual missing-count at migration
    time (re-derive with the §A inventory). If the recomputed count differs
    materially from 249, investigate before backfilling: a divergence means
    either the symlink dedup failed (the 3 `baseline/` symlinks point at
    `ponytail-full-pilot-w2/baseline`) or a newer run stopped recording the
    field — both are worth understanding, not silently papering over with
    `DEFAULT_THINKING`.

    **Collision detection (mandatory):** the new layout drops the `run-name`
    axis, so two old runs can map to the same `(model-leaf, thinking, config,
    task, rep)` tuple. Verified collisions that MUST be resolved before any move:
    - **`advisor-glm52-reliability-rerun` (40 cells) vs `advisor-glm52-full-w4`
      (113 cells)** — both `advisor / deepseek-v4-flash / high / rep0`.
      Deliberately different reps (a reliability rerun is the point): e.g.
      `adaptix-name-mapping-aliases rep0` is `reward_partial=0.000` in full-w4
      vs `0.997` in reliability-rerun. **Policy: the reliability-rerun's 40
      cells become `rep1`** (CONTEXT.md: "reps accumulate under a config
      regardless of which subset produced them"). Genuine additional reps.
    - **`codex-spark-baseline-sub` (36 cells, arm=`baseline-codex`) vs
      `codex-spark-baseline-w2` (45 cells, arm=`baseline`)** — both fold to
      `config=baseline`, same `gpt-5.3-codex-spark / high`, and share 18
      `(task, rep0)` pairs (sub has 36 cells but only 18 are tasks w2 reached).
      **Policy: keep `codex-spark-baseline-w2`'s cells at `rep0`; renumber ALL
      36 of `codex-spark-baseline-sub`'s cells to `rep1`** (uniformity: sub and
      w2 stay separate rep cohorts; the 18 non-overlapping sub tasks get `rep1`
      only, which a future w2 resume fills at `rep0`).
    The `--dry-run` output must list EVERY collision and its resolution before
    the move runs. Any collision not covered by the two policies above fails
    loud.

    **General rep-accumulation rule (applies to ALL configs, not just the two
    collisions above):** reps accumulate under a config leaf regardless of
    which `--subset` produced them (CONTEXT.md). A config's first batch writes
    `rep0`; a later `--subset` expansion (e.g. `--subset 113` after `--subset
    36`) fills `rep1+` for the new tasks and leaves the migrated `rep0` cells
    untouched. The migration MUST preserve each migrated cell's `rep` index
    verbatim (no renumbering except the two collision policies above), so a
    future resume that re-derives the path from `(model, thinking, config,
    task, rep)` finds the existing `result.json` and skips it. Renumbering
    outside the two documented collisions would silently re-run migrated
    cells on resume — the same class of bug the rename exists to prevent.

    **What moves:** `result.json`, the small dirs (`verifier/`, `artifacts/`,
    `logs/`), and the native `session/`. **Do not move `pi.jsonl`** (the 233GB
    of streams — retired by ADR-0002). Old `pi.jsonl` stays in `runs/` until
    manually purged. **Advisor exception:** advisor cells have no other usage
    record, so for advisor cells keep a filtered `tool-usage.jsonl` using the
    exact filter `jq -c 'select(.type=="tool_execution_end" and
    .toolName=="advisor")'` at `results/<model-leaf>/<thinking>/<config>/<task>/
    rep<N>/tool-usage.jsonl`, scoped ONLY to `arm=pi-advisor-glm52` cells. (If
    the old advisor cells' `result.json` already carry `advisor_cost_usd` /
    `advisor_total_tokens`, this old-cell filter is optional; the run-time
    capture in §14 is the real fix going forward.)
20. Rebuild `results.jsonl` per config from the moved `result.json` files.
    `analyze.py` prefers `result.json` files over `results.jsonl` and dedups by
    `(task, rep)`, so row order and dupes are low-risk — but the rebuild must
    run AFTER all moves + renumbering so the rep axis is consistent.
21. Move hand-curated `reports/` as-is (it already references study names; update
    pointers in its READMEs to the new comparison names in a follow-up).

## Phase 5 — Docs & cleanup

22. Rewrite root `README.md`: drop arm/study/run-noun language, update all
    commands to `--config`/`--subset`/`--comparison`, document the new tree and
    the nesting-resume pattern.
23. `git mv` leftover `arms/README.md` etc. as needed; delete empty old dirs.
24. `git mv tmp_task20_29_summary.json data.txt misc/` (scratch files, filed
    per Q7).
25. Smoke test: pick a task present in NO migrated run
    (`adaptix-name-mapping-aliases` is in 5 old runs and would SKIP, testing
    nothing — verify with `find runs -path '*adaptix*result.json'`). Run one
    `--config baseline --model deepseek-v4-flash --thinking high --task <fresh>`
    cell on the new harness and assert ALL of (machine-checkable):
    (a) `result.json` lands at the exact
    `results/<model-leaf>/<thinking>/<config>/<task>/rep0/` path;
    (b) `cost_usd > 0` AND `total_tokens > 0`;
    (c) `session/*.jsonl` contains >=1 `type:"message"` record;
    (d) NO `pi.jsonl` is created in the cell dir;
    (e) a second `run_batch.py` invocation logs `skip` for that cell.
    Only if all five pass does resume (§6) proceed.

## Resolved questions

- **Q5 (baseline vs wf):** `baseline` = plain pi, no extra prompt (the true
  baseline). `baseline-wf` = baseline + mini-swe-agent workflow prompt (a distinct
  config — the prompt is benchmark-specific, i.e. additional config). Both coexist;
  their comparison decides which to standardize on. `baseline` keeps the clean
  name.
- **Q6 (batch logs):** `results/<model>/<thinking>/logs/`.
- **Q7 (root scratch files):** move `tmp_task20_29_summary.json` and `data.txt`
  into a new `misc/` dir.

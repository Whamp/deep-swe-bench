Design complete and validated. The interface reproduces every current call-site path exactly (`run.py` cell dir, `run_batch` result/log/glob-base, `results.jsonl`), unifies the three duplicate leaf derivations into one, and adds a free rep-ordering fix.

---

# Interface design — `harness/paths.py` (variant: **cell-runner-first**)

**Hero choice:** the cell runner fixes all 5 keys and touches ~6 paths in one cell, so `CellPaths` — one frozen object holding every grammar address — is the center of gravity. Readers get a lighter `TreePaths` handle.

```python
def cell_paths(model, thinking, config, task, rep, *, repo=REPO) -> CellPaths  # THE writer entry
def tree_paths(model, thinking, *, repo=REPO) -> TreePaths                      # reader entry

@dataclass(frozen=True) CellPaths:   # one named attr per grammar path (no caller-side path strings)
    task, config, rep, thinking          # echoed (no leaf, no model — leaf hidden, caller has model)
    dir, result, transient_error         # cell files
    artifacts, verifier, logs, session   # cell subdirs
    results_jsonl                        # tree file this cell appends
    .subdirs -> (artifacts,verifier,logs,session)
    .has_result() .has_transient() .exists()   # Category 2, OSError->False
    .rel()

@dataclass(frozen=True) TreePaths:   # model+thinking pinned; leaf derived ONCE then discarded
    thinking, root, results_jsonl
    .cell(config,task,rep) -> CellPaths
    .log_file(task,config,rep)          # tree-level log (≠ cell's logs/ subdir)
    .has_config_results(config)         # glob */rep*/result.json
    .iter_cells(config) / .iter_result_files(configs)  # ascending (config,task,rep-as-int)
```

## 1. Invariants / ordering / error modes
- **Invariant 1 (resume-by-existence):** writer's `cell_paths(...).result` ≡ reader's `tree_paths(...).cell(...).has_result()` — same `Path` from `_build_cell`. ADR-0001's leaf-divergence re-run becomes structurally impossible (one spelling site).
- **Invariant 2 (leaf immutability):** leaf derived in exactly one private site (`_root` → `lib.model_leaf`), never a field, never re-exposed. Collapses today's **3** derivations (`run.py` `model_leaf`, `run_batch.py` `model_leaf_of` — a literal duplicate — `analyze.py` inline) into one.
- **Invariant 3 (executor-only):** `_root` passes no `advisor_model`, so `+advisor` cannot enter results.
- **Ordering:** iteration deterministic, ascending `(config, task, rep-as-int)` — fixes current glob-sort where `rep10 < rep2` (free; stats are order-independent).
- **Errors:** derivation never raises; existence returns `bool` swallowing `OSError`; iteration yields paths only and **never parses JSON** (caller keeps its `try/except`).

## 2. Usage (both call shapes)
```python
# writer (run.py / run_omp.py): one line + a loop
c = cell_paths(model, thinking, config, task_id, rep)
c.dir.mkdir(parents=True, exist_ok=True)
for d in c.subdirs: d.mkdir(exist_ok=True)
c.transient_error.unlink(missing_ok=True)          # reset sentinel
...
c.result.write_text(json.dumps(rec, indent=2))      # WRITES stay in the runner
with c.results_jsonl.open("a") as f: f.write(json.dumps(rec) + "\n")

# reader (run_batch + analyze): pin once
tree = tree_paths(model, thinking)
if not tree.cell(config, task, rep).has_result() or args.force: ...run...
log = tree.log_file(task, config, rep)
for rj in tree.iter_result_files(configs): rows.append(json.loads(rj.read_text()))
```

## 3. Hidden behind the seam
Single leaf derivation; the full 5-segment grammar + tree file + tree-log naming (incl. the **tree-level `logs/` vs cell-level `logs/`** distinction, same word, two addresses — separated by object); executor-only guarantee; repo-root substitutability; correct rep-int ordering.

## 4. Dependency strategy & adapters
Cat 1 (path derivation: pure, no I/O) → no seam. Cat 2 (existence/iteration: local `pathlib`, substitutable via `repo=` → `tmp_path`) → no seam either. No network/DB/clock → **no Cat 3/4 → no ports.** Deletion test on a hypothetical `FileSystem` port: one implementation = zero leverage; `repo=` already gives substitutability and tests want the real FS. Slots into the existing `test_run_batch.py` / `test_run_state_properties.py` temp-root pattern.

## 5. Trade-offs + deletion test
- **CellPaths — PASS.** Delete it → both writers re-type `REPO/"results"/leaf/thinking/config/task/rep{rep}"` + 4 subdirs inline; grammar scatters across 2 writers and resume again relies on hand-synced strings.
- **TreePaths — PASS.** Delete it → `run_batch` re-derives the leaf per `result_path`/`log_path` (it does today, via a `model_leaf_of` duplicate).
- **`cell_paths()` is sugar (thin).** Deletion test: caller writes `tree_paths(model,thinking).cell(config,task,rep)`. Kept *only* because the cell runner is the hot path — the chosen constraint. Weakest member, acknowledged.
- **Deliberate width:** `CellPaths` is wide (8 `Path` fields) rather than exposing only `.dir`. The thin accessor is rejected because it re-scatters grammar strings — exactly the ADR-0001 write-vs-existence divergence surface. One attr per grammar path = one spelling.
- **Scope boundary:** module owns the *grammar* addresses only; non-grammar leaf files (`tool-usage.jsonl`, `pi-agent/`, `initial_context/`, `logs/*.txt`) stay caller-named relative to `c.dir`/`c.logs`.
- **Non-contradiction:** `run_state.cell_id` uses a display string `task/config/rep` (task-first); the FS grammar is config-first. Module owns the FS address only and does not generate the display id.

Full design written to `docs/design/paths-module--cell-runner-first.md`.
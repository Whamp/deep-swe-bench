I've verified all call sites, the ADR-0001 incident, and CONTEXT.md against the brief. The grammar, the three invariants, and the two access patterns all check out. Now I'll deliver my minimized-interface design.

---

# Design D — One entry point, two types (the minimized interface)

**Differentiator vs. the other three designs:** every other design will fan out into more entry points / scopes / methods. Mine front-loads *one* constructor and reaches the entire 3-level grammar through a single returned object. The ruthlessness is at the **entry-point** and **type** level; method count is then forced by the grammar size, which is irreducible.

---

## 1. Interface

### Entry point (exactly one)

```python
def tree(model: str, thinking: str, *, repo: str | Path | None = None) -> "Tree":
    """Pin the results tree at (model, thinking). The ONLY way into this module.
    Derives the executor-only leaf once via lib.model_leaf(model) — never
    +advisor — and discards it (leaf is never re-exposed)."""
```

### Type 1 — `Tree` (frozen; one field: `root`)

```python
@dataclass(frozen=True)
class Tree:
    root: Path          # results/<leaf>/<thinking>/

    # --- tree-level files ---
    @property
    def results_jsonl(self) -> Path: ...        # root/results.jsonl
    def log_file(self, task: str, config: str, rep: int) -> Path: ...   # root/logs/{task}__{config}__rep{rep}.log

    # --- narrowing ---
    def cell(self, config: str, task: str, rep: int) -> "Cell": ...

    # --- existence / iteration (config scope) ---
    def has_results(self, config: str) -> bool: ...
    def cells(self, config: str) -> Iterator["Cell"]: ...   # sorted, deterministic
```

### Type 2 — `Cell` (frozen; seven path fields — the irreducible grammar)

```python
@dataclass(frozen=True)
class Cell:
    dir: Path               # root/config/task/rep<N>/
    result: Path            #   /result.json
    transient_error: Path   #   /transient_error.json
    artifacts: Path         #   /artifacts/
    verifier: Path          #   /verifier/
    logs: Path              #   /logs/        (per-cell runner logs)
    session: Path           #   /session/

    def has_result(self) -> bool: ...   # self.result.exists()
```

### Invariants the interface protects (why it exists)

| # | Invariant | How this interface makes it structural |
|---|-----------|----------------------------------------|
| 1 | **resume-by-existence** — the path a writer creates (`cell/result.json`) ≡ the path a reader existence-checks | A `Cell` is always built by `Tree.cell(config,task,rep)` — one derivation, both sides. `has_result()` and `cells()` (which reconstructs via `self.cell(...)`) check that exact path. The ADR-0001 leaf-divergence re-run cannot recur: there is no second place to spell the path. |
| 2 | **model-leaf immutability** — leaf derived one way everywhere | Leaf is computed **once**, inside `tree()`, via `lib.model_leaf`. `Cell`/`Tree` never carry it as a settable field; no caller ever types a leaf. |
| 3 | **executor-only in results** — never `+advisor` | `tree()` is the sole constructor and calls `lib.model_leaf(model)` *without* `advisor_model`. The `+advisor` form is **unreachable** through this module. The advisor leaf exists only on the configs side, which this module never touches. |

### Ordering
- **Pure (no I/O), deterministic:** `tree()`, `cell()`, `log_file()`, `results_jsonl`, `root`, all `Cell` fields. Same args ⇒ byte-identical `Path` objects every time.
- **`cells(config)`** yields in `sorted(...)` order by `(task, rep)` — matches `analyze.py`'s `sorted((root/config).glob(...))`. Deterministic ⇒ reproducible comparisons.

### Error modes
- **No write/create surface at all** (module's decided job: derive/check/iterate only). It never `mkdir`s or writes — so no permission/ENOSPC errors originate here.
- **Path-derivation members never raise** on missing dirs; callers `mkdir` from the returned `Cell`.
- **Existence/iteration are missing-safe:** `has_result()`/`has_results()`/`cells()` return `False`/`False`/empty on a tree that has no results yet (glob over a nonexistent dir yields nothing; `.exists()` returns `False`). A reader scanning an unstarted `(model, thinking)` gets `[]`, not `FileNotFoundError`. (`run_batch` preflight hits exactly this.)
- **Leaf edge:** `lib.model_leaf("")` would yield `""` → `root/results//thinking`. The source `lib.model_leaf` doesn't guard this; I add no guard the source lacks (scope). Noted as residual.

---

## 2. Usage example

### Single-cell writer (`run.py` / `run_omp.py` style — fixes all 5 keys)

```python
from harness.results_addr import tree

def run_cell(config, task_id, *, model, thinking, rep, ...):
    t = tree(model, thinking)                       # executor-only leaf, derived once
    c = t.cell(config, task_id, rep)
    c.dir.mkdir(parents=True, exist_ok=True)
    for sub in (c.artifacts, c.verifier, c.logs, c.session):
        sub.mkdir(exist_ok=True)
    c.transient_error.unlink(missing_ok=True)
    # ... agent + verifier ...
    c.result.write_text(json.dumps(rec, indent=2))
    with t.results_jsonl.open("a") as f:           # tree-level append
        f.write(json.dumps(rec) + "\n")
```

Replaces today's hand-wired `REPO/"results"/model_leaf(model)/thinking/config/task_id/f"rep{rep}"` + four hand-named subdirs + `REPO/"results"/mleaf/thinking/"results.jsonl"`.

### Cross-cell reader (`analyze.py` style — iterate) + `run_batch` resume

```python
from harness.results_addr import tree

# analyze.py — iterate over a config
def load_results(model, thinking, configs):
    t = tree(model, thinking)
    rows = []
    for config in configs:
        for c in t.cells(config):                  # sorted, deterministic
            try:
                rows.append(json.loads(c.result.read_text()))
            except Exception:
                pass
    return rows

# run_batch.py — resume-by-existence (invariant 1) + tree-level log + preflight
t = tree(args.model, args.thinking)
if t.cell(config, task, rep).has_result() and not args.force:   # writer≡reader identity
    skip()
lf = t.log_file(task, config, rep)
lf.parent.mkdir(parents=True, exist_ok=True); lf.write_text(...)
if t.has_results(config):                          # preflight smoke gate
    skip_smoke()
```

---

## 3. What the implementation hides behind the seam

Everything that today is duplicated, string-formatted, or glob-hand-written across 5 files:

- **The leaf derivation** (last `/`-segment) and the **executor-only** rule — callers never see either.
- **The whole path grammar:** 3 levels, the `rep{N}` formatting, the `__`-joined **tree-level** log filename, the 4 cell subdirs, the `results.jsonl` location.
- **The two different "logs":** `cell.logs` (per-cell runner-log *subdir*) vs `tree.log_file(...)` (flat batch stdout/stderr *file*). Disambiguated by scope — exactly the grammar-centralization the module exists for.
- **The existence/iteration glob grammar** (`*/rep*/result.json`).
- **The repo-root resolution.**

Behind a *one-call* front door, the implementation is the entire grammar.

---

## 4. Dependency strategy & adapters

- **Category 1 — pure path derivation (in-process, deterministic):** `tree()`, `cell()`, `log_file()`, `results_jsonl`, `root`, all `Cell` fields. No I/O.
- **Category 2 — local-substitutable I/O:** `has_result()` / `has_results()` / `cells()` — just `Path.exists()` / `Path.glob()`. Identical behavior under pytest `tmp_path`: pass `tree(model, thinking, repo=tmp_path)`.
- **No Category 3/4** (no external service, no shared mutable store, no device) ⇒ **no ports & adapters warranted.**

**No-port argument (deletion test on a hypothetical `ResultStore`/`PathPort`):** such an interface would have exactly **one** implementation — the local filesystem — so it is a pure pass-through; deleting it changes nothing. The one real substitutability need (tests vs. real repo) is already served by the plain `repo=` keyword argument, not by an injected port object. *One adapter = a hypothetical seam; two adapters = a real one. Here there are zero.* Note this module also **consumes** `lib` one-way (`results_addr → lib`) and never re-exports `leaf()`, so it adds no upstream coupling.

---

## 5. Trade-offs — where leverage is high vs. thin

**High leverage (the design's center of gravity):**
- **`tree()`** — one call replaces ~6 hand-wired path expressions across 5 call sites and is the *sole* place leaf+grammar live. *Deletion test:* delete it → every caller re-derives leaf + grammar independently ⇒ ADR-0001 incident literally returns. **Earns its keep decisively.**
- **`cell()`** — collapses cell dir + 4 subdirs + 2 named files (7 paths) into one frozen object; writer's `mkdir` loop and reader's existence check use the *same* `Cell`. *Deletion test:* delete → 7 path expressions re-appear in both writers and both readers. **Earns its keep.**
- **`Tree` as a one-field type** — not thin: its value is *behavior* (`cell`/`log_file`/`cells`/`has_results`), not data. It earns its keep by pinning `(model, thinking)` so leaf is derived **once** rather than re-passed into 5 module-level functions (the alternative "many functions" design repeats the `(model, thinking, repo)` triple and re-derives leaf per call).

**Borderline-thin (kept for legibility, deletable for maximal minimalism):**
- **`has_results(config)`** — almost `next(t.cells(config), None) is not None`. Kept because (a) it hides the glob grammar inside the module and (b) it *names* invariant-1's config-level form at the call site; the inline idiom would re-leak the glob. If one member must go to hit a hard cap, **this is the one to cut** (perf is irrelevant — only `run_batch` preflight calls it, once per config).
- **`Cell.has_result()`** — one-liner `self.result.exists()`. Symmetric with the writer writing `c.result`; names the resume check. Deletion: callers write `c.result.exists()` (fine, loses the named primitive).

**Non-goal (noted, not owned):** `run_state.py::cell_id(task,config,rep)` = `f"{task}/{config}/rep{rep}"` is a *different* relative address (no model/thinking, reordered). This interface deliberately does **not** own or contradict it; coupling `Cell` to that format would be scope creep.

---
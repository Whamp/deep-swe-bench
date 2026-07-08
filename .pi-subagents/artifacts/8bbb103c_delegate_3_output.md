Grounded against the real call sites. The strongest finding: **leaf is currently derived three different ways** — `lib.model_leaf(model)` (run.py/run_omp.py), `run_batch.model_leaf_of(model)`, and an inline `model.rstrip("/").split("/")[-1]` in analyze.py. ADR-0001's "silently re-ran everything" bug is *already latent* in this three-way split. That's the lever my design is built around.

---

# Radical alternative: **"Freeze the scope, never materialize the cell."**

The OOP default — `ResultsTree(model, thinking).cell(c, t, r)` returning a `CellAddress` with `.result_json / .transient_error / .artifacts` properties — is a **wide, shallow module**: the interface (N properties) is nearly as big as the implementation (join path segments). Every property is a pass-through that fails the deletion test (`cell / "result.json"` is equally readable at the call site). My design inverts it on both axes: **one frozen value carries the only coordinates that matter (leaf+thinking); the cell is never an object — it's positional keys projected to paths by free functions.** A smaller interface with equal power = a deeper module.

Module: `harness/results_tree.py`. Direction: `results_tree → lib` (one-way import of `model_leaf`); lib never imports back.

## 1. Interface

```python
# harness/results_tree.py
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, NamedTuple
from harness import lib          # one-way: consume lib.model_leaf, do NOT re-expose leaf()

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
DEFAULT_ROOT = REPO / "results"

# The grammar's declared cell children (results/…/rep<N>/<these>/):
SUBDIRS: tuple[str, ...] = ("artifacts", "verifier", "logs", "session")

@dataclass(frozen=True, slots=True)
class Root:
    """The ONLY state-bearing type. Frozen value object — NOT a navigable tree.
    Carries the (leaf, thinking) coordinates sealed inside `path`; leaf is
    computed exactly once in Root.of and is never re-exposed."""
    thinking: str
    path: Path                       # == base / leaf / thinking; leaf is baked in, not readable

    @classmethod
    def of(cls, model: str, thinking: str, *, base: Path = DEFAULT_ROOT) -> "Root":
        """SOLE leaf-derivation chokepoint. EXECUTOR-ONLY by construction:
        calls lib.model_leaf(model) with no advisor arg, so the +advisor form
        is impossible to produce here. Raises ValueError on empty model."""
        if not model:
            raise ValueError("model must be a non-empty executor model id")
        return cls(thinking=thinking, path=base / lib.model_leaf(model) / thinking)

    def __repr__(self) -> str:       # debug aid only; never exposes leaf() separately
        return f"Root({self.path.relative_to(REPO)})"

# ---- Category 1: pure path derivation (in-process, no I/O) ----
def tree_results_jsonl(root: Root) -> Path: ...          # root.path / "results.jsonl"
def tree_log_file(root: Root, config: str, task: str, rep: int) -> Path: ...
    # root.path / "logs" / f"{task}__{config}__rep{rep}.log"   ← ROOT-level, not cell/logs/
def config_dir(root: Root, config: str) -> Path: ...      # root.path / config
def cell_dir(root: Root, config: str, task: str, rep: int) -> Path: ...
    # config_dir / task / f"rep{rep}"
def result_json(root: Root, config: str, task: str, rep: int) -> Path: ...      # cell / "result.json"
def transient_error(root: Root, config: str, task: str, rep: int) -> Path: ...  # cell / "transient_error.json"
def cell_subdir(root: Root, config: str, task: str, rep: int, name: str) -> Path: ...
    # cell_dir / name  (name expected in SUBDIRS)

# ---- Category 2: local-FS reads (existence + iteration) ----
def result_exists(root: Root, config: str, task: str, rep: int) -> bool: ...
    # result_json(...).exists()  — thin, but NAMES the resume-by-existence contract
def config_has_results(root: Root, config: str) -> bool: ...
    # config_dir exists AND any(config_dir.glob("*/rep*/result.json"))
def iter_cells(root: Root, *, configs: Iterable[str] | None = None) -> Iterator["Found"]: ...
    # globs */rep*/result.json per config, parses rep<int>, yields sorted(config, task, rep)

class Found(NamedTuple):            # a READ RESULT (what exists on disk), NOT an address type
    config: str; task: str; rep: int; path: Path
```

**Invariants protected (and how, structurally):**
1. **resume-by-existence** — `result_json(root,…)` is *one function* shared by the writer (run.py) and every reader (run_batch, analyze). The writer's write-path ≡ the reader's existence-path **by identity, not by convention**. Leaf can't diverge because there's no second derivation site.
2. **leaf immutability** — leaf is computed once in `Root.of`, sealed inside frozen `path`, and has no public accessor. You cannot construct a `Root` from an arbitrary leaf, nor read one back out.
3. **executor-only** — `Root.of` takes no advisor arg → `+advisor` is un-expressible.

**Ordering.** `iter_cells` yields `(config, task, rep)` sorted lexicographically on config then task, then numerically on `rep<int>`. Stray dirs not matching `rep<int>` are skipped. Deterministic (analyze already `sorted()`s the glob; this makes it the contract).

**Error modes.** `Root.of("") → ValueError`. All other derivations are total (path joins can't fail). FS errors (PermissionError, etc.) from `.exists()`/`.glob()` propagate unchanged — masking them is out of scope. `iter_cells`/`config_has_results` over a missing config_dir yield `[]`/`False` silently (matches today's `any(glob)`). `thinking` is **deliberately not validated** — it's an opaque path segment, already constrained at the argparse layer; validating policy here would widen the seam from "path" to "grammar police."

**Performance.** All derivations O(1) (cheap path joins, no caching needed). `config_has_results`/`iter_cells` are O(filesystem glob), identical to today.

## 2. Usage — both call shapes

**Single-cell writer (run.py / run_omp.py style)** — note the module *never writes*; it derives paths, the caller does I/O:
```python
from harness import results_tree as rt

def run_cell(config, task_id, *, model, thinking, rep, ...):
    root = rt.Root.of(model, thinking)                       # ONE derivation; both runners identical
    cell = rt.cell_dir(root, config, task_id, rep)
    cell.mkdir(parents=True, exist_ok=True)
    for sub in ("artifacts", "verifier", "logs"):            # writer-managed subset of SUBDIRS
        rt.cell_subdir(root, config, task_id, rep, sub).mkdir(exist_ok=True)
    rt.transient_error(root, config, task_id, rep).unlink(missing_ok=True)
    ...
    rt.result_json(root, config, task_id, rep).write_text(json.dumps(rec, indent=2))  # writer writes
    rl = rt.tree_results_jsonl(root)
    with rl.open("a") as f:
        f.write(json.dumps(rec) + "\n")
```

**Cross-cell reader (analyze.py style)** — same chokepoint, fixed model+thinking, iterate:
```python
from harness import results_tree as rt

def load_results(model, thinking, configs):
    root = rt.Root.of(model, thinking)            # ← same factory the writer used
    return [json.loads(f.path.read_text())
            for f in rt.iter_cells(root, configs=configs)]   # one glob, sorted
```

**Batch reader / resume gate (run_batch.py style)** — the root-level log path is the easy-to-botch one:
```python
root = rt.Root.of(args.model, args.thinking)
if rt.result_exists(root, config, task, rep) and not args.force:  # resume gate ≡ write path
    ...
log = rt.tree_log_file(root, config, task, rep)   # results/…/logs/{t}__{c}__rep{r}.log  (root-level!)
if rt.config_has_results(root, config): ...        # preflight: replaces the duplicated glob
```

## 3. What the implementation hides behind the seam

- **The model→leaf derivation** (delegated to `lib.model_leaf`; sealed in `Root`; never re-exposed — collapses the three current derivations into one).
- **REPO anchoring** (`HERE.parent` → `results/`) — currently recomputed in run_batch, run.py, run_omp, analyze independently.
- **The executor-only constraint** (no advisor arg can reach `of`).
- **The grammar's two trapdoors:** the *root-level* `logs/{task}__{config}__rep{rep}.log` vs the *cell-level* `rep<N>/logs/` subdir (today these are string-concatenated ad hoc in 3 files); the `rep{N}` dir convention; the `SUBDIRS` set.
- **The iteration glob** `*/rep*/result.json` + deterministic sort + `rep<int>` parse — duplicated today in run_batch L83 and analyze L30.
- **The immutability freeze** — a `Root` can't drift after construction, so a long-lived batch can't accidentally re-anchor.

## 4. Dependency strategy & adapters — why no ports

- **Category 1 (pure derivation):** `Root.of` and every projection function. No I/O, in-process. The bulk of the module.
- **Category 2 (local-substitutable):** `result_exists`/`config_has_results`/`iter_cells` touch the local FS via `pathlib.exists()`/`glob()`. Substitutable in tests by pointing `Root.of(..., base=tmp_path)` at a pytest `tmp_path`. No abstraction needed.
- **No Category 3 (shared mutable service) or 4 (external system):** the module only **reads** the filesystem; **writes stay in the cell runner** (per the brief). Therefore **no ports & adapters warranted.**

Deletion test on a hypothetical `Filesystem` port: delete it, substitute the `base: Path` parameter — complexity vanishes and nothing reappears across callers → the port fails the test. The one-adapter rule (one adapter = hypothetical seam, two = real) says: with zero real seams, don't build the abstraction. A `base` path is strictly simpler than a VFS interface and covers the only substitution axis that actually exists (which tree root).

## 5. Trade-offs — leverage high/thin + deletion test on MY interface

**High leverage (deletion re-exposes the bug / the duplication):**
- **`Root.of` (the chokepoint):** delete it → leaf derivation + REPO anchor + executor-only reappear in ≥3 callers, **and reintroduce the live three-way divergence that ADR-0001 was written about** (analyze doesn't even call `lib.model_leaf` today). This is why the module exists. Earne keep hard.
- **`iter_cells` / `config_has_results`:** delete → the `*/rep*/result.json` glob reappears in run_batch *and* analyze. Earns keep.
- **`result_json` / `cell_dir` / `tree_log_file`:** delete → inline joins reappear in every caller; `tree_log_file` especially, because the root-level-vs-cell-level `logs` distinction is a genuine footgun. Earns keep.

**Thin (honest):**
- **`result_exists` (single-cell):** delete → `result_json(...).exists()`, a one-liner at its single call site (run_batch `run_one`). It survives *only* because it names the resume-by-existence contract at the call site — the one invariant the module is built for. A pragmatic maintainer could legitimately inline it; I'd yield if they prefer.
- **`Found` NamedTuple** from `iter_cells`: could be a bare tuple. Kept named for readability; it's a **read result**, not an address object — distinct from the forbidden "Cell-as-address" pattern.
- **`SUBDIRS` / `cell_subdir`:** marginal; a tuple + sugar that documents the grammar's cell children. Writers only ever create 3 of the 4 (`session` is written by the agent in-container), so this is grammar-documentation more than enforcement.

**Why this beats the obvious OOP `ResultsTree→CellAddress`:** that shape is wide-and-shallow (N pass-through properties, each failing the deletion test), and it gives each caller a `Cell` *object* they construct from keys — which is precisely the surface where a second leaf-derivation can sneak back in. Free functions over a single frozen `Root` is a **smaller interface** (≈8 functions + 1 frozen value, no class hierarchy to navigate), is **more grep-able** (`rt.cell_dir(root, …)`), and makes the resume-equivalence invariant a **type-level fact** (you cannot call a path function with a raw model string; you must carry a `Root`, and there's only one way to make one).

**Considered and rejected radicals:**
- *Declarative path-grammar as data* (grammar is a data structure + one interpreter): elegant, but the grammar is a **static constant** for this repo — it never varies, so the data layer is indirection without leverage (deletion test: inline the 6 rules, lose nothing anyone uses). Shallow, not deep.
- *Fluent builder DSL* (`Root.at(m,t).config(c).cell(t,r).result_json`): call-order coupling, low locality, and it hides a simple function behind a chain that fails the deletion test. Rejected.

**Boundary note (run_state.py):** it uses a *relative display id* `f"{task}/{config}/rep{rep}"` (config-first, no model/thinking). That's a different projection (dashboard token, not a filesystem address). My module produces **absolute, model+thinking-pinned** paths and deliberately does *not* own run_state's relative id — no contradiction, different concern, scope held.

---
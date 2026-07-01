"""Shared infrastructure for the om-impact prototypes (P1/P2/P4).

Reuses the PROVEN repo-checkout + codegraph-query helpers from
analysis/attention_edges.py rather than reinventing them. Everything here is
read-only on benchmark artifacts; new outputs go under analysis/om-impact/.

Case -> task mapping: a replay case's session_path is
  results/<model>/<think>/<config>/<task>/rep0/session/<file>.jsonl
so segment [4] is the DeepSWE task_id, which maps (via task.toml) to a
repository_url + base_commit_hash. attention_edges already caches clones under
cache/codegraph-repos/<slug> and builds .codegraph there.

Digest primitive: we surface CALLER NAMES (the unit impact_capture_rate scores
against). `where <sym> -T -j` returns `uses` = direct callers with names; this
is exactly what attention_edges used to build gold edges, so the prototype's
output is scored against the same graph it could have queried.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "harness"))
# ponytail: reuse the proven checkout/codegraph helpers verbatim.
from attention_edges import ensure_checkout, cg, cg_runok, task_meta, repo_slug  # noqa: E402
from lib import tasks_root  # noqa: E402

OUTDIR = REPO / "analysis" / "om-impact"
CASESDIR = OUTDIR / "cases"
RUNSDIR = OUTDIR / "runs"

CLONE_TIMEOUT = 240
BUILD_TIMEOUT = 180
QUERY_TIMEOUT = 60

# filter noise paths the way codegraph-auto does: test files, vendored/stdlib,
# generated dirs. Keeps the digest focused on real source-change blast radius.
SKIP_SUBSTR = ("_test.", "/tests/", "/test/", "/vendor/", "/node_modules/",
               "/.codegraph/", "/stdlib/", "/third_party/", "/generated/",
               "_generated.", ".min.", ".pb.go")
ALLOWED_EXTS = {"go", "py", "ts", "tsx", "js", "jsx", "rs", "java", "kt",
                "rb", "php", "cs", "c", "cc", "cpp", "h", "hpp"}


def _is_source_path(p: str) -> bool:
    lo = p.lower()
    if lo.split(".").pop() not in ALLOWED_EXTS:
        return False
    return not any(s in lo for s in SKIP_SUBSTR)

# file-path-like tokens in serialized chunks. DeepSWE executor tool calls carry
# a `path`/`file_path` arg; tool results render paths. We extract candidates
# then confirm against the graph.
PATH_RE = re.compile(r'(?:[\w./-]+/)+[\w.-]+\.[A-Za-z]{1,4}')


# --- case <-> task ---------------------------------------------------------

def case_task_id(case: dict[str, Any]) -> str | None:
    sp = case.get("session_path", "")
    segs = sp.split("/")
    if len(segs) > 4 and segs[0] == "results":
        return segs[4]
    return None


def case_model_arm(case: dict[str, Any]) -> tuple[str, str, str]:
    segs = case.get("session_path", "").split("/")
    if len(segs) > 3 and segs[0] == "results":
        return segs[1], segs[2], segs[3]
    return "", "", ""


# --- graph readiness -------------------------------------------------------

def ensure_graph(task_id: str) -> tuple[Path | None, str, dict]:
    """Ensure repo checked out at task base commit + graph built.

    Returns (graph_dir | None, status, meta). meta carries repo/commit/language.
    """
    meta = task_meta(task_id) or {}
    if not meta.get("repo") or not meta.get("commit"):
        return None, "no_task_meta", meta
    slug = repo_slug(meta["repo"])
    rdir, st_ = ensure_checkout(meta["repo"], meta["commit"], slug)
    if rdir is None:
        return None, f"checkout:{st_}", meta
    bstat = cg_runok("build", ".", cwd=rdir, timeout=BUILD_TIMEOUT)
    if bstat != "ok":
        return None, f"build:{bstat}", meta
    return rdir, "ok", meta


# --- changed-file extraction from chunk ------------------------------------

def extract_chunk_files(chunk: str, graph_dir: Path) -> list[str]:
    """File paths mentioned in the serialized chunk that exist in the graph.

    The chunk is the observer's input (serialized conversation). It contains the
    executor's tool-call args (path/file_path) and tool-result renders. We mine
    path-like tokens, then keep only those that resolve as files in the graph so
    prose noise is dropped.
    """
    candidates: list[str] = []
    seen: set[str] = set()
    for m in PATH_RE.findall(chunk):
        p = m.strip().lstrip("./")
        if p in seen or len(p) < 3 or not _is_source_path(p):
            continue
        seen.add(p)
        candidates.append(p)
    # confirm against graph: which of these are real source files? (--file mode)
    confirmed: list[str] = []
    for p in candidates:
        d, _ = cg("where", "--file", p, "-j", cwd=graph_dir, timeout=10)
        if isinstance(d, dict) and d.get("mode") == "file" and d.get("results"):
            confirmed.append(p)
            continue
        # try basename match (chunk may use relative/different prefix)
        base = p.split("/")[-1]
        d, _ = cg("where", "--file", base, "-j", cwd=graph_dir, timeout=10)
        if isinstance(d, dict) and d.get("mode") == "file" and d.get("results"):
            confirmed.append(base)
    # de-dup preserving order
    out: list[str] = []
    s = set()
    for p in confirmed:
        if p not in s:
            s.add(p)
            out.append(p)
    return out


def file_symbols(graph_dir: Path, file_path: str, limit: int = 12) -> list[dict[str, Any]]:
    """Symbols defined in a file with their direct callers (names).

    Two-step because the caller NAMES live in symbol mode (`where <sym> -j` -> uses),
    not file mode. We list symbols via `--file`, then batch-query callers in one
    codegraph process.
    """
    d, _ = cg("where", "--file", file_path, "-j", cwd=graph_dir, timeout=QUERY_TIMEOUT)
    if not isinstance(d, dict) or not d.get("results"):
        return []
    syms_raw = (d["results"][0].get("symbols") or [])[:limit]
    if not syms_raw:
        return []
    # batch-resolve callers for each symbol (one process, not N)
    names = [s.get("name") for s in syms_raw if s.get("name")]
    bd, _ = cg("batch", "where", *names, "-T", "-j", cwd=graph_dir, timeout=QUERY_TIMEOUT)
    callers_by_name: dict[str, list[str]] = {}
    if isinstance(bd, dict):
        for res in (bd.get("results") or []):
            tgt = res.get("target")
            if not tgt:
                continue
            clist = []
            for node in (res.get("data", {}).get("results") or []):
                for u in (node.get("uses") or []):
                    if u.get("name"):
                        clist.append(u["name"])
            callers_by_name[tgt] = clist
    out: list[dict[str, Any]] = []
    for s in syms_raw:
        nm = s.get("name")
        if not nm:
            continue
        out.append({
            "name": nm,
            "kind": s.get("kind"),
            "line": s.get("line"),
            "callers": callers_by_name.get(nm, []),
        })
    return out


# --- digest (the shared blast-radius text) ---------------------------------

def compute_digest(graph_dir: Path, files: list[str], max_files: int = 6) -> str:
    """Terse, graph-derived blast-radius digest over the chunk's touched files.

    Surface caller NAMES (impact_capture_rate's scoring unit). One block per
    file: file -> symbols -> caller list. Hard caps keep it observer-cheap.
    """
    if not files:
        return ""
    lines: list[str] = ["[codegraph blast-radius: callers of symbols in files touched this chunk]"]
    for fp in files[:max_files]:
        syms = file_symbols(graph_dir, fp)
        if not syms:
            continue
        lines.append(f"  {fp}:")
        for s in syms:
            callers = s.get("callers") or []
            tag = f" <- {len(callers)} caller(s)" + (f": {', '.join(callers[:6])}" if callers else "")
            lines.append(f"    {s['name']} ({s.get('kind','?')}){tag}")
    if len(lines) == 1:
        return ""
    return "\n".join(lines)


# --- gold callers (impact_capture_rate ground truth) -----------------------

SUBGRAPHS = REPO / "analysis" / "attention-edges" / "subgraphs"


def load_gold_edges(task_id: str) -> list[dict[str, str]]:
    p = SUBGRAPHS / f"{task_id}.json"
    if not p.exists():
        return []
    d = json.loads(p.read_text())
    if d.get("status") != "ok":
        return []
    return d.get("edges") or []


def gold_callers(task_id: str) -> set[str]:
    return {e["caller"] for e in load_gold_edges(task_id) if e.get("caller")}


def gold_symbols(task_id: str) -> set[str]:
    return {e["gold"] for e in load_gold_edges(task_id) if e.get("gold")}


def gold_edges(task_id: str) -> set[tuple[str, str]]:
    return {(e["caller"], e["gold"]) for e in load_gold_edges(task_id)
            if e.get("caller") and e.get("gold")}


def selftest() -> None:
    # path extraction
    chunk = "edited src/foo/bar.ts and ./lib/util.go plus nonsense a/b.py"
    files = PATH_RE.findall(chunk)
    assert "src/foo/bar.ts" in files, files
    assert "lib/util.go" in files or "./lib/util.go" in files, files
    # task mapping
    case = {"session_path": "results/deepseek-v4-flash/high/observational-memory/abs-module-cache-flags/rep0/session/x.jsonl"}
    assert case_task_id(case) == "abs-module-cache-flags", case_task_id(case)
    assert case_model_arm(case) == ("deepseek-v4-flash", "high", "observational-memory")
    # gold callers load
    gc = gold_callers("abs-module-cache-flags")
    assert "requireFn" in gc or "sourceFn" in gc, gc
    print("SELFTEST PASS")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="om-impact shared lib")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        selftest()

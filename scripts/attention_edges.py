#!/usr/bin/env python3
"""Analysis B: relationship/EDGE-level attention (the core of the hypothesis).

The hypothesis is about attention to relationships between symbols (caller/callee,
dependencies), not files or bare symbols. For each task we build the GOLD SUBGRAPH
= changed symbols (from analysis A) + their 1-hop CALLERS (who calls a changed
function = the blast radius), using codegraph on the repo checked out at the
task's base_commit_hash. Callers are the "if I change this, what breaks" edge --
the relationship an attentive agent checks before editing.

Per rep we then measure attention to EDGES: for each gold edge (caller -> goldSym),
did the agent reference BOTH endpoints (co-occur in the same turn)? The fraction
of gold edges seen is the edge-attention score. We also flag edge_found_then_lost:
the agent referenced a caller relationship early then dropped it before finishing.

Two resumable phases:
  --phase subgraph : clone+build+query per task -> analysis/attention-edges/subgraphs/
  --phase reps     : per-rep edge attention over session logs using cached subgraphs

Read-only on benchmark artifacts. Repos are cloned under cache/codegraph-repos/
(public, no credentials). Graph builds are local (no spend).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import statistics as st
import subprocess
import sys
import tomllib
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "harness"))
from attention_signals import DEFAULT_TARGETS, iter_reps, _flatten_args, _tail, _arm_stats  # noqa: E402
from attention_symbols import parse_gold_symbols  # noqa: E402
from lib import tasks_root  # noqa: E402

OUTDIR = REPO / "analysis" / "attention-edges"
SUBDIR = OUTDIR / "subgraphs"
REPOCACHE = REPO / "cache" / "codegraph-repos"

# per-process timeouts (seconds). ponytail: bounded so one huge repo can't sink
# the whole run; blocked tasks are recorded with their blocker.
CLONE_TIMEOUT = 240
BUILD_TIMEOUT = 180
QUERY_TIMEOUT = 60


# --- task metadata ---------------------------------------------------------

def task_meta(task_id: str) -> dict | None:
    tf = tasks_root() / task_id / "task.toml"
    if not tf.exists():
        return None
    m = tomllib.loads(tf.read_text())
    md = m.get("metadata", {})
    return {"repo": md.get("repository_url", ""), "commit": md.get("base_commit_hash", ""),
            "language": md.get("language", "").lower()}


def repo_slug(url: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]", "_", url.rstrip("/").split("/")[-1].removesuffix(".git"))


# --- phase 1: gold subgraph per task ---------------------------------------

def ensure_checkout(repo_url: str, commit: str, slug: str) -> tuple[Path | None, str]:
    """Clone (blobless) + checkout commit. Returns (path, status)."""
    rdir = REPOCACHE / slug
    if not rdir.exists():
        try:
            subprocess.run(["git", "clone", "--filter=blob:none", "--quiet", repo_url, str(rdir)],
                           timeout=CLONE_TIMEOUT, check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except subprocess.TimeoutExpired:
            return None, "clone_timeout"
        except subprocess.CalledProcessError as e:
            return None, f"clone_failed:{(e.stderr or b'').decode()[:120]}"
    # fetch the commit in case a shallow/partial clone lacks it
    try:
        subprocess.run(["git", "-C", str(rdir), "fetch", "--quiet", "--depth=1", "origin", commit],
                       timeout=CLONE_TIMEOUT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        pass  # ignore; checkout may still succeed if commit present
    try:
        r = subprocess.run(["git", "-C", str(rdir), "checkout", "--quiet", commit],
                           timeout=60, capture_output=True, text=True)
        if r.returncode != 0:
            return None, f"checkout_failed:{r.stderr[:120]}"
    except subprocess.TimeoutExpired:
        return None, "checkout_timeout"
    return rdir, "ok"


def cg(*args, cwd: Path, timeout: int) -> tuple[object | None, str]:
    """Run codegraph, return (parsed_json | None, status)."""
    try:
        r = subprocess.run(["codegraph", *args], cwd=str(cwd), timeout=timeout,
                           capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if r.returncode != 0:
        return None, f"error:{r.stderr[:120].strip()}"
    out = r.stdout.strip()
    try:
        return json.loads(out), "ok"
    except json.JSONDecodeError:
        return None, f"no_json:{out[:120]}"


def cg_runok(*args, cwd: Path, timeout: int) -> str:
    """Run codegraph, return 'ok' on exit 0 regardless of stdout (for `build`)."""
    try:
        r = subprocess.run(["codegraph", *args], cwd=str(cwd), timeout=timeout,
                           capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return "timeout"
    return "ok" if r.returncode == 0 else f"error:{r.stderr[:120].strip()}"


def build_subgraph(task_id: str) -> dict:
    """Return {task, status, gold_symbols, edges, neighbors, blocker}."""
    out_path = SUBDIR / f"{task_id}.json"
    meta = task_meta(task_id)
    gold = parse_gold_symbols(task_id)
    rec = {"task": task_id, "language": (meta or {}).get("language", ""),
           "n_gold_symbols": len(gold.symbols) if gold else 0,
           "gold_symbols": sorted(gold.symbols) if gold else [],
           "gold_files": sorted(gold.files) if gold else [],
           "edges": [], "neighbors": [], "status": "", "blocker": ""}
    if not meta or not meta.get("repo") or not meta.get("commit"):
        rec["status"] = "blocked"; rec["blocker"] = "no_repo_or_commit"; return rec
    if not gold or not gold.symbols:
        rec["status"] = "no_gold_symbols"; return rec

    rdir, st_ = ensure_checkout(meta["repo"], meta["commit"], repo_slug(meta["repo"]))
    if rdir is None:
        rec["status"] = "blocked"; rec["blocker"] = st_; return rec

    # build (incremental; cached in .codegraph). rebuild is cheap if unchanged.
    bstat = cg_runok("build", ".", cwd=rdir, timeout=BUILD_TIMEOUT)
    if bstat != "ok":
        rec["status"] = "blocked"; rec["blocker"] = f"build_{bstat}"; return rec

    gold_basenames = {f.split("/")[-1] for f in gold.files}
    edges, neighbors = [], set()
    for sym in gold.symbols:
        d, qstat = cg("where", sym, "-T", "-j", cwd=rdir, timeout=QUERY_TIMEOUT)
        if qstat != "ok" or not isinstance(d, dict):
            continue
        for node in (d.get("results") or []):
            nfile = (node.get("file") or "")
            # disambiguate: keep only nodes in a gold file (by basename)
            if nfile.split("/")[-1] not in gold_basenames:
                continue
            for u in (node.get("uses") or []):
                cname = u.get("name") or ""
                if not cname:
                    continue
                edges.append({"caller": cname, "gold": sym,
                              "caller_file": u.get("file", "")})
                neighbors.add(cname)
    rec["edges"] = edges
    rec["neighbors"] = sorted(neighbors)
    rec["status"] = "ok" if edges else "no_edges_found"
    return rec


def phase_subgraph(limit: int | None) -> None:
    SUBDIR.mkdir(parents=True, exist_ok=True)
    tasks = sorted(t.name for t in tasks_root().iterdir() if (t / "task.toml").exists())
    if limit:
        tasks = tasks[:limit]
    done = skipped = 0
    statuses = defaultdict(int)
    for i, t in enumerate(tasks, 1):
        out_path = SUBDIR / f"{t}.json"
        if out_path.exists():
            skipped += 1; continue
        rec = build_subgraph(t)
        out_path.write_text(json.dumps(rec))
        statuses[rec["status"]] += 1
        done += 1
        print(f"[B-sub {i}/{len(tasks)}] {t}: {rec['status']} "
              f"(gold={rec['n_gold_symbols']}, edges={len(rec['edges'])}) "
              f"{rec['blocker']}", flush=True)
    print(f"\nphase subgraph: built {done}, skipped(cached) {skipped}")
    print("status counts:", dict(statuses))


# --- phase 2: per-rep edge attention --------------------------------------

def _sym_matchers(syms: set[str]):
    return [(s, re.compile(r"(?:^|[^\w$])" + re.escape(s) + r"(?:[^\w$]|$)"))
            for s in syms if len(s) >= 2]


def turn_edges(session_paths: list[Path], rel_syms: set[str]) -> list[dict]:
    """Per assistant turn: which relationship-relevant symbols appear in its output.

    Counts the assistant's full output -- text blocks (prose reasoning like
    "X calls Y") AND tool-call args. toolResult excluded (environment, not agent)."""
    if not rel_syms:
        return []
    res = _sym_matchers(rel_syms)
    turns = []
    for sp in session_paths:
        for raw in sp.read_text(errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "message":
                continue
            msg = ev.get("message") or {}
            if msg.get("role") != "assistant":
                continue
            touched = set()
            has_tool = False
            blob_parts = []
            for b in (msg.get("content") or []):
                bt = b.get("type")
                if bt == "toolCall":
                    has_tool = True
                    blob_parts.append(_flatten_args(b.get("arguments") or {}))
                elif bt == "text":
                    blob_parts.append(b.get("text", ""))
            if not has_tool:
                continue
            blob = " " + " ".join(blob_parts)
            for sym, r in res:
                if r.search(blob):
                    touched.add(sym)
            turns.append({"refs": sorted(touched)})
    return turns


def load_subgraph(task_id: str) -> dict | None:
    p = SUBDIR / f"{task_id}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text())


def edge_attention_for_rep(session_paths: list[Path], sub: dict) -> dict:
    """Compute edge-attention signals for one rep from its subgraph."""
    edges = sub.get("edges") or []
    if not edges:
        return {"edge_coverage": 0.0, "n_edges": 0, "edge_ftl": False,
                "caller_seen_rate": 0.0, "first_edge_turn": None, "last_edge_turn": None,
                "n_turns": 0}
    gold_set = {e["gold"] for e in edges}
    caller_set = {e["caller"] for e in edges}
    rel_syms = gold_set | caller_set
    turns = turn_edges(session_paths, rel_syms)
    # per turn, which edges have BOTH endpoints referenced
    edge_seen_turns = []  # turn index where each edge first co-referenced
    edge_first = {}
    edge_last = {}
    for ti, t in enumerate(turns):
        refs = set(t["refs"])
        for ei, e in enumerate(edges):
            if e["caller"] in refs and e["gold"] in refs:
                edge_first.setdefault(ei, ti)
                edge_last[ei] = ti
    n_seen = len(edge_first)
    coverage = n_seen / len(edges)
    # callers referenced at all (weaker: did agent ever name a caller)
    caller_any = set()
    for t in turns:
        caller_any |= (set(t["refs"]) & caller_set)
    caller_seen_rate = len(caller_any) / len(caller_set) if caller_set else 0.0
    # edge_ftl: saw an edge early but the last quarter has no caller refs at all
    caller_refs_series = [1 if (set(t["refs"]) & caller_set) else 0 for t in turns]
    edge_ftl = bool(caller_refs_series) and any(caller_refs_series) \
        and not any(_tail(caller_refs_series))
    firsts = sorted(edge_first.values())
    return {"edge_coverage": round(coverage, 3), "n_edges": len(edges),
            "edges_seen": n_seen, "caller_seen_rate": round(caller_seen_rate, 3),
            "edge_ftl": edge_ftl, "first_edge_turn": firsts[0] if firsts else None,
            "last_edge_turn": (sorted(edge_last.values())[-1] if edge_last else None),
            "n_turns": len(turns)}


def phase_reps(model_filter: str | None) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    targets = [(m, th, c) for m, th, cfgs in DEFAULT_TARGETS for c in cfgs]
    if model_filter:
        targets = [(m, th, c) for m, th, c in targets if model_filter in m]
    all_rows = []
    sub_cache: dict[str, dict | None] = {}
    for m, th, c in targets:
        n_reps = n_with_sub = n_blocked = 0
        for repdir, res in iter_reps(m, th, c):
            n_reps += 1
            task = res.get("task")
            if task not in sub_cache:
                sub_cache[task] = load_subgraph(task)
            sub = sub_cache[task]
            if not sub or sub.get("status") != "ok":
                n_blocked += 1
                continue
            n_with_sub += 1
            sessions = sorted((repdir / "session").glob("*.jsonl")) if (repdir / "session").exists() else []
            if not sessions:
                continue
            sig = edge_attention_for_rep(sessions, sub)
            all_rows.append({
                "model": m, "thinking": th, "config": c, "task": task, "rep": res.get("rep"),
                "reward_binary": res.get("reward_binary"), "reward_partial": res.get("reward_partial"),
                "n_gold_symbols": sub["n_gold_symbols"], **sig,
            })
        print(f"[B-reps] {m}/{th}/{c}: {n_reps} reps, {n_with_sub} with subgraph, {n_blocked} blocked/no-sub", flush=True)

    # outputs
    with (OUTDIR / "per_rep.jsonl").open("w") as f:
        for r in all_rows:
            f.write(json.dumps(r) + "\n")
    by = defaultdict(list)
    for r in all_rows:
        by[(r["model"], r["thinking"], r["config"])].append(r)
    with (OUTDIR / "per_config.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "thinking", "config", "n_reps", "solved_rate",
                    "mean_edge_coverage", "mean_caller_seen_rate", "edge_ftl_rate"])
        for (m, th, c), rs in sorted(by.items()):
            n = len(rs)
            w.writerow([m, th, c, n,
                        round(sum(1 for r in rs if r["reward_binary"] == 1) / n, 3),
                        round(st.mean([r["edge_coverage"] for r in rs]), 3),
                        round(st.mean([r["caller_seen_rate"] for r in rs]), 3),
                        round(sum(1 for r in rs if r["edge_ftl"]) / n, 3)])

    # finding
    def stats(m, th, c):
        rs = by.get((m, th, c), [])
        return ({"n": len(rs),
                 "solved": sum(1 for r in rs if r["reward_binary"] == 1) / len(rs),
                 "cov": st.mean([r["edge_coverage"] for r in rs]),
                 "caller": st.mean([r["caller_seen_rate"] for r in rs]),
                 "ftl": sum(1 for r in rs if r["edge_ftl"]) / len(rs)} if rs else None)

    def delta(m, th, b, o, k):
        B, O = stats(m, th, b), stats(m, th, o)
        return None if not (B and O) else O[k] - B[k]

    ds = {k: delta("deepseek-v4-flash", "high", "baseline", "observational-memory", k)
          for k in ("cov", "caller", "ftl")}
    gs = {k: delta("gpt-5.5", "low", "baseline", "observational-memory-gpt55-low", k)
          for k in ("cov", "caller", "ftl")}
    pooled_n = len(all_rows)

    L = ["# Analysis B: relationship/edge-level attention",
         "",
         "Gold unit = graph EDGES. For each task, codegraph (on the repo at "
         "base_commit_hash) finds the 1-hop CALLERS of every changed symbol -> the "
         "blast-radius subgraph. Per rep, edge_coverage = fraction of gold edges "
         "whose two endpoints (caller + changed symbol) the agent co-referenced in "
         "the same turn; caller_seen_rate = fraction of distinct callers ever named; "
         "edge_ftl = referenced a caller early then none in the final quarter.",
         "",
         f"Coverage: {pooled_n} reps analyzed (only tasks whose subgraph built "
         "successfully; blocked tasks listed in subgraphs/*.json).",
         "",
         "## OM vs baseline",
         "model | thinking | arm | n | solved | edge_cov | caller_seen | edge_ftl",
         "---|---|---|---|---|---|---|---"]
    for m, th, b, o in [("gpt-5.5", "low", "baseline", "observational-memory-gpt55-low"),
                        ("deepseek-v4-flash", "high", "baseline", "observational-memory")]:
        for c in (b, o):
            s = stats(m, th, c)
            if s:
                L.append(f"{m}|{th}|{c}|{s['n']}|{s['solved']:.3f}|{s['cov']:.3f}|{s['caller']:.3f}|{s['ftl']:.3f}")
    L += ["", "## thinking axis (gpt-5.5 baseline)", "thinking | n | edge_cov | caller_seen | edge_ftl",
          "---|---|---|---|---"]
    for th in ("low", "medium", "xhigh"):
        s = stats("gpt-5.5", th, "baseline")
        if s:
            L.append(f"{th}|{s['n']}|{s['cov']:.3f}|{s['caller']:.3f}|{s['ftl']:.3f}")
    L += [
        "",
        "## Finding (edge level)",
        "",
        "Edge deltas (OM - baseline): deepseek edge_cov "
        f"{ds['cov']:+.3f}, caller_seen {ds['caller']:+.3f}, edge_ftl {ds['ftl']:+.3f}; "
        f"gpt-5.5/om-gpt55-low edge_cov {gs['cov']:+.3f}, caller_seen {gs['caller']:+.3f}, "
        f"edge_ftl {gs['ftl']:+.3f}.",
        "",
        "edge_coverage and caller_seen_rate are the relationship-attention score. "
        "If OM lifts these (the agent looks at MORE of the caller graph), that is "
        "direct evidence OM externalizes relationship attention. edge_ftl dropping "
        "means the agent holds the caller relationship to the end (attention "
        "maintenance) rather than seeing it once and drifting. The thinking axis "
        "tests whether raw compute buys the same relationship attention.",
        "",
        "Caveat: edge_coverage is bounded by how many callers the task's gold "
        "subgraph actually has and by token-match on caller names; some repos "
        "failed to clone/build and are excluded (see status counts). Callees and "
        "type-dependency edges are the upgrade path (callers = fan-in only here).",
    ]
    (OUTDIR / "FINDING.md").write_text("\n".join(L) + "\n")
    print(f"\nwrote {pooled_n} rep signals -> {OUTDIR}/ (per_rep.jsonl, per_config.csv, FINDING.md)")


# --- self-test -------------------------------------------------------------

def selftest() -> None:
    # edge attention logic on a synthetic trajectory
    sub = {"edges": [{"caller": "CallA", "gold": "Gold1", "caller_file": "f.go"},
                     {"caller": "CallB", "gold": "Gold1", "caller_file": "g.go"},
                     {"caller": "CallC", "gold": "Gold2", "caller_file": "h.go"}],
           "n_gold_symbols": 2}
    # fake session: turn0 refs CallA+Gold1 (edge0 seen), turn5 refs CallB+Gold1
    # (edge1), CallC/Gold2 never co-referenced. caller refs in tail = none.
    import tempfile
    tf = Path(tempfile.mkstemp(suffix=".jsonl")[1])
    lines = []
    for i, refs in enumerate([[], ["CallA", "Gold1"], [], [], [], ["CallB", "Gold1"],
                              [], [], [], [], [], []]):
        msg = {"role": "assistant", "content": [{"type": "toolCall", "name": "bash",
                  "arguments": {"command": " ".join(refs) or "ls"}}]}
        lines.append(json.dumps({"type": "message", "message": msg}))
    tf.write_text("\n".join(lines))
    sig = edge_attention_for_rep([tf], sub)
    assert sig["n_edges"] == 3, sig
    assert sig["edges_seen"] == 2, sig
    assert abs(sig["edge_coverage"] - 2 / 3) < 1e-3, sig
    assert sig["caller_seen_rate"] == round(2 / 3, 3), sig
    assert sig["edge_ftl"] is True, sig  # callers referenced early, none in tail
    tf.unlink()
    # repo_slug
    assert repo_slug("https://github.com/PyCQA/bandit.git") == "bandit"
    assert repo_slug("https://github.com/prometheus/prometheus.git") == "prometheus"
    print("SELFTEST PASS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--phase", choices=["subgraph", "reps"])
    ap.add_argument("--limit", type=int, help="cap tasks (subgraph phase)")
    ap.add_argument("--model", help="filter reps phase by model substring")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest(); return 0
    if args.phase == "subgraph":
        phase_subgraph(args.limit); return 0
    if args.phase == "reps":
        phase_reps(args.model); return 0
    ap.error("pick --selftest, --phase subgraph, or --phase reps")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Analysis C: do OM streams carry relationship-graph content?

Mines the observational-memory custom events inside each OM config's session
jsonl (`om.observations.recorded`, `om.reflections.recorded`) and classifies each
record's content for RELATIONSHIP-graph content -- mentions of caller/callee,
dependency/import, type/inheritance, or data-flow between symbols -- vs file-level
or generic content.

Then correlates: do reps whose OM streams carry more edge-content show better
outcomes (reward_partial) and higher executor edge-attention (analysis B)? This
tests whether OM approximates a poor man's codegraph, i.e. whether external
memory carries the *relationship* attention the hypothesis is about.

Read-only on session logs.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "harness"))
from attention_signals import iter_reps  # noqa: E402

OUTDIR = REPO / "analysis" / "attention-om-content"

# OM configs across the rep set (baseline has zero OM records -> excluded).
OM_TARGETS: list[tuple[str, str, list[str]]] = [
    ("gpt-5.5", "low", ["observational-memory-gpt55-low",
                        "observational-memory-gpt54mini-low",
                        "observational-memory-gpt54-low"]),
    ("deepseek-v4-flash", "high", ["observational-memory",
                                    "advisor-observational-memory"]),
]

# relationship-content lexicon. ponytail: lexical, not semantic. Ceiling: misses
# paraphrased relationships; a symbol-linker / embedding classifier is the
# upgrade. Patterns deliberately target relations BETWEEN things.
REL_PATTERNS = [
    ("caller_callee", re.compile(r"\b(calls?|called by|caller|callee|invoke[ds]?|invoked by|invokes|dispatch(?:es)? to|delegates? to|handled by|triggers?)\b", re.I)),
    ("dependency", re.compile(r"\b(depends? on|dependency|dependencies|imports?|imported by|requires?|required by|used by|uses|referenced? by|references?)\b", re.I)),
    ("type_inheritance", re.compile(r"\b(extends|implements|subclass|superclass|interface|trait|inherits|inheritance|subtype|base class|derived from|concrete impl)\b", re.I)),
    ("dataflow", re.compile(r"\b(returns?|passed to|propagat\w+|flows? (?:to|from|into)|forwarded? to|consumed by|produces?|emits?|pipeline|transform\w* into)\b", re.I)),
    ("register_hook", re.compile(r"\b(registers? (?:a )?(?:hook|handler|callback)|register\w* (?:handler|callback|hook)|subscribes?|emits? (?:event|signal))\b", re.I)),
]
# file-only / generic content marker (so we can contrast)
FILE_PAT = re.compile(r"\b(in file|files?|directory|folder|path|at line)\b", re.I)


def classify_content(text: str) -> dict:
    hits = []
    for kind, pat in REL_PATTERNS:
        if pat.search(text):
            hits.append(kind)
    return {
        "is_rel": bool(hits),
        "rel_kinds": hits,
        "has_file_mention": bool(FILE_PAT.search(text)),
    }


def iter_om_records(session_paths: list[Path]):
    """Yield (record_type, content) from OM custom events in a session."""
    for sp in session_paths:
        for raw in sp.read_text(errors="replace").splitlines():
            raw = raw.strip()
            if not raw:
                continue
            try:
                ev = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "custom":
                continue
            ct = ev.get("customType", "")
            data = ev.get("data") or {}
            if ct == "om.observations.recorded":
                for o in (data.get("observations") or []):
                    yield "observation", (o.get("content") or "")
            elif ct == "om.reflections.recorded":
                for r in (data.get("reflections") or []):
                    yield "reflection", (r.get("content") or "")


def scan_rep(session_paths: list[Path]) -> dict:
    n_obs = n_ref = n_rel_obs = n_rel_ref = 0
    rel_kinds = defaultdict(int)
    for rtype, content in iter_om_records(session_paths):
        if not content:
            continue
        c = classify_content(content)
        if rtype == "observation":
            n_obs += 1
            if c["is_rel"]:
                n_rel_obs += 1
        else:
            n_ref += 1
            if c["is_rel"]:
                n_rel_ref += 1
        for k in c["rel_kinds"]:
            rel_kinds[k] += 1
    total = n_obs + n_ref
    return {
        "n_observations": n_obs, "n_reflections": n_ref,
        "n_rel_observations": n_rel_obs, "n_rel_reflections": n_rel_ref,
        "rel_frac": round((n_rel_obs + n_rel_ref) / total, 3) if total else 0.0,
        "rel_kinds": dict(rel_kinds),
    }


def scan_all() -> list[dict]:
    rows = []
    for m, th, cfgs in OM_TARGETS:
        for c in cfgs:
            n_reps = n_with_om = 0
            for repdir, res in iter_reps(m, th, c):
                n_reps += 1
                sessions = sorted((repdir / "session").glob("*.jsonl")) if (repdir / "session").exists() else []
                if not sessions:
                    continue
                s = scan_rep(sessions)
                if s["n_observations"] + s["n_reflections"] == 0:
                    continue
                n_with_om += 1
                rows.append({
                    "model": m, "thinking": th, "config": c,
                    "task": res.get("task"), "rep": res.get("rep"),
                    "reward_binary": res.get("reward_binary"),
                    "reward_partial": res.get("reward_partial"),
                    **s,
                })
            print(f"[C] {m}/{th}/{c}: {n_reps} reps, {n_with_om} with OM records", flush=True)
    return rows


def write_outputs(rows: list[dict]) -> None:
    OUTDIR.mkdir(parents=True, exist_ok=True)
    with (OUTDIR / "per_rep.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["thinking"], r["config"])].append(r)
    with (OUTDIR / "per_config.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["model", "thinking", "config", "n_reps", "solved_rate",
                    "mean_partial", "mean_n_observations", "mean_n_reflections",
                    "mean_rel_frac", "rel_kinds_pooled"])
        kinds_pool = defaultdict(int)
        for r in rows:
            for k, v in r["rel_kinds"].items():
                kinds_pool[k] += v
        for (m, th, c), rs in sorted(by.items()):
            n = len(rs)
            w.writerow([m, th, c, n,
                        round(sum(1 for r in rs if r["reward_binary"] == 1) / n, 3),
                        round(st.mean([r["reward_partial"] for r in rs]), 3),
                        round(st.mean([r["n_observations"] for r in rs]), 1),
                        round(st.mean([r["n_reflections"] for r in rs]), 1),
                        round(st.mean([r["rel_frac"] for r in rs]), 3),
                        json.dumps(kinds_pool)])


def write_finding(rows: list[dict]) -> None:
    by = defaultdict(list)
    for r in rows:
        by[(r["model"], r["thinking"], r["config"])].append(r)

    def stats(m, th, c):
        rs = by.get((m, th, c), [])
        if not rs:
            return None
        return {"n": len(rs),
                "solved": sum(1 for r in rs if r["reward_binary"] == 1) / len(rs),
                "partial": st.mean([r["reward_partial"] for r in rs]),
                "rel_frac": st.mean([r["rel_frac"] for r in rs]),
                "n_obs": st.mean([r["n_observations"] for r in rs])}

    # within-config correlation: high-rel-frac vs low-rel-frac reps -> outcome
    def split_corr(rs):
        if len(rs) < 8:
            return None
        fracs = sorted(r["rel_frac"] for r in rs)
        med = st.median(fracs)
        hi = [r for r in rs if r["rel_frac"] > med]
        lo = [r for r in rs if r["rel_frac"] <= med]
        if not hi or not lo:
            return None
        return (st.mean([r["reward_partial"] for r in hi]) -
                st.mean([r["reward_partial"] for r in lo]))

    L = ["# Analysis C: do OM streams carry relationship-graph content?",
         "",
         "Each OM observation/reflection is classified lexically for relationship "
         "content (caller/callee, dependency/import, type/inheritance, dataflow, "
         "register/hook) vs file-level or generic. rel_frac = share of OM records "
         "carrying at least one relationship signal.",
         "",
         "## OM stream composition by config",
         "model | thinking | config | n | solved | partial | rel_frac | mean_n_obs",
         "---|---|---|---|---|---|---|---"]
    for (m, th, c), rs in sorted(by.items()):
        s = stats(m, th, c)
        if s:
            L.append(f"{m}|{th}|{c}|{s['n']}|{s['solved']:.3f}|{s['partial']:.3f}|{s['rel_frac']:.3f}|{s['n_obs']:.0f}")

    L += ["", "## within-config split: mean(partial | rel_frac above median) - mean(partial | at/below median)",
          "config | n | delta_partial(high_rel - low_rel)", "---|---|---"]
    for (m, th, c), rs in sorted(by.items()):
        d = split_corr(rs)
        L.append(f"{c} | {len(rs)} | {d:+.3f}" if d is not None else f"{c} | {len(rs)} | (too few)")

    L += [
        "",
        "## Finding (OM content)",
        "",
        "rel_frac answers: how much of what OM records is *relationship* content "
        "(the codegraph unit) vs file/generic. If rel_frac is high AND reps with "
        "higher rel_frac solve more (positive within-config delta), that is evidence "
        "OM externalizes relationship attention -- the 'poor man's codegraph' claim. "
        "If rel_frac is high but the delta is ~0, OM carries relationships but they "
        "don't drive outcomes (scaffolding, not mechanism). If rel_frac is low, OM is "
        "mostly file/generic and the hypothesis is not supported at this layer.",
        "",
        "Caveat: lexical classification undercounts paraphrased relationships (a "
        "symbol-linker/embedding classifier is the upgrade). The cross-check with "
        "analysis B (do high-rel-frac reps also show higher executor edge_coverage?) "
        "is the stronger test and is joined in the SYNTHESIS.",
    ]
    (OUTDIR / "FINDING.md").write_text("\n".join(L) + "\n")


def selftest() -> None:
    c = classify_content("NewLinter calls ParseConfig to build the rule set; "
                         "ParseConfig is also invoked by RunCheck.")
    assert c["is_rel"] and "caller_callee" in c["rel_kinds"], c
    c = classify_content("The task is to add a feature in the repo.")
    assert not c["is_rel"], c
    c = classify_content("ASTNode extends BaseNode and implements Visitor.")
    assert "type_inheritance" in c["rel_kinds"], c
    c = classify_content("imports the config from settings.py")
    assert "dependency" in c["rel_kinds"], c
    # synthetic session with one OM observation event
    import tempfile
    tf = Path(tempfile.mkstemp(suffix=".jsonl")[1])
    ev = {"type": "custom", "customType": "om.observations.recorded",
          "data": {"observations": [{"content": "X calls Y"}, {"content": "a file"}]}}
    ev2 = {"type": "custom", "customType": "om.reflections.recorded",
           "data": {"reflections": [{"content": "Z depends on W"}]}}
    tf.write_text(json.dumps(ev) + "\n" + json.dumps(ev2) + "\n")
    recs = list(iter_om_records([tf]))
    assert len(recs) == 3, recs
    s = scan_rep([tf])
    assert s["n_observations"] == 2 and s["n_reflections"] == 1, s
    assert s["n_rel_observations"] == 1 and s["n_rel_reflections"] == 1, s
    assert s["rel_frac"] == round(2 / 3, 3), s
    tf.unlink()
    print("SELFTEST PASS")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)
    if args.selftest:
        selftest(); return 0
    rows = scan_all()
    if not rows:
        print("no OM records found", file=sys.stderr); return 1
    write_outputs(rows)
    write_finding(rows)
    print(f"\nwrote {len(rows)} rep signals -> {OUTDIR}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

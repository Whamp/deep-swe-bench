#!/usr/bin/env python3
"""Offline eval for the CMB bash-hook prototype.

Builds an independent-ish golden set from actual pi session bash calls using
`build_gold.py`, then scores the prototype parser against it.

This is not perfect truth; it is a cheap referee for iteration.
"""
from __future__ import annotations

import argparse, json
from collections import Counter
from pathlib import Path
from typing import Any

from build_gold import label as make_gold
from prototype_parser import decide

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
DEFAULT_CONFIGS = [
    "baseline",
    "observational-memory-gpt54mini-low",
    "codebase-memory-om",
    "codebase-memory-om-reindex",
]


def text_content(content: Any) -> str:
    if isinstance(content, str): return content
    if isinstance(content, list):
        s = []
        for b in content:
            if isinstance(b, dict): s.append(str(b.get("text") or b.get("content") or ""))
            else: s.append(str(b))
        return "".join(s)
    return str(content or "")


def iter_bash_pairs(session_file: Path):
    pending: list[dict] = []
    for line in session_file.open(errors="ignore"):
        try: ev = json.loads(line)
        except Exception: continue
        if ev.get("type") != "message": continue
        msg = ev.get("message") or {}
        role = msg.get("role")
        if role == "assistant":
            for b in msg.get("content") or []:
                if isinstance(b, dict) and b.get("type") == "toolCall" and b.get("name") == "bash":
                    args = b.get("arguments") or {}
                    cmd = args.get("command", "") if isinstance(args, dict) else str(args)
                    pending.append({"id": b.get("id") or b.get("toolCallId"), "command": cmd})
        elif role == "toolResult" and msg.get("toolName") == "bash":
            tcid = msg.get("toolCallId")
            idx = next((i for i, p in enumerate(pending) if p.get("id") == tcid), None)
            if idx is None and pending: idx = 0
            if idx is not None:
                p = pending.pop(idx)
                yield p["command"], text_content(msg.get("content"))


def collect_samples(configs: list[str], subset_path: Path, runs: int) -> list[dict]:
    tasks = [x.strip() for x in subset_path.read_text().splitlines() if x.strip() and not x.startswith("#")]
    samples = []
    root = ROOT / "results" / "gpt-5.5" / "low"
    sid = 0
    for cfg in configs:
        for task in tasks:
            for rep in range(runs):
                sdir = root / cfg / task / f"rep{rep}" / "session"
                if not sdir.exists(): continue
                for sf in sorted(sdir.glob("*.jsonl")):
                    for command, output in iter_bash_pairs(sf):
                        sid += 1
                        samples.append({
                            "id": f"s{sid:05d}", "config": cfg, "task": task, "rep": rep,
                            "session": str(sf.relative_to(ROOT)),
                            "command": command, "output": output[:20000],
                        })
    return samples


def prf(tp, fp, fn):
    p = tp / (tp + fp) if tp + fp else 1.0
    r = tp / (tp + fn) if tp + fn else 1.0
    f = 2*p*r/(p+r) if p+r else 0.0
    return p, r, f


def evaluate(samples: list[dict], gold: list[dict]) -> tuple[str, dict]:
    gmap = {g["id"]: g for g in gold}
    rows = []
    for s in samples:
        d = decide(s["command"], s.get("output", ""))
        g = gmap[s["id"]]
        pred = d.augment
        rows.append((s, g, d, pred, g["positive"]))

    tp = sum(pred and pos for _,_,_,pred,pos in rows)
    fp = sum(pred and not pos for _,_,_,pred,pos in rows)
    fn = sum((not pred) and pos for _,_,_,pred,pos in rows)
    tn = sum((not pred) and not pos for _,_,_,pred,pos in rows)
    p, r, f = prf(tp, fp, fn)

    tok_hits = tok_total = tok_pred = 0
    file_hits = file_total = file_pred = 0
    for s, g, d, pred, pos in rows:
        if not pos: continue
        gs, ps = set(g["tokens"]), set(d.tokens)
        tok_hits += len(gs & ps); tok_total += len(gs); tok_pred += len(ps)
        gf, pf = set(g["files"][:8]), set(d.files)
        file_hits += len(gf & pf); file_total += len(gf); file_pred += len(pf)
    tok_p, tok_r, tok_f = prf(tok_hits, max(tok_pred - tok_hits, 0), max(tok_total - tok_hits, 0))
    file_p, file_r, file_f = prf(file_hits, max(file_pred - file_hits, 0), max(file_total - file_hits, 0))

    by_reason = Counter(g["reason"] for _, g, _, _, _ in rows)
    by_decision = Counter(d.reason for _, _, d, _, _ in rows)

    def examples(filter_fn, n=10):
        out = []
        for s, g, d, pred, pos in rows:
            if filter_fn(s, g, d, pred, pos):
                out.append((s, g, d))
                if len(out) >= n: break
        return out

    summary = []
    summary.append("# CMB bash-hook parser eval\n")
    summary.append(f"Samples: **{len(samples)}** real bash calls from 12_v0 configs `{', '.join(DEFAULT_CONFIGS)}`.\n")
    summary.append("## Command classification\n")
    summary.append("| metric | value |\n|---|---:|\n")
    summary.append(f"| true positive | {tp} |\n| false positive | {fp} |\n| false negative | {fn} |\n| true negative | {tn} |\n")
    summary.append(f"| precision | {p:.3f} |\n| recall | {r:.3f} |\n| F1 | {f:.3f} |\n")
    summary.append("\n## Token/file extraction on positive commands\n")
    summary.append("| target | precision | recall | F1 |\n|---|---:|---:|---:|\n")
    summary.append(f"| search tokens | {tok_p:.3f} | {tok_r:.3f} | {tok_f:.3f} |\n")
    summary.append(f"| output files (top 8) | {file_p:.3f} | {file_r:.3f} | {file_f:.3f} |\n")
    summary.append("\n## Label mix\n")
    summary.append("Gold reasons: " + ", ".join(f"{k}={v}" for k,v in by_reason.most_common()) + "\n\n")
    summary.append("Parser decisions: " + ", ".join(f"{k}={v}" for k,v in by_decision.most_common()) + "\n")

    for title, filt in [
        ("False positives", lambda s,g,d,pred,pos: pred and not pos),
        ("False negatives", lambda s,g,d,pred,pos: (not pred) and pos),
        ("Token misses", lambda s,g,d,pred,pos: pos and bool(set(g["tokens"]) - set(d.tokens))),
    ]:
        summary.append(f"\n## {title}\n")
        ex = examples(filt, 12)
        if not ex:
            summary.append("None.\n")
            continue
        for s, g, d in ex:
            cmd = s["command"].replace("\n", " ")[:220]
            summary.append(f"- `{s['id']}` {s['config']}/{s['task']}/r{s['rep']}\n")
            summary.append(f"  - cmd: `{cmd}`\n")
            summary.append(f"  - gold: pos={g['positive']} reason={g['reason']} tokens={g['tokens'][:6]} files={g['files'][:5]}\n")
            summary.append(f"  - pred: augment={d.augment} reason={d.reason} tokens={d.tokens} files={d.files[:5]}\n")

    data = {
        "samples": len(samples), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": p, "recall": r, "f1": f,
        "token_precision": tok_p, "token_recall": tok_r, "token_f1": tok_f,
        "file_precision": file_p, "file_recall": file_r, "file_f1": file_f,
        "gold_reasons": dict(by_reason), "parser_decisions": dict(by_decision),
    }
    return "".join(summary), data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", default=str(ROOT / "subsets" / "12_v0.txt"))
    ap.add_argument("--configs", default=",".join(DEFAULT_CONFIGS))
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--write-fixtures", action="store_true")
    args = ap.parse_args()

    configs = [c for c in args.configs.split(",") if c]
    samples = collect_samples(configs, Path(args.subset), args.runs)
    gold = [make_gold(s) for s in samples]
    md, data = evaluate(samples, gold)

    if args.write_fixtures:
        fx = OUT / "fixtures"; fx.mkdir(exist_ok=True)
        with (fx / "sampled_commands.jsonl").open("w") as f:
            for s in samples:
                slim = dict(s); slim["output"] = slim.get("output", "")[:4000]
                f.write(json.dumps(slim) + "\n")
        with (fx / "gold.jsonl").open("w") as f:
            for g in gold: f.write(json.dumps(g) + "\n")
    (OUT / "eval_summary.md").write_text(md)
    (OUT / "eval_summary.json").write_text(json.dumps(data, indent=2, sort_keys=True))
    print(md)

if __name__ == "__main__":
    main()

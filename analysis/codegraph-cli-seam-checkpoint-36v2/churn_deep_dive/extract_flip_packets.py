#!/usr/bin/env python3
"""Build paired trajectory packets for every old-skill <-> seam-skill solve flip."""
from __future__ import annotations
import json, re
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
SUMMARY = json.loads((ROOT / "analysis/codegraph-cli-seam-checkpoint-36v2/summary.json").read_text())
PAIR = SUMMARY["pairs"]["codegraph-cli-skill__vs__codegraph-cli-skill-seam-checkpoint"]
GAINS = PAIR["solve_gains"]   # old fail -> seam solve
LOSSES = PAIR["solve_losses"]  # old solve -> seam fail
BASE = ROOT / "results/gpt-5.5/low"
LEFT = "codegraph-cli-skill"      # old skill
RIGHT = "codegraph-cli-skill-seam-checkpoint"  # seam skill


def result(cfg, task, rep):
    return json.loads((BASE / cfg / task / f"rep{rep}" / "result.json").read_text())

def session_file(cfg, task, rep):
    files = sorted((BASE / cfg / task / f"rep{rep}" / "session").glob("*.jsonl"))
    return files[-1] if files else None

def patch_file(cfg, task, rep):
    return BASE / cfg / task / f"rep{rep}" / "artifacts/model.patch"

def patch_stats(path: Path):
    txt = path.read_text(errors="ignore") if path.exists() else ""
    files = []; adds = dels = 0
    for line in txt.splitlines():
        if line.startswith("diff --git "):
            parts = line.split()
            if len(parts) >= 4:
                files.append(parts[3][2:] if parts[3].startswith("b/") else parts[3])
        elif line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
    return {"bytes": len(txt.encode()), "files": files, "files_count": len(files), "adds": adds, "dels": dels, "changed_lines": adds + dels}

def parse_session(path: Path):
    tool_counts = Counter(); bash_cmds = []; codegraph_cmds = []; test_cmds = []; total_assistant = 0
    events = []
    if path is None:
        return {"assistant_turns": 0, "tool_counts": {}, "events": [], "bash_cmds": [], "codegraph_cmds": [], "test_cmds": []}
    for i, line in enumerate(path.read_text(errors="ignore").splitlines()):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        m = obj.get("message") if isinstance(obj.get("message"), dict) else None
        if not m:
            continue
        if m.get("role") == "assistant":
            total_assistant += 1
            content = m.get("content")
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "toolCall":
                        name = item.get("name"); args = item.get("arguments") or {}
                        tool_counts[name] += 1
                        events.append({"idx": i, "name": name, "args": args})
                        if name == "bash":
                            cmd = str(args.get("command", ""))
                            bash_cmds.append(cmd)
                            if re.search(r"(^|[;&|\s])(codegraph|cg)(\s|$)", cmd):
                                codegraph_cmds.append(cmd)
                            if re.search(r"\b(test|pytest|go test|npm test|pnpm test|cargo test|mvn test|gradle test|tsc|ruff|eslint|jest|vitest)\b", cmd):
                                test_cmds.append(cmd)
    return {"assistant_turns": total_assistant, "tool_counts": dict(tool_counts), "events": events, "bash_cmds": bash_cmds, "codegraph_cmds": codegraph_cmds, "test_cmds": test_cmds}

def verifier_summary(cfg, task, rep):
    p = BASE / cfg / task / f"rep{rep}" / "verifier/reward.json"
    out = {}
    if p.exists():
        try:
            out = json.loads(p.read_text())
        except Exception:
            pass
    runlog = BASE / cfg / task / f"rep{rep}" / "verifier/run.log"
    tail = ""
    if runlog.exists():
        lines = runlog.read_text(errors="ignore").splitlines()
        tail = "\n".join(lines[-60:])
    return out, tail

def compact_metrics(r):
    keys = ["reward_binary", "reward_partial", "f2p_passed", "f2p_total", "p2p_passed", "p2p_total", "combined_total_tokens", "combined_cost_usd", "agent_wall_s", "turns", "tool_calls", "patch_bytes", "agent_timed_out"]
    return {k: r.get(k) for k in keys}

def rel_path(p):
    return str(p.relative_to(ROOT)) if p else None

def build_packet(cell, direction):
    """direction: 'seam_gain' (old fail->seam solve) or 'seam_loss' (old solve->seam fail)."""
    task = cell["task"]; rep = cell["rep"]
    lr = result(LEFT, task, rep); rr = result(RIGHT, task, rep)
    ls = session_file(LEFT, task, rep); rs = session_file(RIGHT, task, rep)
    lt = parse_session(ls); rt = parse_session(rs)
    lp = patch_stats(patch_file(LEFT, task, rep)); rp = patch_stats(patch_file(RIGHT, task, rep))
    lv, lv_tail = verifier_summary(LEFT, task, rep); rv, rv_tail = verifier_summary(RIGHT, task, rep)

    md = []
    md.append(f"# {task} rep{rep}: {direction.replace('_', ' ')}\n")
    md.append(f"- Title: {cell['title']}\n- Difficulty: {cell['difficulty']} / language {cell['language']}")
    md.append(f"- Partial: old {cell['a_partial']:.6f} → seam {cell['b_partial']:.6f} (Δ {cell['delta_partial']:+.6f})")
    md.append(f"- Tokens Δ: {cell['delta_tokens']:+,}; cost Δ: {cell['delta_cost']:+.6f}; wall Δ: {cell['delta_wall_s']:+.1f}s; tool-call Δ: {cell['delta_tool_calls']:+}\n")
    md.append("## Metrics\n```json\n" + json.dumps({"old_skill": compact_metrics(lr), "seam_skill": compact_metrics(rr)}, indent=2) + "\n```\n")
    md.append("## Patch stats\n```json\n" + json.dumps({"old_skill": lp, "seam_skill": rp}, indent=2) + "\n```\n")
    md.append("## Tool summary\n```json\n" + json.dumps({"old_skill": {"tool_counts": lt["tool_counts"], "assistant_turns": lt["assistant_turns"], "codegraph_cmds_n": len(lt["codegraph_cmds"])}, "seam_skill": {"tool_counts": rt["tool_counts"], "assistant_turns": rt["assistant_turns"], "codegraph_cmds_n": len(rt["codegraph_cmds"])}}, indent=2) + "\n```\n")
    md.append("## Old-skill bash timeline\n```\n" + "\n".join(lt["bash_cmds"][:140]) + "\n```\n")
    md.append("## Seam-skill bash timeline\n```\n" + "\n".join(rt["bash_cmds"][:140]) + "\n```\n")
    md.append("## Old-skill CodeGraph commands\n```\n" + "\n".join(lt["codegraph_cmds"][:60]) + "\n```\n")
    md.append("## Seam-skill CodeGraph commands\n```\n" + "\n".join(rt["codegraph_cmds"][:60]) + "\n```\n")
    md.append("## Old-skill changed files\n" + "\n".join(f"- {f}" for f in lp["files"]) + "\n")
    md.append("## Seam-skill changed files\n" + "\n".join(f"- {f}" for f in rp["files"]) + "\n")
    md.append("## Old-skill verifier tail\n```\n" + lv_tail + "\n```\n")
    md.append("## Seam-skill verifier tail\n```\n" + rv_tail + "\n```\n")

    obj = {
        "task": task, "rep": rep, "direction": direction, "cell": cell,
        "old_skill": {"result": compact_metrics(lr), "session": rel_path(ls), "trace_summary": {"tool_counts": lt["tool_counts"], "assistant_turns": lt["assistant_turns"], "codegraph_cmds": lt["codegraph_cmds"][:60], "test_cmds": lt["test_cmds"][:40]}, "patch_stats": lp, "verifier": lv},
        "seam_skill": {"result": compact_metrics(rr), "session": rel_path(rs), "trace_summary": {"tool_counts": rt["tool_counts"], "assistant_turns": rt["assistant_turns"], "codegraph_cmds": rt["codegraph_cmds"][:60], "test_cmds": rt["test_cmds"][:40]}, "patch_stats": rp, "verifier": rv},
    }
    stem = f"{task}__rep{rep}__{direction}"
    (OUT / f"{stem}.md").write_text("\n".join(md))
    return obj

OUT.mkdir(parents=True, exist_ok=True)
packets = []
for g in GAINS:
    packets.append(build_packet(g, "seam_gain"))
for l in LOSSES:
    packets.append(build_packet(l, "seam_loss"))
(OUT / "flip_packets_index.json").write_text(json.dumps(packets, indent=2, sort_keys=True))
print(f"wrote {len(packets)} packets ({len(GAINS)} gains, {len(LOSSES)} losses) to {OUT}")

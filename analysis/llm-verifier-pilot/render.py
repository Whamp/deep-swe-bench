"""Render a deep-swe-bench cell (Pi session JSONL + result.json + patch) into
verifier-visible {problem, trace} text, following the trajectory rendering
style of llm_verifier.loaders._tb_format_trace.

The verifier must never see reward/verifier outcomes or cell identity
(model/config). Those live only in the pool metadata, never in the trace.
"""
import glob
import json
import os
import re

# per-block character caps (chars ~ tokens*4 for English/code)
CAP_PROBLEM = 5000
CAP_THINK = 260
CAP_SAY = 500
CAP_ARGS = 260
CAP_OUTPUT = 420
CAP_PATCH = 1400


def _clip(text, cap):
    text = (text or "").rstrip()
    if len(text) <= cap:
        return text
    return text[:cap].rstrip() + f" …[+{len(text) - cap} chars]"


def _args_summary(name, args):
    if not isinstance(args, dict):
        return _clip(str(args), CAP_ARGS)
    if name == "bash":
        return _clip(args.get("command", ""), CAP_ARGS)
    if name in ("read", "write", "edit"):
        path = args.get("path", "")
        extra = args.get("content") or args.get("newText") or ""
        return _clip(f"{path} {extra}", CAP_ARGS)
    return _clip(json.dumps(args, ensure_ascii=False), CAP_ARGS)


def load_problem(records):
    """First user message holds /task/instruction.md content."""
    for r in records:
        if r.get("type") != "message":
            continue
        m = r.get("message", {})
        if m.get("role") != "user":
            continue
        c = m.get("content")
        text = "".join(b.get("text", "") for b in c if isinstance(b, dict)) \
            if isinstance(c, list) else str(c)
        text = re.sub(r'<file name="/task/instruction\.md">', "", text)
        text = re.sub(r"</file>", "", text)
        return _clip(text.strip(), CAP_PROBLEM)
    return "(task instruction not found)"


def render_steps(records):
    """Chronological agent steps: thinking/say/tool-call/output."""
    steps = []
    results = {}
    for r in records:
        if r.get("type") != "message":
            continue
        m = r.get("message", {})
        role = m.get("role")
        if role == "toolResult":
            text = "".join(b.get("text", "") for b in m.get("content", [])
                           if isinstance(b, dict))
            results[m.get("toolCallId")] = (text, m.get("isError", False))
        elif role == "assistant":
            block = {"think": "", "say": "", "calls": []}
            for b in m.get("content", []):
                t = b.get("type")
                if t == "thinking":
                    block["think"] += b.get("thinking", "")
                elif t == "text":
                    block["say"] += b.get("text", "")
                elif t == "toolCall":
                    block["calls"].append(
                        {"id": b.get("id"), "name": b.get("name", "?"),
                         "args": _args_summary(b.get("name", "?"),
                                               b.get("arguments", {}))})
            steps.append(block)
    lines = []
    for i, s in enumerate(steps, 1):
        chunk = [f"--- Agent Step {i} ---"]
        if s["think"].strip():
            chunk.append(f"[Think] {_clip(s['think'], CAP_THINK)}")
        if s["say"].strip():
            chunk.append(f"[Say] {_clip(s['say'], CAP_SAY)}")
        for call in s["calls"]:
            chunk.append(f"[Tool] {call['name']}: {call['args']}")
            out, is_err = results.get(call["id"], ("(no result)", False))
            tag = "Output, ERROR" if is_err else "Output"
            chunk.append(f"[{tag}] {_clip(out, CAP_OUTPUT)}")
        lines.append("\n".join(chunk))
    return lines


def elide_middle(step_lines, budget):
    """Keep head 30% and tail ~60% of the char budget; elide the middle."""
    total = sum(len(s) + 1 for s in step_lines)
    if total <= budget:
        return "\n".join(step_lines)
    head_budget = int(budget * 0.3)
    tail_budget = int(budget * 0.62)
    head, used = [], 0
    for s in step_lines:
        if used + len(s) > head_budget:
            break
        head.append(s)
        used += len(s) + 1
    tail, used = [], 0
    for s in reversed(step_lines):
        if used + len(s) > tail_budget:
            break
        tail.append(s)
        used += len(s) + 1
    tail.reverse()
    n_elided = len(step_lines) - len(head) - len(tail)
    marker = (f"\n… [{n_elided} middle agent steps elided for length; "
              "trace continues near the end] …\n")
    return "\n".join(head) + marker + "\n".join(tail)


def render_cell(rep_dir, trace_budget=6500):
    """Return dict(problem, trace, meta) for one cell rep directory."""
    with open(os.path.join(rep_dir, "result.json")) as f:
        result = json.load(f)
    session_files = glob.glob(os.path.join(rep_dir, "session", "*.jsonl"))
    if not session_files:
        raise FileNotFoundError(f"no session jsonl under {rep_dir}")
    records = [json.loads(l) for l in open(session_files[0])]
    problem = load_problem(records)
    step_lines = render_steps(records)
    trace = elide_middle(step_lines, trace_budget)

    patch_path = os.path.join(rep_dir, "artifacts", "model.patch")
    if os.path.isfile(patch_path):
        with open(patch_path, errors="replace") as f:
            patch = f.read()
        if patch.strip():
            trace += (f"\n\n--- Final patch produced by the agent "
                      f"(artifacts/model.patch) ---\n{_clip(patch, CAP_PATCH)}")

    meta = {
        "cell": os.path.relpath(rep_dir),
        "model": result.get("model"),
        "config": result.get("config"),
        "reward_binary": result.get("reward_binary"),
        "reward_partial": result.get("reward_partial"),
        "turns": result.get("turns"),
        "agent_timed_out": result.get("agent_timed_out"),
        "output_tokens": result.get("output_tokens"),
    }
    return {"problem": problem, "trace": trace, "meta": meta}


if __name__ == "__main__":
    import sys
    out = render_cell(sys.argv[1])
    print(out["problem"][:300])
    print("=" * 60)
    print(out["trace"][:2000])
    print("=" * 60)
    print("trace chars:", len(out["trace"]), "| meta:", out["meta"])

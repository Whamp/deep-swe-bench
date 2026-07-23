#!/usr/bin/env python3
from __future__ import annotations
import csv, json, re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
BASE = ROOT / "results/Qwen3.6-27B-AWQ-BF16-INT4/high/baseline-qwen36-27b"
TREAT = ROOT / "results/Qwen3.6-27B-AWQ-BF16-INT4/high/qwen36-27b-pi-codex-goal"
SELECTED = [
    ("go-critic-doc-link-checker", 1, ["solve discordance", "top-four positive partial delta"]),
    ("langchain-request-coalescing", 2, ["termination-path discordance", "top-four positive partial delta"]),
    ("superjson-error-stack-serialization", 2, ["top-four positive partial delta"]),
    ("goreleaser-retry-publish-auditing", 1, ["top-four positive partial delta"]),
    ("mobly-grouped-test-barriers", 1, ["termination-path discordance"]),
    ("mobly-grouped-test-barriers", 2, ["termination-path discordance", "top-four negative partial delta"]),
    ("goreleaser-retry-publish-auditing", 2, ["top-four negative partial delta"]),
    ("participle-grammar-conflict-analysis", 0, ["top-four negative partial delta"]),
    ("tengo-callable-instance-isolation", 0, ["top-four negative partial delta"]),
]

EARLIEST_DIVERGENCE = {
    ("go-critic-doc-link-checker", 1): ("seam_location", "The patches chose different checker/type-resolution scopes before their verifier outcomes diverged."),
    ("langchain-request-coalescing", 2): ("validation", "Treatment reached focused and broader validation; baseline remained unvalidated before its agent timeout."),
    ("superjson-error-stack-serialization", 2): ("implementation", "The sides implemented materially different Error serialization behavior before grading diverged."),
    ("goreleaser-retry-publish-auditing", 1): ("seam_location", "Treatment centralized attempt tracking while baseline distributed retry behavior across publisher paths."),
    ("mobly-grouped-test-barriers", 1): ("termination", "Both sides remained reward-negative, but baseline reached verifier timeout after agent completion while treatment hit the agent cap."),
    ("mobly-grouped-test-barriers", 2): ("validation", "Treatment entered repeated focused-test debugging and exhausted the agent budget; baseline completed and reached grading."),
    ("goreleaser-retry-publish-auditing", 2): ("implementation", "Treatment stopped after API scaffolding while baseline implemented retry paths."),
    ("participle-grammar-conflict-analysis", 0): ("implementation", "Treatment introduced recursive analysis behavior that later overflowed the verifier stack."),
    ("tengo-callable-instance-isolation", 0): ("seam_location", "Treatment worked at direct invocation setup rather than the transitive callable graph seam."),
}

EXPECTED_DIFFICULTY_COLUMNS = ["pass_rate", "language", "slug", "repository", "title"]


def difficulty():
    with (ROOT / "data/deepswe-v1.1-task-difficulty.tsv").open() as f:
        reader = csv.DictReader(f, delimiter="\t")
        if reader.fieldnames != EXPECTED_DIFFICULTY_COLUMNS:
            raise RuntimeError(f"unexpected difficulty TSV columns: {reader.fieldnames}")
        return {r["slug"]: r for r in reader}

def load(path):
    return json.loads(path.read_text()) if path.exists() else {}

def patch_info(cell):
    p = cell / "artifacts/model.patch"
    text = p.read_text(errors="ignore") if p.exists() else ""
    files, hunks, adds, dels = [], [], 0, 0
    for line in text.splitlines():
        if line.startswith("diff --git "):
            files.append(line.split()[3].removeprefix("b/"))
        elif line.startswith("@@"):
            hunks.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
    return {"path": str(p.relative_to(ROOT)), "bytes": len(text.encode()), "files": files,
            "adds": adds, "dels": dels, "hunks": hunks[:80]}

def message_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        str(x.get("text") or x.get("thinking") or "")
        for x in content if isinstance(x, dict)
    )


def session_info(cell):
    files = sorted((cell / "session").glob("*.jsonl"))
    if not files:
        return {"path": None, "tool_counts": {}, "commands": [], "tests": [], "assistant_tail": [],
                "expanded_adapter_prompt": False, "literal_create_goal_command": False, "goal_custom_events": 0}
    p = files[-1]; counts = Counter(); commands=[]; tests=[]; assistants=[]; first_user=""; goal_custom_events=0
    for line in p.read_text(errors="ignore").splitlines():
        try: o=json.loads(line)
        except Exception: continue
        if o.get("customType") == "pi-codex-goal": goal_custom_events += 1
        m=o.get("message") if isinstance(o.get("message"),dict) else None
        if m and m.get("role") == "user" and not first_user:
            first_user = message_text(m.get("content"))
        if not m or m.get("role") != "assistant": continue
        texts=[]
        for x in m.get("content",[]) if isinstance(m.get("content"),list) else []:
            if not isinstance(x,dict): continue
            if x.get("type") in ("text","thinking") and (x.get("text") or x.get("thinking")):
                texts.append(str(x.get("text") or x.get("thinking")))
            if x.get("type") == "toolCall":
                name=x.get("name"); counts[name]+=1; args=x.get("arguments") or {}
                if name == "bash":
                    cmd=str(args.get("command", "")); commands.append(cmd)
                    if re.search(r"(?:pytest|go test|npm test|pnpm test|yarn test|vitest|jest|tsc|lint|typecheck)",cmd,re.I): tests.append(cmd)
        if texts: assistants.append("\n".join(texts))
    expanded = (
        "Turn the user task into exactly one durable pi-codex-goal objective" in first_user
        and "call the goal creation tool" in first_user
    )
    return {"path": str(p.relative_to(ROOT)), "tool_counts": dict(counts), "commands": commands,
            "tests": tests, "assistant_tail": assistants[-4:], "expanded_adapter_prompt": expanded,
            "literal_create_goal_command": first_user.lstrip().startswith("/create-goal"),
            "goal_custom_events": goal_custom_events}

def verifier_info(cell):
    ctrf=load(cell/"verifier/ctrf.json")
    failed=[]
    for t in ctrf.get("results",{}).get("tests",[]):
        if t.get("status") == "failed":
            failed.append({k:t.get(k) for k in ("name","message","trace") if t.get(k)})
    run=cell/"verifier/run.log"
    lines=run.read_text(errors="ignore").splitlines() if run.exists() else []
    return {"reward": load(cell/"verifier/reward.json"), "failed": failed,
            "run_log": str(run.relative_to(ROOT)), "run_tail": lines[-80:]}

def metrics(r):
    keys=("reward_binary","reward_partial","f2p_passed","f2p_total","p2p_passed","p2p_total",
          "combined_total_tokens","agent_wall_s","turns","tool_calls","patch_bytes","agent_timed_out","agent_exit","verifier_exit")
    return {k:r.get(k) for k in keys}

def termination(result):
    if result.get("agent_timed_out") or result.get("agent_exit") == "timeout":
        return "agent_timeout"
    if result.get("verifier_exit") == "timeout":
        return "verifier_timeout"
    if result.get("reward_binary") == -1:
        return "reward_negative_other"
    return "completed_and_graded"


def validate_selection():
    tasks=[x.strip() for x in (ROOT/"subsets/12_v2.txt").read_text().splitlines() if x.strip()]
    rows=[]
    actual={}
    def add(key, trigger):
        actual.setdefault(key, []).append(trigger)
    for task in tasks:
        for rep in range(3):
            a=load(BASE/task/f"rep{rep}"/"result.json")
            b=load(TREAT/task/f"rep{rep}"/"result.json")
            key=(task,rep)
            delta=(b.get("reward_partial") or 0)-(a.get("reward_partial") or 0)
            rows.append((delta,key))
            if (a.get("reward_binary")==1) != (b.get("reward_binary")==1):
                add(key,"solve discordance")
            if (a.get("reward_binary")==-1 or b.get("reward_binary")==-1) and termination(a) != termination(b):
                add(key,"termination-path discordance")
    for _,key in sorted((x for x in rows if x[0]>0), reverse=True)[:4]:
        add(key,"top-four positive partial delta")
    for _,key in sorted(x for x in rows if x[0]<0)[:4]:
        add(key,"top-four negative partial delta")
    expected={(task,rep):set(triggers) for task,rep,triggers in SELECTED}
    observed={key:set(triggers) for key,triggers in actual.items()}
    if observed != expected:
        raise RuntimeError(f"packet selection drift: expected={expected}, observed={observed}")


def stage_ledger(label, side):
    result=side["result"]; patch=side["patch"]; session=side["session"]
    treatment = label == "treatment"
    initialized = session.get("expanded_adapter_prompt") and session.get("tool_counts",{}).get("create_goal") == 1
    return [
        {"stage":"initialization", "status":"observed" if (initialized or not treatment) else "absent",
         "evidence":"expanded adapter prompt plus one create_goal call" if treatment else "stock task prompt; goal treatment not applicable"},
        {"stage":"contract_representation", "status":"observed" if session.get("assistant_tail") else "unknown",
         "evidence":"session contains assistant reasoning/text" if session.get("assistant_tail") else "no assistant text recovered"},
        {"stage":"seam_location", "status":"observed" if session.get("commands") else "unknown",
         "evidence":f"{len(session.get('commands',[]))} shell commands recorded; read/edit calls are counted in tool_counts"},
        {"stage":"implementation", "status":"observed" if patch.get("bytes",0) else "absent",
         "evidence":f"model.patch has {patch.get('bytes',0)} bytes across {len(patch.get('files',[]))} files"},
        {"stage":"targeted_validation", "status":"observed" if session.get("tests") else "absent",
         "evidence":f"{len(session.get('tests',[]))} test/build/lint command(s) recorded"},
        {"stage":"regression_validation", "status":"unknown",
         "evidence":"packet preserves validation commands; breadth requires task-specific review"},
        {"stage":"completion_audit", "status":"observed" if session.get("tool_counts",{}).get("update_goal") else ("not_applicable" if not treatment else "absent"),
         "evidence":"update_goal call recorded" if session.get("tool_counts",{}).get("update_goal") else ("baseline has no goal lifecycle" if not treatment else "no update_goal call recorded")},
        {"stage":"termination", "status":"observed", "evidence":termination(result)},
    ]


validate_selection()
diff=difficulty(); packets=[]
for task,rep,triggers in SELECTED:
    sides={}
    for label,root in (("baseline",BASE),("treatment",TREAT)):
        cell=root/task/f"rep{rep}"
        sides[label]={"result":metrics(load(cell/"result.json")),"patch":patch_info(cell),
                      "session":session_info(cell),"verifier":verifier_info(cell)}
        sides[label]["stage_ledger"] = stage_ledger(label, sides[label])
    a=sides["baseline"]["result"]; b=sides["treatment"]["result"]
    stage,note=EARLIEST_DIVERGENCE[(task,rep)]
    packets.append({"task":task,"rep":rep,"selection_triggers":triggers,"difficulty":diff.get(task,{}),
                    "delta_partial":(b["reward_partial"] or 0)-(a["reward_partial"] or 0),
                    "earliest_paired_stage_divergence":{"stage":stage,"interpretation":note},"sides":sides})
(OUT/"trajectory_packets.json").write_text(json.dumps(packets,indent=2))
print(f"wrote {len(packets)} packets to {OUT/'trajectory_packets.json'}")

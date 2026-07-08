#!/usr/bin/env python3
from __future__ import annotations
import json, re, subprocess
from pathlib import Path
from collections import Counter

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
SUMMARY=json.loads((ROOT/'analysis/codegraph-cli-skill-36v2/summary.json').read_text())
LOSSES=SUMMARY['pairs']['baseline__vs__codegraph-cli-skill']['solve_losses']
BASE=ROOT/'results/gpt-5.5/low'


def result(cfg, task, rep):
    return json.loads((BASE/cfg/task/f'rep{rep}/result.json').read_text())

def session_file(cfg, task, rep):
    files=sorted((BASE/cfg/task/f'rep{rep}/session').glob('*.jsonl'))
    return files[-1]

def patch_file(cfg, task, rep):
    return BASE/cfg/task/f'rep{rep}/artifacts/model.patch'

def patch_stats(path: Path):
    txt=path.read_text(errors='ignore') if path.exists() else ''
    files=[]; adds=dels=0
    cur=None
    for line in txt.splitlines():
        if line.startswith('diff --git '):
            parts=line.split()
            if len(parts)>=4:
                cur=parts[3][2:] if parts[3].startswith('b/') else parts[3]
                files.append(cur)
        elif line.startswith('+') and not line.startswith('+++'):
            adds+=1
        elif line.startswith('-') and not line.startswith('---'):
            dels+=1
    return {'bytes': len(txt.encode()), 'files': files, 'files_count': len(files), 'adds': adds, 'dels': dels, 'changed_lines': adds+dels}

def patch_excerpt(path: Path, max_lines=220):
    if not path.exists(): return ''
    lines=path.read_text(errors='ignore').splitlines()
    # include headers and hunk context, bounded
    return '\n'.join(lines[:max_lines])

def parse_session(path: Path):
    events=[]; tool_counts=Counter(); bash_cmds=[]; codegraph_cmds=[]; reads=[]; edits=[]; writes=[]; test_cmds=[]; commit_cmds=[]
    total_assistant=0
    for i,line in enumerate(path.read_text(errors='ignore').splitlines()):
        try: obj=json.loads(line)
        except Exception: continue
        m=obj.get('message') if isinstance(obj.get('message'), dict) else None
        if not m: continue
        role=m.get('role')
        if role=='assistant':
            total_assistant+=1
            content=m.get('content')
            if isinstance(content,list):
                for item in content:
                    if isinstance(item,dict) and item.get('type')=='toolCall':
                        name=item.get('name'); args=item.get('arguments') or {}
                        tool_counts[name]+=1
                        rec={'idx':i,'name':name,'args':args}
                        events.append(rec)
                        if name=='bash':
                            cmd=str(args.get('command',''))
                            bash_cmds.append(cmd)
                            if re.search(r'(^|[;&|\s])(codegraph|cg)(\s|$)',cmd): codegraph_cmds.append(cmd)
                            if re.search(r'\b(test|pytest|go test|npm test|pnpm test|cargo test|mvn test|gradle test|tsc|ruff|eslint)\b',cmd): test_cmds.append(cmd)
                            if 'git commit' in cmd or 'git status' in cmd or 'git diff' in cmd: commit_cmds.append(cmd)
                        elif name=='read': reads.append(args)
                        elif name=='edit': edits.append(args)
                        elif name=='write': writes.append(args)
    return {'assistant_turns': total_assistant, 'tool_counts': dict(tool_counts), 'events': events, 'bash_cmds': bash_cmds, 'codegraph_cmds': codegraph_cmds, 'reads': reads, 'edits': edits, 'writes': writes, 'test_cmds': test_cmds, 'git_cmds': commit_cmds}

def verifier_summary(cfg, task, rep):
    p=BASE/cfg/task/f'rep{rep}/verifier/reward.json'
    out={}
    if p.exists():
        try: out=json.loads(p.read_text())
        except Exception: pass
    runlog=BASE/cfg/task/f'rep{rep}/verifier/run.log'
    tail=''
    if runlog.exists():
        lines=runlog.read_text(errors='ignore').splitlines()
        tail='\n'.join(lines[-80:])
    return out, tail

def compact_metrics(r):
    keys=['reward_binary','reward_partial','f2p_passed','f2p_total','p2p_passed','p2p_total','combined_total_tokens','combined_cost_usd','agent_wall_s','turns','tool_calls','patch_bytes','agent_timed_out','verifier_exit']
    return {k:r.get(k) for k in keys}

def rel_path(p: Path):
    return str(p.relative_to(ROOT))

def write_packet(loss):
    task=loss['task']; rep=loss['rep']
    b=result('baseline',task,rep); c=result('codegraph-cli-skill',task,rep)
    bs=session_file('baseline',task,rep); cs=session_file('codegraph-cli-skill',task,rep)
    bt=parse_session(bs); ct=parse_session(cs)
    bp=patch_stats(patch_file('baseline',task,rep)); cp=patch_stats(patch_file('codegraph-cli-skill',task,rep))
    bv, bv_tail=verifier_summary('baseline',task,rep); cv, cv_tail=verifier_summary('codegraph-cli-skill',task,rep)
    md=[]
    md.append(f"# {task} rep{rep}: clean Pi solve lost by CodeGraph CLI\n")
    md.append(f"- Title: {loss['title']}\n- Difficulty: {loss['difficulty']} / language {loss['language']}\n- Partial: baseline {loss['a_partial']:.6f} → codegraph {loss['b_partial']:.6f} (Δ {loss['delta_partial']:.6f})\n- Tokens Δ: {loss['delta_tokens']:+,}; cost Δ: {loss['delta_cost']:+.6f}; wall Δ: {loss['delta_wall_s']:+.1f}s; tool-call Δ: {loss['delta_tool_calls']:+}\n")
    md.append("## Metrics\n")
    md.append("```json\n"+json.dumps({'baseline':compact_metrics(b),'codegraph':compact_metrics(c)},indent=2)+"\n```\n")
    md.append("## Patch stats\n")
    md.append("```json\n"+json.dumps({'baseline':bp,'codegraph':cp},indent=2)+"\n```\n")
    md.append("## Tool summary\n")
    md.append("```json\n"+json.dumps({'baseline':{'tool_counts':bt['tool_counts'],'assistant_turns':bt['assistant_turns']},'codegraph':{'tool_counts':ct['tool_counts'],'assistant_turns':ct['assistant_turns'],'codegraph_cmds':ct['codegraph_cmds']}},indent=2)+"\n```\n")
    md.append("## Baseline bash/test timeline\n")
    md.append("```\n"+'\n'.join(bt['bash_cmds'][:120])+"\n```\n")
    md.append("## CodeGraph bash/test timeline\n")
    md.append("```\n"+'\n'.join(ct['bash_cmds'][:160])+"\n```\n")
    md.append("## Baseline changed files\n")
    md.append('\n'.join(f"- {f}" for f in bp['files'])+"\n")
    md.append("## CodeGraph changed files\n")
    md.append('\n'.join(f"- {f}" for f in cp['files'])+"\n")
    md.append("## Baseline patch excerpt\n```diff\n"+patch_excerpt(patch_file('baseline',task,rep),260)+"\n```\n")
    md.append("## CodeGraph patch excerpt\n```diff\n"+patch_excerpt(patch_file('codegraph-cli-skill',task,rep),300)+"\n```\n")
    md.append("## CodeGraph verifier tail\n```\n"+cv_tail+"\n```\n")
    obj={'loss':loss,'baseline':{'result':compact_metrics(b),'session':rel_path(bs),'trace':bt,'patch_stats':bp,'verifier':bv},'codegraph':{'result':compact_metrics(c),'session':rel_path(cs),'trace':ct,'patch_stats':cp,'verifier':cv}}
    stem=f"{task}__rep{rep}"
    (OUT/f'{stem}.md').write_text('\n'.join(md))
    (OUT/f'{stem}.json').write_text(json.dumps(obj,indent=2,sort_keys=True))
    return obj

all_objs=[write_packet(l) for l in LOSSES]
(OUT/'loss_packets_index.json').write_text(json.dumps(all_objs,indent=2,sort_keys=True))
print('wrote',len(all_objs),'packets to',OUT)

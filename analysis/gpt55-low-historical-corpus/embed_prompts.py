#!/usr/bin/env python3
from __future__ import annotations
import json, math, os, re, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CORPUS = ROOT / 'analysis/gpt55-low-historical-corpus/corpus_overlap_vs_clean_low.json'
OUTDIR = ROOT / 'analysis/gpt55-low-historical-corpus'
EMBED_URL = os.environ.get('OCTEN_EMBED_URL', 'http://100.77.237.75:8090/v1/embeddings')
MODEL = os.environ.get('OCTEN_EMBED_MODEL', 'octen-embed')
EXPLICIT_NAMES = {'system_preamble.md', 'orchestration.md', 'omp-system-prompt.md', 'SYSTEM_PROMPT.md'}
SURFACE_RE = re.compile(r'(prompt|instruction|message|goal|memory|recursive|workflow|ponytail|codegraph|advisor|codebase|initial|hook)', re.I)
SKIP_PARTS = {'node_modules', '.git'}
SKIP_NAMES = {'package-lock.json', '.package-lock.json', 'package.json'}


def read_text(p: Path, limit: int = 12000) -> str:
    try:
        text = p.read_text(errors='replace')
    except Exception:
        return ''
    if len(text) > limit:
        return text[:limit] + f'\n\n[TRUNCATED at {limit} chars from {p}]'
    return text


def explicit_files(cdir: Path):
    return [cdir / name for name in ['system_preamble.md', 'orchestration.md', 'omp-system-prompt.md'] if (cdir / name).exists()]


def selected_extension_files(cdir: Path):
    ext = cdir / 'extensions'
    if not ext.exists():
        return []
    out = []
    for p in ext.rglob('*'):
        if not p.is_file():
            continue
        if any(part in SKIP_PARTS for part in p.parts):
            continue
        if p.name in SKIP_NAMES:
            continue
        if p.suffix.lower() not in {'.md', '.ts', '.js', '.json'}:
            continue
        if p.name in EXPLICIT_NAMES or SURFACE_RE.search(str(p.relative_to(cdir))):
            out.append(p)
    return sorted(out)


def make_docs():
    rows = json.load(open(CORPUS))['rows']
    by_config = {r['config']: r for r in rows}
    docs = []
    for cfg, r in sorted(by_config.items()):
        cdir = ROOT / 'configs' / cfg
        if not cdir.exists():
            continue
        ex = explicit_files(cdir)
        if ex:
            parts = []
            for p in ex:
                parts.append(f'### {p.relative_to(ROOT)}\n' + read_text(p))
            docs.append({
                'id': f'{cfg}::explicit_prompt',
                'config': cfg,
                'doc_type': 'explicit_prompt',
                'category': r['category'],
                'solve_delta': r['solve_delta'],
                'solves': r['solves_on_overlap'],
                'cost_delta': r['cost_delta'],
                'overlap_cells': r['overlap_cells'],
                'invalid_reward_cells': r['invalid_reward_cells'],
                'paths': [str(p.relative_to(ROOT)) for p in ex],
                'text': '\n\n'.join(parts),
            })
        surf = []
        seen = set()
        for p in ex + selected_extension_files(cdir):
            if p in seen: continue
            seen.add(p)
            surf.append(p)
        if surf:
            parts = []
            total = 0
            for p in surf:
                t = read_text(p)
                if not t.strip():
                    continue
                chunk = f'### {p.relative_to(ROOT)}\n{t}'
                if total + len(chunk) > 28000:
                    parts.append(f'### {p.relative_to(ROOT)}\n[OMITTED: corpus text cap reached]')
                    break
                parts.append(chunk); total += len(chunk)
            docs.append({
                'id': f'{cfg}::prompt_surface',
                'config': cfg,
                'doc_type': 'prompt_surface',
                'category': r['category'],
                'solve_delta': r['solve_delta'],
                'solves': r['solves_on_overlap'],
                'cost_delta': r['cost_delta'],
                'overlap_cells': r['overlap_cells'],
                'invalid_reward_cells': r['invalid_reward_cells'],
                'paths': [str(p.relative_to(ROOT)) for p in surf],
                'text': '\n\n'.join(parts),
            })
    return docs


def embed(texts):
    payload = json.dumps({'model': MODEL, 'input': texts}).encode()
    req = urllib.request.Request(EMBED_URL, data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=240) as resp:
        data = json.load(resp)
    return [row['embedding'] for row in data['data']], data.get('usage', {})


def cosine(a, b):
    dot = sum(x*y for x, y in zip(a,b))
    na = math.sqrt(sum(x*x for x in a)); nb = math.sqrt(sum(y*y for y in b))
    return dot / (na*nb) if na and nb else 0.0


def cluster(ids, sims, threshold=0.86):
    parent = {i:i for i in ids}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    def union(a,b):
        ra, rb = find(a), find(b)
        if ra != rb: parent[rb] = ra
    for a,b,s in sims:
        if s >= threshold:
            union(a,b)
    groups = {}
    for i in ids:
        groups.setdefault(find(i), []).append(i)
    return sorted(groups.values(), key=lambda g:(-len(g), g[0]))


def summarize(doc_subset, vectors):
    ids = [d['id'] for d in doc_subset]
    vec = {d['id']: vectors[d['id']] for d in doc_subset}
    sims = []
    for i,a in enumerate(ids):
        for b in ids[i+1:]:
            sims.append((a,b,cosine(vec[a], vec[b])))
    sims.sort(key=lambda x:x[2], reverse=True)
    groups = cluster(ids, sims)
    nearest = {}
    for a in ids:
        ns = sorted([(b, cosine(vec[a], vec[b])) for b in ids if b != a], key=lambda x:x[1], reverse=True)[:5]
        nearest[a] = [{'id': b, 'similarity': s} for b,s in ns]
    return {'threshold': 0.86, 'clusters': groups, 'nearest': nearest, 'top_pairs': [{'a':a,'b':b,'similarity':s} for a,b,s in sims[:40]]}


def main():
    docs = make_docs()
    # Embed in small batches because llama.cpp slots are finite and prompt surfaces can be long.
    all_vecs = {}
    usages = []
    for i in range(0, len(docs), 8):
        batch = docs[i:i+8]
        vecs, usage = embed([d['text'] for d in batch])
        usages.append(usage)
        for d,v in zip(batch, vecs):
            all_vecs[d['id']] = v
    for d in docs:
        d['text_chars'] = len(d.pop('text'))
    explicit = [d for d in docs if d['doc_type'] == 'explicit_prompt']
    surface = [d for d in docs if d['doc_type'] == 'prompt_surface']
    analysis = {
        'embedding_endpoint': EMBED_URL,
        'model': MODEL,
        'dimensions': len(next(iter(all_vecs.values()))) if all_vecs else None,
        'usage': usages,
        'documents': docs,
        'explicit_prompt_analysis': summarize(explicit, all_vecs) if explicit else None,
        'prompt_surface_analysis': summarize(surface, all_vecs) if surface else None,
    }
    (OUTDIR/'prompt_embedding_analysis.json').write_text(json.dumps(analysis, indent=2))
    # Keep vectors separate because they are bulky but reproducible.
    (OUTDIR/'prompt_embeddings.json').write_text(json.dumps({'model': MODEL, 'vectors': all_vecs}))
    print('documents', len(docs), 'explicit', len(explicit), 'surface', len(surface), 'dims', analysis['dimensions'])
    print('wrote', (OUTDIR/'prompt_embedding_analysis.json').relative_to(ROOT))
    for name, part in [('explicit', analysis['explicit_prompt_analysis']), ('surface', analysis['prompt_surface_analysis'])]:
        print('\n'+name, 'clusters')
        if not part: continue
        for g in part['clusters'][:12]:
            print(len(g), ' | '.join(g[:6]))
        print(name, 'top pairs')
        for p in part['top_pairs'][:10]:
            print(f"{p['similarity']:.3f} {p['a']} <-> {p['b']}")

if __name__ == '__main__':
    main()

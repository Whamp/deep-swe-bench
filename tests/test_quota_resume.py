"""Tests for the transient-limit auto-resume loop in harness/run_batch.

Covers QuotaResumer decision logic (mocked I/O) and the main() resume loop,
without making real network calls or sleeping.
"""

from __future__ import annotations

import json
import sys
import tempfile
import contextlib
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

import pytest

from harness import run_batch
from harness.quota import Window


NOW = datetime(2026, 7, 3, 17, 0, tzinfo=timezone.utc)


def _args(**over):
    base = dict(
        model="openai-codex/gpt-5.5",
        no_auto_resume=False,
        max_quota_wait_s=21600.0,
        quota_poll_s=300.0,
        rate_limit_backoff_s=60.0,
    )
    base.update(over)
    return mock.Mock(**base)


class _FakeState:
    def __init__(self):
        self.stages = []

    def set_stage(self, stage):
        self.stages.append(stage)


# --- QuotaResumer classification ----------------------------------------- #


class TestQuotaResumerQuota:
    def test_quota_near_reset_retries_and_sets_quota_wait(self):
        resumer = run_batch.QuotaResumer(_args())
        state = _FakeState()
        windows = [Window("5h", 100, NOW + timedelta(minutes=30))]
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="usage limit reached"), \
             mock.patch.object(run_batch.quota, "codex_windows", return_value=(windows, "api")), \
             mock.patch.object(run_batch, "datetime", wraps=datetime) as dt, \
             mock.patch.object(resumer, "_sleep_until_reset") as sleeper:
            dt.now.return_value = NOW
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is True
        assert "quota_wait" in state.stages
        sleeper.assert_called_once()

    def test_quota_far_reset_does_not_retry(self):
        resumer = run_batch.QuotaResumer(_args(max_quota_wait_s=3600.0))  # 1h max
        state = _FakeState()
        windows = [Window("Week", 100, NOW + timedelta(days=5))]  # 5 days >> 1h max
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="usage limit"), \
             mock.patch.object(run_batch.quota, "codex_windows", return_value=(windows, "api")), \
             mock.patch.object(run_batch.time, "sleep"):
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is False
        assert "too far away" in decision["reason"]

    def test_quota_no_usage_data_does_not_retry(self):
        resumer = run_batch.QuotaResumer(_args())
        state = _FakeState()
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="usage limit"), \
             mock.patch.object(run_batch.quota, "codex_windows", return_value=([], "none")):
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is False
        assert "no usage data" in decision["reason"]

    def test_quota_unknown_reset_polls_and_retries(self):
        resumer = run_batch.QuotaResumer(_args(quota_poll_s=1.0))
        state = _FakeState()
        # exhausted but reset_at is None
        windows = [Window("5h", 100, None)]
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="usage limit"), \
             mock.patch.object(run_batch.quota, "codex_windows", return_value=(windows, "api")), \
             mock.patch.object(run_batch.time, "sleep"):
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is True
        assert "quota_wait" in state.stages

    def test_sleep_rechecks_and_exits_early_when_not_exhausted(self):
        resumer = run_batch.QuotaResumer(_args(quota_poll_s=1.0))
        reset = NOW + timedelta(hours=10)
        clock = {"t": NOW}
        calls = []

        def fake_sleep(s):
            clock["t"] += timedelta(seconds=s)

        def fake_windows(*a, **k):
            calls.append(1)
            # first check: exhausted; second check: cleared -> early exit
            if len(calls) == 1:
                return ([Window("5h", 100, reset)], "api")
            return ([Window("5h", 10, reset)], "api")

        with mock.patch.object(run_batch, "datetime", wraps=datetime) as dt, \
             mock.patch.object(run_batch.quota, "codex_windows", side_effect=fake_windows), \
             mock.patch.object(run_batch.time, "sleep", side_effect=fake_sleep):
            dt.now.side_effect = lambda *a, **k: clock["t"]
            resumer._sleep_until_reset(reset)
        assert len(calls) == 2  # exhausted check then clear check


class TestQuotaResumerRateLimit:
    def test_rate_limit_backs_off_and_retries(self):
        resumer = run_batch.QuotaResumer(_args(rate_limit_backoff_s=5.0))
        state = _FakeState()
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="rate limit exceeded"), \
             mock.patch.object(run_batch.time, "sleep") as sleeper:
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is True
        sleeper.assert_called_once_with(5.0)


class TestQuotaResumerUnknown:
    def test_unknown_transient_does_not_retry(self):
        resumer = run_batch.QuotaResumer(_args())
        state = _FakeState()
        with mock.patch.object(run_batch, "_latest_transient_error_msg", return_value="some weird error"), \
             mock.patch.object(run_batch.time, "sleep"):
            decision = resumer.on_transient_pause(state)
        assert decision["retry"] is False
        assert "unclassified" in decision["reason"]


# --- main() resume loop -------------------------------------------------- #


class TestMainResumeLoop:
    def _setup_repo(self, root: Path):
        run_batch.REPO = root
        run_batch.STATE_ROOT = root / "results" / "_runs"
        run_batch.RESULTS_ROOT = root / "results"
        run_batch.SMOKE_SUBSET = root / "subsets" / "12_v0.txt"
        run_batch.SMOKE_SUBSET.parent.mkdir(parents=True)
        run_batch.SMOKE_SUBSET.write_text("task-a\n")

    def test_resumes_after_quota_pause_then_completes(self):
        """main() loops: _execute_batch returns 75, resumer retries, then 0."""
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = (run_batch.REPO, run_batch.STATE_ROOT, run_batch.SMOKE_SUBSET, run_batch.RESULTS_ROOT)
            self._setup_repo(root)
            # pre-existing result so the cell is skipped (no Docker needed)
            result = root / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
            result.parent.mkdir(parents=True)
            result.write_text(json.dumps({"agent_exit": 0, "verifier_exit": 0, "total_tokens": 1}))
            argv = [
                "run_batch.py", "--configs", "cfg", "--tasks", "task-a",
                "--runs", "1", "--workers", "1", "--no-smoke-new-configs",
                "--run-id", "resume-test", "--progress-interval", "0",
            ]
            try:
                codes = iter([run_batch.TRANSIENT_EXIT, 0])
                with mock.patch.object(sys, "argv", argv), \
                     mock.patch.object(run_batch, "_execute_batch", side_effect=lambda *a, **k: next(codes)) as exec_mock, \
                     mock.patch.object(run_batch, "QuotaResumer") as ResumerCls:
                    ResumerCls.return_value.on_transient_pause.return_value = {"retry": True, "reason": "test"}
                    ResumerCls.return_value.attempt = 1
                    out = io.StringIO()
                    with contextlib.redirect_stdout(out):
                        run_batch.main()  # should return normally (code 0)
                # _execute_batch called twice: first 75 (resume), then 0
                assert exec_mock.call_count == 2
                assert "re-launching batch (attempt 1)" in out.getvalue()
            finally:
                (run_batch.REPO, run_batch.STATE_ROOT, run_batch.SMOKE_SUBSET, run_batch.RESULTS_ROOT) = old

    def test_no_auto_resume_exits_75_without_looping(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old = (run_batch.REPO, run_batch.STATE_ROOT, run_batch.SMOKE_SUBSET, run_batch.RESULTS_ROOT)
            self._setup_repo(root)
            result = root / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
            result.parent.mkdir(parents=True)
            result.write_text(json.dumps({"agent_exit": 0, "verifier_exit": 0, "total_tokens": 1}))
            argv = [
                "run_batch.py", "--configs", "cfg", "--tasks", "task-a",
                "--runs", "1", "--workers", "1", "--no-smoke-new-configs",
                "--run-id", "noresume-test", "--progress-interval", "0",
                "--no-auto-resume",
            ]
            try:
                with mock.patch.object(sys, "argv", argv), \
                     mock.patch.object(run_batch, "_execute_batch", return_value=run_batch.TRANSIENT_EXIT) as exec_mock, \
                     mock.patch.object(run_batch, "QuotaResumer") as ResumerCls:
                    with pytest.raises(SystemExit) as ei:
                        run_batch.main()
                    assert ei.value.code == run_batch.TRANSIENT_EXIT
                # only called once — no resume loop
                assert exec_mock.call_count == 1
                # resumer never consulted
                ResumerCls.return_value.on_transient_pause.assert_not_called()
            finally:
                (run_batch.REPO, run_batch.STATE_ROOT, run_batch.SMOKE_SUBSET, run_batch.RESULTS_ROOT) = old

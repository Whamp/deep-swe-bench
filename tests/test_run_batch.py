import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import harness.run_batch as run_batch


class SmokeValidationTests(unittest.TestCase):
    def write_cell(self, root: Path, *, runner_log: str | None) -> Path:
        cell = root / "cell"
        (cell / "session").mkdir(parents=True)
        (cell / "logs").mkdir()
        (cell / "session" / "session.jsonl").write_text('{"type":"session"}\n')
        (cell / "result.json").write_text(json.dumps({
            "agent_exit": 0,
            "agent_timed_out": False,
            "total_tokens": 1,
        }))
        if runner_log is not None:
            (cell / "logs" / "pi-rpc-runner.jsonl").write_text(runner_log)
        return cell / "result.json"

    def test_validate_smoke_result_requires_rpc_runner_lifecycle_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_cell(Path(td), runner_log=None)

            errors = run_batch.validate_smoke_result(path)

            self.assertIn("RPC runner log missing", errors)

    def test_validate_smoke_result_accepts_rpc_runner_lifecycle_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            path = self.write_cell(Path(td), runner_log=(
                '{"event":"started","transport":"rpc"}\n'
                '{"event":"prompt_sent"}\n'
                '{"event":"quiescent"}\n'
            ))

            errors = run_batch.validate_smoke_result(path)

            self.assertEqual(errors, [])


class RunnerSelectionTests(unittest.TestCase):
    def test_runner_script_defaults_to_pi(self):
        args = type("Args", (), {})()

        self.assertEqual(run_batch.runner_script(args).name, "run.py")

    def test_runner_script_can_select_omp(self):
        args = type("Args", (), {"agent": "omp"})()

        self.assertEqual(run_batch.runner_script(args).name, "run_omp.py")


class StructuredStateIntegrationTests(unittest.TestCase):
    def test_main_writes_structured_state_for_skipped_existing_cell_without_changing_stdout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old_repo = run_batch.REPO
            old_state_root = run_batch.STATE_ROOT
            old_smoke_subset = run_batch.SMOKE_SUBSET
            run_batch.REPO = root
            run_batch.STATE_ROOT = root / "results" / "_runs"
            run_batch.SMOKE_SUBSET = root / "subsets" / "12_v0.txt"
            run_batch.SMOKE_SUBSET.parent.mkdir(parents=True)
            run_batch.SMOKE_SUBSET.write_text("task-a\n")
            result = root / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
            result.parent.mkdir(parents=True)
            result.write_text(json.dumps({"agent_exit": 0, "verifier_exit": 0, "total_tokens": 1}))
            argv = [
                "run_batch.py",
                "--configs", "cfg",
                "--tasks", "task-a",
                "--runs", "1",
                "--workers", "1",
                "--no-smoke-new-configs",
                "--run-id", "unit-state",
                "--progress-interval", "0",
            ]
            out = io.StringIO()
            try:
                with patch.object(sys, "argv", argv), contextlib.redirect_stdout(out):
                    run_batch.main()
            finally:
                run_batch.REPO = old_repo
                run_batch.STATE_ROOT = old_state_root
                run_batch.SMOKE_SUBSET = old_smoke_subset

            self.assertIn("running 1 cells: 1 tasks × 1 configs × 1 reps; workers=1", out.getvalue())
            self.assertIn("[1/1] task-a / cfg / rep0  skip", out.getvalue())
            state_dir = root / "results" / "_runs" / "unit-state"
            status = json.loads((state_dir / "status.json").read_text())
            self.assertEqual(status["state"], "completed")
            self.assertEqual(status["counts"]["batch_done"], 1)
            self.assertEqual(status["counts"]["batch_skipped"], 1)
            # Skipped cells reuse an existing result but must NOT inflate the
            # ok bucket — they count toward batch_skipped only. The actual
            # outcome is preserved on the cell for detail views.
            self.assertEqual(status["counts"]["ok"], 0)
            events = (state_dir / "events.ndjson").read_text()
            self.assertIn('"event": "run_started"', events)
            self.assertIn('"event": "cell_skipped"', events)
            self.assertIn('"event": "run_completed"', events)


class RunOneCommandTests(unittest.TestCase):
    def test_run_one_forwards_no_initial_context_capture(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            old_repo = run_batch.REPO
            run_batch.REPO = root
            args = type("Args", (), {
                "model": "openrouter/deepseek/deepseek-v4-flash",
                "thinking": "high",
                "force": False,
                "agent": "pi",
                "agent_timeout": None,
                "rpc_quiescence": None,
                "pass_openai_codex_oauth": False,
                "no_initial_context_capture": True,
            })()
            try:
                completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="ok", stderr="")
                with patch.object(run_batch.subprocess, "run", return_value=completed) as run_mock:
                    run_batch.run_one(("task-a", "cfg", 0), args)
            finally:
                run_batch.REPO = old_repo

        cmd = run_mock.call_args[0][0]
        self.assertIn("--no-initial-context-capture", cmd)


class SmokeTaskTests(unittest.TestCase):
    def setUp(self):
        self._old_smoke_subset = run_batch.SMOKE_SUBSET
        self._tmp = tempfile.TemporaryDirectory()
        run_batch.SMOKE_SUBSET = Path(self._tmp.name) / "12_v0.txt"

    def tearDown(self):
        run_batch.SMOKE_SUBSET = self._old_smoke_subset
        self._tmp.cleanup()

    def write_smoke_subset(self, *tasks: str) -> None:
        run_batch.SMOKE_SUBSET.write_text("\n".join(tasks) + "\n")

    def test_prefers_requested_task_from_smoke_subset(self):
        self.write_smoke_subset("old-first", "shared-second", "shared-third")

        task = run_batch.smoke_task(["shared-third", "new-task", "shared-second"])

        self.assertEqual(task, "shared-second")

    def test_falls_back_to_first_requested_task_when_smoke_subset_does_not_overlap(self):
        self.write_smoke_subset("old-first", "old-second")

        task = run_batch.smoke_task(["v2-first", "v2-second"])

        self.assertEqual(task, "v2-first")


class PathIdentityTests(unittest.TestCase):
    """result_path / log_path / config_has_results resolve to the ADR-0001
    results grammar (ticket #5 migrates them onto harness/results_tree.py).

    Characterization for the behavior-preserving refactor: these hand-built
    path assertions must hold before and after the migration.
    """

    def setUp(self):
        self._old_repo = run_batch.REPO
        self._tmp = tempfile.TemporaryDirectory()
        run_batch.REPO = Path(self._tmp.name)

    def tearDown(self):
        run_batch.REPO = self._old_repo
        self._tmp.cleanup()

    def test_result_path_and_log_path_match_grammar(self):
        # leaf deepseek-v4-flash == lib.model_leaf(openrouter/deepseek/deepseek-v4-flash)
        model = "openrouter/deepseek/deepseek-v4-flash"
        root = Path(self._tmp.name)
        rp = run_batch.result_path(model, "high", "cfg", "task-a", 0)
        lp = run_batch.log_path(model, "high", "cfg", "task-a", 0)
        self.assertEqual(
            rp, root / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0" / "result.json"
        )
        self.assertEqual(
            lp, root / "results" / "deepseek-v4-flash" / "high" / "logs" / "task-a__cfg__rep0.log"
        )

    def test_config_has_results_uses_existence_under_config(self):
        model = "openrouter/deepseek/deepseek-v4-flash"
        self.assertFalse(run_batch.config_has_results(model, "high", "cfg"))
        base = Path(self._tmp.name) / "results" / "deepseek-v4-flash" / "high" / "cfg" / "task-a" / "rep0"
        base.mkdir(parents=True)
        (base / "result.json").write_text("{}")
        self.assertTrue(run_batch.config_has_results(model, "high", "cfg"))


if __name__ == "__main__":
    unittest.main()

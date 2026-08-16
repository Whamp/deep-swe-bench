import json
import subprocess
import sys
import tempfile
import textwrap
import unittest
from dataclasses import replace
from pathlib import Path

from harness.degeneration_watchdog import coding_agent_early_gate_watchdog
from harness.pi_rpc_runner import run_pi_rpc


class PiRpcRunnerTests(unittest.TestCase):
    def test_standalone_cli_keeps_direct_import_path(self):
        runner = Path(__file__).parents[1] / "harness" / "pi_rpc_runner.py"

        completed = subprocess.run(
            [sys.executable, str(runner), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("Run a Pi RPC process", completed.stdout)

    def write_fake_rpc(self, directory: Path, body: str) -> Path:
        script = directory / "fake_pi_rpc.py"
        script.write_text(textwrap.dedent(body))
        return script

    def test_waits_through_deferred_activity_and_filters_advisor_usage(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            received = root / "received.jsonl"
            fake = self.write_fake_rpc(
                root,
                f"""
                import json, sys, threading, time

                received_path = {str(received)!r}
                state = {{"isStreaming": False, "pendingMessageCount": 0}}

                def emit(obj):
                    print(json.dumps(obj, separators=(",", ":")), flush=True)

                def record(obj):
                    with open(received_path, "a") as f:
                        f.write(json.dumps(obj, separators=(",", ":")) + "\\n")

                def deferred_activity():
                    time.sleep(0.12)
                    state["isStreaming"] = True
                    emit({{"type": "agent_start"}})
                    emit({{"type": "tool_execution_end", "toolName": "not-advisor", "result": {{}}}})
                    emit({{"type": "tool_execution_end", "toolName": "advisor", "result": {{"details": {{"usage": {{"inputTokens": 3, "outputTokens": 4, "totalTokens": 7, "cost": {{"total": 0.01}}, "provider": "p", "model": "m"}}}}}}, "isError": False}})
                    state["isStreaming"] = False
                    emit({{"type": "agent_end"}})

                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    record(cmd)
                    if cmd.get("type") == "prompt":
                        emit({{"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}})
                        emit({{"type": "extension_ui_request", "id": "confirm-1", "method": "confirm", "title": "replace?"}})
                        state["isStreaming"] = True
                        emit({{"type": "agent_start"}})
                        state["isStreaming"] = False
                        emit({{"type": "agent_end"}})
                        threading.Thread(target=deferred_activity, daemon=False).start()
                    elif cmd.get("type") == "get_state":
                        emit({{"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": dict(state)}})
                    elif cmd.get("type") == "extension_ui_response":
                        pass
                """,
            )

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="hello from /task/instruction.md",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                advisor_usage_path=root / "tool-usage.jsonl",
                timeout_s=5,
                quiescence_s=0.25,
                state_poll_s=0.05,
            )

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(result.quiescent)
            self.assertTrue(result.prompt_accepted)
            self.assertGreaterEqual(result.agent_end_count, 2)

            received_lines = [json.loads(line) for line in received.read_text().splitlines()]
            prompts = [line for line in received_lines if line.get("type") == "prompt"]
            self.assertEqual(prompts[0]["message"], "hello from /task/instruction.md")
            self.assertTrue(any(line.get("type") == "extension_ui_response" and line.get("confirmed") is False
                                for line in received_lines))
            self.assertTrue(any(line.get("type") == "get_state" for line in received_lines))

            advisor_lines = [json.loads(line) for line in (root / "tool-usage.jsonl").read_text().splitlines()]
            self.assertEqual(len(advisor_lines), 1)
            self.assertEqual(advisor_lines[0]["toolName"], "advisor")
            self.assertEqual(advisor_lines[0]["result"]["details"]["usage"]["totalTokens"], 7)

            runner_log = (root / "pi-rpc-runner.jsonl").read_text()
            self.assertIn('"event":"prompt_sent"', runner_log)
            self.assertIn('"event":"quiescent"', runner_log)
            self.assertIn('"transport":"rpc"', runner_log)

    def test_can_quiesce_after_agent_end_without_pi_state_shape(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = self.write_fake_rpc(
                root,
                """
                import json, sys
                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "prompt":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}), flush=True)
                        print(json.dumps({"type": "agent_start"}), flush=True)
                        print(json.dumps({"type": "agent_end"}), flush=True)
                    elif cmd.get("type") == "get_state":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": {"busy": False}}), flush=True)
                """,
            )

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="omp-like rpc",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                timeout_s=5,
                quiescence_s=0.1,
                state_poll_s=0.05,
                quiesce_after_agent_end=True,
            )

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(result.quiescent)
            self.assertEqual(result.agent_end_count, 1)
            runner_log = (root / "pi-rpc-runner.jsonl").read_text()
            self.assertIn('"event":"quiescent"', runner_log)
            self.assertIn('"reason":"agent_end"', runner_log)

    def test_degeneration_watchdog_aborts_and_records_compact_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = self.write_fake_rpc(
                root,
                """
                import json, sys, time
                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "prompt":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}), flush=True)
                        for index in range(4):
                            print(json.dumps({"type": "tool_execution_start", "toolCallId": f"read-{index}", "toolName": "read", "args": {"path": "/app/src/index.ts"}}), flush=True)
                    elif cmd.get("type") == "abort":
                        print(json.dumps({"type": "response", "command": "abort", "success": True}), flush=True)
                        break
                    elif cmd.get("type") == "get_state":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": {"isStreaming": True, "pendingMessageCount": 0}}), flush=True)
                    time.sleep(0.01)
                """,
            )
            policy = replace(
                coding_agent_early_gate_watchdog(),
                max_tool_calls_per_turn=20,
                max_identical_tool_calls_per_turn=3,
            )

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="repeat forever",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                timeout_s=5,
                quiescence_s=0.1,
                state_poll_s=0.05,
                degeneration_watchdog_policy=policy,
            )

            self.assertEqual(result.exit_code, "degeneration")
            self.assertFalse(result.timed_out)
            self.assertIsNotNone(result.degeneration_watchdog)
            assert result.degeneration_watchdog is not None
            self.assertEqual(
                result.degeneration_watchdog["reason"],
                "identical_tool_calls_per_turn",
            )
            runner_log = (root / "pi-rpc-runner.jsonl").read_text()
            self.assertIn('"event":"degeneration_watchdog"', runner_log)
            self.assertNotIn("/app/src/index.ts", runner_log)

    def test_timeout_kills_process_and_reports_timeout(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = self.write_fake_rpc(
                root,
                """
                import json, sys, time
                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "prompt":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}), flush=True)
                    elif cmd.get("type") == "get_state":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": {"isStreaming": True, "pendingMessageCount": 0}}), flush=True)
                    time.sleep(0.02)
                """,
            )

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="never idle",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                timeout_s=0.25,
                quiescence_s=0.1,
                state_poll_s=0.05,
            )

            self.assertEqual(result.exit_code, "timeout")
            self.assertTrue(result.timed_out)
            self.assertFalse(result.quiescent)
            self.assertIn('"event":"timeout"', (root / "pi-rpc-runner.jsonl").read_text())


if __name__ == "__main__":
    unittest.main()

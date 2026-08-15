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

    def test_degeneration_watchdog_writes_bounded_unfinished_response(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = self.write_fake_rpc(
                root,
                """
                import json, sys, time

                def emit(obj):
                    print(json.dumps(obj), flush=True)

                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "prompt":
                        emit({"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True})
                        emit({"type": "turn_start"})
                        emit({"type": "message_start", "message": {"role": "assistant", "content": []}})
                        emit({"type": "message_update", "usage": {"input": 180235, "output": 4000}, "assistantMessageEvent": {"type": "thinking_start", "contentIndex": 0}})
                        emit({"type": "message_update", "usage": {"input": 180235, "output": 8000}, "assistantMessageEvent": {"type": "thinking_delta", "contentIndex": 0, "delta": "BEGIN-" + "a" * 12000}})
                        emit({"type": "message_update", "usage": {"input": 180235, "output": 12000}, "assistantMessageEvent": {"type": "thinking_delta", "contentIndex": 0, "delta": "b" * 7996 + "-TAIL"}})
                    elif cmd.get("type") == "abort":
                        emit({"type": "response", "command": "abort", "success": True})
                        break
                    elif cmd.get("type") == "get_state":
                        emit({"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": {"isStreaming": True, "pendingMessageCount": 0}})
                    time.sleep(0.01)
                """,
            )
            policy = replace(
                coding_agent_early_gate_watchdog(),
                max_assistant_chars_per_turn=20_000,
            )
            diagnostic_path = root / "agent-degeneration-diagnostic.json"

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="sensitive prompt must not be captured",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                timeout_s=5,
                quiescence_s=0.1,
                state_poll_s=0.05,
                degeneration_watchdog_policy=policy,
                degeneration_diagnostic_path=diagnostic_path,
            )

            self.assertEqual(result.exit_code, "degeneration")
            diagnostic = json.loads(diagnostic_path.read_text())
            self.assertEqual(diagnostic["schema_version"], 1)
            self.assertEqual(
                diagnostic["violation"]["reason"],
                "assistant_chars_per_turn",
            )
            response = diagnostic["unfinished_response"]
            self.assertEqual(response["total_chars"], 20_007)
            self.assertEqual(response["delta_event_counts"], {"thinking_delta": 2})
            self.assertEqual(
                response["latest_usage"], {"input": 180235, "output": 12000}
            )
            self.assertEqual(
                response["open_blocks"],
                [{"content_index": 0, "type": "thinking"}],
            )
            self.assertTrue(response["first_chars"].startswith("BEGIN-"))
            self.assertTrue(response["last_chars"].endswith("-TAIL"))
            self.assertLessEqual(len(response["first_chars"]), 16_384)
            self.assertLessEqual(len(response["last_chars"]), 16_384)
            self.assertEqual(diagnostic_path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn("sensitive prompt", diagnostic_path.read_text())
            runner_log = (root / "pi-rpc-runner.jsonl").read_text()
            self.assertIn('"diagnostic_bytes":', runner_log)
            self.assertIn('"diagnostic_sha256":', runner_log)
            self.assertNotIn("BEGIN-", runner_log)
            self.assertNotIn("-TAIL", runner_log)

    def test_watchdog_writes_no_diagnostic_for_normal_completion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fake = self.write_fake_rpc(
                root,
                """
                import json, sys
                state = {"isStreaming": False, "pendingMessageCount": 0}
                for raw in sys.stdin:
                    cmd = json.loads(raw)
                    if cmd.get("type") == "prompt":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}), flush=True)
                        print(json.dumps({"type": "turn_start"}), flush=True)
                        print(json.dumps({"type": "message_update", "usage": {"output": 2}, "assistantMessageEvent": {"type": "text_delta", "contentIndex": 0, "delta": "done"}}), flush=True)
                        print(json.dumps({"type": "message_end", "message": {"role": "assistant", "usage": {"output": 2}}}), flush=True)
                        print(json.dumps({"type": "agent_end"}), flush=True)
                    elif cmd.get("type") == "get_state":
                        print(json.dumps({"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": state}), flush=True)
                """,
            )
            diagnostic_path = root / "agent-degeneration-diagnostic.json"

            result = run_pi_rpc(
                [sys.executable, str(fake)],
                prompt_text="normal completion",
                stderr_path=root / "pi.stderr.txt",
                runner_log_path=root / "pi-rpc-runner.jsonl",
                timeout_s=5,
                quiescence_s=0.05,
                state_poll_s=0.02,
                degeneration_watchdog_policy=coding_agent_early_gate_watchdog(),
                degeneration_diagnostic_path=diagnostic_path,
            )

            self.assertEqual(result.exit_code, 0)
            self.assertTrue(result.quiescent)
            self.assertFalse(diagnostic_path.exists())

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

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import harness.run as run
import harness.run_omp as run_omp


class CredentialRouteTests(unittest.TestCase):
    def test_declared_route_passes_only_environment_name(self):
        secret = "credential-value-must-not-enter-docker-arguments"
        with patch.dict(
            run.os.environ,
            {"WORKER_API_KEY": secret},
            clear=True,
        ):
            flags = run.credential_route_env_flags(
                ("OPENAI_CODEX_OAUTH", "WORKER_API_KEY")
            )

        self.assertEqual(flags, ["-e", "WORKER_API_KEY"])
        self.assertNotIn(secret, repr(flags))

    def test_missing_declared_route_fails_by_route_name(self):
        with (
            patch.dict(run.os.environ, {}, clear=True),
            self.assertRaisesRegex(
                SystemExit,
                "Declared credential route unavailable: WORKER_API_KEY",
            ),
        ):
            run.credential_route_env_flags(("WORKER_API_KEY",))


class ConfigPromptLayerTests(unittest.TestCase):
    def test_clean_config_has_no_append_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            old_repo = run.REPO
            root = Path(td)
            (root / "configs" / "baseline" / "model" / "low").mkdir(
                parents=True
            )
            try:
                run.REPO = root
                cfg = run.load_config("baseline", "openrouter/example/model", "low")
            finally:
                run.REPO = old_repo

        self.assertEqual(cfg["system_preamble"], "")
        self.assertEqual(cfg["orchestration"], "")
        self.assertEqual(run.config_append_text(cfg), "")

    def test_prompt_bearing_config_uses_config_local_layers(self):
        with tempfile.TemporaryDirectory() as td:
            old_repo = run.REPO
            root = Path(td)
            cdir = root / "configs" / "baseline-preamble-orchestration"
            (cdir / "model" / "low").mkdir(parents=True)
            (cdir / "system_preamble.md").write_text("preamble\n")
            (cdir / "orchestration.md").write_text("orchestration\n")
            try:
                run.REPO = root
                cfg = run.load_config("baseline-preamble-orchestration", "openrouter/example/model", "low")
            finally:
                run.REPO = old_repo

        self.assertEqual(run.config_append_text(cfg), "preamble\n\norchestration")

    def test_advisor_config_keeps_effective_leaf_files(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            config_root = root / "configs" / "advisor-config"
            config_leaf = config_root / "model+advisor" / "low"
            config_leaf.mkdir(parents=True)
            expected_files = {}
            for filename in ("models.json", "advisor.json", "settings.json"):
                path = config_leaf / filename
                path.write_text("{}")
                expected_files[filename] = path

            cfg = run.load_config(
                "advisor-config",
                "provider/model",
                "low",
                repository_root=root,
            )

        self.assertEqual(cfg["dir"], config_root)
        self.assertEqual(cfg["leaf_rel"], "model+advisor/low")
        self.assertEqual(cfg["models_json"], expected_files["models.json"])
        self.assertEqual(cfg["advisor_json"], expected_files["advisor.json"])
        self.assertEqual(cfg["settings_json"], expected_files["settings.json"])


class SubjectRunnerConfigResolutionTests(unittest.TestCase):
    def test_pi_run_cell_rejects_missing_config_leaf(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configs" / "cfg").mkdir(parents=True)
            with (
                patch.object(run, "REPO", root),
                patch.object(run, "load_task", return_value=object()),
                self.assertRaises(ValueError) as raised,
            ):
                run.run_cell(
                    "cfg",
                    "task-a",
                    model="openrouter/example/model",
                    thinking="low",
                    rep=0,
                    agent_timeout=1,
                    keep=False,
                    pass_openai_codex_oauth=False,
                    rpc_quiescence=0,
                )

        message = str(raised.exception)
        self.assertIn("Config leaf missing:", message)
        self.assertIn("config='cfg'", message)
        self.assertIn("model_leaf='model'", message)
        self.assertIn("thinking='low'", message)

    def test_omp_run_cell_rejects_ambiguous_config_leaf(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            direct_leaf = root / "configs" / "cfg" / "model" / "low"
            worker_leaf = root / "configs" / "cfg" / "model+worker" / "low"
            direct_leaf.mkdir(parents=True)
            worker_leaf.mkdir(parents=True)
            with (
                patch.object(run_omp, "REPO", root),
                patch.object(run_omp, "load_task", return_value=object()),
                self.assertRaises(ValueError) as raised,
            ):
                run_omp.run_cell(
                    "cfg",
                    "task-a",
                    model="openai-codex/model",
                    thinking="low",
                    rep=0,
                    agent_timeout=1,
                    keep=False,
                    pass_openai_codex_oauth=True,
                    rpc_quiescence=0,
                )

        message = str(raised.exception)
        self.assertIn("Config leaf ambiguous:", message)
        self.assertIn(str(direct_leaf), message)
        self.assertIn(str(worker_leaf), message)


class ProbeCommandTests(unittest.TestCase):
    def test_pi_library_call_requires_explicit_output_cell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configs" / "cfg" / "model" / "low").mkdir(
                parents=True
            )
            task = type("Task", (), {"agent_timeout_s": 30.0})()
            with (
                patch.object(run, "REPO", root),
                patch.object(run, "load_task", return_value=task),
                patch.object(run, "ensure_env_image") as ensure_image,
                self.assertRaisesRegex(
                    ValueError,
                    "Confirmed launch or draft probe output required",
                ),
            ):
                run.run_cell(
                    "cfg",
                    "task-a",
                    model="provider/model",
                    thinking="low",
                    rep=0,
                    agent_timeout=1,
                    keep=False,
                    pass_openai_codex_oauth=False,
                    rpc_quiescence=0,
                )

        ensure_image.assert_not_called()

    def test_omp_library_call_requires_explicit_output_cell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "configs" / "cfg" / "model" / "low").mkdir(
                parents=True
            )
            task = type("Task", (), {"agent_timeout_s": 30.0})()
            with (
                patch.object(run_omp, "REPO", root),
                patch.object(run_omp, "load_task", return_value=task),
                patch.object(run_omp, "ensure_env_image") as ensure_image,
                self.assertRaisesRegex(
                    ValueError,
                    "Confirmed launch or draft probe output required",
                ),
            ):
                run_omp.run_cell(
                    "cfg",
                    "task-a",
                    model="openai-codex/model",
                    thinking="low",
                    rep=0,
                    agent_timeout=1,
                    keep=False,
                    pass_openai_codex_oauth=True,
                    rpc_quiescence=0,
                )

        ensure_image.assert_not_called()

    def test_pi_direct_debugging_requires_scratch_probe_output(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            argv = [
                "run.py",
                "--config",
                "cfg",
                "--task",
                "task-a",
            ]
            with (
                patch.object(sys, "argv", argv),
                patch.object(run, "REPO", root),
                patch.object(run, "run_cell") as run_cell,
                self.assertRaisesRegex(SystemExit, "Draft probe required"),
            ):
                run.main()

        run_cell.assert_not_called()

    def test_pi_probe_writes_only_to_explicit_scratch_cell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            probe_output = root / "scratch" / "probe-cell"
            argv = [
                "run.py",
                "--config",
                "cfg",
                "--task",
                "task-a",
                "--probe-output",
                str(probe_output),
            ]
            task = type("Task", (), {"agent_timeout_s": 30.0})()
            with (
                patch.object(sys, "argv", argv),
                patch.object(run, "REPO", root),
                patch.object(run, "load_task", return_value=task),
                patch.object(
                    run,
                    "run_cell",
                    return_value={"reward_partial": 0.0, "total_tokens": 1},
                ) as run_cell,
            ):
                run.main()

        self.assertEqual(run_cell.call_args.kwargs["output_cell"], probe_output)
        self.assertFalse(run_cell.call_args.kwargs["persist_result_index"])

    def test_omp_probe_writes_only_to_explicit_scratch_cell(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            probe_output = root / "scratch" / "omp-probe-cell"
            argv = [
                "run_omp.py",
                "--config",
                "cfg",
                "--task",
                "task-a",
                "--probe-output",
                str(probe_output),
            ]
            task = type("Task", (), {"agent_timeout_s": 30.0})()
            with (
                patch.object(sys, "argv", argv),
                patch.object(run_omp, "REPO", root),
                patch.object(run_omp, "load_task", return_value=task),
                patch.object(
                    run_omp,
                    "run_cell",
                    return_value={"reward_partial": 0.0, "total_tokens": 1},
                ) as run_cell,
            ):
                run_omp.main()

        self.assertEqual(run_cell.call_args.kwargs["output_cell"], probe_output)
        self.assertFalse(run_cell.call_args.kwargs["persist_result_index"])


class RunPiCommandTests(unittest.TestCase):
    def test_pi_cmd_uses_rpc_without_print_mode_and_preserves_session_dir(self):
        cmd = run.pi_cmd(
            {"pi_flags": ["-e", "/arm/extensions/example.ts"], "skill_dirs": []},
            "openrouter/example/model",
            "low",
            "system text",
        )

        self.assertEqual(cmd[:3], ["pi", "--mode", "rpc"])
        self.assertNotIn("-p", cmd)
        self.assertNotIn("@/task/instruction.md", cmd)
        self.assertIn("--session-dir", cmd)
        self.assertEqual(cmd[cmd.index("--session-dir") + 1], "/out/session")
        self.assertIn("--append-system-prompt", cmd)
        self.assertIn("--no-skills", cmd)
        self.assertEqual(cmd[-4:], [
            "-e", "/arm/extensions/example.ts",
            "-e", run.INITIAL_CONTEXT_CAPTURE_CONTAINER,
        ])

    def test_pi_cmd_can_disable_initial_context_capture(self):
        cmd = run.pi_cmd(
            {"pi_flags": ["-e", "/arm/extensions/example.ts"], "skill_dirs": []},
            "openrouter/example/model",
            "low",
            "system text",
            capture_initial_context=False,
        )

        self.assertEqual(cmd[-2:], ["-e", "/arm/extensions/example.ts"])
        self.assertNotIn(run.INITIAL_CONTEXT_CAPTURE_CONTAINER, cmd)

    def test_pi_cmd_omits_append_system_prompt_for_clean_baseline(self):
        cmd = run.pi_cmd(
            {"pi_flags": [], "skill_dirs": []},
            "openrouter/example/model",
            "low",
            "",
            capture_initial_context=False,
        )

        self.assertNotIn("--append-system-prompt", cmd)


class RunOmpCommandTests(unittest.TestCase):
    def test_omp_cmd_loads_initial_context_capture_last_by_default(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "system text",
            "read,bash,edit,write",
            overlay="/arm/omp-overlay.yml",
        )

        self.assertNotIn("--no-extensions", cmd)
        self.assertEqual(cmd[-2:], ["-e", run.INITIAL_CONTEXT_CAPTURE_CONTAINER])

    def test_omp_cmd_loads_config_extensions_before_capture(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "",
            "read,bash,edit,write",
            capture_initial_context=True,
            extension_paths=["/arm/extensions/omp_strip_project_message.js"],
        )

        self.assertNotIn("--no-extensions", cmd)
        self.assertEqual(cmd[-4:], [
            "-e", "/arm/extensions/omp_strip_project_message.js",
            "-e", run.INITIAL_CONTEXT_CAPTURE_CONTAINER,
        ])

    def test_omp_cmd_keeps_extensions_when_capture_disabled(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "",
            "read,bash,edit,write",
            capture_initial_context=False,
            extension_paths=["/arm/extensions/omp_strip_project_message.js"],
        )

        self.assertNotIn("--no-extensions", cmd)
        self.assertIn("/arm/extensions/omp_strip_project_message.js", cmd)

    def test_omp_cmd_can_disable_initial_context_capture(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "system text",
            "read,bash,edit,write",
            capture_initial_context=False,
        )

        self.assertIn("--no-extensions", cmd)
        self.assertNotIn(run.INITIAL_CONTEXT_CAPTURE_CONTAINER, cmd)

    def test_omp_cmd_omits_append_system_prompt_for_clean_config(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "",
            "read,bash,edit,write",
            capture_initial_context=False,
        )

        self.assertNotIn("--append-system-prompt", cmd)

    def test_omp_cmd_can_set_system_prompt_override(self):
        cmd = run_omp.omp_cmd(
            "openai-codex/gpt-5.5",
            "low",
            "",
            "read,bash,edit,write",
            capture_initial_context=False,
            system_prompt="Pi-like prompt",
        )

        self.assertIn("--system-prompt", cmd)
        self.assertEqual(cmd[cmd.index("--system-prompt") + 1], "Pi-like prompt")

    def test_render_omp_system_prompt_replaces_only_supported_tokens(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = Path(td)
            (cdir / "omp-system-prompt.md").write_text("date={{current_date}} cwd={{cwd}} other={{x}}")

            rendered = run_omp.render_omp_system_prompt(cdir)

        self.assertIn("cwd=/app", rendered)
        self.assertNotIn("{{current_date}}", rendered)
        self.assertIn("other={{x}}", rendered)

    def test_resolve_omp_extensions_maps_relative_paths_to_arm(self):
        with tempfile.TemporaryDirectory() as td:
            cdir = Path(td)
            (cdir / "extensions").mkdir()
            (cdir / "extensions" / "strip.js").write_text("export default function noop() {}")
            (cdir / "omp-extensions.txt").write_text("# comment\nextensions/strip.js\n")

            resolved = run_omp.resolve_omp_extensions(cdir)

        self.assertEqual(resolved, ["/arm/extensions/strip.js"])


if __name__ == "__main__":
    unittest.main()

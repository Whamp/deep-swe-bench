import tempfile
import unittest
from pathlib import Path

import harness.run as run
import harness.run_omp as run_omp


class ConfigPromptLayerTests(unittest.TestCase):
    def test_clean_config_has_no_append_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            old_repo = run.REPO
            root = Path(td)
            (root / "configs" / "baseline").mkdir(parents=True)
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
            cdir.mkdir(parents=True)
            (cdir / "system_preamble.md").write_text("preamble\n")
            (cdir / "orchestration.md").write_text("orchestration\n")
            try:
                run.REPO = root
                cfg = run.load_config("baseline-preamble-orchestration", "openrouter/example/model", "low")
            finally:
                run.REPO = old_repo

        self.assertEqual(run.config_append_text(cfg), "preamble\n\norchestration")


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

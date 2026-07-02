import unittest

import harness.run as run


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
        self.assertEqual(cmd[-2:], ["-e", "/arm/extensions/example.ts"])


if __name__ == "__main__":
    unittest.main()

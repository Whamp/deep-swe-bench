import tempfile
import unittest
from pathlib import Path

import harness.run as run


class PatchCleanupTests(unittest.TestCase):
    def test_strip_patch_paths_removes_only_gocache_sections(self):
        with tempfile.TemporaryDirectory() as td:
            patch = Path(td) / "model.patch"
            patch.write_bytes(
                b"diff --git a/src/main.go b/src/main.go\n"
                b"index 1..2 100644\n"
                b"--- a/src/main.go\n"
                b"+++ b/src/main.go\n"
                b"@@ -1 +1 @@\n-old\n+new\n"
                b"diff --git a/.gocache/00/blob b/.gocache/00/blob\n"
                b"new file mode 100644\n"
                b"@@ -0,0 +1 @@\n+junk\n"
                b"diff --git a/tests/test.go b/tests/test.go\n"
                b"@@ -1 +1 @@\n-a\n+b\n"
            )

            removed = run.strip_patch_paths(patch)
            data = patch.read_bytes()

            self.assertGreater(removed, 0)
            self.assertIn(b"diff --git a/src/main.go", data)
            self.assertIn(b"diff --git a/tests/test.go", data)
            self.assertNotIn(b".gocache", data)


class VerifierStdoutCleanupTests(unittest.TestCase):
    def test_compact_verifier_stdout_replaces_duplicate_raw_log(self):
        with tempfile.TemporaryDirectory() as td:
            verifier = Path(td) / "verifier"
            verifier.mkdir()
            (verifier / "run.log").write_text("raw line\n")
            stdout = (
                "[verifier] model.patch applied\n"
                "===== raw suite output: run.log =====\n"
                "raw line\n"
                "more raw\n"
            )

            compacted = run.compact_verifier_stdout(stdout, verifier)

            self.assertIn("[verifier] model.patch applied", compacted)
            self.assertIn("===== raw suite output: run.log =====", compacted)
            self.assertIn("see verifier/run.log", compacted)
            self.assertNotIn("more raw", compacted)

    def test_compact_verifier_stdout_keeps_inline_log_when_file_missing(self):
        with tempfile.TemporaryDirectory() as td:
            stdout = "===== raw suite output: run.log =====\nraw line\n"

            compacted = run.compact_verifier_stdout(stdout, Path(td))

            self.assertEqual(compacted, stdout)


if __name__ == "__main__":
    unittest.main()

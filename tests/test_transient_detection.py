import json
import tempfile
from pathlib import Path

from hypothesis import given, strategies as st

from harness import quota
from harness.run import transient_model_error


def _write(path, text):
    path.write_text(text)
    return path


class TestTransientModelErrorScanner:
    def test_ignores_codebase_memory_reindex_counts_containing_429(self, tmp_path):
        log = _write(
            tmp_path / "pi.stderr.txt",
            "[cbm-pi] auto-reindex done: indexed, 1429 nodes\n"
            "[cbm-pi] auto-reindex done: indexed, 429 nodes\n",
        )

        assert transient_model_error([log]) is None

    def test_detects_codex_usage_limit_from_assistant_error_record(self, tmp_path):
        session = tmp_path / "session.jsonl"
        session.write_text(
            json.dumps(
                {
                    "type": "message",
                    "message": {
                        "role": "assistant",
                        "stopReason": "error",
                        "errorMessage": "Codex error: The usage limit has been reached",
                    },
                }
            )
            + "\n"
        )

        assert transient_model_error([session]) == "Codex error: The usage limit has been reached"

    def test_detects_provider_429_from_stderr_with_error_context(self, tmp_path):
        log = _write(tmp_path / "pi.stderr.txt", "OpenAI provider error 429: slow down\n")

        assert transient_model_error([log]) == "OpenAI provider error 429: slow down"

    def test_ignores_task_output_that_mentions_rate_limits_without_model_context(self, tmp_path):
        log = _write(
            tmp_path / "pi.stderr.txt",
            "github api rate limit exceeded while testing fixture\n"
            "github api error 429 while exercising task fixture\n"
            "model graph indexing failed: error 429 in local fixture\n"
            "docs mention the usage limit policy for this repository\n"
            "try again at examples appear in user-facing docs\n",
        )

        assert transient_model_error([log]) is None

    def test_ignores_structured_non_model_errors_that_mention_limits(self, tmp_path):
        session = tmp_path / "session.jsonl"
        session.write_text(
            json.dumps({"type": "custom", "data": {"error": "github api error 429 while testing fixture"}})
            + "\n"
        )

        assert transient_model_error([session]) is None

    def test_ignores_structured_non_error_messages_that_mention_limits(self, tmp_path):
        session = tmp_path / "session.jsonl"
        session.write_text(
            json.dumps(
                {
                    "type": "custom",
                    "message": "docs mention usage limit and rate limit exceeded examples",
                }
            )
            + "\n"
        )

        assert transient_model_error([session]) is None

    @given(st.integers(min_value=0, max_value=999_999), st.sampled_from(["indexed", "fetched", "symbols", "nodes"]))
    def test_plain_progress_counts_are_not_transient_errors(self, number, noun):
        with tempfile.TemporaryDirectory() as td:
            log = _write(Path(td) / "pi.stderr.txt", f"[cbm-pi] auto-reindex done: {noun}, {number} nodes\n")

            assert transient_model_error([log]) is None


class TestQuotaTransientClassification:
    @given(st.integers(min_value=0, max_value=999_999).filter(lambda n: n != 429))
    def test_numeric_progress_is_not_rate_limit(self, number):
        assert quota.classify_transient(f"indexed, {number} nodes") == "unknown"

    def test_bounded_429_still_classifies_rate_limit(self):
        assert quota.classify_transient("Error 429: slow down") == "rate_limit"
        assert quota.classify_transient("HTTP status 429 from provider") == "rate_limit"

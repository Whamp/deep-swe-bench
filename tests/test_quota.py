"""Tests for harness.quota — provider quota parsing, classification, and reset math.

These cover the pure parsing/classification/reset logic with no network calls.
The fetcher is injected so codex_windows() can be tested with a fake.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from harness import quota
from harness.quota import Window


NOW = datetime(2026, 7, 3, 17, 0, tzinfo=timezone.utc)


def _ts(seconds_from_now: int) -> int:
    """Unix timestamp `seconds_from_now` from NOW."""
    return int((NOW + timedelta(seconds=seconds_from_now)).timestamp())


# --- provider usage parsing ---------------------------------------------- #


class TestParseZaiUsage:
    def test_personal_coding_plan_token_windows(self):
        data = {
            "code": 200,
            "success": True,
            "data": {
                "limits": [
                    {
                        "type": "TOKENS_LIMIT",
                        "unit": 3,
                        "number": 5,
                        "percentage": 4,
                        "nextResetTime": 1786040812384,
                    },
                    {
                        "type": "TOKENS_LIMIT",
                        "unit": 6,
                        "number": 1,
                        "percentage": 40,
                        "nextResetTime": 1786142541997,
                    },
                    {
                        "type": "TIME_LIMIT",
                        "unit": 5,
                        "number": 1,
                        "percentage": 0,
                        "nextResetTime": 1788216141995,
                    },
                ]
            },
        }

        windows = quota.parse_zai_usage(data)

        assert [(window.label, window.used_percent) for window in windows] == [
            ("5h", 4),
            ("Week", 40),
        ]
        assert windows[0].reset_at == datetime(
            2026, 8, 6, 18, 26, 52, 384000, tzinfo=timezone.utc
        )

    def test_zai_windows_uses_environment_api_key(self, monkeypatch):
        monkeypatch.setenv("ZAI_API_KEY", "fixture-key")
        calls = []

        def fetcher(api_key):
            calls.append(api_key)
            return {
                "data": {
                    "limits": [
                        {
                            "type": "TOKENS_LIMIT",
                            "unit": 3,
                            "number": 5,
                            "percentage": 12,
                        }
                    ]
                }
            }

        windows, source = quota.zai_windows(fetcher=fetcher)

        assert source == "zai-api"
        assert calls == ["fixture-key"]
        assert [(window.label, window.used_percent) for window in windows] == [
            ("5h", 12)
        ]


class TestParseCodexUsage:
    def test_main_plan_primary_and_secondary(self):
        data = {
            "rate_limit": {
                "primary_window": {"reset_at": _ts(3000), "limit_window_seconds": 18000, "used_percent": 100},
                "secondary_window": {"reset_at": _ts(600000), "limit_window_seconds": 604800, "used_percent": 58},
            }
        }
        windows = quota.parse_codex_usage(data)
        labels = [w.label for w in windows]
        assert "5h" in labels
        assert "Week" in labels
        five_h = next(w for w in windows if w.label == "5h")
        assert five_h.used_percent == 100
        assert five_h.reset_at is not None
        assert five_h.reset_at.year == 2026

    def test_spark_additional_rate_limits_get_prefixed(self):
        data = {
            "rate_limit": {
                "primary_window": {"reset_at": _ts(3000), "limit_window_seconds": 18000, "used_percent": 0},
            },
            "additional_rate_limits": [
                {
                    "limit_name": "GPT-5.3-Codex-Spark",
                    "rate_limit": {
                        "primary_window": {"reset_at": _ts(7200), "limit_window_seconds": 18000, "used_percent": 100},
                    },
                }
            ],
        }
        windows = quota.parse_codex_usage(data)
        spark = [w for w in windows if w.is_spark]
        assert len(spark) == 1
        assert "GPT-5.3-Codex-Spark" in spark[0].label
        assert spark[0].used_percent == 100
        non_spark = [w for w in windows if not w.is_spark]
        assert len(non_spark) == 1

    def test_missing_windows_are_skipped(self):
        windows = quota.parse_codex_usage({"rate_limit": {"primary_window": None}})
        assert windows == []

    def test_metered_feature_fallback_prefix(self):
        data = {
            "additional_rate_limits": [
                {"metered_feature": "Experimental Pool", "rate_limit": {"primary_window": {"used_percent": 10, "limit_window_seconds": 3600}}}
            ]
        }
        windows = quota.parse_codex_usage(data)
        assert any("Experimental Pool" in w.label for w in windows)

    def test_fallback_label_when_limit_window_seconds_missing(self):
        data = {"rate_limit": {"primary_window": {"used_percent": 50}}}
        windows = quota.parse_codex_usage(data)
        assert len(windows) == 1
        # fallback is 18000s = 5h
        assert windows[0].label == "5h"


# --- relevant_windows / model routing ------------------------------------ #


class TestRelevantWindows:
    def test_spark_model_gets_only_spark_windows(self):
        windows = [
            Window("5h", 100, NOW + timedelta(hours=1)),
            Window("Week", 58, NOW + timedelta(days=5)),
            Window("GPT-5.3-Codex-Spark 5h", 0, NOW + timedelta(hours=3)),
        ]
        rel = quota.relevant_windows(windows, "openai-codex/gpt-5.3-codex-spark")
        assert len(rel) == 1
        assert rel[0].is_spark

    def test_non_spark_model_excludes_spark_windows(self):
        windows = [
            Window("5h", 100, NOW + timedelta(hours=1)),
            Window("GPT-5.3-Codex-Spark 5h", 0, NOW + timedelta(hours=3)),
        ]
        rel = quota.relevant_windows(windows, "openai-codex/gpt-5.5")
        assert len(rel) == 1
        assert not rel[0].is_spark


# --- exhaustion + reset math --------------------------------------------- #


class TestExhaustionAndReset:
    def test_exhausted_at_threshold(self):
        windows = [Window("5h", 95, NOW), Window("Week", 94, NOW), Window("Spark 5h", 100, NOW)]
        ex = quota.exhausted_windows(windows)
        labels = [w.label for w in ex]
        assert "5h" in labels
        assert "Spark 5h" in labels
        assert "Week" not in labels

    def test_next_reset_is_latest_among_exhausted(self):
        windows = [
            Window("5h", 100, NOW + timedelta(minutes=30)),
            Window("Week", 100, NOW + timedelta(days=5)),
            Window("Spark 5h", 0, NOW + timedelta(minutes=10)),
        ]
        reset = quota.next_reset(windows)
        assert reset == NOW + timedelta(days=5)

    def test_next_reset_none_when_nothing_exhausted(self):
        windows = [Window("5h", 40, NOW + timedelta(minutes=30))]
        assert quota.next_reset(windows) is None

    def test_next_reset_skips_exhausted_without_reset_at(self):
        windows = [
            Window("5h", 100, None),
            Window("Week", 100, NOW + timedelta(days=5)),
        ]
        reset = quota.next_reset(windows)
        assert reset == NOW + timedelta(days=5)

    def test_next_reset_none_when_all_exhausted_lack_reset_at(self):
        windows = [Window("5h", 100, None)]
        assert quota.next_reset(windows) is None


class TestWaitSeconds:
    def test_basic(self):
        reset = NOW + timedelta(minutes=30)
        assert quota.wait_seconds(reset, now=NOW, buffer_s=60) == 30 * 60 + 60

    def test_past_reset_returns_zero(self):
        reset = NOW - timedelta(minutes=5)
        assert quota.wait_seconds(reset, now=NOW) == 0

    def test_none_reset_returns_none(self):
        assert quota.wait_seconds(None, now=NOW) is None


# --- transient classification -------------------------------------------- #


class TestClassifyTransient:
    @pytest.mark.parametrize(
        "msg",
        [
            "Codex error: The usage limit has been reached",
            "usage limit",
            "Weekly limit reached",
            "plan_limit exceeded",
        ],
    )
    def test_quota(self, msg):
        assert quota.classify_transient(msg) == "quota"

    @pytest.mark.parametrize(
        "msg",
        [
            "rate limit exceeded",
            "Too Many Requests",
            "Error 429: slow down",
            "temporarily rate limited",
        ],
    )
    def test_rate_limit(self, msg):
        assert quota.classify_transient(msg) == "rate_limit"

    def test_unknown(self):
        assert quota.classify_transient("some other transient error") == "unknown"

    def test_none(self):
        assert quota.classify_transient(None) == "unknown"

    def test_empty(self):
        assert quota.classify_transient("") == "unknown"


# --- credentials --------------------------------------------------------- #


class TestLoadCredentials:
    def test_reads_openai_codex_entry(self, tmp_path):
        auth = tmp_path / "auth.json"
        auth.write_text(
            '{"openai-codex": {"access": "tok123", "accountId": "acc9"}}'
        )
        creds = quota.load_codex_credentials(auth)
        assert creds == {"access_token": "tok123", "account_id": "acc9"}

    def test_missing_file_returns_none(self, tmp_path):
        assert quota.load_codex_credentials(tmp_path / "nope.json") is None

    def test_no_openai_codex_key_returns_none(self, tmp_path):
        auth = tmp_path / "auth.json"
        auth.write_text('{"other": {}}')
        assert quota.load_codex_credentials(auth) is None

    def test_invalid_json_returns_none(self, tmp_path):
        auth = tmp_path / "auth.json"
        auth.write_text("not json")
        assert quota.load_codex_credentials(auth) is None


# --- sub-core cache fallback -------------------------------------------- #


class TestSubcoreCache:
    def test_parses_cache_windows(self, tmp_path):
        cache = tmp_path / "cache.json"
        cache.write_text(
            json_text(
                {
                    "codex": {
                        "usage": {
                            "windows": [
                                {"label": "5h", "usedPercent": 100, "resetAt": "2026-07-03T17:55:22.000Z"},
                                {"label": "Week", "usedPercent": 58, "resetAt": "2026-07-09T03:20:27.000Z"},
                            ]
                        }
                    }
                }
            )
        )
        windows = quota.read_subcore_cache(cache)
        assert windows is not None
        assert len(windows) == 2
        assert windows[0].used_percent == 100
        assert windows[0].reset_at == datetime(2026, 7, 3, 17, 55, 22, tzinfo=timezone.utc)

    def test_missing_file_returns_none(self, tmp_path):
        assert quota.read_subcore_cache(tmp_path / "nope.json") is None

    def test_bad_reset_at_string_yields_none_reset(self, tmp_path):
        cache = tmp_path / "cache.json"
        cache.write_text(
            json_text({"codex": {"usage": {"windows": [{"label": "5h", "usedPercent": 100, "resetAt": "garbage"}]}}})
        )
        windows = quota.read_subcore_cache(cache)
        assert windows is not None
        assert windows[0].reset_at is None
        assert windows[0].used_percent == 100


# --- codex_windows end-to-end (injected fetcher) ------------------------- #


class TestCodexWindows:
    def test_api_success_filters_by_model(self, tmp_path):
        auth = tmp_path / "auth.json"
        auth.write_text('{"openai-codex": {"access": "tok"}}')
        cache = tmp_path / "cache.json"  # absent

        def fake_fetch(token, account_id=None, **kw):
            assert token == "tok"
            return {
                "rate_limit": {
                    "primary_window": {"reset_at": _ts(3000), "limit_window_seconds": 18000, "used_percent": 100},
                },
                "additional_rate_limits": [
                    {"limit_name": "GPT-5.3-Codex-Spark", "rate_limit": {"primary_window": {"used_percent": 0, "reset_at": _ts(9999)}}}
                ],
            }

        windows, source = quota.codex_windows(
            "openai-codex/gpt-5.5", auth_path=auth, cache_path=cache, fetcher=fake_fetch
        )
        assert source == "api"
        assert len(windows) == 1
        assert not windows[0].is_spark

    def test_api_failure_falls_back_to_cache(self, tmp_path):
        auth = tmp_path / "auth.json"
        auth.write_text('{"openai-codex": {"access": "tok"}}')
        cache = tmp_path / "cache.json"
        cache.write_text(
            json_text(
                {"codex": {"usage": {"windows": [{"label": "5h", "usedPercent": 100, "resetAt": "2026-07-03T17:55:22.000Z"}]}}}
            )
        )

        def boom(token, account_id=None, **kw):
            raise OSError("network down")

        windows, source = quota.codex_windows(
            "openai-codex/gpt-5.5", auth_path=auth, cache_path=cache, fetcher=boom
        )
        assert source == "cache"
        assert len(windows) == 1

    def test_no_credentials_no_cache_returns_none(self, tmp_path):
        windows, source = quota.codex_windows(
            "openai-codex/gpt-5.5",
            auth_path=tmp_path / "noauth.json",
            cache_path=tmp_path / "nocache.json",
            fetcher=lambda *a, **k: {},
        )
        assert source == "none"
        assert windows == []


# --- describe_pause ------------------------------------------------------ #


class TestDescribePause:
    def test_lists_exhausted_windows_with_eta(self):
        windows = [
            Window("5h", 100, NOW + timedelta(minutes=47)),
            Window("Week", 58, NOW + timedelta(days=5)),
        ]
        desc = quota.describe_pause(windows, now=NOW)
        assert "5h @ 100%" in desc
        assert "resets in 47m" in desc
        assert "Week" not in desc  # not exhausted

    def test_hours_formatting(self):
        windows = [Window("Week", 100, NOW + timedelta(hours=5, minutes=30))]
        desc = quota.describe_pause(windows, now=NOW)
        assert "resets in 5h30m" in desc

    def test_no_reset_at(self):
        windows = [Window("5h", 100, None)]
        desc = quota.describe_pause(windows, now=NOW)
        assert "5h @ 100%" in desc
        assert "resets" not in desc


def json_text(obj) -> str:
    import json

    return json.dumps(obj)

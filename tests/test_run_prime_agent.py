from pathlib import Path

import pytest

from harness import run_prime_agent


def test_prime_agent_cmd_pins_direct_zai_glm52_max_and_stock_rlm() -> None:
    command = run_prime_agent.prime_agent_cmd(
        model="zai/glm-5.2",
        thinking="max",
        capture_initial_context=False,
    )

    assert command == [
        "prime-agent",
        "--mode",
        "rpc",
        "--cwd",
        "/app",
        "--provider",
        "zai",
        "--model",
        "glm-5.2",
        "--thinking",
        "max",
        "--session-dir",
        "/out/session",
        "--no-extensions",
    ]
    assert "--autonomous" not in command
    assert "--goal" not in command
    assert "--no-skills" not in command


def test_prime_agent_proxy_models_redirects_only_zai_to_local_guard() -> None:
    assert run_prime_agent.prime_agent_proxy_models() == {
        "providers": {
            "zai": {
                "baseUrl": "http://127.0.0.1:8765",
            }
        }
    }
    assert run_prime_agent.ZAI_MAX_CONCURRENCY == 8
    assert run_prime_agent.ZAI_MAX_REQUESTS_PER_CELL == 64


def test_prime_agent_cmd_rejects_non_zai_glm52_model() -> None:
    with pytest.raises(SystemExit, match="requires exact model zai/glm-5.2"):
        run_prime_agent.prime_agent_cmd(
            model="openrouter/z-ai/glm-5.2",
            thinking="max",
            capture_initial_context=False,
        )


def test_prime_agent_cmd_rejects_non_max_thinking() -> None:
    with pytest.raises(SystemExit, match="requires max thinking"):
        run_prime_agent.prime_agent_cmd(
            model="zai/glm-5.2",
            thinking="high",
            capture_initial_context=False,
        )


def test_prime_agent_settings_require_stock_depth_one(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        '{"defaultProvider":"zai","defaultModel":"glm-5.2",'
        '"defaultThinkingLevel":"max","rlmMaxDepth":1}\n'
    )

    assert run_prime_agent.validate_prime_agent_settings(settings) == {
        "defaultProvider": "zai",
        "defaultModel": "glm-5.2",
        "defaultThinkingLevel": "max",
        "rlmMaxDepth": 1,
    }


def test_prime_agent_settings_reject_behavior_overrides(tmp_path: Path) -> None:
    settings = tmp_path / "settings.json"
    settings.write_text(
        '{"defaultProvider":"zai","defaultModel":"glm-5.2",'
        '"defaultThinkingLevel":"max","rlmMaxDepth":1,'
        '"autoRefine":{"enabled":false}}\n'
    )

    with pytest.raises(SystemExit, match="unsupported settings keys"):
        run_prime_agent.validate_prime_agent_settings(settings)

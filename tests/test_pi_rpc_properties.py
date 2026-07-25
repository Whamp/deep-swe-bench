import json
import string
import sys
import tempfile
import textwrap
from collections import Counter
from pathlib import Path

import pytest
from hypothesis import given, settings, strategies as st

import harness.run as run
from harness import pi_config
from harness.pi_rpc_runner import (
    _advisor_usage_line,
    _auto_ui_response,
    _is_advisor_usage_event,
    _is_idle,
    _json_line,
    run_pi_rpc,
)


json_scalar = st.one_of(
    st.none(),
    st.booleans(),
    st.integers(min_value=-(2**53), max_value=2**53),
    st.floats(allow_nan=False, allow_infinity=False, width=32),
    st.text(max_size=80),
)
json_value = st.recursive(
    json_scalar,
    lambda children: st.one_of(
        st.lists(children, max_size=5),
        st.dictionaries(st.text(max_size=20), children, max_size=5),
    ),
    max_leaves=25,
)
json_object = st.dictionaries(st.text(max_size=20), json_value, max_size=8)


def parsed_json_line(line: str):
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


@settings(max_examples=80, deadline=None)
@given(json_object)
def test_json_line_roundtrips_json_objects(obj):
    line = _json_line(obj)

    assert line.endswith("\n")
    assert line.count("\n") == 1
    assert json.loads(line) == obj


@settings(max_examples=120, deadline=None)
@given(
    extra=json_object,
    req_id=st.one_of(json_value, st.text(min_size=1, max_size=20)),
    method=st.one_of(json_value, st.sampled_from(["confirm", "select", "input", "editor", "custom"])),
)
def test_auto_ui_response_has_safe_serializable_noninteractive_shape(extra, req_id, method):
    request = {**extra, "id": req_id, "method": method}
    response = _auto_ui_response(request)

    if not req_id or not isinstance(method, str):
        assert response is None
    elif method == "confirm":
        assert response == {"type": "extension_ui_response", "id": req_id, "confirmed": False}
    elif method in {"select", "input", "editor", "custom"}:
        assert response == {"type": "extension_ui_response", "id": req_id, "cancelled": True}
    else:
        assert response is None

    if response is not None:
        assert json.loads(_json_line(response)) == response
        assert response["type"] == "extension_ui_response"
        assert response["id"] == req_id
        assert response.get("confirmed") is not True


@settings(max_examples=160, deadline=None)
@given(state=json_value)
def test_is_idle_is_conservative_and_never_crashes_for_arbitrary_rpc_state(state):
    result = _is_idle(state)

    expected = (
        isinstance(state, dict)
        and state.get("isStreaming") is False
        and type(state.get("pendingMessageCount")) is int
        and state.get("pendingMessageCount") == 0
    )
    assert result is expected


@settings(max_examples=120, deadline=None)
@given(extra=json_object, event_type=json_value, tool_name=json_value)
def test_advisor_usage_filter_is_exact(extra, event_type, tool_name):
    event = {**extra, "type": event_type, "toolName": tool_name}

    assert _is_advisor_usage_event(event) is (event_type == "tool_execution_end" and tool_name == "advisor")


invalid_line = st.text(string.ascii_letters + string.digits + "-_:", max_size=40).map(lambda s: f"not-json:{s}\n")


@settings(max_examples=100, deadline=None)
@given(lines=st.lists(st.one_of(json_object.map(_json_line), invalid_line), max_size=20))
def test_advisor_usage_lines_preserve_only_raw_advisor_events_in_order(lines):
    actual = []
    expected = []
    for line in lines:
        parsed = parsed_json_line(line)
        if isinstance(parsed, dict):
            sidecar_line = _advisor_usage_line(parsed, line)
            if sidecar_line is not None:
                actual.append(sidecar_line)
            if parsed.get("type") == "tool_execution_end" and parsed.get("toolName") == "advisor":
                expected.append(line.rstrip("\n") + "\n")

    assert actual == expected


safe_token_alphabet = string.ascii_letters + string.digits + "-_./:=+"
plain_flag = st.text(safe_token_alphabet, min_size=1, max_size=30).filter(
    lambda token: (
        token not in pi_config._RPC_OWNED_PI_FLAGS
        and not token.startswith(pi_config._RPC_OWNED_PI_FLAG_PREFIXES)
        and token not in {"--no-skills", "--skill", "--no-extensions"}
    )
)
owned_flag = st.one_of(
    st.sampled_from(sorted(pi_config._RPC_OWNED_PI_FLAGS)),
    st.sampled_from(
        [
            "--mode=json",
            "--mode=rpc",
            "--model=x",
            "--thinking=low",
            "--session-dir=/tmp/x",
            "--append-system-prompt=x",
        ]
    ),
)
flag_token = st.one_of(plain_flag, owned_flag)
skill_name = st.from_regex(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,24}", fullmatch=True).filter(
    lambda name: name not in {".", ".."}
)
model_id = st.from_regex(r"[a-z0-9_.-]+/[A-Za-z0-9_.:/-]+", fullmatch=True)
thinking_level = st.sampled_from(["off", "low", "medium", "high", "xhigh"])


def is_rpc_owned_flag(flag: str) -> bool:
    return flag in pi_config._RPC_OWNED_PI_FLAGS or flag.startswith(
        pi_config._RPC_OWNED_PI_FLAG_PREFIXES
    )


@settings(max_examples=120, deadline=None)
@given(
    model=model_id,
    thinking=thinking_level,
    append_text=st.text(max_size=200),
    flags=st.lists(flag_token, max_size=8),
    skills=st.lists(skill_name, unique=True, max_size=5),
)
def test_pi_cmd_preserves_rpc_invariants_or_rejects_control_overrides(model, thinking, append_text, flags, skills):
    arm_cfg = {"pi_flags": flags, "skill_dirs": [Path(name) for name in skills]}

    if any(is_rpc_owned_flag(flag) for flag in flags):
        with pytest.raises(ValueError, match="RPC runner control flag"):
            run.pi_cmd(arm_cfg, model, thinking, append_text)
        return

    cmd = run.pi_cmd(arm_cfg, model, thinking, append_text)

    assert cmd[:3] == ["pi", "--mode", "rpc"]
    assert "-p" not in cmd
    assert "@/task/instruction.md" not in cmd
    assert cmd[cmd.index("--model") + 1] == model
    assert cmd[cmd.index("--thinking") + 1] == thinking
    assert cmd[cmd.index("--session-dir") + 1] == "/out/session"
    if append_text:
        assert cmd[cmd.index("--append-system-prompt") + 1] == append_text
    else:
        assert "--append-system-prompt" not in cmd
    assert "--no-extensions" in cmd

    if skills:
        assert "--no-skills" not in cmd
        skill_pairs = [cmd[i:i + 2] for i in range(len(cmd) - 1)]
        for name in skills:
            assert ["--skill", f"/arm/skills/{name}"] in skill_pairs
    else:
        assert "--no-skills" in cmd

    capture_tail = run.initial_context_capture_flags(True)
    assert cmd[-len(capture_tail):] == capture_tail
    command_before_capture = cmd[:-len(capture_tail)]

    if flags:
        assert command_before_capture[-len(flags):] == flags
    else:
        assert command_before_capture[-1] == "--no-extensions"


truthy_json_id = json_value.filter(bool)
ui_event = st.builds(
    lambda extra, req_id, method: {**extra, "type": "extension_ui_request", "id": req_id, "method": method},
    extra=json_object,
    req_id=truthy_json_id,
    method=st.one_of(json_value, st.sampled_from(["confirm", "select", "input", "editor", "custom", "notify", "status"])),
)
advisor_event = st.builds(
    lambda extra: {**extra, "type": "tool_execution_end", "toolName": "advisor"},
    extra=json_object,
)
non_advisor_tool_event = st.builds(
    lambda extra, tool_name: {**extra, "type": "tool_execution_end", "toolName": tool_name},
    extra=json_object,
    tool_name=json_value.filter(lambda value: value != "advisor"),
)
rpc_stdout_line = st.one_of(
    st.one_of(ui_event, advisor_event, non_advisor_tool_event, json_object).map(_json_line),
    st.text(string.ascii_letters + string.digits + "-_:", max_size=40).map(lambda s: f"invalid-rpc-json:{s}\n"),
)


@settings(max_examples=25, deadline=None)
@given(stdout_lines=st.lists(rpc_stdout_line, max_size=10), prompt_text=st.text(max_size=120))
def test_run_pi_rpc_preserves_protocol_stream_properties(stdout_lines, prompt_text):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        event_file = root / "events.jsonl"
        received = root / "received.jsonl"
        event_file.write_text("".join(stdout_lines))
        fake = root / "fake_pi_rpc.py"
        fake.write_text(textwrap.dedent(f"""
            import json, sys, time

            event_file = {str(event_file)!r}
            received = {str(received)!r}

            def emit(obj):
                print(json.dumps(obj, separators=(",", ":")), flush=True)

            def record(obj):
                with open(received, "a") as f:
                    f.write(json.dumps(obj, separators=(",", ":")) + "\\n")

            for raw in sys.stdin:
                cmd = json.loads(raw)
                record(cmd)
                if cmd.get("type") == "prompt":
                    emit({{"id": cmd.get("id"), "type": "response", "command": "prompt", "success": True}})
                    with open(event_file) as f:
                        for line in f:
                            sys.stdout.write(line)
                            if not line.endswith("\\n"):
                                sys.stdout.write("\\n")
                            sys.stdout.flush()
                            time.sleep(0.001)
                elif cmd.get("type") == "get_state":
                    emit({{"id": cmd.get("id"), "type": "response", "command": "get_state", "success": True, "data": {{"isStreaming": False, "pendingMessageCount": 0}}}})
                elif cmd.get("type") == "extension_ui_response":
                    pass
        """))

        result = run_pi_rpc(
            [sys.executable, str(fake)],
            prompt_text=prompt_text,
            stderr_path=root / "pi.stderr.txt",
            runner_log_path=root / "pi-rpc-runner.jsonl",
            advisor_usage_path=root / "tool-usage.jsonl",
            timeout_s=3,
            quiescence_s=0.05,
            state_poll_s=0.02,
            shutdown_timeout_s=1,
        )

        assert result.exit_code == 0
        assert result.quiescent
        assert result.prompt_accepted

        parsed_events = [parsed_json_line(line) for line in stdout_lines]
        expected_advisor_lines = [
            line.rstrip("\n") + "\n"
            for line, event in zip(stdout_lines, parsed_events)
            if isinstance(event, dict) and _is_advisor_usage_event(event)
        ]
        assert (root / "tool-usage.jsonl").read_text() == "".join(expected_advisor_lines)

        invalid_count = sum(1 for event in parsed_events if event is None)
        assert result.event_counts.get("invalid_json", 0) == invalid_count

        received_commands = [json.loads(line) for line in received.read_text().splitlines()]
        prompts = [cmd for cmd in received_commands if cmd.get("type") == "prompt"]
        assert len(prompts) == 1
        assert prompts[0]["message"] == prompt_text
        assert any(cmd.get("type") == "get_state" for cmd in received_commands)

        expected_ui_responses = Counter(
            _json_line(response)
            for event in parsed_events
            if isinstance(event, dict)
            for response in [_auto_ui_response(event)]
            if response is not None
        )
        actual_ui_responses = Counter(
            _json_line(cmd)
            for cmd in received_commands
            if cmd.get("type") == "extension_ui_response"
        )
        for response_line, expected_count in expected_ui_responses.items():
            assert actual_ui_responses[response_line] >= expected_count

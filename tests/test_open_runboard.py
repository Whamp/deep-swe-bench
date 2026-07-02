import json
from pathlib import Path
from subprocess import CompletedProcess

import pytest

import scripts.open_runboard as open_runboard


def test_tail_targets_parse_common_tail_forms():
    assert open_runboard.tail_targets(["tail", "-n", "60", "-f", "runs/x/track.out"]) == ["runs/x/track.out"]
    assert open_runboard.tail_targets(["tail", "--lines=30", "--follow", "/tmp/track.out"]) == ["/tmp/track.out"]
    assert open_runboard.tail_targets(["tail", "-n60", "-F", "a", "b"]) == ["a", "b"]
    assert open_runboard.tail_targets(["python", "tail", "runs/x/track.out"]) == []


def test_process_tails_track_matches_relative_path_against_process_cwd(tmp_path):
    repo = tmp_path / "repo"
    track = repo / "runs" / "run-a" / "track.out"
    track.parent.mkdir(parents=True)
    track.write_text("running 1 cells:\n")
    process_info = {
        "foreground_processes": [
            {
                "argv": ["tail", "-n", "60", "-f", "runs/run-a/track.out"],
                "cwd": str(repo),
            }
        ]
    }

    assert open_runboard.process_tails_track(process_info, track)


def test_process_tails_track_rejects_scrollback_echo_without_tail(tmp_path):
    track = tmp_path / "runs" / "run-a" / "track.out"
    track.parent.mkdir(parents=True)
    track.write_text("running 1 cells:\n")
    process_info = {
        "foreground_processes": [
            {
                "argv": ["pi"],
                "cmdline": f"echo tail -f {track}",
                "cwd": str(tmp_path),
            }
        ]
    }

    assert not open_runboard.process_tails_track(process_info, track)


@pytest.mark.parametrize(
    "text",
    [
        "running 36 cells: pi-codex-goal\n",
        "[17/36] mobly-grouped-test-barriers / pi-codex-goal / rep0  ok\n",
        "[3/?] task / config / rep2  timeout\n",
        "[4/12] task / config / rep1  exit=75\n",
    ],
)
def test_visible_has_runboard_accepts_native_runboard_lines(text):
    assert open_runboard.visible_has_runboard(text)


@pytest.mark.parametrize(
    "text",
    [
        "tail -n 60 -f runs/run/track.out\n",
        "some old scrollback mentioning [1/36] but not enough\n",
        "[1/36] missing pieces ok\n",
    ],
)
def test_visible_has_runboard_rejects_non_progress_text(text):
    assert not open_runboard.visible_has_runboard(text)


def test_current_workspace_uses_focused_pane():
    def fake_run(cmd):
        assert cmd == ["herdr", "pane", "list"]
        return CompletedProcess(cmd, 0, json.dumps({
            "result": {
                "panes": [
                    {"pane_id": "w1:p1", "workspace_id": "w1", "focused": False},
                    {"pane_id": "w2:p1", "workspace_id": "w2", "focused": True},
                ]
            }
        }), "")

    assert open_runboard.current_workspace(fake_run) == "w2"


def test_find_existing_runboard_only_reads_verified_tail_pane(tmp_path):
    track = tmp_path / "runs" / "run-a" / "track.out"
    track.parent.mkdir(parents=True)
    track.write_text("running 1 cells:\n")
    calls = []

    def fake_run(cmd):
        calls.append(cmd)
        if cmd[:4] == ["herdr", "pane", "list", "--workspace"]:
            return CompletedProcess(cmd, 0, json.dumps({"result": {"panes": [{"pane_id": "p1"}, {"pane_id": "p2"}]}}), "")
        if cmd[:3] == ["herdr", "pane", "process-info"] and cmd[-1] == "p1":
            return CompletedProcess(cmd, 0, json.dumps({"result": {"process_info": {"foreground_processes": [{"argv": ["pi"], "cwd": str(tmp_path)}]}}}), "")
        if cmd[:3] == ["herdr", "pane", "process-info"] and cmd[-1] == "p2":
            return CompletedProcess(cmd, 0, json.dumps({"result": {"process_info": {"foreground_processes": [{"argv": ["tail", "-n", "60", "-f", str(track)], "cwd": str(tmp_path)}]}}}), "")
        if cmd[:3] == ["herdr", "pane", "read"]:
            assert cmd[3] == "p2"
            return CompletedProcess(cmd, 0, "running 1 cells: cfg\n", "")
        raise AssertionError(cmd)

    assert open_runboard.find_existing_runboard("w1", track, lines=30, run=fake_run)[0] == "p2"
    read_calls = [cmd for cmd in calls if cmd[:3] == ["herdr", "pane", "read"]]
    assert len(read_calls) == 1

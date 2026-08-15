from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path


def test_latest_provider_request_overwrites_without_expanding_numbered_capture(
    tmp_path: Path,
) -> None:
    source = Path(__file__).parents[1] / "harness" / "initial_context_capture.js"
    extension = tmp_path / "initial_context_capture.mjs"
    extension.write_text(source.read_text())
    driver = tmp_path / "exercise_capture.mjs"
    driver.write_text(
        """
        import register from "./initial_context_capture.mjs";

        const handlers = new Map();
        register({ on(name, handler) { handlers.set(name, handler); } });
        const context = { cwd: process.cwd() };
        for (let request = 1; request <= 3; request += 1) {
          handlers.get("before_provider_request")(
            { payload: { model: "diagnostic-model", request } },
            context,
          );
        }
        """
    )
    capture_dir = tmp_path / "capture"
    env = {
        **os.environ,
        "PI_INITIAL_CONTEXT_CAPTURE_LATEST_PROVIDER_REQUEST": "1",
        "PI_INITIAL_CONTEXT_DIR": str(capture_dir),
        "PI_INITIAL_CONTEXT_MAX_PROVIDER_REQUESTS": "1",
    }

    subprocess.run(
        ["node", str(driver)],
        check=True,
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
    )

    numbered = json.loads((capture_dir / "provider_request_0001.json").read_text())
    latest = json.loads((capture_dir / "provider_request_latest.json").read_text())
    metadata = json.loads(
        (capture_dir / "provider_request_latest_meta.json").read_text()
    )
    assert numbered["request"] == 1
    assert latest["request"] == 3
    assert metadata["providerRequestCount"] == 3
    assert metadata["payloadBytes"] > 0
    assert len(metadata["payloadSha256"]) == 64
    assert not (capture_dir / "provider_request_0002.json").exists()
    assert (
        capture_dir / "provider_request_latest.json"
    ).stat().st_mode & 0o777 == 0o600

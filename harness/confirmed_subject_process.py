"""Load and invoke one planned subject runner in an isolated interpreter."""

from __future__ import annotations

import argparse
import importlib.util
import json
import traceback
from collections.abc import Mapping
from pathlib import Path
from types import ModuleType
from typing import cast

_PATH_ARGUMENTS = frozenset(
    {
        "config_leaf",
        "config_root",
        "omp_binary_path",
        "output_cell",
        "task_root",
    }
)


def _read_request(request_path: Path) -> dict[str, object]:
    request: object = json.loads(request_path.read_text())
    if not isinstance(request, dict):
        raise TypeError("Confirmed subject request invalid: expected an object")
    return request


def _load_subject_runner(runner_path: Path) -> ModuleType:
    if not runner_path.is_file():
        raise ValueError(
            "Confirmed subject runner missing: planned runner does not exist "
            f"at {runner_path}"
        )
    specification = importlib.util.spec_from_file_location(
        "_deep_swe_bench_confirmed_subject_runner",
        runner_path,
    )
    if specification is None or specification.loader is None:
        raise ValueError(
            "Confirmed subject runner invalid: cannot load planned runner "
            f"at {runner_path}"
        )
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _request_arguments(
    request: Mapping[str, object],
) -> tuple[str, str, dict[str, object]]:
    config = request.get("config")
    task = request.get("task")
    raw_arguments = request.get("arguments")
    if (
        not isinstance(config, str)
        or not isinstance(task, str)
        or not isinstance(raw_arguments, dict)
    ):
        raise TypeError(
            "Confirmed subject request invalid: config, task, and arguments "
            "must be resolved"
        )
    arguments = dict(raw_arguments)
    for name in _PATH_ARGUMENTS:
        value = arguments.get(name)
        if value is not None:
            if not isinstance(value, str):
                raise TypeError(
                    "Confirmed subject request invalid: path argument "
                    f"{name!r} must be a string"
                )
            arguments[name] = Path(value)
    credential_routes = arguments.get("credential_routes")
    if not isinstance(credential_routes, list) or not all(
        isinstance(route, str) for route in credential_routes
    ):
        raise TypeError(
            "Confirmed subject request invalid: credential routes must be "
            "strings"
        )
    arguments["credential_routes"] = tuple(credential_routes)
    return config, task, arguments


def _render_omp_prompt(
    runner: ModuleType,
    arguments: dict[str, object],
) -> None:
    behavior = arguments.get("subject_behavior")
    if not isinstance(behavior, dict):
        raise TypeError(
            "Confirmed OMP behavior invalid: expected a resolved object"
        )
    system_prompt = behavior.get("systemPrompt")
    if system_prompt is None:
        return
    renderer = getattr(runner, "render_omp_system_prompt_template", None)
    if not callable(renderer):
        raise TypeError(
            "Confirmed OMP runner invalid: system prompt renderer is missing"
        )
    rendered_behavior = dict(behavior)
    rendered_behavior["systemPrompt"] = renderer(system_prompt)
    arguments["subject_behavior"] = rendered_behavior


def execute_confirmed_subject_request(
    request_path: Path,
) -> Mapping[str, object]:
    """Execute one JSON request through its exact planned runner module."""
    request = _read_request(request_path)
    runner_path = request.get("runner")
    subject = request.get("subject")
    if not isinstance(runner_path, str) or subject not in {
        "pi", "omp", "prime-agent"
    }:
        raise TypeError(
            "Confirmed subject request invalid: runner and subject must be "
            "resolved"
        )
    runner = _load_subject_runner(Path(runner_path))
    config, task, arguments = _request_arguments(request)
    if subject == "omp":
        _render_omp_prompt(runner, arguments)
    run_cell = getattr(runner, "run_cell", None)
    if not callable(run_cell):
        raise TypeError(
            "Confirmed subject runner invalid: planned module has no run_cell"
        )
    record = run_cell(config, task, **arguments)
    if not isinstance(record, Mapping):
        raise TypeError(
            "Confirmed subject runner invalid: run_cell must return a mapping"
        )
    return cast(Mapping[str, object], record)


def _write_response(
    response_path: Path, response: Mapping[str, object]
) -> None:
    response_path.write_text(
        json.dumps(response, allow_nan=False, sort_keys=True) + "\n"
    )


def main() -> None:
    """Run the private file-based protocol used by confirmed batch adapters."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--response", type=Path, required=True)
    arguments = parser.parse_args()
    try:
        record = execute_confirmed_subject_request(arguments.request)
    except SystemExit as error:
        _write_response(
            arguments.response,
            {"code": error.code, "status": "system_exit"},
        )
    except Exception as error:  # noqa: BLE001 - preserve child diagnostics.
        _write_response(
            arguments.response,
            {
                "errorMessage": str(error),
                "errorType": type(error).__name__,
                "status": "error",
                "traceback": traceback.format_exc(),
            },
        )
    else:
        _write_response(
            arguments.response,
            {"record": dict(record), "status": "ok"},
        )


if __name__ == "__main__":
    main()

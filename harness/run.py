#!/usr/bin/env python3
"""Run one (config, task) cell end-to-end through pi, then the DeepSWE verifier.

Topology (one task):
  env container  (pi-agent image: task env image + pi). repo at /app.
    |- pi --mode rpc --model ...  (the agent, driven by harness/pi_rpc_runner.py)
    |- bash /task/pre_artifacts.sh  -> /logs/artifacts/model.patch
  verifier container (env image + hidden tests/, --network none)
    |- bash /tests/test.sh          -> /logs/verifier/reward.json

The agent works in the real task container so it can run the project's own tests
with the correct toolchain; the reward is always measured in a pristine verifier
container (separate-env grading), exactly as DeepSWE/Pier define it.

Usage (draft probe only):
  python run.py --config baseline --task abs-module-cache-flags \\
    --probe-output scratch/probes/baseline-abs-module
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import parse_usage  # noqa: E402
import results_tree  # noqa: E402
from config_lock import require_matching_config_lock  # noqa: E402
from config_resolution import resolve_config_leaf  # noqa: E402
from lib import REPO, load_task, read_reward, result_record  # noqa: E402
from pi_rpc_runner import run_pi_rpc  # noqa: E402

DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-flash"
DEFAULT_THINKING = "high"
TRANSIENT_EXIT = 75
INITIAL_CONTEXT_CAPTURE_SOURCE = HERE / "initial_context_capture.js"
INITIAL_CONTEXT_CAPTURE_CONTAINER = "/harness/initial_context_capture.js"
INITIAL_CONTEXT_CAPTURE_OUT = "/out/initial_context"
TRANSIENT_MODEL_ERROR_PATTERNS = [
    "you've hit your usage limit",
    "you have hit your usage limit",
    "usage limit",
    "weekly limit",
    "5-hour limit",
    "try again at",
    "rate limit exceeded",
    "rate_limit_exceeded",
    "too many requests",
    "temporarily rate limited",
]
TRANSIENT_MODEL_ERROR_REGEXES = [
    re.compile(r"(?:http\s*)?(?:status\s*)?(?:error\s*)?\b429\b", re.I),
]
TRANSIENT_ERROR_CONTEXT_PATTERNS = [
    "codex",
    "openai",
    "openrouter",
    "provider",
    "llm",
    "responses",
    "zai",
    "z.ai",
    "vllm",
    "anthropic",
    "gemini",
]
ERROR_CONTEXT_PATTERNS = [
    "error",
    "exception",
    "traceback",
    "failed",
    "failure",
    "unavailable",
]


def sh(cmd: list[str], timeout: float | None = None, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, **kw)


def initial_context_capture_mount(enabled: bool) -> list[str]:
    if not enabled:
        return []
    if not INITIAL_CONTEXT_CAPTURE_SOURCE.exists():
        sys.exit(f"initial context capture extension missing: {INITIAL_CONTEXT_CAPTURE_SOURCE}")
    return ["-v", f"{INITIAL_CONTEXT_CAPTURE_SOURCE}:{INITIAL_CONTEXT_CAPTURE_CONTAINER}:ro"]


def initial_context_capture_env(enabled: bool) -> list[str]:
    if not enabled:
        return []
    env = ["-e", f"PI_INITIAL_CONTEXT_DIR={INITIAL_CONTEXT_CAPTURE_OUT}"]
    for name in (
        "PI_INITIAL_CONTEXT_MAX_CONTEXTS",
        "PI_INITIAL_CONTEXT_MAX_PROVIDER_REQUESTS",
        "PI_INITIAL_CONTEXT_STOP_AFTER",
    ):
        if os.environ.get(name):
            env += ["-e", f"{name}={os.environ[name]}"]
    return env


def initial_context_capture_flags(enabled: bool) -> list[str]:
    return ["-e", INITIAL_CONTEXT_CAPTURE_CONTAINER] if enabled else []


def strip_patch_paths(patch: Path, prefixes: tuple[bytes, ...] = (b".gocache/",)) -> int:
    """Remove generated-cache file sections from a unified git patch.

    Some agents/tools create repository-local Go build caches. If committed,
    those caches can turn one cell's model.patch into hundreds of MB of junk.
    Keep real source diffs; drop only whole diff sections whose a/ or b/ path
    starts with a known generated-cache prefix.
    """
    if not patch.exists():
        return 0
    tmp = patch.with_suffix(patch.suffix + ".tmp")
    original = patch.stat().st_size
    removed = 0
    dropping = False
    current_size = 0
    with patch.open("rb") as src, tmp.open("wb") as dst:
        for line in src:
            if line.startswith(b"diff --git a/"):
                if dropping:
                    removed += current_size
                current_size = len(line)
                parts = line.split()
                paths = []
                if len(parts) >= 4:
                    paths = [parts[2][2:], parts[3][2:]]
                dropping = any(path.startswith(prefix) for path in paths for prefix in prefixes)
                if not dropping:
                    dst.write(line)
                continue
            current_size += len(line)
            if not dropping:
                dst.write(line)
        if dropping:
            removed += current_size
    tmp.replace(patch)
    return max(removed, original - patch.stat().st_size)


def compact_verifier_stdout(stdout: str, verifier_dir: Path) -> str:
    """Keep verifier prelude, but do not duplicate raw suite log files.

    DeepSWE verifier scripts often print full run.log/base_run.log/new_run.log
    to stdout while also writing those files under /logs/verifier. Keeping both
    doubles large test logs. Leave a pointer in stdout and keep the real file.
    """
    out: list[str] = []
    skipping = False
    for line in stdout.splitlines(keepends=True):
        if line.startswith("===== raw suite output: ") and line.rstrip().endswith("====="):
            name = line.rstrip()[len("===== raw suite output: "):]
            name = name.removesuffix("=====").strip()
            log_path = verifier_dir / name
            if log_path.exists():
                out.append(line)
                out.append(f"[compact] raw suite output omitted; see verifier/{name} in this cell.\n")
                skipping = True
                continue
        if skipping:
            if line.startswith("====="):
                skipping = False
            else:
                continue
        if not skipping:
            out.append(line)
    return "".join(out)


def ensure_env_image(env_image: str):
    r = sh(["docker", "image", "inspect", env_image])
    if r.returncode == 0:
        return

    # ECR rate-limits parallel anonymous pulls. One global pull at a time is
    # slower than a stampede, but it actually finishes.
    lock_dir = REPO / "cache"
    lock_dir.mkdir(exist_ok=True)
    with open(lock_dir / "docker-pull.lock", "w") as lf:
        fcntl.flock(lf, fcntl.LOCK_EX)
        r = sh(["docker", "image", "inspect", env_image])
        if r.returncode == 0:
            return
        for attempt in range(1, 7):
            print(f"[image] pulling env image {env_image} (attempt {attempt}/6)", flush=True)
            r = sh(["docker", "pull", "--platform", "linux/amd64", env_image], timeout=1200)
            if r.returncode == 0:
                return
            msg = (r.stderr or r.stdout or "")[-800:]
            if attempt == 6:
                sys.exit(f"[image] pull failed: {msg}")
            sleep_s = 30 * attempt
            print(f"[image] pull failed; retrying in {sleep_s}s: {msg[:300]}", flush=True)
            time.sleep(sleep_s)


def ensure_pi_image(task) -> str:
    img = task.pi_image
    r = sh(["docker", "image", "inspect", img])
    if r.returncode == 0:
        return img
    print(f"[image] building pi-agent layer {img}", flush=True)
    r = sh(["docker", "build", "--build-arg", f"ENV_IMAGE={task.env_image}",
            "-t", img, "-f", str(HERE / "Dockerfile.pi-agent"), str(HERE)], timeout=600)
    if r.returncode != 0:
        sys.exit(f"[image] pi-agent build failed:\n{r.stderr[-1500:]}")
    return img


def ensure_verifier_image(task) -> str:
    img = task.verifier_image
    r = sh(["docker", "image", "inspect", img])
    if r.returncode == 0:
        return img
    print(f"[image] building verifier {img}", flush=True)
    r = sh(["docker", "build", "--platform", "linux/amd64", "-t", img,
            "-f", str(task.dir / "tests" / "Dockerfile"), str(task.dir / "tests")], timeout=1800)
    if r.returncode != 0:
        sys.exit(f"[image] verifier build failed:\n{r.stderr[-1500:]}")
    return img


def load_config(
    config: str,
    model: str,
    thinking: str,
    *,
    repository_root: Path | None = None,
) -> dict:
    """Load a config's constants (from configs/<config>/) and its model leaf
    (from configs/<config>/<model-leaf>/<thinking>/).

    The leaf dir matches the exact executor model-leaf, optionally followed by
    a ``+<secondary-role>`` suffix for configs with additional model roles.
    Returns 'leaf_rel' = the leaf path relative to the config dir, so the
    in-container cp sources are /arm/<leaf_rel>/{models,advisor,settings}.json
    (the config dir is mounted as /arm:ro, preserving /arm/extensions/).
    """
    if repository_root is None:
        repository_root = REPO
    resolved = resolve_config_leaf(repository_root, config, model, thinking)
    require_matching_config_lock(resolved, config)
    return load_resolved_config(resolved.config_root, resolved.config_leaf)


def load_resolved_config(config_root: Path, config_leaf: Path) -> dict:
    """Load one exact config leaf already approved by a launch plan."""
    cdir = config_root
    leafdir = config_leaf
    leaf_rel = leafdir.relative_to(cdir).as_posix()
    skill_dirs = []
    sd = cdir / "skills"
    if sd.is_dir():
        skill_dirs = [p for p in sd.iterdir() if p.is_dir()]
    pi_flags = []
    pf = cdir / "pi-flags"
    if pf.exists():
        pi_flags = [ln.strip() for ln in pf.read_text().splitlines() if ln.strip() and not ln.startswith("#")]
    env_lines = {}
    ef = cdir / "env"
    if ef.exists():
        for ln in ef.read_text().splitlines():
            ln = ln.strip()
            if ln and "=" in ln and not ln.startswith("#"):
                k, v = ln.split("=", 1)
                env_lines[k.strip()] = v.strip()
    def _leaf(name):
        p = leafdir / name
        return p if p.exists() else None
    def _optional_text(name):
        p = cdir / name
        return p.read_text() if p.exists() else ""
    return {"dir": cdir, "leaf_rel": leaf_rel,
            "system_preamble": _optional_text("system_preamble.md"),
            "orchestration": _optional_text("orchestration.md"),
            "skill_dirs": skill_dirs, "pi_flags": pi_flags, "env": env_lines,
            "models_json": _leaf("models.json"),
            "advisor_json": _leaf("advisor.json"),
            "settings_json": _leaf("settings.json")}


def agent_auth_mount(*, pass_openai_codex_oauth: bool, pass_openrouter_env: bool) -> tuple[list[str], str | None]:
    """Build the minimal Pi auth.json mounted into an agent container.

    The main executor can use OPENROUTER_API_KEY from the process environment,
    but extension workers call modelRegistry.getApiKeyAndHeaders(), which does
    not use env fallback. Put an auth.json entry that resolves to the same env
    var so worker models and the main executor share the intended credential
    path without writing the secret into result artifacts.
    """
    data = {}
    if pass_openai_codex_oauth:
        auth = Path.home() / ".pi" / "agent" / "auth.json"
        host_data = json.loads(auth.read_text())
        if "openai-codex" not in host_data:
            sys.exit(f"openai-codex OAuth entry not found in {auth}; run Pi Codex login first")
        data["openai-codex"] = host_data["openai-codex"]
    if pass_openrouter_env:
        data["openrouter"] = {"type": "api_key", "key": "$OPENROUTER_API_KEY"}
    if not data:
        return [], None
    tmp = tempfile.mkdtemp(prefix="dsw-agent-auth-")
    os.chmod(tmp, 0o700)
    (Path(tmp) / "auth.json").write_text(json.dumps(data))
    os.chmod(Path(tmp) / "auth.json", 0o600)
    return ["-v", f"{tmp}:/agent-auth:ro"], tmp


def needs_openrouter_key(model: str, arm_cfg: dict) -> bool:
    if model.startswith("openrouter/"):
        return True
    for key in ("models_json", "settings_json"):
        p = arm_cfg.get(key)
        if p and "OPENROUTER_API_KEY" in Path(p).read_text():
            return True
    return False


def _matches_transient_marker(text: str) -> bool:
    low = text.lower()
    return any(s in low for s in TRANSIENT_MODEL_ERROR_PATTERNS) or any(
        r.search(text) for r in TRANSIENT_MODEL_ERROR_REGEXES
    )


def _looks_like_model_error_context(text: str) -> bool:
    low = text.lower()
    return any(s in low for s in TRANSIENT_ERROR_CONTEXT_PATTERNS) and any(
        s in low for s in ERROR_CONTEXT_PATTERNS
    )


def transient_model_error(paths: list[Path]) -> str | None:
    for p in paths:
        if not p.exists():
            continue
        is_structured = p.suffix in (".jsonl", ".ndjson")
        with p.open(errors="replace") as f:
            for line in f:
                probes: list[tuple[str, bool]] = []
                if is_structured:
                    try:
                        d = json.loads(line)
                        msg = d.get("message") if isinstance(d.get("message"), dict) else d
                        data = d.get("data") if isinstance(d.get("data"), dict) else None
                        for obj in (d, msg, data):
                            if not isinstance(obj, dict):
                                continue
                            stop = str(obj.get("stopReason") or "").lower()
                            role = str(obj.get("role") or "").lower()
                            assistant_error = role == "assistant" and stop == "error"
                            for key in ("errorMessage", "error"):
                                val = obj.get(key)
                                if val and not isinstance(val, (dict, list)):
                                    text = str(val)
                                    probes.append((text, assistant_error or _looks_like_model_error_context(text)))
                            val = obj.get("message")
                            if val and not isinstance(val, (dict, list)):
                                text = str(val)
                                probes.append((text, assistant_error or _looks_like_model_error_context(text)))
                    except Exception:
                        pass
                else:
                    probes.append((line, _looks_like_model_error_context(line)))
                for probe, error_context in probes:
                    if _matches_transient_marker(probe) and error_context:
                        return probe.strip()[:1000]
    return None


_RPC_OWNED_PI_FLAGS = {
    "-p",
    "--print",
    "--mode",
    "--model",
    "--thinking",
    "--session-dir",
    "--append-system-prompt",
}
_RPC_OWNED_PI_FLAG_PREFIXES = tuple(
    f"{flag}=" for flag in _RPC_OWNED_PI_FLAGS if flag.startswith("--")
)


def _validate_rpc_pi_flags(flags: list[str]) -> None:
    """Reject config flags that would silently bypass the RPC harness contract."""
    for flag in flags:
        if flag in _RPC_OWNED_PI_FLAGS or flag.startswith(_RPC_OWNED_PI_FLAG_PREFIXES):
            raise ValueError(f"config pi-flags may not override RPC runner control flag: {flag}")


def config_append_text(arm_cfg: dict) -> str:
    """Return config-authored prompt layers, without any global harness preamble."""
    parts = []
    for key in ("system_preamble", "orchestration"):
        text = (arm_cfg.get(key) or "").strip("\n")
        if text.strip():
            parts.append(text)
    return "\n\n".join(parts)


def pi_cmd(arm_cfg: dict, model: str, thinking: str, append_text: str,
           capture_initial_context: bool = True) -> list[str]:
    flags = arm_cfg["pi_flags"]
    _validate_rpc_pi_flags(flags)
    cmd = ["pi", "--mode", "rpc",
           "--model", model, "--thinking", thinking, "--offline",
           "--session-dir", "/out/session"]
    if append_text:
        cmd += ["--append-system-prompt", append_text]

    # Keep discovery isolated; Pi still loads explicit -e/--extension paths with --no-extensions.
    if not arm_cfg["skill_dirs"]:
        cmd += ["--no-skills"]
    else:
        for s in arm_cfg["skill_dirs"]:
            cmd += ["--skill", f"/arm/skills/{s.name}"]
    cmd += ["--no-extensions"]
    cmd += flags
    # Load last so it observes final chained before_agent_start / provider payload state.
    cmd += initial_context_capture_flags(capture_initial_context)
    return cmd


def run_cell(config: str, task_id: str, *, model: str, thinking: str, rep: int,
             agent_timeout: float | None, keep: bool,
             pass_openai_codex_oauth: bool, rpc_quiescence: float,
             capture_initial_context: bool = True,
             output_cell: Path | None = None,
             persist_result_file: bool = True,
             persist_result_index: bool = True,
             config_root: Path | None = None,
             config_leaf: Path | None = None,
             task_root: Path | None = None) -> dict:
    task = load_task(task_id, root=task_root)
    agent_timeout = agent_timeout or task.agent_timeout_s
    if (config_root is None) != (config_leaf is None):
        raise ValueError(
            "Confirmed config paths invalid: config root and leaf must be "
            "provided together"
        )
    arm_cfg = (
        load_resolved_config(config_root, config_leaf)
        if config_root is not None and config_leaf is not None
        else load_config(config, model, thinking)
    )
    ensure_env_image(task.env_image)
    pi_image = ensure_pi_image(task)

    cell = output_cell or results_tree.Tree.of(
        model, thinking, repo=REPO
    ).cell(config, task_id, rep).dir
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "artifacts").mkdir(exist_ok=True)
    (cell / "verifier").mkdir(exist_ok=True)
    (cell / "logs").mkdir(exist_ok=True)
    (cell / "transient_error.json").unlink(missing_ok=True)

    append_text = config_append_text(arm_cfg)

    suffix = f"{config}-{task_id}-r{rep}-{os.getpid()}"
    cname = f"dsw-{suffix}"
    if model.startswith("openai-codex/") and not pass_openai_codex_oauth:
        sys.exit("openai-codex models require --pass-openai-codex-oauth")

    env_flag = []
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if api_key:
        env_flag += ["-e", f"OPENROUTER_API_KEY={api_key}"]
    elif needs_openrouter_key(model, arm_cfg):
        sys.exit("OPENROUTER_API_KEY not set in environment")

    auth_mount, auth_tmp = agent_auth_mount(
        pass_openai_codex_oauth=pass_openai_codex_oauth,
        pass_openrouter_env=bool(api_key),
    )
    # Optional advisor/secondary-model providers. Passing these symmetrically is
    # harmless; only arms with matching extensions/models use them.
    if os.environ.get("ZAI_API_KEY"):
        env_flag += ["-e", f"ZAI_API_KEY={os.environ['ZAI_API_KEY']}"]
    for k, v in arm_cfg["env"].items():
        env_flag += ["-e", f"{k}={v}"]
    env_flag += initial_context_capture_env(capture_initial_context)

    print(f"[cell] task={task_id} config={config} lang={task.language} "
          f"budget={agent_timeout:.0f}s model={model} thinking={thinking}", flush=True)

    # --- start env container (agent works here) ---
    # Agent sees ONLY instruction.md + pre_artifacts.sh as /task. The reference
    # solution/ and hidden tests/ are verifier-only (baked into the verifier
    # image); never mount the raw task dir into the agent container.
    task_public = tempfile.mkdtemp(prefix="dsw-task-public-")
    shutil.copy2(task.dir / "instruction.md", Path(task_public) / "instruction.md")
    shutil.copy2(task.dir / "pre_artifacts.sh", Path(task_public) / "pre_artifacts.sh")
    run_args = ["docker", "run", "-d", "--name", cname, "--platform", "linux/amd64",
                "-w", "/app",
                "-v", f"{task_public}:/task:ro",
                "-v", f"{cell}:/out",
                "-v", f"{arm_cfg['dir']}:/arm:ro",
                *initial_context_capture_mount(capture_initial_context),
                # /logs mount = same as /out so pre_artifacts + verifier land on host
                "-v", f"{cell}:/logs",
                *auth_mount,
                *env_flag, pi_image, "sleep", str(int(agent_timeout + 600))]
    r = sh(run_args)
    if r.returncode != 0:
        for d in (auth_tmp, task_public):
            if d:
                shutil.rmtree(d, ignore_errors=True)
        sys.exit(f"[cell] docker run failed:\n{r.stderr[:800]}")

    started = time.time()
    status = {}
    try:
        if pass_openai_codex_oauth or arm_cfg.get("advisor_json") or arm_cfg.get("models_json") or arm_cfg.get("settings_json"):
            sh(["docker", "exec", cname, "mkdir", "-p", "/root/.pi/agent"])
            if auth_mount:
                sh(["docker", "exec", cname, "cp", "/agent-auth/auth.json", "/root/.pi/agent/auth.json"])
            if arm_cfg.get("advisor_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/advisor.json", "/root/.pi/agent/advisor.json"])
            if arm_cfg.get("models_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/models.json", "/root/.pi/agent/models.json"])
            if arm_cfg.get("settings_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/settings.json", "/root/.pi/agent/settings.json"])

        # --- run the agent ---
        # Executor usage is read from the native session (session/*.jsonl) AFTER
        # the run. RPC stdout is consumed by harness/pi_rpc_runner.py and is NOT
        # persisted (ADR-0002: raw per-cell streams ballooned to 233GB). For
        # advisor configs the advisor LLM's usage is absent from the session, so
        # the RPC runner filters only advisor tool_execution_end events into
        # tool-usage.jsonl while discarding the full event stream.
        pre_session_paths = set((cell / "session").glob("*.jsonl"))
        pre_om_debug_paths = set((cell / "pi-agent" / "observational-memory" / "debug").glob("*.ndjson"))
        cmd = pi_cmd(arm_cfg, model, thinking, append_text, capture_initial_context)
        # argv list, not shell: the append-system-prompt text contains
        # newlines/spaces that a bash -lc join would mangle. docker exec needs
        # -i so the RPC driver's stdin pipe remains open until quiescence.
        rpc_result = run_pi_rpc(
            ["docker", "exec", "-i", cname, *cmd],
            prompt_text=(Path(task_public) / "instruction.md").read_text(),
            stderr_path=cell / "logs" / "pi.stderr.txt",
            runner_log_path=cell / "logs" / "pi-rpc-runner.jsonl",
            advisor_usage_path=(cell / "tool-usage.jsonl") if arm_cfg.get("advisor_json") else None,
            timeout_s=agent_timeout,
            quiescence_s=rpc_quiescence,
        )
        status["agent_exit"] = rpc_result.exit_code
        if rpc_result.timed_out:
            status["agent_timed_out"] = True
        status["agent_wall_s"] = round(time.time() - started, 1)

        sh(["docker", "exec", cname, "bash", "-lc",
            "mkdir -p /out/pi-agent; "
            "if [ -d /root/.pi/agent/observational-memory ]; then "
            "rm -rf /out/pi-agent/observational-memory && "
            "cp -a /root/.pi/agent/observational-memory /out/pi-agent/observational-memory; fi; "
            "if [ -d /root/.pi/workflows ]; then "
            "rm -rf /out/pi-agent/workflows && "
            "cp -a /root/.pi/workflows /out/pi-agent/workflows; fi"])
        transient_paths = [cell / "logs" / "pi.stderr.txt", cell / "logs" / "pi-rpc-runner.jsonl"]
        transient_paths += [p for p in (cell / "session").glob("*.jsonl") if p not in pre_session_paths]
        transient_paths += [p for p in (cell / "pi-agent" / "observational-memory" / "debug").glob("*.ndjson") if p not in pre_om_debug_paths]
        transient = transient_model_error(transient_paths)
        if transient and status.get("agent_exit") != "timeout":
            status["transient_model_error"] = transient
            (cell / "transient_error.json").write_text(json.dumps(status, indent=2))
            print(f"[pause] transient model error for {task_id}/{config}#{rep}: {transient}", flush=True)
            raise SystemExit(TRANSIENT_EXIT)

        # --- capture ALL work (committed or not) then extract the submission patch ---
        # Commit any uncommitted edits so a forgetful agent is not scored 0 by accident.
        # Keep repository-local build caches out of the commit; they are never a solution.
        sh(["docker", "exec", cname, "bash", "-lc", "find /app -type d -name .gocache -prune -exec rm -rf {} +"])
        for c in (["add", "-A"],
                  ["-c", "user.email=agent@dsw", "-c", "user.name=agent",
                   "commit", "-q", "-m", "agent work", "--allow-empty", "--no-verify"]):
            sh(["docker", "exec", cname, "git", *c])
        # pre_artifacts.sh does: cd /app; git diff <base> HEAD > /logs/artifacts/model.patch
        r = sh(["docker", "exec", cname, "bash", "/task/pre_artifacts.sh"], timeout=120)
        (cell / "logs" / "pre_artifacts.stdout.txt").write_text(r.stdout + r.stderr)
        patch = cell / "artifacts" / "model.patch"
        removed_patch_bytes = strip_patch_paths(patch)
        if removed_patch_bytes:
            status["patch_sanitized_bytes_removed"] = removed_patch_bytes
        status["patch_bytes"] = patch.stat().st_size if patch.exists() else 0
    finally:
        # Keep extension state/debug logs when an arm writes Pi agent-local data.
        sh(["docker", "exec", cname, "sh", "-lc",
            "mkdir -p /out/pi-agent; "
            "if [ -d /root/.pi/agent/observational-memory ]; then "
            "rm -rf /out/pi-agent/observational-memory && "
            "cp -a /root/.pi/agent/observational-memory /out/pi-agent/observational-memory; fi; "
            "if [ -d /root/.pi/workflows ]; then "
            "rm -rf /out/pi-agent/workflows && "
            "cp -a /root/.pi/workflows /out/pi-agent/workflows; fi"])
        if not keep:
            sh(["docker", "rm", "-f", cname])
        for d in (auth_tmp, task_public):
            if d:
                shutil.rmtree(d, ignore_errors=True)

    # --- verify in a pristine, air-gapped container ---
    reward = {"reward": -1, "partial": 0.0}
    if status.get("patch_bytes", 0) > 0:
        try:
            ensure_verifier_image(task)
            r = sh(["docker", "run", "--rm", "--network", "none", "--platform", "linux/amd64",
                    "-v", f"{cell}:/logs",
                    task.verifier_image, "bash", "/tests/test.sh"],
                   timeout=task.verifier_timeout_s + 300)
            verifier_stdout = compact_verifier_stdout(r.stdout + r.stderr, cell / "verifier")
            (cell / "logs" / "verifier.stdout.txt").write_text(verifier_stdout)
            status["verifier_exit"] = r.returncode
            reward = read_reward(cell / "verifier")
        except subprocess.TimeoutExpired:
            status["verifier_exit"] = "timeout"
    else:
        status["verifier_exit"] = "skipped_empty_patch"

    # Executor usage from the native session (newest segment = the run that
    # wrote result.json); advisor and observational-memory worker usage from
    # compact sidecar traces that do not store streamed text deltas.
    usage = parse_usage.parse(
        session_dir=cell / "session",
        advisor_path=cell / "tool-usage.jsonl" if arm_cfg.get("advisor_json") else None,
        worker_usage_path=cell / "pi-agent" / "observational-memory" / "worker-usage" / "usage.ndjson",
        workflow_usage_path=cell / "pi-agent" / "workflows")
    arm_settings = None
    if arm_cfg.get("settings_json"):
        arm_settings = json.loads(Path(arm_cfg["settings_json"]).read_text())
    arm_advisor = None
    if arm_cfg.get("advisor_json"):
        arm_advisor = json.loads(Path(arm_cfg["advisor_json"]).read_text())
    arm_models = None
    if arm_cfg.get("models_json"):
        arm_models = json.loads(Path(arm_cfg["models_json"]).read_text())

    rec = result_record(
        task, config, model, rep,
        arm_pi_flags=arm_cfg["pi_flags"],
        system_preamble_chars=len(arm_cfg.get("system_preamble") or ""),
        orchestration_chars=len(arm_cfg.get("orchestration") or ""),
        append_system_prompt_chars=len(append_text),
        arm_settings=arm_settings,
        arm_advisor=arm_advisor,
        arm_models=arm_models,
        thinking_level=thinking,
        openai_codex_oauth_passed=pass_openai_codex_oauth,
        initial_context_capture_enabled=capture_initial_context,
        initial_context_capture_path="initial_context" if capture_initial_context else None,
        reward_binary=reward.get("reward", -1),
        reward_partial=float(reward.get("partial", 0.0)),
        f2p=reward.get("f2p"), p2p=reward.get("p2p"),
        f2p_passed=reward.get("f2p_passed"), f2p_total=reward.get("f2p_total"),
        p2p_passed=reward.get("p2p_passed"), p2p_total=reward.get("p2p_total"),
        patch_bytes=status.get("patch_bytes", 0),
        agent_exit=status.get("agent_exit"),
        agent_timed_out=status.get("agent_timed_out", False),
        verifier_exit=status.get("verifier_exit"),
        agent_wall_s=status.get("agent_wall_s"),
        **usage,
    )
    if persist_result_file:
        (cell / "result.json").write_text(json.dumps(rec, indent=2))
    if persist_result_index:
        rl = results_tree.Tree.of(model, thinking, repo=REPO).results_jsonl
        rl.parent.mkdir(parents=True, exist_ok=True)
        with open(rl, "a") as f:
            f.write(json.dumps(rec) + "\n")
    print(f"[done] {task_id}/{config}#{rep}: partial={rec['reward_partial']:.3f} "
          f"binary={rec['reward_binary']} tok={rec['total_tokens']} "
          f"cost=${rec['cost_usd']:.4f} wall={rec['agent_wall_s']}s "
          f"patch={rec['patch_bytes']}B", flush=True)
    return rec


def require_draft_probe_output(
    probe_output: Path | None,
    canonical_results: Path,
) -> Path:
    """Return a resolved scratch probe cell outside canonical results."""
    if probe_output is None:
        raise SystemExit(
            "Draft probe required: direct one-cell debugging needs "
            "--probe-output outside canonical results"
        )
    resolved_output = probe_output.resolve()
    canonical_root = canonical_results.resolve()
    if resolved_output == canonical_root or resolved_output.is_relative_to(
        canonical_root
    ):
        raise SystemExit(
            "Draft probe output invalid: scratch output must be outside "
            f"canonical results at {canonical_root}"
        )
    return resolved_output


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--task", required=True)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--thinking", default=DEFAULT_THINKING,
                    choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--rep", type=int, default=0)
    ap.add_argument("--agent-timeout", type=float, default=None,
                    help="override task's agent timeout (s). default: task.toml")
    ap.add_argument("--keep", action="store_true", help="keep the env container for debugging")
    ap.add_argument("--pass-openai-codex-oauth", action="store_true",
                    help="copy only the host openai-codex OAuth entry into the agent container")
    ap.add_argument("--rpc-quiescence", type=float, default=2.0,
                    help="seconds Pi RPC must remain idle with no pending messages before the cell stops")
    ap.add_argument("--no-initial-context-capture", action="store_true",
                    help="disable initial system/context/provider-request capture under result initial_context/")
    ap.add_argument(
        "--probe-output",
        type=Path,
        help="required scratch cell for direct draft/probe debugging",
    )
    args = ap.parse_args()

    probe_output = require_draft_probe_output(
        args.probe_output,
        REPO / "results",
    )

    task = load_task(args.task)
    to = args.agent_timeout or task.agent_timeout_s
    rec = run_cell(args.config, args.task, model=args.model, thinking=args.thinking,
                   rep=args.rep, agent_timeout=to, keep=args.keep,
                   pass_openai_codex_oauth=args.pass_openai_codex_oauth,
                   rpc_quiescence=args.rpc_quiescence,
                   capture_initial_context=not args.no_initial_context_capture,
                   output_cell=probe_output,
                   persist_result_index=False)
    print(json.dumps({"ok": True, "reward_partial": rec["reward_partial"],
                      "total_tokens": rec["total_tokens"]}))


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Run one (config, task) cell end-to-end through pi, then the DeepSWE verifier.

Topology (one task):
  env container  (pi-agent image: task env image + pi). repo at /app.
    |- pi -p @/task/instruction.md --model ... --mode json   (the agent)
    |- bash /task/pre_artifacts.sh  -> /logs/artifacts/model.patch
  verifier container (env image + hidden tests/, --network none)
    |- bash /tests/test.sh          -> /logs/verifier/reward.json

The agent works in the real task container so it can run the project's own tests
with the correct toolchain; the reward is always measured in a pristine verifier
container (separate-env grading), exactly as DeepSWE/Pier define it.

Usage:
  python run.py --config baseline --task abs-module-cache-flags
  python run.py --config ponytail-full --task <id> --agent-timeout 600
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
sys.path.insert(0, str(HERE))
from lib import load_task, instruction_text, read_reward, result_record, model_leaf  # noqa: E402
import parse_usage  # noqa: E402

DEFAULT_MODEL = "openrouter/deepseek/deepseek-v4-flash"
DEFAULT_THINKING = "high"
TRANSIENT_EXIT = 75
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
    "429",
]


def sh(cmd: list[str], timeout: float | None = None, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, **kw)


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


def load_config(config: str, model: str, thinking: str) -> dict:
    """Load a config's constants (from configs/<config>/) and its model leaf
    (from configs/<config>/<model-leaf>/<thinking>/).

    The leaf dir matches the executor model-leaf, optionally with a +advisor
    suffix (advisor configs): glob `<exec-leaf>*/<thinking>` catches both.
    Returns 'leaf_rel' = the leaf path relative to the config dir, so the
    in-container cp sources are /arm/<leaf_rel>/{models,advisor,settings}.json
    (the config dir is mounted as /arm:ro, preserving /arm/extensions/).
    """
    cdir = REPO / "configs" / config
    if not cdir.exists():
        sys.exit(f"config not found: {cdir}")
    exec_leaf = model_leaf(model)
    candidates = sorted(p for p in cdir.glob(f"{exec_leaf}*/{thinking}") if p.is_dir())
    leafdir = candidates[0] if candidates else cdir / exec_leaf / thinking
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
    return {"dir": cdir, "leaf_rel": leaf_rel,
            "orchestration": (cdir / "orchestration.md").read_text(),
            "skill_dirs": skill_dirs, "pi_flags": pi_flags, "env": env_lines,
            "models_json": _leaf("models.json"),
            "advisor_json": _leaf("advisor.json"),
            "settings_json": _leaf("settings.json")}


def openai_codex_auth_mount() -> tuple[list[str], str]:
    auth = Path.home() / ".pi" / "agent" / "auth.json"
    data = json.loads(auth.read_text())
    if "openai-codex" not in data:
        sys.exit(f"openai-codex OAuth entry not found in {auth}; run Pi Codex login first")
    tmp = tempfile.mkdtemp(prefix="dsw-codex-auth-")
    os.chmod(tmp, 0o700)
    (Path(tmp) / "auth.json").write_text(json.dumps({"openai-codex": data["openai-codex"]}))
    os.chmod(Path(tmp) / "auth.json", 0o600)
    return ["-v", f"{tmp}:/codex-auth:ro"], tmp


def needs_openrouter_key(model: str, arm_cfg: dict) -> bool:
    if model.startswith("openrouter/"):
        return True
    for key in ("models_json", "settings_json"):
        p = arm_cfg.get(key)
        if p and "OPENROUTER_API_KEY" in Path(p).read_text():
            return True
    return False


def transient_model_error(paths: list[Path]) -> str | None:
    for p in paths:
        if not p.exists():
            continue
        is_structured = p.suffix in (".jsonl", ".ndjson")
        with p.open(errors="replace") as f:
            for line in f:
                probes = []
                if is_structured:
                    try:
                        d = json.loads(line)
                        msg = d.get("message") if isinstance(d.get("message"), dict) else d
                        for obj in (d, msg, d.get("data") if isinstance(d.get("data"), dict) else None):
                            if isinstance(obj, dict):
                                for key in ("errorMessage", "error", "stopReason", "message"):
                                    val = obj.get(key)
                                    if val and not isinstance(val, (dict, list)):
                                        probes.append(str(val))
                    except Exception:
                        pass
                else:
                    probes.append(line)
                for probe in probes:
                    low = probe.lower()
                    if any(s in low for s in TRANSIENT_MODEL_ERROR_PATTERNS):
                        return probe.strip()[:1000]
    return None


def _drain_advisor_stream(proc: subprocess.Popen, path: Path) -> None:
    """Filter pi --mode json stdout to tool-usage.jsonl, keeping only advisor
    tool_execution_end events.

    Advisor LLM usage is absent from the native session (it runs through the
    extension's own provider path), so it is recovered from the stream. Runs in
    a background thread so the stdout pipe never fills and blocks pi; it ends
    naturally when the process exits and the pipe hits EOF. The substring
    pre-filter skips the bulk of streaming lines before the JSON parse.
    """
    with open(path, "w") as tu:
        for raw in proc.stdout:
            line = raw.decode("utf-8", "replace")
            if '"tool_execution_end"' not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("toolName") == "advisor":
                tu.write(line)


def pi_cmd(arm_cfg: dict, model: str, thinking: str, append_text: str) -> list[str]:
    cmd = ["pi", "-p", "@/task/instruction.md",
           "--model", model, "--thinking", thinking, "--mode", "json", "--offline",
           "--session-dir", "/out/session",
           "--append-system-prompt", append_text]
    flags = arm_cfg["pi_flags"]

    # Keep discovery isolated; Pi still loads explicit -e/--extension paths with --no-extensions.
    if not arm_cfg["skill_dirs"]:
        cmd += ["--no-skills"]
    else:
        for s in arm_cfg["skill_dirs"]:
            cmd += ["--skill", f"/arm/skills/{s.name}"]
    cmd += ["--no-extensions"]
    cmd += flags
    return cmd


def run_cell(config: str, task_id: str, *, model: str, thinking: str, rep: int,
             agent_timeout: float, keep: bool, pass_openai_codex_oauth: bool) -> dict:
    task = load_task(task_id)
    arm_cfg = load_config(config, model, thinking)
    ensure_env_image(task.env_image)
    pi_image = ensure_pi_image(task)

    mleaf = model_leaf(model)
    cell = REPO / "results" / mleaf / thinking / config / task_id / f"rep{rep}"
    cell.mkdir(parents=True, exist_ok=True)
    (cell / "artifacts").mkdir(exist_ok=True)
    (cell / "verifier").mkdir(exist_ok=True)
    (cell / "logs").mkdir(exist_ok=True)

    preamble = (HERE / "system_preamble.md").read_text()
    append_text = preamble + "\n\n" + arm_cfg["orchestration"]

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

    auth_mount, auth_tmp = ([], None)
    if pass_openai_codex_oauth:
        auth_mount, auth_tmp = openai_codex_auth_mount()
    # Optional advisor/secondary-model providers. Passing these symmetrically is
    # harmless; only arms with matching extensions/models use them.
    if os.environ.get("ZAI_API_KEY"):
        env_flag += ["-e", f"ZAI_API_KEY={os.environ['ZAI_API_KEY']}"]
    for k, v in arm_cfg["env"].items():
        env_flag += ["-e", f"{k}={v}"]

    print(f"[cell] task={task_id} config={config} lang={task.language} "
          f"budget={agent_timeout:.0f}s model={model} thinking={thinking}", flush=True)

    # --- start env container (agent works here) ---
    run_args = ["docker", "run", "-d", "--name", cname, "--platform", "linux/amd64",
                "-w", "/app",
                "-v", f"{task.dir}:/task:ro",
                "-v", f"{cell}:/out",
                "-v", f"{arm_cfg['dir']}:/arm:ro",
                # /logs mount = same as /out so pre_artifacts + verifier land on host
                "-v", f"{cell}:/logs",
                *auth_mount,
                *env_flag, pi_image, "sleep", str(int(agent_timeout + 600))]
    r = sh(run_args)
    if r.returncode != 0:
        if auth_tmp:
            shutil.rmtree(auth_tmp, ignore_errors=True)
        sys.exit(f"[cell] docker run failed:\n{r.stderr[:800]}")

    started = time.time()
    status = {}
    try:
        if pass_openai_codex_oauth or arm_cfg.get("advisor_json") or arm_cfg.get("models_json") or arm_cfg.get("settings_json"):
            sh(["docker", "exec", cname, "mkdir", "-p", "/root/.pi/agent"])
            if pass_openai_codex_oauth:
                sh(["docker", "exec", cname, "cp", "/codex-auth/auth.json", "/root/.pi/agent/auth.json"])
            if arm_cfg.get("advisor_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/advisor.json", "/root/.pi/agent/advisor.json"])
            if arm_cfg.get("models_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/models.json", "/root/.pi/agent/models.json"])
            if arm_cfg.get("settings_json"):
                sh(["docker", "exec", cname, "cp", f"/arm/{arm_cfg['leaf_rel']}/settings.json", "/root/.pi/agent/settings.json"])

        # --- run the agent ---
        # Executor usage is read from the native session (session/*.jsonl) AFTER
        # the run; the --mode json stream is NOT persisted (ADR-0002: per-cell
        # pi.jsonl streams ballooned to 233GB). For advisor configs the advisor
        # LLM's usage is absent from the session, so the stream is filtered on
        # the fly to tool-usage.jsonl (advisor tool_execution_end events only);
        # for non-advisor configs the stream is discarded entirely.
        cmd = pi_cmd(arm_cfg, model, thinking, append_text)
        with open(cell / "logs" / "pi.stderr.txt", "w") as se:
            # argv list, not shell: the append-system-prompt text contains
            # newlines/spaces that a bash -lc join would mangle.
            if arm_cfg.get("advisor_json"):
                proc = subprocess.Popen(["docker", "exec", cname, *cmd],
                                        stdout=subprocess.PIPE, stderr=se)
                drain = threading.Thread(
                    target=_drain_advisor_stream,
                    args=(proc, cell / "tool-usage.jsonl"), daemon=True)
                drain.start()
            else:
                proc = subprocess.Popen(["docker", "exec", cname, *cmd],
                                        stdout=subprocess.DEVNULL, stderr=se)
            try:
                proc.wait(timeout=agent_timeout)
                status["agent_exit"] = proc.returncode
            except subprocess.TimeoutExpired:
                proc.kill()
                status["agent_exit"] = "timeout"
                status["agent_timed_out"] = True
            if arm_cfg.get("advisor_json"):
                drain.join(timeout=30)
        status["agent_wall_s"] = round(time.time() - started, 1)

        sh(["docker", "exec", cname, "bash", "-lc",
            "if [ -d /root/.pi/agent/observational-memory ]; then "
            "mkdir -p /out/pi-agent && cp -a /root/.pi/agent/observational-memory /out/pi-agent/; fi"])
        transient_paths = [cell / "logs" / "pi.stderr.txt"]
        transient_paths += list((cell / "pi-agent" / "observational-memory" / "debug").glob("*.ndjson"))
        transient = transient_model_error(transient_paths)
        if transient and status.get("agent_exit") != "timeout":
            status["transient_model_error"] = transient
            (cell / "transient_error.json").write_text(json.dumps(status, indent=2))
            print(f"[pause] transient model error for {task_id}/{config}#{rep}: {transient}", flush=True)
            raise SystemExit(TRANSIENT_EXIT)

        # --- capture ALL work (committed or not) then extract the submission patch ---
        # Commit any uncommitted edits so a forgetful agent is not scored 0 by accident.
        for c in (["add", "-A"],
                  ["-c", "user.email=agent@dsw", "-c", "user.name=agent",
                   "commit", "-q", "-m", "agent work", "--allow-empty", "--no-verify"]):
            sh(["docker", "exec", cname, "git", *c])
        # pre_artifacts.sh does: cd /app; git diff <base> HEAD > /logs/artifacts/model.patch
        r = sh(["docker", "exec", cname, "bash", "/task/pre_artifacts.sh"], timeout=120)
        (cell / "logs" / "pre_artifacts.stdout.txt").write_text(r.stdout + r.stderr)
        patch = cell / "artifacts" / "model.patch"
        status["patch_bytes"] = patch.stat().st_size if patch.exists() else 0
    finally:
        # Keep extension state/debug logs when an arm writes Pi agent-local data.
        sh(["docker", "exec", cname, "sh", "-lc",
            "if [ -d /root/.pi/agent/observational-memory ]; then "
            "mkdir -p /out/pi-agent && cp -a /root/.pi/agent/observational-memory /out/pi-agent/; fi"])
        if not keep:
            sh(["docker", "rm", "-f", cname])
        if auth_tmp:
            shutil.rmtree(auth_tmp, ignore_errors=True)

    # --- verify in a pristine, air-gapped container ---
    reward = {"reward": -1, "partial": 0.0}
    if status.get("patch_bytes", 0) > 0:
        try:
            ensure_verifier_image(task)
            r = sh(["docker", "run", "--rm", "--network", "none", "--platform", "linux/amd64",
                    "-v", f"{cell}:/logs",
                    task.verifier_image, "bash", "/tests/test.sh"],
                   timeout=task.verifier_timeout_s + 300)
            (cell / "logs" / "verifier.stdout.txt").write_text(r.stdout + r.stderr)
            status["verifier_exit"] = r.returncode
            reward = read_reward(cell / "verifier")
        except subprocess.TimeoutExpired:
            status["verifier_exit"] = "timeout"
    else:
        status["verifier_exit"] = "skipped_empty_patch"

    # Executor usage from the native session (newest segment = the run that
    # wrote result.json); advisor usage from the filtered tool-usage.jsonl.
    usage = parse_usage.parse(
        session_dir=cell / "session",
        advisor_path=cell / "tool-usage.jsonl" if arm_cfg.get("advisor_json") else None)
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
        arm_settings=arm_settings,
        arm_advisor=arm_advisor,
        arm_models=arm_models,
        thinking_level=thinking,
        openai_codex_oauth_passed=pass_openai_codex_oauth,
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
    (cell / "result.json").write_text(json.dumps(rec, indent=2))
    rl = REPO / "results" / mleaf / thinking / "results.jsonl"
    rl.parent.mkdir(parents=True, exist_ok=True)
    with open(rl, "a") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"[done] {task_id}/{config}#{rep}: partial={rec['reward_partial']:.3f} "
          f"binary={rec['reward_binary']} tok={rec['total_tokens']} "
          f"cost=${rec['cost_usd']:.4f} wall={rec['agent_wall_s']}s "
          f"patch={rec['patch_bytes']}B", flush=True)
    return rec


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
    args = ap.parse_args()

    task = load_task(args.task)
    to = args.agent_timeout or task.agent_timeout_s
    rec = run_cell(args.config, args.task, model=args.model, thinking=args.thinking,
                   rep=args.rep, agent_timeout=to, keep=args.keep,
                   pass_openai_codex_oauth=args.pass_openai_codex_oauth)
    print(json.dumps({"ok": True, "reward_partial": rec["reward_partial"],
                      "total_tokens": rec["total_tokens"]}))


if __name__ == "__main__":
    main()

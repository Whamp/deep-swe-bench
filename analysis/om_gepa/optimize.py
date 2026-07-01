from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from types import SimpleNamespace
from typing import Any

from . import ARTIFACT_ROOT, DEFAULT_CONFIG, REPO_ROOT
from .common import prompt_file_for_role, prompt_patch, read_jsonl, read_prompt_constant, run_ts_runner, write_jsonl
from .evaluate import evaluate_cases, score as score_output


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def make_run_dir(role: str, name: str | None = None) -> Path:
    run_name = name or f"{timestamp()}-{role}-gepa"
    run_dir = ARTIFACT_ROOT / "runs" / run_name
    (run_dir / "candidates").mkdir(parents=True, exist_ok=True)
    return run_dir


def incumbent_prompt(role: str, config: Path = DEFAULT_CONFIG) -> str:
    constant = "OBSERVER_SYSTEM" if role == "observer" else "REFLECTOR_SYSTEM"
    return read_prompt_constant(prompt_file_for_role(config, role), constant)


def comparison(candidate: dict[str, Any], incumbent: dict[str, Any]) -> dict[str, Any]:
    candidate_mean = float(candidate.get("mean_score", 0.0))
    incumbent_mean = float(incumbent.get("mean_score", 0.0))
    candidate_valid = float(candidate.get("valid_rate", 0.0))
    incumbent_valid = float(incumbent.get("valid_rate", 0.0))
    return {
        "incumbent_mean_score": incumbent_mean,
        "candidate_mean_score": candidate_mean,
        "delta_mean_score": candidate_mean - incumbent_mean,
        "incumbent_valid_rate": incumbent_valid,
        "candidate_valid_rate": candidate_valid,
        "delta_valid_rate": candidate_valid - incumbent_valid,
        "cases": candidate.get("cases", incumbent.get("cases")),
    }


# Step-5 selection gate: a candidate is only promote-worthy if it beats the incumbent
# by at least VAL_GATE_MIN_DELTA on val mean score AND does not lower valid_rate.
# Applied before any held-out test runs, per the goal's step-5 rule.
VAL_GATE_MIN_DELTA = 0.02


def val_gate_decision(val_comparison: dict[str, Any]) -> dict[str, Any]:
    delta = float(val_comparison.get("delta_mean_score", 0.0))
    valid_delta = float(val_comparison.get("delta_valid_rate", 0.0))
    cleared = delta >= VAL_GATE_MIN_DELTA and valid_delta >= 0.0
    if cleared:
        reason = f"cleared: val delta {delta:+.4f} >= +{VAL_GATE_MIN_DELTA:.2f} and valid_rate delta {valid_delta:+.4f} >= 0"
    elif delta < VAL_GATE_MIN_DELTA:
        reason = f"not cleared: val delta {delta:+.4f} below +{VAL_GATE_MIN_DELTA:.2f} threshold"
    else:
        reason = f"not cleared: valid_rate delta {valid_delta:+.4f} < 0"
    return {
        "cleared": cleared,
        "min_delta": VAL_GATE_MIN_DELTA,
        "val_delta": delta,
        "valid_rate_delta": valid_delta,
        "reason": reason,
    }


def format_comparison(label: str, data: dict[str, Any]) -> str:
    return (
        f"- {label} incumbent mean: {data['incumbent_mean_score']:.4f}\n"
        f"- {label} candidate mean: {data['candidate_mean_score']:.4f}\n"
        f"- {label} delta: {data['delta_mean_score']:+.4f}\n"
        f"- {label} incumbent valid_rate: {data['incumbent_valid_rate']:.4f}\n"
        f"- {label} candidate valid_rate: {data['candidate_valid_rate']:.4f}\n"
    )


def dry_run(role: str, train: Path, val: Path, run_dir: Path, candidate_prompt: Path | None, train_limit: int | None, val_limit: int | None) -> dict[str, object]:
    prompt_path = candidate_prompt or run_dir / "candidates" / "incumbent_prompt.txt"
    if candidate_prompt is None:
        prompt_path.write_text(incumbent_prompt(role), encoding="utf-8")
    train_summary = evaluate_cases(role, train, run_dir / "train", prompt_path, "gold", train_limit)
    val_summary = evaluate_cases(role, val, run_dir / "val", prompt_path, "gold", val_limit)
    train_comparison = comparison(train_summary, train_summary)
    val_comparison = comparison(val_summary, val_summary)
    shutil.copyfile(prompt_path, run_dir / "candidates" / "best_prompt.txt")
    manifest = {
        "mode": "dry-run",
        "role": role,
        "train": train_summary,
        "val": val_summary,
        "train_comparison": train_comparison,
        "val_comparison": val_comparison,
        "val_gate": val_gate_decision(val_comparison),
        "best_prompt": str(run_dir / "candidates" / "best_prompt.txt"),
        "note": "Dry-run exercises the exact replay/eval/promotion artifact path. Install dspy+gepa to enable evolutionary candidate search.",
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "report.md").write_text(
        f"# OM GEPA {role} optimization dry-run\n\n"
        + format_comparison("train", train_comparison)
        + format_comparison("val", val_comparison)
        + f"- val gate: {manifest['val_gate']['reason']}\n"
        + f"- best prompt: `candidates/best_prompt.txt`\n\n"
        + "This run did not perform DSPy GEPA evolution because it was invoked with `--dry-run`.\n",
        encoding="utf-8",
    )
    return manifest


class ReplayProgramBase:
    """Mixin for DSPy modules that evaluate prompt text through the real TS worker runner."""

    role: str
    runner_mode: str
    eval_rows: list[dict[str, Any]]

    backend: str
    worker_model: str | None
    worker_thinking: str | None

    def _run_replay(self, case: dict[str, Any], prompt: str) -> dict[str, Any]:
        # In-process memo: the incumbent prompt is constant across GEPA iterations and gets
        # re-scored every round. Keying on (prompt_sha256, case_id) skips those repeats without
        # an on-disk store; candidates have fresh prompts each iteration so they score normally.
        memo_key = (hashlib.sha256(prompt.encode("utf-8")).hexdigest(), case.get("case_id"))
        cached = self._replay_memo.get(memo_key)
        if cached is not None:
            cached_row, cached_result = cached
            self.eval_rows.append(dict(cached_row))
            return cached_result
        with NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False) as pf:
            pf.write(prompt)
            prompt_path = Path(pf.name)
        with NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as cf:
            json.dump(case, cf, ensure_ascii=False)
            case_path = Path(cf.name)
        try:
            output = run_ts_runner(
                self.role,
                case_path,
                prompt_path,
                self.runner_mode,
                backend=self.backend,
                model=self.worker_model,
                thinking_level=self.worker_thinking,
            )
            scored = score_output(self.role, case, output)
        finally:
            prompt_path.unlink(missing_ok=True)
            case_path.unlink(missing_ok=True)
        row = {
            "case_id": case.get("case_id"),
            "score": float(scored["score"]),
            "valid": bool(scored["valid"]),
            "feedback": scored["feedback"],
            "runner_mode": self.runner_mode,
            "backend": self.backend,
            "model": self.worker_model,
            "thinking_level": self.worker_thinking,
        }
        self.eval_rows.append(dict(row))
        result = {"output": output, "score": float(scored["score"]), "valid": bool(scored["valid"]), "feedback": scored["feedback"]}
        self._replay_memo[memo_key] = (row, result)
        return result


def make_reflection_lm(dspy: Any, model_spec: str, thinking: str) -> Any:
    if not model_spec.startswith("openai-codex/"):
        return dspy.LM(model_spec, temperature=1.0, max_tokens=4096)

    class CodexSubscriptionLM(dspy.BaseLM):  # type: ignore[misc]
        def __init__(self, model: str, thinking: str):
            super().__init__(model=model, temperature=1.0, max_tokens=4096)
            self.thinking = thinking

        def forward(self, prompt: str | None = None, messages: list[dict[str, Any]] | None = None, **kwargs: Any) -> Any:
            payload = {"prompt": prompt, "messages": messages, "systemPrompt": kwargs.get("system_prompt")}
            cmd = [
                "npx",
                "-y",
                "tsx",
                str(ARTIFACT_ROOT / "runners" / "codex_lm.ts"),
                "--model",
                self.model,
                "--thinking",
                self.thinking,
                "--max-tokens",
                str(kwargs.get("max_tokens") or self.kwargs.get("max_tokens") or 4096),
            ]
            proc = subprocess.run(cmd, cwd=REPO_ROOT, input=json.dumps(payload), text=True, capture_output=True, check=False)
            if proc.returncode != 0:
                raise RuntimeError(f"Codex reflection LM failed ({proc.returncode})\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
            try:
                result = json.loads(proc.stdout)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Codex reflection LM did not emit JSON\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}") from exc
            text = result.get("text") or ""
            return SimpleNamespace(
                model=self.model,
                choices=[SimpleNamespace(message=SimpleNamespace(content=text))],
                usage=result.get("usage") or {},
            )

    return CodexSubscriptionLM(model_spec, thinking)


def gepa_optimize(
    role: str,
    train: Path,
    val: Path,
    run_dir: Path,
    budget: str,
    reflection_model: str,
    train_limit: int | None,
    val_limit: int | None,
    runner_mode: str,
    max_metric_calls_override: int | None,
    candidate_prompt: Path | None,
    backend: str,
    worker_model: str | None,
    worker_thinking: str | None,
    reflection_thinking: str,
) -> dict[str, object]:
    try:
        import dspy  # type: ignore
    except Exception as exc:  # pragma: no cover - optional dependency
        raise SystemExit(
            "DSPy/GEPA is not installed. Install optional dependencies first, e.g. `pip install dspy gepa litellm`, "
            "or run with `--dry-run` to verify replay/evaluation artifacts."
        ) from exc

    train_cases = read_jsonl(train)
    val_cases = read_jsonl(val)
    if train_limit is not None:
        train_cases = train_cases[:train_limit]
    if val_limit is not None:
        val_cases = val_cases[:val_limit]
    if not train_cases or not val_cases:
        raise SystemExit("Train and validation case files must both contain at least one case.")

    seed_prompt = candidate_prompt.read_text(encoding="utf-8") if candidate_prompt else incumbent_prompt(role)
    max_metric_calls = max_metric_calls_override or {"light": 20, "medium": 60, "heavy": 150}[budget]

    class TraceOnlyLM(dspy.BaseLM):  # type: ignore[misc]
        def forward(self, prompt: str | None = None, messages: list[dict[str, Any]] | None = None, **kwargs: Any) -> Any:
            from types import SimpleNamespace

            content = "[[ ## output_json ## ]]\n{}\n\n[[ ## completed ## ]]"
            return SimpleNamespace(model=self.model, choices=[SimpleNamespace(message=SimpleNamespace(content=content))], usage={})

    class ReplayProgram(ReplayProgramBase, dspy.Module):  # type: ignore[misc, valid-type]
        def __init__(self, role: str, runner_mode: str, prompt: str, backend: str, worker_model: str | None, worker_thinking: str | None):
            super().__init__()
            self.role = role
            self.runner_mode = runner_mode
            self.backend = backend
            self.worker_model = worker_model
            self.worker_thinking = worker_thinking
            self.prompt = dspy.Predict("case -> output_json")
            self.prompt.signature = self.prompt.signature.with_instructions(prompt)
            self.eval_rows = []
            self._replay_memo = {}

        def forward(self, case: dict[str, Any]):
            prompt_text = self.prompt.signature.instructions
            # GEPA's DSPy adapter mutates predictor instructions based on captured predictor traces.
            # The actual judged behavior comes from the TS runner below; this fake LM call exists only
            # to attach a valid predictor trace to the current candidate prompt without reimplementing
            # the OM worker in Python or spending an extra model call.
            with dspy.context(lm=TraceOnlyLM("om-gepa-trace-only")):
                _ = self.prompt(case=json.dumps({"case_id": case.get("case_id")}, ensure_ascii=False))
            replay = self._run_replay(case, prompt_text)
            return dspy.Prediction(output=replay["output"], score=replay["score"], valid=replay["valid"], feedback=replay["feedback"])

    from dspy.teleprompt.gepa.gepa_utils import ScoreWithFeedback  # type: ignore

    def metric(example: Any, pred: Any, *args: Any, **kwargs: Any) -> Any:
        feedback = getattr(pred, "feedback", None) or "No feedback returned."
        return ScoreWithFeedback(score=float(getattr(pred, "score", 0.0)), feedback=str(feedback))

    trainset = [dspy.Example(case=case).with_inputs("case") for case in train_cases]
    valset = [dspy.Example(case=case).with_inputs("case") for case in val_cases]
    program = ReplayProgram(role, runner_mode, seed_prompt, backend, worker_model, worker_thinking)
    reflection_lm = make_reflection_lm(dspy, reflection_model, reflection_thinking)
    teleprompter = dspy.GEPA(
        metric=metric,
        max_metric_calls=max_metric_calls,
        reflection_lm=reflection_lm,
        log_dir=str(run_dir / "gepa"),
        track_stats=True,
        candidate_selection_strategy="pareto",
        reflection_minibatch_size=1 if len(trainset) <= 2 else 3,
        num_threads=1,
        skip_perfect_score=False,
        use_merge=False,
    )
    try:
        compiled = teleprompter.compile(program, trainset=trainset, valset=valset)
    except RuntimeError as exc:
        # GEPA hardcodes raise_on_exception=True, so a Codex subscription-limit error
        # mid-run (worker or reflection model) propagates here. Preserve the partial
        # per-iteration state GEPA already wrote to run_dir/gepa/, write a BLOCKER note,
        # and exit cleanly so the run can be resumed after the subscription window resets
        # instead of crashing with total progress loss.
        msg = str(exc)
        if "usage limit" in msg.lower() or "quota" in msg.lower() or "rate limit" in msg.lower() or "codex error" in msg.lower():
            blocker = run_dir / "BLOCKER-quota-midrun.md"
            blocker.write_text(
                f"# BLOCKED: Codex subscription limit hit mid-GEPA-run\n\n"
                f"Run: `{run_dir.name}`\n"
                f"Role: {role}\n"
                f"Stage: `teleprompter.compile()` (GEPA evolutionary loop)\n\n"
                f"The worker or reflection model returned a subscription-limit error mid-run.\n"
                f"GEPA's per-iteration artifacts up to the failure point are preserved in:\n"
                f"  `{run_dir / 'gepa'}`\n\n"
                "## Error\n```\n"
                f"{msg[:2000]}\n"
                "```\n\n"
                f"## Resume\n"
                f"Remove `candidates/` and `gepa/`, wait for the Codex subscription window to\n"
                f"reset, then relaunch the same command from BLOCKER-quota-exhausted.md.\n",
                encoding="utf-8",
            )
            (run_dir / "manifest.json").write_text(
                json.dumps({"mode": "blocked-quota", "role": role, "error": msg[:500], "blocker": str(blocker), "partial_state_dir": str(run_dir / "gepa")}, indent=2),
                encoding="utf-8",
            )
            raise SystemExit(
                f"Codex subscription limit hit mid-GEPA-run. BLOCKER + partial state written to:\n  {blocker}\n"
                f"Remove `candidates/` and `gep/` and relaunch after the window resets."
            )
        raise
    best = compiled.prompt.signature.instructions
    best_path = run_dir / "candidates" / "best_prompt.txt"
    best_path.write_text(best, encoding="utf-8")
    (run_dir / "candidates" / "incumbent_prompt.txt").write_text(seed_prompt, encoding="utf-8")
    write_jsonl(run_dir / "gepa_evaluations.jsonl", getattr(compiled, "eval_rows", []))
    incumbent_path = run_dir / "candidates" / "incumbent_prompt.txt"
    incumbent_train_summary = evaluate_cases(role, train, run_dir / "incumbent_train", incumbent_path, runner_mode, train_limit, backend=backend, model=worker_model, thinking_level=worker_thinking)
    incumbent_val_summary = evaluate_cases(role, val, run_dir / "incumbent_val", incumbent_path, runner_mode, val_limit, backend=backend, model=worker_model, thinking_level=worker_thinking)
    train_summary = evaluate_cases(role, train, run_dir / "train", best_path, runner_mode, train_limit, backend=backend, model=worker_model, thinking_level=worker_thinking)
    val_summary = evaluate_cases(role, val, run_dir / "val", best_path, runner_mode, val_limit, backend=backend, model=worker_model, thinking_level=worker_thinking)
    train_comparison = comparison(train_summary, incumbent_train_summary)
    val_comparison = comparison(val_summary, incumbent_val_summary)
    patch = prompt_patch(role, best)
    (run_dir / "best_prompt.ts.patch").write_text(patch, encoding="utf-8")
    manifest = {
        "mode": "dspy-gepa",
        "role": role,
        "reflection_model": reflection_model,
        "runner_mode": runner_mode,
        "backend": backend,
        "worker_model": worker_model,
        "worker_thinking": worker_thinking,
        "reflection_thinking": reflection_thinking,
        "budget": budget,
        "max_metric_calls": max_metric_calls,
        "best_prompt": str(best_path),
        "train_cases": len(train_cases),
        "val_cases": len(val_cases),
        "incumbent_train": incumbent_train_summary,
        "incumbent_val": incumbent_val_summary,
        "train": train_summary,
        "val": val_summary,
        "train_comparison": train_comparison,
        "val_comparison": val_comparison,
        "val_gate": val_gate_decision(val_comparison),
        "changed_prompt": best != seed_prompt,
    }
    (run_dir / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "report.md").write_text(
        f"# OM GEPA {role} optimization\n\n"
        f"- mode: DSPy GEPA\n"
        f"- reflection_model: {reflection_model}\n"
        f"- reflection_thinking: {reflection_thinking}\n"
        f"- runner_mode: {runner_mode}\n"
        f"- backend: {backend}\n"
        f"- worker_model: {worker_model or '(runner default)'}\n"
        f"- worker_thinking: {worker_thinking or '(runner default)'}\n"
        f"- max_metric_calls: {max_metric_calls}\n"
        + format_comparison("train", train_comparison)
        + format_comparison("val", val_comparison)
        + f"- val gate: {manifest['val_gate']['reason']}\n"
        + f"- changed_prompt: {best != seed_prompt}\n"
        f"- best prompt: `candidates/best_prompt.txt`\n"
        f"- prompt patch: `best_prompt.ts.patch`\n",
        encoding="utf-8",
    )
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Optimize observer/reflector prompts. Dropper is intentionally excluded.")
    parser.add_argument("--role", choices=["observer", "reflector"], required=True)
    parser.add_argument("--train", type=Path, required=True)
    parser.add_argument("--val", type=Path, required=True)
    parser.add_argument("--budget", choices=["light", "medium", "heavy"], default="light")
    parser.add_argument("--reflection-model", default=None, help="DSPy/LiteLLM model name for GEPA reflection. Use openai-codex/gpt-5.5 for Codex subscription reflection.")
    parser.add_argument("--reflection-thinking", default="xhigh", help="Thinking level for openai-codex reflection models, default xhigh.")
    parser.add_argument("--runner-mode", choices=["gold", "empty", "live"], default="live", help="How candidate prompts are evaluated by the TS worker runner during GEPA and held-out validation.")
    parser.add_argument("--backend", choices=["openai-compatible", "pi-codex"], default="openai-compatible", help="Worker backend. Use pi-codex for OpenAI Codex subscription OAuth.")
    parser.add_argument("--worker-model", default=None, help="Worker model spec, e.g. openai-codex/gpt-5.4-mini.")
    parser.add_argument("--worker-thinking", default=None, help="Worker thinking level, e.g. low.")
    parser.add_argument("--max-metric-calls", type=int, default=None, help="Override the budget preset for tiny smoke runs or larger experiments.")
    parser.add_argument("--candidate-prompt", type=Path, default=None, help="Prompt file to evaluate/promote as the candidate seed.")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--train-limit", type=int, default=None, help="Cap train cases (applies after build_cases hash-split). Overrides --limit for train.")
    parser.add_argument("--val-limit", type=int, default=None, help="Cap val cases (applies after build_cases hash-split). Overrides --limit for val.")
    parser.add_argument("--limit", type=int, default=None, help="Back-compat alias: caps both train and val. Overridden by --train-limit/--val-limit when set.")
    parser.add_argument("--dry-run", action="store_true", help="Exercise case replay, metrics, and artifacts without requiring DSPy GEPA or live LLM credentials.")
    args = parser.parse_args()
    train_limit = args.train_limit if args.train_limit is not None else args.limit
    val_limit = args.val_limit if args.val_limit is not None else args.limit
    run_dir = make_run_dir(args.role, args.run_name)
    if args.dry_run:
        manifest = dry_run(args.role, args.train, args.val, run_dir, args.candidate_prompt, train_limit, val_limit)
    else:
        if not args.reflection_model:
            raise SystemExit("--reflection-model is required for DSPy GEPA optimization; use --dry-run for local smoke validation.")
        manifest = gepa_optimize(
            args.role,
            args.train,
            args.val,
            run_dir,
            args.budget,
            args.reflection_model,
            train_limit,
            val_limit,
            args.runner_mode,
            args.max_metric_calls,
            args.candidate_prompt,
            args.backend,
            args.worker_model,
            args.worker_thinking,
            args.reflection_thinking,
        )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

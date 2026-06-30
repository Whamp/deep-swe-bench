---
name: benchmark-launch
description: Use before launching harness/run_batch.py for a benchmark, especially when configs use advisor, observational-memory workers, subagents, local-vllm shims, or any model beyond the main executor; use before claiming a benchmark launch is working.
---

# Benchmark Launch

A launch that uses more than the main executor model must stop for user confirmation.

## Process

1. **Resolve the launch.**
   - Write the exact `harness/run_batch.py` command.
   - List the copied config leaf files: `models.json`, `settings.json`, `advisor.json`, and `pi-flags`.
   - State the resolved result path.
   - Completion: command, config files, and result path are concrete.

2. **Make the role table.**
   - Include every LLM role: main executor, advisor worker, observational-memory observer/reflector/dropper workers, subagents, local-vLLM shims, and any other worker model.
   - For each role list provider, model id, thinking level, and credential path.
   - Ask if any worker model, provider, count, or thinking level is ambiguous.
   - Completion: every LLM call path is named.

3. **Preflight credentials.**
   - Check credentials are available to the agent container path, not just the host shell.
   - For OpenAI Codex models, require Codex OAuth and `--pass-openai-codex-oauth`.
   - For GLM models, prefer direct ZAI through `ZAI_API_KEY`.
   - Never default to OpenRouter unless the user explicitly permits it; the standing exception is `openrouter/deepseek/deepseek-v4-flash`.
   - Completion: no role has an assumed or missing credential.

4. **Prove thinking semantics.**
   - `pi --list-models` or accepted `--thinking` flags are not enough.
   - Reconcile the requested level with provider docs, Pi request shape, and live/provider response evidence.
   - Use the model notes when relevant:
     - `docs/openai-codex-thinking.md`
     - `docs/zai-glm52-thinking.md`
     - `docs/zai-glm51-thinking.md`
     - `docs/zai-glm5v-turbo.md`
   - Completion: every requested thinking level is a real provider condition or an explicitly documented Pi mapping.

5. **Plan host resource protection.**
   - For long or high-concurrency batches, decide whether to run `scripts/container_memory_watchdog.py`.
   - Default conservative policy is a sustained 12 GiB cap on `dsw-*` containers: `--cap-gb 12 --interval 5 --consecutive 3 --grace 10`.
   - The watchdog kills only the largest non-protected child process; if `pi` is the largest process, it logs alert-only.
   - It writes separate logs under `runs/container-memory-watchdog/` and must not mutate official `result.json` artifacts.
   - Completion: launch plan says either watchdog is already running, will be started after confirmation, or is intentionally skipped.

6. **Ask before launching.**
   - Show the command, role table, leaf files, result path, credential preflight, thinking evidence, and watchdog decision.
   - Do not start until the user explicitly confirms.
   - Completion: user confirmation is present in the current conversation.

7. **Verify before claiming it works.**
   - “Working” means the relevant smoke gate passed and left evidence in the result tree.
   - Check the master log for fan-out after smoke, inspect required `smoke.json` artifacts, and verify tracker/result counts in the same turn.
   - If the watchdog is part of the launch plan, verify its pidfile/log in the same turn.
   - Do not claim success because a process is alive, a cell exited `ok`, or source code looks correct.
   - Avoid broad `pgrep` patterns that match the shell command doing the check.
   - Completion: smoke evidence, fan-out evidence, counts, and any watchdog evidence all agree.

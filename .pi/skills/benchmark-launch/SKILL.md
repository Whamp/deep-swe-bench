---
name: benchmark-launch
description: Use before preparing or executing a confirmed deep-swe-bench launch, especially when configs use advisor, observational-memory workers, subagents, local-vLLM shims, or any model beyond the main executor; use before claiming a launch is working.
---

# Benchmark Launch

Canonical benchmark results require a compiled launch plan and explicit approval
of that exact plan identity. Repeating raw model/config/task arguments is not
confirmation and must not execute canonical reps. This gate applies in full to
launches with advisor, observational-memory workers, subagents, local-vLLM
shims, or any other secondary model — they get no separate or weaker path.

## Process

1. **Prepare the model-free plan.**
   - Use `python -m harness.run_batch plan`, never raw batch execution arguments.
   - Supply the exact subject, model, thinking, versioned config identities,
     baseline identity, task selector, reps, workers, stable run id, preflight
     and result policies, cell retry limit, agent timeout, RPC quiescence,
     initial-context capture policy, central `--state-root`, `--plan-out`, and
     `--receipt-out`. For an early coding-agent behavioral gate, select the
     named `coding-agent-early-gate-v1` degeneration watchdog profile; leave it
     disabled for ordinary comparisons unless the operator requests it.
   - Keep the result root in the originating workspace when intended; point the
     state root at the configured central dashboard location.
   - Planning may inspect committed files, local subject versions, credential
     route availability, and already-present image identities. It must not start
     a subject, pull/run a container, make a model call, or write a canonical
     result cell.
   - Completion: the canonical plan and receipt exist and the plan command made
     no subject call.

2. **Resolve clarification before approval.**
   - `Launch clarification required:` means launch-relevant extension behavior,
     model roles, model selection, usage accounting, or bounds are unresolved.
   - Investigate code, config, lock metadata, documentation, and harmless local
     probes first. Do not edit the config or make a benchmark model call.
   - For a broad investigation, propose an appropriate workflow and use it only
     after the user approves that scope. Keep workflows outside the harness.
   - Grill only decisions that remain unresolved after evidence gathering. Reach
     mutual understanding before changing the candidate, refreshing its lock,
     or compiling again.
   - Completion: every clarification item is resolved by evidence or an explicit
     operator decision; the harness remains non-interactive.

3. **Review warnings and exact behavior.**
   - Read the receipt from the top. Resolve every warning before approval.
   - Verify the config identities and lock identities, tested subject versions,
     required capabilities, exact behavior differences from the baseline, task
     selection, reps, concurrency, cell retry limit, agent timeout, RPC
     quiescence, degeneration-watchdog profile and rendered thresholds,
     initial-context capture, preflight cells, conditional batch cells, result
     root, central state path, and originating workspace.
   - Treat legacy config/result warnings as limitations, not modern provenance.
     Legacy evidence is reusable only through an explicit decision naming the
     exact earlier identity, recorded provenance, result identity, and rationale.
   - Completion: the receipt describes the intended run without relying on raw
     command arguments or operator memory.

4. **Review every model role and resource route.**
   - The receipt role table must include the executor and every advisor,
     observational-memory observer/reflector/dropper, recursive child, workflow
     worker, subagent, local-vLLM shim, or other LLM call path.
   - For each role verify role kind, fixed/inherited/bounded-dynamic selection,
     provider, model, thinking, credential route, billing category, compact usage
     source, calls per rep or finite bound, and max concurrency.
   - Billing categories are `subscription quota`, `paid API`, or `local compute`;
     do not invent token or dollar estimates.
   - Completion: no model call path, provider, credential, usage source, or bound
     is assumed or hidden.

5. **Verify credential and thinking evidence.**
   - Planning checks credential route names without reading secret values into
     the plan or receipt. Verify each route reaches the subject container, not
     merely the host shell.
   - OpenAI Codex roles require `OPENAI_CODEX_OAUTH`; GLM roles should prefer
     direct ZAI through `ZAI_API_KEY`. Never default to OpenRouter without
     explicit permission except the standing
     `openrouter/deepseek/deepseek-v4-flash` route.
   - Reconcile requested thinking with provider documentation, Pi/OMP request
     shape, and the applicable evidence note. `--list-models` or accepted flags
     alone are insufficient.
   - Completion: every role has an available declared credential route and a
     proven thinking condition.

6. **Review the atomic preflight and enforced resource policy.**
   - One confirmation covers the receipt's preflight cells and only the stated
     conditional fan-out. No second approval is requested after preflight.
   - Confirm each config's durable smoke contract covers generic subject health,
     native session evidence, compact usage evidence for every role, RPC
     transport, and config-owned structured assertions or stable machine markers.
   - Review the plan's subject/verifier memory limits, additional swap, host
     reserve, confirmed physical host memory, and admission arithmetic. These
     values are behavior-defining and require renewed approval when changed.
   - Verify the singleton `scripts/container_resource_supervisor.py` is active
     through the host user service manager. It must discover containers by the
     `deep-swe-bench.managed=true` label. Its logs stay outside official result
     artifacts.
   - A prior `resource-halt.json` blocks resume. Clear it only with
     `--clear-halt <state-path> --clearance-reason <reason>` after the pressure
     source is fixed; clearance archives the original halt.
   - Completion: preflight, conditional fan-out, cgroup limits, host admission,
     and supervisor liveness are explicit before any paid call.

7. **Ask for exact-plan confirmation.**
   - Present the receipt, plan file, receipt file, plan identity, role table,
     credentials, thinking evidence, preflight contract, paths, dashboard
     command/URL, resource policy, host admission, supervisor status, and any
     enabled degeneration-watchdog profile with every rendered threshold.
   - Ask the operator to approve the exact `sha256:...` plan identity. Do not
     execute until that approval appears in the current conversation.
   - Any changed behavior or plan identity requires a new receipt and renewed
     approval.
   - Completion: explicit approval names the current plan identity.

8. **Execute only the stored plan.**
   - Run:

     ```sh
     python -m harness.run_batch execute \
       --plan <reviewed-launch-plan.json> \
       --confirm 'sha256:<exact-reviewed-plan-identity>'
     ```

   - Do not repeat subject/model/config/task arguments or add raw credential and
     execution flags on execution.
   - The executor must use the plan's worker count, retry limit, timeout, RPC,
     capture, and credential-route controls. It rechecks confirmed inputs before
     every new or retried rep. Already-active reps may finish after drift; no
     pending rep may start.
   - Resume with the same plan file and confirmation identity. Compatible reps
     remain read-only; result-provenance mismatch or launch-input drift requires
     operator action rather than overwrite.
   - Completion: execution consumes the reviewed plan and central registration
     exists before the first subject call.

9. **Verify before claiming it works.**
   - “Working” means every required preflight assertion passed and left evidence,
     then the approved fan-out began (when batch cells remain).
   - Inspect `launch-plan.json`, `manifest.json`, `status.json`, `events.ndjson`,
     preflight diagnostics, result provenance, native sessions, role usage
     evidence, transport logs, result counts, and dashboard projection in the
     same turn. Verify hard Docker limits and labels on active subject and
     verifier containers, plus supervisor process and event-log evidence. When
     the watchdog fires, require a compact `degeneration_watchdog` runner event,
     `agent_exit="degeneration"`, `agent_degeneration_watchdog` evidence, and a
     skipped verifier; treat that cell as a behavioral failure, not infrastructure
     timeout.
   - Process liveness, heartbeat, a subject exit of zero, or source inspection is
     not correctness evidence.
   - Completion: plan, state, smoke evidence, provenance, fan-out, counts, and
     dashboard all agree.

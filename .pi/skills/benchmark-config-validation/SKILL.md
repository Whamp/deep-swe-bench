---
name: benchmark-config-validation
description: Use before adding or changing a deep-swe-bench config release, model leaf, provider/model API path, config lock, role declaration, usage parser, smoke contract, or extension/subagent worker usage accounting.
---

# Benchmark Config Validation

A config release is not ready for confirmed planning until its identity, lock,
roles, compatibility, and durable preflight evidence are reviewable. Never invent
or alter config-authored prompt text without approval of the exact wording.

## Process

1. **Name the release and impact.**
   - New maintained releases use `<behavior-name>@<major>.<minor>.<patch>`.
     Keep the behavior name stable across releases; reject vague lineage suffixes
     such as `-v2`, `-new`, or `-latest`.
   - Choose explicit version impact: `reuse`, `recompute`, or `rerun`. The field
     is descriptive and must not copy, migrate, regrade, recompute, or rerun old
     artifacts automatically.
   - Existing unversioned configs remain readable legacy evidence, but they lack
     modern lock provenance. Never fabricate a lock for historical results.
   - Completion: identity and impact are explicit and use canonical vocabulary.

2. **Validate provider and thinking paths.**
   - Before using a new provider/model/API path, create or update
     `docs/<model>-thinking.md` with official documentation URLs, endpoint/API
     family, thinking/reasoning/tool-streaming/token-limit fields, Pi/custom-model
     metadata, request-shape probe, live/provider-response probe, usage shape,
     config rules, stale patterns to avoid, and `analysis/` artifact paths.
   - A model note and harmless request-shape probe may precede config changes;
     any paid/live provider probe still requires explicit approval.
   - Completion: every requested thinking level and provider path has current
     evidence, not merely an accepted CLI flag.

3. **Declare every model role.**
   - Lock metadata must cover the executor plus every advisor, observational-
     memory observer/reflector/dropper, recursive child, workflow worker,
     subagent, local-vLLM shim, and any other LLM call path.
   - Each role declares role kind, fixed/inherited/bounded-dynamic model
     selection, provider, model, thinking, credential route, billing category,
     compact usage source, and fixed or finite calls/concurrency bounds.
   - Declare every extension/config launch surface and the roles it can reach.
     Arbitrary model selection, unbounded calls, undeclared roles, or unknown
     extension behavior must stop planning with `Launch clarification required:`.
   - Completion: the config can render a complete role table without extension-
     specific compiler conditionals.

4. **Account for compact usage at the real worker boundary.**
   - Main executor usage comes from native `session/*.jsonl` assistant
     `message.usage` records. Never persist raw `--mode json` streams.
   - Advisor usage comes only from filtered `tool_execution_end` events in
     `tool-usage.jsonl`.
   - Observational-memory worker usage comes from
     `pi-agent/observational-memory/worker-usage/usage.ndjson` when
     `extensions/om-worker-usage-trace.ts` is loaded. OM debug `tokens` are
     context coverage, not billed usage.
   - Config-level Pi hooks may not see extension-internal `agentLoop` calls.
     Recursive/subagent configs must prove child sessions have intended tools and
     no structural tool failures; extension registration alone is insufficient.
   - Completion: every declared role has one compact usage source copied into the
     result cell and represented in `result.json` accounting.

5. **Declare subject compatibility and credentials.**
   - Lock metadata lists tested exact subject versions, required capabilities,
     credential route names, usage sources, roles, and launch surfaces.
   - A new untested Pi/OMP version requires investigation and evidence; capability
     names do not substitute for tested-version compatibility.
   - Credential declarations name routes such as `OPENAI_CODEX_OAUTH` or
     `ZAI_API_KEY`, never secret values. Planning checks route availability and
     keeps values out of lock, plan, receipt, result, status, and events.
   - Completion: confirmed planning can prove subject compatibility and route
     availability before approval.

6. **Write durable smoke contracts in config space.**
   - Put feature assertions in
     `configs/<identity>/smoke.json` or the authoritative leaf-local
     `configs/<identity>/<model-leaf>/<thinking>/smoke.json`; leaf-local wins.
   - Use structured result fields/counters, required files, compact structured
     usage records, and explicitly extension-owned stable machine markers.
   - Do not gate launches on README/documentation/source prose, source formatting,
     line breaks, character counts, or other human wording. Versioned planning
     rejects those brittle assertions before a model call.
   - Contract paths are relative to the copied result cell. For nested workers,
     require the actual copied audit/usage artifact and forbid known structural
     failures such as missing `rg`/`fd`, missing command tools, or
     `Max calls exceeded` where applicable.
   - Keep generic subject health in the harness: subject exit zero, no timeout,
     nonzero usage, native session evidence, and RPC transport lifecycle.
   - Completion: one preflight can prove every declared role and config-owned
     behavior with durable evidence.

7. **Create or refresh the lock only as maintenance.**
   - After reviewed behavior and metadata are ready, create the leaf lock with:

     ```sh
     python -m harness.config_lock create \
       --repository . \
       --config '<name>@<version>' \
       --model '<provider/model>' \
       --thinking '<thinking>' \
       --version-impact {reuse,recompute,rerun} \
       --metadata <release-metadata.json>
     ```

   - `refresh` is allowed only for an editable draft after investigation and
     renewed agreement. Planning and execution verify locks read-only and never
     create, refresh, or rewrite them.
   - A successful preflight seals the leaf and shared release behavior. A later
     leaf may join only when shared fingerprints remain unchanged.
   - Completion: `python -m harness.config_lock verify ...` matches exactly and
     secret values are excluded.

8. **Resolve clarification before editing.**
   - On `Launch clarification required:`, inspect extension source, config,
     package metadata, docs, worker paths, and harmless local probes first.
   - For broad independent fact gathering, propose a workflow and use it only
     with user approval. The harness never invokes workflows or grilling.
   - Grill only unresolved decisions after investigation. Do not edit config
     behavior, refresh a lock, or make a benchmark model call until mutual
     understanding is reached.
   - Completion: evidence and operator decisions fully determine the candidate.

9. **Prepare and inspect a confirmed preflight.**
   - Use `python -m harness.run_batch plan` with `new-configs` or `required`
     preflight policy. Review the receipt's config identity/lock, roles, routes,
     usage sources, tested subject versions, capabilities, preflight cell, paths,
     warnings, and conditional fan-out.
   - Stop for explicit approval of the exact plan identity. One approval covers
     paid preflight and only the receipt's conditional fan-out.
   - A config is working only when the atomic preflight passes and the result
     tree contains matching native session, usage, transport, config assertions,
     modern provenance, and structured diagnostics/state.
   - Completion: all evidence agrees; a usage gap discovered after fan-out is data
     that was never collected.

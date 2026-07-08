# projected-om-delta-no-orchestration-gpt54mini-low

Experimental cache-safe projected observational memory config for GPT-5.5 low, with no config-authored orchestration prompt.

This config keeps the stock `pi-observational-memory` workers from `observational-memory-gpt54mini-low`:

- main executor: `openai-codex/gpt-5.5` at thinking `low`
- OM workers: `openai-codex/gpt-5.4-mini` at thinking `low`
- observer/reflector/dropper thresholds match `observational-memory-gpt54mini-low`

The extra extension is `extensions/om-delta-projection.ts`.
Prompt surface:

- no `system_preamble.md`
- no `orchestration.md`
- no config-authored `--append-system-prompt` text
- executor-visible prompt additions come only from the loaded extensions/tools


Unlike `projected-om-gpt54mini-low`, this config does **not** rewrite provider `instructions` or prepend a full folded memory summary to every request. Instead, it watches the OM ledger during the main agent `context` hook and, when new observations/reflections/drop records exist, appends a hidden `custom_message` with only the net-new memory delta.

Intended cache shape:

```text
Pi instructions/tools/project context
→ task
→ turn/tool history
→ <observational-memory-update> net-new obs/refls </observational-memory-update>
→ later turns
→ next net-new OM update
→ later turns
```

That makes memory executor-visible while preserving append-only prompt-cache behavior. Each published delta is persisted as `custom_message` type `om.delta_projection`; the source OM records remain normal `custom` ledger entries.

Projection audit rows are written to:

```text
pi-agent/observational-memory/projection/projection.ndjson
```

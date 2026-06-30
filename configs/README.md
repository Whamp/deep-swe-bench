# Configs

A **config** is one configuration of the pi agent under test: a system-prompt
addition plus the skills/extensions it loads. The harness
(`harness/run.py --config <name>`) loads the config and applies whatever files
it finds. Convention over configuration: only `orchestration.md` is required.

A config is split into **constant** files (shared across every model+thinking
variant of that config) and **model leaves** (the per-model-variant files):

```
configs/<config>/                       # constant files
  orchestration.md                      # appended to the system prompt (required)
  pi-flags, env, skills/, extensions/   # optional, config-wide
  <model-leaf>/<thinking>/              # model leaf — the immutable variant dir
    models.json, advisor.json, settings.json   # model-identity files (optional)
```

`<model-leaf>` is `lib.model_leaf(model)` (the last `/`-segment of the model id);
advisor configs use `<exec>+<advisor>` here (e.g. `deepseek-v4-flash+glm-5.2`).
The `results/` path uses the **executor-only** leaf (never `+advisor`), so a
resumed `run_batch` can recompute the path from `--model` alone.

## The immutable-leaf rule (why the split exists)

`model+thinking` is a first-class axis, separate from the config dir. The
model-identity files (`models.json`, `advisor.json`, model-bearing
`settings.json`) live in the **leaf**, not at config-root. This is deliberate:
mutating `models.json` in place (the old single-file layout) silently
invalidated prior runs and broke resume. With the leaf layout, changing the
model creates a new leaf and leaves existing reps untouched. Never edit a leaf
file in place — add a new `<model-leaf>/<thinking>/` instead.

## Recognized files

| File / dir          | Scope    | Effect                                                                                  |
|---------------------|----------|-----------------------------------------------------------------------------------------|
| `orchestration.md`  | constant | Appended to the system prompt via `--append-system-prompt`. Required.                   |
| `skills/`           | constant | Each subdir passed to pi via `--skill`. The baseline config passes none.                |
| `pi-flags`          | constant | Extra raw flags appended to the `pi` invocation (one argv per line).                    |
| `env`               | constant | `KEY=VALUE` lines exported into the agent container env.                               |
| `extensions/`       | constant | Vendored extension source loaded via `-e`.                                             |
| `models.json`       | leaf     | Copied to `/root/.pi/agent/models.json`; defines providers (e.g. local-vllm).           |
| `advisor.json`      | leaf     | Copied to `/root/.pi/agent/advisor.json`; advisor config only.                          |
| `settings.json`     | leaf     | Copied to `/root/.pi/agent/settings.json`. For `observational-memory` this carries the  |
|                     |          | WORKER model, so it is leaf-level (distinct worker per leaf).                           |
| `smoke.json`        | constant | Optional smoke contract for a new config. Config-root applies to all leaves; leaf-local |
|                     | or leaf  | `smoke.json` overrides it. See [Smoke tests and contracts](#smoke-tests-and-contracts). |

A leaf is **path-only** (no files) when its models are all built-in providers
(openrouter / openai-codex); `models.json` is only placed when `local-vllm` is
involved (executor or worker). See `scripts/materialize_configs.py` for the
provenance rules.

## Configs in this comparison

- `baseline/` — stock pi, no skills, no discovered extensions. The true control.
  Loads the local-vLLM preserve-thinking shim so local Qwen gets the same
  transport workaround as non-baseline configs.
- `baseline-wf/` — baseline plus the mini-swe-agent step-by-step workflow prompt
  (benchmark-specific guidance absent from a normal AGENTS.md).
- `advisor/` — stock executor plus the `pi-advisor` extension using `zai/glm-5.2`
  as advisor (leaf `deepseek-v4-flash+glm-5.2`).
- `observational-memory/` — stock executor plus the `pi-observational-memory`
  extension. Worker model is pinned per leaf (Qwen for the local/deepseek leaves,
  `gpt-5.4-mini` for the gpt-5.5 leaf). OM configs should also load
  `extensions/om-worker-usage-trace.ts`, which records compact final assistant
  usage for observer/reflector/dropper calls under
  `pi-agent/observational-memory/worker-usage/usage.ndjson`. The trace records
  token/cost metadata only; it must not persist streamed text deltas or repeated
  growing output.
- `ponytail-full/`, `ponytail-lite/`, `ponytail-ultra/` — ponytail skill loaded,
  level pinned to full/lite/ultra.
- `ponytail-extension/` — ponytail loaded as a pi extension rather than a skill.

`skills/ponytail/` is a verbatim copy of the ponytail SKILL.md from
https://github.com/DietrichGebert/ponytail so the comparison is self-contained.
Extension configs vendor their extension source under `extensions/`. If an extension
is consumed as an npm package rather than vendored source, commit its
`package.json`/`package-lock.json`, keep `node_modules/` ignored, and document the
required `npm ci` step in the config README.

## Adding a config + model leaf

```sh
mkdir -p configs/<name>
$EDITOR configs/<name>/orchestration.md                       # required
# add a model leaf when you first run it on a given model+thinking:
mkdir -p configs/<name>/<model-leaf>/<thinking>
# optional leaf files: models.json, advisor.json, settings.json, smoke.json
```

`harness/run.py --config <name> --model <m> --thinking <t> --task <id>` picks it
up. No harness changes.

## Smoke tests and contracts

`harness/run_batch.py` has an automatic smoke gate for configs that have no
existing results for the selected executor model + thinking leaf. Before it fans
out a full batch, it runs one `rep0` cell on a task from `subsets/12_v0.txt`.
Using `12_v0` makes the smoke result reusable data instead of a throwaway cell.

The default smoke check is deliberately generic. It only verifies that the
harness produced a normal cell:

- `result.json` exists
- `agent_exit == 0`
- the agent did not time out
- token usage is non-zero
- native `session/*.jsonl` exists

Do **not** add feature-specific checks directly to `run_batch.py`. Future configs
may use new skills, extensions, subagents, worker models, or other behavior that
the harness cannot know about. Instead, a config can define its own success
signals in `smoke.json` at either:

```text
configs/<config>/smoke.json                         # all model leaves
configs/<config>/<model-leaf>/<thinking>/smoke.json # one leaf; overrides root
```

Supported contract keys:

Contract paths are evaluated relative to the result cell directory, after
`harness/run.py` has copied artifacts out of the container. Do not write a
contract for a live in-container path unless `run.py` also preserves it. Current
OM artifacts are copied from `/root/.pi/agent/observational-memory` to
`pi-agent/observational-memory`; an audit written elsewhere under
`/root/.pi/agent` will not satisfy smoke checks.

```json
{
  "minResultValues": { "advisor_calls": 1 },
  "equalsResultValues": { "agent_exit": 0 },
  "requireFiles": ["pi-agent/observational-memory/debug/*.ndjson"],
  "requireText": [
    {
      "globs": ["session/*.jsonl", "pi-agent/observational-memory/debug/*.ndjson"],
      "text": "om.observations.recorded"
    }
  ],
  "forbidText": [
    {
      "globs": ["session/*.jsonl", "pi-agent/observational-memory/debug/*.ndjson"],
      "text": "model_unavailable"
    }
  ]
}
```

The example above is intentionally config-specific: it says that an
advisor+observational-memory config is not healthy unless the advisor is called
and OM records observations. OM configs that rely on worker-token accounting
should also require `pi-agent/observational-memory/worker-usage/usage.ndjson`
and text `assistant_usage` in that file. A future skill or extension should
write a contract for its own expected artifacts instead of reusing this one.

If the contract proves provider request behavior for an extension worker, verify
where that worker request is actually made. `pi-observational-memory` invokes
observer/reflector/dropper LLM calls via direct `agentLoop` calls, so ordinary
config-level request hooks may not see them. Put required mutation/audit logic in
the nested worker path itself (or otherwise prove the hook fires there), then
require the copied audit artifact in `smoke.json`.

You can bypass the automatic gate with `--no-smoke-new-configs`, but only do that
when you have separate evidence that the config already works.

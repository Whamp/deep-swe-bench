# Configs

A **config** is one configuration of the pi agent under test: a system-prompt
treatment plus the skills/extensions it loads. The harness
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

A leaf is **path-only** (no files) when its models are all built-in providers
(openrouter / openai-codex); `models.json` is only placed when `local-vllm` is
involved (executor or worker). See `scripts/materialize_configs.py` for the
provenance rules.

## Configs in this comparison

- `baseline/` — stock pi, no skills, no discovered extensions. The true control.
  Loads the local-vLLM preserve-thinking shim so local Qwen gets the same
  transport workaround as treatment configs.
- `baseline-wf/` — baseline plus the mini-swe-agent step-by-step workflow prompt
  (benchmark-specific guidance absent from a normal AGENTS.md).
- `advisor/` — stock executor plus the `pi-advisor` extension using `zai/glm-5.2`
  as advisor (leaf `deepseek-v4-flash+glm-5.2`).
- `observational-memory/` — stock executor plus the `pi-observational-memory`
  extension. Worker model is pinned per leaf (Qwen for the local/deepseek leaves,
  `gpt-5.4-mini` for the gpt-5.5 leaf).
- `ponytail-full/`, `ponytail-lite/`, `ponytail-ultra/` — ponytail skill loaded,
  level pinned to full/lite/ultra.
- `ponytail-extension/` — ponytail loaded as a pi extension rather than a skill.

`skills/ponytail/` is a verbatim copy of the ponytail SKILL.md from
https://github.com/DietrichGebert/ponytail so the comparison is self-contained.
Extension configs vendor their extension source under `extensions/`.

## Adding a config + model leaf

```sh
mkdir -p configs/<name>
$EDITOR configs/<name>/orchestration.md                       # required
# add a model leaf when you first run it on a given model+thinking:
mkdir -p configs/<name>/<model-leaf>/<thinking>
# optional leaf files: models.json, advisor.json, settings.json
```

`harness/run.py --config <name> --model <m> --thinking <t> --task <id>` picks it
up. No harness changes.

# Arms

An **arm** is one configuration of the pi agent under test. The harness
(`harness/run.py --arm <name>`) loads the arm directory and applies whatever
files it finds. Convention over configuration: only `orchestration.md` is
required.

## What an arm controls (and nothing else)

The model, the task, the timeout, the container image, and the verifier are all
held constant by the harness. An arm only changes what is injected into pi's
system prompt and which skills/extensions load. That is the single variable a
study compares.

## Recognized files

| File / dir          | Effect                                                                                  |
|---------------------|-----------------------------------------------------------------------------------------|
| `orchestration.md`  | Appended to the system prompt via `--append-system-prompt`. Required.                   |
| `skills/`           | Each subdir passed to pi via `--skill` (one per entry). The baseline arm passes none.   |
| `pi-flags`          | Extra raw flags appended to the `pi` invocation (one argv per line). Optional.          |
| `env`               | `KEY=VALUE` lines exported into the agent container env (e.g. `PONYTAIL_DEFAULT_MODE`). |
| `settings.json`     | Copied to `/root/.pi/agent/settings.json` before Pi starts and recorded in `result.json`. Optional. |
| `models.json`       | Copied to `/root/.pi/agent/models.json` before Pi starts and recorded in `result.json`. Optional.   |
| `advisor.json`      | Copied to `/root/.pi/agent/advisor.json` before Pi starts and recorded in `result.json`. Optional.  |

## Arms in this study

- `baseline/` — stock pi, no skills, no discovered extensions. The fair "no
  ponytail" control. It explicitly loads only the local-vLLM preserve-thinking
  shim so local Qwen gets the same transport workaround as treatment arms;
  `--no-skills --no-extensions` still blocks operator-global discovery.
- `ponytail-full/` — ponytail skill loaded, level pinned to **full** (the
  documented default). This is the primary comparison.
- `ponytail-lite/` — ponytail skill loaded, level pinned to **lite**.
- `ponytail-ultra/` — ponytail skill loaded, level pinned to **ultra**.
- `pi-advisor-glm52/` — stock executor plus the `pi-advisor` extension using
  `zai/glm-5.2` as advisor via `ZAI_API_KEY`, with Pi retry settings enabled for
  transient Z.AI 429s. It intentionally does not route GLM-5.2 through OpenRouter.
- `pi-observational-memory/` — stock executor plus the symmetric local-vLLM
  preserve-thinking shim and the `pi-observational-memory` extension. Memory
  workers are pinned to the configured local Qwen model and debug/state persists
  under each cell's `pi-agent/`.

`skills/ponytail/` is a verbatim copy of the ponytail SKILL.md from
https://github.com/DietrichGebert/ponytail so the study is self-contained and
reproducible without depending on the operator's checked-out copy. Extension
arms vendor their extension source under `extensions/` for the same reason.

## Adding an arm

```sh
mkdir arms/<name>
$EDITOR arms/<name>/orchestration.md      # required, even if just "no extra guidance"
# optional: skills/<name>/SKILL.md, pi-flags, env, settings.json, models.json
```

`harness/run.py --arm <name> --task <id>` picks it up. No harness changes.

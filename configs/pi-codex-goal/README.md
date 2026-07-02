# pi-codex-goal

Config for running DeepSWE cells with the `pi-codex-goal` Pi package.

## Behavior

The config loads two explicit extensions:

1. `/arm/extensions/node_modules/pi-codex-goal` — the package manifest registers the goal tools and `prompts/create-goal.md` prompt template.
2. `/arm/extensions/initial-create-goal.ts` — wraps the first benchmark task prompt as `/create-goal <task>`, so the package prompt creates a durable completion goal before work starts.

The orchestration text stays neutral. The package controls continuation and completion auditing.

## Local setup

Install the config-local package dependencies before launching on a fresh checkout:

```sh
cd configs/pi-codex-goal/extensions
npm ci
```

`node_modules/` is ignored. The harness mounts this config read-only at `/arm`, so the container loads `pi-codex-goal` from `/arm/extensions/node_modules/pi-codex-goal`.

## Launch notes

Use OpenAI Codex OAuth for the executor and pass it into the container:

```sh
python harness/run_batch.py \
  --configs pi-codex-goal \
  --model openai-codex/gpt-5.5 \
  --thinking low \
  --agent-timeout 5400 \
  --pass-openai-codex-oauth
```

Keep `--agent-timeout 5400` as a launch-time override. It gives each cell 90 minutes, roughly double the longest observed GPT-5.5:xhigh task median in the existing result set.

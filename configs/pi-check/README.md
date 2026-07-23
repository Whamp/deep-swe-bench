# pi-check

Config for running DeepSWE reps with the `pi-check` Pi extension on
`openai-codex/gpt-5.5` at thinking `low`.

## Behavior

The config explicitly loads the vendored extension and passes its headless
`--check` flag. After the benchmark task's first agent run, `pi-check` queues one
ordinary follow-up in the same session. The follow-up asks the same executor
model to re-audit the task with fresh evidence, fix failures or uncertainty, and
rerun relevant checks.

`pi-check` does not add a second model or an LLM-callable tool. All usage remains
main-executor usage recorded in Pi's native `session/*.jsonl` messages.

The config adds no `system_preamble.md` or `orchestration.md`; the only extra
prompt text is the extension-owned verification follow-up.

## Vendored source

The package files under `extensions/pi-check/` are copied from:

- repository: <https://github.com/Whamp/pi-check>
- commit: `169bad23ca814a446637c4b64a777d09e8729ef7`
- package version: `0.1.0`

The extension has no runtime npm dependencies, so no install step is required.

## Launch shape

```sh
python3 harness/run_batch.py \
  --configs baseline pi-check \
  --model openai-codex/gpt-5.5 \
  --thinking low \
  --subset 12_v0 \
  --runs 3 \
  --run-id pi-check-gpt55-low-12v0-r3 \
  --progress-interval 10 \
  --pass-openai-codex-oauth
```

The first launch automatically runs the config's one-rep preflight before
fan-out.

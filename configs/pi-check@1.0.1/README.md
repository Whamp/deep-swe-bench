# pi-check@1.0.1

Pi Check config for `openai-codex/gpt-5.6-sol` at thinking `low` and
`openai-codex/gpt-5.6-luna` at thinking `low`, `high`, and `max`.

## Behavior

The config loads the vendored `pi-check` extension and passes its headless
`--check` flag. After the benchmark task's first agent run, the extension queues
one ordinary follow-up in the same session. The follow-up asks the same executor
model to re-audit the task with fresh evidence, fix failures or uncertainty, and
rerun relevant checks.

`pi-check` does not add another model or an LLM-callable tool. Pi records all
usage as main-executor usage in native `session/*.jsonl` messages.

The config adds no `system_preamble.md` or `orchestration.md`. Its only extra
prompt text is the extension-owned verification follow-up.

## Vendored source

The package under `extensions/pi-check/` comes from:

- repository: <https://github.com/Whamp/pi-check>
- commit: `169bad23ca814a446637c4b64a777d09e8729ef7`
- package version: `0.1.0`

The extension has no runtime npm dependencies.

## Validation change from 1.0.0

This release keeps the executor behavior from `pi-check@1.0.0`. Its smoke
contract adds structured JSON checks for both captured provider requests and
the native session thinking-level record. A mismatched model or reasoning
effort cannot pass preflight by merely creating the expected files.

## Release identity

Each model/thinking leaf owns `config-lock.json`. The SOL leaf declares Pi
`0.81.1`; the Luna leaves declare Pi `0.83.0`. Every lock declares Codex OAuth
subscription billing, native session usage, and the Pi RPC and extension
capabilities required by this release.

Prepare canonical work through `python3 -m harness.run_batch plan`; execute only
the stored plan and its reviewed confirmation identity.

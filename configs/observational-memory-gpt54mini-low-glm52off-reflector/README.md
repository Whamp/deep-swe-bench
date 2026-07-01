# observational-memory-gpt54mini-low-glm52off-reflector

Split-stage observational-memory config for GPT-5.5-low executor experiments.

- Main executor: `openai-codex/gpt-5.5`, thinking `low` (selected by `harness/run_batch.py --model/--thinking`).
- Observer: `openai-codex/gpt-5.4-mini`, thinking `low`.
- Reflector: direct ZAI `glm-5.2`, thinking `off`.
- Dropper: unset, so it inherits the reflector model/thinking from the local fork's stage-resolution rules.
- Extension source: vendored from local path `~/projects/pi-observational-memory` after the per-stage model/thinking override change, then patched only to emit the benchmark worker-usage trace hook.
- Extension loading: the harness mounts this config at `/arm:ro` and runs Pi with `--no-extensions` plus explicit `-e /arm/extensions/...` flags. `pi install /absolute/path` can load local packages on the host, but benchmark containers cannot see host-local paths unless mounted, so vendoring under `configs/.../extensions/` is the reproducible path here.

Validation references:

- Codex thinking: `docs/openai-codex-thinking.md` and `analysis/openai-codex-thinking-*.jsonl`.
- ZAI GLM-5.2 thinking: `docs/zai-glm52-thinking.md` and `analysis/pi-zai-request-shape-probe.jsonl`.
- Stage override implementation: `extensions/pi-observational-memory/src/config.ts` and `extensions/pi-observational-memory/src/hooks/consolidation-trigger.ts`.

# OM GEPA prompt lab

This sidecar makes pi-observational-memory prompt work benchmarkable instead of manual prompt gardening. It covers **observer** and **reflector** only. **Dropper is intentionally excluded** until a forced-over-target dropper suite exists, because current benchmark sessions did not activate real drop decisions.

## Mutable vs locked files

Mutable prompt files for this sidecar:

- `configs/observational-memory/extensions/pi-observational-memory/src/agents/observer/prompts.ts`
- `configs/observational-memory/extensions/pi-observational-memory/src/agents/reflector/prompts.ts`

Locked for the first optimization pass:

- `agent.ts`
- `config.ts`
- `hooks/consolidation-trigger.ts`
- tool schemas
- ledger logic
- dropper logic

The TypeScript runners copy the extension source to a temporary directory and replace only the role prompt in that temp copy. The repository's vendored extension files are not modified during replay/evaluation.

## Layout

```text
analysis/om-gepa/
  build_cases.py          # wrapper for analysis.om_gepa.build_cases
  evaluate.py             # wrapper for analysis.om_gepa.evaluate
  optimize.py             # wrapper for analysis.om_gepa.optimize
  promote.py              # wrapper for analysis.om_gepa.promote
  runners/
    observer_replay.ts    # imports actual runObserver from temp extension copy
    reflector_replay.ts   # imports actual runReflector from temp extension copy
  metrics/
    observer.py           # wrapper metric import
    reflector.py          # wrapper metric import
  cases/                  # generated JSONL replay cases
  runs/                   # generated eval/optimization artifacts
```

Importable implementation code lives in `analysis/om_gepa/` because Python modules cannot contain hyphens.

## Build replay cases

```bash
python3 -m analysis.om_gepa.build_cases \
  --role observer \
  --from results/deepseek-v4-flash/high/observational-memory \
  --out analysis/om-gepa/cases \
  --limit 20

python3 -m analysis.om_gepa.build_cases \
  --role reflector \
  --from results/deepseek-v4-flash/high/observational-memory \
  --out analysis/om-gepa/cases \
  --limit 20
```

Outputs:

- `<role>_all.jsonl`
- `<role>_train.jsonl`
- `<role>_val.jsonl`
- `<role>_test.jsonl`

## Replay and evaluate

```bash
python3 -m analysis.om_gepa.evaluate \
  --role observer \
  --cases analysis/om-gepa/cases/observer_val.jsonl \
  --out analysis/om-gepa/runs/eval-observer-smoke \
  --mock-mode gold \
  --limit 3
```

Artifacts:

- `scores.csv`
- `candidate_outputs.jsonl`
- `changed_cases.html`
- `report.md`
- `best_prompt.ts.patch` when `--candidate-prompt` is supplied

`--mock-mode gold` exercises the actual worker contract happy path by calling the worker's real tool with historical gold records. `--mock-mode empty` exercises no-tool-call behavior. `--mock-mode live` calls an OpenAI-compatible model through the same worker contract; set `OM_GEPA_API_KEY` or `OPENAI_API_KEY`, optionally `OM_GEPA_BASE_URL`, and `OM_GEPA_MODEL`.

## Optimize

Dry-run the full artifact path:

```bash
python3 -m analysis.om_gepa.optimize \
  --role observer \
  --train analysis/om-gepa/cases/observer_train.jsonl \
  --val analysis/om-gepa/cases/observer_val.jsonl \
  --dry-run \
  --limit 3
```

Live candidate evolution uses **DSPy GEPA**. The DSPy program contains one optimizable predictor whose instruction text is the observer or reflector prompt. During each forward pass it records a lightweight trace-only predictor call, then evaluates the candidate by writing that prompt to a temporary file and running the real TypeScript worker runner. Scoring is still done by the deterministic Python metrics plus textual feedback.

Preferred no-paid-API setup for this project:

- worker model: `openai-codex/gpt-5.4-mini`, thinking `low`, through Pi's OpenAI Codex OAuth subscription;
- reflection model: `openai-codex/gpt-5.5`, thinking `xhigh`, through the same Codex OAuth path.

This uses `~/.pi/agent/auth.json`; no OpenRouter key is needed.

Install optional dependencies:

```bash
python3 -m pip install '.[om-gepa]'
# or: python3 -m pip install dspy gepa litellm
```

No-model-call smoke for the artifact path:

```bash
python3 -m analysis.om_gepa.optimize \
  --role observer \
  --train analysis/om-gepa/cases/observer_train.jsonl \
  --val analysis/om-gepa/cases/observer_all.jsonl \
  --dry-run \
  --limit 1
```

Codex-subscription smoke with your preferred models:

```bash
python3 -m analysis.om_gepa.optimize \
  --role observer \
  --train analysis/om-gepa/cases/observer_train.jsonl \
  --val analysis/om-gepa/cases/observer_all.jsonl \
  --reflection-model openai-codex/gpt-5.5 \
  --reflection-thinking xhigh \
  --runner-mode live \
  --backend pi-codex \
  --worker-model openai-codex/gpt-5.4-mini \
  --worker-thinking low \
  --max-metric-calls 2 \
  --limit 1 \
  --run-name smoke-observer-codex54mini-low-gepa55-xhigh
```

First real observer run, still modest:

```bash
python3 -m analysis.om_gepa.optimize \
  --role observer \
  --train analysis/om-gepa/cases/observer_train.jsonl \
  --val analysis/om-gepa/cases/observer_val.jsonl \
  --reflection-model openai-codex/gpt-5.5 \
  --reflection-thinking xhigh \
  --runner-mode live \
  --backend pi-codex \
  --worker-model openai-codex/gpt-5.4-mini \
  --worker-thinking low \
  --budget light \
  --run-name observer-codex54mini-low-gepa55-xhigh-v1
```

OpenAI-compatible local/ZAI backends are still supported via `--backend openai-compatible` plus `OM_GEPA_API_KEY`, `OM_GEPA_BASE_URL`, and `OM_GEPA_MODEL`; avoid OpenRouter here unless explicitly testing paid API behavior.

Optimization artifacts include `manifest.json`, `report.md`, `gepa_evaluations.jsonl`, `candidates/best_prompt.txt`, `best_prompt.ts.patch`, and held-out `train/` and `val/` evaluation packets.

## Promote only after gates pass

```bash
python3 -m analysis.om_gepa.promote \
  --role observer \
  --candidate-prompt analysis/om-gepa/runs/<run>/candidates/best_prompt.txt \
  --base-config configs/observational-memory \
  --new-config configs/observational-memory-gepa-observer-v1 \
  --dry-run
```

Remove `--dry-run` only after held-out validation and manual review pass. Promotion refuses to overwrite an existing config and checks that only the selected prompt plus README/promotion patch changed.

## Metrics

Observer metrics:

- schema validity
- timestamp validity
- valid `sourceEntryIds`
- no invented source IDs
- content similarity to historical gold observations
- duplicate/redundant observation penalties
- relevance validity

Reflector metrics:

- valid `supportingObservationIds`
- one-line reflection content
- content similarity to historical gold reflections
- duplicate penalties
- support density/shape
- correct empty/no-tool-call smoke behavior via `--mock-mode empty`

## Completion gate for prompt candidates

A candidate is not accepted because GEPA liked it. It must produce fresh evidence:

1. deterministic schema/source/support checks pass;
2. held-out score improves over incumbent;
3. no source/support ID regression;
4. `changed_cases.html` or equivalent review packet is inspected;
5. a small live DeepSWE slice passes before public claims or default-config replacement;
6. promotion creates a new config rather than overwriting `configs/observational-memory`.

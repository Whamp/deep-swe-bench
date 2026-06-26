# DeepSWE subsamples for fast iteration

Full DeepSWE runs cost ~113 cells per arm. A stratified subsample trades a
little signal for ~3× faster, ~3× cheaper iterations, so A/B diagnostics
(advisor vs control, OM vs no-OM, provider-routing reruns) can be run quickly
before committing to a full 113-cell run.

## `fast-iter-v1` — 36 tasks (~32% of 113)

File: [`fast-iter-v1.txt`](fast-iter-v1.txt)

### Difficulty axis

Tasks are bucketed by DeepSWE's **cross-model pass rate** — the "Pass Rate (All
Model Efforts)" column aggregated across the full model matrix on
[datacurve.ai](https://deepswe.datacurve.ai). This is an **out-of-sample**
difficulty metric: no single tested model biases it, so it does not leak any
arm's results into the stratification. This mirrors the equal-count tercile
principle from Kun Chen / programbench-bench, adapted to DeepSWE which has no
auxiliary language arms, by using the cross-model aggregate instead.

Thresholds (natural terciles of the 113-task distribution):

| bucket  | cross-model pass | full suite | subsample |
|---------|------------------|-----------|-----------|
| hard    | < 33%            | 34        | 11        |
| medium  | 33–66%           | 45        | 14        |
| easy    | ≥ 66%            | 34        | 11        |

### Selection rules

1. **Always include all DeepSeek-v4-flash solves** (2/2: `actionlint-action-pinning-lint`, `wazero-multi-module-snapshots`) — preserves regression signal for the cheap iteration model.
2. **Language-balanced fill** via round-robin across TypeScript / Go / Python / Rust / JavaScript, proportional to the full suite (TS 35 / Go 34 / Py 34 / Rust 5 / JS 5).
3. **Diagnostic seed tasks** baked in — tasks we have repeatedly studied across prior runs (`adaptix-name-mapping-aliases`, `fastapi-implicit-head-options`, `mashumaro-flattened-dataclass-fields`, `kombu-single-active-consumer-priority`, `kgateway-consistent-hash-policy`, `gql-incremental-graphql-delivery`, `obsidian-linter-auto-table-of-contents`, `httpx-streaming-json-iteration`) so future reruns stay comparable to existing analysis.
4. **Deterministic seed (42)** for reproducibility.

Resulting language mix: TS 8, Go 11, Python 11, Rust 4, JS 2.

### What it is NOT

- Not a leaderboard score. Subsample numbers are diagnostic only; never report them as pass@1.
- Not powered for binary-solve claims (see limitation below).

## Primary signal: partial reward, not binary solves

**On this subsample, lean on mean `reward_partial` (continuous), not binary solve counts.**

DeepSWE's own methodology uses continuous partial reward rather than binarized
pass/fail. With n=36, binary solve counts are too sparse to carry solve-jump
headlines (e.g. the full-suite DeepSeek 2→10 OM jump compresses to 2→3 here —
see validation below). Partial reward preserves both the direction and
approximate magnitude of every treatment effect and is the statistically
robust metric at this sample size.

## Validation against completed full runs

Computed over the 36 subsample tasks vs the full 113, for every arm with a
complete 113-cell run:

| arm | full solved | sub solved | full mean_partial | sub mean_partial |
|-----|-------------|------------|-------------------|------------------|
| DeepSeek baseline       | 2/113  | 2/36  | 0.774 | 0.686 |
| Ponytail-full (DS)      | 4/113  | 1/36  | 0.709 | 0.646 |
| DeepSeek + OM           | 10/113 | 3/36  | 0.856 | 0.821 |
| DeepSeek + Advisor      | 5/113  | 1/36  | 0.536 | 0.553 |
| GPT-5.5 + OM            | 47/113 | 10/36 | 0.962 | 0.955 |

**Findings:**

- **Rankings preserved.** Every pairwise ordering on mean_partial is identical
  to the full suite. No conclusion inverts on the subsample.
- **Partial-reward deltas track or amplify.** DeepSeek→OM mean Δpartial is
  +0.082 full / **+0.135 sub** (amplified). The difficulty-bucket mechanism
  reads cleanly: OM gains +0.195 (hard) / +0.215 (medium) / −0.026 (easy) on
  the subsample, matching the full-suite "helps hard/medium, neutral on easy"
  story.
- **Cost story preserved.** Token and patch-byte medians track the full suite
  within a few percent.

### Known limitation: binary solve compression

Binary solve counts compress non-linearly on small n. Concretely:

- Full suite: DeepSeek 2 → OM 10 (**+8**)
- Subsample:  DeepSeek 2 → OM 3  (**+1**)

Only 1 of OM's 8 new solves (`fd-deterministic-multi-key-sorting`) landed in
the subsample. The other 7 cluster at the easy end (cross-model pass 80–92%),
which the stratification deliberately did not over-sample because (a) they are
low-information near-ceiling tasks and (b) forcing them in would bias the
subsample toward easy tasks. This is the fundamental problem of binary metrics
on small n, not a task-selection flaw.

**Decision:** accept binary compression and lean on partial reward as the
primary signal. This keeps the subsample representative rather than
over-fitting it to one arm's solve set. When a binary solve-jump headline
matters, run the full 113-cell suite.

## Usage

```bash
# any arm, restricted to the subsample
python harness/run_batch.py --arms baseline,pi-observational-memory \
  --subsample fast-iter-v1 --run-name om-diag --workers 4
```

`--subsample <name>` reads `harness/subsamples/<name>.txt` (one task id per
line). It is mutually exclusive with `--tasks` and composes with `--slice`.

## Designing a new subsample

The selection script lives inline in this repo's history (commit that added
`fast-iter-v1`). To regenerate or design a new one:

1. Source cross-model pass rates from datacurve.ai ("Pass Rate (All Model
   Efforts)"). Raw extract + parser: `data.txt` at repo root (cleaning: title
   line, then overall % on the next line, discard per-model % lines).
2. Map titles → task ids via `display_title` in each task's `task.toml`.
3. Bucket by the thresholds above (or equal-count terciles by rank).
4. Apply the four selection rules; fix the seed for reproducibility.
5. Validate against completed full runs (table above) before adopting.

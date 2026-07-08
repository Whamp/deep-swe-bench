# GPT-5.5 low workflow-checklist ablation: final report

## Executive summary

The original workflow checklist remains the best prompt-only scaffold in this test.

We ran three approved ablations of `baseline-wf-only` on DeepSWE subset `36_v2` with GPT-5.5 low, three reps, and 24 workers:

1. remove the explicit repro-script step;
2. remove the final commit step;
3. compress the six-step checklist into tighter wording.

None beat the original workflow checklist. The no-repro and no-commit variants still beat clean low, but both lost paired solves against the original workflow. The tight checklist was worse than clean low.

The result is clear: the gain is not just from adding an ordered list. The specific workflow language matters, especially the explicit reproduction/verification loop and the less-compressed task framing.

## Headline results

| Config | Solves | Δ vs clean low | Δ vs original workflow | Total cost | Any-success tasks | Stable 3/3 tasks |
|---|---:|---:|---:|---:|---:|---:|
| `baseline` | 28/108 | — | -7 | $102.19 | 14/36 | 6/36 |
| `baseline-wf-only` | 35/108 | +7 | — | $118.17 | 16/36 | 6/36 |
| `baseline-wf-no-repro-script` | 32/108 | +4 | -3 | $94.66 | 14/36 | 7/36 |
| `baseline-wf-no-commit` | 31/108 | +3 | -4 | $98.03 | 16/36 | 5/36 |
| `baseline-wf-tight-checklist` | 25/108 | -3 | -10 | $97.73 | 14/36 | 3/36 |

## Paired comparison against the original workflow

| Comparison | Original-only wins | Variant-only wins | Net variant delta | Cost delta | Task-bootstrap 95% CI |
|---|---:|---:|---:|---:|---:|
| No repro-script step | 7 | 4 | -3 | -$23.51 | -10 to +4 |
| No commit step | 12 | 8 | -4 | -$20.14 | -12 to +4 |
| Tight checklist | 15 | 5 | -10 | -$20.44 | -16 to -5 |

The no-repro and no-commit variants were cheaper, but they gave back solves. The tight checklist was the only ablation with a clearly negative task-bootstrap interval.

## Interpretation

### 1. Keep the original workflow checklist for solve rate

`baseline-wf-only` stayed at 35/108 solves, seven above clean low. It also beat each ablation on exact task/rep pairings.

This makes the original checklist the current prompt-only solve-rate leader in this family.

### 2. The repro-script instruction is probably useful, not dead weight

Removing the explicit repro-script step cut cost by $23.51 across the paired cells and reduced repro-signal commands from 6.31 per cell to 1.80 per cell. It still solved 32/108, four above clean low.

But it lost 7 cells that the original workflow solved and gained only 4. That pattern argues against deleting the repro step if the goal is maximum solve rate.

The right takeaway is narrower: a no-repro variant may belong on a cost frontier, but it is not a replacement for the original workflow prompt.

### 3. The commit step is not the main signal, but removing it did not help

Removing only the commit step produced 31/108 solves. It remained above clean low, but it lost 12 workflow-only cells and gained 8 no-commit-only cells.

The commit instruction probably is not the core source of the workflow gain. Still, deleting it changed the trajectory enough to lose net solves. If future prompts remove the commit step, they should preserve an explicit finalization/checkpoint instruction rather than simply ending earlier.

### 4. Compact wording hurt

The tight checklist kept the six-step shape but compressed the wording. It fell to 25/108 solves, three below clean low and ten below the original workflow.

This is the strongest result in the run. A terse ordered list is not enough. The model appears to benefit from the fuller, more concrete wording: analyze relevant files, create a reproduction script, edit source, rerun the script, test edge cases, and commit changes.

### 5. The ablations changed reliability, not just total solves

The original workflow had 16/36 any-success tasks and 6/36 stable 3/3 tasks.

The no-repro variant had fewer any-success tasks, 14/36, but one more stable task, 7/36. That means it sometimes made solved tasks more repeatable while losing reach on other tasks.

The tight checklist dropped to 3 stable tasks and lost ten paired solves against the original. That is not just noise in one or two reps; it is a broad reliability loss.

## Recommendation

Keep `baseline-wf-only` as the default prompt-only workflow scaffold.

If we run another ablation, do not shorten the whole checklist. Instead, test one precise hypothesis at a time:

- keep the explicit reproduction/verification loop;
- replace the commit step with a non-git finalization check;
- test a cheaper verification variant without deleting reproduction entirely.

Do not adopt `baseline-wf-tight-checklist`.

Treat `baseline-wf-no-repro-script` as a cost-frontier candidate only, not as the new solve-rate winner.

## Caveats

- Scope is limited to DeepSWE subset `36_v2`, three reps, GPT-5.5 low, and these exact prompt-only configs.
- Solve counts use `reward_binary == 1` only.
- The three ablations were run together under `gpt55-low-wf-ablation-36v2-r3-w24`. Clean low and `baseline-wf-only` are historical same-subset/same-model/same-thinking anchors, not same-run drift controls.
- Rep labels are paired by task and rep index, but they are not proven matched random seeds.
- The packet classifications are deterministic heuristics over verifier failures, patches, and session traces. The packet evidence should be treated as source material, not as a substitute for human review.

## Evidence

Primary artifacts:

- `reports/gpt55-low-wf-ablation-36v2/index.html`
- `analysis/gpt55-low-wf-ablation-36v2/full_analysis.json`
- `analysis/gpt55-low-wf-ablation-36v2/paired_summary.csv`
- `analysis/gpt55-low-wf-ablation-36v2/config_summary.csv`
- `analysis/gpt55-low-wf-ablation-36v2/task_k3_profiles.csv`
- `analysis/gpt55-low-wf-ablation-36v2/solve_flip_index.csv`
- `analysis/gpt55-low-wf-ablation-36v2/churn_packets/`

Validation:

- run status: completed;
- batch cells: 324/324 done;
- failures: 0;
- transients: 0;
- packet count: 51 solve-flip packets;
- `python3 -m pytest -q`: 203 passed;
- HTML report served at `http://100.112.72.93:8823/` with HTTP 200.

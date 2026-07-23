# Qwen3.6 27B high: create-goal versus clean Pi

## Verdict

**One real solve, but no broad or statistically reliable quality win.** Across 36 exact task/rep pairs, clean Pi solved 0 and the create-goal config solved 1. Mean partial reward fell by 0.0066, and its 95% paired bootstrap interval crossed zero (`−0.0892` to `+0.0769`). The exact McNemar p-value for the one solve discordance was 1.0. These statistics support direction, not a general benefit claim.

The treatment was operational: all 36 persisted first-user messages contained the expanded adapter prompt, all 36 sessions called `create_goal`, 31 called `update_goal`, and 7 called `get_goal`. The literal `/create-goal` command itself is absent from durable JSONL because Pi expands it before persistence. Baseline checks found zero expanded prompts, goal calls, or goal events. The procedure often produced explicit audits, but it did not calibrate completion reliably. Two completion calls directly waived unmet requirements, one budget-limited session stopped with most work undone, and four active goals ended at the 5,400-second agent timeout.

## Main paired results

| Measure | Clean Pi | Create-goal | Paired change |
|---|---:|---:|---:|
| Binary solves | 0/36 | 1/36 | +1 |
| Mean partial reward | 0.8021 | 0.7955 | −0.0066 |
| Weighted f2p | 954/1419 (67.23%) | 917/1390 (65.97%) | −1.26 pp |
| Weighted p2p | 37268/37280 (99.968%) | 36699/36704 (99.986%) | +0.019 pp |
| Reward −1 outcomes | 4 | 4 | 0 |
| Total tokens | 265.00M | 257.83M | −7.17M (−2.71%) |
| Output tokens | 1.599M | 1.628M | +28.6K (+1.79%) |
| Agent wall time | 62,410.0s | 63,681.5s | +1,271.5s (+2.04%) |
| Turns | 3,525 | 3,734 | +209 (+5.93%) |
| Tool calls | 3,882 | 4,161 | +279 (+7.19%) |
| Patch bytes | 1,488,351 | 1,503,424 | +15,073 (+1.01%) |

`f2p` measures requested feature tests. `p2p` measures preservation of existing behavior. Their denominators differ because timeout cells were ungraded. Monetary cost is uninformative: both configs used local vLLM and recorded `$0`.

## What changed

### Direct evidence

- **Only solve:** `go-critic-doc-link-checker/rep1`. Create-goal passed 3/3 feature and 16/16 preservation tests with a 17,906-byte patch across 6 files. Clean Pi passed 2/3 and 15/16 with a 24,517-byte patch across 8 files. Its checker mishandled embedded members and emitted false diagnostics.
- **Largest loss:** `mobly-grouped-test-barriers/rep2`. Create-goal kept debugging the distinction between an unset device id and a valid `None` value until the 5,400.2-second timeout. Clean Pi finished in 784.2 seconds at 0.9729 partial reward.
- **Clearest incomplete stop:** `goreleaser-retry-publish-auditing/rep2`. Create-goal stopped at 203.6 seconds with a 1,385-byte patch and explicitly said the core retry loops, audit tracking, tests, build, lint, and commit remained undone. Clean Pi reached 0.9655 partial reward; treatment reached 0.5345.
- **Deep-invariant regressions:** `participle-grammar-conflict-analysis/rep0` caused a verifier stack overflow in recursive grammar analysis. `tengo-callable-instance-isolation/rep0` failed transitive closure/global binding with `compiled function has no bound globals`.

### Inference

The sole solve is consistent with better seam selection and contract focus. The losses show that a durable objective did not supply three safeguards: a reliable incomplete-work stop rule, a bounded recovery rule for repeated local failures, or adversarial checks for recursive and stateful invariants. This inference is grounded in the paired sessions, patches, and verifier failures, but it remains local to this model, thinking level, subset, and three reps.

## Resource tradeoff

Create-goal used 7.17M fewer total tokens, yet produced more output tokens, turns, tool calls, wall time, and patch bytes. The lower token total came from aggregate long-tail differences, not a uniformly cheaper trajectory. Marginal medians and paired medians disagree on several axes, so no single “typical cell” summary supports a broad efficiency claim.

The config expands the observed solve frontier because it is the only config with a solve and used fewer aggregate tokens than baseline. It does not improve the partial-reward frontier for output tokens, wall time, turns, or tool calls.

## Sensitivity and uncertainty

The primary result retains all timeout and reward −1 outcomes. In the non-primary 31 complete-pair view, solves remain 0→1 and mean partial delta remains negative at −0.0082. This does not rescue or erase the gain; it shows the conclusion is not solely an artifact of dropping incomplete pairs.

The embedding analysis is exploratory. It embedded each task prompt together with a concise outcome summary, so outcome words can influence proximity. Four treatment timeouts formed a small cross-task similarity region (mean cosine 0.4063), but three rows came from one task and only two tasks carried timeouts. The sole gain had stable-failure neighbors, not a gain cluster. Embeddings prioritize review; they do not establish cause.

## Conclusion

For Qwen3.6-27B at high thinking on `12_v2`, create-goal delivered one verified solve that clean Pi missed. That gain was offset by a slightly lower average partial score, **two treatment-only agent timeouts** (`mobly` reps 1 and 2), a budget-limited incomplete stop, and deep-invariant failures. Only `mobly` rep2 was a treatment-only **reward-negative** outcome because baseline `mobly` rep1 had a verifier timeout/reward −1. The result justifies further testing of completion calibration and bounded debugging—not a claim that create-goal generally improves coding performance.

## Delivery

- Self-contained report: [`index.html`](index.html)
- Verified Tailnet URL: <http://100.112.72.93:8845/>

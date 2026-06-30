# Offline OM observer-quality screen

This report screens observer worker model/thinking settings on reconstructed observational-memory observer chunks. It isolates the observer task from downstream DeepSWE reward noise.

## Methodology

- Extracted one observer replay case for each task in `subsets/12_v0.txt` from historical DeepSeek observational-memory sessions.
- Replayed the observer task with the vendored observer system prompt, the same `record_observations` tool schema, source-entry validation, timestamp/relevance validation, and a 16-turn cap.
- Compared 10 completed candidate settings: deepseek-v4-flash-low, deepseek-v4-flash-off, glm51-high, glm51-off, glm52-high, glm52-low, glm52-off, glm52-xhigh, gpt-5.4-mini-low, gpt-5.5-low.
- Scored outputs mechanically against historical observations as a silver reference, then judged recall, faithfulness, specificity, salience, relevance calibration, hallucinations, and missed important facts with an LLM judge.
- Produced `HUMAN_REVIEW_PACKET.md` so a human can spot-check source chunks, silver observations, and every candidate output.

## Recommendation

Recommended setting: **deepseek-v4-flash-low**.

Selection rule: choose the lowest estimated-cost candidate within 95% of the best composite judge score, with average faithfulness >= 4 and hallucination count <= 0.25 per case. If no judge scores exist, use mechanical silver-reference overlap as a fallback.

## Aggregate scores

| candidate | composite | judge recall | faithfulness | hallucinations/case | silver recall >=0.35 | est cost/case | cases |
|---|---:|---:|---:|---:|---:|---:|---:|
| glm51-high | 4.812 | 5.00 | 5.00 | 0.00 | 0.657 | $0.04628 | 12 |
| glm52-off | 4.746 | 5.00 | 4.92 | 0.00 | 0.717 | $0.04329 | 12 |
| glm51-off | 4.742 | 5.00 | 4.92 | 0.00 | 0.594 | $0.04479 | 12 |
| deepseek-v4-flash-low | 4.708 | 4.75 | 5.00 | 0.00 | 0.689 | $0.00437 | 12 |
| glm52-xhigh | 4.708 | 5.00 | 4.83 | 0.00 | 0.639 | $0.04545 | 12 |
| glm52-low | 4.704 | 5.00 | 4.83 | 0.00 | 0.705 | $0.04439 | 12 |
| gpt-5.5-low | 4.654 | 4.83 | 4.92 | 0.00 | 0.647 | $0.26157 | 12 |
| deepseek-v4-flash-off | 4.579 | 4.67 | 4.83 | 0.00 | 0.669 | $0.00481 | 12 |
| gpt-5.4-mini-low | 4.575 | 4.58 | 5.00 | 0.00 | 0.416 | $0.03291 | 12 |
| glm52-high | 4.546 | 4.92 | 4.67 | 0.17 | 0.672 | $0.04315 | 12 |

## Artificial Analysis comparison

The provided Artificial Analysis key had free-tier API access, which did not expose Pro per-benchmark fields. As a point of comparison, the public AA-Omniscience page was scraped into `analysis/om-observer-screen/artificial_analysis_comparison.csv`. Coverage is partial because the public page exposes selected chart rows rather than a full API dump.

| AA label | Omniscience Index ↑ | Accuracy ↑ | Hallucination Rate ↓ | Notes |
|---|---:|---:|---:|---|
| DeepSeek V4 Flash (Max) | -22.90 | 37.2% | — | Tested here as DeepSeek V4 Flash off/low; AA public row is Max. |
| GLM-5.2 (max) | 3.97 | 25.1% | 28.1% | Tested here at xhigh/high/low/off; AA public row is max. |
| GPT-5.4 mini (xhigh) | -18.68 | 37.5% | — | Tested here at low; AA public row is xhigh. |
| GPT-5.5 (xhigh) | 20.07 | 56.9% | 85.5% | Tested here at low; AA public row is xhigh and shows high hallucination rate despite high accuracy. |
| Gemini 3.5 Flash | 22.68 | 51.9% | 60.7% | Used as judge model family comparison, not observer candidate in this screen. |

Interpretation: AA-Omniscience is useful prior information about knowledge reliability, but it did not overturn the direct observer replay result. In our actual observer task, GLM settings had the highest judged composite scores, while DeepSeek V4 Flash low remained the recommendation under the cost-aware rule because it was within 95% of the best composite score and much cheaper.

## Skipped local Qwen run

Local Qwen was skipped after timeout problems. Preserved partial rows: 10 in `analysis/om-observer-screen/partial_local_qwen_outputs_skipped.jsonl`, with 6 timeout/error rows. These rows are excluded from aggregate scoring and recommendation.

## Artifacts

- Cases: `analysis/om-observer-screen/cases.jsonl`
- Candidate outputs: `analysis/om-observer-screen/candidate_outputs.jsonl`
- Mechanical scores: `analysis/om-observer-screen/mechanical_scores.csv`
- Judge scores: `analysis/om-observer-screen/judge_scores.jsonl`
- Human review packet: `analysis/om-observer-screen/HUMAN_REVIEW_PACKET.md`
- Artificial Analysis comparison: `analysis/om-observer-screen/artificial_analysis_comparison.csv`

## Caveats

- Historical observations are a silver reference, not ground truth.
- OpenRouter accepts requested reasoning effort, but API acceptance alone does not prove a provider implements distinct internal thinking levels.
- Current pi-observational-memory uses one configured worker model/thinking setting for observer, reflector, and dropper.

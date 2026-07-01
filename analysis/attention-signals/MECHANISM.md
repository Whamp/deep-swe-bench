# Tier 0 mechanism finding

Labels (computed per rep from session logs vs the gold patch):
- `solved` = reward_binary==1
- `found_then_lost` = touched a gold file then drifted off (ATTENTION failure)
- `search_failure` = never touched a gold file (search/reasoning failure)
- `found_kept_failed` = kept gold in focus but still failed (execution)

Attention hypothesis predicts OM / higher thinking cut `found_then_lost`
specifically. If they instead mainly cut `search_failure`, OM looks like
generic scaffolding, not attention maintenance.

## OM vs baseline (found_then_lost = attention; search = reasoning)
model | thinking | arm | n | solved | ftl | search | kept
---|---|---|---|---|---|---|---
gpt-5.5|low|baseline|185|0.222|0.114|0.000|0.665
gpt-5.5|low|observational-memory-gpt55-low|36|0.333|0.083|0.000|0.583
gpt-5.5|low|baseline|185|0.222|0.114|0.000|0.665
gpt-5.5|low|observational-memory-gpt54mini-low|185|0.238|0.135|0.000|0.627
deepseek-v4-flash|high|baseline|113|0.018|0.168|0.000|0.814
deepseek-v4-flash|high|observational-memory|113|0.088|0.195|0.000|0.717
deepseek-v4-flash|high|baseline|113|0.018|0.168|0.000|0.814
deepseek-v4-flash|high|advisor-observational-memory|36|0.139|0.278|0.000|0.583

## thinking axis (gpt-5.5 baseline, low -> medium -> xhigh)
thinking | n | solved | ftl | search | kept
---|---|---|---|---|---
low|185|0.222|0.114|0.000|0.665
medium|108|0.361|0.037|0.000|0.602
xhigh|39|0.513|0.103|0.000|0.385

## Verdict (file-level proxy)

Across 1063 reps, `search_failure` (never touching a gold file) is 0.002 pooled -- essentially zero; mean first-gold-turn is ~2-4 turns in every arm. DeepSWE failure is almost never a finding/search problem. The dominant bucket is `found_kept_failed` (agent held the gold file in focus through the final quarter but still failed): 0.60-0.81 of reps by arm. `found_then_lost` (true file-level drift) is the smaller bucket, 0.08-0.28.

Both levers raise solve rate: thinking (gpt-5.5 baseline low->medium->xhigh) lifts solves 0.222->0.361->0.513; OM lifts deepseek 0.018->0.088 (2/113->10/113, matching the om-memory-pilot-w10 number exactly). But the gains come overwhelmingly out of `found_kept_failed` (deepseek OM kept 0.814->0.717 = -0.097; xhigh kept 0.665->0.385), NOT out of `found_then_lost`. ftl is non-monotonic on thinking (0.114->0.037->0.103) and roughly flat-to-up on OM (deepseek +0.027, partly a length confound: OM reps run +22 median turns; gpt-5.5/om-gpt55-low -0.030).

**At file granularity the strong form of the attention hypothesis -- that thinking/OM work by preventing drift OFF the gold area -- is NOT supported: there is little file-level drift to prevent.** The execution-failure dominance says the real difficulty is finishing the change, not locating or holding the file. This does not falsify the broader attention idea; it shows the file-touch proxy is saturated (everyone finds the gold file). The demo rep `abs-stepped-slices/deepseek-baseline/rep0` proves the signal IS recoverable when drift is real (gold focus turns 2-75, then empty for the final 40 turns, partial 0.667).

**Recommendation before any Tier-1 budget spend:** move the focus proxy from gold FILE to gold SYMBOL/HUNK (the functions/identifiers the patch changes) so intra-file drift becomes visible, then re-test whether OM/thinking cut symbol-level drift. The matched-budget ablation (Tier 1) remains the decisive test, but Tier 0 says measure symbol-level attention, not file-level, or the ablation answers the wrong question.

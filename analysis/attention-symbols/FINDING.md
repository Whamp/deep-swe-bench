# Analysis A: symbol/hunk-level attention

Gold unit = SYMBOLS changed by the patch (func/def/class/type/method), extracted from `@@` hunk context + def lines on added hunks. Focus = a turn whose tool-call args mention a gold symbol as a word-bounded token.

Symbol extraction: 113/113 tasks have >=1 gold symbol (0.0% have none -- patches that only touch config, imports, or non-def lines).

## OM vs baseline (symbol_found_then_lost = attention; never_found = search)
model | thinking | arm | n | solved | ftl | never | kept
---|---|---|---|---|---|---|---
gpt-5.5|low|baseline|185|0.222|0.216|0.054|0.508
gpt-5.5|low|observational-memory-gpt55-low|36|0.333|0.194|0.139|0.333
gpt-5.5|low|baseline|185|0.222|0.216|0.054|0.508
gpt-5.5|low|observational-memory-gpt54mini-low|185|0.238|0.205|0.086|0.470
deepseek-v4-flash|high|baseline|113|0.018|0.124|0.062|0.796
deepseek-v4-flash|high|observational-memory|113|0.088|0.159|0.044|0.708
deepseek-v4-flash|high|baseline|113|0.018|0.124|0.062|0.796
deepseek-v4-flash|high|advisor-observational-memory|36|0.139|0.056|0.111|0.694

## thinking axis (gpt-5.5 baseline, low -> medium -> xhigh)
thinking | n | solved | ftl | never | kept
---|---|---|---|---|---
low|185|0.222|0.216|0.054|0.508
medium|108|0.361|0.148|0.056|0.435
xhigh|39|0.513|0.077|0.000|0.410

## Finding (symbol level)

At symbol granularity the picture differs from the file level. OM still lifts solves on the known axes (deepseek +0.071; gpt-5.5/om-gpt55-low +0.112), reconciling with the 2/113->10/113 deepseek number. The question is whether the gains come out of symbol_found_then_lost (attention) or symbol_kept_failed (execution): deepseek OM ftl +0.035, kept -0.088; gpt-5.5/om-gpt55-low ftl -0.022, kept -0.175.

**If OM/thinking now cut symbol-level ftl where they did NOT cut file-level ftl, that is the first positive evidence for the attention hypothesis at the correct unit.** Compare these deltas to the Tier-0 file-level table (analysis/attention-signals/MECHANISM.md), where file ftl was flat-to-up. The contrast between file-ftl and symbol-ftl is the headline of analysis A.

Caveat: symbol focus uses word-boundary token match, so very common identifiers add noise; sym_coverage is reported so the reader can see scale. Analysis B moves to graph EDGES (caller/callee), which is the relationship unit the hypothesis is really about and is not token-match noisy.

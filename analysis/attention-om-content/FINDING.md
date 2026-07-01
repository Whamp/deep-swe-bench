# Analysis C: do OM streams carry relationship-graph content?

Each OM observation/reflection is classified lexically for relationship content (caller/callee, dependency/import, type/inheritance, dataflow, register/hook) vs file-level or generic. rel_frac = share of OM records carrying at least one relationship signal.

## OM stream composition by config
model | thinking | config | n | solved | partial | rel_frac | mean_n_obs
---|---|---|---|---|---|---|---
deepseek-v4-flash|high|observational-memory|113|0.088|0.856|0.300|48
gpt-5.5|low|observational-memory-gpt54-low|36|0.333|0.970|0.226|12
gpt-5.5|low|observational-memory-gpt54mini-low|180|0.233|0.953|0.165|13
gpt-5.5|low|observational-memory-gpt55-low|33|0.303|0.980|0.229|17

## within-config split: mean(partial | rel_frac above median) - mean(partial | at/below median)
config | n | delta_partial(high_rel - low_rel)
---|---|---
observational-memory | 113 | +0.085
observational-memory-gpt54-low | 36 | -0.049
observational-memory-gpt54mini-low | 180 | +0.024
observational-memory-gpt55-low | 33 | -0.018

## Finding (OM content)

rel_frac answers: how much of what OM records is *relationship* content (the codegraph unit) vs file/generic. If rel_frac is high AND reps with higher rel_frac solve more (positive within-config delta), that is evidence OM externalizes relationship attention -- the 'poor man's codegraph' claim. If rel_frac is high but the delta is ~0, OM carries relationships but they don't drive outcomes (scaffolding, not mechanism). If rel_frac is low, OM is mostly file/generic and the hypothesis is not supported at this layer.

Caveat: lexical classification undercounts paraphrased relationships (a symbol-linker/embedding classifier is the upgrade). The cross-check with analysis B (do high-rel-frac reps also show higher executor edge_coverage?) is the stronger test and is joined in the SYNTHESIS.

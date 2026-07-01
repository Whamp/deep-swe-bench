# Analysis B: relationship/edge-level attention

Gold unit = graph EDGES. For each task, codegraph (on the repo at base_commit_hash) finds the 1-hop CALLERS of every changed symbol -> the blast-radius subgraph. Per rep, edge_coverage = fraction of gold edges whose two endpoints (caller + changed symbol) the agent co-referenced in the same turn; caller_seen_rate = fraction of distinct callers ever named; edge_ftl = referenced a caller early then none in the final quarter.

Coverage: 862 reps analyzed (only tasks whose subgraph built successfully; blocked tasks listed in subgraphs/*.json).

## OM vs baseline
model | thinking | arm | n | solved | edge_cov | caller_seen | edge_ftl
---|---|---|---|---|---|---|---
gpt-5.5|low|baseline|150|0.213|0.030|0.105|0.287
gpt-5.5|low|observational-memory-gpt55-low|30|0.400|0.020|0.142|0.267
deepseek-v4-flash|high|baseline|92|0.022|0.064|0.171|0.228
deepseek-v4-flash|high|observational-memory|92|0.087|0.080|0.190|0.250

## thinking axis (gpt-5.5 baseline)
thinking | n | edge_cov | caller_seen | edge_ftl
---|---|---|---|---
low|150|0.030|0.105|0.287
medium|87|0.037|0.122|0.322
xhigh|30|0.071|0.105|0.333

## Finding (edge level)

Edge deltas (OM - baseline): deepseek edge_cov +0.015, caller_seen +0.019, edge_ftl +0.022; gpt-5.5/om-gpt55-low edge_cov -0.010, caller_seen +0.037, edge_ftl -0.020.

edge_coverage and caller_seen_rate are the relationship-attention score. If OM lifts these (the agent looks at MORE of the caller graph), that is direct evidence OM externalizes relationship attention. edge_ftl dropping means the agent holds the caller relationship to the end (attention maintenance) rather than seeing it once and drifting. The thinking axis tests whether raw compute buys the same relationship attention.

Caveat: edge_coverage is bounded by how many callers the task's gold subgraph actually has and by token-match on caller names; some repos failed to clone/build and are excluded (see status counts). Callees and type-dependency edges are the upgrade path (callers = fan-in only here).

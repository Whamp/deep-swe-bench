# SYNTHESIS: attention vs intelligence at the correct unit (symbols & edges)

Three analyses, one per layer of the attention unit:
- **A (symbol):** gold = changed functions/classes/types from the patch; focus = a turn whose output mentions a gold symbol. `attention-symbols/`.
- **B (edge):** gold = codegraph 1-hop CALLERS of changed symbols (blast radius); focus = a turn whose output co-references a caller + changed symbol. `attention-edges/`.
- **C (OM content):** lexical classification of OM observation/reflection text for relationship content. `attention-om-content/`.

All three count the assistant's full output (text + tool args), not just tool args -- a bug found and fixed mid-run (relationship reasoning lives in prose like "X calls Y", and thinking blocks are encrypted for gpt-5.5 so only readable text is counted).

## 1. Thinking buys SYMBOL attention; it barely buys EDGE attention

gpt-5.5 baseline, low -> medium -> xhigh:

| thinking | solved | symbol_ftl | edge_coverage |
|---|---|---|---|
| low | 0.222 | 0.216 | 0.030 |
| medium | 0.361 | 0.148 | 0.037 |
| xhigh | 0.513 | 0.077 | 0.071 |

Symbol-level drift (`symbol_ftl`) falls **monotonically** 0.216 -> 0.148 -> 0.077 as thinking rises: higher thinking holds the changed symbol in focus. This is the cleanest positive evidence for the user's hypothesis -- at the symbol layer, more 'intelligence' looks exactly like better attention maintenance. By contrast `edge_coverage` barely moves (0.030 -> 0.037 -> 0.071) and stays near zero: **more thinking does NOT make the model attend to caller relationships.** Agents almost never co-reference a function with its callers at any thinking level.

## 2. OM does not substitute for thinking's symbol-attention benefit

OM vs baseline symbol_ftl deltas: deepseek +0.035 (baseline 0.124 -> OM 0.159, slightly WORSE); gpt-5.5/om-gpt55-low -0.022 (0.216 -> 0.194, marginal). OM does not reproduce thinking's monotonic symbol-drift reduction. On solves OM still helps (deepseek 2/113->10/113), so its benefit is real but is NOT mediated by symbol-level attention -- it comes out of `kept_failed` (execution), same as the file-level finding.

## 3. OM CARRIES relationship content but the executor doesn't act on it

OM streams carry relationship content (C rel_frac): deepseek OM mean 0.297, gpt-5.5/om-gpt54mini-low 0.164. So OM *records* caller/dependency/type relationships -- it is not purely file/generic notes. The cross-analysis join (within deepseek OM, n=92): corr(rel_frac, executor edge_coverage) = +0.040; corr(rel_frac, reward_partial) = +0.199; corr(rel_frac, solved) = +0.022. gpt-5.5/om-gpt54mini-low (n=146): corr(rel_frac, edge_coverage) = +0.045, corr(rel_frac, partial) = +0.101.

Read: more relationship CONTENT in OM weakly correlates with better OUTCOME on deepseek but **does not correlate with the executor exhibiting more EDGE attention.** There is a memory->execution gap: OM captures the relationship graph (a poor man's codegraph, in content) but that capture does not flow through into the executor actually looking at callers. This is the sharpest finding: the relationship attention the hypothesis is about is neither bought by thinking (B) nor effectively externalized by observational memory (C->B join).

## Verdict

**Partially supported, layer-dependent.**
- Symbol layer: SUPPORTED. Thinking maintains symbol attention (monotonic drift fall). Intelligence behaves like attention here.
- Relationship/edge layer: NOT SUPPORTED at present. Neither thinking nor observational memory produces meaningful caller-graph attention (edge_coverage 0.02-0.11 everywhere). The two tools the user named (codegraph / codebase-memory-mcp) exist precisely because models don't do this spontaneously -- and the data confirms they don't, even at xhigh.
- OM-as-substitute: NOT YET. OM records relationships (C) but the executor doesn't act on them (C->B), and OM doesn't reproduce thinking's symbol benefit. Observational memory is a leaky proxy for an explicit relationship tool.

## What this implies for Tier 1 (the decisive test)

The matched-budget ablation should now be framed at the EDGE layer, and should compare observational memory against an EXPLICIT relationship tool (codegraph/codebase-memory-mcp), not against bare baseline: the question is whether forcing caller-graph attention (a tool that returns callers, not prose that mentions them) lets a cheap model match xhigh on edge_coverage and on solves. Tier 0+A+B+C predict that observational memory alone will NOT close the edge gap (C->B join ~0), but an explicit graph tool plausibly would -- because the bottleneck is execution-time relationship lookup, which only a queryable tool provides.

## Caveats (honest)

- A/B symbol+edge focus is word-bounded token match; common identifiers add noise (sym_coverage reported so scale is visible).
- B measures only caller (fan-in) edges; callees/type-deps are the upgrade path (callers are the blast-radius edge and the one codegraph's `fn-impact` is built around).
- 21/113 tasks have `no_edges_found` (patches that ADD new files/functions with no existing callers at base_commit) and are excluded from B; this is correct, not a failure.
- 0 tasks were blocked: all 92 distinct repos cloned + codegraph-built at base_commit_hash.
- gpt-5.5 thinking content is encrypted; only readable assistant text is counted (undercounts thinking models' true internal relationship reasoning).
- Lexical C classifier undercounts paraphrased relationships.

Artifacts: analysis/attention-symbols/, analysis/attention-edges/, analysis/attention-om-content/. Scripts: scripts/attention_symbols.py, scripts/attention_edges.py, scripts/attention_om_content.py.

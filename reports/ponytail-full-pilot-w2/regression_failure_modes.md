# Easy/medium Ponytail regression failure modes

Scope: easy/medium tasks where Ponytail partial reward regressed by more than 5 percentage points vs baseline (`delta_partial < -0.05`). This yields 18 paired regressions. Categories are primary-cause labels based on patch paths, verifier f2p/p2p deltas, and trace/patched-file evidence.

## Summary

| primary bucket | n | mean Δpartial | mean Δf2p | mean Δp2p | median Δtokens | median Δchanged lines | interpretation |
|---|--:|--:|--:|--:|--:|--:|---|
| omitted tests/fixtures as guardrail | 7 | -0.520 | -0.743 | -0.455 | -4,620,998 | -425 | Ponytail often solved the visible core but dropped the local spec/fixture that would have forced complete hidden-case coverage. |
| missing downstream wiring/export/init | 6 | -0.550 | -0.496 | -0.506 | -1,638,004 | -582 | The implementation existed somewhere, but public exports, init paths, generated parser files, themes, or cross-module hooks were not fully connected. |
| wrong layer or incomplete semantics | 5 | -0.316 | -0.407 | -0.239 | -507,328 | -260 | Ponytail changed plausible files, but the algorithm/model was wrong or incomplete; tests/exports alone do not explain the loss. |

## Classified tasks

| bucket | task | category | partial | f2p | p2p | evidence |
|---|---|---|---:|---|---|---|
| easy | `gql-incremental-graphql-delivery` | missing downstream wiring/export/init | 0.994 → 0.000 (-0.994) | 13/17 → 0/17 | 810/811 → 0/811 | Ponytail omitted transport base/async interfaces and `gql/utilities/__init__.py`; source patch was a narrow client/transport subset and all verifier tests failed. |
| medium | `fastapi-deprecation-response-headers` | missing downstream wiring/export/init | 0.966 → 0.006 (-0.960) | 70/137 → 19/137 | 3090/3134 → 0/3134 | Ponytail omitted `fastapi/__init__.py` from baseline path set and trace/workflow found a runtime `NameError: sunset`; p2p fell to 0/3134. |
| medium | `anko-typed-variable-bindings` | missing downstream wiring/export/init | 0.961 → 0.010 (-0.951) | 5/9 → 0/9 | 94/94 → 1/94 | Ponytail omitted parser grammar/generated parser and `envTypes.go` while adding `envValues.go`; typed binding syntax was not wired through the parser/type environment, p2p 94/94 to 1/94. |
| medium | `superjson-error-stack-serialization` | missing downstream wiring/export/init | 0.878 → 0.633 (-0.245) | 56/80 → 8/80 | 116/116 → 116/116 | Ponytail omitted public/index and transformer wiring (`src/index.ts`, `src/transformer.ts`); p2p stayed 116/116 but f2p fell 56/80 to 8/80. |
| medium | `quill-shared-toolbar-focus` | missing downstream wiring/export/init | 0.829 → 0.743 (-0.086) | 7/13 → 5/13 | 22/22 → 21/22 | Ponytail omitted bubble/snow theme wiring and touched only toolbar/base; f2p and p2p both slipped. |
| medium | `mobly-grouped-test-barriers` | missing downstream wiring/export/init | 0.966 → 0.905 (-0.061) | 49/79 → 7/79 | 808/808 → 796/808 | Ponytail moved work into `mobly/sync.py` and omitted `mobly/group_execution.py` plus `tests/mobly/group_execution_test.py`; f2p cratered 49/79 to 7/79. |
| easy | `actionlint-action-pinning-lint` | omitted tests/fixtures as guardrail | 1.000 → 0.000 (-1.000) | 55/55 → 0/55 | 145/145 → 0/145 | Ponytail dropped both changed test/fixture files (`rule_action_pinning_test.go`, `testdata/format/test.sarif`) and produced a much smaller source-only patch; verifier went 55/55+145/145 to 0/55+0/145. |
| easy | `adaptix-name-mapping-aliases` | omitted tests/fixtures as guardrail | 0.999 → 0.000 (-0.999) | 40/44 → 0/44 | 2738/2738 → 0/2738 | Ponytail omitted both baseline test files and four downstream source modules (`loader_provider.py`, name-layout base/provider, overlay_schema); hidden verifier collapsed to zero. |
| easy | `yjs-map-conflict-detection` | omitted tests/fixtures as guardrail | 0.996 → 0.000 (-0.996) | 8/9 → 0/9 | 231/231 → 0/231 | Ponytail omitted both conflict tests and lower-level integration files (`Item.js`, `encoding.js`), turning a near-solve into zero. |
| medium | `textual-richlog-follow-state` | omitted tests/fixtures as guardrail | 0.923 → 0.654 (-0.269) | 18/20 → 11/20 | 6/6 → 6/6 | Same core widget files, but Ponytail dropped `tests/test_follow_state.py`; p2p stayed 6/6 while f2p fell 18/20 to 11/20, suggesting missed hidden follow-state cases. |
| easy | `sql-formatter-bigquery-pipe-formatting` | omitted tests/fixtures as guardrail | 0.999 → 0.813 (-0.186) | 21/26 → 0/26 | 5709/5709 → 4664/5709 | Same parser/formatter files but Ponytail dropped `test/pipe_syntax.test.ts`; p2p mostly held while f2p went 21/26 to 0/26. |
| medium | `tengo-callable-instance-isolation` | omitted tests/fixtures as guardrail | 0.959 → 0.855 (-0.103) | 17/23 → 2/23 | 122/122 → 122/122 | Ponytail swapped to `callable_test.go` and omitted baseline `script_test.go`; also changed compiler surface, leaving only 2/23 f2p. |
| easy | `true-myth-iterable-collection-combinators` | omitted tests/fixtures as guardrail | 0.998 → 0.912 (-0.087) | 95/96 → 38/96 | 561/561 → 561/561 | Ponytail touched only maybe/result and omitted task/toolbelt source plus all four corresponding tests; f2p fell 95/96 to 38/96 while p2p stayed green. |
| easy | `expr-try-catch-errors` | wrong layer or incomplete semantics | 0.999 → 0.006 (-0.993) | 3/79 → 0/79 | 66265/66265 → 395/66265 | Baseline worked in AST/parser/lexer/checker; Ponytail added compiler/vm/opcode handling and omitted `ast/visitor.go` + lexer state; p2p collapsed from 66265/66265 to 395/66265. |
| easy | `dasel-html-document-format` | wrong layer or incomplete semantics | 0.992 → 0.698 (-0.294) | 137/146 → 0/146 | 1012/1012 → 808/1012 | Ponytail added go.mod/go.sum dependency surface while staying in HTML parser/reader/writer; f2p went 137/146 to 0/146 with p2p losses, indicating semantic mismatch rather than just missing exports. |
| medium | `katex-multicolumn-array-spans` | wrong layer or incomplete semantics | 0.978 → 0.864 (-0.114) | 79/94 → 0/94 | 599/599 → 599/599 | Same source files as baseline, but Ponytail implementation failed all f2p (79/94 to 0/94) while p2p stayed green: wrong semantics inside the right layer. |
| medium | `onedump-dump-encryption-pipeline` | wrong layer or incomplete semantics | 0.977 → 0.886 (-0.091) | 80/82 → 72/82 | 6/6 → 6/6 | Same source/test surface as baseline, smaller quality drop (80/82 to 72/82 f2p): likely incomplete edge semantics rather than missing wiring. |
| medium | `returns-validated-error-accumulation` | wrong layer or incomplete semantics | 0.973 → 0.886 (-0.086) | 153/159 → 134/159 | 61/61 → 61/61 | Same source surface as baseline, p2p stable, f2p fell 153/159 to 134/159: hidden semantic incompleteness within the right files. |

## Takeaway

- The largest bucket is not “Ponytail made a weird crash”; it is **Ponytail stopped too early**. In 13/18 cases, the loss is best explained by omitted test/fixture guardrails or missing downstream wiring.

- The catastrophic easy regressions are mostly all-or-nothing verifier failures where a smaller patch missed a required compatibility surface.

- The more benign medium regressions often preserve p2p while losing f2p, which means Ponytail kept existing behavior but missed new hidden requirements.

- Public phrasing should be: Ponytail reduces patch/cost by pruning work, but the same pruning can remove the tests/wiring that make easy tasks actually complete.

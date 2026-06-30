# Unique observations: GLM-5.2 off vs GPT-5.4-mini low

Nearest-neighbor search is task-local. An observation is marked unique when its best cross-config neighbor has cosine similarity `< 0.8`.

## Summary

| direction | observations | unique | unique rate | environment/tooling notes | substantive unique rate | mean nearest sim | median nearest sim |
|---|---:|---:|---:|---:|---:|---:|---:|
| observational-memory-glm52-off -> observational-memory-gpt54mini-low | 738 | 298 | 0.404 | 20 | 0.396 | 0.810 | 0.822 |
| observational-memory-gpt54mini-low -> observational-memory-glm52-off | 462 | 129 | 0.279 | 5 | 0.280 | 0.836 | 0.851 |

## Lowest-similarity examples: observational-memory-glm52-off -> observational-memory-gpt54mini-low

### kgateway-consistent-hash-policy rep0 · sim 0.307 · other · environment/tooling

Observation:

> Observation: rg (ripgrep) is not available in this environment; grep is available instead.

Nearest other-config observation:

> Agent confirmed the existing URL rewrite code already uses envoy type matcher RegexMatchAndSubstitute, which can be reused as a pattern for hash-policy regex rewrites.

### kgateway-consistent-hash-policy rep2 · sim 0.328 · other · environment/tooling

Observation:

> rg (ripgrep) is not available in the environment; grep is used instead for searching code.

Nearest other-config observation:

> Agent confirmed the existing URL rewrite code already uses envoy type matcher RegexMatchAndSubstitute, which can be reused as a pattern for hash-policy regex rewrites.

### kgateway-consistent-hash-policy rep1 · sim 0.334 · implementation_state · environment/tooling

Observation:

> Environment note: 'rg' (ripgrep) command is not available; must use grep instead.

Nearest other-config observation:

> Agent confirmed the existing URL rewrite code already uses envoy type matcher RegexMatchAndSubstitute, which can be reused as a pattern for hash-policy regex rewrites.

### fastapi-implicit-head-options rep0 · sim 0.348 · other · environment/tooling

Observation:

> `rg` (ripgrep) is not installed in the environment; `grep` is used instead.

Nearest other-config observation:

> running pytest on tests/test_additional_response_extra.py failed during collection because starlette.testclient requires httpx2, which is not installed in the environment.

### boa-hierarchical-evaluation-cancellation rep2 · sim 0.351 · other · environment/tooling

Observation:

> rg is not available in the environment; grep is used instead for code search.

Nearest other-config observation:

> Assistant found Script::evaluate and Module::evaluate plus Module::load_link_evaluate in core/engine/src/script.rs and core/engine/src/module/mod.rs.

### dynamodb-toolbox-lazy-recursive-schemas rep2 · sim 0.355 · implementation_state · environment/tooling

Observation:

> Note: rg (ripgrep) is not available in this environment; use grep or find instead.

Nearest other-config observation:

> Assistant tried running vitest with --runInBand, but the CLI rejected the option as unknown.

### actionlint-action-pinning-lint rep1 · sim 0.412 · implementation_state · environment/tooling

Observation:

> Note: 'rg' (ripgrep) is not available in this environment; use 'grep -R' instead.

Nearest other-config observation:

> Agent inspected ast.go, command.go, and linter.go to locate String, Exec, config loading, and command-line flag wiring for the new action-pinning rule.

### anko-default-function-arguments rep0 · sim 0.424 · implementation_state

Observation:

> Repository is the anko Go interpreter (github.com/mattn/anko). Started on branch master, top-level dirs include ast, parser, vm, core, env, core, packages, cmd, misc.

Nearest other-config observation:

> The repository is currently on branch master with a clean working tree, and a new branch named default-args was created after main was unavailable.


## Lowest-similarity substantive examples: observational-memory-glm52-off -> observational-memory-gpt54mini-low

### anko-default-function-arguments rep0 · sim 0.424 · implementation_state

Observation:

> Repository is the anko Go interpreter (github.com/mattn/anko). Started on branch master, top-level dirs include ast, parser, vm, core, env, core, packages, cmd, misc.

Nearest other-config observation:

> The repository is currently on branch master with a clean working tree, and a new branch named default-args was created after main was unavailable.

### actionlint-action-pinning-lint rep2 · sim 0.486 · code_structure

Observation:

> Pass interface in pass.go defines VisitStep, VisitJobPre, VisitJobPost, VisitWorkflowPre, VisitWorkflowPost callbacks. Visitor traverses workflow tree depth-first: Workflow -> Jobs -> Steps.

Nearest other-config observation:

> Agent found that step action uses are represented by ExecAction.Uses and reusable workflow calls by WorkflowCall.Uses in ast.go, and that current rule registration in linter.go already includes NewRuleAction and NewRuleWorkflowCall.

### kgateway-consistent-hash-policy rep1 · sim 0.494 · implementation_state

Observation:

> Duration handling pattern in trafficpolicy plugin: uses golang durationpb package (google.golang.org/protobuf/types/known/durationpb) with .Duration field from gateway-api types, e.g. durationpb.New(spec.Timeouts.Request.Duration). Relevant for cookie TTL parsing.

Nearest other-config observation:

> pkg/kgateway/extensions2/plugins/trafficpolicy/constructor.go calls constructHeaderModifiers twice and constructRBAC twice when building TrafficPolicy IR.

### actionlint-action-pinning-lint rep2 · sim 0.519 · test_failure

Observation:

> RuleBase in rule.go provides Error/Errorf methods and embeds name, desc, errs, config. NewRuleBase(name, desc) constructor. The Rule interface requires Errs(), Name(), Description(), EnableDebug, SetConfig, Config methods plus Pass methods.

Nearest other-config observation:

> Agent inspected config.go, rule_action.go, rule.go, popular_actions.go, and ast.go to locate existing config and action/workflow AST structures relevant to the new rule.

### awilix-async-container-initialization rep2 · sim 0.520 · test_failure

Observation:

> Pre-existing issue: examples/typescript/src/index.ts:2 has TS2307 error 'Cannot find module ../../..' which is unrelated to the async initializer changes. This blocks npm run check but does not block jest tests run directly via npx jest.

Nearest other-config observation:

> Assistant checked the repo state, confirmed the working tree was clean on branch master, then created a new branch named async-initializers.

### cattrs-partial-structuring-recovery rep1 · sim 0.524 · code_structure

Observation:

> black module not installed (python -m black fails, uv run black fails with 'No such file or directory'). Formatted code manually via edits instead. uv run creates .venv with CPython 3.12.12.

Nearest other-config observation:

> Agent reformatted the new partial-structure code in src/cattrs/converters.py after a failed black invocation because black is not installed in the environment.

### actionlint-action-pinning-lint rep2 · sim 0.525 · code_structure

Observation:

> Surveyed popular_actions.go: PopularActions is a generated map[string]*ActionMetadata keyed by full specs like '8398a7/action-slack@v3', marked DO NOT EDIT.

Nearest other-config observation:

> User requested error suggestions for popular actions to reference the specific known version from known-actions data.

### cattrs-partial-structuring-recovery rep2 · sim 0.530 · implementation_state

Observation:

> confirmed: requires-python is >=3.10 in pyproject.toml. ExceptionGroup is imported from _compat (builtins for 3.11+, exceptiongroup backport otherwise), not defined locally. Updated converters.py to import ExceptionGroup from _compat instead of using it unqualified.

Nearest other-config observation:

> Agent changed partial error aggregation to honor detailed_validation, returning the first error when it is disabled and ExceptionGroup when it is enabled.

### cattrs-partial-structuring-recovery rep1 · sim 0.574 · code_structure

Observation:

> pyproject.toml read: cattrs requires Python >=3.10, depends on attrs>=25.4.0, typing-extensions>=4.14.0, exceptiongroup>=1.1.1 (for python<3.11). mypy strict=true. Build system is hatchling+hatch-vcs. black and ruff are lint deps but black is not installed in the environment.

Nearest other-config observation:

> Agent reformatted the new partial-structure code in src/cattrs/converters.py after a failed black invocation because black is not installed in the environment.

### yjs-map-conflict-detection rep0 · sim 0.578 · implementation_state

Observation:

> Doc constructor signature before changes: constructor({ guid, collectionid, gc, gcFilter, meta, autoLoad, shouldLoad, isSuggestionDoc } = {}). Doc has properties: share (Map), store (StructStore), _transaction, _transactionCleanups, subdocs, _item, etc.

Nearest other-config observation:

> Assistant inspected src/utils/Doc.js and src/utils/Transaction.js to locate document and transaction handling, including transaction cleanup and update emission paths.

### ts-pattern-match-each rep2 · sim 0.592 · implementation_state

Observation:

> User specified each clause must maintain independent selection state; named selections from one clause must not leak into another. Selections via `P.select()` must produce independent results across multiple calls of any compiled function.

Nearest other-config observation:

> User requested matchEach to support .tap, reusable compiled matchers via explicit type parameters, .toFunction, .toExhaustiveFunction, .toPartialFunction, independent P.select() results across calls, and per-clause selection isolation.

### boa-hierarchical-evaluation-cancellation rep0 · sim 0.595 · task_requirement

Observation:

> APIs that evaluate, enqueue, or run under a handle must take the handle by shared reference, not ownership.

Nearest other-config observation:

> completed: added doc comments to the new EvaluationHandle API methods and promoted EvaluationHandle to the crate root export in core/engine/src/lib.rs.


## Lowest-similarity examples: observational-memory-gpt54mini-low -> observational-memory-glm52-off

### fastapi-implicit-head-options rep0 · sim 0.445 · test_failure

Observation:

> running pytest on tests/test_additional_response_extra.py failed during collection because starlette.testclient requires httpx2, which is not installed in the environment.

Nearest other-config observation:

> Bug found: APIRouter.__init__ auto_head/auto_options params were not actually persisted as self.auto_head/self.auto_options due to patch targeting wrong location; AttributeError 'APIRouter object has no attribute auto_head' at add_api_route line 1427. Needs fixing.

### httpx-streaming-json-iteration rep2 · sim 0.461 · test_failure

Observation:

> a targeted run of tests/test_timeouts.py::test_write_timeout still failed under trio with a ByteStream async-generator ResourceWarning unrelated to the JSON work

Nearest other-config observation:

> Response class is defined at httpx/_models.py:515. Existing iter_bytes/iter_text/iter_lines/iter_raw sync methods and aiter_bytes/aiter_text/aiter_lines/aiter_raw async methods are the established patterns for new iter_json/aiter_json to follow.

### anko-default-function-arguments rep1 · sim 0.495 · code_structure

Observation:

> The parser was tightened so rewriteParams now bails out early when no top-level '=' exists, preserving ordinary parameter lists.

Nearest other-config observation:

> Modified ParseSrc in parser/lexer.go to call rewriteDefaultArgs(src) before scanning.

### actionlint-action-pinning-lint rep1 · sim 0.557 · test_failure

Observation:

> User requested error messages that distinguish reusable workflows from step actions.

Nearest other-config observation:

> AST survey: ExecAction struct (ast.go ~line 455) has Uses *String field for step-level actions. WorkflowCall struct (ast.go ~line 849) has Uses *String field for job-level reusable workflows. Job struct is at ast.go line 876.

### ts-pattern-match-each rep2 · sim 0.567 · test_failure

Observation:

> Assistant ran npm run build, which produced dist bundles but failed in scripts/generate-cts.sh with repeated sed errors and exit code 2.

Nearest other-config observation:

> completed: tsc --noEmit passes with no type errors. Note: npm run build fails due to pre-existing issue in scripts/generate-cts.sh (sed errors, unrelated to matchEach changes).

### cattrs-partial-structuring-recovery rep0 · sim 0.572 · test_failure

Observation:

> A full pytest run could not complete because optional test dependencies were missing: msgspec, yaml, immutables, and bson.

Nearest other-config observation:

> pyproject.toml read: cattrs requires Python >=3.10, depends on attrs>=25.4.0, typing-extensions>=4.14.0, exceptiongroup>=1.1.1 (for python<3.11). mypy strict=true. Build system is hatchling+hatch-vcs. black and ruff are lint deps but black is not installed in the environment.

### mashumaro-flattened-dataclass-fields rep0 · sim 0.581 · code_structure

Observation:

> Assistant inspected DataClassDictMixin in mashumaro/mixins/dict.py and confirmed mixin compilation happens during __init_subclass__.

Nearest other-config observation:

> Task requirements: validate at class creation for collisions (including all alias types), non-dataclass types, and invalid/duplicate rename keys. Flattened children must keep their own config. forbid_extra_keys must account for flattened keys. Optional flattened fields should work.

### cattrs-partial-structuring-recovery rep2 · sim 0.583 · test_failure

Observation:

> Agent ran the full pytest suite and hit missing optional dependency import errors for msgspec, yaml, immutables, and bson during collection.

Nearest other-config observation:

> Environment note: full test suite has 6 collection errors due to missing optional dependencies (msgspec, yaml, immutables, bson) -- these are pre-existing and unrelated to partial_structure changes. Tests run scoped to test_partial_structure.py, test_converter.py, test_structure.py instead.


## Lowest-similarity substantive examples: observational-memory-gpt54mini-low -> observational-memory-glm52-off

### fastapi-implicit-head-options rep0 · sim 0.445 · test_failure

Observation:

> running pytest on tests/test_additional_response_extra.py failed during collection because starlette.testclient requires httpx2, which is not installed in the environment.

Nearest other-config observation:

> Bug found: APIRouter.__init__ auto_head/auto_options params were not actually persisted as self.auto_head/self.auto_options due to patch targeting wrong location; AttributeError 'APIRouter object has no attribute auto_head' at add_api_route line 1427. Needs fixing.

### httpx-streaming-json-iteration rep2 · sim 0.461 · test_failure

Observation:

> a targeted run of tests/test_timeouts.py::test_write_timeout still failed under trio with a ByteStream async-generator ResourceWarning unrelated to the JSON work

Nearest other-config observation:

> Response class is defined at httpx/_models.py:515. Existing iter_bytes/iter_text/iter_lines/iter_raw sync methods and aiter_bytes/aiter_text/aiter_lines/aiter_raw async methods are the established patterns for new iter_json/aiter_json to follow.

### anko-default-function-arguments rep1 · sim 0.495 · code_structure

Observation:

> The parser was tightened so rewriteParams now bails out early when no top-level '=' exists, preserving ordinary parameter lists.

Nearest other-config observation:

> Modified ParseSrc in parser/lexer.go to call rewriteDefaultArgs(src) before scanning.

### actionlint-action-pinning-lint rep1 · sim 0.557 · test_failure

Observation:

> User requested error messages that distinguish reusable workflows from step actions.

Nearest other-config observation:

> AST survey: ExecAction struct (ast.go ~line 455) has Uses *String field for step-level actions. WorkflowCall struct (ast.go ~line 849) has Uses *String field for job-level reusable workflows. Job struct is at ast.go line 876.

### ts-pattern-match-each rep2 · sim 0.567 · test_failure

Observation:

> Assistant ran npm run build, which produced dist bundles but failed in scripts/generate-cts.sh with repeated sed errors and exit code 2.

Nearest other-config observation:

> completed: tsc --noEmit passes with no type errors. Note: npm run build fails due to pre-existing issue in scripts/generate-cts.sh (sed errors, unrelated to matchEach changes).

### cattrs-partial-structuring-recovery rep0 · sim 0.572 · test_failure

Observation:

> A full pytest run could not complete because optional test dependencies were missing: msgspec, yaml, immutables, and bson.

Nearest other-config observation:

> pyproject.toml read: cattrs requires Python >=3.10, depends on attrs>=25.4.0, typing-extensions>=4.14.0, exceptiongroup>=1.1.1 (for python<3.11). mypy strict=true. Build system is hatchling+hatch-vcs. black and ruff are lint deps but black is not installed in the environment.

### mashumaro-flattened-dataclass-fields rep0 · sim 0.581 · code_structure

Observation:

> Assistant inspected DataClassDictMixin in mashumaro/mixins/dict.py and confirmed mixin compilation happens during __init_subclass__.

Nearest other-config observation:

> Task requirements: validate at class creation for collisions (including all alias types), non-dataclass types, and invalid/duplicate rename keys. Flattened children must keep their own config. forbid_extra_keys must account for flattened keys. Optional flattened fields should work.

### cattrs-partial-structuring-recovery rep2 · sim 0.583 · test_failure

Observation:

> Agent ran the full pytest suite and hit missing optional dependency import errors for msgspec, yaml, immutables, and bson during collection.

Nearest other-config observation:

> Environment note: full test suite has 6 collection errors due to missing optional dependencies (msgspec, yaml, immutables, bson) -- these are pre-existing and unrelated to partial_structure changes. Tests run scoped to test_partial_structure.py, test_converter.py, test_structure.py instead.

### yjs-map-conflict-detection rep2 · sim 0.585 · test_failure

Observation:

> Assistant ran npm test after the encoding.js change and all 237 tests passed.

Nearest other-config observation:

> confirmed working: ran full test suite (237 tests) with all changes in place, all tests successful in 9.65s, no regressions.

### httpx-streaming-json-iteration rep1 · sim 0.595 · self_reported_completion

Observation:

> Agent ran mypy on httpx/_models.py and it reported no issues.

Nearest other-config observation:

> httpx._models.py imports from jsonlib (the json module imported as jsonlib) and uses jsonlib.detect_encoding for encoding detection; DecodingError and StreamConsumed are defined in httpx/_exceptions.py. DecodingError is a subclass of RequestError.

### mashumaro-flattened-dataclass-fields rep0 · sim 0.599 · test_failure

Observation:

> Assistant ran pytest on tests/test_aliases.py and it passed with 14 tests.

Nearest other-config observation:

> Agent created tests/test_flatten.py with 4 tests: test_flatten_prefix_and_child_aliases, test_flatten_rename_and_optional, test_flatten_forbid_extra_keys, test_flatten_validation. Added TO_DICT_ADD_BY_ALIAS_FLAG import and Config to the rename test.

### anko-default-function-arguments rep1 · sim 0.605 · code_structure

Observation:

> parser/lexer.go was adjusted so applyFuncDefaults now also walks LetsStmt RHS expressions when attaching collected default metadata.

Nearest other-config observation:

> ast/astutil/walk.go has a case *ast.FuncExpr that only walks expr.Stmt (does not yet walk default expressions). May need updating to walk Defaults.

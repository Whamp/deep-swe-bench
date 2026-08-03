# Fixed-unit feedback calibration instructions

Classify every supplied candidate unit exactly once and in the supplied order. Do not discover events, merge events into episodes, omit uncertain units, or inspect any external file.

Use only the bounded focal event and following assistant responses in each unit. `result_outcome` provides trajectory context but cannot prove that an immediate response addressed feedback.

## Candidate disposition

- `negative_feedback`: the subject received an observation that disconfirmed the action's immediate objective or task objective.
- `not_negative_feedback`: the candidate signal is a false positive or a successful observation.
- `not_subject_visible`: a transport diagnostic or missing observation was recorded by the harness but was not presented to the subject.
- `unscorable`: the bounded evidence cannot determine whether feedback occurred.

For any disposition other than `negative_feedback`, set `next_response_label`, `window_outcome`, `revalidation_scope`, and `plan_revision` to `not_applicable`.

## Observation class

- `command_nonzero`: a shell command returned an explicit nonzero status.
- `command_timeout`: a shell command timed out.
- `negative_semantics_with_zero_status`: the tool status was successful but output visibly disconfirmed the action, often through a shell pipeline.
- `schema_invalid_tool_arguments`: a tool rejected argument shape or types.
- `tool_application_rejection`: validly shaped arguments could not apply, such as stale edit text or a missing literal path.
- `execution_environment_failure`: the environment could not perform an otherwise valid operation.
- `transport_or_parser_failure`: independent provider, stream, parser, RPC, or result-transport evidence exists.
- `observation_missing_mid_trajectory`: a call lacks a result but later actions exist.
- `observation_missing_at_termination`: a call lacks a result at trajectory termination.
- `successful_observation`, `unclassified`, or `not_applicable` as defined by their names.

`reported_tool_error` and `read_error` are detector signals, not semantic class names or proof of a broken tool. Classify a missing literal read path as `tool_application_rejection` unless the evidence establishes an environment failure. A failed test, no-match search, compiler error, and rejected edit are ordinary feedback from working tools.

## Action purpose

Choose one: `diagnostic`, `repository_validation`, `ad_hoc_probe`, `mutation`, `delivery_or_tool_mechanics`, `setup_or_commit`, `other`, `indeterminate`, or `not_applicable`. Use `delivery_or_tool_mechanics` for provider transport and malformed tool-invocation candidates, even when the candidate is not subject-visible.

## Immediate response

- `corrective_change`: changes implicated code, configuration, test data, or command inputs.
- `targeted_investigation`: reads, searches, or probes evidence directly tied to the observation.
- `revalidate_same`: reruns the same check without a relevant change.
- `retry_unchanged`: retries the same failed operation without material change.
- `alternate_route`: pursues the same immediate objective through another tool or method.
- `continue_without_addressing`: continues observably but does not address the feedback.
- `terminate`, `indeterminate`, or `not_applicable`.

Label the first meaningful response. Later actions only establish `window_outcome` and revalidation.

## Window outcome and revalidation

- `recovered`: the bounded window visibly closes the failed operation or makes the same behavioral scope pass.
- `progressed`: an addressing response advances the objective or changes the failure, but recovery is not shown.
- `not_recovered`: the failure persists or no addressing progress appears.
- `indeterminate` or `not_applicable`.

Revalidation scope is `same_scope`, `broader_scope`, `narrower_scope`, `different_scope`, `none`, `not_applicable`, or `indeterminate`. A rerun before a relevant change is not post-change revalidation.

## Plan revision

Use `none_observed`, `local_adjustment`, `strategy_revision`, `objective_abandonment`, `indeterminate`, or `not_applicable`. Changing one command argument, target, fixture, or local implementation detail is a local adjustment. Require observable action evidence; prose cannot establish a revision by itself.

## Uncertainty

Use only schema values. Any `indeterminate` value in any semantic field, including `action_purpose`, requires at least one uncertainty reason. Keep confidence low when the bounded excerpt hides the relevant failure or the next action's relevance is ambiguous.

Return one JSON object that satisfies `annotation-schema.json`. Use the exact candidate-set hash, sample hash, annotator ID, candidate IDs, and ID order supplied in the final request. Return JSON only, without Markdown fences or commentary.

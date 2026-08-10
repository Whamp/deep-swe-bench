# Feedback calibration v2 instructions

Classify every held-out candidate exactly once and in the supplied order. Use only each bounded focal event and its following assistant responses. Do not inspect external files, discover more events, merge candidates, omit uncertain cases, or infer success from the final task result.

The development units and development annotations are worked examples. They explain the rules. They are separate from the held-out cases that you must classify.

## 1. Was negative feedback visible to the subject?

Choose `candidate_disposition`:

- `negative_feedback`: the subject received an observation that contradicted the action's immediate objective or the task objective.
- `not_negative_feedback`: the observation was successful or the detector was a false positive.
- `not_subject_visible`: the harness recorded a transport problem or missing result that was not shown to the subject.
- `unscorable`: the bounded evidence cannot establish whether feedback occurred.

If this is not `negative_feedback`, set all five uptake fields to `not_applicable`: `next_response_label`, `window_outcome`, `relevant_change_observed`, `post_change_validation_scope`, and `plan_revision`.

## 2. What happened?

Choose `observation_class`:

- `command_nonzero`: a shell command explicitly exited nonzero.
- `command_timeout`: a shell command timed out.
- `negative_semantics_with_zero_status`: the tool reported success, but visible output still contradicted the objective. This often happens in a shell pipeline.
- `schema_invalid_tool_arguments`: a tool rejected the shape or type of its arguments.
- `tool_application_rejection`: validly shaped arguments could not apply, such as stale edit text or a missing literal path.
- `execution_environment_failure`: the environment could not perform an otherwise valid operation.
- `transport_or_parser_failure`: independent provider, stream, parser, RPC, or result-transport evidence exists.
- `observation_missing_mid_trajectory`: a call has no result but later actions exist.
- `observation_missing_at_termination`: a call has no result at the end of the trajectory.
- `successful_observation`, `unclassified`, or `not_applicable` as their names imply.

A failing test, no-match search, compiler error, or rejected edit is ordinary feedback from a working tool. Detector names such as `reported_tool_error` are review flags, not semantic labels.

Choose `action_purpose` for the focal action: `diagnostic`, `repository_validation`, `ad_hoc_probe`, `mutation`, `delivery_or_tool_mechanics`, `setup_or_commit`, `other`, `indeterminate`, or `not_applicable`.

## 3. What did the subject do first?

Label the first meaningful response after visible negative feedback:

- `corrective_change`: changes implicated code, configuration, test data, or command inputs.
- `targeted_investigation`: reads, searches, or probes evidence directly tied to the observation.
- `revalidate_same`: reruns the same check without a relevant change.
- `retry_unchanged`: retries the same failed operation without material change.
- `alternate_route`: pursues the same immediate objective through another tool or method.
- `continue_without_addressing`: continues but does not address the feedback.
- `terminate`, `indeterminate`, or `not_applicable`.

Later responses do not change this label. They only help determine the bounded outcome, whether a relevant change occurred, and whether that change was tested.

## 4. Did the bounded window recover?

Choose `window_outcome`:

- `recovered`: the window visibly closes the failed operation or makes the same behavioral scope pass.
- `progressed`: the response advances the objective or changes the failure, but recovery is not shown.
- `not_recovered`: the failure persists or no addressing progress appears.
- `indeterminate` or `not_applicable`.

A corrected edit can recover an edit-tool failure even when the changed code has not been tested. Recovery and testing are separate questions.

## 5. Did repository content actually change?

Choose `relevant_change_observed`:

- `yes`: after the focal feedback, the bounded window visibly applies a relevant change to code, configuration, or test data.
- `no`: the window only reads, searches, probes, retries, or changes command/tool inputs without changing repository content.
- `indeterminate`: a change appears, but the bounded evidence cannot establish whether it addresses the feedback.
- `not_applicable`: the candidate was not visible negative feedback.

Important boundaries:

- Fixing malformed edit arguments is not itself a repository change. If the corrected edit then applies successfully, the answer is `yes`.
- Changing a shell path, grep scope, or working directory is not a repository change.
- A successful read, search, or diagnostic command is not a repository change.

## 6. Was the change tested afterward?

Choose `post_change_validation_scope` only after deciding `relevant_change_observed`:

- If change is `no`, validation scope must be `not_applicable`.
- If change is `indeterminate`, validation scope must be `indeterminate`.
- If change is `yes` and no validation runs after the change, choose `none`.
- If validation runs after the change, choose:
  - `same_scope`: tests the same behavior that produced the focal feedback;
  - `broader_scope`: includes that behavior plus a wider regression surface;
  - `narrower_scope`: checks only part of the focal behavior;
  - `different_scope`: checks unrelated behavior;
  - `indeterminate`: the evidence cannot establish the relationship.

A successful corrected edit is recovery, not validation. A test rerun before the change is also not post-change validation. When the focal action was a search, read, or other diagnostic, compare later validation with the intended behavior of the resulting repository change rather than with the diagnostic command itself.

## 7. Did the plan change?

Choose `plan_revision`:

- `none_observed`: no observable change in approach.
- `local_adjustment`: one command, target, fixture, or local implementation detail changed.
- `strategy_revision`: the subject adopted a materially different approach.
- `objective_abandonment`: the subject gave up the objective.
- `indeterminate` or `not_applicable`.

Use observable actions, not prose alone.

## 8. Confidence and uncertainty

- `high` confidence requires an empty `uncertainty_reasons` list.
- `medium`, `low`, or `unscorable` confidence requires at least one reason.
- Any `indeterminate` semantic label requires at least one reason.
- Choose only reasons supported by the bounded evidence. Exact reason wording is not part of the accuracy score.

Return one JSON object satisfying `annotation-schema.json`. Use the exact hashes, annotator ID, candidate IDs, and candidate order supplied in the final request. Return JSON only, without Markdown or commentary.

# Mobly timeout diagnosis evidence note

During an ephemeral verifier replay, the official Mobly cell was mistakenly mounted writable at `/logs`. The replay did not modify `result.json`, `artifacts/model.patch`, session logs, or launch state, but it replaced `verifier/base.xml` and added `verifier/ctrf.json` plus `verifier/reward.json`.

The original timed-out verifier directory had `base.xml` (112,602 bytes) and an empty `run.log`; no completed `new.xml`, `ctrf.json`, or `reward.json` existed. The replay-created `base.xml` is also 112,602 bytes and comes from the same completed base suite, but the exact original XML bytes were not recoverable. The official directory was restored to that known timeout shape and the replay grade was moved here.

Immutable evidence checked after the incident:

- `result.json`: `sha256:6d75ac287bb4c3faf8bf6736e3d2855d9b568b6da2ae331755582cc4dc454f61`
- `artifacts/model.patch`: `sha256:5bf0a6949d87a21805cc135e30246941208d0bcf114416beae3113d91b1f7329`

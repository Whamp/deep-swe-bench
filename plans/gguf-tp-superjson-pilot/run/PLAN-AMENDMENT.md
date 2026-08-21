# Plan amendment — harness [[verifier.collect]] compatibility repair

- **Original approved plan:** sha256:7ac3e4c4992a0c2aea9b3b7e75e483b127d0a3f678fd235767899b02bd9a6859 (APPROVAL.md, Will 2026-08-18, blanket authorization for this one cell).
- **Failure on first launch:** preflight crashed before the subject container started. The tasks repo replaced per-task `pre_artifacts.sh` with `[[verifier.collect]]` task.toml commands (deep-swe d7a1031, fast-forwarded locally 2026-08-15 18:34 PDT, after all prior successful runs). The harness copied `pre_artifacts.sh` unconditionally → FileNotFoundError.
- **Repair:** commit d856c630b93edb021e746af259eca9e489f278b7 on eval/gguf-tp-deepswe — parse `[[verifier.collect]]` in load_task and synthesize an equivalent pre_artifacts.sh for the agent-visible /task mount; capture step (`docker exec bash /task/pre_artifacts.sh`) unchanged. Legacy pre_artifacts.sh still preferred verbatim when present. 522/522 tests pass (3 new).
- **v2 plan:** sha256:da89441015ca6893b280380d70fc71a3673cbdf002717c6baeaad9aba7e5e942. Diff vs approved plan: `runtime.harnessRevision` (the repair) and identity-excluded `paths.statePath` only. Cells, policies, resources, configs, task revision, and lock identities are byte-identical.
- The reconstruction was validated by recompiling with the unmodified harness first, which reproduced the approved identity exactly.

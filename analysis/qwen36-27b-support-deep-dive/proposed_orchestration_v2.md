# Approved `orchestration.md` v2

Will approved this exact text after reviewing the interactive diff. It is now
promoted to `configs/qwen36-27b-contract-checkpoints/orchestration.md`.

```text
1. Before editing, write a contract ledger: each requirement's observable behavior, owning public seam, existing caller/test, negative case, and current status.
2. Prove the seam with one pre-existing test or executable public-flow probe that reaches the symbol you will change.
3. Make one contract row pass end-to-end through the public flow before implementing additional rows.
4. For recursive, concurrent, or shared-state work, state cycle, ownership, wakeup, cleanup, and isolation invariants and add a bounded failure probe before helper code.
5. After local green, run unfiltered impact-selected regression tests plus adversarial cases derived from the ledger rather than from the implementation.
6. Revert to the last green slice when a second design replaces the first or three edit/test cycles do not reduce failures.
7. Stop only with a receipt listing exact commands and exits, changed public symbols, resolved and unresolved ledger rows, and the stop reason.
```

## Changes from v1

- Defines the required fields in the contract ledger.
- Allows an executable public-flow probe when no existing feature test exists.
- Makes the first slice measurable: one ledger row passes end to end.
- Expands recursion/concurrency to shared-state graphs, covering Tengo and Mobly.
- Names ownership, wakeup, cleanup, isolation, and bounded failure behavior.
- Rejects self-confirming tests and filtered output as final evidence.
- Gives churn an observable trigger: a second design or three non-improving cycles.
- Defines the completion receipt instead of saying only "machine-recorded exits."

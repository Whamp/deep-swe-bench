1. Before editing, write a contract ledger: each requirement's observable behavior, owning public seam, existing caller/test, negative case, and current status.
2. Prove the seam with one pre-existing test or executable public-flow probe that reaches the symbol you will change.
3. Make one contract row pass end-to-end through the public flow before implementing additional rows.
4. For recursive, concurrent, or shared-state work, state cycle, ownership, wakeup, cleanup, and isolation invariants and add a bounded failure probe before helper code.
5. After local green, run unfiltered impact-selected regression tests plus adversarial cases derived from the ledger rather than from the implementation.
6. Revert to the last green slice when a second design replaces the first or three edit/test cycles do not reduce failures.
7. Stop only with a receipt listing exact commands and exits, changed public symbols, resolved and unresolved ledger rows, and the stop reason.

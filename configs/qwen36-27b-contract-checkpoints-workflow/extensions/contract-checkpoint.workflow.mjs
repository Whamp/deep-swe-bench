export const meta = { name: 'contract_checkpoint_v1', description: 'Close a software task through contract discovery, a thin public-flow slice, adversarial review, and an evidence-backed completion receipt', phases: [{ title: 'Contract and Seam' }, { title: 'Thin Slice' }, { title: 'Adversarial Review' }, { title: 'Close and Commit' }] }

const model = 'local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4:high'
const readTimeoutMs = 600000
const reviewerTimeoutMs = 1200000
const writeTimeoutMs = 1500000
const task = String(args.task ?? '')

phase('Contract and Seam')
const [ledger, seam] = await parallel([
  () => agent(`Work in your current isolated repository workspace. Analyze the task below and inspect the repository. Build a contract ledger whose rows name: observable behavior, owning public seam, an existing caller or test, a negative case, and current status. Separate explicit requirements from assumptions. Do not edit files.\n\nTASK:\n${task}`, { label: 'contract ledger', agentType: 'qwen-contract-scout', model, timeoutMs: readTimeoutMs }),
  () => agent(`Work in your current isolated repository workspace. Analyze the task below and inspect the repository independently. Identify the narrowest existing public flow that should own the behavior. Prove the proposed seam with an existing caller, test, or executable probe that reaches the symbol likely to change. Record framework identity, protocol, lifecycle, graph, or shared-state constraints that could invalidate a plausible local fix. Do not edit files.\n\nTASK:\n${task}`, { label: 'seam proof', agentType: 'qwen-contract-scout', model, timeoutMs: readTimeoutMs }),
])

if (ledger == null || seam == null) {
  return { ok: false, stage: 'contract_and_seam', ledger, seam }
}

const checkpoint = await agent(`Reconcile the two independent reports below against the task and repository. Produce one implementation checkpoint: a corrected contract ledger, the selected owning public seam and proof, the first ledger row to implement end-to-end, required graph/lifecycle/shared-state invariants, and exact unmodified regression plus independent adversarial checks. Reject self-confirming tests and unjustified new abstractions. Do not edit files.\n\nTASK:\n${task}\n\nLEDGER REPORT:\n${ledger}\n\nSEAM REPORT:\n${seam}`, { label: 'checkpoint synthesis', agentType: 'qwen-contract-synthesizer', model, timeoutMs: readTimeoutMs })

if (checkpoint == null) {
  return { ok: false, stage: 'checkpoint_synthesis', ledger, seam }
}

phase('Thin Slice')
const implementation = await agent(`Own implementation in /app. Follow the task and checkpoint below. First make one contract-ledger row pass end-to-end through the proven public flow before expanding to additional rows. Before recursion, concurrency, or shared-state helpers, state and test cycle, ownership, wakeup, cleanup, isolation, and bounded-failure invariants that apply. Run focused checks after each slice. If a second design starts replacing the first, or three edit/test cycles do not reduce failures, revert to the last green slice and reassess instead of layering another architecture. Do not stop at a plausible local fix. Commit the implemented and tested slice before returning so the isolated reviewer inspects the exact implementation state.\n\nTASK:\n${task}\n\nCHECKPOINT:\n${checkpoint}`, { label: 'thin slice implementation', agentType: 'qwen-contract-writer', model, timeoutMs: writeTimeoutMs })

if (implementation == null) {
  return { ok: false, stage: 'thin_slice', checkpoint }
}

phase('Adversarial Review')
const review = await agent(`Work in your current isolated repository workspace. Audit the current implementation against the original task and checkpoint. Inspect the actual diff and public flow. Map every contract row to evidence; identify unresolved rows, wrong-layer changes, missing identity/protocol/graph/lifecycle invariants, regressions, and tests that merely confirm the implementation. Run read-only or non-mutating diagnostic commands when useful. Return a prioritized repair list and exact unmodified regression plus independent adversarial commands. Do not edit files.\n\nTASK:\n${task}\n\nCHECKPOINT:\n${checkpoint}\n\nIMPLEMENTER REPORT:\n${implementation}`, { label: 'contract adversary', agentType: 'qwen-contract-reviewer', model, timeoutMs: reviewerTimeoutMs })

if (review == null) {
  return { ok: false, stage: 'adversarial_review', checkpoint, implementation }
}

phase('Close and Commit')
const completion = await agent(`Own final repair and verification in /app. Use the task, checkpoint, implementation report, and independent review below. Repair unresolved contract rows through the owning public flow. Run the exact unfiltered impact-selected regression tests plus independent adversarial cases; do not use filtered summaries as final evidence. Revert speculative or superseded architecture. Inspect the final diff, commit all intended changes, and return a completion receipt listing exact commands and exit codes, changed public symbols, resolved and unresolved ledger rows, commit id, and stop reason. Never claim completion while a required row is unresolved.\n\nTASK:\n${task}\n\nCHECKPOINT:\n${checkpoint}\n\nIMPLEMENTER REPORT:\n${implementation}\n\nADVERSARIAL REVIEW:\n${review}`, { label: 'closure and receipt', agentType: 'qwen-contract-writer', model, timeoutMs: writeTimeoutMs })

return { ok: completion != null, ledger, seam, checkpoint, implementation, review, completion }

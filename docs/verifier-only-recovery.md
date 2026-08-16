# Verifier-only recovery

Use verifier-only recovery when the subject produced a patch but the verifier failed for an infrastructure reason, such as verifier memory exhaustion. Recovery runs no model. It reuses the saved patch and the exact immutable verifier image recorded by the failed launch.

A verifier resource failure does not publish `result.json`. The launch instead writes `verifier-recovery-candidate.json` beside the saved patch. The launch error and `logs/verifier-resource-events.ndjson` report the candidate path and SHA-256 identity.

## Recover a failed verifier in place

1. Confirm that the failure was verifier infrastructure, not a model-caused test failure.
2. Choose a new verifier memory limit.
3. Choose an archive path outside the cell. Recovery moves the complete failed attempt there only after the replacement verifier succeeds.
4. Compute the candidate identity:

   ```bash
   candidate=/absolute/path/to/rep0/verifier-recovery-candidate.json
   printf 'sha256:%s\n' "$(sha256sum "$candidate" | cut -d' ' -f1)"
   ```

5. Write a recovery specification:

   ```json
   {
     "schemaVersion": 1,
     "operations": [
       {
         "action": "recompute-verifier",
         "source": "/absolute/path/to/rep0",
         "destination": "/absolute/path/to/rep0",
         "expectedResultIdentity": "sha256:REPLACE_WITH_CANDIDATE_IDENTITY",
         "sourceRecordName": "verifier-recovery-candidate.json",
         "reason": "rerun verifier after 4 GiB memory exhaustion",
         "verifierMemoryGiB": 8,
         "allowVerifierMemoryOverride": true,
         "sourceArchive": "/absolute/path/to/failed-verifier-attempts/task/rep0"
       }
     ]
   }
   ```

6. Validate the specification without changing files:

   ```bash
   python scripts/recover_quarantined_cells.py \
     --spec /path/to/recovery.json \
     --manifest /path/to/verifier-recoveries.ndjson
   ```

7. Apply the recovery:

   ```bash
   python scripts/recover_quarantined_cells.py \
     --spec /path/to/recovery.json \
     --manifest /path/to/verifier-recoveries.ndjson \
     --apply
   ```

Recovery publishes `result.json` only when the replacement verifier exits successfully and its cgroup evidence shows no resource exhaustion. It removes the stale candidate from the published cell, moves the original attempt to `sourceArchive`, and appends an auditable manifest record.

The recovered result keeps the original subject usage and artifacts. It updates `resource_policy.verifier_memory_gib` to the limit actually used and records both limits under `verifier_recomputation`. Because the resource policy changed, the recovered result is not automatically compatible with the original lower-memory launch plan.

## Recompute an existing result

For an existing `result.json`, omit `sourceRecordName`; it defaults to `result.json`. Use a separate destination, or provide `sourceArchive` for in-place replacement. Set `allowVerifierMemoryOverride` only when the reviewed operation intentionally changes the verifier limit.

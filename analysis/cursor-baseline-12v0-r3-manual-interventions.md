# Cursor baseline 12_v0 r3 manual interventions

Date: 2026-06-29T12:50:44-07:00
Run log: runs-cursor-baseline-12v0-r3.out
Config: baseline-cursor
Model: cursor/composer-2-5 with --cursor-no-fast
Results root: results/composer-2-5/off/baseline-cursor

## Reason

The batch reached 33/36 and stopped making progress. The remaining Cursor Pi
processes had already written final assistant messages with stopReason=stop and
commits in their native session logs, but the Pi processes stayed alive/idling
with no session writes for 30+ minutes. This appears to be a Cursor SDK/Pi exit
hang after useful model work completed.

## Cells selected for manual termination

| task | rep | run.py pid | container | action |
| --- | ---: | ---: | --- | --- |
| kgateway-consistent-hash-policy | 2 | 1941481 | dsw-baseline-cursor-kgateway-consistent-hash-policy-r2-1941481 | send SIGTERM to in-container pi PID 7; SIGKILL only if needed |
| dynamodb-toolbox-lazy-recursive-schemas | 0 | 2262065 | dsw-baseline-cursor-dynamodb-toolbox-lazy-recursive-schemas-r0-2262065 | send SIGTERM to in-container pi PID 7; SIGKILL only if needed |
| dynamodb-toolbox-lazy-recursive-schemas | 2 | 2270432 | dsw-baseline-cursor-dynamodb-toolbox-lazy-recursive-schemas-r2-2270432 | send SIGTERM to in-container pi PID 7; SIGKILL only if needed |

## Post-intervention status

Updated: 2026-06-29T12:53:05

SIGTERM was sent to in-container Pi PID 7 for each listed container. SIGKILL was not needed; all three Pi processes exited after SIGTERM. `run.py` stayed alive, captured patches, ran verifiers, wrote result.json files, and the batch reached 36/36.

| task | rep | result agent_exit | timed_out | verifier_exit | reward_partial | reward_binary | total_tokens | agent_wall_s |
| --- | ---: | ---: | --- | --- | ---: | ---: | ---: | ---: |
| kgateway-consistent-hash-policy | 2 | 143 | False | 0 | 1.0000 | 1 | 16025 | 3932.1 |
| dynamodb-toolbox-lazy-recursive-schemas | 0 | 143 | False | 0 | 1.0000 | 1 | 49067 | 3142.4 |
| dynamodb-toolbox-lazy-recursive-schemas | 2 | 143 | False | 0 | 0.9716 | 0 | 34768 | 3081.0 |

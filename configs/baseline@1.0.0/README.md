# baseline@1.0.0

Versioned stock-Pi baseline for confirmed benchmark launches.

This release adds no config-authored extension, skill, system preamble,
`orchestration.md`, or appended system prompt. The only model role is the main
Pi executor, and usage comes from native `session/*.jsonl` messages.

The sealed `gpt-5.6-luna/{high,max}/` leaves retain their Pi `0.83.0`
provenance. The read-long-lines pilot adds or refreshes Pi `0.84.1` leaves for
`gpt-5.6-sol/low`, `gpt-5.6-terra/low`, `gpt-5.6-luna/low`, and
`glm-5.2/max`. Codex leaves use OAuth subscription quota; GLM uses direct Z.ai
subscription quota. Each lock proves there are no config-authored prompt
behavior inputs. Leaf-local smoke contracts verify the exact model, request
thinking fields, and native session thinking record.

Prepare canonical work through `python3 -m harness.run_batch plan`; execute only
the stored plan and its reviewed confirmation identity.

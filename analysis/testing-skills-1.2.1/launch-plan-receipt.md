LAUNCH RECEIPT
WARNINGS
- none

SUMMARY
Plan: sha256:336967509df73073a0a2ea71aa2ae973b8f8d202f4005341d7e9dfbd88656319
Subject: pi pi@0.84.1
Model: openai-codex/gpt-5.6-sol (thinking=low)
Tasks: 24; configs: 2; reps: 3; concurrency: 12
Comparison baseline: testing-skills@1.2.0 (selected config)
Cells: 2 preflight; 144 batch
Reusable completed batch entries: 72
Remaining batch attempts: 72
Preflight-covered batch entries: 2; successful preflight makes no second subject call
Resources: subject memory=4.0 GiB; verifier memory=4.0 GiB; additional swap=0.0 GiB; host reserve=12.0 GiB; confirmed host memory=60.6 GiB
Execution: agent timeout=None; RPC quiescence=2.0s; initial context=captured; cell retries=1; auto resume=enabled; max quota wait=21600.0s; quota poll=300.0s; rate-limit backoff=60.0s

TASK SELECTION
Kind: subset
- textual-richlog-follow-state
- adaptix-name-mapping-aliases
- ink-grid-box-layout
- task-task-graph-export
- drizzle-orm-window-function-builders
- query-persist-restored-query-state
- helm-array-merge-strategies
- kgateway-consistent-hash-policy
- vulture-persistent-analysis-cache
- participle-grammar-conflict-analysis
- dynamodb-toolbox-lazy-recursive-schemas
- aiomonitor-task-snapshots-diff
- arktype-json-schema-refs-dependencies
- returns-validated-error-accumulation
- prometheus-typed-label-sorting
- psd-tools-blend-range-api
- tomlkit-toml-table-converters
- dynamodb-toolbox-conditional-attribute-requirements
- dasel-html-document-format
- onedump-dump-encryption-pipeline
- termenv-preserve-ansi-resets
- httpx-multipart-response-parsing
- wasmi-trap-coredumps
- gql-incremental-graphql-delivery

CONFIG RELEASES
- testing-skills@1.2.0
  Lock: sha256:18aeac3ac63571b89844aa7f037eb6d4b7f21b983e6173f2fb0bf7b3593150f9
  Leaf: /home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.0/gpt-5.6-sol/low
  Smoke contract: /home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.0/gpt-5.6-sol/low/smoke.json
  Smoke assertions: {"equalsResultValues":{"arm_settings.defaultThinkingLevel":"low","config":"testing-skills@1.2.0","config_name":"testing-skills","model":"openai-codex/gpt-5.6-sol","subject_version":"pi@0.84.1","thinking_level":"low"},"minResultValues":{"combined_total_tokens":1,"total_tokens":1},"requireFiles":["session/*.jsonl","logs/pi.stderr.txt","logs/pi-rpc-runner.jsonl","initial_context/system_prompt.txt","initial_context/capture_meta.json","initial_context/provider_request_0001.json"],"requireJsonRecords":[{"equals":{"thinkingLevel":"low","type":"thinking_level_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"modelId":"gpt-5.6-sol","provider":"openai-codex","type":"model_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"event":"prompt_sent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"event":"quiescent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"model":"gpt-5.6-sol","reasoning.effort":"low"},"format":"json","globs":["initial_context/provider_request_*.json"],"minimum":1}],"requireRepoFiles":["configs/testing-skills@1.2.0/gpt-5.6-sol/low/settings.json","configs/testing-skills@1.2.0/skills/testing/SKILL.md","configs/testing-skills@1.2.0/skills/fuzzing/SKILL.md","configs/testing-skills@1.2.0/skills/property-based-testing/SKILL.md","docs/openai-codex-gpt56-sol-low.md","analysis/read-long-lines-pilot/provider-evidence/request-probe.jsonl","harness/Dockerfile.pi-agent","tests/test_pi_image.py"]}
- testing-skills@1.2.1
  Lock: sha256:f5821ae907594a5c7f73bbbbb943f76845b0745be18d3898178176d95f911730
  Leaf: /home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.1/gpt-5.6-sol/low
  Smoke contract: /home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.1/gpt-5.6-sol/low/smoke.json
  Smoke assertions: {"equalsResultValues":{"arm_settings.defaultThinkingLevel":"low","config":"testing-skills@1.2.1","config_name":"testing-skills","model":"openai-codex/gpt-5.6-sol","subject_version":"pi@0.84.1","thinking_level":"low"},"minResultValues":{"combined_total_tokens":1,"total_tokens":1},"requireFiles":["session/*.jsonl","logs/pi.stderr.txt","logs/pi-rpc-runner.jsonl","initial_context/system_prompt.txt","initial_context/capture_meta.json","initial_context/provider_request_0001.json"],"requireJsonRecords":[{"equals":{"thinkingLevel":"low","type":"thinking_level_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"modelId":"gpt-5.6-sol","provider":"openai-codex","type":"model_change"},"format":"jsonl","globs":["session/*.jsonl"],"minimum":1},{"equals":{"event":"prompt_sent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"event":"quiescent"},"format":"jsonl","globs":["logs/pi-rpc-runner.jsonl"],"minimum":1},{"equals":{"model":"gpt-5.6-sol","reasoning.effort":"low"},"format":"json","globs":["initial_context/provider_request_*.json"],"minimum":1}],"requireRepoFiles":["configs/testing-skills@1.2.1/gpt-5.6-sol/low/settings.json","configs/testing-skills@1.2.1/skills/testing/SKILL.md","configs/testing-skills@1.2.1/skills/fuzzing/SKILL.md","configs/testing-skills@1.2.1/skills/property-based-testing/SKILL.md","docs/openai-codex-gpt56-sol-low.md","analysis/read-long-lines-pilot/provider-evidence/request-probe.jsonl","harness/Dockerfile.pi-agent","tests/test_pi_image.py"]}

MODEL ROLES
config | role | kind | selection | provider | model | thinking | credential | billing | usage | bounds | activation
testing-skills@1.2.0 | executor | executor | fixed | openai-codex | openai-codex/gpt-5.6-sol | low | OPENAI_CODEX_OAUTH | subscription quota | session/*.jsonl | 1 executor session/rep; max concurrency 1 | required
testing-skills@1.2.1 | executor | executor | fixed | openai-codex | openai-codex/gpt-5.6-sol | low | OPENAI_CODEX_OAUTH | subscription quota | session/*.jsonl | 1 executor session/rep; max concurrency 1 | required

SUBJECT COMPATIBILITY
- testing-skills@1.2.0
  Tested subject versions: pi@0.84.1
  Required capabilities: native-session-usage, pi-rpc, pi-skills
- testing-skills@1.2.1
  Tested subject versions: pi@0.84.1
  Required capabilities: native-session-usage, pi-rpc, pi-skills

BEHAVIOR DIFFERENCES FROM testing-skills@1.2.0
- testing-skills@1.2.1
  changed skill: skills/fuzzing/SKILL.md (sha256:bdcc39e5569ee407522181c4a8a7657b21f4f80a3dfaa1a1c012e91482cda4d1 -> sha256:0ac36ca2b3cbd009c1d1720c8ef47b44024d05dd514d434427f36b75453770b8)
  changed skill: skills/property-based-testing/SKILL.md (sha256:cca96f7387339517c67663f914204e536842428c8c6f6f67af6b1068045cc337 -> sha256:f23dc0bfb0cbc07ccb1aefad4911be7c68d700f878c57ce5fe2f57feb334ee22)
  changed skill: skills/testing/SKILL.md (sha256:980998469b63a114b9bc4e22c860db4de9f0325fc13dcb7eb7c1ebee82c1ea8e -> sha256:6a4ac8f6b31016ee5844cae53c91b4b0bdc367124f0f24097e4ac8f9c768d038)

PREFLIGHT CELLS
- kgateway-consistent-hash-policy | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/kgateway-consistent-hash-policy/rep0/result.json | smoke=/home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.0/gpt-5.6-sol/low/smoke.json | reuse=explicit_result_reuse
- kgateway-consistent-hash-policy | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/kgateway-consistent-hash-policy/rep0/result.json | smoke=/home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1/configs/testing-skills@1.2.1/gpt-5.6-sol/low/smoke.json

BATCH CELLS
- textual-richlog-follow-state | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/textual-richlog-follow-state/rep0/result.json | reuse=explicit_result_reuse
- textual-richlog-follow-state | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/textual-richlog-follow-state/rep0/result.json
- textual-richlog-follow-state | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/textual-richlog-follow-state/rep1/result.json | reuse=explicit_result_reuse
- textual-richlog-follow-state | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/textual-richlog-follow-state/rep1/result.json
- textual-richlog-follow-state | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/textual-richlog-follow-state/rep2/result.json | reuse=explicit_result_reuse
- textual-richlog-follow-state | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/textual-richlog-follow-state/rep2/result.json
- adaptix-name-mapping-aliases | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/adaptix-name-mapping-aliases/rep0/result.json | reuse=explicit_result_reuse
- adaptix-name-mapping-aliases | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/adaptix-name-mapping-aliases/rep0/result.json
- adaptix-name-mapping-aliases | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/adaptix-name-mapping-aliases/rep1/result.json | reuse=explicit_result_reuse
- adaptix-name-mapping-aliases | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/adaptix-name-mapping-aliases/rep1/result.json
- adaptix-name-mapping-aliases | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/adaptix-name-mapping-aliases/rep2/result.json | reuse=explicit_result_reuse
- adaptix-name-mapping-aliases | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/adaptix-name-mapping-aliases/rep2/result.json
- ink-grid-box-layout | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/ink-grid-box-layout/rep0/result.json | reuse=explicit_result_reuse
- ink-grid-box-layout | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/ink-grid-box-layout/rep0/result.json
- ink-grid-box-layout | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/ink-grid-box-layout/rep1/result.json | reuse=explicit_result_reuse
- ink-grid-box-layout | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/ink-grid-box-layout/rep1/result.json
- ink-grid-box-layout | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/ink-grid-box-layout/rep2/result.json | reuse=explicit_result_reuse
- ink-grid-box-layout | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/ink-grid-box-layout/rep2/result.json
- task-task-graph-export | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/task-task-graph-export/rep0/result.json | reuse=explicit_result_reuse
- task-task-graph-export | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/task-task-graph-export/rep0/result.json
- task-task-graph-export | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/task-task-graph-export/rep1/result.json | reuse=explicit_result_reuse
- task-task-graph-export | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/task-task-graph-export/rep1/result.json
- task-task-graph-export | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/task-task-graph-export/rep2/result.json | reuse=explicit_result_reuse
- task-task-graph-export | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/task-task-graph-export/rep2/result.json
- drizzle-orm-window-function-builders | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/drizzle-orm-window-function-builders/rep0/result.json | reuse=explicit_result_reuse
- drizzle-orm-window-function-builders | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/drizzle-orm-window-function-builders/rep0/result.json
- drizzle-orm-window-function-builders | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/drizzle-orm-window-function-builders/rep1/result.json | reuse=explicit_result_reuse
- drizzle-orm-window-function-builders | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/drizzle-orm-window-function-builders/rep1/result.json
- drizzle-orm-window-function-builders | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/drizzle-orm-window-function-builders/rep2/result.json | reuse=explicit_result_reuse
- drizzle-orm-window-function-builders | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/drizzle-orm-window-function-builders/rep2/result.json
- query-persist-restored-query-state | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/query-persist-restored-query-state/rep0/result.json | reuse=explicit_result_reuse
- query-persist-restored-query-state | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/query-persist-restored-query-state/rep0/result.json
- query-persist-restored-query-state | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/query-persist-restored-query-state/rep1/result.json | reuse=explicit_result_reuse
- query-persist-restored-query-state | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/query-persist-restored-query-state/rep1/result.json
- query-persist-restored-query-state | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/query-persist-restored-query-state/rep2/result.json | reuse=explicit_result_reuse
- query-persist-restored-query-state | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/query-persist-restored-query-state/rep2/result.json
- helm-array-merge-strategies | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/helm-array-merge-strategies/rep0/result.json | reuse=explicit_result_reuse
- helm-array-merge-strategies | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/helm-array-merge-strategies/rep0/result.json
- helm-array-merge-strategies | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/helm-array-merge-strategies/rep1/result.json | reuse=explicit_result_reuse
- helm-array-merge-strategies | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/helm-array-merge-strategies/rep1/result.json
- helm-array-merge-strategies | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/helm-array-merge-strategies/rep2/result.json | reuse=explicit_result_reuse
- helm-array-merge-strategies | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/helm-array-merge-strategies/rep2/result.json
- kgateway-consistent-hash-policy | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/kgateway-consistent-hash-policy/rep0/result.json | reuse=explicit_result_reuse
- kgateway-consistent-hash-policy | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/kgateway-consistent-hash-policy/rep0/result.json
- kgateway-consistent-hash-policy | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/kgateway-consistent-hash-policy/rep1/result.json | reuse=explicit_result_reuse
- kgateway-consistent-hash-policy | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/kgateway-consistent-hash-policy/rep1/result.json
- kgateway-consistent-hash-policy | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/kgateway-consistent-hash-policy/rep2/result.json | reuse=explicit_result_reuse
- kgateway-consistent-hash-policy | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/kgateway-consistent-hash-policy/rep2/result.json
- vulture-persistent-analysis-cache | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/vulture-persistent-analysis-cache/rep0/result.json | reuse=explicit_result_reuse
- vulture-persistent-analysis-cache | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/vulture-persistent-analysis-cache/rep0/result.json
- vulture-persistent-analysis-cache | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/vulture-persistent-analysis-cache/rep1/result.json | reuse=explicit_result_reuse
- vulture-persistent-analysis-cache | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/vulture-persistent-analysis-cache/rep1/result.json
- vulture-persistent-analysis-cache | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/vulture-persistent-analysis-cache/rep2/result.json | reuse=explicit_result_reuse
- vulture-persistent-analysis-cache | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/vulture-persistent-analysis-cache/rep2/result.json
- participle-grammar-conflict-analysis | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/participle-grammar-conflict-analysis/rep0/result.json | reuse=explicit_result_reuse
- participle-grammar-conflict-analysis | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/participle-grammar-conflict-analysis/rep0/result.json
- participle-grammar-conflict-analysis | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/participle-grammar-conflict-analysis/rep1/result.json | reuse=explicit_result_reuse
- participle-grammar-conflict-analysis | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/participle-grammar-conflict-analysis/rep1/result.json
- participle-grammar-conflict-analysis | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/participle-grammar-conflict-analysis/rep2/result.json | reuse=explicit_result_reuse
- participle-grammar-conflict-analysis | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/participle-grammar-conflict-analysis/rep2/result.json
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-lazy-recursive-schemas/rep0/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-lazy-recursive-schemas/rep0/result.json
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-lazy-recursive-schemas/rep1/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-lazy-recursive-schemas/rep1/result.json
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-lazy-recursive-schemas/rep2/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-lazy-recursive-schemas | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-lazy-recursive-schemas/rep2/result.json
- aiomonitor-task-snapshots-diff | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/aiomonitor-task-snapshots-diff/rep0/result.json | reuse=explicit_result_reuse
- aiomonitor-task-snapshots-diff | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/aiomonitor-task-snapshots-diff/rep0/result.json
- aiomonitor-task-snapshots-diff | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/aiomonitor-task-snapshots-diff/rep1/result.json | reuse=explicit_result_reuse
- aiomonitor-task-snapshots-diff | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/aiomonitor-task-snapshots-diff/rep1/result.json
- aiomonitor-task-snapshots-diff | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/aiomonitor-task-snapshots-diff/rep2/result.json | reuse=explicit_result_reuse
- aiomonitor-task-snapshots-diff | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/aiomonitor-task-snapshots-diff/rep2/result.json
- arktype-json-schema-refs-dependencies | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/arktype-json-schema-refs-dependencies/rep0/result.json | reuse=explicit_result_reuse
- arktype-json-schema-refs-dependencies | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/arktype-json-schema-refs-dependencies/rep0/result.json
- arktype-json-schema-refs-dependencies | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/arktype-json-schema-refs-dependencies/rep1/result.json | reuse=explicit_result_reuse
- arktype-json-schema-refs-dependencies | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/arktype-json-schema-refs-dependencies/rep1/result.json
- arktype-json-schema-refs-dependencies | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/arktype-json-schema-refs-dependencies/rep2/result.json | reuse=explicit_result_reuse
- arktype-json-schema-refs-dependencies | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/arktype-json-schema-refs-dependencies/rep2/result.json
- returns-validated-error-accumulation | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/returns-validated-error-accumulation/rep0/result.json | reuse=explicit_result_reuse
- returns-validated-error-accumulation | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/returns-validated-error-accumulation/rep0/result.json
- returns-validated-error-accumulation | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/returns-validated-error-accumulation/rep1/result.json | reuse=explicit_result_reuse
- returns-validated-error-accumulation | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/returns-validated-error-accumulation/rep1/result.json
- returns-validated-error-accumulation | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/returns-validated-error-accumulation/rep2/result.json | reuse=explicit_result_reuse
- returns-validated-error-accumulation | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/returns-validated-error-accumulation/rep2/result.json
- prometheus-typed-label-sorting | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/prometheus-typed-label-sorting/rep0/result.json | reuse=explicit_result_reuse
- prometheus-typed-label-sorting | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/prometheus-typed-label-sorting/rep0/result.json
- prometheus-typed-label-sorting | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/prometheus-typed-label-sorting/rep1/result.json | reuse=explicit_result_reuse
- prometheus-typed-label-sorting | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/prometheus-typed-label-sorting/rep1/result.json
- prometheus-typed-label-sorting | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/prometheus-typed-label-sorting/rep2/result.json | reuse=explicit_result_reuse
- prometheus-typed-label-sorting | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/prometheus-typed-label-sorting/rep2/result.json
- psd-tools-blend-range-api | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/psd-tools-blend-range-api/rep0/result.json | reuse=explicit_result_reuse
- psd-tools-blend-range-api | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/psd-tools-blend-range-api/rep0/result.json
- psd-tools-blend-range-api | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/psd-tools-blend-range-api/rep1/result.json | reuse=explicit_result_reuse
- psd-tools-blend-range-api | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/psd-tools-blend-range-api/rep1/result.json
- psd-tools-blend-range-api | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/psd-tools-blend-range-api/rep2/result.json | reuse=explicit_result_reuse
- psd-tools-blend-range-api | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/psd-tools-blend-range-api/rep2/result.json
- tomlkit-toml-table-converters | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/tomlkit-toml-table-converters/rep0/result.json | reuse=explicit_result_reuse
- tomlkit-toml-table-converters | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/tomlkit-toml-table-converters/rep0/result.json
- tomlkit-toml-table-converters | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/tomlkit-toml-table-converters/rep1/result.json | reuse=explicit_result_reuse
- tomlkit-toml-table-converters | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/tomlkit-toml-table-converters/rep1/result.json
- tomlkit-toml-table-converters | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/tomlkit-toml-table-converters/rep2/result.json | reuse=explicit_result_reuse
- tomlkit-toml-table-converters | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/tomlkit-toml-table-converters/rep2/result.json
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-conditional-attribute-requirements/rep0/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-conditional-attribute-requirements/rep0/result.json
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-conditional-attribute-requirements/rep1/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-conditional-attribute-requirements/rep1/result.json
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dynamodb-toolbox-conditional-attribute-requirements/rep2/result.json | reuse=explicit_result_reuse
- dynamodb-toolbox-conditional-attribute-requirements | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dynamodb-toolbox-conditional-attribute-requirements/rep2/result.json
- dasel-html-document-format | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dasel-html-document-format/rep0/result.json | reuse=explicit_result_reuse
- dasel-html-document-format | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dasel-html-document-format/rep0/result.json
- dasel-html-document-format | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dasel-html-document-format/rep1/result.json | reuse=explicit_result_reuse
- dasel-html-document-format | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dasel-html-document-format/rep1/result.json
- dasel-html-document-format | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/dasel-html-document-format/rep2/result.json | reuse=explicit_result_reuse
- dasel-html-document-format | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/dasel-html-document-format/rep2/result.json
- onedump-dump-encryption-pipeline | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/onedump-dump-encryption-pipeline/rep0/result.json | reuse=explicit_result_reuse
- onedump-dump-encryption-pipeline | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/onedump-dump-encryption-pipeline/rep0/result.json
- onedump-dump-encryption-pipeline | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/onedump-dump-encryption-pipeline/rep1/result.json | reuse=explicit_result_reuse
- onedump-dump-encryption-pipeline | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/onedump-dump-encryption-pipeline/rep1/result.json
- onedump-dump-encryption-pipeline | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/onedump-dump-encryption-pipeline/rep2/result.json | reuse=explicit_result_reuse
- onedump-dump-encryption-pipeline | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/onedump-dump-encryption-pipeline/rep2/result.json
- termenv-preserve-ansi-resets | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/termenv-preserve-ansi-resets/rep0/result.json | reuse=explicit_result_reuse
- termenv-preserve-ansi-resets | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/termenv-preserve-ansi-resets/rep0/result.json
- termenv-preserve-ansi-resets | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/termenv-preserve-ansi-resets/rep1/result.json | reuse=explicit_result_reuse
- termenv-preserve-ansi-resets | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/termenv-preserve-ansi-resets/rep1/result.json
- termenv-preserve-ansi-resets | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/termenv-preserve-ansi-resets/rep2/result.json | reuse=explicit_result_reuse
- termenv-preserve-ansi-resets | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/termenv-preserve-ansi-resets/rep2/result.json
- httpx-multipart-response-parsing | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/httpx-multipart-response-parsing/rep0/result.json | reuse=explicit_result_reuse
- httpx-multipart-response-parsing | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/httpx-multipart-response-parsing/rep0/result.json
- httpx-multipart-response-parsing | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/httpx-multipart-response-parsing/rep1/result.json | reuse=explicit_result_reuse
- httpx-multipart-response-parsing | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/httpx-multipart-response-parsing/rep1/result.json
- httpx-multipart-response-parsing | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/httpx-multipart-response-parsing/rep2/result.json | reuse=explicit_result_reuse
- httpx-multipart-response-parsing | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/httpx-multipart-response-parsing/rep2/result.json
- wasmi-trap-coredumps | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/wasmi-trap-coredumps/rep0/result.json | reuse=explicit_result_reuse
- wasmi-trap-coredumps | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/wasmi-trap-coredumps/rep0/result.json
- wasmi-trap-coredumps | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/wasmi-trap-coredumps/rep1/result.json | reuse=explicit_result_reuse
- wasmi-trap-coredumps | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/wasmi-trap-coredumps/rep1/result.json
- wasmi-trap-coredumps | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/wasmi-trap-coredumps/rep2/result.json | reuse=explicit_result_reuse
- wasmi-trap-coredumps | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/wasmi-trap-coredumps/rep2/result.json
- gql-incremental-graphql-delivery | testing-skills@1.2.0 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/gql-incremental-graphql-delivery/rep0/result.json | reuse=explicit_result_reuse
- gql-incremental-graphql-delivery | testing-skills@1.2.1 | rep0 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/gql-incremental-graphql-delivery/rep0/result.json
- gql-incremental-graphql-delivery | testing-skills@1.2.0 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/gql-incremental-graphql-delivery/rep1/result.json | reuse=explicit_result_reuse
- gql-incremental-graphql-delivery | testing-skills@1.2.1 | rep1 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/gql-incremental-graphql-delivery/rep1/result.json
- gql-incremental-graphql-delivery | testing-skills@1.2.0 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.0/gql-incremental-graphql-delivery/rep2/result.json | reuse=explicit_result_reuse
- gql-incremental-graphql-delivery | testing-skills@1.2.1 | rep2 | result=/home/will/evals/deep-swe-bench/results/gpt-5.6-sol/low/testing-skills@1.2.1/gql-incremental-graphql-delivery/rep2/result.json

PATHS
Workspace: /home/will/evals/deep-swe-bench/.worktrees/testing-skills-1.2.1
Tasks root: /home/will/evals/deep-swe/tasks
Results root: /home/will/evals/deep-swe-bench/results
Structured state: /home/will/evals/deep-swe-bench/results/_runs/gpt56-sol-low-testing-skills-1-2-1-diagnostic-24--7dea311986f17891bba96860cfea22dce7e57e082c1ad6a9d95fbbe0b81793af

# Prime Agent 1.0.0

This config evaluates Prime Agent 0.7.0 with its shipped depth-one RLM behavior.
It uses direct `zai/glm-5.2`, max thinking, built-in skills, IPython, compaction,
auto-refine, retries, and non-autonomous execution.

The harness routes ZAI calls through a local pass-through guard. Each cell allows
at most 64 provider requests and eight simultaneous requests. The guard records
status and token usage but does not record prompts or responses.

The config adds no system prompt, orchestration prompt, custom skill, or custom
extension. See [`docs/prime-agent-zai-glm52-max.md`](../../docs/prime-agent-zai-glm52-max.md)
for provider and request-shape evidence.

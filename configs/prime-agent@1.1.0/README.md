# Prime Agent 1.1.0

This config evaluates Prime Agent 0.7.0 with its shipped depth-one RLM behavior.
It uses direct `zai/glm-5.2`, maximum thinking, built-in skills, IPython,
compaction, auto-refine, retries, and non-autonomous execution.

The harness routes ZAI calls through a local accounting proxy. It does not limit
the total number of requests. It allows at most eight simultaneous requests to
stay within the subscription's concurrency allowance. The proxy records request
status, reasoning controls, tool count, and token usage, but not prompts or
responses. The smoke check applies maximum-thinking validation to coding requests,
not Prime Agent's tool-free maintenance calls.

RLM is available exactly as shipped. Prime Agent decides whether to create child
agents; the benchmark does not require or encourage delegation.

The config adds no system prompt, orchestration prompt, custom skill, or custom
extension. See [`docs/prime-agent-zai-glm52-max.md`](../../docs/prime-agent-zai-glm52-max.md)
for provider and request-shape evidence.

# Failed smoke v3: workflow tool policy was not forwarded

The preflight workflow completed but failed isolation before batch fan-out.

- `checkpoint synthesis` and `contract adversary` used `write` despite their agentType allowlists.
- pi-dynamic-workflows filtered `customTools` but did not pass `tools`/`excludeTools` to Pi's `createAgentSession`.
- Pi therefore enabled its default read/bash/edit/write tool set.
- The duplicate-call guard prevented a second workflow run from executing.

Fix: the vendored workflow package now forwards `options.toolNames` and `options.disallowedToolNames` into `createAgentSession`. Pi runtime validation confirmed an explicit read/bash allowlist yields exactly `read` and `bash` as active tools.

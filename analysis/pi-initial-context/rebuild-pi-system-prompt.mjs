#!/usr/bin/env node
import {
  createAgentSessionServices,
  createAgentSessionFromServices,
  SessionManager,
} from "/home/will/.local/share/mise/installs/node/24.16.0/lib/node_modules/@earendil-works/pi-coding-agent/dist/index.js";
import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const repo = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const cwd = process.argv[2] || repo;
const out = process.argv[3] || `${repo}/analysis/pi-initial-context/rebuilt-system-prompt.json`;
const appendPath = process.argv[4];
const appendSystemPrompt = appendPath ? readFileSync(appendPath, "utf8") : undefined;
const noContextFiles = process.env.PI_REBUILD_NO_CONTEXT_FILES === "1";
const noSkills = process.env.PI_REBUILD_NO_SKILLS !== "0";
const noExtensions = process.env.PI_REBUILD_NO_EXTENSIONS !== "0";
const tools = (process.env.PI_REBUILD_TOOLS || "read,bash,edit,write")
  .split(",")
  .map((x) => x.trim())
  .filter(Boolean);

const services = await createAgentSessionServices({
  cwd,
  resourceLoaderOptions: {
    noSkills,
    noExtensions,
    noContextFiles,
    appendSystemPrompt: appendSystemPrompt ? [appendSystemPrompt] : undefined,
  },
});
const sessionManager = SessionManager.inMemory(cwd);
const { session, extensionsResult } = await createAgentSessionFromServices({
  services,
  sessionManager,
  tools,
});

const payload = {
  cwd,
  tools: session.getActiveToolNames(),
  systemPromptChars: session.systemPrompt.length,
  systemPrompt: session.systemPrompt,
  // Internal-but-stable enough for analysis: the same structured inputs exposed
  // to extensions as before_agent_start event.systemPromptOptions.
  systemPromptOptions: session._baseSystemPromptOptions,
  allTools: session.getAllTools().map((tool) => ({
    name: tool.name,
    description: tool.description,
    parameters: tool.parameters,
    promptGuidelines: tool.promptGuidelines,
    sourceInfo: tool.sourceInfo,
  })),
  resourceDiagnostics: services.diagnostics,
  extensionCount: extensionsResult.extensions.length,
  extensionErrors: extensionsResult.errors,
};
writeFileSync(out, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
console.log(out);

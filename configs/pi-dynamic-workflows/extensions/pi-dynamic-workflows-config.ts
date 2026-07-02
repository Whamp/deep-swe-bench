import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type { ExtensionAPI, InputEventResult } from "@earendil-works/pi-coding-agent";

const CONFIG_SENTINEL = "__PI_DYNAMIC_WORKFLOWS_CONFIGURED__";
const SKIP_SENTINEL = "__PI_DYNAMIC_WORKFLOWS_CONFIG_SKIPPED_OUTSIDE_HARNESS__";
const WRAP_SENTINEL = "__PI_DYNAMIC_WORKFLOWS_INITIAL_PROMPT_WRAPPED__";
const TRIGGER_WORD = "pi-workflow";

const SETTINGS = {
  keywordTriggerEnabled: true,
  keywordTriggerWord: TRIGGER_WORD,
  defaultConcurrency: 4,
  defaultAgentRetries: 1,
  progressPanelMode: "compact",
} as const;

const MODEL_TIERS = {
  tiers: {
    small: "openai-codex/gpt-5.4-mini:medium",
    medium: "openai-codex/gpt-5.4:medium",
    big: "openai-codex/gpt-5.5:medium",
  },
} as const;

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function configureWorkflowHome(): void {
  if (!existsSync("/arm") || !existsSync("/out")) {
    console.error(`${SKIP_SENTINEL} trigger=${TRIGGER_WORD}`);
    return;
  }

  const workflowHome = join(homedir(), ".pi", "workflows");
  mkdirSync(workflowHome, { recursive: true });
  writeJson(join(workflowHome, "settings.json"), SETTINGS);
  writeJson(join(workflowHome, "model-tiers.json"), MODEL_TIERS);
  console.error(
    `${CONFIG_SENTINEL} trigger=${TRIGGER_WORD} small=${MODEL_TIERS.tiers.small} medium=${MODEL_TIERS.tiers.medium} big=${MODEL_TIERS.tiers.big} concurrency=${SETTINGS.defaultConcurrency} thinking=medium`,
  );
}

function buildForcedWorkflowPrompt(text: string, extraDirective?: string): string {
  const lines = [
    text,
    "",
    "---",
    "[workflows mode is ON for this message]",
    "You MUST handle this request by calling the tool named exactly `workflow` (Pi's",
    "deterministic JavaScript workflow-orchestration tool from pi-dynamic-workflows).",
    "Write a workflow script that fans the task out across subagents via",
    "agent()/parallel()/pipeline().",
    "",
    "The ONLY acceptable action is a `workflow` tool call. Do NOT instead:",
    "- answer directly or in prose,",
    "- call the `subagent` tool yourself,",
    "- use any skill or command (e.g. pi-subagents, /code-review, deep-research),",
    '- or interpret the word "workflow/workflows" loosely as some other parallel/audit approach.',
    "Even for a small task, wrap it in a minimal `workflow` call with at least one agent().",
  ];
  if (extraDirective) lines.push("", extraDirective);
  return lines.join("\n");
}

function workflowBenchmarkPrompt(text: string): string {
  return buildForcedWorkflowPrompt(
    `${TRIGGER_WORD}\n\n${text}`,
    [
      "Benchmark-specific workflow requirements:",
      "- This task was intentionally triggered with the custom keyword `pi-workflow`.",
      "- Call the `workflow` tool with `background: false`; the benchmark harness must wait for the workflow result before the cell ends.",
      "- Tag every agent with `tier`: use `small` for lightweight repository inventory/search, `medium` for focused implementation/test investigation, and `big` for final synthesis, judgment, or cross-context decisions.",
      "- Keep fan-out useful and bounded; prefer a small number of high-signal agents over broad speculative spawning.",
      "- The final benchmark patch must be committed in `/app` before completion.",
    ].join("\n"),
  );
}

export default function (pi: ExtensionAPI): void {
  configureWorkflowHome();
  let wrapped = false;

  pi.on("input", async (event): Promise<InputEventResult> => {
    if (event.source === "extension") {
      return { action: "continue" };
    }

    if (wrapped || !event.text.trim()) {
      return { action: "continue" };
    }

    wrapped = true;
    const trimmed = event.text.trimStart();
    if (trimmed.startsWith("/workflows") || trimmed.includes("[workflows mode is ON for this message]")) {
      console.error(`${WRAP_SENTINEL} already_wrapped source=${event.source} chars=${event.text.length}`);
      return { action: "continue" };
    }

    console.error(`${WRAP_SENTINEL} source=${event.source} chars=${event.text.length}`);
    return {
      action: "transform",
      text: workflowBenchmarkPrompt(event.text),
      images: event.images,
    };
  });
}

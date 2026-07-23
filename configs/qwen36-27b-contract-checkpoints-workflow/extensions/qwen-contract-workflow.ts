import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { dirname, join } from "node:path";
import type {
  ExtensionAPI,
  ExtensionContext,
  InputEventResult,
  ToolDefinition,
} from "@earendil-works/pi-coding-agent";
import {
  createWorkflowStorage,
  createWorkflowTool,
  WorkflowManager,
} from "@quintinshaw/pi-dynamic-workflows";
import { Type } from "typebox";

const MODEL = "local-vllm/cyankiwi/Qwen3.6-27B-AWQ-BF16-INT4";
const MODEL_WITH_THINKING = `${MODEL}:high`;
const TOOL_NAME = "contract_checkpoint_workflow";
const WORKFLOW_PATH = "/arm/extensions/contract-checkpoint.workflow.mjs";
const WORKFLOW_HOME = join(homedir(), ".pi", "workflows");
const LIVE_STATUS_PATH = join(WORKFLOW_HOME, "qwen-workflow-live.json");
const CONFIGURED_MARKER = "__QWEN_CONTRACT_WORKFLOW_CONFIGURED__";
const WRAPPED_MARKER = "__QWEN_CONTRACT_WORKFLOW_PROMPT_WRAPPED__";
const AGENT_FILES = [
  "qwen-contract-scout.md",
  "qwen-contract-synthesizer.md",
  "qwen-contract-writer.md",
  "qwen-contract-reviewer.md",
];

const SETTINGS = {
  keywordTriggerEnabled: false,
  defaultConcurrency: 2,
  defaultAgentRetries: 0,
  defaultAgentTimeoutMs: 1_200_000,
  progressPanelMode: "compact",
};

const MODEL_TIERS = {
  tiers: {
    small: MODEL_WITH_THINKING,
    medium: MODEL_WITH_THINKING,
    big: MODEL_WITH_THINKING,
  },
};

function writeJson(path: string, value: unknown): void {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, `${JSON.stringify(value, null, 2)}\n`, "utf8");
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function writeIsolationAudit(details: unknown): string[] {
  const allowedTools = new Map<string, Set<string>>([
    ["contract ledger", new Set(["read", "bash"])],
    ["seam proof", new Set(["read", "bash"])],
    ["checkpoint synthesis", new Set(["read", "bash"])],
    ["contract adversary", new Set(["read", "bash"])],
  ]);
  const violations: string[] = [];
  const observed: Array<{ label: string; toolNames: string[] }> = [];
  const agents = isRecord(details) && Array.isArray(details.agents) ? details.agents : [];

  for (const agent of agents) {
    if (!isRecord(agent) || typeof agent.label !== "string") {
      continue;
    }
    const toolNames: string[] = [];
    const history = Array.isArray(agent.history) ? agent.history : [];
    for (const entry of history) {
      if (isRecord(entry) && typeof entry.toolName === "string" && !toolNames.includes(entry.toolName)) {
        toolNames.push(entry.toolName);
      }
    }
    observed.push({ label: agent.label, toolNames });
    const allowed = allowedTools.get(agent.label);
    if (allowed) {
      for (const toolName of toolNames) {
        if (!allowed.has(toolName)) {
          violations.push(`${agent.label} used forbidden tool ${toolName}`);
        }
      }
    }
  }

  writeJson(join(WORKFLOW_HOME, "isolation-audit.json"), {
    expectedReadOnlyLabels: [...allowedTools.keys()],
    observed,
    violations,
  });
  return violations;
}

function configureWorkflowHome(): void {
  const piHome = join(homedir(), ".pi");
  const agentHome = join(piHome, "agents");
  writeJson(join(WORKFLOW_HOME, "settings.json"), SETTINGS);
  writeJson(join(WORKFLOW_HOME, "model-tiers.json"), MODEL_TIERS);
  mkdirSync(agentHome, { recursive: true });
  for (const file of AGENT_FILES) {
    copyFileSync(join("/arm/extensions/agents", file), join(agentHome, file));
  }
}

function forcedToolPrompt(task: string): string {
  return [
    task,
    "",
    "---",
    "This task must run through the registered contract_checkpoint_workflow tool.",
    "Call contract_checkpoint_workflow exactly once with an empty object.",
    "Do not call another tool and do not attempt the task directly.",
    "The tool owns the fixed task-agnostic workflow, model routing, edits, validation, and final commit.",
  ].join("\n");
}

export default function qwenContractWorkflow(pi: ExtensionAPI): void {
  if (!existsSync("/arm") || !existsSync("/out")) {
    return;
  }

  configureWorkflowHome();

  const cwd = process.cwd();
  const storage = createWorkflowStorage(cwd);
  const manager = new WorkflowManager({
    cwd,
    loadSavedWorkflow: (name) => storage.load(name)?.script,
    defaultAgentTimeoutMs: SETTINGS.defaultAgentTimeoutMs,
    concurrency: SETTINGS.defaultConcurrency,
    defaultAgentRetries: SETTINGS.defaultAgentRetries,
  });
  const workflowTool = createWorkflowTool({ cwd, manager, storage });
  const workflowScript = readFileSync(WORKFLOW_PATH, "utf8");
  const parameters = Type.Object({}, { additionalProperties: false });
  let benchmarkTask: string | undefined;
  let wrapped = false;
  let workflowExecuted = false;

  const fixedTool: ToolDefinition<typeof parameters> = {
    name: TOOL_NAME,
    label: "Contract checkpoint workflow",
    description:
      "Run the current software task through the fixed contract-ledger, seam-proof, thin-slice, adversarial-review, and completion-receipt workflow.",
    promptSnippet:
      "Run the current task through the fixed contract-checkpoint workflow using only the configured local Qwen model.",
    promptGuidelines: [
      "Call contract_checkpoint_workflow exactly once for the current task; the tool already holds the original task text.",
    ],
    parameters,
    async execute(toolCallId, _params, signal, onUpdate, ctx) {
      if (benchmarkTask === undefined) {
        throw new Error("The benchmark task was not captured before workflow execution");
      }
      if (workflowExecuted) {
        return {
          content: [{
            type: "text",
            text: "The contract-checkpoint workflow already ran for this task. Do not call it again.",
          }],
          details: { duplicateWorkflowCallBlocked: true },
          isError: true,
        };
      }
      workflowExecuted = true;
      const previousWorkflowState = process.env.PI_QWEN_WORKFLOW_ACTIVE;
      process.env.PI_QWEN_WORKFLOW_ACTIVE = "1";
      writeJson(LIVE_STATUS_PATH, {
        status: "running",
        toolCallId,
        startedAt: new Date().toISOString(),
      });
      try {
        const result = await workflowTool.execute(
          toolCallId,
          {
            script: workflowScript,
            args: { task: benchmarkTask },
            background: false,
            maxAgents: 6,
            concurrency: SETTINGS.defaultConcurrency,
            agentRetries: SETTINGS.defaultAgentRetries,
            agentTimeoutMs: SETTINGS.defaultAgentTimeoutMs,
          },
          signal,
          onUpdate,
          ctx,
        );
        const violations = writeIsolationAudit(result.details);
        if (violations.length > 0) {
          throw new Error(`Workflow isolation failed: ${violations.join("; ")}`);
        }
        writeJson(LIVE_STATUS_PATH, {
          status: "completed",
          toolCallId,
          finishedAt: new Date().toISOString(),
        });
        return result;
      } catch (error) {
        writeJson(LIVE_STATUS_PATH, {
          status: "failed",
          toolCallId,
          finishedAt: new Date().toISOString(),
          error: error instanceof Error ? error.message : String(error),
        });
        throw error;
      } finally {
        if (previousWorkflowState === undefined) {
          delete process.env.PI_QWEN_WORKFLOW_ACTIVE;
        } else {
          process.env.PI_QWEN_WORKFLOW_ACTIVE = previousWorkflowState;
        }
      }
    },
  };

  pi.registerTool(fixedTool);

  pi.on("session_start", (_event: unknown, ctx: ExtensionContext) => {
    manager.setMainModel(ctx.model ? `${ctx.model.provider}/${ctx.model.id}` : undefined);
    manager.setModelRegistry(ctx.modelRegistry);
    manager.setSessionId(ctx.sessionManager.getSessionId());
    pi.setActiveTools([TOOL_NAME]);
    process.stderr.write(
      `${CONFIGURED_MARKER} model=${MODEL_WITH_THINKING} concurrency=${SETTINGS.defaultConcurrency}\n`,
    );
  });

  pi.on("input", async (event): Promise<InputEventResult> => {
    if (event.source === "extension" || wrapped || !event.text.trim()) {
      return { action: "continue" };
    }
    benchmarkTask = event.text;
    wrapped = true;
    process.stderr.write(`${WRAPPED_MARKER} chars=${event.text.length}\n`);
    return {
      action: "transform",
      text: forcedToolPrompt(event.text),
      images: event.images,
    };
  });
}

import { appendFileSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

type UsageLike = {
  input?: number;
  output?: number;
  cacheRead?: number;
  cacheWrite?: number;
  totalTokens?: number;
  cost?: {
    input?: number;
    output?: number;
    cacheRead?: number;
    cacheWrite?: number;
    total?: number;
  };
};

type TraceEvent = {
  type: string;
  message?: {
    role?: string;
    api?: string;
    provider?: string;
    model?: string;
    usage?: UsageLike;
    stopReason?: string;
    errorMessage?: string;
    timestamp?: number;
  };
  messages?: Array<{ role?: string; usage?: UsageLike }>;
};

type WorkerTraceInput = {
  stage: "observer" | "reflector" | "dropper" | string;
  model?: { provider?: string; id?: string; api?: string };
  thinkingLevel?: string;
  event: TraceEvent;
};

type ActiveRun = {
  id: string;
  stage: string;
  provider?: string;
  model?: string;
  api?: string;
  thinkingLevel?: string;
  assistantCalls: number;
  usage: Required<Omit<UsageLike, "cost">> & { cost: Required<NonNullable<UsageLike["cost"]>> };
};

const TRACE_RELATIVE_DIR = join("observational-memory", "worker-usage");
const TRACE_FILE = "usage.ndjson";

function zeroUsage(): ActiveRun["usage"] {
  return {
    input: 0,
    output: 0,
    cacheRead: 0,
    cacheWrite: 0,
    totalTokens: 0,
    cost: { input: 0, output: 0, cacheRead: 0, cacheWrite: 0, total: 0 },
  };
}

function addUsage(target: ActiveRun["usage"], usage: UsageLike | undefined): void {
  if (!usage) return;
  target.input += usage.input ?? 0;
  target.output += usage.output ?? 0;
  target.cacheRead += usage.cacheRead ?? 0;
  target.cacheWrite += usage.cacheWrite ?? 0;
  target.totalTokens += usage.totalTokens ?? ((usage.input ?? 0) + (usage.output ?? 0) + (usage.cacheRead ?? 0) + (usage.cacheWrite ?? 0));
  target.cost.input += usage.cost?.input ?? 0;
  target.cost.output += usage.cost?.output ?? 0;
  target.cost.cacheRead += usage.cost?.cacheRead ?? 0;
  target.cost.cacheWrite += usage.cost?.cacheWrite ?? 0;
  target.cost.total += usage.cost?.total ?? ((usage.cost?.input ?? 0) + (usage.cost?.output ?? 0) + (usage.cost?.cacheRead ?? 0) + (usage.cost?.cacheWrite ?? 0));
}

function compactUsage(usage: UsageLike | undefined): UsageLike | undefined {
  if (!usage) return undefined;
  return {
    input: usage.input ?? 0,
    output: usage.output ?? 0,
    cacheRead: usage.cacheRead ?? 0,
    cacheWrite: usage.cacheWrite ?? 0,
    totalTokens: usage.totalTokens ?? ((usage.input ?? 0) + (usage.output ?? 0) + (usage.cacheRead ?? 0) + (usage.cacheWrite ?? 0)),
    cost: {
      input: usage.cost?.input ?? 0,
      output: usage.cost?.output ?? 0,
      cacheRead: usage.cost?.cacheRead ?? 0,
      cacheWrite: usage.cost?.cacheWrite ?? 0,
      total: usage.cost?.total ?? ((usage.cost?.input ?? 0) + (usage.cost?.output ?? 0) + (usage.cost?.cacheRead ?? 0) + (usage.cost?.cacheWrite ?? 0)),
    },
  };
}

function tracePath(): string {
  return join(getAgentDir(), TRACE_RELATIVE_DIR, TRACE_FILE);
}

function writeRecord(record: Record<string, unknown>): void {
  const path = tracePath();
  mkdirSync(join(getAgentDir(), TRACE_RELATIVE_DIR), { recursive: true });
  appendFileSync(path, JSON.stringify({ timestamp: new Date().toISOString(), ...record }) + "\n", "utf8");
}

function modelKey(input: WorkerTraceInput): string {
  const provider = input.model?.provider ?? "unknown";
  const id = input.model?.id ?? "unknown";
  return `${input.stage}:${provider}/${id}:${input.thinkingLevel ?? "unknown"}`;
}

export default function (_pi: ExtensionAPI) {
  let seq = 0;
  const active = new Map<string, ActiveRun>();

  function getOrCreateRun(input: WorkerTraceInput): ActiveRun {
    const key = modelKey(input);
    let run = active.get(key);
    if (!run) {
      run = {
        id: `${Date.now().toString(36)}-${++seq}`,
        stage: input.stage,
        provider: input.model?.provider,
        model: input.model?.id,
        api: input.model?.api,
        thinkingLevel: input.thinkingLevel,
        assistantCalls: 0,
        usage: zeroUsage(),
      };
      active.set(key, run);
      writeRecord({
        event: "agent_start_inferred",
        runId: run.id,
        stage: run.stage,
        provider: run.provider,
        model: run.model,
        api: run.api,
        thinkingLevel: run.thinkingLevel,
      });
    }
    return run;
  }

  (globalThis as any).__PI_OM_WORKER_USAGE_TRACE = {
    recordAgentEvent(input: WorkerTraceInput) {
      const event = input.event;
      if (!event || typeof event.type !== "string") return;
      const key = modelKey(input);

      if (event.type === "agent_start") {
        const run: ActiveRun = {
          id: `${Date.now().toString(36)}-${++seq}`,
          stage: input.stage,
          provider: input.model?.provider,
          model: input.model?.id,
          api: input.model?.api,
          thinkingLevel: input.thinkingLevel,
          assistantCalls: 0,
          usage: zeroUsage(),
        };
        active.set(key, run);
        writeRecord({
          event: "agent_start",
          runId: run.id,
          stage: run.stage,
          provider: run.provider,
          model: run.model,
          api: run.api,
          thinkingLevel: run.thinkingLevel,
        });
        return;
      }

      if (event.type === "message_end" && event.message?.role === "assistant") {
        const run = getOrCreateRun(input);
        run.assistantCalls++;
        addUsage(run.usage, event.message.usage);
        writeRecord({
          event: "assistant_usage",
          runId: run.id,
          stage: run.stage,
          provider: event.message.provider ?? run.provider,
          model: event.message.model ?? run.model,
          api: event.message.api ?? run.api,
          thinkingLevel: run.thinkingLevel,
          assistantCallIndex: run.assistantCalls,
          stopReason: event.message.stopReason,
          errorMessage: event.message.errorMessage,
          usage: compactUsage(event.message.usage),
        });
        return;
      }

      if (event.type === "agent_end") {
        const run = active.get(key) ?? getOrCreateRun(input);
        writeRecord({
          event: "agent_end",
          runId: run.id,
          stage: run.stage,
          provider: run.provider,
          model: run.model,
          api: run.api,
          thinkingLevel: run.thinkingLevel,
          assistantCalls: run.assistantCalls,
          usage: run.usage,
        });
        active.delete(key);
      }
    },
  };
}

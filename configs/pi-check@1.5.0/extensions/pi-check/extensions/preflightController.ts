import { isToolCallEventType } from '@earendil-works/pi-coding-agent';
import type {
  ExtensionAPI,
  ExtensionCommandContext,
  ExtensionContext,
  SessionStartEvent,
  ToolCallEvent,
  ToolCallEventResult,
} from '@earendil-works/pi-coding-agent';
import { isBashFileMutation } from './isBashFileMutation.ts';

const PREFLIGHT_DESCRIPTION = 'Run a pi-check preflight before the first detected file change.';
const PREFLIGHT_BLOCK_REASON = 'Blocked by pi-check preflight before execution.';
const PREFLIGHT_PROMPT = `Pi-check preflight: your attempted file-changing tool call was temporarily blocked before execution to allow you to follow this Pi-check preflight process. Any other file-changing calls detected in the same assistant response were also blocked; read-only calls may have completed. Do not assume that a blocked change occurred or immediately retry it.

Before attempting another file change, treat your current plan and architecture as provisional. Briefly explain the task as you understand it, your current plan, the exact evidence that supports it, its expected benefits and drawbacks, its assumptions, and observations that could invalidate or materially change it.

Check that each material requirement is connected to the relevant existing seam and observable evidence. Where applicable, account for:

- repository instructions, READMEs, public documentation, and schemas;
- the public API or entry point and the existing owner of the behavior;
- producers, consumers, callers, interfaces, and end-to-end data or control flow;
- state, lifecycle, persistence, error-attribution, and round-trip paths;
- tests, helpers, fixtures, configuration, build rules, and a way to validate the behavior.

Identify the highest-value gap or disconfirming evidence you have not examined. A search or listing discovers a file; it does not mean you have read it. Use the available tools to inspect the gap. Do not repeat an earlier read unless you have a specific new question. When practical, run one small discriminating probe for the riskiest requirement or invariant before broad implementation. Prioritize evidence that could materially change the plan rather than chasing low-value completeness.

If the evidence or probe contradicts your chosen seam or strategy, reopen and revise it instead of patching around the result. Then continue the original task automatically in this session. Do not ask the user for confirmation merely because of this preflight. Reissue any still-needed blocked change yourself after completing the checkpoint.`;

function describePreflightError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function reportPreflightWarning(ctx: ExtensionContext, error: unknown): void {
  const previousExitCode = process.exitCode;
  const reason = describePreflightError(error);
  try {
    if (ctx.hasUI) {
      ctx.ui.notify(`Pi-check preflight disabled after an internal error: ${reason}`, 'warning');
    } else {
      process.stderr.write(`pi-check: Preflight disabled after an internal error: ${reason}\n`);
    }
  } catch (warningError: unknown) {
    // Warning delivery is best-effort and must never turn preflight into a failure boundary.
    void warningError;
  } finally {
    process.exitCode = previousExitCode;
  }
}

enum PreflightLifecycle {
  INACTIVE,
  ARMED_NEXT,
  ARMED_CURRENT,
  CLOSED_CURRENT,
}

/** Owns the one-task preflight lifecycle and mutation interception. */
export class PreflightController {
  private readonly pi: ExtensionAPI;
  private lifecycle = PreflightLifecycle.INACTIVE;
  private blockMutatingSiblings = false;

  constructor(pi: ExtensionAPI) {
    this.pi = pi;
  }

  /** Expires an unused preflight when final verification actually begins. */
  expireUnusedForVerification(): void {
    if (
      this.lifecycle === PreflightLifecycle.ARMED_NEXT ||
      this.lifecycle === PreflightLifecycle.ARMED_CURRENT
    ) {
      this.lifecycle = PreflightLifecycle.CLOSED_CURRENT;
    }
  }

  /** Registers the preflight command and lifecycle handlers with Pi. */
  register(): void {
    this.pi.registerFlag('check-preflight', {
      description: PREFLIGHT_DESCRIPTION,
      type: 'boolean',
    });

    this.pi.registerCommand('check-preflight', {
      description: PREFLIGHT_DESCRIPTION,
      handler: (args, ctx) => this.handleCommand(args, ctx),
    });

    this.pi.on('session_start', (event) => this.handleSessionStart(event));
    this.pi.on('agent_start', () => this.handleAgentStart());
    this.pi.on('agent_settled', () => this.resetLifecycle());
    this.pi.on('session_shutdown', () => this.resetLifecycle());
    this.pi.on('turn_start', () => this.handleTurnStart());
    this.pi.on('tool_call', (event, ctx) => this.handleToolCall(event, ctx));
  }

  private async handleCommand(args: string, ctx: ExtensionCommandContext): Promise<void> {
    if (args.trim().length > 0) {
      ctx.ui.notify('Usage: /check-preflight', 'warning');
      return;
    }

    if (this.lifecycle === PreflightLifecycle.CLOSED_CURRENT) {
      ctx.ui.notify('Preflight is unavailable until the current task settles.', 'info');
      return;
    }

    if (this.lifecycle !== PreflightLifecycle.INACTIVE) {
      this.lifecycle = PreflightLifecycle.INACTIVE;
      ctx.ui.notify('Preflight disarmed.', 'info');
      return;
    }

    if (ctx.isIdle()) {
      this.lifecycle = PreflightLifecycle.ARMED_NEXT;
      ctx.ui.notify('Preflight armed for the next task.', 'info');
      return;
    }

    this.lifecycle = PreflightLifecycle.ARMED_CURRENT;
    ctx.ui.notify('Preflight armed for the current task.', 'info');
  }

  private handleSessionStart(event: SessionStartEvent): void {
    if (event.reason === 'startup' && this.pi.getFlag('check-preflight') === true) {
      this.lifecycle = PreflightLifecycle.ARMED_NEXT;
    }
  }

  private handleAgentStart(): void {
    if (this.lifecycle === PreflightLifecycle.ARMED_NEXT) {
      this.lifecycle = PreflightLifecycle.ARMED_CURRENT;
    }
  }

  private handleTurnStart(): void {
    this.blockMutatingSiblings = false;
  }

  private handleToolCall(
    event: ToolCallEvent,
    ctx: ExtensionContext,
  ): ToolCallEventResult | undefined {
    if (!this.blockMutatingSiblings && this.lifecycle !== PreflightLifecycle.ARMED_CURRENT) {
      return undefined;
    }

    let mutatesFiles: boolean;
    try {
      mutatesFiles =
        event.toolName === 'edit' ||
        event.toolName === 'write' ||
        (isToolCallEventType('bash', event) && isBashFileMutation(event.input.command));
    } catch (error: unknown) {
      if (this.lifecycle === PreflightLifecycle.ARMED_CURRENT) {
        this.lifecycle = PreflightLifecycle.CLOSED_CURRENT;
      }
      reportPreflightWarning(ctx, error);
      return undefined;
    }

    if (!mutatesFiles) {
      return undefined;
    }
    if (this.blockMutatingSiblings) {
      return { block: true, reason: PREFLIGHT_BLOCK_REASON };
    }

    this.lifecycle = PreflightLifecycle.CLOSED_CURRENT;
    try {
      this.pi.sendUserMessage(PREFLIGHT_PROMPT, { deliverAs: 'steer' });
    } catch (error: unknown) {
      reportPreflightWarning(ctx, error);
      return undefined;
    }
    this.blockMutatingSiblings = true;
    return { block: true, reason: PREFLIGHT_BLOCK_REASON };
  }

  private resetLifecycle(): void {
    this.lifecycle = PreflightLifecycle.INACTIVE;
    this.blockMutatingSiblings = false;
  }
}

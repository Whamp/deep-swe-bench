import type {
  ExtensionAPI,
  ExtensionCommandContext,
  ExtensionContext,
  MessageStartEvent,
  TurnEndEvent,
} from '@earendil-works/pi-coding-agent';
import { PreflightController } from './preflightController.ts';

const CHECK_PROMPT = `Re-audit every requirement in the original request with fresh, independent evidence; do not restate prior claims.

Run provided tests with the correct runner and confirm tests were collected. Otherwise, black-box the requested behavior on a fresh boundary or adversarial input and, when relevant, in a fresh process or environment.

File existence, imports, logs, ports, and re-running the same development example are not sufficient proof.

Keep verification isolated so it cannot change the required final state. Do not clean up, reset, delete, revert, or stop services unless required to satisfy the request.

Fix any failure or uncertainty, then rerun the check. If the request is satisfied, briefly confirm what was verified.`;

type ThinkingLevel = Parameters<ExtensionAPI['setThinkingLevel']>[0];
type ExtensionModel = NonNullable<ExtensionContext['model']>;
type ExplicitCheckStatus =
  | 'armed'
  | 'waiting'
  | 'switching'
  | 'queued'
  | 'verifying'
  | 'restoring'
  | 'restored';

interface ModelSpecification {
  requested: string;
  provider: string;
  modelId: string;
  thinkingLevel: ThinkingLevel;
}

interface SavedSelection {
  model: ExtensionModel;
  thinkingLevel: ThinkingLevel;
}

interface ExplicitTarget extends ModelSpecification {
  model: ExtensionModel;
}

interface ExplicitCheck {
  target: ExplicitTarget;
  status: ExplicitCheckStatus;
  savedSelection?: SavedSelection;
}

interface ModelSpecificationSuccess {
  specification: ModelSpecification;
}

interface ModelSpecificationFailure {
  error: string;
}

interface ExplicitTargetSuccess {
  target: ExplicitTarget;
}

type ModelSpecificationResult = ModelSpecificationSuccess | ModelSpecificationFailure;
type ExplicitTargetResult = ExplicitTargetSuccess | ModelSpecificationFailure;

function parseThinkingLevel(value: string): ThinkingLevel | undefined {
  switch (value) {
    case 'off':
    case 'minimal':
    case 'low':
    case 'medium':
    case 'high':
    case 'xhigh':
    case 'max':
      return value;
    default:
      return undefined;
  }
}

function parseModelSpecification(value: string): ModelSpecificationResult {
  const requested = value.trim();
  const providerSeparator = requested.indexOf('/');
  const thinkingSeparator = requested.lastIndexOf(':');
  if (providerSeparator <= 0 || thinkingSeparator <= providerSeparator + 1) {
    return { error: `Invalid check model "${requested}": expected provider/model:thinking` };
  }

  const provider = requested.slice(0, providerSeparator);
  const modelId = requested.slice(providerSeparator + 1, thinkingSeparator);
  const thinkingLevel = parseThinkingLevel(requested.slice(thinkingSeparator + 1));
  if (modelId.length === 0 || thinkingLevel === undefined) {
    return { error: `Invalid check model "${requested}": expected provider/model:thinking` };
  }

  return { specification: { requested, provider, modelId, thinkingLevel } };
}

async function resolveExplicitTarget(
  value: string,
  ctx: ExtensionContext,
): Promise<ExplicitTargetResult> {
  const parsed = parseModelSpecification(value);
  if ('error' in parsed) {
    return parsed;
  }

  const model = ctx.modelRegistry.find(parsed.specification.provider, parsed.specification.modelId);
  if (model === undefined) {
    return { error: `Unknown check model "${parsed.specification.requested}".` };
  }

  const authentication = await ctx.modelRegistry.getApiKeyAndHeaders(model);
  if (!authentication.ok) {
    return {
      error: `Cannot use check model "${parsed.specification.requested}": ${authentication.error}`,
    };
  }

  return { target: { ...parsed.specification, model } };
}

function describeError(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

function reportFailure(ctx: ExtensionContext, message: string): void {
  if (ctx.mode === 'print' || ctx.mode === 'json') {
    process.stderr.write(`pi-check: ${message}\n`);
    if (process.exitCode === undefined || process.exitCode === 0) {
      process.exitCode = 1;
    }
    return;
  }
  ctx.ui.notify(message, 'error');
}

function isFinalTurn(event: TurnEndEvent): boolean {
  if (event.message.role !== 'assistant') {
    return false;
  }
  return !event.message.content.some((content) => content.type === 'toolCall');
}

function isCheckPrompt(event: MessageStartEvent): boolean {
  if (event.message.role !== 'user') {
    return false;
  }
  if (typeof event.message.content === 'string') {
    return event.message.content === CHECK_PROMPT;
  }
  return event.message.content.some(
    (content) => content.type === 'text' && content.text === CHECK_PROMPT,
  );
}

class CheckController {
  private readonly pi: ExtensionAPI;
  private readonly preflight: PreflightController;
  private armed = false;
  private pending = false;
  private flagConsumed = false;
  private explicitCheck?: ExplicitCheck;

  constructor(pi: ExtensionAPI, preflight: PreflightController) {
    this.pi = pi;
    this.preflight = preflight;
  }

  register(): void {
    this.pi.registerFlag('check', {
      description: 'Verify the first agent run with a temporary model',
      type: 'string',
    });

    this.pi.registerCommand('check', {
      description: 'Verify the current or next task with fresh evidence',
      handler: (args, ctx) => this.handleCommand(args, ctx),
    });

    this.pi.on('session_start', (_event, ctx) => this.handleSessionStart(ctx));
    this.pi.on('agent_start', () => this.handleAgentStart());
    this.pi.on('message_start', (event) => this.handleMessageStart(event));
    this.pi.on('turn_end', (event, ctx) => this.handleTurnEnd(event, ctx));
    this.pi.on('agent_settled', (_event, ctx) => this.handleAgentSettled(ctx));
    this.pi.on('session_shutdown', (_event, ctx) => this.handleSessionShutdown(ctx));
  }

  private async restoreExplicitSelection(ctx: ExtensionContext): Promise<boolean> {
    const check = this.explicitCheck;
    if (check === undefined || check.savedSelection === undefined) {
      reportFailure(ctx, 'Cannot restore the model because no saved selection exists.');
      return false;
    }
    const savedSelection = check.savedSelection;
    if (check.status === 'restored') {
      return true;
    }

    check.status = 'restoring';
    let restored: boolean;
    try {
      restored = await this.pi.setModel(savedSelection.model);
    } catch (error: unknown) {
      reportFailure(
        ctx,
        `Could not restore the model used before verification: ${describeError(error)}`,
      );
      return false;
    }
    if (!restored) {
      reportFailure(ctx, 'Could not restore the model used before verification.');
      return false;
    }
    this.pi.setThinkingLevel(savedSelection.thinkingLevel);
    check.status = 'restored';
    return true;
  }

  private async startExplicitVerification(ctx: ExtensionContext): Promise<boolean> {
    const check = this.explicitCheck;
    if (check === undefined) {
      return false;
    }
    if (ctx.model === undefined) {
      reportFailure(ctx, 'Cannot run model-specific verification without an active model.');
      this.explicitCheck = undefined;
      return false;
    }

    check.savedSelection = {
      model: ctx.model,
      thinkingLevel: this.pi.getThinkingLevel(),
    };
    check.status = 'switching';
    let selected: boolean;
    try {
      selected = await this.pi.setModel(check.target.model);
    } catch (error: unknown) {
      reportFailure(
        ctx,
        `Cannot use check model "${check.target.requested}": ${describeError(error)}`,
      );
      await this.restoreExplicitSelection(ctx);
      return false;
    }
    if (!selected) {
      reportFailure(ctx, `Cannot use check model "${check.target.requested}".`);
      await this.restoreExplicitSelection(ctx);
      return false;
    }

    this.pi.setThinkingLevel(check.target.thinkingLevel);
    check.status = 'queued';
    this.pi.sendUserMessage(CHECK_PROMPT, { deliverAs: 'followUp' });
    return true;
  }

  private async handleCommand(args: string, ctx: ExtensionCommandContext): Promise<void> {
    if (this.armed || this.pending || this.explicitCheck !== undefined) {
      ctx.ui.notify('Verification is already armed or queued.', 'info');
      return;
    }

    if (args.trim().length > 0) {
      await this.handleExplicitCommand(args, ctx);
      return;
    }

    if (ctx.isIdle()) {
      this.armed = true;
      ctx.ui.notify('Verification armed for the next task.', 'info');
      return;
    }

    this.pending = true;
    this.pi.sendUserMessage(CHECK_PROMPT, { deliverAs: 'followUp' });
    ctx.ui.notify('Verification queued for the current task.', 'info');
  }

  private async handleExplicitCommand(args: string, ctx: ExtensionCommandContext): Promise<void> {
    const wasIdle = ctx.isIdle();
    if (!wasIdle && ctx.hasPendingMessages()) {
      reportFailure(ctx, 'A model-specific check cannot be added while another message is queued.');
      return;
    }

    const resolved = await resolveExplicitTarget(args, ctx);
    if ('error' in resolved) {
      reportFailure(ctx, resolved.error);
      return;
    }

    await this.activateExplicitTarget(resolved.target, wasIdle, ctx);
  }

  private async activateExplicitTarget(
    target: ExplicitTarget,
    wasIdle: boolean,
    ctx: ExtensionCommandContext,
  ): Promise<void> {
    const isIdle = ctx.isIdle();
    const armForNextTask = wasIdle && isIdle;
    this.explicitCheck = {
      target,
      status: armForNextTask ? 'armed' : 'waiting',
    };
    if (!wasIdle && isIdle) {
      if (!(await this.startExplicitVerification(ctx))) {
        return;
      }
      ctx.ui.notify(`Verification with ${target.requested} queued.`, 'info');
      return;
    }

    ctx.ui.notify(
      armForNextTask
        ? `Verification with ${target.requested} armed for the next task.`
        : `Verification with ${target.requested} will run at the next safe boundary.`,
      'info',
    );
  }

  private async handleSessionStart(ctx: ExtensionContext): Promise<void> {
    if (this.flagConsumed) {
      return;
    }
    const flag = this.pi.getFlag('check');
    if (typeof flag !== 'string') {
      return;
    }
    this.flagConsumed = true;

    const resolved = await resolveExplicitTarget(flag, ctx);
    if ('error' in resolved) {
      reportFailure(ctx, resolved.error);
      return;
    }
    this.explicitCheck = { target: resolved.target, status: 'armed' };
  }

  private handleAgentStart(): void {
    if (this.explicitCheck?.status === 'armed') {
      this.explicitCheck.status = 'waiting';
      return;
    }
    if (!this.armed) {
      return;
    }

    this.armed = false;
    this.pending = true;
    this.pi.sendUserMessage(CHECK_PROMPT, { deliverAs: 'followUp' });
  }

  private handleMessageStart(event: MessageStartEvent): void {
    const expectsSameModelCheck = this.pending;
    const expectsExplicitCheck = this.explicitCheck?.status === 'queued';
    if ((!expectsSameModelCheck && !expectsExplicitCheck) || !isCheckPrompt(event)) {
      return;
    }

    this.preflight.expireUnusedForVerification();
    if (expectsExplicitCheck && this.explicitCheck !== undefined) {
      this.explicitCheck.status = 'verifying';
    }
  }

  private async handleTurnEnd(event: TurnEndEvent, ctx: ExtensionContext): Promise<void> {
    if (this.explicitCheck?.status === 'verifying' && isFinalTurn(event)) {
      await this.restoreExplicitSelection(ctx);
      return;
    }

    if (
      this.explicitCheck?.status !== 'waiting' ||
      !isFinalTurn(event) ||
      ctx.hasPendingMessages()
    ) {
      return;
    }

    await this.startExplicitVerification(ctx);
  }

  private async handleAgentSettled(ctx: ExtensionContext): Promise<void> {
    this.pending = false;
    if (
      this.explicitCheck?.savedSelection !== undefined &&
      this.explicitCheck.status !== 'restored'
    ) {
      await this.restoreExplicitSelection(ctx);
    }
    if (this.explicitCheck?.status === 'restored') {
      this.explicitCheck = undefined;
    }
  }

  private async handleSessionShutdown(ctx: ExtensionContext): Promise<void> {
    if (
      this.explicitCheck?.savedSelection !== undefined &&
      this.explicitCheck.status !== 'restored'
    ) {
      await this.restoreExplicitSelection(ctx);
    }
  }
}

/** Registers one-shot verification and preflight follow-ups with Pi. */
export default function checkExtension(pi: ExtensionAPI): void {
  const preflight = new PreflightController(pi);
  new CheckController(pi, preflight).register();
  preflight.register();
}

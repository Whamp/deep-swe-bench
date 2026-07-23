import type { ExtensionAPI } from '@earendil-works/pi-coding-agent';

const CHECK_PROMPT = `Re-audit every requirement in the original request with fresh, independent evidence; do not restate prior claims.

Run provided tests with the correct runner and confirm tests were collected. Otherwise, black-box the requested behavior on a fresh boundary or adversarial input and, when relevant, in a fresh process or environment.

File existence, imports, logs, ports, and re-running the same development example are not sufficient proof.

Keep verification isolated so it cannot change the required final state. Do not clean up, reset, delete, revert, or stop services unless required to satisfy the request.

Fix any failure or uncertainty, then rerun the check. If the request is satisfied, briefly confirm what was verified.`;

/** Registers one-shot verification follow-ups with Pi. */
export default function checkExtension(pi: ExtensionAPI): void {
  let armed = false;
  let pending = false;

  pi.registerFlag('check', {
    description: 'Verify the first agent run with fresh evidence',
    type: 'boolean',
    default: false,
  });

  pi.registerCommand('check', {
    description: 'Verify the current or next task with fresh evidence',
    handler: async (...[, ctx]) => {
      if (armed || pending) {
        ctx.ui.notify('Verification is already armed or queued.', 'info');
        return;
      }

      if (ctx.isIdle()) {
        armed = true;
        ctx.ui.notify('Verification armed for the next task.', 'info');
        return;
      }

      pending = true;
      pi.sendUserMessage(CHECK_PROMPT, { deliverAs: 'followUp' });
      ctx.ui.notify('Verification queued for the current task.', 'info');
    },
  });

  pi.on('session_start', () => {
    if (pi.getFlag('check') === true) {
      armed = true;
    }
  });

  pi.on('agent_start', () => {
    if (!armed) {
      return;
    }

    armed = false;
    pending = true;
    pi.sendUserMessage(CHECK_PROMPT, { deliverAs: 'followUp' });
  });

  pi.on('agent_settled', () => {
    pending = false;
  });
}

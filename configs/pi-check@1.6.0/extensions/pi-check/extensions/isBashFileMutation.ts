const DIRECT_FILESYSTEM_MUTATION_COMMANDS = new Set([
  'cp',
  'install',
  'ln',
  'mkdir',
  'mv',
  'rm',
  'rmdir',
  'touch',
  'unlink',
]);

const COMMAND_SEPARATORS = new Set([';', '\n', '&&', '||', '|', '&', '(', ')', '{', '}']);
const OUTPUT_REDIRECTS = new Set(['>', '>>', '>|', '&>', '&>>']);
const REDIRECTS = new Set([...OUTPUT_REDIRECTS, '<', '>&', '<&']);
const SHELL_OPERATORS = [
  '&>>',
  '&>',
  '>>',
  '>|',
  '>&',
  '<&',
  '&&',
  '||',
  '>',
  '<',
  '|',
  '&',
  ';',
  '(',
  ')',
  '{',
  '}',
];
const NON_FILE_OUTPUT_TARGETS = new Set([
  '-',
  '/dev/null',
  '/dev/stdout',
  '/dev/stderr',
  '/dev/fd/1',
  '/dev/fd/2',
  '/proc/self/fd/1',
  '/proc/self/fd/2',
]);
const GIT_APPLY_INSPECTION_OPTIONS = new Set(['--check', '--stat', '--numstat', '--summary']);

interface BashToken {
  value: string;
  operator: boolean;
}

interface BashCommand {
  name: string;
  arguments: string[];
  tokens: BashToken[];
}

function tokenizeBashCommand(command: string): BashToken[] {
  const tokens: BashToken[] = [];
  let word = '';
  let quote: "'" | '"' | undefined;
  let escaped = false;

  const finishWord = (): void => {
    if (word.length > 0) {
      tokens.push({ value: word, operator: false });
      word = '';
    }
  };

  for (let index = 0; index < command.length; index += 1) {
    const character = command[index] ?? '';
    if (escaped) {
      word += character;
      escaped = false;
      continue;
    }
    if (character === '\\' && quote !== "'") {
      escaped = true;
      continue;
    }
    if (quote !== undefined) {
      if (character === quote) {
        quote = undefined;
      } else {
        word += character;
      }
      continue;
    }
    if (character === "'" || character === '"') {
      quote = character;
      continue;
    }
    if (/\s/.test(character)) {
      finishWord();
      if (character === '\n') {
        tokens.push({ value: '\n', operator: true });
      }
      continue;
    }

    const operator = SHELL_OPERATORS.find((candidate) => command.startsWith(candidate, index));
    if (operator !== undefined) {
      finishWord();
      tokens.push({ value: operator, operator: true });
      index += operator.length - 1;
      continue;
    }
    word += character;
  }
  finishWord();
  return tokens;
}

function findCommandIndex(tokens: BashToken[]): number | undefined {
  for (let index = 0; index < tokens.length; index += 1) {
    const token = tokens[index];
    if (token === undefined) {
      continue;
    }
    if (token.operator && REDIRECTS.has(token.value)) {
      index += 1;
      continue;
    }
    if (token.operator) {
      continue;
    }
    const next = tokens[index + 1];
    if (/^\d+$/.test(token.value) && next?.operator === true && REDIRECTS.has(next.value)) {
      continue;
    }
    if (/^[A-Za-z_][A-Za-z0-9_]*=/.test(token.value)) {
      continue;
    }
    return index;
  }
  return undefined;
}

function getBashCommands(command: string): BashCommand[] {
  const commands: BashCommand[] = [];
  let segment: BashToken[] = [];

  const finishCommand = (): void => {
    const commandIndex = findCommandIndex(segment);
    if (commandIndex !== undefined) {
      const commandToken = segment[commandIndex];
      if (commandToken !== undefined) {
        commands.push({
          name: commandToken.value.split('/').at(-1) ?? commandToken.value,
          arguments: segment.slice(commandIndex + 1).map((token) => token.value),
          tokens: segment,
        });
      }
    }
    segment = [];
  };

  for (const token of tokenizeBashCommand(command)) {
    if (token.operator && COMMAND_SEPARATORS.has(token.value)) {
      finishCommand();
    } else {
      segment.push(token);
    }
  }
  finishCommand();
  return commands;
}

function isOrdinaryOutputTarget(target: string | undefined): boolean {
  return target !== undefined && target.length > 0 && !NON_FILE_OUTPUT_TARGETS.has(target);
}

function hasOrdinaryFileRedirection(command: BashCommand): boolean {
  return command.tokens.some((token, index) => {
    if (!token.operator || !OUTPUT_REDIRECTS.has(token.value)) {
      return false;
    }
    return isOrdinaryOutputTarget(command.tokens[index + 1]?.value);
  });
}

function isInPlaceEditorCommand(command: BashCommand): boolean {
  if (!['sed', 'perl', 'ruby'].includes(command.name)) {
    return false;
  }
  const optionTerminatorIndex = command.arguments.indexOf('--');
  const options =
    optionTerminatorIndex === -1
      ? command.arguments
      : command.arguments.slice(0, optionTerminatorIndex);
  return options.some((argument) => {
    if (command.name === 'sed') {
      return (
        argument === '-i' ||
        argument.startsWith('-i.') ||
        argument === '--in-place' ||
        argument.startsWith('--in-place=')
      );
    }
    return argument === '-i' || argument.startsWith('-i.') || argument === '-pi';
  });
}

function isTeeMutation(command: BashCommand): boolean {
  if (command.name !== 'tee') {
    return false;
  }
  const targets: string[] = [];
  for (const argument of command.arguments) {
    if (argument === '-a' || argument === '--append' || argument === '--') {
      continue;
    }
    if (argument.startsWith('-')) {
      return false;
    }
    targets.push(argument);
  }
  return targets.some(isOrdinaryOutputTarget);
}

function isDdMutation(command: BashCommand): boolean {
  return (
    command.name === 'dd' &&
    command.arguments.some(
      (argument) => argument.startsWith('of=') && isOrdinaryOutputTarget(argument.slice(3)),
    )
  );
}

function isPatchMutation(command: BashCommand): boolean {
  return (
    command.name === 'patch' &&
    !command.arguments.some(
      (argument) => argument === '--dry-run' || argument.startsWith('--dry-run='),
    )
  );
}

function findGitSubcommandIndex(commandArguments: string[]): number | undefined {
  for (let index = 0; index < commandArguments.length; index += 1) {
    const argument = commandArguments[index];
    if (argument === undefined) {
      continue;
    }
    if (argument === '-C') {
      if (commandArguments[index + 1] === undefined) {
        return undefined;
      }
      index += 1;
      continue;
    }
    if (argument.startsWith('-C') && argument.length > 2) {
      continue;
    }
    if (argument.startsWith('-')) {
      return undefined;
    }
    return index;
  }
  return undefined;
}

function isGitApplyMutation(command: BashCommand): boolean {
  if (command.name !== 'git') {
    return false;
  }
  const applyIndex = findGitSubcommandIndex(command.arguments);
  if (applyIndex === undefined || command.arguments[applyIndex] !== 'apply') {
    return false;
  }
  const applyArguments = command.arguments.slice(applyIndex + 1);
  const inspectionOnly = applyArguments.some((argument) =>
    GIT_APPLY_INSPECTION_OPTIONS.has(argument),
  );
  return !inspectionOnly || applyArguments.includes('--apply');
}

/** Detects only the approved, positively recognized Bash file mutation forms. */
export function isBashFileMutation(command: string): boolean {
  return getBashCommands(command).some(
    (bashCommand) =>
      DIRECT_FILESYSTEM_MUTATION_COMMANDS.has(bashCommand.name) ||
      isInPlaceEditorCommand(bashCommand) ||
      hasOrdinaryFileRedirection(bashCommand) ||
      isTeeMutation(bashCommand) ||
      bashCommand.name === 'truncate' ||
      isDdMutation(bashCommand) ||
      isPatchMutation(bashCommand) ||
      isGitApplyMutation(bashCommand),
  );
}

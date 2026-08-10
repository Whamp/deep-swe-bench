import {
  createReadToolDefinition,
  type AgentToolResult,
  type ExtensionAPI,
  type ReadToolInput,
  SettingsManager,
} from "@earendil-works/pi-coding-agent";

const READ_LINE_PREVIEW_CHARACTERS = 2_000;
const READ_LONG_LINES_TELEMETRY_TYPE = "read-long-lines.telemetry";

interface ShortenedReadLine {
  lineNumber: number;
  totalCharacters: number;
  omittedCharacters: number;
}

interface ReadLongLinePreview<TDetails> {
  result: AgentToolResult<TDetails>;
  shortenedLines: ShortenedReadLine[];
}

function formatCharacterCount(count: number): string {
  return count.toLocaleString("en-US");
}

function previewReadLongLines<TDetails>(
  result: AgentToolResult<TDetails>,
  input: ReadToolInput,
): ReadLongLinePreview<TDetails> {
  if (input.limit === 1) {
    return { result, shortenedLines: [] };
  }

  const startLine = input.offset ? Math.max(0, input.offset - 1) + 1 : 1;
  const shortenedLines: ShortenedReadLine[] = [];
  const content = result.content.map((part) => {
    if (part.type !== "text") {
      return part;
    }

    const previewedText = part.text
      .split("\n")
      .map((line, index) => {
        const lineEnding = line.endsWith("\r") ? "\r" : "";
        const lineText = lineEnding ? line.slice(0, -1) : line;
        const characters = Array.from(lineText);
        if (characters.length <= READ_LINE_PREVIEW_CHARACTERS) {
          return line;
        }

        shortenedLines.push({
          lineNumber: startLine + index,
          totalCharacters: characters.length,
          omittedCharacters: characters.length - READ_LINE_PREVIEW_CHARACTERS,
        });
        return `${characters.slice(0, READ_LINE_PREVIEW_CHARACTERS).join("")}${lineEnding}`;
      })
      .join("\n");

    return { ...part, text: previewedText };
  });

  if (shortenedLines.length === 0) {
    return { result, shortenedLines };
  }

  const notices = shortenedLines.map(
    ({ lineNumber, totalCharacters }) =>
      `[Line ${lineNumber} shortened: showing ${formatCharacterCount(READ_LINE_PREVIEW_CHARACTERS)} of ${formatCharacterCount(totalCharacters)} characters. Use offset=${lineNumber}, limit=1 to read the complete line.]`,
  );
  const lastTextPartIndex = content.findLastIndex((part) => part.type === "text");
  const lastTextPart = content[lastTextPartIndex];
  if (lastTextPart?.type === "text") {
    content[lastTextPartIndex] = {
      ...lastTextPart,
      text: `${lastTextPart.text}\n\n${notices.join("\n")}`,
    };
  }

  return { result: { ...result, content }, shortenedLines };
}

/** Shorten long lines in an ordinary read result while preserving focused one-line reads. */
export function addReadLongLinePreviews<TDetails>(
  result: AgentToolResult<TDetails>,
  input: ReadToolInput,
): AgentToolResult<TDetails> {
  return previewReadLongLines(result, input).result;
}

const readToolTemplate = createReadToolDefinition(process.cwd());

/** Register a read override that previews long lines unless one line was requested explicitly. */
export default function readLongLinesExtension(pi: ExtensionAPI) {
  pi.on("session_start", () => {
    pi.appendEntry(READ_LONG_LINES_TELEMETRY_TYPE, {
      schemaVersion: 1,
      event: "registered",
    });
  });

  pi.registerTool({
    name: readToolTemplate.name,
    label: readToolTemplate.label,
    description: `${readToolTemplate.description} In ordinary reads, lines longer than ${formatCharacterCount(READ_LINE_PREVIEW_CHARACTERS)} characters are shortened; use offset with limit=1 to read one in full.`,
    promptSnippet: readToolTemplate.promptSnippet,
    promptGuidelines: readToolTemplate.promptGuidelines,
    parameters: readToolTemplate.parameters,
    async execute(toolCallId, input, signal, onUpdate, context) {
      const settings = SettingsManager.create(context.cwd, undefined, {
        projectTrusted: context.isProjectTrusted(),
      });
      const coreReadTool = createReadToolDefinition(context.cwd, {
        autoResizeImages: settings.getImageAutoResize(),
      });
      const result = await coreReadTool.execute(toolCallId, input, signal, onUpdate, context);
      const preview = previewReadLongLines(result, input);
      if (preview.shortenedLines.length > 0) {
        pi.appendEntry(READ_LONG_LINES_TELEMETRY_TYPE, {
          schemaVersion: 1,
          event: "previewed",
          toolCallId,
          path: input.path,
          shortenedLines: preview.shortenedLines,
          omittedCharacters: preview.shortenedLines.reduce(
            (total, line) => total + line.omittedCharacters,
            0,
          ),
        });
      }
      return preview.result;
    },
  });
}

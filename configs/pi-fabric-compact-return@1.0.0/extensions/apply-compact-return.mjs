import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const packageRoot = path.resolve(process.argv[2] ?? "node_modules/pi-fabric");
const compactReturnMarker = "pi_fabric.compact_return.v1";
const compactReturnGuideline =
  "Compose related work freely inside one `fabric_exec` program using loops, branches, retries, `Promise.all`, and sequential awaits. Keep intermediate tool results inside the sandbox. Return the smallest sufficient decision-ready value: conclusions, exact locations, and evidence needed for the next turn—not raw files, broad search dumps, or full command logs unless those bytes are themselves required.";
const originalToolDescription =
  "Execute type-checked TypeScript through Fabric's configured executor for Pi core tools, MCP, Fabric providers, discovery, and extensions. QuickJS is isolated by default; the optional Node process is an unsafe trusted-code escape hatch. In full code mode, and always in Schema enforce mode, this is the exclusive model tool path.";
const originalBatchGuideline =
  "Batch independent operations in one `fabric_exec` program (`Promise.all` for parallel, sequential `await` for ordered), not one call per tool; keep dependent/conditional steps sequential. Return only the compact final value; intermediate results stay in the sandbox.";
const originalToolMetadata = `    description: ${JSON.stringify(originalToolDescription)},
    promptSnippet: "Pi core tools, MCP, Fabric providers, discovery, and extensions",
    promptGuidelines: [
        ${JSON.stringify(originalBatchGuideline)},
    ],`;
const compactToolMetadata = `    description: ${JSON.stringify(`${originalToolDescription} ${compactReturnMarker}`)},
    promptSnippet: "Pi core tools, MCP, Fabric providers, discovery, and extensions",
    promptGuidelines: [
        ${JSON.stringify(compactReturnGuideline)},
    ],`;
const originalReadExample = "Examples and returns: `pi.read('/x')`,";
const compactReadExample = `${compactReturnMarker} ${compactReturnGuideline}\\nExamples and returns: \`pi.read('/x')\`,`;
const originalSkillTableEnd =
  "| `write` | `{path,content}` \\| `(path, content)` | `{ok,output,details}` |\n\n";
const compactSkillTableEnd = `${originalSkillTableEnd}### Compact return boundary\n\n${compactReturnMarker} ${compactReturnGuideline}\n\n`;

const patches = [
  {
    relativePath: "dist/core/action-registry.js",
    original: `const bounded = boundedResult(value, context.maxResultChars);
            const resultError = failedResultError(value);`,
    replacement: `const bounded = boundedResult(value, context.maxResultChars);
            const serializedRawValue = JSON.stringify(value) ?? "null";
            const serializedSandboxValue = JSON.stringify(bounded.value) ?? "null";
            const rawResultBytes = Buffer.byteLength(serializedRawValue, "utf8");
            const sandboxResultChars = serializedSandboxValue.length;
            const sandboxResultBytes = Buffer.byteLength(serializedSandboxValue, "utf8");
            const resultError = failedResultError(value);`,
  },
  {
    relativePath: "dist/core/action-registry.js",
    original: `activeAudit.resultChars = bounded.chars;
            activeAudit.resultTruncated = bounded.truncated;`,
    replacement: `activeAudit.resultChars = bounded.chars;
            activeAudit.rawResultBytes = rawResultBytes;
            activeAudit.sandboxResultChars = sandboxResultChars;
            activeAudit.sandboxResultBytes = sandboxResultBytes;
            activeAudit.resultTruncated = bounded.truncated;`,
  },
  {
    relativePath: "dist/fabric-exec-tool.js",
    original: `const rawOutput = sections.join("\\n\\n");
        const outputWillTruncate = rawOutput.length > state.config.executor.maxOutputChars;`,
    replacement: `const rawOutput = sections.join("\\n\\n");
        const output = truncateMiddle(rawOutput || "(no output)", state.config.executor.maxOutputChars);
        const outputTelemetry = {
            kind: "pi-fabric.output-telemetry.v1",
            nestedOperationCount: result.audits.length,
            nestedMeasuredResultCount: result.audits.filter((audit) => typeof audit.resultChars === "number").length,
            nestedRawResultChars: result.audits.reduce((sum, audit) => sum + (audit.resultChars ?? 0), 0),
            nestedRawResultBytes: result.audits.reduce((sum, audit) => sum + (audit.rawResultBytes ?? 0), 0),
            nestedSandboxResultChars: result.audits.reduce((sum, audit) => sum + (audit.sandboxResultChars ?? 0), 0),
            nestedSandboxResultBytes: result.audits.reduce((sum, audit) => sum + (audit.sandboxResultBytes ?? 0), 0),
            nestedTruncatedResults: result.audits.filter((audit) => audit.resultTruncated === true).length,
            formattedValueChars: formattedValue.text?.length ?? 0,
            formattedValueBytes: Buffer.byteLength(formattedValue.text ?? "", "utf8"),
            logChars: logPrefix.length,
            logBytes: Buffer.byteLength(logPrefix, "utf8"),
            rawOutputChars: rawOutput.length,
            rawOutputBytes: Buffer.byteLength(rawOutput, "utf8"),
            returnedTextChars: output.length,
            returnedTextBytes: Buffer.byteLength(output, "utf8"),
        };
        const outputWillTruncate = rawOutput.length > state.config.executor.maxOutputChars;`,
  },
  {
    relativePath: "dist/fabric-exec-tool.js",
    original: `const persistedDetails = createFabricPersistedExecutionDetails({
            ...result,`,
    replacement: `const persistedDetails = createFabricPersistedExecutionDetails({
            ...result,
            telemetry: outputTelemetry,`,
  },
  {
    relativePath: "dist/fabric-exec-tool.js",
    original: `const output = truncateMiddle(rawOutput || "(no output)", state.config.executor.maxOutputChars);
        const terminate =`,
    replacement: `// Output is measured before details are persisted.
        const terminate =`,
  },
  {
    relativePath: "dist/audit/details.js",
    original: `trace: cloneTrace(input.trace),`,
    replacement: `trace: cloneTrace(input.trace),
        ...(input.telemetry ? { telemetry: structuredClone(input.telemetry) } : {}),`,
  },
  {
    relativePath: "dist/fabric-exec-tool.js",
    original: originalToolMetadata,
    replacement: compactToolMetadata,
  },
  {
    relativePath: "dist/index.js",
    original: originalReadExample,
    replacement: compactReadExample,
  },
  {
    relativePath: "skills/fabric-exec/SKILL.md",
    original: originalSkillTableEnd,
    replacement: compactSkillTableEnd,
  },
];

for (const patch of patches) {
  const filePath = path.join(packageRoot, patch.relativePath);
  const source = await readFile(filePath, "utf8");
  if (source.includes(patch.replacement)) continue;

  const occurrences = source.split(patch.original).length - 1;
  if (occurrences !== 1) {
    throw new Error(
      `Pi Fabric compact return patch mismatch: ${patch.relativePath} expected one source block, found ${occurrences}`,
    );
  }
  await writeFile(filePath, source.replace(patch.original, patch.replacement));
}

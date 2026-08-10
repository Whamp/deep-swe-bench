import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const packageRoot = path.resolve(process.argv[2] ?? "node_modules/pi-fabric");

const nativeReadDescription =
  "Read the contents of a file. Supports text files and images (jpg, png, gif, webp, bmp). Images are sent as attachments. For text files, output is truncated to 2000 lines or 50KB (whichever is hit first). Use offset/limit for large files. When you need the full file, continue with offset until complete.";
const nativeReadGuideline = "Use read to examine files instead of cat or sed.";
const nativeReadMarker = "pi_fabric.native_read_guidance.v1";
const stagedReadGuideline =
  "Batch independent discovery operations in one `fabric_exec` program. Keep dependent steps sequential: observe search results before choosing read ranges, then use `pi.read({path, offset, limit})` for targeted reads. Batch reads only after their relevant ranges are known. Return only the compact final value; intermediate results stay in the sandbox.";

async function replaceExactly(relativePath, original, replacement) {
  const filePath = path.join(packageRoot, relativePath);
  const source = await readFile(filePath, "utf8");
  if (source.includes(replacement)) return;

  const occurrences = source.split(original).length - 1;
  if (occurrences !== 1) {
    throw new Error(
      `Pi Fabric native read guidance patch mismatch: ${relativePath} expected one source block, found ${occurrences}`,
    );
  }
  await writeFile(filePath, source.replace(original, replacement));
}

const originalToolDescription =
  "Execute type-checked TypeScript through Fabric's configured executor for Pi core tools, MCP, Fabric providers, discovery, and extensions. QuickJS is isolated by default; the optional Node process is an unsafe trusted-code escape hatch. In full code mode, and always in Schema enforce mode, this is the exclusive model tool path.";
const originalBatchGuideline =
  "Batch independent operations in one `fabric_exec` program (`Promise.all` for parallel, sequential `await` for ordered), not one call per tool; keep dependent/conditional steps sequential. Return only the compact final value; intermediate results stay in the sandbox.";
const patchedToolDescription = `${originalToolDescription} ${nativeReadMarker} ${nativeReadDescription}`;
const originalToolMetadata = `    description: ${JSON.stringify(originalToolDescription)},
    promptSnippet: "Pi core tools, MCP, Fabric providers, discovery, and extensions",
    promptGuidelines: [
        ${JSON.stringify(originalBatchGuideline)},
    ],`;
const patchedToolMetadata = `    description: ${JSON.stringify(patchedToolDescription)},
    promptSnippet: "Pi core tools, MCP, Fabric providers, discovery, and extensions",
    promptGuidelines: [
        ${JSON.stringify(`${nativeReadMarker} ${nativeReadDescription} ${nativeReadGuideline}`)},
        ${JSON.stringify(stagedReadGuideline)},
    ],`;
await replaceExactly("dist/fabric-exec-tool.js", originalToolMetadata, patchedToolMetadata);

const originalReadExample = "Examples and returns: `pi.read('/x')`,";
const patchedReadExample = `${nativeReadMarker} ${nativeReadDescription} ${nativeReadGuideline} Observe search results before choosing read ranges; then use bounded reads and batch them only after the relevant ranges are known.\\nExamples and returns: \`pi.read({path:'/x', offset:1, limit:200})\`,`;
await replaceExactly("dist/index.js", originalReadExample, patchedReadExample);

const originalSkillTableEnd =
  "| `write` | `{path,content}` \\| `(path, content)` | `{ok,output,details}` |\n\n";
const patchedSkillTableEnd = `${originalSkillTableEnd}### Native Pi read behavior\n\n${nativeReadMarker} ${nativeReadDescription} ${nativeReadGuideline}\n\nBatch independent discovery operations first. Observe search results before choosing read ranges, then use \`pi.read({path, offset, limit})\` for targeted reads. Batch reads only after their relevant ranges are known.\n\n`;
await replaceExactly("skills/fabric-exec/SKILL.md", originalSkillTableEnd, patchedSkillTableEnd);

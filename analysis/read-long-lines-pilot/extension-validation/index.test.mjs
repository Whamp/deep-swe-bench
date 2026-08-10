import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  createReadExecutionContext,
  getReadResultText,
  piModule,
  registerReadLongLinesTool,
} from "./read-long-lines.test-support.mjs";

const testDirectory = await mkdtemp(join(tmpdir(), "pi-read-long-lines-"));
try {
  const path = join(testDirectory, "long-line.txt");
  await writeFile(path, `before\n${"x".repeat(3_000)}\nafter`);

  const readTool = registerReadLongLinesTool();
  const result = await readTool.execute(
    "test-call",
    { path },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );

  assert.equal(
    getReadResultText(result),
    `before\n${"x".repeat(2_000)}\nafter\n\n[Line 2 shortened: showing 2,000 of 3,000 characters. Use offset=2, limit=1 to read the complete line.]`,
  );

  const zeroOffsetPath = join(testDirectory, "zero-offset.txt");
  await writeFile(zeroOffsetPath, `${"q".repeat(3_000)}\nafter`);
  const zeroOffsetResult = await readTool.execute(
    "zero-offset-test-call",
    { path: zeroOffsetPath, offset: 0 },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );
  assert.equal(
    getReadResultText(zeroOffsetResult),
    `${"q".repeat(2_000)}\nafter\n\n[Line 1 shortened: showing 2,000 of 3,000 characters. Use offset=1, limit=1 to read the complete line.]`,
  );

  const focusedResult = await readTool.execute(
    "focused-test-call",
    { path, offset: 2, limit: 1 },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );
  assert.equal(
    getReadResultText(focusedResult),
    `${"x".repeat(3_000)}\n\n[1 more lines in file. Use offset=3 to continue.]`,
  );

  const windowsPath = join(testDirectory, "windows-lines.txt");
  await writeFile(windowsPath, `${"y".repeat(2_000)}\r\nnext`);
  const windowsResult = await readTool.execute(
    "windows-test-call",
    { path: windowsPath },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );
  assert.equal(getReadResultText(windowsResult), `${"y".repeat(2_000)}\r\nnext`);

  const unicodePath = join(testDirectory, "unicode-line.txt");
  await writeFile(unicodePath, `skip\nshort\n${"😀".repeat(2_001)}\nafter`);
  const unicodeResult = await readTool.execute(
    "unicode-test-call",
    { path: unicodePath, offset: 2, limit: 2 },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );
  assert.equal(
    getReadResultText(unicodeResult),
    `short\n${"😀".repeat(2_000)}\n\n[1 more lines in file. Use offset=4 to continue.]\n\n[Line 3 shortened: showing 2,000 of 2,001 characters. Use offset=3, limit=1 to read the complete line.]`,
  );

  const byteLimitedPath = join(testDirectory, "byte-limited.txt");
  const byteLimitedLines = Array.from(
    { length: 500 },
    (_, index) => `Line ${index + 1}: ${"z".repeat(200)}`,
  );
  await writeFile(byteLimitedPath, byteLimitedLines.join("\n"));
  const byteLimitedInput = { path: byteLimitedPath };
  const context = createReadExecutionContext(testDirectory);
  const coreReadTool = piModule.createReadToolDefinition(testDirectory);
  const coreByteLimitedResult = await coreReadTool.execute(
    "core-byte-limit-call",
    byteLimitedInput,
    undefined,
    undefined,
    context,
  );
  const extensionByteLimitedResult = await readTool.execute(
    "extension-byte-limit-call",
    byteLimitedInput,
    undefined,
    undefined,
    context,
  );
  assert.deepEqual(extensionByteLimitedResult, coreByteLimitedResult);

  const lineLimitedPath = join(testDirectory, "line-limited.txt");
  const lineLimitedLines = Array.from({ length: 2_500 }, (_, index) => `Line ${index + 1}`);
  await writeFile(lineLimitedPath, lineLimitedLines.join("\n"));
  const lineLimitedInput = { path: lineLimitedPath };
  const coreLineLimitedResult = await coreReadTool.execute(
    "core-line-limit-call",
    lineLimitedInput,
    undefined,
    undefined,
    context,
  );
  const extensionLineLimitedResult = await readTool.execute(
    "extension-line-limit-call",
    lineLimitedInput,
    undefined,
    undefined,
    context,
  );
  assert.deepEqual(extensionLineLimitedResult, coreLineLimitedResult);

  const missingInput = { path: join(testDirectory, "missing.txt") };
  await assert.rejects(
    readTool.execute("missing-file-call", missingInput, undefined, undefined, context),
    /ENOENT/,
  );

  const abortController = new AbortController();
  abortController.abort();
  await assert.rejects(
    readTool.execute("aborted-call", { path }, abortController.signal, undefined, context),
    /Operation aborted/,
  );

  const imagePath = join(testDirectory, "pixel.png");
  await writeFile(
    imagePath,
    Buffer.from(
      "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII=",
      "base64",
    ),
  );
  const imageInput = { path: imagePath };
  const imageContext = createReadExecutionContext(testDirectory, { model: { input: ["image"] } });
  const coreImageResult = await coreReadTool.execute(
    "core-image-call",
    imageInput,
    undefined,
    undefined,
    imageContext,
  );
  const extensionImageResult = await readTool.execute(
    "extension-image-call",
    imageInput,
    undefined,
    undefined,
    imageContext,
  );
  assert.deepEqual(extensionImageResult, coreImageResult);
} finally {
  await rm(testDirectory, { recursive: true, force: true });
}

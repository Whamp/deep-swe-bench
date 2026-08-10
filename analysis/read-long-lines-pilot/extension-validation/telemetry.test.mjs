import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import {
  createReadExecutionContext,
  registerReadLongLinesExtension,
} from "./read-long-lines.test-support.mjs";

const testDirectory = await mkdtemp(join(tmpdir(), "pi-read-long-lines-telemetry-"));
try {
  const path = join(testDirectory, "long-line.txt");
  await writeFile(path, `before\n${"x".repeat(3_000)}\nafter`);

  const extension = registerReadLongLinesExtension();
  const sessionStart = extension.handlers.get("session_start");
  assert.ok(sessionStart, "session_start telemetry handler registered");
  await sessionStart({ reason: "startup" }, createReadExecutionContext(testDirectory));

  assert.deepEqual(extension.entries, [
    {
      customType: "read-long-lines.telemetry",
      data: { schemaVersion: 1, event: "registered" },
    },
  ]);

  await extension.readTool.execute(
    "preview-call",
    { path },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );

  assert.deepEqual(extension.entries[1], {
    customType: "read-long-lines.telemetry",
    data: {
      schemaVersion: 1,
      event: "previewed",
      toolCallId: "preview-call",
      path,
      shortenedLines: [
        {
          lineNumber: 2,
          totalCharacters: 3_000,
          omittedCharacters: 1_000,
        },
      ],
      omittedCharacters: 1_000,
    },
  });

  await extension.readTool.execute(
    "focused-call",
    { path, offset: 2, limit: 1 },
    undefined,
    undefined,
    createReadExecutionContext(testDirectory),
  );
  assert.equal(extension.entries.length, 2, "focused recovery read emits no preview event");
} finally {
  await rm(testDirectory, { recursive: true, force: true });
}

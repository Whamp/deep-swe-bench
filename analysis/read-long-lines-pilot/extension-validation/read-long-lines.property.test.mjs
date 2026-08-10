import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import fc from "fast-check";
import {
  createReadExecutionContext,
  extensionModule,
  getReadResultText,
  piModule,
  registerReadLongLinesTool,
} from "./read-long-lines.test-support.mjs";

const READ_LINE_PREVIEW_CHARACTERS = 2_000;
const PROPERTY_SEED = Number(process.env.READ_LONG_LINES_PROPERTY_SEED ?? 20_260_810);
const PURE_PROPERTY_RUNS = Number(process.env.READ_LONG_LINES_PURE_RUNS ?? 1_000);
const INTEGRATION_PROPERTY_RUNS = Number(process.env.READ_LONG_LINES_INTEGRATION_RUNS ?? 200);

const { addReadLongLinePreviews } = extensionModule;

const codePointArbitrary = fc.constantFrom("a", "é", "😀", "\u0301", "\ud800", "\udc00");
const boundaryLengthArbitrary = fc.oneof(
  { weight: 5, arbitrary: fc.constantFrom(0, 1, 1_999, 2_000, 2_001, 3_000) },
  { weight: 1, arbitrary: fc.integer({ min: 0, max: 4_000 }) },
);
const shortLengthArbitrary = fc.oneof(
  { weight: 5, arbitrary: fc.constantFrom(0, 1, 1_999, 2_000) },
  { weight: 1, arbitrary: fc.integer({ min: 0, max: 2_000 }) },
);
const longLengthArbitrary = fc.oneof(
  { weight: 5, arbitrary: fc.constantFrom(2_001, 2_002, 3_000, 4_000) },
  { weight: 1, arbitrary: fc.integer({ min: 2_001, max: 8_000 }) },
);

function formatCharacterCount(count) {
  return count.toLocaleString("en-US");
}

function makeLine(character, length) {
  assert.equal(Array.from(character).length, 1, "generated line unit must contain one code point");
  return character.repeat(length);
}

function createTextResult(text, details = undefined) {
  return {
    content: [{ type: "text", text }],
    details,
  };
}

function splitPreviewNotices(text) {
  const noticeStart = text.indexOf("\n\n[Line ");
  if (noticeStart === -1) {
    return { body: text, notices: [] };
  }
  return {
    body: text.slice(0, noticeStart),
    notices: text.slice(noticeStart + 2).split("\n"),
  };
}

function expectedPreviewNotice(lineNumber, totalCharacters) {
  return `[Line ${lineNumber} shortened: showing ${formatCharacterCount(READ_LINE_PREVIEW_CHARACTERS)} of ${formatCharacterCount(totalCharacters)} characters. Use offset=${lineNumber}, limit=1 to read the complete line.]`;
}

async function assertGeneratedProperty(name, property, numRuns) {
  await fc.assert(property, { seed: PROPERTY_SEED, numRuns });
  process.stdout.write(`property ok - ${name} (${numRuns} cases, seed ${PROPERTY_SEED})\n`);
}

const detailsArbitrary = fc.option(
  fc.record({
    source: fc.string({ unit: "grapheme-ascii", maxLength: 20 }),
    count: fc.nat({ max: 10_000 }),
  }),
  { nil: undefined },
);
const focusedResultArbitrary = fc
  .tuple(
    fc.array(fc.tuple(codePointArbitrary, boundaryLengthArbitrary), { minLength: 1, maxLength: 5 }),
    fc.constantFrom("\n", "\r\n"),
    detailsArbitrary,
  )
  .map(([lineSpecs, separator, details]) =>
    createTextResult(
      lineSpecs.map(([character, length]) => makeLine(character, length)).join(separator),
      details,
    ),
  );
const shortTextCaseArbitrary = fc
  .tuple(
    fc.array(fc.tuple(codePointArbitrary, shortLengthArbitrary), { minLength: 1, maxLength: 8 }),
    fc.constantFrom("\n", "\r\n"),
    fc.nat({ max: 2_000 }),
    detailsArbitrary,
  )
  .map(([lineSpecs, separator, offset, details]) => ({
    result: createTextResult(
      lineSpecs.map(([character, length]) => makeLine(character, length)).join(separator),
      details,
    ),
    input: { path: "generated.txt", offset },
  }));
const longTextCaseArbitrary = fc
  .tuple(
    fc.array(fc.tuple(codePointArbitrary, boundaryLengthArbitrary), { maxLength: 3 }),
    fc.tuple(codePointArbitrary, longLengthArbitrary),
    fc.array(fc.tuple(codePointArbitrary, boundaryLengthArbitrary), { maxLength: 3 }),
    fc.constantFrom("\n", "\r\n"),
    fc.nat({ max: 2_000 }),
    detailsArbitrary,
  )
  .map(([before, requiredLongLine, after, separator, offset, details]) => {
    const lineSpecs = [...before, requiredLongLine, ...after];
    return {
      lineSpecs,
      separator,
      result: createTextResult(
        lineSpecs.map(([character, length]) => makeLine(character, length)).join(separator),
        details,
      ),
      input: { path: "generated.txt", offset },
    };
  });

await assertGeneratedProperty(
  "focused one-line reads are exact identity",
  fc.property(focusedResultArbitrary, (result) => {
    const transformed = addReadLongLinePreviews(result, { path: "generated.txt", limit: 1 });
    assert.strictEqual(transformed, result);
  }),
  PURE_PROPERTY_RUNS,
);

await assertGeneratedProperty(
  "results without long lines are exact identity",
  fc.property(shortTextCaseArbitrary, ({ result, input }) => {
    const transformed = addReadLongLinePreviews(result, input);
    assert.strictEqual(transformed, result);
  }),
  PURE_PROPERTY_RUNS,
);

await assertGeneratedProperty(
  "long lines preserve prefixes, structure, details, and accurate notices",
  fc.property(longTextCaseArbitrary, ({ lineSpecs, separator, result, input }) => {
    const originalText = result.content[0].text;
    Object.freeze(result.content[0]);
    Object.freeze(result.content);
    if (result.details !== undefined) {
      Object.freeze(result.details);
    }
    Object.freeze(result);

    const transformed = addReadLongLinePreviews(result, input);

    assert.equal(result.content[0].text, originalText, "input text mutated");
    assert.strictEqual(transformed.details, result.details, "details reference changed");
    assert.equal(transformed.content.length, result.content.length);
    assert.equal(transformed.content[0].type, "text");

    const { body, notices } = splitPreviewNotices(transformed.content[0].text);
    const transformedLines = body.split("\n");
    const expectedNotices = [];
    const startLine = input.offset ? Math.max(0, input.offset - 1) + 1 : 1;

    assert.equal(transformedLines.length, lineSpecs.length);
    for (const [index, [character, length]] of lineSpecs.entries()) {
      const hasCarriageReturn = separator === "\r\n" && index < lineSpecs.length - 1;
      const expectedLength = Math.min(length, READ_LINE_PREVIEW_CHARACTERS);
      assert.equal(
        transformedLines[index],
        `${makeLine(character, expectedLength)}${hasCarriageReturn ? "\r" : ""}`,
      );
      if (length > READ_LINE_PREVIEW_CHARACTERS) {
        expectedNotices.push(expectedPreviewNotice(startLine + index, length));
      }
    }
    assert.deepEqual(notices, expectedNotices);
  }),
  PURE_PROPERTY_RUNS,
);

await assertGeneratedProperty(
  "preview transformation is idempotent",
  fc.property(longTextCaseArbitrary, ({ result, input }) => {
    const once = addReadLongLinePreviews(result, input);
    const twice = addReadLongLinePreviews(once, input);
    assert.deepEqual(twice, once);
  }),
  PURE_PROPERTY_RUNS,
);

const imageResultArbitrary = fc
  .record({
    note: fc.string({ unit: "grapheme", maxLength: 100 }),
    data: fc.base64String({ maxLength: 200 }),
    mimeType: fc.constantFrom("image/png", "image/jpeg", "image/gif", "image/webp"),
    details: detailsArbitrary,
  })
  .map(({ note, data, mimeType, details }) => ({
    content: [
      { type: "text", text: note },
      { type: "image", data, mimeType },
    ],
    details,
  }));

await assertGeneratedProperty(
  "image results and non-text content are exact identity",
  fc.property(imageResultArbitrary, (result) => {
    const transformed = addReadLongLinePreviews(result, { path: "generated.png" });
    assert.strictEqual(transformed, result);
  }),
  PURE_PROPERTY_RUNS,
);

const testDirectory = await mkdtemp(join(tmpdir(), "pi-read-long-lines-property-"));
try {
  const readTool = registerReadLongLinesTool();
  const coreReadTool = piModule.createReadToolDefinition(testDirectory);
  const context = createReadExecutionContext(testDirectory);
  let generatedFileNumber = 0;

  const inertReadCaseArbitrary = fc
    .array(fc.tuple(fc.constantFrom("a", "é", "😀"), shortLengthArbitrary), {
      minLength: 1,
      maxLength: 8,
    })
    .chain((lineSpecs) =>
      fc.record({
        lineSpecs: fc.constant(lineSpecs),
        separator: fc.constantFrom("\n", "\r\n"),
        offset: fc.integer({ min: 0, max: lineSpecs.length }),
        limit: fc.option(fc.integer({ min: 0, max: lineSpecs.length + 2 }), { nil: undefined }),
      }),
    );

  await assertGeneratedProperty(
    "extension equals core whenever no returned source line exceeds the preview limit",
    fc.asyncProperty(inertReadCaseArbitrary, async ({ lineSpecs, separator, offset, limit }) => {
      const path = join(testDirectory, `inert-${generatedFileNumber++}.txt`);
      await writeFile(
        path,
        lineSpecs.map(([character, length]) => makeLine(character, length)).join(separator),
      );
      const input = { path, offset, ...(limit === undefined ? {} : { limit }) };
      const coreResult = await coreReadTool.execute(
        "core-inert",
        input,
        undefined,
        undefined,
        context,
      );
      const extensionResult = await readTool.execute(
        "extension-inert",
        input,
        undefined,
        undefined,
        context,
      );
      assert.deepEqual(extensionResult, coreResult);
    }),
    INTEGRATION_PROPERTY_RUNS,
  );

  const recoverableLongLineArbitrary = fc.record({
    before: fc.array(fc.string({ unit: "grapheme-ascii", maxLength: 40 }), { maxLength: 3 }),
    longLineLength: fc.oneof(
      { weight: 5, arbitrary: fc.constantFrom(2_001, 2_002, 3_000, 51_198, 51_199) },
      { weight: 1, arbitrary: fc.integer({ min: 2_001, max: 51_199 }) },
    ),
    after: fc.array(fc.string({ unit: "grapheme-ascii", maxLength: 40 }), { maxLength: 3 }),
    separator: fc.constantFrom("\n", "\r\n"),
  });

  await assertGeneratedProperty(
    "every preview escape hatch reproduces Pi's complete focused line",
    fc.asyncProperty(
      recoverableLongLineArbitrary,
      async ({ before, longLineLength, after, separator }) => {
        const longLine = makeLine("x", longLineLength);
        const lines = [...before, longLine, ...after];
        const path = join(testDirectory, `recoverable-${generatedFileNumber++}.txt`);
        await writeFile(path, lines.join(separator));
        const lineNumber = before.length + 1;

        const normalResult = await readTool.execute(
          "extension-preview",
          { path, offset: lineNumber },
          undefined,
          undefined,
          context,
        );
        assert.match(
          getReadResultText(normalResult),
          new RegExp(`Use offset=${lineNumber}, limit=1 to read the complete line\\.`),
        );

        const focusedInput = { path, offset: lineNumber, limit: 1 };
        const coreFocusedResult = await coreReadTool.execute(
          "core-focused",
          focusedInput,
          undefined,
          undefined,
          context,
        );
        const extensionFocusedResult = await readTool.execute(
          "extension-focused",
          focusedInput,
          undefined,
          undefined,
          context,
        );
        assert.deepEqual(extensionFocusedResult, coreFocusedResult);
        const expectedFocusedLine = `${longLine}${separator === "\r\n" && after.length > 0 ? "\r" : ""}`;
        assert.equal(
          getReadResultText(extensionFocusedResult).split("\n", 1)[0],
          expectedFocusedLine,
        );
      },
    ),
    INTEGRATION_PROPERTY_RUNS,
  );

  for (const [character, characterCount] of [
    ["b", 51_200],
    ["é", 25_600],
    ["😀", 12_800],
  ]) {
    const exactByteLimitPath = join(testDirectory, `exact-byte-limit-${characterCount}.txt`);
    const exactByteLimitLine = makeLine(character, characterCount);
    await writeFile(exactByteLimitPath, exactByteLimitLine);
    const exactByteLimitNormalResult = await readTool.execute(
      "extension-exact-byte-limit",
      { path: exactByteLimitPath },
      undefined,
      undefined,
      context,
    );
    assert.match(
      getReadResultText(exactByteLimitNormalResult),
      new RegExp(`showing 2,000 of ${formatCharacterCount(characterCount)} characters`),
    );
    const exactByteLimitFocusedInput = { path: exactByteLimitPath, offset: 1, limit: 1 };
    const exactByteLimitCoreResult = await coreReadTool.execute(
      "core-exact-byte-limit-focused",
      exactByteLimitFocusedInput,
      undefined,
      undefined,
      context,
    );
    const exactByteLimitExtensionResult = await readTool.execute(
      "extension-exact-byte-limit-focused",
      exactByteLimitFocusedInput,
      undefined,
      undefined,
      context,
    );
    assert.deepEqual(exactByteLimitExtensionResult, exactByteLimitCoreResult);
    assert.equal(getReadResultText(exactByteLimitExtensionResult), exactByteLimitLine);
  }

  const overByteLimitLineArbitrary = fc.oneof(
    fc.record({
      character: fc.constant("z"),
      characterCount: fc.integer({ min: 51_201, max: 60_000 }),
    }),
    fc.record({
      character: fc.constant("é"),
      characterCount: fc.integer({ min: 25_601, max: 30_000 }),
    }),
    fc.record({
      character: fc.constant("😀"),
      characterCount: fc.integer({ min: 12_801, max: 15_000 }),
    }),
  );

  await assertGeneratedProperty(
    "lines above Pi's byte ceiling retain core behavior",
    fc.asyncProperty(overByteLimitLineArbitrary, async ({ character, characterCount }) => {
      const path = join(testDirectory, `over-byte-limit-${generatedFileNumber++}.txt`);
      await writeFile(path, makeLine(character, characterCount));
      const input = { path };
      const coreResult = await coreReadTool.execute(
        "core-over-byte-limit",
        input,
        undefined,
        undefined,
        context,
      );
      const extensionResult = await readTool.execute(
        "extension-over-byte-limit",
        input,
        undefined,
        undefined,
        context,
      );
      assert.deepEqual(extensionResult, coreResult);
    }),
    INTEGRATION_PROPERTY_RUNS,
  );
} finally {
  await rm(testDirectory, { recursive: true, force: true });
}

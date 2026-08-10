import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { realpathSync } from "node:fs";
import { registerHooks } from "node:module";
import { dirname, join } from "node:path";
import { pathToFileURL } from "node:url";

const piExecutable = execFileSync("which", ["pi"], { encoding: "utf8" }).trim();
const PI_PACKAGE_ENTRY = join(dirname(realpathSync(piExecutable)), "index.js");

registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === "@earendil-works/pi-coding-agent") {
      return { url: pathToFileURL(PI_PACKAGE_ENTRY).href, shortCircuit: true };
    }
    return nextResolve(specifier, context);
  },
});

export const piModule = await import(pathToFileURL(PI_PACKAGE_ENTRY).href);
export const extensionModule =
  await import("../../../configs/read-long-lines@1.0.0/extensions/read-long-lines.ts");

/** Register the complete extension against an observable in-memory Pi API. */
export function registerReadLongLinesExtension() {
  let registeredTool;
  const handlers = new Map();
  const entries = [];
  extensionModule.default({
    registerTool(tool) {
      registeredTool = tool;
    },
    on(event, handler) {
      handlers.set(event, handler);
    },
    appendEntry(customType, data) {
      entries.push({ customType, data });
    },
  });
  assert.ok(registeredTool, "read tool registered");
  return { readTool: registeredTool, handlers, entries };
}

/** Register the extension and return its read tool definition. */
export function registerReadLongLinesTool() {
  return registerReadLongLinesExtension().readTool;
}

/** Join all text parts from a Pi tool result in their original order. */
export function getReadResultText(result) {
  return result.content
    .filter((part) => part.type === "text")
    .map((part) => part.text)
    .join("\n");
}

/** Create the minimum execution context accepted by Pi's read definition. */
export function createReadExecutionContext(cwd, properties = {}) {
  return {
    cwd,
    isProjectTrusted() {
      return true;
    },
    ...properties,
  };
}

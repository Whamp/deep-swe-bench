/**
 * codegraph-auto — forces relationship-graph attention into view.
 *
 * Hypothesis under test: a cheap model fails DeepSWE tasks partly because it
 * never checks who calls the symbol it edits. This extension removes the need
 * to choose to look:
 *   1. session_start: build the codegraph index once (base-commit structure).
 *   2. tool_result on read/edit/write of a source file: append `codegraph brief`
 *      — the file's symbols with caller counts and risk tier — to the result.
 *
 * This is the "hard" variant: the relationship map is auto-attached, not left
 * for the model to request. The `codegraph-skill` config (skill only) is the
 * "soft" control that relies on the model choosing to query.
 *
 * ponytail: injects `brief` (counts + roles) only — one cached call per file,
 * ~300 chars. Caller *names* via per-symbol `where` are the escalation path if
 * brief counts alone don't move edge-attention in the 12v0 read.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFileSync } from "node:fs";

const CG = "/arm/bin/codegraph/dist/cli.js";
const REPO = "/app";
const TRACE = "/out/codegraph-trace.jsonl";

// Languages present across the 113 deep-swe tasks + common variants.
const ALLOWED_EXTS = new Set([
  "ts", "tsx", "js", "jsx", "mjs", "mts", "cjs",
  "go", "py", "rs",
]);
const SKIP_SUBSTR = ["node_modules", "/.codegraph", "/task", "/tests", "/out", "/root", "vendor/"];

const BUILD_TIMEOUT_MS = 120_000; // most repos <2s; prometheus/langchain are the tail
const BRIEF_TIMEOUT_MS = 8_000;
const MAX_INJECT_CHARS = 2000;

type State = { built: boolean; buildError?: string; cache: Map<string, string | null>; injections: number; builds: number };
const state: State = { built: false, cache: new Map(), injections: 0, builds: 0 };

function trace(ev: Record<string, unknown>) {
  try {
    appendFileSync(TRACE, JSON.stringify({ ts: Date.now(), ...ev }) + "\n");
  } catch {
    /* /out may not exist pre-session; injection evidence also lives in session jsonl */
  }
}

async function buildGraph(pi: ExtensionAPI) {
  trace({ event: "build_start", repo: REPO });
  try {
    const r = await pi.exec("node", [CG, "build", REPO], { timeout: BUILD_TIMEOUT_MS });
    state.builds++;
    if (r.code === 0) {
      state.built = true;
      // codegraph logs the orchestrator line to stderr.
      const log = (r.stderr || "") + (r.stdout || "");
      const m = log.match(/(\d+)\s+nodes,\s*(\d+)\s+edges/);
      trace({ event: "build_ok", nodes: m ? Number(m[1]) : null, edges: m ? Number(m[2]) : null });
    } else {
      state.buildError = (r.stderr || r.stdout || `exit ${r.code}`).slice(0, 300);
      trace({ event: "build_failed", code: r.code, err: state.buildError });
    }
  } catch (e: any) {
    state.buildError = String(e?.message || e).slice(0, 300);
    trace({ event: "build_error", err: state.buildError });
  }
}

function shouldInject(path: unknown): string | null {
  if (typeof path !== "string" || !path) return null;
  const p = path;
  const lo = p.toLowerCase();
  const ext = lo.split(".").pop() || "";
  if (!ALLOWED_EXTS.has(ext)) return null;
  for (const s of SKIP_SUBSTR) if (p.includes(s)) return null;
  return p;
}

function toRel(p: string): string {
  // codegraph brief resolves relative to the build root (/app).
  if (p.startsWith(REPO + "/")) return p.slice(REPO.length + 1);
  if (p.startsWith("./")) return p.slice(2);
  return p;
}

async function briefFor(pi: ExtensionAPI, file: string): Promise<string | null> {
  const cached = state.cache.get(file);
  if (cached !== undefined) return cached;
  try {
    const r = await pi.exec("node", [CG, "brief", toRel(file)], { timeout: BRIEF_TIMEOUT_MS });
    const out = (r.stdout || "").trim();
    if (r.code !== 0 || !out || out.toLowerCase().includes("no symbols") || out.toLowerCase().startsWith("no ")) {
      state.cache.set(file, null);
      return null;
    }
    const clipped = out.length > MAX_INJECT_CHARS ? out.slice(0, MAX_INJECT_CHARS) + "\n…[truncated]" : out;
    state.cache.set(file, clipped);
    return clipped;
  } catch {
    state.cache.set(file, null);
    return null;
  }
}

function appendInjection(content: unknown, brief: string): unknown {
  const block = `\n\n[codegraph: symbol & caller map for this file — symbols with caller counts and risk tier]\n${brief}`;
  if (Array.isArray(content)) {
    if (content.length && typeof content[0] === "object" && content[0] !== null && (content[0] as any).type === "text") {
      (content[0] as any).text = ((content[0] as any).text || "") + block;
      return content;
    }
    return [...content, { type: "text", text: block }];
  }
  if (typeof content === "string") return content + block;
  return [{ type: "text", text: block }];
}

export default function codegraphAuto(pi: ExtensionAPI) {
  pi.on("session_start", async () => {
    await buildGraph(pi);
  });

  pi.on("tool_result", async (event: any) => {
    if (!state.built) return;
    const tool = event?.toolName;
    if (tool !== "read" && tool !== "edit" && tool !== "write") return;
    const file = shouldInject(event?.input?.path);
    if (!file) return;
    if (event?.isError) return;
    const brief = await briefFor(pi, file);
    if (!brief) return;
    state.injections++;
    trace({ event: "inject", tool, file });
    return { content: appendInjection(event.content, brief) };
  });

  pi.on("session_shutdown", async () => {
    trace({ event: "summary", built: state.built, builds: state.builds, injections: state.injections, cache_size: state.cache.size, buildError: state.buildError });
  });
}

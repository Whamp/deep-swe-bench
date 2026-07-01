/**
 * codegraph-impact — forces caller-NAME attention into view (v2 of codegraph-auto).
 *
 * v1 (codegraph-auto) injected `brief` = caller COUNTS + risk tier. The 12v0×3
 * run showed that was net-harmful (-0.091 partial): a loud "34 callers, HIGH
 * RISK" signal with no actionable detail bloated context and misled edits.
 * CODEGRAPH_PRIMITIVE_AUDIT.md named the fix: inject caller NAMES via
 * `fn-impact`.
 *
 * This extension, per read/edit/write of a source file:
 *   1. `brief <file> -j`  → the file's symbols with role + callerCount.
 *   2. `batch fn-impact <top symbols> --depth 1 -j` → the NAMES of each
 *      symbol's direct callers, in ONE process.
 *   3. drops test/benchmark callers (the `-T` flag does not filter on batch in
 *      3.15.0 — verified; filtering is done here by name prefix + file path).
 *   4. injects: `SymbolName [role] ← callerA, callerB, …`
 *
 * Names, not counts. Cached per file. Same trace contract as v1 so the smoke
 * gate and analysis scripts carry over.
 *
 * ponytail: depth-1 (direct callers) only — the actionable blast radius.
 * Transitive levels + callees/type-deps are the upgrade path; the model can
 * still query them via the codegraph skill. CEILING: codegraph is repo-scoped;
 * cross-package / shared-type / node_modules callers are invisible (see audit).
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { appendFileSync } from "node:fs";

const CG = "/arm/bin/codegraph/dist/cli.js";
const REPO = "/app";
const TRACE = "/out/codegraph-trace.jsonl";

const ALLOWED_EXTS = new Set([
  "ts", "tsx", "js", "jsx", "mjs", "mts", "cjs",
  "go", "py", "rs",
]);
const SKIP_SUBSTR = ["node_modules", "/.codegraph", "/task", "/tests", "/out", "/root", "vendor/"];

const BUILD_TIMEOUT_MS = 120_000;
const BRIEF_TIMEOUT_MS = 10_000;
const IMPACT_TIMEOUT_MS = 20_000;
const MAX_BATCH_SYMBOLS = 15;   // bound the batch fn-impact argv
const MAX_CALLERS_SHOWN = 6;    // per symbol
const MAX_INJECT_CHARS = 2000;

type Sym = { name: string; role: string; count: number };
type Caller = { name: string; file: string };
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
  const lo = path.toLowerCase();
  const ext = lo.split(".").pop() || "";
  if (!ALLOWED_EXTS.has(ext)) return null;
  for (const s of SKIP_SUBSTR) if (path.includes(s)) return null;
  return path;
}

function toRel(p: string): string {
  if (p.startsWith(REPO + "/")) return p.slice(REPO.length + 1);
  if (p.startsWith("./")) return p.slice(2);
  return p;
}

function isTestCaller(name: string, file: string): boolean {
  const f = (file || "").toLowerCase();
  const n = name || "";
  // file-pattern first (most reliable across languages)
  if (/(^|\/)(_test\.go|\.test\.[tj]sx?|\.spec\.[tj]sx?|_test\.py|test_[a-z0-9_]+\.py|_test\.rs|__tests__\/|\/tests\/|\/test\/|\.bench\.[tj]sx?)/.test(f)) return true;
  // name-pattern fallback
  if (/^(test|benchmark|example)[a-z0-9_]/i.test(n)) return true;
  if (/^test_/i.test(n)) return true;
  return false;
}

async function briefSymbols(pi: ExtensionAPI, file: string): Promise<Sym[]> {
  const r = await pi.exec("node", [CG, "brief", toRel(file), "-j"], { timeout: BRIEF_TIMEOUT_MS });
  if (r.code !== 0 || !r.stdout) return [];
  let d: any;
  try { d = JSON.parse(r.stdout); } catch { return []; }
  const res = d?.results?.[0]?.symbols;
  if (!Array.isArray(res)) return [];
  return res.map((s: any) => ({ name: String(s.name), role: String(s.role || ""), count: Number(s.callerCount || 0) }));
}

async function batchCallers(pi: ExtensionAPI, names: string[]): Promise<Map<string, Caller[]>> {
  const out = new Map<string, Caller[]>();
  if (!names.length) return out;
  const r = await pi.exec("node", [CG, "batch", "fn-impact", ...names, "--depth", "1", "-j"], { timeout: IMPACT_TIMEOUT_MS });
  if (r.code !== 0 || !r.stdout) return out;
  let d: any;
  try { d = JSON.parse(r.stdout); } catch { return out; }
  for (const res of d?.results || []) {
    if (!res?.ok) continue;
    const lv1 = res?.data?.results?.[0]?.levels?.["1"];
    if (Array.isArray(lv1)) out.set(String(res.target), lv1.map((c: any) => ({ name: String(c.name), file: String(c.file || "") })));
  }
  return out;
}

function renderDigest(symbols: Sym[], callers: Map<string, Caller[]>): string {
  const rows: { name: string; role: string; real: Caller[] }[] = [];
  for (const s of symbols) {
    const all = callers.get(s.name) || [];
    const real = all.filter((c) => !isTestCaller(c.name, c.file));
    if (real.length) rows.push({ name: s.name, role: s.role, real });
  }
  if (!rows.length) return "";
  rows.sort((a, b) => b.real.length - a.real.length); // most-called first
  let out = `[codegraph: non-test callers of this file's symbols — review these names before editing]`;
  for (const r of rows) {
    const shown = r.real.slice(0, MAX_CALLERS_SHOWN).map((c) => c.name);
    const more = r.real.length > MAX_CALLERS_SHOWN ? ` (+${r.real.length - MAX_CALLERS_SHOWN} more)` : "";
    const line = `\n${r.name} [${r.role || "?"}] ← ${shown.join(", ")}${more}`;
    if (out.length + line.length > MAX_INJECT_CHARS) { out += "\n…[more symbols omitted]"; break; }
    out += line;
  }
  return out;
}

async function digestFor(pi: ExtensionAPI, file: string): Promise<string | null> {
  const cached = state.cache.get(file);
  if (cached !== undefined) return cached;
  const symbols = await briefSymbols(pi, file);
  // batch only symbols that have any callers, top-N by callerCount.
  const targets = symbols
    .filter((s) => s.count > 0)
    .sort((a, b) => b.count - a.count)
    .slice(0, MAX_BATCH_SYMBOLS)
    .map((s) => s.name);
  let digest = "";
  if (targets.length) {
    const callers = await batchCallers(pi, targets);
    digest = renderDigest(symbols, callers);
  }
  const result = digest || null;
  state.cache.set(file, result);
  return result;
}

function appendInjection(content: unknown, digest: string): unknown {
  const block = `\n\n${digest}`;
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

export default function codegraphImpact(pi: ExtensionAPI) {
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
    const digest = await digestFor(pi, file);
    if (!digest) return;
    state.injections++;
    trace({ event: "inject", tool, file });
    return { content: appendInjection(event.content, digest) };
  });

  pi.on("session_shutdown", async () => {
    trace({ event: "summary", built: state.built, builds: state.builds, injections: state.injections, cache_size: state.cache.size, buildError: state.buildError });
  });
}

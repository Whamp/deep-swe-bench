/**
 * codebase-memory-mcp integration for the pi coding agent.
 *
 * Wraps the built-in `read` tool (via the exported `createReadToolDefinition`)
 * to prefix a codebase-memory symbol block for indexed code files. Image
 * handling, truncation, offset/limit, the "Use offset=N to continue" hint, and
 * the rich renderer are preserved exactly — only the text result is augmented.
 *
 * Design (what helps the agent, not what pleases the eye): the one fact the
 * graph gives that the file itself cannot is EDGES — who calls a symbol. So the
 * block leads with caller-connected symbols sorted by blast radius; macros and
 * constants (already visible in the file) are demoted to a count. Whenever any
 * symbol is omitted — inline cap, isolated summary, or the 200-row fetch cap —
 * the block carries a concrete CLI command to retrieve the rest (pi's own
 * truncation rule: never truncate without a pointer to the full data).
 *
 * Cardinal rule (inherited from CMB commit c29e6d5): the augmenter can never
 * break a read. Every CMB failure path (binary missing, not indexed, query
 * error, timeout) is silent and returns the original result unchanged.
 *
 * Usage (ad-hoc test):  pi -e /path/to/codebase-memory.ts
 * Loaded globally at:   ~/.pi/agent/extensions/codebase-memory.ts
 *
 * Auto-index: set CBM_AUTO_INDEX=1 to index the session's git repo at startup
 * (awaited before the first read — deterministic for tests; ~10ms when the
 * repo is unchanged). Off by default; never indexes non-repo dirs.
 */
import { type ExtensionAPI, createReadToolDefinition } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { resolve, relative, sep, join, dirname } from "node:path";
import { promisify } from "node:util";

const execFileP = promisify(execFile);
const CBM_BIN = "codebase-memory-mcp";
const QUERY_TIMEOUT_MS = 4_000;        // CMB's own backstop is 5s; stay under it
const PROJECT_TTL_MS = 60_000;          // refresh project index cache each minute
const FETCH_LIMIT = 200;                // symbols fetched per file read (one query)
const INLINE_LIMIT = 20;                // connected symbols shown inline
const DUMP_LIMIT = 500;                 // "give me everything" hint uses this
const DEBUG = !!process.env.CBM_PI_DEBUG;
const AUTO_INDEX = ["1", "true", "yes", "on"].includes((process.env.CBM_AUTO_INDEX || "").toLowerCase());
const INDEX_TIMEOUT_MS = 60_000;       // first index of a big repo; re-index of unchanged repo is ~10ms
const REINDEX_DEBOUNCE_MS = 1_500;     // coalesce a burst of edits into one background reindex

interface CmbProject { name: string; root_path: string; }
interface CmbSymbol {
	name: string; qualified_name: string; label: string;
	file_path: string; in_degree: number; out_degree: number;
	lines: number; is_exported: boolean; is_entry_point: boolean;
}
interface CmbHit {
	symbols: CmbSymbol[]; total: number; has_more: boolean;
	project: string; pattern: string;
}

let projectsCache: CmbProject[] | null = null;
let projectsCacheTime = 0;

function debug(msg: string) {
	if (!DEBUG) return;
	try { process.stderr.write(`[cbm-pi] ${msg}\n`); } catch { /* ignore */ }
}

async function cmbExec(args: string[]): Promise<any> {
	const { stdout } = await execFileP(CBM_BIN, ["cli", ...args], {
		encoding: "utf-8",
		timeout: QUERY_TIMEOUT_MS,
		maxBuffer: 10 * 1024 * 1024,
	});
	// CMB writes logrus `level=info` lines to stderr; stdout is pure JSON.
	return JSON.parse(stdout.trim());
}

async function listProjects(): Promise<CmbProject[]> {
	if (projectsCache && Date.now() - projectsCacheTime < PROJECT_TTL_MS) return projectsCache;
	const d = await cmbExec(["list_projects", "{}"]);
	projectsCache = Array.isArray(d?.projects) ? d.projects : [];
	projectsCacheTime = Date.now();
	return projectsCache;
}

function findProject(absPath: string, projects: CmbProject[]): CmbProject | undefined {
	return projects.find((p) => {
		const root = p.root_path;
		return absPath === root || absPath.startsWith(root + sep);
	});
}

async function symbolsForFile(absPath: string): Promise<CmbHit | null> {
	const projects = await listProjects();
	const proj = findProject(absPath, projects);
	if (!proj) return null;
	const rel = relative(proj.root_path, absPath).split(sep).join("/");
	const pattern = rel || absPath;
	const d = await cmbExec(["search_graph", JSON.stringify({
		project: proj.name,
		file_pattern: pattern,
		limit: FETCH_LIMIT,
	})]);
	const symbols: CmbSymbol[] = Array.isArray(d?.results) ? d.results : [];
	if (!symbols.length) return null;
	return {
		symbols,
		total: typeof d?.total === "number" ? d.total : symbols.length,
		has_more: !!d?.has_more,
		project: proj.name,
		pattern,
	};
}

// Build a shell-ready CLI command with correctly-quoted JSON args.
function cmd(project: string, pattern: string, extra: Record<string, unknown> = {}): string {
	const args = JSON.stringify({ project, file_pattern: pattern, ...extra });
	return `${CBM_BIN} cli search_graph '${args}'`;
}

function renderBlock(hit: CmbHit): string {
	const { symbols, total, has_more, project, pattern } = hit;

	const deg = (s: CmbSymbol) => (s.in_degree ?? 0) + (s.out_degree ?? 0);
	const connected = symbols
		.filter((s) => deg(s) > 0)
		.sort((a, b) => deg(b) - deg(a));
	const isolated = symbols.filter((s) => deg(s) === 0);

	const shown = connected.slice(0, INLINE_LIMIT);
	const moreConnected = connected.length - shown.length;
	const omitted = moreConnected > 0 || isolated.length > 0 || has_more || total > symbols.length;

	const L: string[] = [];
	L.push(`┌─ codebase-memory: ${total} symbols in file · ${connected.length} with caller edges`);
	if (shown.length) {
		for (const s of shown) {
			const tags: string[] = [];
			if (s.is_entry_point) tags.push("entry");
			if (s.is_exported) tags.push("exported");
			const t = tags.length ? ` [${tags.join(",")}]` : "";
			const ln = s.lines != null ? `${s.lines}L` : "-";
			L.push(`  ${s.label.padEnd(10)} ${s.name}${t}  (callers:${s.in_degree ?? 0} callees:${s.out_degree ?? 0}, ${ln})`);
		}
		if (moreConnected > 0) L.push(`  … +${moreConnected} more symbols with caller edges`);
		if (isolated.length) L.push(`  … +${isolated.length} isolated (macros/constants/leaves — visible in the file)`);
	} else {
		// No edges at all (constants/leaf header). Show a few names for orientation.
		const names = isolated.slice(0, 10).map((s) => s.name).join(", ");
		L.push(`  no caller edges · ${isolated.length} leaf symbols: ${names}${isolated.length > 10 ? " …" : ""}`);
	}

	// Truncation hint — present whenever anything was omitted (pi rule: never
	// truncate without a pointer to the full data).
	if (omitted) {
		L.push(`├─ full symbol list (untruncated):`);
		L.push(`  ${cmd(project, pattern, { limit: DUMP_LIMIT })}`);
		if (total > DUMP_LIMIT) L.push(`  (page further with "offset": ${DUMP_LIMIT})`);
	}
	L.push(`└─ trace a symbol's full caller/callee graph:`);
	L.push(`   ${CBM_BIN} cli trace_path '{"project":"${project}","function_name":"<name>"}'  # callers + callees`);
	L.push("");
	return L.join("\n");
}

// Walk up from `start` to the nearest directory containing .git (the repo root).
// Returns null for non-repo dirs so home, /tmp, etc. are never indexed.
function gitRoot(start: string): string | null {
	let dir = start;
	for (;;) {
		if (existsSync(join(dir, ".git"))) return dir;
		const parent = dirname(dir);
		if (parent === dir) return null;
		dir = parent;
	}
}

async function indexRepo(repoPath: string): Promise<any> {
	const { stdout } = await execFileP(CBM_BIN, ["cli", "index_repository", JSON.stringify({ repo_path: repoPath })], {
		encoding: "utf-8",
		timeout: INDEX_TIMEOUT_MS,
		maxBuffer: 50 * 1024 * 1024,
	});
	try { return JSON.parse(stdout.trim()); } catch { return null; }
}

export default async function (pi: ExtensionAPI) {
	// Optional auto-index at startup (CBM_AUTO_INDEX=1, off by default). Runs in
	// the factory because pi awaits it before continuing startup
	// (docs/extensions.md:180) — edges are guaranteed present for the first read,
	// which makes it deterministic for tests. Only indexes the git root found by
	// walking up from cwd; never touches non-repo dirs. Non-fatal on any failure.
	if (AUTO_INDEX) {
		const root = gitRoot(process.cwd());
		if (root) {
			try {
				debug(`auto-indexing ${root} (CBM_AUTO_INDEX=1, blocking)`);
				const r = await indexRepo(root);
				debug(`auto-index done: ${r?.status ?? "ok"}, ${r?.nodes ?? 0} nodes`);
			} catch (e: any) {
				debug(`auto-index skipped (non-fatal): ${e?.message ?? e}`);
			}
		} else {
			debug(`auto-index: ${process.cwd()} is not inside a git repo — skipped`);
		}
	}

	// Refresh project cache when a session (re)starts so newly indexed repos show up.
	pi.on("session_start", () => {
		projectsCache = null;
		projectsCacheTime = 0;
	});

	// Keep the graph fresh during a long-lived session: after a file-mutating
	// tool completes, reindex the repo in the background. tool_result can't break
	// the tool (it already ran) and the handler returns immediately, so edits are
	// never blocked — pure side effect. Debounced so a burst of edits coalesces
	// into one reindex. Gated by CBM_AUTO_INDEX. (Short-lived runs that exit
	// before the debounce fires are still fresh — startup auto-index covers the
	// next process.)
	let reindexTimer: ReturnType<typeof setTimeout> | null = null;
	pi.on("tool_result", (event: any, ctx: any) => {
		if (!AUTO_INDEX) return;
		if (event?.toolName !== "edit" && event?.toolName !== "write") return;
		if (reindexTimer) clearTimeout(reindexTimer);
		const cwd = ctx?.cwd ?? process.cwd();
		reindexTimer = setTimeout(() => {
			reindexTimer = null;
			const root = gitRoot(cwd);
			if (!root) return;
			debug(`auto-reindex scheduled for ${root}`);
			indexRepo(root)
				.then((r) => debug(`auto-reindex done: ${r?.status ?? "ok"}, ${r?.nodes ?? 0} nodes`))
				.catch((e: any) => debug(`auto-reindex skipped (non-fatal): ${e?.message ?? e}`));
		}, REINDEX_DEBOUNCE_MS);
	});

	// Built-in read definition. renderCall/renderResult/parameters use
	// context.cwd at render time, not the factory closure, so one static
	// construction is safe for those. execute builds a per-call instance bound
	// to ctx.cwd so path resolution matches the session.
	const baseRead = createReadToolDefinition(process.cwd());

	pi.registerTool({
		...baseRead,
		name: "read",
		label: "read",
		description:
			baseRead.description +
			" For indexed code files, prefixes a codebase-memory block listing caller-connected symbols (blast radius) with a CLI hint for the full list; silent no-op if unavailable.",
		promptGuidelines: [
			...(baseRead.promptGuidelines ?? []),
			"For indexed code, read prefixes a codebase-memory block of caller-connected symbols; use the printed codebase-memory-mcp cli trace_path / search_graph commands to pull full caller/callee graphs.",
		],
		async execute(toolCallId, params, signal, onUpdate, ctx) {
			const builtin = createReadToolDefinition(ctx?.cwd ?? process.cwd());
			const result: any = await builtin.execute(toolCallId, params, signal, onUpdate, ctx);

			// Cardinal rule: never break read.
			if (!result?.content) return result;
			if (result.content.some((c: any) => c?.type === "image")) return result;

			try {
				const rawPath: string | undefined = params?.file_path ?? params?.path;
				if (!rawPath) return result;
				const absPath = resolve(ctx?.cwd ?? process.cwd(), rawPath);
				const hit = await symbolsForFile(absPath);
				if (!hit) {
					debug(`no symbols for ${absPath}`);
					return result;
				}
				const block = renderBlock(hit);
				const textContent = result.content.find((c: any) => c?.type === "text");
				if (textContent) {
					textContent.text = block + textContent.text;
				} else {
					result.content.unshift({ type: "text", text: block });
				}
				debug(`augmented ${absPath}: ${hit.symbols.length}/${hit.total} fetched, ${connectedOf(hit)} with edges`);
			} catch (e: any) {
				debug(`augment skipped: ${e?.message ?? e}`);
			}
			return result;
		},
	});
}

function connectedOf(hit: CmbHit): number {
	return hit.symbols.filter((s) => (s.in_degree ?? 0) + (s.out_degree ?? 0) > 0).length;
}

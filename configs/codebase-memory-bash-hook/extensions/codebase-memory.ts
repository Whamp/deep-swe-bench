/**
 * codebase-memory-mcp bash-search integration for pi.
 *
 * This variant intentionally does NOT override/read-augment the `read` tool.
 * It targets the earlier discovery step instead: bash search/listing results.
 *
 * Cardinal rule: never break tools. Every CMB failure path silently returns the
 * original bash result unchanged. Auto-index/reindex are non-fatal side effects.
 */
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { execFile } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join, relative, resolve, sep } from "node:path";
import { promisify } from "node:util";

const execFileP = promisify(execFile);
const CBM_BIN = "codebase-memory-mcp";
const QUERY_TIMEOUT_MS = 4_000;
const PROJECT_TTL_MS = 60_000;
const INDEX_TIMEOUT_MS = 60_000;
const REINDEX_DEBOUNCE_MS = 1_500;
const SEARCH_SYMBOL_LIMIT = 40;
const FILE_SYMBOL_LIMIT = 20;
const INLINE_SYMBOL_LIMIT = 10;
const FILE_ONLY_LIMIT = 8;
const DEBUG = !!process.env.CBM_PI_DEBUG;
const AUTO_INDEX = ["1", "true", "yes", "on"].includes((process.env.CBM_AUTO_INDEX || "").toLowerCase());

interface CmbProject { name: string; root_path: string; }
interface CmbSymbol {
	name?: string; qualified_name?: string; label?: string; file_path?: string;
	in_degree?: number; out_degree?: number; lines?: number;
	is_exported?: boolean; is_entry_point?: boolean;
}
interface Decision { augment: boolean; reason: string; tokens: string[]; files: string[]; commandKind: string; }

let projectsCache: CmbProject[] | null = null;
let projectsCacheTime = 0;

function debug(msg: string) {
	if (!DEBUG) return;
	try { process.stderr.write(`[cbm-pi] ${msg}\n`); } catch { /* ignore */ }
}

async function cmbExec(args: string[], timeout = QUERY_TIMEOUT_MS): Promise<any> {
	const { stdout } = await execFileP(CBM_BIN, ["cli", ...args], {
		encoding: "utf-8",
		timeout,
		maxBuffer: 20 * 1024 * 1024,
	});
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
	let best: CmbProject | undefined;
	for (const p of projects) {
		const root = p.root_path;
		if (absPath === root || absPath.startsWith(root + sep)) {
			if (!best || root.length > best.root_path.length) best = p;
		}
	}
	return best;
}

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

function escRe(s: string): string {
	return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

async function searchSymbols(project: string, tokens: string[]): Promise<CmbSymbol[]> {
	if (!tokens.length) return [];
	const pattern = tokens.length === 1 ? `.*${escRe(tokens[0])}.*` : `.*(${tokens.map(escRe).join("|")}).*`;
	const d = await cmbExec(["search_graph", JSON.stringify({ project, name_pattern: pattern, limit: SEARCH_SYMBOL_LIMIT })]);
	return Array.isArray(d?.results) ? d.results : [];
}

async function fileSymbols(project: string, file: string): Promise<CmbSymbol[]> {
	const d = await cmbExec(["search_graph", JSON.stringify({ project, file_pattern: file, limit: FILE_SYMBOL_LIMIT })]);
	return Array.isArray(d?.results) ? d.results : [];
}

const SOURCE_EXT_RE = /\.(py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs)$/;
const TEST_PATH_RE = /(^|\/)(__tests__|tests?|testdata|fixtures?)(\/|$)|(_test\.go|\.tests?\.[tj]sx?$|\.spec\.[tj]sx?$|test_.*\.py$|_test\.rs$)/;
const SKIP_PATH_PARTS = [".git/", "node_modules/", "vendor/", "dist/", "build/", "target/", ".cache/", "__pycache__/", "site-packages/", ".venv/", "coverage/"];
const VALIDATION_RE = /\b(go\s+test|go\s+build|cargo\s+(test|check|build)|pytest|python\s+-m\s+pytest|npm\s+(test|run)|npx\s+(tsc|jest|vitest)|pnpm|yarn|make|gofmt|ruff|mypy|git\s+(add|commit|checkout|push|pull|merge|rebase|stash|clean|reset)|pip\s+install|poetry|uv\s+)\b/;
const SEARCH_VERB_RE = /\b(git\s+grep|grep|egrep|fgrep|rg|ripgrep)\b/;
const DISCOVERY_ONLY_RE = /\b(find|fd|ls|tree)\b/;
const DEP_MANIFEST_RE = /\b(go\.sum|go\.mod|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|Cargo\.lock|poetry\.lock)\b/;
const PATH_COLON_RE = /^(?:\x1b\[[0-9;]*m)*(?<path>[^:\n\r]+?):(?<line>\d+)(?::\d+)?:/gm;
const BARE_PATH_RE = /^\s*(?:\.\/)?(?<path>[A-Za-z0-9_./@+\-]+\.(?:py|go|ts|tsx|js|jsx|rs|c|h|cpp|hpp|mjs|cjs))\s*$/gm;
const GIT_STATUS_RE = /^[ MARCUD!?]{1,2}\s+(?<path>.+?)(?: -> (?<new>.+))?$/gm;
const DIFF_STAT_RE = /^\s*(?<path>[^|\n]+?)\s+\|\s+\d+/gm;
const DIFF_GIT_RE = /^diff --git a\/(?<a>.+?) b\/(?<b>.+)$/gm;
const IDENT_RE = /[A-Za-z_][A-Za-z0-9_]{3,95}/g;
const NOISE = new Set(["grep", "egrep", "fgrep", "rg", "find", "xargs", "git", "status", "branch", "show", "current", "short", "head", "tail", "sort", "uniq", "sed", "awk", "cat", "less", "more", "maxdepth", "mindepth", "type", "name", "path", "print", "exec", "include", "exclude", "files", "file", "src", "pkg", "lib", "app", "test", "tests", "true", "false", "null", "package", "config", "index", "main", "from", "import", "const", "func", "def", "class"]);

function splitSegments(command: string): string[] {
	const parts: string[] = [];
	let buf = "";
	let quote = "";
	let esc = false;
	for (let i = 0; i < command.length; i++) {
		const ch = command[i];
		if (esc) { buf += ch; esc = false; continue; }
		if (ch === "\\") { buf += ch; esc = true; continue; }
		if (quote) { buf += ch; if (ch === quote) quote = ""; continue; }
		if (ch === "'" || ch === '"' || ch === "`") { quote = ch; buf += ch; continue; }
		if (command.startsWith("&&", i) || command.startsWith("||", i)) {
			if (buf.trim()) parts.push(buf.trim());
			buf = ""; i++; continue;
		}
		if (ch === ";" || ch === "|") {
			if (buf.trim()) parts.push(buf.trim());
			buf = ""; continue;
		}
		buf += ch;
	}
	if (buf.trim()) parts.push(buf.trim());
	return parts;
}

function shellWords(segment: string): string[] {
	const out: string[] = [];
	let buf = "";
	let quote = "";
	let esc = false;
	for (let i = 0; i < segment.length; i++) {
		const ch = segment[i];
		if (esc) { buf += ch; esc = false; continue; }
		if (ch === "\\") { esc = true; continue; }
		if (quote) { if (ch === quote) quote = ""; else buf += ch; continue; }
		if (ch === "'" || ch === '"' || ch === "`") { quote = ch; continue; }
		if (/\s/.test(ch)) { if (buf) { out.push(buf); buf = ""; } continue; }
		buf += ch;
	}
	if (buf) out.push(buf);
	return out;
}

function normalizePath(path: string): string | null {
	let p = path.trim().replace(/^['"`]|['"`]$/g, "").replace(/\\/g, "/");
	if (p.includes(" -> ")) p = p.split(" -> ").pop() || p;
	while (p.startsWith("./")) p = p.slice(2);
	if (p.startsWith("/app/")) p = p.slice(5);
	if (p.startsWith("a/") || p.startsWith("b/")) p = p.slice(2);
	if (p.startsWith("/") || p.split("/").includes("..")) return null;
	if (SKIP_PATH_PARTS.some((part) => p.includes(part))) return null;
	if (!SOURCE_EXT_RE.test(p)) return null;
	if (TEST_PATH_RE.test(p)) return null;
	return p;
}

function addPath(counts: Map<string, number>, raw?: string) {
	if (!raw) return;
	const p = normalizePath(raw);
	if (!p) return;
	counts.set(p, (counts.get(p) || 0) + 1);
}

function extractOutputFiles(output: string): Map<string, number> {
	const counts = new Map<string, number>();
	for (const m of output.matchAll(PATH_COLON_RE)) addPath(counts, m.groups?.path);
	for (const m of output.matchAll(BARE_PATH_RE)) addPath(counts, m.groups?.path);
	for (const m of output.matchAll(GIT_STATUS_RE)) addPath(counts, m.groups?.new || m.groups?.path);
	for (const m of output.matchAll(DIFF_STAT_RE)) addPath(counts, m.groups?.path);
	for (const m of output.matchAll(DIFF_GIT_RE)) addPath(counts, m.groups?.b);
	return counts;
}

function extractCommandFiles(command: string): Map<string, number> {
	const counts = new Map<string, number>();
	for (const seg of splitSegments(command.slice(0, 4000))) {
		for (const w of shellWords(seg)) {
			if (/[*$(){}[\]]/.test(w)) continue;
			addPath(counts, w);
		}
	}
	return counts;
}

function mergeCounts(a: Map<string, number>, b: Map<string, number>) {
	for (const [k, v] of b) a.set(k, (a.get(k) || 0) + v);
}

function isPatternOpt(cmd: string, opt: string): boolean {
	return ["grep", "egrep", "fgrep", "rg", "ripgrep", "git grep"].includes(cmd) && ["-e", "--regexp"].includes(opt);
}

function extractPatterns(words: string[]): string[] {
	if (!words.length) return [];
	let cmd = words[0];
	let start = 1;
	if (words[0] === "git" && words[1] === "grep") { cmd = "git grep"; start = 2; }
	else if (!["grep", "egrep", "fgrep", "rg", "ripgrep"].includes(cmd)) {
		const i = words.findIndex((w) => ["grep", "egrep", "fgrep", "rg", "ripgrep"].includes(w));
		if (i < 0) return [];
		cmd = words[i]; start = i + 1;
	}
	const patterns: string[] = [];
	for (let i = start; i < words.length;) {
		const w = words[i];
		if (isPatternOpt(cmd, w)) { if (words[i + 1]) patterns.push(words[i + 1]); i += 2; continue; }
		if (w.startsWith("--regexp=")) { patterns.push(w.slice("--regexp=".length)); i++; continue; }
		if (w === "--") { if (words[i + 1]) patterns.push(words[i + 1]); break; }
		if (w.startsWith("-")) {
			if (["-g", "--glob", "--include", "--exclude", "--exclude-dir", "-m", "-A", "-B", "-C", "--context"].includes(w) && words[i + 1]) i += 2;
			else i++;
			continue;
		}
		patterns.push(w); break;
	}
	return patterns;
}

function tokenScore(tok: string): [number, number] {
	const codey = /[a-z][A-Z]|[A-Z][a-z]|_/.test(tok) ? 1 : 0;
	const allcaps = tok.toUpperCase() === tok && tok.length <= 5 ? 1 : 0;
	return [codey - allcaps, tok.length];
}

function tokensFromPatterns(patterns: string[], limit = 5): string[] {
	const seen = new Set<string>();
	const toks: string[] = [];
	for (const pat of patterns) {
		for (const tok of pat.replace(/\\\|/g, "|").match(IDENT_RE) || []) {
			if (seen.has(tok)) continue;
			if (tok === tok.toLowerCase() && NOISE.has(tok)) continue;
			if (tok === tok.toLowerCase() && tok.length < 7) continue;
			seen.add(tok); toks.push(tok);
		}
	}
	toks.sort((a, b) => {
		const as = tokenScore(a), bs = tokenScore(b);
		return (bs[0] - as[0]) || (bs[1] - as[1]);
	});
	return toks.slice(0, limit);
}

function classify(command: string): { kind: string; patterns: string[] } {
	if (VALIDATION_RE.test(command)) return { kind: "skip_validation_or_mutation", patterns: [] };
	let sawSearch = false;
	const patterns: string[] = [];
	for (const seg of splitSegments(command.slice(0, 4000))) {
		const words = shellWords(seg);
		if (!words.length) continue;
		if (SEARCH_VERB_RE.test(words.join(" "))) { sawSearch = true; patterns.push(...extractPatterns(words)); }
		if (words.includes("xargs") && words.some((w) => ["grep", "rg", "ripgrep"].includes(w))) { sawSearch = true; patterns.push(...extractPatterns(words)); }
	}
	if (sawSearch) return { kind: "search", patterns };
	if (DISCOVERY_ONLY_RE.test(command)) return { kind: "skip_listing_no_pattern", patterns: [] };
	return { kind: "skip_other", patterns: [] };
}

function decide(command: string, output: string): Decision {
	const { kind, patterns } = classify(command);
	const counts = extractOutputFiles(output || "");
	mergeCounts(counts, extractCommandFiles(command));
	const files = [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([p]) => p).slice(0, FILE_ONLY_LIMIT);
	if (kind === "search") {
		const tokens = tokensFromPatterns(patterns);
		if (tokens.length && DEP_MANIFEST_RE.test(command) && files.length === 0) return { augment: false, reason: "skip_dependency_manifest_search", tokens: [], files, commandKind: kind };
		if (tokens.length) return { augment: true, reason: "search_with_tokens", tokens, files, commandKind: kind };
		if (files.length) return { augment: true, reason: "search_file_output", tokens: [], files, commandKind: kind };
		return { augment: false, reason: "search_no_good_token", tokens: [], files, commandKind: kind };
	}
	if (kind === "skip_listing_no_pattern" && files.length > 0 && files.length <= FILE_ONLY_LIMIT) return { augment: true, reason: "listing_small_file_output", tokens: [], files, commandKind: kind };
	return { augment: false, reason: kind, tokens: [], files, commandKind: kind };
}

function relFile(sym: CmbSymbol): string { return (sym.file_path || "").replace(/\\/g, "/"); }
function degree(sym: CmbSymbol): number { return (sym.in_degree || 0) + (sym.out_degree || 0); }
function displayName(sym: CmbSymbol): string { return sym.qualified_name || sym.name || "<unknown>"; }

function rankSymbols(symbols: CmbSymbol[], files: string[]): CmbSymbol[] {
	const rank = new Map(files.map((f, i) => [f, i]));
	const seen = new Set<string>();
	return symbols
		.filter((s) => {
			const k = displayName(s) + "\0" + relFile(s);
			if (seen.has(k)) return false;
			seen.add(k); return true;
		})
		.sort((a, b) => {
			const af = relFile(a), bf = relFile(b);
			const ar = files.find((f) => af === f || af.endsWith("/" + f));
			const br = files.find((f) => bf === f || bf.endsWith("/" + f));
			const as = (ar ? 10_000 - (rank.get(ar) || 0) : 0) + degree(a);
			const bs = (br ? 10_000 - (rank.get(br) || 0) : 0) + degree(b);
			return bs - as;
		});
}

function renderBlock(project: string, d: Decision, symbols: CmbSymbol[]): string {
	const shown = symbols.slice(0, INLINE_SYMBOL_LIMIT);
	const L: string[] = [];
	L.push(`┌─ codebase-memory: bash search · ${shown.length}/${symbols.length} graph symbols${d.tokens.length ? ` for ${d.tokens.join(", ")}` : " from search-result files"}`);
	if (d.files.length) L.push(`├─ files from search: ${d.files.slice(0, 5).join(", ")}${d.files.length > 5 ? " …" : ""}`);
	for (const s of shown) {
		const file = relFile(s);
		const label = s.label || "Symbol";
		L.push(`  ${label.padEnd(10)} ${displayName(s)}  ${file}  (callers:${s.in_degree ?? 0} callees:${s.out_degree ?? 0})`);
	}
	L.push(`└─ For more: ${CBM_BIN} cli trace_path '{"project":"${project}","function_name":"QualifiedName","direction":"both"}'`);
	L.push("");
	return L.join("\n");
}

function textFromContent(content: any): string {
	if (typeof content === "string") return content;
	if (Array.isArray(content)) return content.map((c) => typeof c?.text === "string" ? c.text : "").join("");
	return String(content ?? "");
}

function appendContent(content: any, block: string): any {
	if (Array.isArray(content)) {
		const next = content.map((c) => ({ ...c }));
		const idx = next.findIndex((c) => c?.type === "text" && typeof c.text === "string");
		if (idx >= 0) next[idx].text = `${next[idx].text}\n\n${block}`;
		else next.push({ type: "text", text: block });
		return next;
	}
	if (typeof content === "string") return `${content}\n\n${block}`;
	return [{ type: "text", text: block }];
}

async function buildAugment(command: string, output: string, cwd: string): Promise<string | null> {
	const d = decide(command, output);
	if (!d.augment) return null;
	const projects = await listProjects();
	const proj = findProject(resolve(cwd), projects);
	if (!proj) return null;

	let symbols: CmbSymbol[] = [];
	if (d.tokens.length) {
		symbols = await searchSymbols(proj.name, d.tokens);
	} else {
		for (const f of d.files.slice(0, FILE_ONLY_LIMIT)) {
			try { symbols.push(...await fileSymbols(proj.name, f)); } catch { /* keep going */ }
		}
	}
	if (!symbols.length) return null;
	const ranked = rankSymbols(symbols, d.files);
	debug(`bash-augment ${d.reason}: tokens=${d.tokens.join("|") || "-"} files=${d.files.length} symbols=${ranked.length}`);
	return renderBlock(proj.name, d, ranked);
}

export default async function (pi: ExtensionAPI) {
	if (AUTO_INDEX) {
		const root = gitRoot(process.cwd());
		if (root) {
			try {
				debug(`auto-indexing ${root} (CBM_AUTO_INDEX=1, blocking)`);
				const r = await indexRepo(root);
				projectsCache = null;
				debug(`auto-index done: ${r?.status ?? "ok"}, ${r?.nodes ?? 0} nodes`);
			} catch (e: any) {
				debug(`auto-index skipped (non-fatal): ${e?.message ?? e}`);
			}
		}
	}

	pi.on("session_start", () => {
		projectsCache = null;
		projectsCacheTime = 0;
	});

	let reindexTimer: ReturnType<typeof setTimeout> | null = null;
	pi.on("tool_result", async (event: any, ctx: any) => {
		if (AUTO_INDEX && (event?.toolName === "edit" || event?.toolName === "write")) {
			if (reindexTimer) clearTimeout(reindexTimer);
			const cwd = ctx?.cwd ?? process.cwd();
			reindexTimer = setTimeout(() => {
				reindexTimer = null;
				const root = gitRoot(cwd);
				if (!root) return;
				debug(`auto-reindex scheduled for ${root}`);
				indexRepo(root)
					.then((r) => { projectsCache = null; debug(`auto-reindex done: ${r?.status ?? "ok"}, ${r?.nodes ?? 0} nodes`); })
					.catch((e: any) => debug(`auto-reindex skipped (non-fatal): ${e?.message ?? e}`));
			}, REINDEX_DEBOUNCE_MS);
			return;
		}

		if (event?.toolName !== "bash") return;
		try {
			const command = event?.input?.command;
			if (typeof command !== "string" || !command.trim()) return;
			const output = textFromContent(event.content);
			const block = await buildAugment(command, output, ctx?.cwd ?? process.cwd());
			if (!block) return;
			return { content: appendContent(event.content, block) };
		} catch (e: any) {
			debug(`bash augment skipped (non-fatal): ${e?.message ?? e}`);
			return;
		}
	});
}

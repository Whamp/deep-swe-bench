// Typed fetch client for the Python dashboard API.

import type {
  RunsResponse,
  RunSummary,
  RunDetail,
  DetailLevel,
  CompareResponse,
  SubsetsResponse,
  RunScore,
  CellSession,
} from "./types";

const API_BASE = "/api";

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) {
    const text = await res.text().catch(() => res.statusText);
    throw new ApiError(res.status, text);
  }
  return res.json() as Promise<T>;
}

export async function fetchRuns(detail: DetailLevel = "summary"): Promise<RunSummary[]> {
  const data = await getJSON<RunsResponse>(`${API_BASE}/runs?detail=${detail}`);
  return data.runs;
}

export async function fetchRun(
  runId: string,
  detail: DetailLevel = "operational",
): Promise<RunDetail> {
  return getJSON<RunDetail>(`${API_BASE}/runs/${encodeURIComponent(runId)}?detail=${detail}`);
}

export async function fetchRunEvents(
  runId: string,
  limit = 100,
  after?: number,
): Promise<Array<Record<string, unknown>>> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (after !== undefined) params.set("after", String(after));
  const data = await getJSON<{ events: Array<Record<string, unknown>> }>(
    `${API_BASE}/runs/${encodeURIComponent(runId)}/events?${params}`,
  );
  return data.events;
}

export async function fetchCompare(opts?: {
  subset?: string;
  reps?: number;
}): Promise<CompareResponse> {
  const params = new URLSearchParams();
  if (opts?.subset) params.set("subset", opts.subset);
  if (opts?.reps && opts.reps > 0) params.set("reps", String(opts.reps));
  const qs = params.toString();
  return getJSON<CompareResponse>(`${API_BASE}/compare${qs ? `?${qs}` : ""}`);
}

export async function fetchSubsets(): Promise<SubsetsResponse> {
  return getJSON<SubsetsResponse>(`${API_BASE}/subsets`);
}

export async function fetchRunScore(runId: string): Promise<RunScore | null> {
  const data = await getJSON<{ score?: RunScore }>(
    `${API_BASE}/runs/${encodeURIComponent(runId)}/score`,
  );
  return data.score ?? null;
}

export async function fetchCellSession(resultPath: string, tail = 30): Promise<CellSession> {
  const params = new URLSearchParams({ path: resultPath, tail: String(tail) });
  const data = await getJSON<{ session: CellSession }>(`${API_BASE}/cell-session?${params}`);
  return data.session;
}

export async function fetchFile(path: string, tail = 200): Promise<string> {
  const params = new URLSearchParams({ path, tail: String(tail) });
  const res = await fetch(`${API_BASE}/file?${params}`);
  if (!res.ok) throw new ApiError(res.status, await res.text().catch(() => res.statusText));
  return res.text();
}

export { ApiError };

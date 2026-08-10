// Types matching the Python API response shapes from harness/run_state.py

export type RunState = "running" | "stalled" | "completed" | "paused" | "failed" | "unknown";
export type CellState = "pending" | "running" | "skipped" | "done" | "passed" | "failed";
export type CellOutcome = "ok" | "empty" | "skipped" | "timeout" | "transient" | "failed";
export type DetailLevel = "summary" | "operational" | "diagnostic";
export type RunKind = "structured" | "legacy";

export interface Counts {
  batch_total?: number;
  batch_done?: number;
  batch_running?: number;
  batch_skipped?: number;
  preflight_done?: number;
  preflight_failed?: number;
  preflight_running?: number;
  preflight_skipped?: number;
  ok?: number;
  empty?: number;
  timeout?: number;
  transient?: number;
  failed?: number;
}

export interface CellSummary {
  reward_binary?: number;
  reward_partial?: number;
  f2p?: number;
  p2p?: number;
  total_tokens?: number;
  input_tokens?: number;
  output_tokens?: number;
  cache_read_tokens?: number;
  cache_write_tokens?: number;
  cost_usd?: number;
  combined_total_tokens?: number;
  combined_cost_usd?: number;
  agent_wall_s?: number;
  agent_exit?: number;
  agent_timed_out?: boolean;
  patch_bytes?: number;
  [key: string]: number | boolean | string | null | undefined;
}

export interface Cell {
  cell_id?: string;
  task?: string;
  config?: string;
  rep?: number;
  state?: CellState;
  outcome?: CellOutcome;
  started_at?: string;
  finished_at?: string;
  result_path?: string;
  log_path?: string;
  contract_path?: string;
  reason?: string;
  diagnostics?: Array<{
    requirement?: string;
    target?: string;
    reason?: string;
  }>;
  kind?: string;
  summary?: CellSummary;
  cell_age_s?: number;
  potentially_stale?: boolean;
}

export interface RunPaths {
  run_dir?: string;
  manifest?: string;
  status?: string;
  events?: string;
}

export interface RunSummary {
  kind: RunKind;
  run_id: string;
  /** Unique routing key (directory name). Used for navigation to avoid collisions when two runs share a manifest run_id. */
  run_key?: string;
  state: RunState;
  declared_state?: string;
  stage?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  heartbeat_at?: string | null;
  heartbeat_age_s?: number | null;
  eta_s?: number | null;
  model?: string | null;
  thinking?: string | null;
  configs?: string[];
  launch_metadata: "confirmed_plan" | "legacy_structured" | "legacy_track";
  launch_plan_identity?: string | null;
  preflight_state:
    | "not_required"
    | "pending"
    | "running"
    | "passed"
    | "failed"
    | "skipped"
    | "incomplete"
    | "unknown";
  results_root?: string | null;
  state_root?: string | null;
  workspace?: string | null;
  selection?: Record<string, unknown>;
  workers?: number | null;
  counts: Counts;
  active_count: number;
  max_cell_age_s?: number | null;
  stale_cell_count: number;
  failure_buckets?: Record<string, number>;
  score_snapshot?: { solved: number; finished: number; solve_rate: number };
}

export interface RunDetail extends RunSummary {
  paths?: RunPaths;
  active_cells?: Cell[];
  /** Every terminal batch rep, retained for result and session inspection. */
  finished_cells?: Cell[];
  /** Bounded compatibility view of the 30 most recently finished reps. */
  recent_finished?: Cell[];
  preflight?: Record<string, Cell>;
  events_tail?: Array<Record<string, unknown>>;
  manifest?: Record<string, unknown>;
  status?: Record<string, unknown>;
  track_tail?: string[];
}

export interface RunsResponse {
  runs: RunSummary[];
}

// Comparison data types (for /api/compare)
export interface ComparisonCell {
  task: string;
  config: string;
  rep: number;
  reward_binary: number;
  reward_partial: number;
  total_tokens: number;
  cost_usd: number;
  agent_wall_s: number;
  patch_bytes: number;
  difficulty?: "hard" | "medium" | "easy" | "unknown";
  language?: string;
}

export interface ComparisonRun {
  run_id: string;
  model: string | null;
  thinking: string | null;
  config: string;
  state: RunState;
  total_cells: number;
  distinct_tasks: number;
  solved: number;
  solve_rate: number;
  mean_partial: number;
  median_cost: number;
  median_tokens: number;
  median_wall_s: number;
  total_cost: number;
  cells: ComparisonCell[];
}

export interface CompareResponse {
  runs: ComparisonRun[];
  subset?: string | null;
}

export interface Subset {
  name: string;
  task_count: number;
  tasks: string[];
}

export interface SubsetsResponse {
  subsets: Subset[];
}

// Live score projection (from /api/runs/<id>/score — events.ndjson replay)
export interface ScorePoint {
  ts: string | null;
  finished: number;
  solved: number;
  cost: number;
  mean_partial: number;
  tool_calls: number;
  tool_call_errors: number;
  tool_call_error_rate: number | null;
}

export interface ScoreTask {
  task: string;
  best_reward_binary: number;
  best_reward_partial: number;
  reps: number;
  solved: boolean;
  last_outcome: string;
}

export interface RunScore {
  finished: number;
  processed: number;
  solved: number;
  tasks_total: number;
  tasks_solved: number;
  solve_rate: number;
  mean_partial: number;
  tool_calls: number;
  tool_call_errors: number;
  tool_call_error_rate: number | null;
  active: number;
  cumulative_cost: number;
  cost_per_solve: number;
  projected_total_cost: number;
  throughput_cells_per_hr: number;
  eta_s: number | null;
  failure_breakdown: Record<string, number>;
  timeline: ScorePoint[];
  tasks: ScoreTask[];
}

// Cell session activity (from /api/cell-session — JSONL turn timeline)
export interface SessionTurn {
  idx: number;
  ts: string | null;
  intent: string | null;
  tools: string[];
  targets: string[];
  token_delta: number;
  cost_delta: number;
  cumulative_tokens: number;
  cumulative_cost: number;
}

export interface CellSession {
  found: boolean;
  path?: string;
  turns?: number;
  total_tokens?: number;
  total_cost?: number;
  tool_calls?: number;
  tool_call_errors?: number;
  tool_call_error_rate?: number | null;
  distinct_tools?: string[];
  last_intent?: string | null;
  started_at?: string | null;
  updated_at?: number | null;
  is_live?: boolean;
  truncated?: boolean;
  turns_list?: SessionTurn[];
  error?: string;
}

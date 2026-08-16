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
  result_path: string;
  reward_binary: number;
  reward_partial: number;
  total_tokens: number;
  reported_total_tokens?: number;
  cache_read_tokens?: number;
  adjusted_tokens?: number;
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
  total_reported_tokens?: number;
  total_cache_read_tokens?: number;
  total_adjusted_tokens?: number;
  cache_read_share?: number;
  solves_per_million_adjusted_tokens?: number | null;
  token_policy?: string;
  cache_read_weight?: number;
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

/** One browsable file stored inside a benchmark cell. */
export interface CellTrajectoryArtifact {
  path: string;
  relative_path: string;
  kind: "patch" | "tests" | "log" | "result" | "session" | "other";
  size: number;
}

/** Compact verifier counts read from the cell's CTRF report. */
export interface CellTrajectoryTestSummary {
  tests: number;
  passed: number;
  failed: number;
  skipped: number;
  pending: number;
  other: number;
}

/** Provider usage recorded for one assistant trajectory turn. */
export interface CellTrajectoryTurnUsage {
  input_tokens: number;
  output_tokens: number;
  cache_read_tokens: number;
  cache_write_tokens: number;
  reasoning_tokens: number;
  total_tokens: number;
  cost: number;
}

/** Complete tool output paired to its originating call ID. */
export interface CellTrajectoryToolResult {
  timestamp: string | number | null;
  text: string;
  is_error: boolean;
  details: unknown;
  duration_ms: number;
}

/** A reasoning or assistant text block in original message order. */
export interface CellTrajectoryTextBlock {
  type: "thinking" | "text";
  text: string;
}

/** A tool invocation with unmodified arguments and complete paired output. */
export interface CellTrajectoryToolCallBlock {
  type: "tool_call";
  id: string;
  name: string;
  arguments: unknown;
  result: CellTrajectoryToolResult | null;
}

/** A tool result whose originating call was absent from the session log. */
export interface CellTrajectoryOrphanResultBlock extends CellTrajectoryToolResult {
  type: "tool_result";
  id: string;
  name: string;
}

/** An unrecognized provider block retained instead of silently discarded. */
export interface CellTrajectoryUnknownBlock {
  type: "unknown";
  data: Record<string, unknown>;
}

/** One original-order content block within an assistant turn. */
export type CellTrajectoryBlock =
  | CellTrajectoryTextBlock
  | CellTrajectoryToolCallBlock
  | CellTrajectoryOrphanResultBlock
  | CellTrajectoryUnknownBlock;

/** One complete assistant turn and all tool results that followed it. */
export interface CellTrajectoryTurn {
  idx: number;
  id: string | null;
  timestamp: string | number | null;
  elapsed_s: number | null;
  stop_reason: string | null;
  error: string | null;
  usage: CellTrajectoryTurnUsage;
  cumulative_cost: number;
  observation_chars: number;
  command_time_ms: number;
  blocks: CellTrajectoryBlock[];
}

/** Small all-turn datapoint used for trajectory charts and turn navigation. */
export interface CellTrajectoryMetric {
  idx: number;
  timestamp: string | number | null;
  intent: string | null;
  cumulative_cost: number;
  context_tokens: number;
  output_tokens: number;
  total_tokens: number;
  observation_chars: number;
  command_time_ms: number;
}

/** Allowlisted result metadata shown in a trajectory header. */
export interface CellTrajectoryCell extends CellSummary {
  result_path: string;
  cell_path: string;
  task?: string;
  config?: string;
  rep?: number;
  model?: string;
  thinking_level?: string;
  language?: string;
  category?: string;
}

/** Native Pi session identity and live-file state for a trajectory. */
export interface CellTrajectorySession {
  id?: string | null;
  cwd?: string | null;
  provider?: string | null;
  model?: string | null;
  thinking_level?: string | null;
  started_at?: string | null;
  path: string;
  updated_at: number;
  is_live: boolean;
}

/** Paginated complete trajectory response for one benchmark cell. */
export interface CellTrajectory {
  found: boolean;
  error?: string;
  cell?: CellTrajectoryCell;
  session?: CellTrajectorySession;
  prompt?: string;
  artifacts?: CellTrajectoryArtifact[];
  test_summary?: CellTrajectoryTestSummary | null;
  total_turns?: number;
  offset?: number;
  limit?: number;
  has_previous?: boolean;
  has_next?: boolean;
  turns?: CellTrajectoryTurn[];
  metrics?: CellTrajectoryMetric[];
}

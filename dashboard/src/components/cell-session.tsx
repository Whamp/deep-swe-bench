import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchCellSession } from "@/lib/api";
import type { Cell, CellSession, SessionTurn } from "@/lib/types";
import { Sparkline } from "@/components/sparkline";
import { Badge } from "@/components/ui/badge";
import { fmtTokens, fmtCost, fmtPercent } from "@/lib/metrics";

interface CellSessionPanelProps {
  cell: Cell;
  onClose: () => void;
}

/**
 * Focused-cell drill-in: parses the agent's session JSONL (server-side) into a
 * turn timeline. Each turn shows the agent's self-narrated intent, the tools it
 * touched, and its token/cost delta. Polls only while the transcript is still
 * being written (a terminal cell stops polling). Works for both native-pi and
 * pi-fabric sessions (the server unwraps fabric's inner tools).
 */
export function CellSessionPanel({ cell, onClose }: CellSessionPanelProps) {
  const resultPath = cell.result_path;
  const {
    data: session,
    isLoading,
    error,
  } = useQuery({
    queryKey: ["cell-session", resultPath],
    queryFn: () => fetchCellSession(resultPath!, 40),
    enabled: !!resultPath,
    // Stop polling once the transcript is no longer being written to. Uses the
    // function form so the decision can read the latest data without referencing
    // the `session` binding this hook defines.
    refetchInterval: (query) =>
      (query.state.data as CellSession | undefined)?.is_live ? 4000 : false,
  });

  // Wire the "Esc" the close button promises.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const turns = (session?.turns_list || []).slice().reverse(); // newest first

  return (
    <div
      className="fixed inset-0 z-50 flex justify-end bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label={`Session for ${cell.task}`}
      onClick={onClose}
    >
      <div
        className="flex h-full w-full max-w-xl flex-col border-l border-border bg-card shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-3 border-b border-border p-4">
          <div className="min-w-0">
            <div className="truncate text-sm font-semibold">{cell.task}</div>
            <div className="mt-0.5 text-xs text-muted-foreground">
              {cell.config} · rep {cell.rep ?? "—"}
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close session panel"
            className="rounded-md border border-border px-2 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            Esc ✕
          </button>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-auto">
          {isLoading && <div className="p-4 text-sm text-muted-foreground">Loading session…</div>}
          {error && <div className="p-4 text-sm text-red-400">Unable to load session.</div>}
          {session && !session.found && (
            <div className="p-4 text-sm text-muted-foreground">
              No session transcript yet.{" "}
              {session.error ? `(${session.error})` : "It appears once the agent starts working."}
            </div>
          )}
          {session?.found && (
            <>
              <SessionSummary cell={cell} session={session} turns={turns} />
              <div className="border-t border-border">
                <div className="px-4 py-2 text-[10px] uppercase tracking-wide text-muted-foreground">
                  Turn timeline {session.truncated ? "(most recent)" : ""}
                </div>
                {turns.map((t) => (
                  <TurnRow key={t.idx} turn={t} />
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

function SessionSummary({
  cell,
  session,
  turns,
}: {
  cell: Cell;
  session: CellSession;
  turns: SessionTurn[];
}) {
  const s = cell.summary || {};
  const allTurns = session.turns_list || [];
  // LIVE only when the transcript is still being written AND the cell is still
  // running — a just-finished cell's file is <3min old but is not live.
  const isRunning = cell.state === "running";
  const live = !!session.is_live && isRunning;
  const lastTurnTs = turns[0]?.ts;
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!live) return;
    const id = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(id);
  }, [live]);

  return (
    <div className="space-y-3 p-4">
      <div className="flex items-center gap-2">
        {live ? (
          <span className="flex items-center gap-1.5 text-xs font-medium text-green-400">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-green-400 opacity-60" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-green-400" />
            </span>
            LIVE
          </span>
        ) : (
          <span className="text-xs text-muted-foreground">{isRunning ? "idle" : "finished"}</span>
        )}
        <span className="text-xs text-muted-foreground">
          {String(session.turns ?? "—")} turns · {fmtTokens(session.total_tokens)} ·{" "}
          {fmtCost(session.total_cost)}
        </span>
        {s.reward_binary !== undefined && (
          <Badge variant={s.reward_binary >= 1 ? "ok" : "empty"}>
            {s.reward_binary >= 1 ? "solved" : "not solved"}
          </Badge>
        )}
        {session.tool_calls !== undefined && session.tool_calls > 0 && (
          <Badge variant={(session.tool_call_errors || 0) > 0 ? "failed" : "default"}>
            {session.tool_call_errors || 0}/{session.tool_calls} tool calls ·{" "}
            {fmtPercent(session.tool_call_error_rate)} error rate
          </Badge>
        )}
      </div>

      {/* Honest liveness: seconds since the last recorded turn. More reliable
          than the mtime dot — answers "stuck or working?" directly. */}
      {lastTurnTs && (
        <div className="text-[11px] text-muted-foreground">
          last turn {secondsAgo(lastTurnTs, now)} ago
        </div>
      )}

      {session.last_intent && (
        <div className="rounded-md border border-border bg-background/50 p-2">
          <div className="text-[10px] uppercase tracking-wide text-muted-foreground">
            Latest activity
          </div>
          <div className="text-sm">{String(session.last_intent)}</div>
        </div>
      )}

      <div className="flex flex-wrap items-center gap-2">
        {session.distinct_tools?.map((tool) => (
          <Badge key={tool}>{tool}</Badge>
        ))}
        <Sparkline
          data={allTurns.map((t) => t.cumulative_tokens)}
          color="hsl(var(--primary))"
          width={150}
          height={28}
          ariaLabel="Cumulative tokens per turn"
        />
        <span className="text-[10px] text-muted-foreground">tokens</span>
      </div>
    </div>
  );
}

function TurnRow({ turn }: { turn: SessionTurn }) {
  const hasTools = turn.tools.length > 0;
  return (
    <div className="border-t border-border/50 px-4 py-2.5">
      <div className="flex items-baseline gap-2">
        <span className="font-mono text-[10px] text-muted-foreground">{turn.idx}</span>
        <span className="flex-1 text-sm">
          {turn.intent || <span className="italic text-muted-foreground">no recorded intent</span>}
        </span>
        <span className="font-mono text-[10px] text-muted-foreground">
          +{fmtTokens(turn.token_delta)}
        </span>
      </div>
      {/* Tools and the files/cmds touched are rendered as SEPARATE rows. The
          parser collects them independently (it cannot reliably bind a tool to
          a specific target inside a fabric JS blob), so we do not imply a
          per-call binding by zipping them. */}
      {hasTools && (
        <div className="mt-1 space-y-1 pl-5">
          <div className="flex flex-wrap gap-1.5">
            {turn.tools.map((tool, i) => (
              <span
                key={`${tool}-${i}`}
                className="rounded border border-border bg-background/60 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
              >
                {tool}
              </span>
            ))}
          </div>
          {turn.targets.length > 0 && (
            <div className="flex flex-wrap gap-x-3 gap-y-0.5 font-mono text-[10px] text-muted-foreground/80">
              {turn.targets.map((t, i) => (
                <span key={`tgt-${i}`} className="max-w-full truncate">
                  {t}
                </span>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function secondsAgo(ts: string, now: number): string {
  const t = new Date(ts).getTime();
  if (!Number.isFinite(t)) return "—";
  const s = Math.max(0, Math.round((now - t) / 1000));
  if (s < 60) return `${s}s`;
  if (s < 3600) return `${Math.round(s / 60)}m`;
  return `${(s / 3600).toFixed(1)}h`;
}

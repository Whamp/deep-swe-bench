import type {
  CellTrajectoryBlock,
  CellTrajectoryOrphanResultBlock,
  CellTrajectoryToolCallBlock,
  CellTrajectoryTurn,
  CellTrajectoryUnknownBlock,
} from "@/lib/types";
import { fmtCost, fmtSeconds, fmtTokens } from "@/lib/metrics";
import { cn } from "@/lib/utils";

/** Output density for complete trajectory turn rendering. */
export type TrajectoryDensity = "focus" | "full";

/** Render one complete assistant turn and its paired tool results. */
export function CellTrajectoryTurnCard({
  turn,
  density,
}: {
  turn: CellTrajectoryTurn;
  density: TrajectoryDensity;
}) {
  return (
    <article
      id={`turn-${turn.idx}`}
      className="scroll-mt-28 rounded-lg border border-border bg-card"
    >
      <header className="flex flex-wrap items-center gap-x-3 gap-y-1 border-b border-border px-3 py-2 text-xs">
        <span className="font-mono font-semibold text-primary">Turn {turn.idx}</span>
        <span className="text-muted-foreground">{formatTrajectoryTimestamp(turn.timestamp)}</span>
        {turn.elapsed_s != null && (
          <span className="text-muted-foreground">+{fmtSeconds(turn.elapsed_s)}</span>
        )}
        <span className="ml-auto tabular-nums text-muted-foreground">
          {fmtTokens(turn.usage.total_tokens)} · {fmtCost(turn.usage.cost)}
        </span>
      </header>
      <div className="space-y-3 p-3">
        {turn.error && (
          <pre className="whitespace-pre-wrap break-words rounded-md border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-300">
            {turn.error}
          </pre>
        )}
        {turn.blocks.map((block, index) => (
          <TrajectoryBlockView
            key={`${block.type}-${"id" in block ? String(block.id) : index}`}
            block={block}
            density={density}
          />
        ))}
        {turn.blocks.length === 0 && !turn.error && (
          <p className="text-sm italic text-muted-foreground">No recorded assistant content.</p>
        )}
      </div>
    </article>
  );
}

function TrajectoryBlockView({
  block,
  density,
}: {
  block: CellTrajectoryBlock;
  density: TrajectoryDensity;
}) {
  switch (block.type) {
    case "thinking":
      return density === "full" ? (
        <TrajectoryTextSection label="Reasoning" text={block.text} muted />
      ) : (
        <details className="rounded-md border border-border/70 bg-background/30">
          <summary className="cursor-pointer px-3 py-2 text-xs font-medium text-muted-foreground">
            Reasoning
          </summary>
          <pre className="whitespace-pre-wrap break-words border-t border-border/70 p-3 text-sm text-muted-foreground">
            {block.text}
          </pre>
        </details>
      );
    case "text":
      return <TrajectoryTextSection label="Assistant" text={block.text} />;
    case "tool_call":
      return <TrajectoryToolCallView call={block} density={density} />;
    case "tool_result":
      return <TrajectoryOrphanResultView result={block} density={density} />;
    case "unknown":
      return <TrajectoryUnknownBlockView block={block} density={density} />;
  }
}

function TrajectoryTextSection({
  label,
  text,
  muted = false,
}: {
  label: string;
  text: string;
  muted?: boolean;
}) {
  return (
    <section>
      <div className="mb-1 text-[10px] font-medium uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
      <pre
        className={cn(
          "whitespace-pre-wrap break-words text-sm leading-6",
          muted && "text-muted-foreground",
        )}
      >
        {text}
      </pre>
    </section>
  );
}

function TrajectoryToolCallView({
  call,
  density,
}: {
  call: CellTrajectoryToolCallBlock;
  density: TrajectoryDensity;
}) {
  const result = call.result;
  const resultOpen = density === "full" || Boolean(result?.is_error);
  return (
    <section className="overflow-hidden rounded-md border border-border bg-background/45">
      <header className="flex flex-wrap items-center gap-2 border-b border-border bg-muted/30 px-3 py-2">
        <span className="font-mono text-xs font-semibold text-primary">{call.name}</span>
        {result && (
          <span className="text-[10px] tabular-nums text-muted-foreground">
            {fmtSeconds(result.duration_ms / 1_000)}
          </span>
        )}
        {result?.is_error && (
          <span className="rounded bg-red-500/15 px-1.5 py-0.5 text-[10px] font-medium text-red-300">
            error
          </span>
        )}
      </header>
      <div className="space-y-2 p-3">
        <div>
          <div className="mb-1 text-[10px] uppercase tracking-wide text-muted-foreground">
            Arguments
          </div>
          <pre className="max-h-80 overflow-auto whitespace-pre-wrap break-words rounded bg-black/20 p-2 text-xs leading-5">
            {formatTrajectoryValue(call.arguments)}
          </pre>
        </div>
        {result ? (
          density === "full" ? (
            <ToolResultBody result={result} detailsOpen />
          ) : (
            <details open={resultOpen}>
              <summary className="cursor-pointer text-xs font-medium text-muted-foreground">
                Output · {formatCharacterCount(result.text.length)}
              </summary>
              <div className="mt-2">
                <ToolResultBody result={result} />
              </div>
            </details>
          )
        ) : (
          <p className="text-xs italic text-muted-foreground">No matching tool result recorded.</p>
        )}
      </div>
    </section>
  );
}

function ToolResultBody({
  result,
  detailsOpen = false,
}: {
  result: NonNullable<CellTrajectoryToolCallBlock["result"]>;
  detailsOpen?: boolean;
}) {
  return (
    <div className="space-y-2">
      <pre
        className={cn(
          "max-h-[42rem] overflow-auto whitespace-pre-wrap break-words rounded p-2 text-xs leading-5",
          result.is_error ? "bg-red-500/10 text-red-200" : "bg-black/20",
        )}
      >
        {result.text || "(empty output)"}
      </pre>
      {result.details != null && (
        <details open={detailsOpen}>
          <summary className="cursor-pointer text-[11px] text-muted-foreground">
            Structured details
          </summary>
          <pre className="mt-1 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded bg-black/20 p-2 text-xs">
            {formatTrajectoryValue(result.details)}
          </pre>
        </details>
      )}
    </div>
  );
}

function TrajectoryOrphanResultView({
  result,
  density,
}: {
  result: CellTrajectoryOrphanResultBlock;
  density: TrajectoryDensity;
}) {
  return (
    <section className="rounded-md border border-amber-500/30 bg-amber-500/5 p-3">
      <div className="mb-2 text-xs font-medium text-amber-300">Unpaired result · {result.name}</div>
      {density === "full" ? (
        <ToolResultBody result={result} detailsOpen />
      ) : (
        <details open={result.is_error}>
          <summary className="cursor-pointer text-xs text-muted-foreground">Show output</summary>
          <div className="mt-2">
            <ToolResultBody result={result} />
          </div>
        </details>
      )}
    </section>
  );
}

function TrajectoryUnknownBlockView({
  block,
  density,
}: {
  block: CellTrajectoryUnknownBlock;
  density: TrajectoryDensity;
}) {
  return (
    <details open={density === "full"} className="rounded-md border border-border/70 p-3">
      <summary className="cursor-pointer text-xs text-muted-foreground">
        Unrecognized provider block
      </summary>
      <pre className="mt-2 whitespace-pre-wrap break-words text-xs">
        {formatTrajectoryValue(block.data)}
      </pre>
    </details>
  );
}

function formatTrajectoryTimestamp(value: string | number | null): string {
  if (value == null) return "time unavailable";
  const date = new Date(
    typeof value === "number" && value < 10_000_000_000 ? value * 1_000 : value,
  );
  return Number.isFinite(date.getTime()) ? date.toLocaleTimeString() : String(value);
}

function formatTrajectoryValue(value: unknown): string {
  if (typeof value === "string") return value;
  try {
    return JSON.stringify(value, null, 2);
  } catch {
    return String(value);
  }
}

function formatCharacterCount(value: number): string {
  return value >= 1_000 ? `${(value / 1_000).toFixed(1)}k chars` : `${value} chars`;
}

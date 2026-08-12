import { useEffect, useId, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { fetchFile } from "@/lib/api";
import type { CellTrajectoryArtifact } from "@/lib/types";

/** Render a selectable text preview for one class of cell artifacts. */
export function CellTrajectoryArtifactViewer({
  artifacts,
  kinds,
  emptyMessage,
}: {
  artifacts: CellTrajectoryArtifact[];
  kinds: CellTrajectoryArtifact["kind"][];
  emptyMessage: string;
}) {
  const artifactSelectId = useId();
  const matching = useMemo(
    () => artifacts.filter((artifact) => kinds.includes(artifact.kind)),
    [artifacts, kinds],
  );
  const defaultArtifact = matching.find((artifact) => artifact.size > 0) ?? matching[0];
  const [selectedPath, setSelectedPath] = useState(defaultArtifact?.path ?? "");

  useEffect(() => {
    if (!matching.some((artifact) => artifact.path === selectedPath)) {
      setSelectedPath(defaultArtifact?.path ?? "");
    }
  }, [defaultArtifact, matching, selectedPath]);

  const selected = matching.find((artifact) => artifact.path === selectedPath) ?? defaultArtifact;
  const previewMode = selected?.kind === "log" ? "tail" : "head";
  const preview = useQuery({
    queryKey: ["cell-artifact", selected?.path, previewMode],
    queryFn: () => fetchFile(selected!.path, 2_000, previewMode),
    enabled: Boolean(selected),
    staleTime: Infinity,
  });

  if (!selected) {
    return (
      <p className="rounded-md border border-border p-6 text-sm text-muted-foreground">
        {emptyMessage}
      </p>
    );
  }

  const previewUrl = `/api/file?${new URLSearchParams({
    path: selected.path,
    [previewMode]: "2000",
  })}`;
  const downloadUrl = `/api/file?${new URLSearchParams({
    path: selected.path,
    download: "1",
  })}`;
  return (
    <section className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <label className="text-xs text-muted-foreground" htmlFor={artifactSelectId}>
          File
        </label>
        <select
          id={artifactSelectId}
          value={selected.path}
          onChange={(event) => setSelectedPath(event.target.value)}
          className="min-w-0 max-w-full rounded-md border border-border bg-background px-2 py-1.5 font-mono text-xs"
        >
          {matching.map((artifact) => (
            <option key={artifact.path} value={artifact.path}>
              {artifact.relative_path} · {formatArtifactBytes(artifact.size)}
            </option>
          ))}
        </select>
        <a
          href={previewUrl}
          target="_blank"
          rel="noreferrer"
          className="text-xs text-primary hover:underline"
        >
          open preview ↗
        </a>
        <a href={downloadUrl} className="text-xs text-primary hover:underline">
          download full file ↓
        </a>
      </div>
      <p className="text-[11px] text-muted-foreground">
        Preview shows the {previewMode === "head" ? "first" : "last"} 2,000 lines, capped at 256 KB.
        Download returns the complete stored file.
      </p>
      {preview.isLoading && <p className="text-sm text-muted-foreground">Loading artifact…</p>}
      {preview.error && <p className="text-sm text-red-400">Unable to load artifact preview.</p>}
      {preview.data != null && (
        <pre className="max-h-[65vh] overflow-auto whitespace-pre-wrap break-words rounded-md border border-border bg-black/20 p-3 text-xs leading-5">
          {preview.data || "(empty file)"}
        </pre>
      )}
    </section>
  );
}

function formatArtifactBytes(bytes: number): string {
  if (bytes < 1_000) return `${bytes} B`;
  if (bytes < 1_000_000) return `${(bytes / 1_000).toFixed(1)} KB`;
  return `${(bytes / 1_000_000).toFixed(1)} MB`;
}

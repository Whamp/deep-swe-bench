const SENTINEL = process.env.OM_VISIBILITY_SENTINEL ?? "OM_VISIBILITY_SENTINEL_UNSET";
const OBS_ID = "abc123abc123";

function lastSourceEntry(entries: any[]): any | undefined {
  for (let i = entries.length - 1; i >= 0; i--) {
    const type = entries[i]?.type;
    if (type === "message" || type === "custom_message" || type === "branch_summary") return entries[i];
  }
  return undefined;
}

function seed(pi: any, ctx: any): string {
  const entries = ctx?.sessionManager?.getBranch?.() ?? [];
  const source = lastSourceEntry(entries);
  if (!source?.id) return "NO_SOURCE_ENTRY";
  const content = `Seeded observational-memory smoke sentinel: ${SENTINEL}`;
  pi.appendEntry("om.observations.recorded", {
    observations: [
      {
        id: OBS_ID,
        content,
        timestamp: "2026-07-01T00:00:00.000Z",
        relevance: "critical",
        sourceEntryIds: [source.id],
        tokenCount: Math.ceil(content.length / 4),
      },
    ],
    coversUpToId: source.id,
  });
  return `SEEDED ${OBS_ID} after ${source.id}`;
}

export default function seedOmMemory(pi: any) {
  pi.registerCommand("seedom", {
    description: "Seed a deterministic OM observation for visibility smoke tests",
    handler: async (_args: string, ctx: any) => {
      const result = seed(pi, ctx);
      ctx?.ui?.notify?.(result, "info");
    },
  });
}

export const tool = {
    description: "Execute type-checked TypeScript through Fabric's configured executor for Pi core tools, MCP, Fabric providers, discovery, and extensions. QuickJS is isolated by default; the optional Node process is an unsafe trusted-code escape hatch. In full code mode, and always in Schema enforce mode, this is the exclusive model tool path.",
    promptSnippet: "Pi core tools, MCP, Fabric providers, discovery, and extensions",
    promptGuidelines: [
        "Batch independent operations in one `fabric_exec` program (`Promise.all` for parallel, sequential `await` for ordered), not one call per tool; keep dependent/conditional steps sequential. Return only the compact final value; intermediate results stay in the sandbox.",
    ],
};

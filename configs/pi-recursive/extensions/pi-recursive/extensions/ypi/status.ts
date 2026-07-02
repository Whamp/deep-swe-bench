import type { ExtensionContext } from "@earendil-works/pi-coding-agent";
import { currentDepth, maxDepth } from "./env.ts";

export function updateStatus(ctx: ExtensionContext): void {
	const label = ctx.ui.theme.fg("accent", "ypi");
	const depthInfo = ctx.ui.theme.fg("dim", ` ∞ depth ${currentDepth()}/${maxDepth()}`);
	ctx.ui.setStatus("ypi", label + depthInfo);
	ctx.ui.setTitle("ypi");
}

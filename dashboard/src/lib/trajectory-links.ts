/** Build a deep link for one benchmark cell trajectory. */
export function cellTrajectoryHref(resultPath: string): string {
  return `/trajectory?${new URLSearchParams({ path: resultPath })}`;
}

/** Build a synchronized side-by-side link for two matched cell trajectories. */
export function pairedCellTrajectoryHref(leftResultPath: string, rightResultPath: string): string {
  return `/trajectory?${new URLSearchParams({
    left: leftResultPath,
    right: rightResultPath,
  })}`;
}

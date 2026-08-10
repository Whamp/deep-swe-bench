// Tiny dependency-free SVG sparkline. Used for live cost/token/solve trends on
// the run page where a full Recharts block would be visual noise. Keeps to the
// dashboard's CSS variable palette so it matches the theme.

interface SparklineProps {
  /** Y values in series order. Missing/invalid points are skipped. */
  data: Array<number | null | undefined>;
  width?: number;
  height?: number;
  /** CSS color (theme var or literal) for the line. */
  color?: string;
  /** Optional fill under the line (defaults to a faint version of color). */
  fill?: boolean;
  strokeWidth?: number;
  /** Optional second series drawn behind the primary (e.g. finished vs solved). */
  behind?: Array<number | null | undefined>;
  behindColor?: string;
  /** Fixed y-axis extent, useful for honest 0–1 percentage plots. */
  domain?: readonly [number, number];
  /** Accessible label. */
  ariaLabel?: string;
}

/**
 * Normalise a series into SVG points fitting the viewBox. Returns null if too
 * few finite points to draw a line.
 */
function toPoints(
  data: Array<number | null | undefined>,
  width: number,
  height: number,
  strokeWidth: number,
  padY: boolean,
  domain?: readonly [number, number],
): { d: string; min: number; max: number } | null {
  const vals = data.filter((v): v is number => Number.isFinite(v));
  if (vals.length < 2) return null;
  const validDomain = domain && domain[1] > domain[0] ? domain : null;
  const min = validDomain ? validDomain[0] : Math.min(...vals);
  const max = validDomain ? validDomain[1] : Math.max(...vals);
  const range = max - min || 1;
  const innerH = height - (padY ? strokeWidth * 2 : 0);
  const top = padY ? strokeWidth : 0;
  // x is spread across the full width by INDEX over the full data length so
  // null gaps don't compress surviving points together.
  const stepX = width / (data.length - 1 || 1);
  let d = "";
  let started = false;
  data.forEach((v, i) => {
    if (v == null || !Number.isFinite(v)) return;
    const x = i * stepX;
    const y = top + innerH - ((v - min) / range) * innerH;
    d += `${started ? "L" : "M"}${x.toFixed(1)} ${y.toFixed(1)} `;
    started = true;
  });
  return { d: d.trim(), min, max };
}

export function Sparkline({
  data,
  width = 120,
  height = 32,
  color = "hsl(var(--primary))",
  fill = true,
  strokeWidth = 1.5,
  behind,
  behindColor = "hsl(var(--muted-foreground))",
  domain,
  ariaLabel,
}: SparklineProps) {
  const padY = true;
  const behindPts = behind ? toPoints(behind, width, height, strokeWidth, padY, domain) : null;
  const mainPts = toPoints(data, width, height, strokeWidth, padY, domain);

  if (!mainPts) {
    return (
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        aria-label={ariaLabel}
        role="img"
      >
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="hsl(var(--border))"
          strokeWidth={1}
          strokeDasharray="2 3"
        />
      </svg>
    );
  }

  // Build a closed area path for the fill.
  const stepX = width / (data.length - 1 || 1);
  const lastFiniteIdx = (() => {
    for (let i = data.length - 1; i >= 0; i--) if (Number.isFinite(data[i])) return i;
    return 0;
  })();
  const areaD = `${mainPts.d} L${(lastFiniteIdx * stepX).toFixed(1)} ${height} L0 ${height} Z`;

  return (
    <svg
      width={width}
      height={height}
      viewBox={`0 0 ${width} ${height}`}
      aria-label={ariaLabel}
      role="img"
      preserveAspectRatio="none"
    >
      {behindPts && (
        <path
          d={behindPts.d}
          fill="none"
          stroke={behindColor}
          strokeWidth={strokeWidth}
          strokeLinejoin="round"
          strokeLinecap="round"
          opacity={0.5}
        />
      )}
      {fill && <path d={areaD} fill={color} opacity={0.12} stroke="none" />}
      <path
        d={mainPts.d}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}

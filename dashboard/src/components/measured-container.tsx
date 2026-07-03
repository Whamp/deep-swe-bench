import { useState, useEffect, useRef, type ReactElement } from 'react'

/**
 * Measures container width with ResizeObserver and renders children with
 * explicit pixel dimensions. This avoids the Recharts ResponsiveContainer
 * "blank on initial render" bug where the internal ResizeObserver doesn't
 * fire on first paint in some browsers/environments.
 *
 * Usage:
 *   <MeasuredContainer height={300}>
 *     {(width, height) => <BarChart width={width} height={height} ...>}
 *   </MeasuredContainer>
 */
export function MeasuredContainer({
  height,
  children,
}: {
  height: number
  children: (width: number, height: number) => ReactElement
}) {
  const ref = useRef<HTMLDivElement>(null)
  const [width, setWidth] = useState(0)

  useEffect(() => {
    const el = ref.current
    if (!el) return
    const update = () => setWidth(el.clientWidth)
    update()
    const observer = new ResizeObserver(update)
    observer.observe(el)
    return () => observer.disconnect()
  }, [])

  return (
    <div ref={ref} style={{ width: '100%', height }}>
      {width > 0 && children(width, height)}
    </div>
  )
}

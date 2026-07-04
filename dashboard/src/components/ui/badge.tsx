import { type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { cn } from '@/lib/utils'
import type { RunState, CellState, CellOutcome } from '@/lib/types'

const badgeVariants = cva(
  'inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default: 'border-border text-muted-foreground',
        running: 'border-green-500/50 text-green-400',
        completed: 'border-green-500/50 text-green-400',
        paused: 'border-yellow-500/50 text-yellow-400',
        failed: 'border-red-500/50 text-red-400',
        stale: 'border-yellow-500/50 bg-yellow-500/10 text-yellow-400',
        ok: 'border-green-500/50 text-green-400',
        timeout: 'border-red-500/50 text-red-400',
        transient: 'border-orange-500/50 text-orange-400',
        empty: 'border-muted text-muted-foreground',
        skipped: 'border-muted text-muted-foreground',
      },
    },
    defaultVariants: { variant: 'default' },
  },
)

export interface BadgeProps
  extends HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {}

export function Badge({ className, variant, ...props }: BadgeProps) {
  return <span className={cn(badgeVariants({ variant }), className)} {...props} />
}

export function StateBadge({ state }: { state: RunState | CellState | string | undefined }) {
  if (!state) return null
  const variant = (['running', 'completed', 'paused', 'failed'] as const).includes(state as never)
    ? (state as 'running' | 'completed' | 'paused' | 'failed')
    : 'default'
  return <Badge variant={variant}>{state}</Badge>
}

export function OutcomeBadge({ outcome }: { outcome: CellOutcome | string | undefined }) {
  if (!outcome) return null
  const variant = (['ok', 'timeout', 'transient', 'empty', 'skipped', 'failed'] as const).includes(
    outcome as never,
  )
    ? (outcome as 'ok' | 'timeout' | 'transient' | 'empty' | 'skipped' | 'failed')
    : 'default'
  return <Badge variant={variant}>{outcome}</Badge>
}

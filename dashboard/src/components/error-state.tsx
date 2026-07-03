import { Link } from 'react-router-dom'
import { Card, CardContent } from '@/components/ui/card'

/**
 * Friendly error state shown when a run is not found or an API error occurs.
 * Replaces raw ApiError JSON with a clear message and recovery CTA.
 */
export function ErrorState({
  title = 'Run not found',
  message,
  runId,
}: {
  title?: string
  message?: string
  runId?: string
}) {
  return (
    <Card className="max-w-lg mx-auto mt-12">
      <CardContent className="space-y-3 p-6 text-center">
        <div className="text-3xl">🔍</div>
        <h2 className="text-lg font-bold">{title}</h2>
        {runId && (
          <p className="text-sm text-muted-foreground break-all">
            Run: <code className="rounded bg-muted px-1 py-0.5">{runId}</code>
          </p>
        )}
        {message && <p className="text-sm text-muted-foreground">{message}</p>}
        <Link
          to="/"
          className="inline-block rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
        >
          ← Back to Overview
        </Link>
      </CardContent>
    </Card>
  )
}

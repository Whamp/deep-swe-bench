import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderResult } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { vi } from 'vitest'

/** Installs one successful JSON response for dashboard API component tests. */
export function mockDashboardJson(responseBody: unknown): void {
  globalThis.fetch = vi.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: () => Promise.resolve(responseBody),
  })
}

/** Renders a dashboard route with isolated query and router providers. */
export function renderDashboardRoute(
  element: ReactNode,
  routePath: string,
  initialPath: string,
): RenderResult {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false, gcTime: 0 } },
  })
  return render(
    <QueryClientProvider client={client}>
      <MemoryRouter initialEntries={[initialPath]}>
        <Routes>
          <Route path={routePath} element={element} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

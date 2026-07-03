import '@testing-library/jest-dom/vitest'
import { vi } from 'vitest'

// Recharts ResponsiveContainer uses ResizeObserver which jsdom doesn't provide.
class MockResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
}
global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver

// jsdom returns 0 for clientWidth, which prevents MeasuredContainer from
// rendering children. Give elements a non-zero width so charts render in tests.
Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
  configurable: true,
  get() {
    return parseInt(this.style.width) || 800
  },
})

// jsdom doesn't implement fetch natively in all versions; ensure it exists.
if (!global.fetch) {
  global.fetch = vi.fn() as unknown as typeof fetch
}

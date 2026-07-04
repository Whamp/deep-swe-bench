import { NavLink, Outlet } from 'react-router-dom'
import { cn } from '@/lib/utils'

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex items-center gap-6 px-6 py-3">
          <h1 className="text-lg font-semibold">deep-swe-bench</h1>
          <nav className="flex gap-1">
            <NavItem to="/">Overview</NavItem>
            <NavItem to="/leaderboard">Leaderboard</NavItem>
            <NavItem to="/compare">Compare</NavItem>
          </nav>
        </div>
      </header>
      <main className="p-6">
        <Outlet />
      </main>
    </div>
  )
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn(
          'rounded-md px-3 py-1.5 text-sm font-medium transition-colors',
          isActive ? 'bg-accent text-foreground' : 'text-muted-foreground hover:text-foreground',
        )
      }
    >
      {children}
    </NavLink>
  )
}

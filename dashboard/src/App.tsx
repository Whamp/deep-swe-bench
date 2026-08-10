import { NavLink, Outlet } from "react-router-dom";
import { cn } from "@/lib/utils";

export default function App() {
  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-50 border-b border-border bg-background/95 backdrop-blur">
        <div className="flex items-center gap-2 px-3 py-3 sm:gap-6 sm:px-6">
          <h1 className="hidden whitespace-nowrap text-lg font-semibold sm:block">
            deep-swe-bench
          </h1>
          <nav className="flex flex-1 justify-center gap-1 sm:flex-none sm:justify-start">
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
  );
}

function NavItem({ to, children }: { to: string; children: React.ReactNode }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        cn(
          "rounded-md px-2 py-1.5 text-xs font-medium transition-colors sm:px-3 sm:text-sm",
          isActive ? "bg-accent text-foreground" : "text-muted-foreground hover:text-foreground",
        )
      }
    >
      {children}
    </NavLink>
  );
}

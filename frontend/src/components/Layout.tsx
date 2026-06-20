import { Outlet, Link, useLocation } from "react-router-dom";
import { Zap } from "lucide-react";

export function Layout() {
  const location = useLocation();

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100">
      <header className="border-b border-zinc-800 bg-zinc-900/50 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-violet-500 to-fuchsia-500 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-lg tracking-tight">
              ATELIX
              <span className="text-zinc-500 font-normal ml-1 text-sm">
                ViralClip
              </span>
            </span>
          </Link>

          <nav className="flex items-center gap-6 text-sm text-zinc-400">
            <Link
              to="/"
              className={`hover:text-white transition-colors ${location.pathname === "/" ? "text-white" : ""}`}
            >
              Dashboard
            </Link>
            <span className="text-xs px-2 py-0.5 rounded-full bg-violet-500/10 text-violet-400 border border-violet-500/20">
              v0.1.0
            </span>
          </nav>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <Outlet />
      </main>
    </div>
  );
}

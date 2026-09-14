import { Link, useLocation } from 'react-router-dom'
import { Scissors, History, Home, Sparkles } from 'lucide-react'

export default function Navbar() {
  const { pathname } = useLocation()

  const navLinks = [
    { to: '/',        label: 'Dashboard', icon: <Home className="w-4 h-4" /> },
    { to: '/history', label: 'History',   icon: <History className="w-4 h-4" /> },
  ]

  return (
    <header className="sticky top-0 z-50 border-b border-white/5 backdrop-blur-md"
            style={{ background: 'rgba(10, 10, 15, 0.85)' }}>
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-600 to-accent-500 
                          flex items-center justify-center shadow-lg shadow-brand-900/50
                          group-hover:shadow-brand-600/40 transition-shadow duration-300">
            <Scissors className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-white text-lg hidden sm:block">
            AI<span className="text-brand-400">Clipper</span>
          </span>
        </Link>

        {/* Nav links */}
        <nav className="flex items-center gap-1">
          {navLinks.map(({ to, label, icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200
                ${pathname === to
                  ? 'bg-brand-500/15 text-brand-400 border border-brand-500/30'
                  : 'text-white/40 hover:text-white/70 hover:bg-white/5'
                }`}
            >
              {icon}
              <span className="hidden sm:block">{label}</span>
            </Link>
          ))}
        </nav>

        {/* Right side badge */}
        <div className="flex items-center gap-1.5 text-xs text-white/30 hidden sm:flex">
          <Sparkles className="w-3.5 h-3.5 text-brand-500" />
          <span>TimmyAI</span>
        </div>
      </div>
    </header>
  )
}

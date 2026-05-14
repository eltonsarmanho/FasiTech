import { Link, useLocation } from 'react-router-dom'
import { GraduationCap, Menu, X } from 'lucide-react'
import { useState } from 'react'
import { cn } from '@/shared/lib/utils'

const navLinks = [
  { to: '/',             label: 'Portal' },
  { to: '/faq',          label: 'FAQ' },
  { to: '/documentos',   label: 'Documentos' },
  { to: '/calendarios',  label: 'Calendários' },
  { to: '/configuracao', label: 'Configuração' },
]

export function Header() {
  const { pathname } = useLocation()
  const [menuOpen, setMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 bg-white border-b border-border shadow-fasi-sm">
      <div className="container max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo + Nome */}
        <Link to="/" className="flex items-center gap-3 group shrink-0">
          <div className="w-8 h-8 rounded-lg bg-fasi-500 flex items-center justify-center
                          group-hover:bg-fasi-600 transition-colors">
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col leading-none">
            <span className="font-bold text-fasi-500 text-lg tracking-tight">FasiTech</span>
            <span className="text-xs text-muted-foreground hidden sm:block">Portal Acadêmico UFPA</span>
          </div>
        </Link>

        {/* Nav Desktop */}
        <nav className="hidden md:flex items-center gap-1">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                'px-3 py-1.5 rounded-md text-sm font-medium transition-colors',
                pathname === to
                  ? 'bg-fasi-500 text-white'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile menu toggle */}
        <button
          className="md:hidden p-2 rounded-md text-muted-foreground hover:bg-muted transition-colors"
          onClick={() => setMenuOpen(v => !v)}
          aria-label="Menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-border bg-white px-4 py-3 flex flex-col gap-1">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMenuOpen(false)}
              className={cn(
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                pathname === to
                  ? 'bg-fasi-500 text-white'
                  : 'text-muted-foreground hover:text-foreground hover:bg-muted',
              )}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  )
}

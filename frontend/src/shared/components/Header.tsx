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
    <header className="sticky top-0 z-50 bg-white shadow-navy-sm" style={{ borderBottom: '2px solid #1A3A6B' }}>
      <div className="container max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">

        {/* Logo + Identidade institucional */}
        <Link to="/" className="flex items-center gap-3 group shrink-0">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center
                        group-hover:opacity-90 transition-opacity"
            style={{ background: '#1A3A6B' }}
          >
            <GraduationCap className="w-5 h-5 text-white" />
          </div>
          <div className="flex flex-col leading-none gap-0.5">
            <span
              className="font-display font-bold text-lg tracking-tight"
              style={{ color: '#1A3A6B' }}
            >
              FasiTech
            </span>
            <span className="text-[10px] font-medium tracking-wide uppercase hidden sm:block"
                  style={{ color: '#64748B', letterSpacing: '0.1em' }}>
              FASI · UFPA
            </span>
          </div>
        </Link>

        {/* Nav Desktop */}
        <nav className="hidden md:flex items-center gap-0.5">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              className={cn(
                'px-3.5 py-1.5 rounded-md text-sm font-medium transition-all duration-150',
                pathname === to
                  ? 'text-white'
                  : 'text-[#475569] hover:text-[#0F172A] hover:bg-[#F4F6FA]',
              )}
              style={pathname === to ? { background: '#1A3A6B' } : {}}
            >
              {label}
            </Link>
          ))}
        </nav>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 rounded-md transition-colors"
          style={{ color: '#475569' }}
          onClick={() => setMenuOpen(v => !v)}
          aria-label="Menu"
        >
          {menuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {menuOpen && (
        <div className="md:hidden border-t border-[#E2E8F0] bg-white px-4 py-3 flex flex-col gap-1">
          {navLinks.map(({ to, label }) => (
            <Link
              key={to}
              to={to}
              onClick={() => setMenuOpen(false)}
              className={cn(
                'px-3 py-2 rounded-md text-sm font-medium transition-colors',
                pathname === to
                  ? 'text-white'
                  : 'text-[#475569] hover:text-[#0F172A] hover:bg-[#F4F6FA]',
              )}
              style={pathname === to ? { background: '#1A3A6B' } : {}}
            >
              {label}
            </Link>
          ))}
        </div>
      )}
    </header>
  )
}

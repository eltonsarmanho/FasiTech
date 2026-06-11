import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import type { ReactNode } from 'react'

interface PageShellProps {
  title: string
  subtitle?: string
  icon?: string
  showBack?: boolean
  children: ReactNode
}

export function PageShell({ title, subtitle, icon, showBack = true, children }: PageShellProps) {
  const navigate = useNavigate()

  return (
    <div className="animate-slide-up">
      {/* Cabeçalho navy */}
      <div className="fasi-header-gradient rounded-2xl px-8 py-8 mb-8 text-white">
        <div className="relative">
          {showBack && (
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-sm font-medium mb-5 transition-opacity hover:opacity-80"
              style={{ color: 'rgba(255,255,255,0.65)' }}
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar
            </button>
          )}

          {icon && (
            <div
              className="w-11 h-11 rounded-xl flex items-center justify-center mb-3 text-xl"
              style={{ background: 'rgba(255,255,255,0.12)' }}
            >
              <span role="img" aria-hidden>{icon}</span>
            </div>
          )}

          <h1 className="text-2xl md:text-3xl font-display font-bold text-white mb-1 leading-tight">
            {title}
          </h1>
          {subtitle && (
            <p className="text-sm md:text-base" style={{ color: 'rgba(255,255,255,0.72)' }}>
              {subtitle}
            </p>
          )}
        </div>
      </div>

      {children}
    </div>
  )
}

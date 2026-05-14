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
      {/* Hero azul FASI */}
      <div className="fasi-header-gradient rounded-2xl p-8 mb-8 text-white relative overflow-hidden">
        {/* Círculo decorativo */}
        <div className="absolute -top-12 -right-12 w-48 h-48 rounded-full bg-white/5 pointer-events-none" />
        <div className="absolute -bottom-8 -left-8 w-32 h-32 rounded-full bg-white/5 pointer-events-none" />

        <div className="relative">
          {showBack && (
            <button
              onClick={() => navigate(-1)}
              className="flex items-center gap-1.5 text-white/70 hover:text-white
                         text-sm font-medium mb-4 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" />
              Voltar
            </button>
          )}

          {icon && <div className="text-4xl mb-3">{icon}</div>}
          <h1 className="text-2xl md:text-3xl font-bold mb-1">{title}</h1>
          {subtitle && <p className="text-white/80 text-sm md:text-base">{subtitle}</p>}
        </div>
      </div>

      {/* Conteúdo */}
      {children}
    </div>
  )
}

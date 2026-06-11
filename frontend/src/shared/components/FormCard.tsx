import { useNavigate } from 'react-router-dom'
import { cn } from '@/shared/lib/utils'

interface FormCardProps {
  icon: string
  title: string
  description: string
  to: string
  external?: boolean
  variant?: 'primary' | 'warning'
}

export function FormCard({ icon, title, description, to, external = false, variant = 'primary' }: FormCardProps) {
  const navigate = useNavigate()

  const handleClick = () => {
    if (external) window.open(to, '_blank', 'noopener,noreferrer')
    else navigate(to)
  }

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={(e) => e.key === 'Enter' && handleClick()}
      className={cn('fasi-service-card group', variant === 'warning' && 'variant-warning')}
    >
      {/* Ícone */}
      <div className="text-2xl mb-3.5 group-hover:scale-110 transition-transform duration-200 leading-none">
        <span role="img" aria-hidden>{icon}</span>
      </div>

      {/* Título */}
      <h3
        className="font-display font-bold text-[0.9375rem] mb-1.5 leading-snug"
        style={{ color: '#0F172A' }}
      >
        {title}
      </h3>

      {/* Descrição */}
      <p className="text-sm leading-relaxed mb-4" style={{ color: '#64748B' }}>
        {description}
      </p>

      {/* CTA */}
      <div
        className="inline-flex items-center gap-1 text-xs font-semibold
                   group-hover:gap-2 transition-all duration-150"
        style={{ color: variant === 'primary' ? '#2563EB' : '#d97706' }}
      >
        Acessar <span aria-hidden>→</span>
      </div>
    </div>
  )
}

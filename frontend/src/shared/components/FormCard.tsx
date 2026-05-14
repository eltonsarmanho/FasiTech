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
      className={cn(
        'group rounded-xl p-6 text-white cursor-pointer select-none',
        'transition-all duration-200 ease-out focus:outline-none',
        'focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:ring-fasi-500',
        variant === 'primary'
          ? 'bg-fasi-500 hover:bg-fasi-600'
          : 'bg-amber-500 hover:bg-amber-600',
      )}
      style={{
        boxShadow: variant === 'primary'
          ? '0 4px 14px rgba(0,0,255,0.20)'
          : '0 4px 14px rgba(245,158,11,0.20)',
      }}
    >
      {/* Ícone */}
      <div className="text-3xl mb-3 group-hover:scale-110 transition-transform duration-200">
        {icon}
      </div>

      {/* Título */}
      <h3 className="font-bold text-base mb-2 leading-tight">{title}</h3>

      {/* Descrição */}
      <p className="text-sm text-white/80 leading-relaxed mb-4">{description}</p>

      {/* CTA */}
      <div className="inline-flex items-center gap-1.5 text-xs font-semibold
                      bg-white/15 hover:bg-white/25 rounded-full px-3 py-1.5
                      transition-colors duration-150">
        Acessar →
      </div>
    </div>
  )
}

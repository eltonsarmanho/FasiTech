import { Loader2 } from 'lucide-react'
import { cn } from '@/shared/lib/utils'
import type { ButtonHTMLAttributes } from 'react'

interface SubmitButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  loading?: boolean
  label?: string
  loadingLabel?: string
}

export function SubmitButton({
  loading = false,
  label = 'Enviar',
  loadingLabel = 'Enviando...',
  className,
  ...props
}: SubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={loading}
      className={cn('fasi-btn-primary w-full py-3 text-base', className)}
      {...props}
    >
      {loading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          {loadingLabel}
        </>
      ) : label}
    </button>
  )
}

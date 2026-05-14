import type { ReactNode } from 'react'
import { cn } from '@/shared/lib/utils'

interface FormSectionProps {
  title?: string
  children: ReactNode
  className?: string
}

export function FormSection({ title, children, className }: FormSectionProps) {
  return (
    <div className={cn('fasi-card p-6 mb-6', className)}>
      {title && (
        <h2 className="text-base font-semibold text-foreground mb-5 flex items-center gap-2">
          <span className="w-1 h-5 rounded-full bg-fasi-500 inline-block" />
          {title}
        </h2>
      )}
      {children}
    </div>
  )
}

interface FieldGroupProps {
  cols?: 1 | 2 | 3
  children: ReactNode
}

export function FieldGroup({ cols = 2, children }: FieldGroupProps) {
  return (
    <div
      className={cn('grid gap-4', {
        'grid-cols-1': cols === 1,
        'grid-cols-1 sm:grid-cols-2': cols === 2,
        'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3': cols === 3,
      })}
    >
      {children}
    </div>
  )
}

interface FieldProps {
  label: string
  required?: boolean
  error?: string
  hint?: string
  className?: string
  children: ReactNode
}

export function Field({ label, required, error, hint, className, children }: FieldProps) {
  return (
    <div className={cn('flex flex-col gap-1.5', className)}>
      <label className="text-sm font-medium text-foreground">
        {label}
        {required && <span className="text-red-500 ml-0.5">*</span>}
      </label>
      {children}
      {hint && !error && <p className="text-xs text-muted-foreground">{hint}</p>}
      {error && <p className="text-xs text-red-500">{error}</p>}
    </div>
  )
}

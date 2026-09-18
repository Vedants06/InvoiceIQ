import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface EmptyStateProps {
  icon?: ReactNode
  title: string
  description?: ReactNode
  action?: ReactNode
  className?: string
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'card flex flex-col items-center justify-center px-6 py-14 text-center',
        className,
      )}
    >
      {icon && (
        <div className="mb-4 flex h-12 w-12 items-center justify-center rounded border border-paper-300 bg-paper-100 text-stone-400">
          {icon}
        </div>
      )}
      <p className="font-serif text-[19px] font-semibold text-stone-900">{title}</p>
      {description && (
        <p className="mt-2 max-w-sm text-[13.5px] leading-relaxed text-stone-500">{description}</p>
      )}
      {action && <div className="mt-6 flex flex-wrap justify-center gap-2">{action}</div>}
    </div>
  )
}

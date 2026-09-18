import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps {
  title: string
  description?: ReactNode
  action?: ReactNode
  /** Small label above the title, e.g. a breadcrumb or count. */
  eyebrow?: ReactNode
  className?: string
}

export default function PageHeader({
  title,
  description,
  action,
  eyebrow,
  className,
}: PageHeaderProps) {
  return (
    <div
      className={cn(
        'mb-7 flex flex-col gap-4 border-b border-paper-300 pb-5 sm:flex-row sm:items-end sm:justify-between',
        className,
      )}
    >
      <div className="min-w-0">
        {eyebrow && (
          <div className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
            {eyebrow}
          </div>
        )}
        <h1 className="font-serif text-[30px] font-semibold leading-tight tracking-[-0.01em] text-stone-900">
          {title}
        </h1>
        {description && (
          <p className="mt-2 max-w-2xl text-[13.5px] leading-relaxed text-stone-600">
            {description}
          </p>
        )}
      </div>
      {action && <div className="flex shrink-0 flex-wrap items-center gap-2">{action}</div>}
    </div>
  )
}

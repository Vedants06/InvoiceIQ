import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'

type Tone = 'neutral' | 'accent' | 'success' | 'warning' | 'danger'

const TONE_STYLES: Record<Tone, { value: string; rule: string }> = {
  neutral: { value: 'text-stone-900', rule: 'border-paper-300' },
  accent: { value: 'text-stone-900', rule: 'border-accent-300' },
  success: { value: 'text-[#28593c]', rule: 'border-[#cfe3d7]' },
  warning: { value: 'text-[#6d4d10]', rule: 'border-[#f0dcaa]' },
  danger: { value: 'text-[#96231b]', rule: 'border-[#f0c4c1]' },
}

interface StatCardProps {
  label: string
  value: ReactNode
  hint?: ReactNode
  tone?: Tone
  loading?: boolean
  className?: string
}

export default function StatCard({
  label,
  value,
  hint,
  tone = 'neutral',
  loading,
  className,
}: StatCardProps) {
  const s = TONE_STYLES[tone]

  if (loading) {
    return (
      <div className="card p-5">
        <div className="skeleton h-3 w-20" />
        <div className="skeleton mt-3 h-7 w-14" />
        <div className="skeleton mt-3 h-3 w-24" />
      </div>
    )
  }

  return (
    <div
      className={cn(
        'card card-hover border-l-2 p-5',
        s.rule,
        className,
      )}
    >
      <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
        {label}
      </p>
      <p className={cn('tabular mt-3 font-serif text-[30px] font-semibold leading-none', s.value)}>
        {value}
      </p>
      {hint && <p className="mt-2.5 text-[11.5px] text-stone-400">{hint}</p>}
    </div>
  )
}

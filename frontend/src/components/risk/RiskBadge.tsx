import { cn } from '../../lib/utils'
import type { RiskLevel } from '../../types/analysis'
import { riskStyle } from './riskStyle'

export default function RiskBadge({
  level,
  score,
  size = 'md',
  showScore = true,
}: {
  level: RiskLevel | null | undefined
  score?: number | null
  size?: 'sm' | 'md' | 'lg'
  showScore?: boolean
}) {
  const s = riskStyle(level)

  if (!level) {
    return (
      <span className="inline-flex items-center rounded border border-paper-300 bg-paper-100 px-2.5 py-1 text-xs font-medium text-stone-400">
        Not scored
      </span>
    )
  }

  return (
    <span
      className={cn(
        'chip tabular',
        s.pill,
        size === 'sm' ? 'px-2 py-0.5 text-2xs' : size === 'lg' ? 'px-3 py-1 text-sm' : 'text-xs',
      )}
      title={`Risk score ${score ?? '—'}/100 — ${s.label}`}
    >
      <span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />
      {showScore && (
        <span>
          {score !== undefined && score !== null ? `${score} ` : ''}
          {s.label}
        </span>
      )}
      {!showScore && s.label}
    </span>
  )
}

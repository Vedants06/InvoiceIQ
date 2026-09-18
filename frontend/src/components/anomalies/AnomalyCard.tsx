import { AlertTriangle, TrendingDown } from 'lucide-react'
import type { Anomaly } from '../../types/analysis'
import { cn } from '../../lib/utils'
import EvidenceFields from './EvidenceFields'

const SEVERITY = {
  high: {
    card: 'border-[#f0c4c1] bg-[#fbeceb]/60',
    tile: 'bg-[#f7dbd9] text-[#96231b]',
    chip: 'border-[#f0c4c1] bg-paper-50 text-[#7f1d16]',
  },
  medium: {
    card: 'border-[#f0dcaa] bg-[#fdf7ea]/60',
    tile: 'bg-[#f9eed5] text-[#8a6212]',
    chip: 'border-[#f0dcaa] bg-paper-50 text-[#6d4d10]',
  },
  low: {
    card: 'border-paper-300 bg-paper-100/60',
    tile: 'bg-paper-200 text-stone-600',
    chip: 'border-paper-300 bg-paper-50 text-stone-700',
  },
} as const

export default function AnomalyCard({ anomaly }: { anomaly: Anomaly }) {
  const currency = (anomaly.evidence.currency as string) || undefined
  const s = SEVERITY[anomaly.severity] ?? SEVERITY.medium

  return (
    <article className={cn('rounded-md border p-4 shadow-xs', s.card)}>
      <div className="flex items-start gap-3">
        <span
          className={cn(
            'mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded',
            s.tile,
          )}
        >
          <AlertTriangle className="h-4 w-4" strokeWidth={1.75} />
        </span>

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <h4 className="text-sm font-bold text-stone-900">{anomaly.title}</h4>
            <span className={cn('chip px-2 py-0.5 text-2xs uppercase', s.chip)}>
              {anomaly.severity}
            </span>
          </div>
          <p className="mt-1 text-sm leading-relaxed text-stone-600">{anomaly.description}</p>
        </div>

        <span className="flex shrink-0 flex-col items-end">
          <span className="inline-flex items-center gap-1 rounded bg-stone-900 px-2 py-1 text-xs font-bold text-paper-50">
            <TrendingDown className="h-3 w-3" strokeWidth={2} />+{anomaly.points}
          </span>
          <span className="mt-1 text-2xs font-medium text-stone-400">points</span>
        </span>
      </div>

      <EvidenceFields evidence={anomaly.evidence} currency={currency} />
    </article>
  )
}

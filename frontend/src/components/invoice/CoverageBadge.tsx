import { CheckCircle2, AlertCircle } from 'lucide-react'
import { cn } from '../../lib/utils'

export default function CoverageBadge({ coverage }: { coverage: number | null | undefined }) {
  if (coverage == null) return null
  const percent = Math.round(coverage * 100)
  const complete = percent >= 90

  return (
    <div
      className={cn(
        'chip tabular',
        complete
          ? 'border-[#cfe3d7] bg-[#f1f7f3] text-[#28593c]'
          : 'border-[#f0dcaa] bg-[#fdf7ea] text-[#6d4d10]',
      )}
      title="Share of expected invoice/contract fields successfully extracted (field-presence measure, computed by the backend)"
    >
      {complete ? (
        <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={1.75} />
      ) : (
        <AlertCircle className="h-3.5 w-3.5" strokeWidth={1.75} />
      )}
      Extraction coverage {percent}%
    </div>
  )
}

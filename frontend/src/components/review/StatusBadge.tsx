import { Clock3, CheckCircle2, XCircle, Loader2, AlertTriangle } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { BusinessStatus, ProcessingStatus } from '../../types/analysis'

const STYLES: Record<
  BusinessStatus,
  { classes: string; label: string; Icon: typeof Clock3 }
> = {
  PENDING_REVIEW: {
    classes: 'border-[#f0dcaa] bg-[#fdf7ea] text-[#6d4d10]',
    label: 'Pending review',
    Icon: Clock3,
  },
  APPROVED: {
    classes: 'border-[#cfe3d7] bg-[#f1f7f3] text-[#28593c]',
    label: 'Approved',
    Icon: CheckCircle2,
  },
  REJECTED: {
    classes: 'border-[#f0c4c1] bg-[#fbeceb] text-[#7f1d16]',
    label: 'Rejected',
    Icon: XCircle,
  },
}

export default function StatusBadge({
  status,
  size = 'md',
}: {
  status: BusinessStatus
  size?: 'sm' | 'md'
}) {
  const s = STYLES[status]
  return (
    <span
      className={cn(
        'chip',
        s.classes,
        size === 'sm' ? 'px-2 py-0.5 text-2xs' : 'px-2.5 py-1 text-xs',
      )}
    >
      <s.Icon className={size === 'sm' ? 'h-3 w-3' : 'h-3.5 w-3.5'} strokeWidth={1.75} />
      {s.label}
    </span>
  )
}

const PROCESSING_STYLES: Record<ProcessingStatus, { classes: string; label: string }> = {
  UPLOADED: { classes: 'border-paper-300 bg-paper-100 text-stone-600', label: 'Uploaded' },
  PROCESSING: { classes: 'border-accent-200 bg-accent-50 text-accent-800', label: 'Processing' },
  COMPLETED: { classes: 'border-paper-300 bg-paper-100 text-stone-600', label: 'Analyzed' },
  FAILED: { classes: 'border-[#f0c4c1] bg-[#fbeceb] text-[#7f1d16]', label: 'Analysis failed' },
}

export function ProcessingBadge({ status }: { status: ProcessingStatus }) {
  const s = PROCESSING_STYLES[status]
  return (
    <span className={cn('chip px-2 py-0.5 text-2xs', s.classes)}>
      {status === 'PROCESSING' ? (
        <Loader2 className="h-3 w-3 animate-spin" strokeWidth={1.75} />
      ) : status === 'FAILED' ? (
        <AlertTriangle className="h-3 w-3" strokeWidth={1.75} />
      ) : null}
      {s.label}
    </span>
  )
}

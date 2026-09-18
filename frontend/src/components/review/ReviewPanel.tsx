import { useState } from 'react'
import { CheckCircle2, Info, Loader2, ShieldQuestion, XCircle } from 'lucide-react'
import type { InvoiceDetail, ReviewDecision } from '../../types/analysis'
import { formatCurrency } from '../../lib/utils'

interface Props {
  invoice: InvoiceDetail
  onReview: (decision: ReviewDecision, reason?: string) => void
  isReviewing: boolean
  error: unknown
}

export default function ReviewPanel({ invoice, onReview, isReviewing, error }: Props) {
  const [mode, setMode] = useState<'none' | 'reject' | 'confirm-approve'>('none')
  const [reason, setReason] = useState('')

  // Decision already recorded
  if (invoice.review) {
    const approved = invoice.review.decision === 'APPROVED'
    return (
      <div
        className={`panel ${approved ? 'border-[#cfe3d7]' : 'border-[#f0c4c1]'}`}
        aria-live="polite"
      >
        <header
          className={`panel-header ${
            approved ? 'bg-[#f1f7f3]/60' : 'bg-[#fbeceb]/60'
          } border-inherit`}
        >
          <h2 className="panel-title">
            <span
              className={`flex h-7 w-7 items-center justify-center rounded ${
                approved ? 'bg-[#e3efe7] text-[#2f6b47]' : 'bg-[#f7dbd9] text-[#96231b]'
              }`}
            >
              {approved ? (
                <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={1.75} />
              ) : (
                <XCircle className="h-3.5 w-3.5" strokeWidth={1.75} />
              )}
            </span>
            Review decision
          </h2>
          <span
            className={`chip px-2 py-0.5 text-2xs ${
              approved
                ? 'border-[#cfe3d7] bg-paper-50 text-[#28593c]'
                : 'border-[#f0c4c1] bg-paper-50 text-[#7f1d16]'
            }`}
          >
            {approved ? 'Approved' : 'Rejected'}
          </span>
        </header>

        <div className="p-5">
          <p
            className={`font-serif text-[17px] font-semibold ${
              approved ? 'text-[#28593c]' : 'text-[#7f1d16]'
            }`}
          >
            {approved ? 'This invoice was approved' : 'This invoice was rejected'}
          </p>
          {invoice.review.reason && (
            <p className="mt-3 rounded bg-paper-100 p-3.5 text-sm leading-relaxed text-stone-700">
              {invoice.review.reason}
            </p>
          )}
          <p className="mt-3 text-xs text-stone-400">
            Reviewed{' '}
            {new Date(invoice.review.reviewed_at).toLocaleString(undefined, {
              dateStyle: 'medium',
              timeStyle: 'short',
            })}
          </p>
        </div>
      </div>
    )
  }

  if (invoice.processing_status !== 'COMPLETED') return null

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-accent-100 text-accent-700">
            <ShieldQuestion className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
          Human review
        </h2>
      </header>

      <div className="p-5">
        <p className="text-sm leading-relaxed text-stone-600">
          InvoiceIQ surfaces risk indicators — the decision stays with you. No payment is executed
          from this screen.
        </p>

        {mode === 'none' && (
          <div className="mt-5 flex flex-col gap-3 sm:flex-row">
            <button
              className="btn-danger flex-1"
              onClick={() => setMode('reject')}
              disabled={isReviewing}
            >
              <XCircle className="h-4 w-4" strokeWidth={1.75} />
              Reject invoice
            </button>
            <button
              className="btn-success flex-1"
              onClick={() => setMode('confirm-approve')}
              disabled={isReviewing}
            >
              <CheckCircle2 className="h-4 w-4" strokeWidth={1.75} />
              Approve invoice
            </button>
          </div>
        )}

        {mode === 'confirm-approve' && (
          <div className="mt-5 animate-scale-in rounded border border-[#cfe3d7] bg-[#f1f7f3]/60 p-4">
            <p className="text-sm font-semibold text-[#1f4a31]">
              Approve {formatCurrency(invoice.total, invoice.currency ?? undefined)}
              {invoice.vendor_name ? ` to ${invoice.vendor_name}` : ''}?
            </p>
            <p className="mt-1 text-xs text-[#28593c]/80">
              This records your decision on invoice{' '}
              <span className="font-semibold">{invoice.invoice_number ?? '—'}</span>.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="btn-success btn-sm"
                disabled={isReviewing}
                onClick={() => onReview('APPROVED')}
              >
                {isReviewing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <CheckCircle2 className="h-3.5 w-3.5" strokeWidth={1.75} />
                )}
                Confirm approval
              </button>
              <button
                className="btn-ghost btn-sm"
                onClick={() => setMode('none')}
                disabled={isReviewing}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {mode === 'reject' && (
          <div className="mt-5 animate-scale-in rounded border border-[#f0c4c1] bg-[#fbeceb]/50 p-4">
            <label
              htmlFor="rejection-reason"
              className="mb-1.5 block text-sm font-semibold text-stone-800"
            >
              Rejection reason <span className="text-[#96231b]">*</span>
            </label>
            <textarea
              id="rejection-reason"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              autoFocus
              className="input"
              placeholder="e.g. Billed rate exceeds the contracted hourly rate."
            />
            <p className="mt-2 flex items-start gap-1.5 text-2xs text-stone-500">
              <Info className="mt-0.5 h-3 w-3 shrink-0" />
              A reason is required and is stored with the decision.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                className="btn-danger-solid btn-sm"
                disabled={isReviewing || reason.trim().length === 0}
                onClick={() => onReview('REJECTED', reason.trim())}
              >
                {isReviewing ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <XCircle className="h-3.5 w-3.5" strokeWidth={1.75} />
                )}
                Confirm rejection
              </button>
              <button
                className="btn-ghost btn-sm"
                onClick={() => setMode('none')}
                disabled={isReviewing}
              >
                Cancel
              </button>
            </div>
          </div>
        )}

        {error instanceof Error && (
          <p className="mt-4 rounded bg-[#fbeceb] px-3 py-2 text-sm text-[#7f1d16]">{error.message}</p>
        )}
      </div>
    </div>
  )
}

import type { ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowUpRight, ChevronRight, FileSpreadsheet, Receipt } from 'lucide-react'
import type { InvoiceSummary } from '../../types/analysis'
import { cn, formatCurrency, formatDate } from '../../lib/utils'
import RiskBadge from '../risk/RiskBadge'
import StatusBadge, { ProcessingBadge } from '../review/StatusBadge'

function vendorInitials(name?: string | null) {
  if (!name) return '—'
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase())
    .join('')
}

// Vendors get a quiet monogram tile rather than a coloured avatar.
const VENDOR_TILE = 'bg-paper-200 text-stone-600'

export default function InvoiceTable({
  invoices,
  compact = false,
}: {
  invoices: InvoiceSummary[]
  compact?: boolean
}) {
  const navigate = useNavigate()

  if (invoices.length === 0) return null

  return (
    <div className="panel">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-paper-200/50">
            <tr className="border-b border-paper-300">
              <th className="table-head px-5 py-3 text-left">Invoice</th>
              <th className="table-head px-5 py-3 text-left">Vendor</th>
              <th className="table-head px-5 py-3 text-right">Amount</th>
              <th className="table-head px-5 py-3 text-left">Risk</th>
              <th className="table-head px-5 py-3 text-left">Status</th>
              <th className="table-head hidden px-5 py-3 text-left lg:table-cell">Date</th>
              <th className="table-head px-5 py-3 text-right">
                <span className="sr-only">Open</span>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-paper-100">
            {invoices.map((inv) => (
              <tr
                key={inv.id}
                onClick={() => navigate(`/invoices/${inv.id}`)}
                tabIndex={0}
                role="link"
                aria-label={`Open invoice ${inv.invoice_number ?? inv.id}`}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault()
                    navigate(`/invoices/${inv.id}`)
                  }
                }}
                className="group cursor-pointer transition-colors hover:bg-paper-100/80 focus:bg-paper-100 focus:outline-none"
              >
                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-stone-900 transition group-hover:text-accent-800">
                      {inv.invoice_number ?? '—'}
                    </span>
                    {inv.has_timesheet && (
                      <span
                        title="Timesheet provided"
                        className="text-stone-300"
                        aria-label="Timesheet provided"
                      >
                        <FileSpreadsheet className="h-3.5 w-3.5" />
                      </span>
                    )}
                  </div>
                  {inv.processing_status !== 'COMPLETED' && (
                    <div className="mt-1">
                      <ProcessingBadge status={inv.processing_status} />
                    </div>
                  )}
                </td>

                <td className="px-5 py-3.5">
                  <div className="flex items-center gap-2.5">
                    <span
                      className={cn(
                        'flex h-7 w-7 shrink-0 items-center justify-center rounded text-[10px] font-semibold uppercase tracking-wide',
                        VENDOR_TILE,
                      )}
                      aria-hidden
                    >
                      {vendorInitials(inv.vendor_name)}
                    </span>
                    <span className="truncate text-stone-700">
                      {inv.vendor_name ?? '—'}
                    </span>
                  </div>
                </td>

                <td className="tabular px-5 py-3.5 text-right font-semibold text-stone-900">
                  {formatCurrency(inv.total, inv.currency ?? undefined)}
                </td>

                <td className="px-5 py-3.5">
                  <RiskBadge level={inv.risk_level} score={inv.risk_score} size="sm" />
                </td>

                <td className="px-5 py-3.5">
                  <StatusBadge status={inv.status} size="sm" />
                </td>

                <td className="hidden whitespace-nowrap px-5 py-3.5 text-stone-500 lg:table-cell">
                  {formatDate(inv.created_at)}
                </td>

                <td className="px-5 py-3.5 text-right">
                  <Link
                    to={`/invoices/${inv.id}`}
                    onClick={(e) => e.stopPropagation()}
                    className={cn(
                      'inline-flex items-center gap-1 rounded px-2 py-1 text-xs font-semibold text-stone-500',
                      'transition hover:bg-paper-50 hover:text-accent-800 hover:shadow-xs',
                      compact && 'lg:opacity-0 lg:group-hover:opacity-100',
                    )}
                  >
                    <span className="hidden sm:inline">
                      {inv.processing_status === 'COMPLETED' ? 'Review' : 'View'}
                    </span>
                    <ChevronRight className="h-4 w-4 sm:hidden" />
                    <ArrowUpRight className="hidden h-3.5 w-3.5 sm:block" />
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export function InvoiceTableEmpty({
  title,
  description,
  action,
}: {
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="panel flex flex-col items-center justify-center px-6 py-16 text-center">
      <span className="mb-4 flex h-12 w-12 items-center justify-center rounded border border-paper-300 bg-paper-100 text-stone-400">
        <Receipt className="h-5 w-5" strokeWidth={1.75} />
      </span>
      <p className="font-serif text-[19px] font-semibold text-stone-900">{title}</p>
      <p className="mt-2 max-w-sm text-[13.5px] leading-relaxed text-stone-500">{description}</p>
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}

import type { ContractFacts, InvoiceDetail, TimesheetFacts } from '../../types/analysis'
import { formatCurrency, formatDate } from '../../lib/utils'

function Row({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-paper-200 py-2 text-sm last:border-0">
      <span className="shrink-0 text-stone-500">{label}</span>
      <span
        className={
          strong
            ? 'tabular text-right text-base font-bold text-stone-900'
            : 'tabular text-right font-medium text-stone-900'
        }
      >
        {value}
      </span>
    </div>
  )
}

export function InvoicePreview({ invoice }: { invoice: InvoiceDetail }) {
  const c = invoice.currency ?? undefined
  const hours = (invoice.line_items ?? [])
    .filter((li) => li.quantity != null)
    .reduce((s, li) => s + (li.quantity ?? 0), 0)

  return (
    <div className="p-5">
      <div className="mb-3 flex items-start justify-between gap-3 border-b border-paper-300 pb-3">
        <div>
          <h4 className="text-sm font-bold text-stone-900">{invoice.vendor_name ?? 'Vendor'}</h4>
          <p className="mt-0.5 text-xs text-stone-400">Invoice to client</p>
        </div>
        <span className="tabular shrink-0 rounded bg-paper-200 px-2 py-1 text-2xs font-semibold text-stone-600">
          {invoice.invoice_number ?? '—'}
        </span>
      </div>

      <Row label="Invoice date" value={formatDate(invoice.invoice_date)} />
      <Row label="Due date" value={formatDate(invoice.due_date)} />
      <Row label="Subtotal" value={formatCurrency(invoice.subtotal, c)} />
      <Row label="Tax" value={formatCurrency(invoice.tax, c)} />
      <Row label="Billed hours" value={hours ? `${hours} hrs` : '—'} />
      <div className="mt-1 rounded bg-paper-100 px-3 py-2">
        <Row label="Total" value={formatCurrency(invoice.total, c)} strong />
      </div>

      <div className="mt-4">
        <p className="eyebrow mb-1.5">Line items</p>
        {(invoice.line_items ?? []).length === 0 ? (
          <p className="text-sm text-stone-400">No line items extracted.</p>
        ) : (
          <ul className="space-y-1.5">
            {invoice.line_items!.map((li, i) => (
              <li
                key={i}
                className="flex items-baseline justify-between gap-3 rounded border border-paper-200 px-3 py-2 text-sm"
              >
                <span className="min-w-0 flex-1 truncate text-stone-800">
                  {li.description ?? 'Service'}
                </span>
                <span className="tabular shrink-0 text-xs text-stone-500">
                  {li.quantity ?? 0} × {formatCurrency(li.unit_price, c)}
                </span>
                <span className="tabular w-20 shrink-0 text-right font-semibold text-stone-900">
                  {formatCurrency(li.amount, c)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

export function ContractPreview({
  contract,
  currency,
}: {
  contract: ContractFacts
  currency?: string
}) {
  const c = contract.currency ?? currency
  return (
    <div className="p-5">
      <div className="mb-3 border-b border-paper-300 pb-3">
        <h4 className="text-sm font-bold text-stone-900">
          {contract.vendor_name ?? 'Vendor'}
          <span className="ml-1.5 font-medium text-stone-400">· Contract</span>
        </h4>
      </div>
      <Row
        label="Period"
        value={`${formatDate(contract.start_date)} – ${formatDate(contract.end_date)}`}
      />
      <Row label="Hourly rate" value={`${formatCurrency(contract.hourly_rate, c)}/hr`} />
      <Row
        label="Maximum hours"
        value={contract.max_hours != null ? `${contract.max_hours} hrs` : '—'}
      />
      <Row label="Maximum amount" value={formatCurrency(contract.max_amount, c)} />
      <Row label="Currency" value={contract.currency ?? '—'} />
      <Row label="Payment terms" value={contract.payment_terms ?? '—'} />
    </div>
  )
}

export function TimesheetPreview({ timesheet }: { timesheet: TimesheetFacts }) {
  return (
    <div className="p-5">
      <div className="mb-3 border-b border-paper-300 pb-3">
        <h4 className="text-sm font-bold text-stone-900">Timesheet</h4>
        <p className="mt-0.5 truncate text-xs text-stone-400">{timesheet.file_name}</p>
      </div>
      <div className="rounded bg-paper-100 px-3 py-2">
        <Row label="Total recorded hours" value={`${timesheet.total_hours} hrs`} strong />
      </div>
      <p className="mt-3 text-2xs leading-relaxed text-stone-400">
        Hours are summed deterministically from the submitted CSV/XLSX — no model involved.
      </p>
    </div>
  )
}

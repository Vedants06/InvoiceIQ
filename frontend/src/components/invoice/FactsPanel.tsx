import type { ReactNode } from 'react'
import { Building2, FileSpreadsheet, Receipt } from 'lucide-react'
import type { InvoiceDetail } from '../../types/analysis'
import { cn, formatCurrency, formatDate } from '../../lib/utils'

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <dt className="text-xs text-stone-500">{label}</dt>
      <dd className="tabular text-sm font-semibold text-stone-900">{value}</dd>
    </div>
  )
}

function billedHours(invoice: InvoiceDetail): number | null {
  const total = (invoice.line_items ?? [])
    .filter((li) => li.quantity != null)
    .reduce((sum, li) => sum + (li.quantity ?? 0), 0)
  return total > 0 ? total : null
}

function billedRate(invoice: InvoiceDetail): number | null {
  const rates = (invoice.line_items ?? [])
    .map((li) => li.unit_price)
    .filter((r): r is number => r != null)
  return rates.length > 0 ? Math.max(...rates) : null
}

function SourceHeader({
  icon,
  title,
  note,
  tone = 'default',
}: {
  icon: ReactNode
  title: string
  note?: string
  tone?: 'default' | 'warning'
}) {
  return (
    <div className="mb-3 flex items-center gap-2">
      <span
        className={cn(
          'flex h-6 w-6 items-center justify-center rounded',
          tone === 'warning' ? 'bg-[#f9eed5] text-[#8a6212]' : 'bg-paper-200 text-stone-500',
        )}
      >
        {icon}
      </span>
      <h3 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">{title}</h3>
      {note && (
        <span className="ml-auto text-[10px] font-semibold uppercase tracking-[0.14em] text-[#8a6212]">{note}</span>
      )}
    </div>
  )
}

function UtilisationBar({
  label,
  used,
  max,
  format,
}: {
  label: string
  used: number
  max: number
  format: (n: number) => string
}) {
  if (!(max > 0)) return null
  const pct = (used / max) * 100
  const over = pct > 100
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between text-xs">
        <span className="text-stone-500">{label}</span>
        <span className={cn('tabular font-semibold', over ? 'text-[#96231b]' : 'text-stone-700')}>
          {format(used)} of {format(max)} · {Math.round(pct)}%
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-paper-200">
        <div
          className={cn(
            'h-full rounded-full transition-[width] duration-700 ease-spring',
            over ? 'bg-[#ba443c]' : pct > 85 ? 'bg-[#b9862a]' : 'bg-accent-500',
          )}
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
    </div>
  )
}

export default function FactsPanel({ invoice }: { invoice: InvoiceDetail }) {
  const c = invoice.currency ?? undefined
  const contract = invoice.contract
  const timesheet = invoice.timesheet
  const hours = billedHours(invoice)
  const rate = billedRate(invoice)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">Verified facts</h2>
        <p className="text-2xs text-stone-400">Extracted by the backend pipeline</p>
      </header>

      <div className="grid grid-cols-1 divide-y divide-paper-100 md:grid-cols-3 md:divide-x md:divide-y-0">
        <div className="p-5">
          <SourceHeader icon={<Receipt className="h-3.5 w-3.5" />} title="Invoice" />
          <dl className="space-y-2.5">
            <Fact label="Total" value={formatCurrency(invoice.total, c)} />
            <Fact label="Billed hours" value={hours != null ? `${hours} hrs` : '—'} />
            <Fact
              label="Billed rate"
              value={rate != null ? `${formatCurrency(rate, c)}/hr` : '—'}
            />
            <Fact label="Invoice date" value={formatDate(invoice.invoice_date)} />
          </dl>
        </div>

        <div className="p-5">
          <SourceHeader icon={<Building2 className="h-3.5 w-3.5" />} title="Contract" />
          {contract ? (
            <dl className="space-y-2.5">
              <Fact
                label="Maximum amount"
                value={formatCurrency(contract.max_amount, contract.currency ?? c)}
              />
              <Fact
                label="Maximum hours"
                value={contract.max_hours != null ? `${contract.max_hours} hrs` : '—'}
              />
              <Fact
                label="Hourly rate"
                value={
                  contract.hourly_rate != null
                    ? `${formatCurrency(contract.hourly_rate, contract.currency ?? c)}/hr`
                    : '—'
                }
              />
              <Fact
                label="Period"
                value={`${formatDate(contract.start_date)} – ${formatDate(contract.end_date)}`}
              />
            </dl>
          ) : (
            <p className="text-sm text-stone-400">Contract terms not extracted.</p>
          )}
        </div>

        <div className="p-5">
          <SourceHeader
            icon={<FileSpreadsheet className="h-3.5 w-3.5" />}
            title="Timesheet"
            note={timesheet ? undefined : 'Not provided'}
            tone={timesheet ? 'default' : 'warning'}
          />
          {timesheet ? (
            <dl className="space-y-2.5">
              <Fact label="Recorded hours" value={`${timesheet.total_hours} hrs`} />
              <Fact label="Source file" value={timesheet.file_name} />
            </dl>
          ) : (
            <p className="text-sm leading-relaxed text-stone-500">
              Timesheet reconciliation was not performed. This is not treated as passing evidence —
              the remaining checks still ran.
            </p>
          )}
        </div>
      </div>

      {(hours != null && contract?.max_hours != null) ||
      (invoice.total != null && contract?.max_amount != null) ? (
        <div className="space-y-3 border-t border-paper-200 bg-paper-100/60 p-5">
          {hours != null && contract?.max_hours != null && (
            <UtilisationBar
              label="Hours billed against contract maximum"
              used={hours}
              max={contract.max_hours}
              format={(n) => `${n} hrs`}
            />
          )}
          {invoice.total != null && contract?.max_amount != null && (
            <UtilisationBar
              label="Amount billed against contract maximum"
              used={invoice.total}
              max={contract.max_amount}
              format={(n) => formatCurrency(n, contract.currency ?? c)}
            />
          )}
        </div>
      ) : null}
    </div>
  )
}

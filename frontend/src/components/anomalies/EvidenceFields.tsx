import { formatCurrency } from '../../lib/utils'

const LABELS: Record<string, string> = {
  invoice_rate: 'Invoice rate',
  contract_rate: 'Contract rate',
  difference_percent: 'Difference',
  invoice_hours: 'Billed hours',
  contract_max_hours: 'Contract maximum',
  excess_hours: 'Excess hours',
  invoice_total: 'Invoice total',
  contract_max_amount: 'Contract maximum',
  excess_amount: 'Excess amount',
  timesheet_hours: 'Timesheet hours',
  unsupported_hours: 'Unsupported hours',
  invoice_vendor: 'Invoice vendor',
  contract_vendor: 'Contract vendor',
  invoice_currency: 'Invoice currency',
  contract_currency: 'Contract currency',
  invoice_date: 'Invoice date',
  contract_start: 'Contract start',
  contract_end: 'Contract end',
  subtotal: 'Subtotal',
  tax: 'Tax',
  total: 'Total',
  currency: 'Currency',
  current_amount: 'Current invoice',
  average_amount: 'Historical average',
  deviation_percent: 'Deviation',
  prior_invoice_count: 'Prior invoices',
}

const MONEY_KEYS = new Set([
  'invoice_rate',
  'contract_rate',
  'invoice_total',
  'contract_max_amount',
  'excess_amount',
  'subtotal',
  'tax',
  'total',
  'current_amount',
  'average_amount',
])

const HOUR_KEYS = new Set([
  'invoice_hours',
  'contract_max_hours',
  'excess_hours',
  'timesheet_hours',
  'unsupported_hours',
])

function formatValue(key: string, value: unknown, currency?: string): string {
  if (value === null || value === undefined) return '—'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  if (MONEY_KEYS.has(key)) {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : formatCurrency(n, currency)
  }
  if (HOUR_KEYS.has(key)) {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : `${n} hrs`
  }
  if (key === 'difference_percent' || key === 'deviation_percent') {
    const n = Number(value)
    return Number.isNaN(n) ? String(value) : `${n > 0 ? '+' : ''}${n}%`
  }
  if (typeof value === 'number') return String(value)
  if (Array.isArray(value)) return value.join(', ')
  return String(value)
}

export default function EvidenceFields({
  evidence,
  currency,
}: {
  evidence: Record<string, unknown>
  currency?: string | null
}) {
  const entries = Object.entries(evidence).filter(
    ([k, v]) => k !== 'line_items' && v !== null && v !== undefined && v !== '',
  )
  if (entries.length === 0) return null

  return (
    <div className="mt-3 rounded border border-paper-300 bg-paper-50/80 p-3">
      <p className="eyebrow mb-2">Evidence</p>
      <dl className="grid grid-cols-2 gap-x-4 gap-y-2.5 sm:grid-cols-3">
        {entries.map(([key, value]) => (
          <div key={key} className="min-w-0">
            <dt className="truncate text-2xs font-medium text-stone-500">
              {LABELS[key] ?? key.replace(/_/g, ' ')}
            </dt>
            <dd className="tabular truncate text-sm font-semibold text-stone-900">
              {formatValue(key, value, currency ?? undefined)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  )
}

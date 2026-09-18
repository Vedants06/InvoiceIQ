import { Receipt } from 'lucide-react'
import type { InvoiceDetail } from '../../types/analysis'
import { formatCurrency } from '../../lib/utils'

export default function LineItemsCard({ invoice }: { invoice: InvoiceDetail }) {
  const items = invoice.line_items ?? []
  if (items.length === 0) return null
  const c = invoice.currency ?? undefined
  const total = items.reduce((sum, li) => sum + (li.amount ?? 0), 0)

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-paper-200 text-stone-500">
            <Receipt className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
          Invoice line items
        </h2>
        <span className="tabular text-xs text-stone-400">{items.length} items</span>
      </header>

      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-paper-200">
              <th className="table-head px-5 py-2.5 text-left">Description</th>
              <th className="table-head px-3 py-2.5 text-right">Qty</th>
              <th className="table-head px-3 py-2.5 text-right">Rate</th>
              <th className="table-head px-5 py-2.5 text-right">Amount</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-paper-100">
            {items.map((li, i) => (
              <tr key={i} className="transition-colors hover:bg-paper-100/70">
                <td className="px-5 py-2.5 text-stone-800">{li.description ?? 'Service'}</td>
                <td className="tabular px-3 py-2.5 text-right text-stone-600">
                  {li.quantity != null ? `${li.quantity} hrs` : '—'}
                </td>
                <td className="tabular px-3 py-2.5 text-right text-stone-600">
                  {li.unit_price != null ? formatCurrency(li.unit_price, c) : '—'}
                </td>
                <td className="tabular px-5 py-2.5 text-right font-semibold text-stone-900">
                  {formatCurrency(li.amount, c)}
                </td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr className="border-t border-paper-300 bg-paper-100/70">
              <td className="px-5 py-2.5 text-xs font-semibold uppercase tracking-wider text-stone-500">
                Line item total
              </td>
              <td colSpan={2} />
              <td className="tabular px-5 py-2.5 text-right text-sm font-bold text-stone-900">
                {formatCurrency(total, c)}
              </td>
            </tr>
          </tfoot>
        </table>
      </div>
    </div>
  )
}

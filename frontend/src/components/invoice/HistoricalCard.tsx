import { TrendingUp } from 'lucide-react'
import type { HistoricalStats } from '../../types/analysis'
import { cn, formatCurrency } from '../../lib/utils'

function Stat({ label, value, tone }: { label: string; value: string; tone?: 'warn' }) {
  return (
    <div>
      <dt className="text-2xs font-medium text-stone-500">{label}</dt>
      <dd
        className={cn(
          'tabular text-sm font-bold',
          tone === 'warn' ? 'text-[#6d4d10]' : 'text-stone-900',
        )}
      >
        {value}
      </dd>
    </div>
  )
}

export default function HistoricalCard({
  stats,
  currency,
}: {
  stats: HistoricalStats | null | undefined
  currency?: string | null
}) {
  if (!stats) return null
  const unusual = stats.deviation_percent >= 50
  // Bar shows how far above/below the historical average this invoice sits.
  const pct = Math.min(Math.abs(stats.deviation_percent), 200) / 2

  return (
    <div className={cn('panel', unusual && 'border-[#f0dcaa]')}>
      <header className={cn('panel-header', unusual && 'bg-[#fdf7ea]/60')}>
        <h2 className="panel-title">
          <span
            className={cn(
              'flex h-7 w-7 items-center justify-center rounded',
              unusual ? 'bg-[#f9eed5] text-[#8a6212]' : 'bg-paper-200 text-stone-500',
            )}
          >
            <TrendingUp className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
          Vendor history
        </h2>
        {unusual && (
          <span className="chip border-[#f0dcaa] bg-[#fdf7ea] text-2xs text-[#6d4d10]">
            Above historical average
          </span>
        )}
      </header>

      <div className="p-5">
        <dl className="grid grid-cols-2 gap-x-4 gap-y-4 sm:grid-cols-3">
          <Stat
            label="Current invoice"
            value={formatCurrency(stats.current_amount, currency ?? undefined)}
          />
          <Stat
            label="Historical average"
            value={formatCurrency(stats.average_amount, currency ?? undefined)}
          />
          <Stat
            label="Deviation"
            value={`${stats.deviation_percent > 0 ? '+' : ''}${stats.deviation_percent}%`}
            tone={unusual ? 'warn' : undefined}
          />
          <Stat label="Prior invoices" value={String(stats.prior_invoice_count)} />
          <div className="col-span-2">
            <Stat
              label="Range (min–max)"
              value={`${formatCurrency(stats.min_amount, currency ?? undefined)} – ${formatCurrency(
                stats.max_amount,
                currency ?? undefined,
              )}`}
            />
          </div>
        </dl>

        <div className="mt-4">
          <div className="mb-1 flex items-baseline justify-between text-[10px] uppercase tracking-[0.14em] text-stone-400">
            <span>Below average</span>
            <span>Above average</span>
          </div>
          <div className="relative h-2 rounded bg-paper-200">
            <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-paper-400" />
            <div
              className={cn(
                'absolute top-0 h-full rounded transition-all duration-700 ease-spring',
                stats.deviation_percent >= 0 ? 'bg-[#d3a94c]' : 'bg-[#6f9f84]',
              )}
              style={{
                width: `${pct / 2}%`,
                left: stats.deviation_percent >= 0 ? '50%' : undefined,
                right: stats.deviation_percent < 0 ? '50%' : undefined,
              }}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

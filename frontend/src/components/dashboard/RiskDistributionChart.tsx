import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  type TooltipProps,
} from 'recharts'
import { PieChart } from 'lucide-react'
import type { RiskLevel, Stats } from '../../types/analysis'
import { RISK_STYLES } from '../risk/riskStyle'

const LEVELS: RiskLevel[] = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

function ChartTooltip({ active, payload }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null
  const point = payload[0].payload as { level: RiskLevel; count: number; share: number }
  return (
    <div className="rounded border border-paper-300 bg-paper-50 px-3 py-2 shadow-soft">
      <p className="flex items-center gap-1.5 text-xs font-bold text-stone-900">
        <span
          className="h-2 w-2 rounded-full"
          style={{ background: RISK_STYLES[point.level].hex }}
        />
        {RISK_STYLES[point.level].label}
      </p>
      <p className="tabular mt-0.5 text-xs text-stone-500">
        {point.count} {point.count === 1 ? 'invoice' : 'invoices'} · {point.share}%
      </p>
    </div>
  )
}

export default function RiskDistributionChart({ stats }: { stats: Stats }) {
  const total = LEVELS.reduce((sum, l) => sum + (stats.risk_distribution[l] ?? 0), 0)

  const data = LEVELS.map((level) => {
    const count = stats.risk_distribution[level] ?? 0
    return {
      level,
      count,
      share: total > 0 ? Math.round((count / total) * 100) : 0,
    }
  })

  return (
    <div className="card h-full p-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="panel-title">
            <span className="flex h-7 w-7 items-center justify-center rounded bg-paper-200 text-stone-500">
              <PieChart className="h-3.5 w-3.5" strokeWidth={1.75} />
            </span>
            Risk distribution
          </h3>
          <p className="mt-1 text-xs text-stone-400">
            {total > 0
              ? `${total} analyzed ${total === 1 ? 'invoice' : 'invoices'}`
              : 'No analyzed invoices yet'}
          </p>
        </div>
      </div>

      {total === 0 ? (
        <div className="flex h-[168px] items-center justify-center">
          <p className="max-w-[180px] text-center text-sm text-stone-400">
            Process an invoice to see where the risk sits.
          </p>
        </div>
      ) : (
        <>
          <div className="mt-4 h-[180px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data} margin={{ top: 8, right: 4, bottom: 0, left: -20 }}>
                <XAxis
                  dataKey="level"
                  tick={{ fontSize: 11, fill: '#94a3b8', fontWeight: 600 }}
                  axisLine={{ stroke: '#e2e8f0' }}
                  tickLine={false}
                  tickFormatter={(v: RiskLevel) => RISK_STYLES[v].label}
                />
                <YAxis
                  allowDecimals={false}
                  tick={{ fontSize: 11, fill: '#94a3b8' }}
                  axisLine={false}
                  tickLine={false}
                  width={44}
                />
                <Tooltip
                  content={<ChartTooltip />}
                  cursor={{ fill: 'rgb(148 163 184 / 0.10)' }}
                />
                <Bar dataKey="count" radius={[8, 8, 4, 4]} maxBarSize={56} animationDuration={700}>
                  {data.map((entry) => (
                    <Cell key={entry.level} fill={RISK_STYLES[entry.level].hex} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <ul className="mt-4 space-y-2 border-t border-paper-200 pt-4">
            {data.map((d) => (
              <li key={d.level} className="flex items-center gap-2.5 text-xs">
                <span
                  className="h-2 w-2 shrink-0 rounded-full"
                  style={{ background: RISK_STYLES[d.level].hex }}
                />
                <span className="font-semibold text-stone-600">
                  {RISK_STYLES[d.level].label}
                </span>
                <span className="tabular ml-auto font-semibold text-stone-900">{d.count}</span>
                <span className="tabular w-9 text-right text-stone-400">{d.share}%</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}

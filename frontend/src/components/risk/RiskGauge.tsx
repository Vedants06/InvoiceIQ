import { Gauge } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { Anomaly, RiskLevel } from '../../types/analysis'
import { RISK_BANDS, RISK_GUIDANCE, riskStyle } from './riskStyle'

const RADIUS = 80
const CIRCUMFERENCE = 2 * Math.PI * RADIUS
const ARC = CIRCUMFERENCE * (240 / 360) // 240° sweep

export default function RiskGauge({
  score,
  level,
  anomalies = [],
}: {
  score: number | null
  level: RiskLevel | null
  anomalies?: Anomaly[]
}) {
  const s = riskStyle(level)
  const value = score ?? 0
  const fraction = Math.min(Math.max(value / 100, 0), 1)
  const dash = ARC * fraction
  const top = [...anomalies].sort((a, b) => b.points - a.points).slice(0, 3)

  return (
    <div className={cn('panel overflow-hidden', s.bg, s.border)}>
      <div className="flex flex-col gap-6 p-6 sm:flex-row sm:items-center">
        {/* Dial */}
        <div className="relative mx-auto h-[132px] w-[190px] shrink-0 sm:mx-0">
          <svg viewBox="0 0 200 152" className="h-full w-full">
            <g transform="rotate(150 100 100)">
              <circle
                cx="100"
                cy="100"
                r={RADIUS}
                fill="none"
                stroke="#ded7c7"
                strokeWidth="10"
                strokeLinecap="butt"
                strokeDasharray={`${ARC} ${CIRCUMFERENCE}`}
              />
              {level && dash > 0.5 && (
                <circle
                  cx="100"
                  cy="100"
                  r={RADIUS}
                  fill="none"
                  stroke={s.hex}
                  strokeWidth="10"
                  strokeLinecap="butt"
                  strokeDasharray={`${dash} ${CIRCUMFERENCE}`}
                  style={{ transition: 'stroke-dasharray 1s cubic-bezier(0.22, 1, 0.36, 1)' }}
                />
              )}
            </g>
          </svg>
          <div className="absolute inset-x-0 top-[44%] flex flex-col items-center">
            <span className="tabular font-serif text-[42px] font-semibold leading-none text-stone-900">
              {score ?? '—'}
            </span>
            <span className="mt-1 font-serif text-[11px] italic text-stone-500">
              / 100
            </span>
          </div>
        </div>

        {/* Readout */}
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className={cn('chip', s.pill)}>
              <span className={cn('h-1.5 w-1.5 rounded-full', s.dot)} />
              {level ? `${s.label} RISK` : 'NOT SCORED'}
            </span>
            {level && (
              <span className="inline-flex items-center gap-1.5 text-xs text-stone-500">
                <Gauge className="h-3.5 w-3.5 text-stone-400" strokeWidth={1.75} />
                Deterministic score
              </span>
            )}
          </div>

          <p className="mt-2.5 text-sm leading-relaxed text-stone-600">
            {level
              ? RISK_GUIDANCE[level]
              : 'Run the analysis to compute a verification-based risk score.'}
          </p>

          {top.length > 0 && (
            <div className="mt-4">
              <p className="eyebrow">Top contributors</p>
              <ul className="mt-2 space-y-1.5">
                {top.map((a) => (
                  <li key={a.id} className="flex items-center gap-2 text-xs">
                    <span className="min-w-0 flex-1 truncate text-stone-600">{a.title}</span>
                    <span className="tabular shrink-0 border border-paper-300 bg-paper-50 px-1.5 py-0.5 font-semibold text-stone-700">
                      +{a.points}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* Band legend */}
      <div className="grid grid-cols-4 divide-x divide-paper-300 border-t border-paper-300 bg-paper-200/40">
        {RISK_BANDS.map((band) => {
          const style = riskStyle(band.level)
          const active = level === band.level
          return (
            <div
              key={band.level}
              className={cn('px-3 py-2.5 text-center', active && 'bg-paper-50')}
            >
              <p
                className={cn(
                  'text-[10px] font-semibold uppercase tracking-[0.16em]',
                  active ? style.text : 'text-stone-400',
                )}
              >
                {style.label}
              </p>
              <p className="tabular mt-0.5 text-[11px] text-stone-400">
                {band.from}–{band.to}
              </p>
            </div>
          )
        })}
      </div>
    </div>
  )
}

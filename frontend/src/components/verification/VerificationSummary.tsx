import { Check, Minus, ShieldCheck, X } from 'lucide-react'
import { cn } from '../../lib/utils'
import type { CheckStatus, VerificationCheck } from '../../types/analysis'

const ICONS: Record<CheckStatus, { Icon: typeof Check; tile: string; pill: string; label: string }> =
  {
    PASSED: {
      Icon: Check,
      tile: 'bg-[#e3efe7] text-[#2f6b47]',
      pill: 'border-[#cfe3d7] bg-[#f1f7f3] text-[#28593c]',
      label: 'Passed',
    },
    FAILED: {
      Icon: X,
      tile: 'bg-[#f7dbd9] text-[#96231b]',
      pill: 'border-[#f0c4c1] bg-[#fbeceb] text-[#7f1d16]',
      label: 'Failed',
    },
    NOT_PERFORMED: {
      Icon: Minus,
      tile: 'bg-paper-200 text-stone-400',
      pill: 'border-paper-300 bg-paper-100 text-stone-500',
      label: 'Not performed',
    },
  }

export default function VerificationSummary({ checks }: { checks: VerificationCheck[] }) {
  if (!checks || checks.length === 0) return null

  const passed = checks.filter((c) => c.status === 'PASSED').length
  const failed = checks.filter((c) => c.status === 'FAILED').length
  const skipped = checks.filter((c) => c.status === 'NOT_PERFORMED').length

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-paper-200 text-stone-500">
            <ShieldCheck className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
          Verification summary
        </h2>
        <div className="flex items-center gap-1.5">
          {[
            { key: 'PASSED', count: passed, pill: ICONS.PASSED.pill },
            { key: 'FAILED', count: failed, pill: ICONS.FAILED.pill },
            { key: 'NOT_PERFORMED', count: skipped, pill: ICONS.NOT_PERFORMED.pill },
          ]
            .filter((s) => s.count > 0)
            .map((s) => (
              <span key={s.key} className={cn('chip px-2 py-0.5 text-2xs', s.pill)}>
                <span className="tabular">{s.count}</span>
                {s.key === 'PASSED' ? 'passed' : s.key === 'FAILED' ? 'failed' : 'skipped'}
              </span>
            ))}
        </div>
      </header>

      {checks.length > 0 && (
        <div className="flex h-1.5 gap-0.5 px-5 pt-4">
          {(['PASSED', 'FAILED', 'NOT_PERFORMED'] as CheckStatus[]).map((status) => {
            const count = checks.filter((c) => c.status === status).length
            if (!count) return null
            return (
              <div
                key={status}
                className={cn(
                  'h-full rounded-full transition-all duration-700 ease-spring',
                  status === 'PASSED'
                    ? 'bg-[#6f9f84]'
                    : status === 'FAILED'
                      ? 'bg-[#d06d67]'
                      : 'bg-stone-200',
                )}
                style={{ width: `${(count / checks.length) * 100}%` }}
              />
            )
          })}
        </div>
      )}

      <ul className="divide-y divide-paper-100 px-5">
        {checks.map((check) => {
          const { Icon, tile, pill, label } = ICONS[check.status]
          return (
            <li key={check.key} className="flex items-start gap-3 py-3.5">
              <span
                className={cn(
                  'mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded',
                  tile,
                )}
              >
                <Icon className="h-3.5 w-3.5" strokeWidth={2.25} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span
                    className={cn(
                      'text-sm font-semibold',
                      check.status === 'FAILED' ? 'text-stone-900' : 'text-stone-800',
                    )}
                  >
                    {check.label}
                  </span>
                  <span className={cn('chip px-2 py-0.5 text-2xs', pill)}>{label}</span>
                </div>
                {check.detail && (
                  <p
                    className={cn(
                      'mt-1 text-sm leading-relaxed',
                      check.status === 'FAILED' ? 'text-[#96231b]/90' : 'text-stone-500',
                    )}
                  >
                    {check.detail}
                  </p>
                )}
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

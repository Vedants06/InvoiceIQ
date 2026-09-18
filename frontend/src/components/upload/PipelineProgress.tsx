import { useEffect, useState } from 'react'
import { Check, Loader2 } from 'lucide-react'
import { cn } from '../../lib/utils'

const STEPS = [
  'Invoice uploaded',
  'Extracting invoice information',
  'Reading contract',
  'Processing timesheet',
  'Validating extracted data',
  'Validating invoice against contract',
  'Reconciling hours',
  'Detecting anomalies',
  'Calculating risk',
  'Generating explanation',
]

export default function PipelineProgress({ active }: { active: boolean }) {
  const [visible, setVisible] = useState(0)

  useEffect(() => {
    if (!active) {
      setVisible(0)
      return
    }
    setVisible(1)
    const interval = setInterval(() => {
      setVisible((v) => Math.min(v + 1, STEPS.length))
    }, 450)
    return () => clearInterval(interval)
  }, [active])

  if (!active) return null

  const percent = Math.round((visible / STEPS.length) * 100)

  return (
    <div className="card animate-fade-in-up overflow-hidden p-5">
      <div className="flex items-center justify-between gap-3">
        <h3 className="panel-title">
          <Loader2 className="h-4 w-4 animate-spin text-accent-700" strokeWidth={1.75} />
          Processing pipeline
        </h3>
        <span className="tabular text-xs font-semibold text-stone-500">{percent}%</span>
      </div>

      <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-paper-200">
        <div
          className="h-full rounded-full bg-stone-900 transition-[width] duration-500 ease-spring"
          style={{ width: `${percent}%` }}
        />
      </div>

      <ul className="mt-4 space-y-2">
        {STEPS.map((step, i) => {
          const done = i < visible
          const inProgress = i === visible
          return (
            <li
              key={step}
              className={cn(
                'flex items-center gap-2.5 text-sm transition-all duration-300',
                !done && !inProgress && 'text-stone-300',
                inProgress && 'font-semibold text-stone-900',
                done && 'text-stone-600',
              )}
            >
              {done ? (
                <span className="flex h-4 w-4 items-center justify-center rounded bg-[#e3efe7]">
                  <Check className="h-3 w-3 text-[#2f6b47]" strokeWidth={2.25} />
                </span>
              ) : inProgress ? (
                <Loader2
                  className="h-4 w-4 animate-spin text-accent-700"
                  strokeWidth={1.75}
                />
              ) : (
                <span className="h-4 w-4 rounded border-2 border-paper-300" />
              )}
              <span className={cn(inProgress && 'text-stone-900')}>{step}</span>
            </li>
          )
        })}
      </ul>
    </div>
  )
}

import { cn } from '@/lib/utils'

export interface SegmentedOption<T extends string> {
  value: T
  label: string
  /** Optional colour dot rendered before the label. */
  dotClassName?: string
  count?: number
}

interface SegmentedProps<T extends string> {
  options: SegmentedOption<T>[]
  value: T
  onChange: (value: T) => void
  label?: string
  size?: 'sm' | 'md'
  className?: string
}

export default function Segmented<T extends string>({
  options,
  value,
  onChange,
  label,
  size = 'sm',
  className,
}: SegmentedProps<T>) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      {label && (
        <span className="text-[10px] font-semibold uppercase tracking-[0.16em] text-stone-500">
          {label}
        </span>
      )}
      <div
        role="group"
        aria-label={label}
        className="flex items-center divide-x divide-paper-300 overflow-hidden rounded border border-paper-300 bg-paper-100"
      >
        {options.map((opt) => {
          const active = opt.value === value
          return (
            <button
              key={opt.value || 'all'}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(opt.value)}
              className={cn(
                'inline-flex items-center gap-1.5 font-medium transition-colors duration-150',
                size === 'sm' ? 'px-2.5 py-1 text-xs' : 'px-3.5 py-1.5 text-[13px]',
                active
                  ? 'bg-paper-50 text-stone-900'
                  : 'bg-transparent text-stone-500 hover:bg-paper-200/60 hover:text-stone-800',
              )}
            >
              {opt.dotClassName && (
                <span className={cn('h-1.5 w-1.5 rounded-full', opt.dotClassName)} />
              )}
              {opt.label}
              {opt.count !== undefined && (
                <span className={cn('tabular text-[10px]', active ? 'text-stone-500' : 'text-stone-400')}>
                  {opt.count}
                </span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}

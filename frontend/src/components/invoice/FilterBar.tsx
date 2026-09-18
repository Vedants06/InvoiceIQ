import { Search, X, SlidersHorizontal } from 'lucide-react'
import type { RiskLevel } from '../../types/analysis'
import Segmented from '../ui/Segmented'
import { RISK_STYLES } from '../risk/riskStyle'

export interface Filters {
  risk_level: RiskLevel | ''
  status: 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED' | ''
  vendor: string
}

export const EMPTY_FILTERS: Filters = { risk_level: '', status: '', vendor: '' }

const RISK_OPTIONS: { value: Filters['risk_level']; label: string; dotClassName?: string }[] = [
  { value: '', label: 'All' },
  { value: 'LOW', label: 'Low', dotClassName: RISK_STYLES.LOW.dot },
  { value: 'MEDIUM', label: 'Medium', dotClassName: RISK_STYLES.MEDIUM.dot },
  { value: 'HIGH', label: 'High', dotClassName: RISK_STYLES.HIGH.dot },
  { value: 'CRITICAL', label: 'Critical', dotClassName: RISK_STYLES.CRITICAL.dot },
]

const STATUS_OPTIONS: { value: Filters['status']; label: string }[] = [
  { value: '', label: 'Any' },
  { value: 'PENDING_REVIEW', label: 'Pending' },
  { value: 'APPROVED', label: 'Approved' },
  { value: 'REJECTED', label: 'Rejected' },
]

export default function FilterBar({
  filters,
  onChange,
  resultCount,
  isLoading,
}: {
  filters: Filters
  onChange: (filters: Filters) => void
  resultCount?: number
  isLoading?: boolean
}) {
  const active = Boolean(filters.risk_level || filters.status || filters.vendor)

  return (
    <div className="card mb-5 flex flex-col gap-3 p-3 sm:flex-row sm:items-center">
      <div className="relative flex-1 sm:max-w-xs">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
        <input
          type="text"
          value={filters.vendor}
          onChange={(e) => onChange({ ...filters, vendor: e.target.value })}
          placeholder="Search vendor…"
          aria-label="Search by vendor"
          className="input py-2 pl-9 pr-9"
        />
        {filters.vendor && (
          <button
            type="button"
            onClick={() => onChange({ ...filters, vendor: '' })}
            aria-label="Clear search"
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded-md p-1 text-stone-400 transition hover:bg-paper-200 hover:text-stone-600"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        )}
      </div>

      <div className="flex flex-wrap items-center gap-2.5">
        <Segmented
          label="Risk"
          options={RISK_OPTIONS}
          value={filters.risk_level}
          onChange={(risk_level) => onChange({ ...filters, risk_level })}
        />
        <Segmented
          label="Status"
          options={STATUS_OPTIONS}
          value={filters.status}
          onChange={(status) => onChange({ ...filters, status })}
        />
      </div>

      <div className="ml-auto flex items-center gap-3">
        {resultCount !== undefined && !isLoading && (
          <span className="tabular whitespace-nowrap text-xs text-stone-400">
            {resultCount} {resultCount === 1 ? 'invoice' : 'invoices'}
          </span>
        )}
        {active ? (
          <button
            onClick={() => onChange(EMPTY_FILTERS)}
            className="inline-flex items-center gap-1.5 rounded px-2.5 py-1.5 text-xs font-semibold text-stone-500 transition hover:bg-paper-200 hover:text-stone-800"
          >
            <X className="h-3.5 w-3.5" />
            Clear
          </button>
        ) : (
          <SlidersHorizontal className="hidden h-4 w-4 text-stone-300 sm:block" />
        )}
      </div>
    </div>
  )
}

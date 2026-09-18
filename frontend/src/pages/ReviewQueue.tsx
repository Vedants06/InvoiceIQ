import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { FileSearch, UserCheck } from 'lucide-react'
import PageHeader from '@/components/layout/PageHeader'
import InvoiceTable, { InvoiceTableEmpty } from '@/components/invoice/InvoiceTable'
import FilterBar, { EMPTY_FILTERS, type Filters } from '@/components/invoice/FilterBar'
import EmptyState from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/Skeleton'
import { listInvoices } from '@/api/invoices'

export default function ReviewQueue() {
  // Queue is analyzed invoices pending a human decision; risk/vendor filters
  // narrow it further.
  const [filters, setFilters] = useState<Filters>({ ...EMPTY_FILTERS, status: 'PENDING_REVIEW' })

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices', filters],
    queryFn: () =>
      listInvoices({
        status: filters.status || 'PENDING_REVIEW',
        risk_level: filters.risk_level || undefined,
        vendor: filters.vendor.trim() || undefined,
      }),
  })

  const queue = invoices.filter((i) => i.processing_status === 'COMPLETED')
  const filtered = Boolean(filters.risk_level || filters.vendor.trim())

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Review Queue"
        description="Analyzed invoices that need a human approve or reject decision before payment."
        eyebrow={
          !isLoading ? (
            <span className="tabular text-xs font-semibold text-accent-700">
              {queue.length} awaiting decision
            </span>
          ) : undefined
        }
        action={
          <span className="inline-flex items-center gap-2 rounded border border-paper-300 bg-paper-50 px-3 py-2 text-xs font-medium text-stone-500 shadow-xs">
            <UserCheck className="h-3.5 w-3.5 text-accent-700" strokeWidth={2} />
            Decisions are always human
          </span>
        }
      />

      <FilterBar
        filters={filters}
        onChange={setFilters}
        resultCount={queue.length}
        isLoading={isLoading}
      />

      {isLoading ? (
        <TableSkeleton rows={5} />
      ) : queue.length > 0 ? (
        <div className="animate-fade-in-up">
          <InvoiceTable invoices={queue} />
        </div>
      ) : filtered ? (
        <EmptyState
          icon={<FileSearch className="h-6 w-6" strokeWidth={2} />}
          title="Nothing matches these filters"
          description="Adjust the risk level or vendor search to widen the queue."
          action={
            <button onClick={() => setFilters(EMPTY_FILTERS)} className="btn-secondary">
              Clear filters
            </button>
          }
        />
      ) : (
        <InvoiceTableEmpty
          title="Review queue is empty"
          description="Analyzed invoices land here until you approve or reject them. High and critical risk invoices are the usual candidates."
        />
      )}
    </div>
  )
}

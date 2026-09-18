import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { FileSearch, UploadCloud } from 'lucide-react'
import PageHeader from '@/components/layout/PageHeader'
import InvoiceTable, { InvoiceTableEmpty } from '@/components/invoice/InvoiceTable'
import FilterBar, { EMPTY_FILTERS, type Filters } from '@/components/invoice/FilterBar'
import EmptyState from '@/components/ui/EmptyState'
import { TableSkeleton } from '@/components/ui/Skeleton'
import { listInvoices } from '@/api/invoices'

export default function Invoices() {
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS)

  const { data: invoices = [], isLoading } = useQuery({
    queryKey: ['invoices', filters],
    queryFn: () =>
      listInvoices({
        status: filters.status || undefined,
        risk_level: filters.risk_level || undefined,
        vendor: filters.vendor.trim() || undefined,
      }),
  })

  const filtered = Boolean(filters.risk_level || filters.status || filters.vendor.trim())

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Invoices"
        description="Every processed invoice with its risk score and review status."
        eyebrow={
          !isLoading ? (
            <span className="tabular text-xs font-semibold text-accent-700">
              {invoices.length} total
            </span>
          ) : undefined
        }
        action={
          <Link to="/upload" className="btn-primary">
            <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
            Analyze invoice
          </Link>
        }
      />

      <FilterBar
        filters={filters}
        onChange={setFilters}
        resultCount={invoices.length}
        isLoading={isLoading}
      />

      {isLoading ? (
        <TableSkeleton rows={6} />
      ) : invoices.length > 0 ? (
        <div className="animate-fade-in-up">
          <InvoiceTable invoices={invoices} />
        </div>
      ) : filtered ? (
        <EmptyState
          icon={<FileSearch className="h-6 w-6" strokeWidth={2} />}
          title="No invoices match these filters"
          description="Try a different risk level or status, or clear the search to see everything."
          action={
            <button onClick={() => setFilters(EMPTY_FILTERS)} className="btn-secondary">
              Clear filters
            </button>
          }
        />
      ) : (
        <InvoiceTableEmpty
          title="No invoices yet"
          description="Upload an invoice together with its contract to run deterministic verification."
          action={
            <Link to="/upload" className="btn-primary">
              <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
              Analyze invoice
            </Link>
          }
        />
      )}
    </div>
  )
}

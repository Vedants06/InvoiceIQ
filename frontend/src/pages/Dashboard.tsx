import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ArrowRight, FileCheck2, UploadCloud } from 'lucide-react'
import PageHeader from '@/components/layout/PageHeader'
import StatCard from '@/components/ui/StatCard'
import EmptyState from '@/components/ui/EmptyState'
import { PageSkeleton, TableSkeleton } from '@/components/ui/Skeleton'
import InvoiceTable, { InvoiceTableEmpty } from '@/components/invoice/InvoiceTable'
import RiskDistributionChart from '@/components/dashboard/RiskDistributionChart'
import { getStats } from '@/api/invoices'

export default function Dashboard() {
  const { data: stats, isLoading } = useQuery({
    queryKey: ['stats'],
    queryFn: getStats,
  })

  if (isLoading) return <PageSkeleton />

  const total = stats?.total_processed ?? 0
  const pending = stats?.pending_review ?? 0
  const highRisk = stats?.high_risk ?? 0
  const attention = (stats?.recent ?? []).filter(
    (i) =>
      i.processing_status === 'COMPLETED' &&
      i.status === 'PENDING_REVIEW' &&
      (i.risk_level === 'HIGH' || i.risk_level === 'CRITICAL'),
  )

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Dashboard"
        description="Invoice verification activity across every analyzed document."
        action={
          <Link to="/upload" className="btn-primary">
            <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
            Analyze an invoice
          </Link>
        }
      />

      {total === 0 && (
        <EmptyState
          icon={<FileCheck2 className="h-5 w-5" strokeWidth={1.75} />}
          title="Nothing analyzed yet"
          description="Upload an invoice with its contract to run the deterministic verification pipeline — or load a demo scenario, which needs no API key."
          action={
            <>
              <Link to="/upload" className="btn-primary">
                <UploadCloud className="h-4 w-4" strokeWidth={1.75} />
                Analyze an invoice
              </Link>
              <Link to="/upload#demo" className="btn-secondary">
                Try a demo scenario
              </Link>
            </>
          }
          className="mb-8"
        />
      )}

      <div className="stagger grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-6">
        <StatCard
          label="Processed"
          value={stats?.total_processed ?? '—'}
          hint="Completed analyses"
        />
        <StatCard
          label="Awaiting review"
          value={stats?.pending_review ?? '—'}
          tone={pending > 0 ? 'warning' : 'neutral'}
          hint="Human decision pending"
        />
        <StatCard label="Approved" value={stats?.approved ?? '—'} tone="success" hint="Cleared for payment" />
        <StatCard label="Rejected" value={stats?.rejected ?? '—'} hint="Blocked by a reviewer" />
        <StatCard
          label="High risk"
          value={stats?.high_risk ?? '—'}
          tone={highRisk > 0 ? 'danger' : 'neutral'}
          hint="High or critical score"
        />
        <StatCard
          label="Avg risk score"
          value={stats?.average_risk_score ?? '—'}
          tone="accent"
          hint="Across scored invoices"
        />
      </div>

      {pending > 0 && (
        <div className="mt-6 flex flex-col gap-3 border-l-2 border-[#c9a227] bg-[#fdf7ea]/60 px-4 py-3.5 sm:flex-row sm:items-center">
          <div className="min-w-0 flex-1">
            <p className="text-[13.5px] font-semibold text-stone-900">
              {pending} {pending === 1 ? 'invoice is' : 'invoices are'} waiting on a human decision
            </p>
            <p className="mt-0.5 text-[12.5px] text-stone-600">
              InvoiceIQ flags risk indicators — approving or rejecting stays with you.
            </p>
          </div>
          <Link to="/review" className="btn-secondary btn-sm shrink-0">
            Open review queue
            <ArrowRight className="h-3.5 w-3.5" strokeWidth={1.75} />
          </Link>
        </div>
      )}

      <div className="mt-8 grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-1">
          {stats ? (
            <RiskDistributionChart stats={stats} />
          ) : (
            <div className="card h-64 animate-pulse" />
          )}
        </div>

        <div className="lg:col-span-2">
          <div className="mb-3 flex items-end justify-between gap-3 border-b border-paper-300 pb-2">
            <h2 className="panel-title">Recent invoices</h2>
            <Link
              to="/invoices"
              className="inline-flex items-center gap-1 text-[11.5px] font-medium text-accent-800 underline-offset-2 transition-colors hover:underline"
            >
              View all
              <ArrowRight className="h-3.5 w-3.5" strokeWidth={1.75} />
            </Link>
          </div>
          {!stats ? (
            <TableSkeleton rows={4} />
          ) : stats.recent.length > 0 ? (
            <InvoiceTable invoices={stats.recent} compact />
          ) : (
            <InvoiceTableEmpty
              title="Nothing analyzed yet"
              description="Processed invoices appear here with their risk score and review status."
              action={
                <Link to="/upload" className="btn-secondary">
                  Analyze an invoice
                </Link>
              }
            />
          )}

          {attention.length > 0 && (
            <div className="mt-8">
              <h2 className="panel-title mb-3">
                Needs attention
                <span className="tabular ml-1.5 rounded border border-paper-300 bg-paper-100 px-1.5 text-[10px] font-semibold text-stone-600">
                  {attention.length}
                </span>
              </h2>
              <div className="panel divide-y divide-paper-200">
                {attention.map((inv) => (
                  <Link
                    key={inv.id}
                    to={`/invoices/${inv.id}`}
                    className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-paper-100"
                  >
                    <span
                      className="h-1.5 w-1.5 shrink-0 rounded-full"
                      style={{ background: inv.risk_level === 'CRITICAL' ? '#96231b' : '#a4461d' }}
                    />
                    <span className="min-w-0 flex-1 truncate text-[13.5px] text-stone-800">
                      <span className="font-semibold text-stone-900">
                        {inv.invoice_number ?? '—'}
                      </span>
                      <span className="mx-2 text-paper-400">|</span>
                      {inv.vendor_name ?? 'Unknown vendor'}
                    </span>
                    <ArrowRight className="h-4 w-4 shrink-0 text-stone-300" strokeWidth={1.75} />
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

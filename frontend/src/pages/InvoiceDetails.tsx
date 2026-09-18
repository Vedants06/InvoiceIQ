import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  AlertCircle,
  ArrowLeft,
  Building2,
  CalendarDays,
  Download,
  FileWarning,
} from 'lucide-react'
import { Play, RefreshCw } from 'lucide-react'
import PageHeader from '@/components/layout/PageHeader'
import RiskGauge from '@/components/risk/RiskGauge'
import CoverageBadge from '@/components/invoice/CoverageBadge'
import LineItemsCard from '@/components/invoice/LineItemsCard'
import VerificationSummary from '@/components/verification/VerificationSummary'
import AnomalyCard from '@/components/anomalies/AnomalyCard'
import FactsPanel from '@/components/invoice/FactsPanel'
import HistoricalCard from '@/components/invoice/HistoricalCard'
import DocumentPreview from '@/components/preview/DocumentPreview'
import ExplanationCard from '@/components/invoice/ExplanationCard'
import ReviewPanel from '@/components/review/ReviewPanel'
import StatusBadge, { ProcessingBadge } from '@/components/review/StatusBadge'
import Segmented from '@/components/ui/Segmented'
import EmptyState from '@/components/ui/EmptyState'
import { useInvoiceAnalysis } from '@/hooks/useInvoiceAnalysis'
import { formatCurrency, formatDate } from '@/lib/utils'

export default function InvoiceDetails() {
  const { id } = useParams()
  const [view, setView] = useState<'analysis' | 'documents'>('analysis')
  const {
    invoice,
    isLoading,
    runAnalysis,
    isAnalyzing,
    analyzeError,
    submitReview,
    isReviewing,
    reviewError,
  } = useInvoiceAnalysis(id)

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="skeleton h-4 w-32" />
        <div className="skeleton h-8 w-64" />
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
          <div className="space-y-6 lg:col-span-3">
            <div className="skeleton h-56 rounded-md" />
            <div className="skeleton h-40 rounded-md" />
            <div className="skeleton h-64 rounded-md" />
          </div>
          <div className="hidden lg:col-span-2 lg:block">
            <div className="skeleton h-96 rounded-md" />
          </div>
        </div>
      </div>
    )
  }

  if (!invoice) {
    return (
      <EmptyState
        icon={<FileWarning className="h-6 w-6" strokeWidth={2} />}
        title="Invoice not found"
        description="It may have been removed, or the link is out of date."
        action={
          <Link to="/invoices" className="btn-primary">
            Back to invoices
          </Link>
        }
      />
    )
  }

  const completed = invoice.processing_status === 'COMPLETED'
  const failed = invoice.processing_status === 'FAILED'

  return (
    <div className="animate-fade-in space-y-6">
      <Link
        to="/invoices"
        className="inline-flex items-center gap-1.5 text-xs font-semibold text-stone-500 transition hover:text-accent-800"
      >
        <ArrowLeft className="h-3.5 w-3.5" strokeWidth={1.75} />
        All invoices
      </Link>

      <PageHeader
        title={`Invoice ${invoice.invoice_number ?? '(unprocessed)'}`}
        description={
          <span className="flex flex-wrap items-center gap-x-2 gap-y-1">
            {invoice.vendor_name && (
              <span className="inline-flex items-center gap-1 font-medium text-stone-600">
                <Building2 className="h-3.5 w-3.5 text-stone-400" />
                {invoice.vendor_name}
              </span>
            )}
            <span className="text-stone-300">•</span>
            <span className="tabular font-semibold text-stone-700">
              {formatCurrency(invoice.total, invoice.currency ?? undefined)}
            </span>
            <span className="text-stone-300">•</span>
            <span className="inline-flex items-center gap-1">
              <CalendarDays className="h-3.5 w-3.5 text-stone-400" />
              {formatDate(invoice.invoice_date ?? invoice.created_at)}
            </span>
          </span>
        }
        action={
          <div className="flex flex-wrap items-center gap-2">
            <ProcessingBadge status={invoice.processing_status} />
            {completed && <CoverageBadge coverage={invoice.extraction_coverage} />}
            {invoice.status && <StatusBadge status={invoice.status} />}
            {completed && (
              <a
                href={`/api/invoices/${invoice.id}/export`}
                className="btn-secondary btn-sm"
                title="Download the full deterministic analysis as CSV"
              >
                <Download className="h-3.5 w-3.5" strokeWidth={1.75} />
                Export CSV
              </a>
            )}
            {!completed && !isAnalyzing && (
              <button className="btn-primary btn-sm" onClick={() => runAnalysis()} disabled={isAnalyzing}>
                <Play className="h-3.5 w-3.5" strokeWidth={1.75} />
                Run analysis
              </button>
            )}
          </div>
        }
      />

      {/* Processing / failure states */}
      {isAnalyzing && (
        <div className="card flex items-center gap-3 p-6 text-stone-600">
          <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent-500 border-t-transparent" />
          Running verification, anomaly detection and risk scoring…
        </div>
      )}

      {(analyzeError || failed) && !isAnalyzing && (
        <div className="rounded-md border border-[#f0c4c1] bg-[#fbeceb] p-6">
          <div className="flex items-start gap-3 text-[#7f1d16]">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#f7dbd9]">
              <AlertCircle className="h-4 w-4" strokeWidth={1.75} />
            </span>
            <div>
              <p className="font-serif text-[18px] font-semibold">We couldn’t complete the analysis.</p>
              <p className="mt-1 text-sm leading-relaxed">
                {analyzeError instanceof Error
                  ? analyzeError.message
                  : 'Extraction failed. Check that the documents are clear and try again — or use a demo scenario.'}
              </p>
            </div>
          </div>
          <div className="mt-5 flex flex-wrap gap-3">
            <button className="btn-secondary" onClick={() => runAnalysis()} disabled={isAnalyzing}>
              <RefreshCw className="h-4 w-4" strokeWidth={1.75} />
              Retry analysis
            </button>
            <Link to="/upload" className="btn-primary">
              Try a demo scenario
            </Link>
          </div>
        </div>
      )}

      {/* Results */}
      {completed && (
        <>
          <div className="lg:hidden">
            <Segmented
              className="justify-center"
              size="md"
              value={view}
              onChange={setView}
              options={[
                { value: 'analysis', label: 'Analysis' },
                { value: 'documents', label: 'Documents' },
              ]}
            />
          </div>

          <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
            {/* Analysis column */}
            <div
              className={`space-y-6 lg:col-span-3 ${view === 'documents' ? 'hidden lg:block' : ''}`}
            >
              <RiskGauge
                score={invoice.risk_score}
                level={invoice.risk_level}
                anomalies={invoice.anomalies}
              />

              <FactsPanel invoice={invoice} />

              <LineItemsCard invoice={invoice} />

              <HistoricalCard stats={invoice.historical} currency={invoice.currency} />

              <VerificationSummary checks={invoice.verification_checks ?? []} />

              <section id="anomalies" className="scroll-mt-24">
                <div className="mb-3 flex items-center justify-between gap-3">
                  <h2 className="panel-title">
                    Risk indicators
                    <span className="tabular ml-1 rounded border border-paper-300 bg-paper-100 px-1.5 py-0.5 text-[10px] font-semibold text-stone-600">
                      {invoice.anomalies.length}
                    </span>
                  </h2>
                  {invoice.anomalies.length > 0 && (
                    <span className="tabular text-xs text-stone-400">
                      {invoice.anomalies.reduce((sum, a) => sum + a.points, 0)} points total
                    </span>
                  )}
                </div>

                {invoice.anomalies.length === 0 ? (
                  <div className="card flex items-start gap-3 p-5">
                    <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#e3efe7] text-[#2f6b47]">
                      <svg
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth={2.25}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        className="h-4 w-4"
                      >
                        <path d="m5 13 4 4L19 7" />
                      </svg>
                    </span>
                    <div>
                      <p className="font-serif text-[17px] font-semibold text-stone-900">
                        No anomalies detected
                      </p>
                      <p className="mt-0.5 text-sm text-stone-500">
                        The invoice is consistent with its contract and timesheet.
                      </p>
                    </div>
                  </div>
                ) : (
                  <div className="stagger space-y-3">
                    {invoice.anomalies.map((anomaly) => (
                      <AnomalyCard key={anomaly.id} anomaly={anomaly} />
                    ))}
                  </div>
                )}
              </section>

              <ExplanationCard invoice={invoice} />

              <ReviewPanel
                invoice={invoice}
                onReview={submitReview}
                isReviewing={isReviewing}
                error={reviewError}
              />
            </div>

            {/* Document preview column (PRD §27) */}
            <div className={`lg:col-span-2 ${view === 'analysis' ? 'hidden lg:block' : ''}`}>
              <div className="lg:sticky lg:top-24">
                <DocumentPreview invoice={invoice} />
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}

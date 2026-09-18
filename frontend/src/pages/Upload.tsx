import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import {
  AlertCircle,
  ArrowRight,
  Building2,
  FileSpreadsheet,
  Loader2,
  Receipt,
  ShieldCheck,
  FlaskConical,
} from 'lucide-react'
import PageHeader from '@/components/layout/PageHeader'
import FileDropzone from '@/components/upload/FileDropzone'
import PipelineProgress from '@/components/upload/PipelineProgress'
import { uploadInvoice, analyzeInvoice, createDemoScenario } from '@/api/invoices'
import { ApiError } from '@/api/client'
import { cn } from '@/lib/utils'
import { RISK_STYLES } from '@/components/risk/riskStyle'
import type { RiskLevel } from '@/types/analysis'

const DEMO_SCENARIOS: {
  id: 'clean' | 'critical' | 'timesheet'
  label: string
  hint: string
  risk: RiskLevel
  score: number
}[] = [
  {
    id: 'clean',
    label: 'Clean Invoice',
    hint: 'Every check passes — the happy path.',
    risk: 'LOW',
    score: 0,
  },
  {
    id: 'critical',
    label: 'Critical Invoice',
    hint: 'Rate, hours, amount and timesheet all conflict.',
    risk: 'CRITICAL',
    score: 90,
  },
  {
    id: 'timesheet',
    label: 'Timesheet Anomaly',
    hint: 'Billed hours are not supported by the timesheet.',
    risk: 'MEDIUM',
    score: 25,
  },
]

const CHECKS = [
  'Vendor identity matches the contract',
  'Billing period falls inside contract dates',
  'Currency consistency across documents',
  'Hourly rate and hours within contract limits',
  'Amount does not exceed the contract maximum',
  'Line items add up to the stated total',
  'Billed hours reconcile with the timesheet',
]

export default function Upload() {
  const navigate = useNavigate()
  const [invoice, setInvoice] = useState<File | null>(null)
  const [contract, setContract] = useState<File | null>(null)
  const [timesheet, setTimesheet] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [aiUnavailable, setAiUnavailable] = useState(false)

  const canSubmit = Boolean(invoice && contract)

  const demoMutation = useMutation({
    mutationFn: (scenario: 'clean' | 'critical' | 'timesheet') => createDemoScenario(scenario),
    onSuccess: (result) => navigate(`/invoices/${result.id}`),
    onError: (err) =>
      setError(err instanceof ApiError ? err.message : 'Could not load demo scenario.'),
  })

  const mutation = useMutation({
    mutationFn: async () => {
      setError(null)
      setAiUnavailable(false)
      const form = new FormData()
      form.append('invoice', invoice!)
      form.append('contract', contract!)
      if (timesheet) form.append('timesheet', timesheet)
      const uploaded = await uploadInvoice(form)
      return analyzeInvoice(uploaded.invoice_id)
    },
    onSuccess: (result) => navigate(`/invoices/${result.id}`),
    onError: (err) => {
      if (err instanceof ApiError && err.status === 503) {
        // AI extraction unavailable — demo mode keeps the flow working (PRD §43).
        setAiUnavailable(true)
        setError(
          'Live AI extraction is unavailable (no API key or service unreachable). Use a demo scenario to run the full verification workflow.',
        )
      } else {
        setError(
          err instanceof ApiError
            ? err.message
            : 'Something went wrong while processing the documents.',
        )
      }
    },
  })

  const busy = mutation.isPending || demoMutation.isPending

  return (
    <div className="animate-fade-in">
      <PageHeader
        title="Analyze invoice"
        description="Upload an invoice with its contract (required) and timesheet (optional). Verification runs deterministically; AI explains the result."
      />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-5">
        {/* Upload */}
        <div className="lg:col-span-3">
          <div className="card p-6">
            <div className="space-y-5">
              <FileDropzone
                label="Invoice"
                accept=".pdf,.png,.jpg,.jpeg"
                hint="PDF, PNG or JPG"
                required
                icon={<Receipt className="h-3.5 w-3.5" />}
                file={invoice}
                onFile={setInvoice}
                disabled={busy}
              />
              <FileDropzone
                label="Contract"
                accept=".pdf"
                hint="PDF"
                required
                icon={<Building2 className="h-3.5 w-3.5" />}
                file={contract}
                onFile={setContract}
                disabled={busy}
              />
              <FileDropzone
                label="Timesheet"
                accept=".csv,.xlsx"
                hint="CSV or XLSX"
                icon={<FileSpreadsheet className="h-3.5 w-3.5" />}
                file={timesheet}
                onFile={setTimesheet}
                disabled={busy}
              />
            </div>

            {!timesheet && !busy && (
              <p className="mt-5 flex items-start gap-2 rounded bg-[#fdf7ea] px-3.5 py-2.5 text-xs text-[#5b4112]">
                <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" strokeWidth={1.75} />
                <span>
                  No timesheet provided — timesheet reconciliation cannot be performed. Every other
                  verification check still runs.
                </span>
              </p>
            )}

            {error && (
              <div className="mt-5 flex items-start gap-2.5 rounded bg-[#fbeceb] px-3.5 py-3 text-sm text-[#7f1d16]">
                <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" strokeWidth={1.75} />
                <span>{error}</span>
              </div>
            )}

            <button
              className="btn-primary mt-6 w-full py-3 text-[15px]"
              disabled={!canSubmit || busy}
              onClick={() => mutation.mutate()}
            >
              {mutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" strokeWidth={1.75} />
                  Analyzing documents…
                </>
              ) : (
                <>
                  <ShieldCheck className="h-4 w-4" strokeWidth={1.75} />
                  Analyze invoice
                </>
              )}
            </button>

            {!canSubmit && !busy && (
              <p className="mt-2.5 text-center text-xs text-stone-400">
                Add an invoice and its contract to continue.
              </p>
            )}

            {mutation.isPending && (
              <div className="mt-5">
                <PipelineProgress active />
              </div>
            )}
          </div>
        </div>

        {/* Side panel */}
        <div className="space-y-6 lg:col-span-2">
          <div id="demo" className="card p-5">
            <h3 className="panel-title">
              <span className="flex h-7 w-7 items-center justify-center rounded bg-accent-100 text-accent-700">
                <FlaskConical className="h-3.5 w-3.5" strokeWidth={2} />
              </span>
              Demo scenarios
            </h3>
            <p className="mt-1.5 text-xs leading-relaxed text-stone-500">
              No documents and no API key needed — these deterministic scenarios run the same
              verification pipeline end to end.
            </p>

            {aiUnavailable && (
              <p className="mt-3 rounded bg-accent-50 px-3 py-2 text-xs font-semibold text-accent-800">
                Recommended: pick a scenario below to see the complete workflow now.
              </p>
            )}

            <div className="mt-4 space-y-2.5">
              {DEMO_SCENARIOS.map((s) => {
                const style = RISK_STYLES[s.risk]
                return (
                  <button
                    key={s.id}
                    disabled={busy}
                    onClick={() => demoMutation.mutate(s.id)}
                    className="group flex w-full items-center gap-3 rounded border border-paper-300 bg-paper-50 p-3.5 text-left transition-colors duration-150 hover:border-accent-400 hover:bg-accent-50/40 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className="min-w-0 flex-1">
                      <span className="flex items-center gap-2">
                        <span className="truncate text-sm font-semibold text-stone-900">
                          {s.label}
                        </span>
                      </span>
                      <span className="mt-0.5 block text-xs leading-relaxed text-stone-500">
                        {s.hint}
                      </span>
                    </span>
                    <span className="flex shrink-0 flex-col items-end gap-1">
                      <span className={cn('chip text-2xs', style.pill)}>
                        <span className={cn('h-1.5 w-1.5 rounded-full', style.dot)} />
                        {s.score} {s.risk}
                      </span>
                      <ArrowRight
                        className="h-3.5 w-3.5 text-stone-300 transition group-hover:translate-x-0.5 group-hover:text-accent-700"
                        strokeWidth={1.75}
                      />
                    </span>
                  </button>
                )
              })}
            </div>
          </div>

          <div className="card bg-paper-200/50 p-5">
            <h3 className="panel-title text-accent-900">
              <span className="flex h-7 w-7 items-center justify-center rounded bg-paper-50/80 text-accent-700">
                <ShieldCheck className="h-3.5 w-3.5" strokeWidth={1.75} />
              </span>
              What gets checked
            </h3>
            <ul className="mt-3 space-y-2">
              {CHECKS.map((c) => (
                <li key={c} className="flex items-start gap-2 text-xs text-stone-600">
                  <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-accent-600" />
                  {c}
                </li>
              ))}
            </ul>
            <p className="mt-4 border-t border-accent-100 pt-3 text-2xs leading-relaxed text-stone-500">
              Risk scores are computed by backend rules, never by the model. The AI only reads
              documents and explains verified findings.
            </p>
          </div>
        </div>
      </div>

      {demoMutation.isPending && (
        <div className="mt-6">
          <PipelineProgress active />
        </div>
      )}
    </div>
  )
}

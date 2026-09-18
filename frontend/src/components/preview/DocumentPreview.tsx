import { useState } from 'react'
import { ExternalLink, FileSpreadsheet, FileText, Building2, PanelRight } from 'lucide-react'
import type { DocumentInfo, InvoiceDetail } from '../../types/analysis'
import { cn } from '../../lib/utils'
import { ContractPreview, InvoicePreview, TimesheetPreview } from './StructuredPreview'

const TABS = [
  { type: 'INVOICE' as const, label: 'Invoice', Icon: FileText },
  { type: 'CONTRACT' as const, label: 'Contract', Icon: Building2 },
  { type: 'TIMESHEET' as const, label: 'Timesheet', Icon: FileSpreadsheet },
]

function isImage(name: string) {
  return /\.(png|jpe?g)$/i.test(name)
}

function Body({ doc, invoice }: { doc: DocumentInfo; invoice: InvoiceDetail }) {
  const name = doc.file_name

  // Real uploaded files: embed the original document.
  if (!doc.is_demo) {
    const src = `/api/documents/${doc.id}/raw`
    if (isImage(name)) {
      return (
        <div className="flex justify-center bg-paper-200/70 p-4">
          <img src={src} alt={name} className="max-h-[560px] w-auto rounded object-contain shadow-soft" />
        </div>
      )
    }
    if (/\.pdf$/i.test(name)) {
      return <iframe src={src} title={name ?? 'Document'} className="h-[600px] w-full border-0" />
    }
    if (/\.csv$/i.test(name)) {
      return (
        <div className="p-4">
          <a
            href={src}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1.5 text-sm font-semibold text-accent-800 underline-offset-2 hover:underline"
          >
            Download {name}
            <ExternalLink className="h-3 w-3" />
          </a>
          {invoice.timesheet && (
            <div className="mt-3 rounded border border-paper-300 bg-paper-50">
              <TimesheetPreview timesheet={invoice.timesheet} />
            </div>
          )}
        </div>
      )
    }
    return (
      <div className="p-4 text-sm text-stone-500">
        <a
          href={src}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 font-semibold text-accent-800 underline-offset-2 hover:underline"
        >
          Open {name}
          <ExternalLink className="h-3 w-3" />
        </a>
      </div>
    )
  }

  // Demo documents: structured preview from the verified data.
  if (doc.document_type === 'INVOICE') return <InvoicePreview invoice={invoice} />
  if (doc.document_type === 'CONTRACT' && invoice.contract)
    return <ContractPreview contract={invoice.contract} currency={invoice.currency ?? undefined} />
  if (doc.document_type === 'TIMESHEET' && invoice.timesheet)
    return <TimesheetPreview timesheet={invoice.timesheet} />
  return <div className="p-6 text-sm text-stone-400">No preview available.</div>
}

export default function DocumentPreview({ invoice }: { invoice: InvoiceDetail }) {
  const docs = invoice.documents ?? []
  const available = TABS.filter((t) => docs.some((d) => d.document_type === t.type))
  const [active, setActive] = useState(available[0]?.type ?? 'INVOICE')

  const activeTab = available.find((t) => t.type === active) ?? available[0]
  const activeDoc = docs.find((d) => d.document_type === activeTab?.type)

  if (available.length === 0) {
    return (
      <div className="card flex flex-col items-center justify-center gap-2 p-10 text-center">
        <PanelRight className="h-6 w-6 text-stone-300" />
        <p className="text-sm text-stone-500">No documents attached.</p>
      </div>
    )
  }

  return (
    <div className="panel">
      <header className="panel-header">
        <h2 className="panel-title">
          <span className="flex h-7 w-7 items-center justify-center rounded bg-paper-200 text-stone-500">
            <PanelRight className="h-3.5 w-3.5" strokeWidth={1.75} />
          </span>
          Source documents
        </h2>
        {activeDoc?.is_demo && (
          <span className="chip border-paper-300 bg-paper-100 text-2xs text-stone-500">
            Demo document
          </span>
        )}
      </header>

      <div className="flex gap-1 border-b border-paper-300 bg-paper-100/70 p-1.5">
        {available.map(({ type, label, Icon }) => {
          const isActive = active === type
          return (
            <button
              key={type}
              onClick={() => setActive(type)}
              aria-pressed={isActive}
              className={cn(
                'flex flex-1 items-center justify-center gap-1.5 rounded px-2 py-1.5 text-xs font-semibold transition duration-150',
                isActive
                  ? 'bg-paper-50 text-stone-900 shadow-xs ring-1 ring-paper-300'
                  : 'text-stone-500 hover:bg-paper-50/70 hover:text-stone-700',
              )}
            >
              <Icon className={cn('h-3.5 w-3.5', isActive ? 'text-accent-700' : 'text-stone-400')} />
              {label}
            </button>
          )
        })}
      </div>

      {activeDoc && (
        <div className="flex items-center gap-2 border-b border-paper-200 bg-paper-50 px-4 py-2">
          <FileText className="h-3.5 w-3.5 shrink-0 text-stone-400" />
          <span className="truncate text-xs text-stone-500">{activeDoc.file_name}</span>
          {!activeDoc.is_demo && (
            <a
              href={`/api/documents/${activeDoc.id}/raw`}
              target="_blank"
              rel="noreferrer"
              className="ml-auto inline-flex shrink-0 items-center gap-1 text-2xs font-semibold text-accent-800 hover:underline"
            >
              Open
              <ExternalLink className="h-3 w-3" />
            </a>
          )}
        </div>
      )}

      <div className="max-h-[640px] overflow-auto bg-paper-100/40">
        {activeDoc ? (
          <Body doc={activeDoc} invoice={invoice} />
        ) : (
          <div className="p-6 text-sm text-stone-400">No document.</div>
        )}
      </div>
    </div>
  )
}

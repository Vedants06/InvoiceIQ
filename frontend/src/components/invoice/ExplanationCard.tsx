import { Quote, Info } from 'lucide-react'
import type { InvoiceDetail } from '../../types/analysis'

export default function ExplanationCard({ invoice }: { invoice: InvoiceDetail }) {
  if (invoice.explanation_available && invoice.explanation) {
    return (
      <div className="rounded-md border border-paper-300 bg-paper-200/40 px-6 py-5">
        <h3 className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
          <Quote className="h-3 w-3 text-accent-700" strokeWidth={2} />
          AI assessment
        </h3>
        <p className="mt-3 font-serif text-[16px] italic leading-[1.65] text-stone-800">
          {invoice.explanation}
        </p>
        <p className="mt-4 flex items-start gap-2 border-t border-paper-300 pt-3 text-[11.5px] leading-relaxed text-stone-500">
          <Info className="mt-0.5 h-3 w-3 shrink-0 text-stone-400" />
          Written from the verified findings above. It introduces no numbers of its own and does not
          decide the risk score or the review outcome.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-paper-300 bg-paper-200/40 px-6 py-5">
      <h3 className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-stone-500">
        <Info className="h-3 w-3 text-stone-400" strokeWidth={2} />
        AI assessment
      </h3>
      <p className="mt-3 font-serif text-[16px] italic text-stone-500">
        No AI explanation is available for this invoice.
      </p>
      <p className="mt-3 border-t border-paper-300 pt-3 text-[11.5px] leading-relaxed text-stone-500">
        The verification results, risk score and evidence are unaffected — they come from
        deterministic backend rules.
      </p>
    </div>
  )
}

import { api } from './client'
import type {
  InvoiceDetail,
  InvoiceSummary,
  ReviewDecision,
  Stats,
  UploadResponse,
} from '../types/analysis'

export function uploadInvoice(formData: FormData) {
  return api.upload<UploadResponse>('/invoices/upload', formData)
}

export function analyzeInvoice(id: string) {
  return api.post<InvoiceDetail>(`/invoices/${id}/analyze`)
}

export function getInvoice(id: string) {
  return api.get<InvoiceDetail>(`/invoices/${id}`)
}

export interface ListFilters {
  status?: string
  risk_level?: string
  vendor?: string
}

export function listInvoices(filters: ListFilters = {}) {
  const params = new URLSearchParams()
  if (filters.status) params.set('status', filters.status)
  if (filters.risk_level) params.set('risk_level', filters.risk_level)
  if (filters.vendor) params.set('vendor', filters.vendor)
  const qs = params.toString()
  return api.get<InvoiceSummary[]>(`/invoices${qs ? `?${qs}` : ''}`)
}

export function submitReview(id: string, decision: ReviewDecision, reason?: string) {
  return api.post<InvoiceDetail>(`/invoices/${id}/review`, { decision, reason })
}

export function getStats() {
  return api.get<Stats>('/stats')
}

export function createDemoScenario(scenario: 'clean' | 'critical' | 'timesheet') {
  return api.post<InvoiceDetail>(`/demo/${scenario}`)
}

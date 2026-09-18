// Types mirror the backend API response schemas.

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type BusinessStatus = 'PENDING_REVIEW' | 'APPROVED' | 'REJECTED'
export type ProcessingStatus = 'UPLOADED' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
export type CheckStatus = 'PASSED' | 'FAILED' | 'NOT_PERFORMED'
export type ReviewDecision = 'APPROVED' | 'REJECTED'

export interface LineItem {
  description?: string | null
  quantity?: number | null
  unit_price?: number | null
  amount?: number | null
}

export interface ContractFacts {
  vendor_name?: string | null
  start_date?: string | null
  end_date?: string | null
  hourly_rate?: number | null
  max_hours?: number | null
  max_amount?: number | null
  currency?: string | null
  payment_terms?: string | null
}

export interface TimesheetFacts {
  vendor_name?: string | null
  total_hours: number
  file_name: string
}

export interface DocumentInfo {
  id: string
  document_type: 'INVOICE' | 'CONTRACT' | 'TIMESHEET'
  file_name: string
  mime_type?: string | null
  is_demo: boolean
  created_at: string
}

export interface Anomaly {
  id: string
  type: string
  severity: 'low' | 'medium' | 'high'
  title: string
  description: string
  points: number
  evidence: Record<string, unknown>
}

export interface ReviewInfo {
  decision: ReviewDecision
  reason?: string | null
  reviewed_at: string
}

export interface VerificationCheck {
  key: string
  label: string
  status: CheckStatus
  detail: string
}

export interface InvoiceDetail {
  id: string
  invoice_number?: string | null
  vendor_name?: string | null
  invoice_date?: string | null
  due_date?: string | null
  currency?: string | null
  subtotal?: number | null
  tax?: number | null
  total?: number | null
  line_items: LineItem[]
  status: BusinessStatus
  processing_status: ProcessingStatus
  risk_score: number | null
  risk_level: RiskLevel | null
  extraction_coverage: number | null
  verification_checks: VerificationCheck[] | null
  historical: HistoricalStats | null
  explanation: string | null
  explanation_available: boolean
  created_at: string
  updated_at: string
  contract: ContractFacts | null
  timesheet: TimesheetFacts | null
  documents: DocumentInfo[]
  anomalies: Anomaly[]
  review: ReviewInfo | null
}

export interface InvoiceSummary {
  id: string
  invoice_number?: string | null
  vendor_name?: string | null
  invoice_date?: string | null
  currency?: string | null
  total?: number | null
  status: BusinessStatus
  processing_status: ProcessingStatus
  risk_score: number | null
  risk_level: RiskLevel | null
  created_at: string
  has_timesheet: boolean
}

export interface HistoricalStats {
  prior_invoice_count: number
  average_amount: number
  max_amount: number
  min_amount: number
  current_amount: number
  deviation_percent: number
  average_hours: number | null
}

export interface Stats {
  total_processed: number
  pending_review: number
  approved: number
  rejected: number
  high_risk: number
  average_risk_score: number | null
  risk_distribution: Record<RiskLevel, number>
  recent: InvoiceSummary[]
}

export interface UploadResponse {
  invoice_id: string
  status: string
  has_timesheet: boolean
}

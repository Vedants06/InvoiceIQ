import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { analyzeInvoice, getInvoice, submitReview } from '../api/invoices'
import type { ReviewDecision } from '../types/analysis'

export function useInvoiceAnalysis(id: string | undefined) {
  const queryClient = useQueryClient()
  const queryKey = ['invoice', id]

  const invoiceQuery = useQuery({
    queryKey,
    queryFn: () => getInvoice(id!),
    enabled: Boolean(id),
  })

  const analyzeMutation = useMutation({
    mutationFn: () => analyzeInvoice(id!),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data)
      void queryClient.invalidateQueries({ queryKey: ['invoices'] })
      void queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  const reviewMutation = useMutation({
    mutationFn: (vars: { decision: ReviewDecision; reason?: string }) =>
      submitReview(id!, vars.decision, vars.reason),
    onSuccess: (data) => {
      queryClient.setQueryData(queryKey, data)
      void queryClient.invalidateQueries({ queryKey: ['invoices'] })
      void queryClient.invalidateQueries({ queryKey: ['stats'] })
    },
  })

  return {
    invoice: invoiceQuery.data,
    isLoading: invoiceQuery.isLoading,
    loadError: invoiceQuery.error,
    runAnalysis: analyzeMutation.mutate,
    isAnalyzing: analyzeMutation.isPending,
    analyzeError: analyzeMutation.error,
    submitReview: (decision: ReviewDecision, reason?: string) =>
      reviewMutation.mutate({ decision, reason }),
    isReviewing: reviewMutation.isPending,
    reviewError: reviewMutation.error,
  }
}

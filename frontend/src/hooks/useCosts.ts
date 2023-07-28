import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { api } from '../lib/api'

export function useCostSummary(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'summary', params],
    queryFn: () => api.costs.summary(params),
  })
}

export function useDailyCosts(params?: Record<string, string>) {
  return useQuery({
    queryKey: ['costs', 'daily', params],
    queryFn: () => api.costs.daily(params),
  })
}

export function useAccounts() {
  return useQuery({ queryKey: ['accounts'], queryFn: api.costs.accounts })
}

export function useAnomalies(provider?: string) {
  return useQuery({
    queryKey: ['anomalies', provider],
    queryFn: () => api.anomalies.list(provider),
    refetchInterval: 60_000,
  })
}

export function useResolveAnomaly() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.anomalies.resolve,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['anomalies'] }),
  })
}

export function useBudgets() {
  return useQuery({ queryKey: ['budgets'], queryFn: api.budgets.list })
}

export function useCreateBudget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.budgets.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['budgets'] }),
  })
}

export function useDeleteBudget() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.budgets.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['budgets'] }),
  })
}

export function useRecommendations() {
  return useQuery({ queryKey: ['recommendations'], queryFn: api.recommendations.list })
}

export function useDismissRecommendation() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: api.recommendations.dismiss,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
  })
}

export function useTriggerIngestion() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (daysBack: number) => api.ingestion.trigger(daysBack),
    onSuccess: () => {
      setTimeout(() => {
        qc.invalidateQueries({ queryKey: ['costs'] })
        qc.invalidateQueries({ queryKey: ['anomalies'] })
      }, 3000)
    },
  })
}

import type { CostSummaryRow, DailyCostRow, Anomaly, Budget, Recommendation } from '../types'

const BASE = '/api/v1'

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts?.headers },
    ...opts,
  })
  if (!res.ok) throw new Error(`${res.status}: ${await res.text().catch(() => res.statusText)}`)
  if (res.status === 204) return undefined as unknown as T
  return res.json()
}

export const api = {
  costs: {
    summary: (params?: Record<string, string>) =>
      req<CostSummaryRow[]>(`/costs/summary?${new URLSearchParams(params ?? {})}`),
    daily: (params?: Record<string, string>) =>
      req<DailyCostRow[]>(`/costs/daily?${new URLSearchParams(params ?? {})}`),
    accounts: () => req<{ provider: string; account_id: string }[]>('/costs/accounts'),
  },
  anomalies: {
    list: (provider?: string) =>
      req<Anomaly[]>(`/anomalies${provider ? `?provider=${provider}` : ''}`),
    resolve: (id: string) =>
      req<{ status: string }>(`/anomalies/${id}/resolve`, { method: 'POST' }),
    detect: () => req<{ status: string }>('/anomalies/detect', { method: 'POST' }),
  },
  budgets: {
    list: () => req<Budget[]>('/budgets'),
    create: (body: Omit<Budget, 'id' | 'current_spend' | 'burn_pct' | 'created_at'>) =>
      req<{ id: string }>('/budgets', { method: 'POST', body: JSON.stringify(body) }),
    delete: (id: string) => req<void>(`/budgets/${id}`, { method: 'DELETE' }),
  },
  recommendations: {
    list: () => req<Recommendation[]>('/recommendations'),
    dismiss: (id: string) => req<void>(`/recommendations/${id}/dismiss`, { method: 'POST' }),
    refresh: () => req<{ status: string }>('/recommendations/refresh', { method: 'POST' }),
  },
  ingestion: {
    trigger: (daysBack = 1) =>
      req<{ status: string }>(`/ingestion/trigger?days_back=${daysBack}`, { method: 'POST' }),
  },
}

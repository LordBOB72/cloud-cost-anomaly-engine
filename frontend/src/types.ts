export type Provider = 'aws' | 'gcp' | 'azure'

export interface CostSummaryRow {
  provider: Provider
  account_id: string
  service: string
  region: string
  total_cost: number
}

export interface DailyCostRow {
  usage_date: string
  provider: Provider
  total_cost: number
}

export interface Anomaly {
  id: string
  provider: Provider
  account_id: string
  service: string
  region: string
  usage_date: string
  actual_cost: number
  expected_cost: number
  stddev: number
  confidence: number
  resolved: boolean
  detected_at: string
}

export interface Budget {
  id: string
  name: string
  provider: Provider | null
  account_id: string | null
  tag_key: string | null
  tag_value: string | null
  amount_usd: number
  period: 'monthly' | 'quarterly'
  current_spend: number
  burn_pct: number
  created_at: string
}

export interface Recommendation {
  id: string
  provider: Provider
  account_id: string | null
  resource_id: string | null
  category: 'idle' | 'rightsize' | 'reserved_instance'
  description: string
  savings_usd: number | null
  dismissed: boolean
  created_at: string
}

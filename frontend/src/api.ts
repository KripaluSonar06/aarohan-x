const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export type BackendCase = {
  event_id: string
  customer_name: string | null
  merchant_name: string
  amount_inr: number
  recovered_amount_inr: number
  recovery_probability: number | null
  diagnosed_class: string | null
  playbook_action: string | null
  status: string
  attempts: number
  created_at: string
  communications: { channel: 'text' | 'voice'; action: string; status: string; message?: string; transcript?: string; timestamp: string }[]
  customer_phone?: string
  failure_code?: string
  failure_description?: string
  expected_gross_value_inr: number
  channel_cost_inr: number
  net_expected_value_inr: number
  decision_explanation?: string
  ledger: { action: string; detail: Record<string, unknown>; timestamp: string }[]
  ptp?: { promised_date: string | null; count: number; broken: boolean }
  decision_detail?: Record<string, unknown>
}

export type Metrics = {
  total_at_risk_paise: number
  gross_recovered_paise: number
  contact_cost_inr: number
  net_recovered_paise: number
  events_recovered: number
  events_needs_human: number
  natural_baseline_paise: number
  incremental_recovery_paise: number
  incremental_recovery_rate: number
  ptp_promises: number
  broken_ptps: number
}

export type Analytics = {
  funnel: { label: string; value: number }[]
  statuses: Record<string, number>
  actions: { name: string; events: number; recovered_paise: number }[]
  diagnoses: Record<string, number>
  confidence: Record<string, number>
}

export type ExperimentMetrics = {
  total_events: number
  total_at_risk_paise: number
  gross_recovered_paise: number
  net_recovered_paise: number
  contact_cost_inr: number
  events_recovered: number
  events_stopped: number
  events_needs_human: number
}

export type Policy = {
  max_silent_retries: number
  max_customer_contacts: number
  max_ptp_promises: number
  voice_min_amount_paise: number
  high_value_review_paise: number
  quiet_hours_start: number
  quiet_hours_end: number
  stop_words: string[]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) throw new Error(`Recovery API request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export function getCases() {
  return request<BackendCase[]>('/api/cases')
}

export function getMetrics() {
  return request<Metrics>('/api/metrics')
}

export function getAnalytics() {
  return request<Analytics>('/api/analytics')
}

export function getPolicy() {
  return request<Policy>('/api/policy')
}

export function updatePolicy(policy: Partial<Policy>) {
  return request<Policy>('/api/policy', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(policy) })
}

export function runExperiments() {
  return request<Record<string, ExperimentMetrics>>('/api/experiments', { method: 'POST' })
}

export async function verifyCase(eventId: string) {
  return request<BackendCase>(`/api/cases/${eventId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recovered: true, verified_by: 'Kripalu Sonar' }),
  })
}

export async function runBatch() {
  return request('/api/run-batch', { method: 'POST' })
}

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
}

export type Metrics = {
  total_at_risk_paise: number
  gross_recovered_paise: number
  contact_cost_inr: number
  net_recovered_paise: number
  events_recovered: number
  events_needs_human: number
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

const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

export async function verifyCase(eventId: string) {
  const response = await fetch(`${API_BASE}/api/cases/${eventId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ recovered: true, verified_by: 'Kripalu Sonar' }),
  })
  if (!response.ok) throw new Error('Verification could not be saved')
  return response.json()
}

export async function runBatch() {
  const response = await fetch(`${API_BASE}/api/run-batch`, { method: 'POST' })
  if (!response.ok) throw new Error('Recovery API is unavailable')
  return response.json()
}

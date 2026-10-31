const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api'
export async function apiGet(path, token) {
  const res = await fetch(`${API}${path}`, { headers: token ? { Authorization: `Token ${token}` } : {} })
  if (!res.ok) throw new Error(`Request failed (${res.status})`)
  return res.json()
}
export async function apiPost(path, body, token) {
  const res = await fetch(`${API}${path}`, { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { Authorization: `Token ${token}` } : {}) }, body: JSON.stringify(body) })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || `Request failed (${res.status})`)
  return data
}

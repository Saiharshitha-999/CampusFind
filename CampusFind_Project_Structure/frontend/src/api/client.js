// Uvicorn is started on 127.0.0.1 by the documented Windows command. Using
// localhost can resolve to ::1 first on some Windows setups, where nothing is
// listening, and fetch then reports only "Failed to fetch".
export const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1'
export const apiUrl = (path) => `${API_BASE}${path}`
export const assetUrl = (path) => `${new URL(API_BASE).origin}${path}`
export function token() { return localStorage.getItem('campusfind_token') }
export async function request(path, options = {}) {
  const headers = new Headers(options.headers || {})
  const auth = token(); if (auth) headers.set('Authorization', `Bearer ${auth}`)
  if (options.body && !(options.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  const response = await fetch(apiUrl(path), { ...options, headers })
  if (response.status === 401 && auth) {
    clearSession()
    window.dispatchEvent(new Event('campusfind:session-expired'))
  }
  const data = response.status === 204 ? null : await response.json().catch(() => ({}))
  if (!response.ok) throw new Error(data.detail || data.message || `Request failed (${response.status})`)
  return data
}
export function saveSession(data) { localStorage.setItem('campusfind_token', data.access_token); localStorage.setItem('campusfind_user', JSON.stringify(data.user)) }
export function user() { try { return JSON.parse(localStorage.getItem('campusfind_user')) } catch { return null } }
export function clearSession() { localStorage.removeItem('campusfind_token'); localStorage.removeItem('campusfind_user') }

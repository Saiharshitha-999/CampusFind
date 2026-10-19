import { useEffect, useState } from 'react'
import { request, user } from '../../api/client.js'
import { Notice, AuthPrompt } from '../../shared/Feedback.jsx'

export function Notifications() {
  const [rows, setRows] = useState([])
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function load() {
    setBusy(true)
    setError('')
    try { setRows(await request('/notifications')) }
    catch (err) { setError(err.message) }
    finally { setBusy(false) }
  }
  useEffect(() => { if (user()) load() }, [])
  async function mark(id) {
    setError('')
    try { await request(`/notifications/${id}/read`, { method: 'POST' }); await load() }
    catch (err) { setError(err.message) }
  }
  if (!user()) return <AuthPrompt/>
  return <section className="narrow page"><p className="eyebrow">Updates</p><h1 className="page-title">Notifications</h1><p className="muted">Updates about your reports, claims, and handoffs.</p><Notice error={error}/>{busy && !rows.length ? <div className="empty loading-state"><span className="loading-dot"/><p>Loading your updates…</p></div> : rows.length ? rows.map(row => <article className={`notification ${row.read ? 'read' : ''}`} key={row.id}><div><p>{row.message}</p><time>{new Date(row.created_at).toLocaleString()}</time></div>{!row.read && <button className="text-button" disabled={busy} onClick={() => mark(row.id)}>Mark read</button>}</article>) : !error && <div className="empty"><div>✳</div><h2>All caught up.</h2><p>We’ll let you know when there’s an update.</p></div>}</section>
}

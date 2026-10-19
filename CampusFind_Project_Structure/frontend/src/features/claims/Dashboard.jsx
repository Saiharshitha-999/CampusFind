import { useEffect, useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { request, user } from '../../api/client.js'
import { Notice, AuthPrompt } from '../../shared/Feedback.jsx'
import { StatusControl } from '../status/StatusControl.jsx'

export function Dashboard() {
  const location = useLocation()
  const [reports, setReports] = useState([])
  const [claims, setClaims] = useState([])
  const [received, setReceived] = useState([])
  const [error, setError] = useState('')
  async function load() {
    if (!user()) return
    try {
      const [r, c, incoming] = await Promise.all([request('/reports/mine'), request('/claims/mine'), request('/claims/received')])
      setReports(r); setClaims(c); setReceived(incoming); setError('')
    } catch (e) { setError(e.message) }
  }
  useEffect(() => { load() }, [])
  if (!user()) return <AuthPrompt />
  return <section className="page">
    <p className="eyebrow">Your account</p><h1 className="page-title">Hello, {user().display_name}</h1>
    <Notice error={error} success={location.state?.notice} />
    <div className="dashboard-actions"><Link className="button primary" to="/report-lost">Report lost</Link><Link className="button secondary" to="/report-found">Report found</Link><Link className="button secondary" to="/notifications">View notifications</Link></div>
    <h2 className="section-title">Your reports</h2>
    {reports.length ? <div className="table-wrap"><table><thead><tr><th>Item</th><th>Type</th><th>Status</th><th>Submitted</th><th>Update</th></tr></thead><tbody>{reports.map(r => <tr key={r.id}><td><Link to={`/items/${r.id}`}>{r.item_name}</Link></td><td>{r.kind}</td><td><span className="status">{r.status}</span></td><td>{new Date(r.created_at).toLocaleDateString()}</td><td><StatusControl item={r} onChange={load} onError={setError} /></td></tr>)}</tbody></table></div> : <div className="empty small">You have not submitted any reports yet.</div>}
    <h2 className="section-title">Your claims</h2>
    {claims.length ? <div className="table-wrap"><table><thead><tr><th>Found report</th><th>Status</th><th>Submitted</th><th>Decision note</th></tr></thead><tbody>{claims.map(c => <tr key={c.id}><td><Link to={`/items/${c.report_id}`}>Report #{c.report_id}</Link></td><td><span className="status">{c.status}</span></td><td>{new Date(c.created_at).toLocaleDateString()}</td><td>{c.decision_comment || '—'}</td></tr>)}</tbody></table></div> : <div className="empty small">No claims yet.</div>}
    <h2 className="section-title">Claims on your found reports</h2>
    {received.length ? received.map(c => <article className="review-card" key={`received-${c.id}`}><h3>Claim for report #{c.report_id}</h3><p className="muted">Claim status: {c.status}. Administrators review evidence and decide claims.</p></article>) : <div className="empty small">No claims have been submitted on your found reports.</div>}
  </section>
}

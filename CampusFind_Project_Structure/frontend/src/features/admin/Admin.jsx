import { useEffect, useState } from 'react'
import { apiUrl, request, token, user } from '../../api/client.js'
import { AuthPrompt, Notice } from '../../shared/Feedback.jsx'

const tabs = ['reports', 'claims', 'recoveries', 'audit']

export function Admin() {
  const [data, setData] = useState({ reports: [], claims: [], recoveries: [], audit: [] })
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [note, setNote] = useState({})
  const [tab, setTab] = useState('reports')
  async function load() {
    const sections = [
      ['reports', 'Pending reports', '/admin/reports/pending'],
      ['claims', 'Pending claims', '/admin/claims/pending'],
      ['recoveries', 'Recoveries', '/admin/recoveries'],
      ['audit', 'Audit records', '/admin/audit'],
    ]
    const results = await Promise.allSettled(sections.map(([, , path]) => request(path)))
    setData(current => results.reduce((next, result, index) => {
      if (result.status === 'fulfilled') next[sections[index][0]] = result.value
      return next
    }, { ...current }))
    const failures = results.flatMap((result, index) => result.status === 'rejected'
      ? [`${sections[index][1]}: ${result.reason.message}`] : [])
    setError(failures.join(' · '))
  }
  useEffect(() => { load() }, [])

  async function decideReport(id, decision) {
    setError('')
    setMessage('')
    try {
      await request(`/admin/reports/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision, comment: note[id] || '' }) })
      // The report queue contains pending reports only. Remove the decided row
      // immediately so it does not look pending while the other admin panels load.
      setData(current => ({ ...current, reports: current.reports.filter(report => report.id !== id) }))
      setMessage(decision === 'approve' ? 'Report approved and removed from the pending queue.' : 'Report rejected and removed from the pending queue.')
      await load()
    } catch (e) {
      // A connection can be lost after the server commits. Re-read the pending
      // queue to distinguish that case from a decision that did not complete.
      if (e.message === 'Failed to fetch') {
        try {
          const reports = await request('/admin/reports/pending')
          setData(current => ({ ...current, reports }))
          if (!reports.some(report => report.id === id)) {
            setMessage('The decision was recorded; the report is no longer pending.')
            return
          }
        } catch { /* Preserve the original request error for the administrator. */ }
      }
      setError(e.message)
    }
  }
  async function decideClaim(id, decision) {
    try {
      await request(`/claims/${id}/decision`, { method: 'POST', body: JSON.stringify({ decision, comment: note[`c${id}`] || '' }) })
      await load()
    } catch (e) { setError(e.message) }
  }
  async function closeRecovery(id) {
    try { await request(`/items/${id}/close`, { method: 'POST' }); await load() }
    catch (e) { setError(e.message) }
  }
  async function downloadProof(id) {
    try {
      const response = await fetch(apiUrl(`/claims/${id}/proof`), { headers: { Authorization: `Bearer ${token()}` } })
      if (!response.ok) throw new Error('Could not download private claim proof')
      const url = URL.createObjectURL(await response.blob())
      const anchor = document.createElement('a'); anchor.href = url; anchor.download = `claim-${id}-proof`; anchor.click()
      URL.revokeObjectURL(url)
    } catch (e) { setError(e.message) }
  }

  if (!user()) return <AuthPrompt />
  if (user().role !== 'Administrator') return <section className="narrow page"><div className="panel"><h1 className="page-title">Administrator access required</h1><p>This page is available to administrators.</p></div></section>
  return <section className="page">
    <p className="eyebrow">Administration</p><h1 className="page-title">Campus review console</h1>
    <p className="muted">Moderate reports, review private claim evidence, close recoveries, and inspect audit records.</p>
    <div className="dashboard-actions" role="tablist" aria-label="Admin sections">
      {tabs.map(name => <button key={name} role="tab" aria-selected={tab === name} className={`button ${tab === name ? 'primary' : 'secondary'}`} onClick={() => setTab(name)}>{name[0].toUpperCase() + name.slice(1)} ({data[name].length})</button>)}
    </div>
    <Notice error={error} success={message} />
    {tab === 'reports' && (data.reports.length ? data.reports.map(report => <article className="review-card" key={report.id}>
      <div className="review-head"><span className={`badge ${report.kind}`}>{report.kind}</span><span>{report.category} · {report.location}</span></div>
      <h2>{report.item_name}</h2><p>{report.description}</p><p className="muted">Reporter contact: {report.contact_email} · {new Date(report.created_at).toLocaleString()}</p>
      <textarea aria-label="Moderation note" placeholder="Required when rejecting" value={note[report.id] || ''} onChange={e => setNote({ ...note, [report.id]: e.target.value })} />
      <div className="review-actions"><button className="button primary" onClick={() => decideReport(report.id, 'approve')}>Approve report</button><button className="button danger" onClick={() => decideReport(report.id, 'reject')}>Reject report</button></div>
    </article>) : !error && <div className="empty">No reports are waiting for review.</div>)}
    {tab === 'claims' && (data.claims.length ? data.claims.map(claim => <article className="review-card" key={claim.id}>
      <div className="review-head">Claim #{claim.id} · Found report #{claim.report_id}</div><p>Private evidence file attached for administrator review.</p>
      <p className="muted">Submitted {new Date(claim.created_at).toLocaleString()}</p>
      {claim.has_proof_file && <button className="text-button" onClick={() => downloadProof(claim.id)}>Download private proof</button>}
      <textarea aria-label="Claim decision comment" placeholder="Decision comment" value={note[`c${claim.id}`] || ''} onChange={e => setNote({ ...note, [`c${claim.id}`]: e.target.value })} />
      <div className="review-actions"><button className="button primary" onClick={() => decideClaim(claim.id, 'approve')}>Approve claim</button><button className="button danger" onClick={() => decideClaim(claim.id, 'reject')}>Reject claim</button></div>
    </article>) : !error && <div className="empty">No claims are waiting for review.</div>)}
    {tab === 'recoveries' && (data.recoveries.length ? data.recoveries.map(report => <article className="review-card" key={report.id}>
      <div className="review-head">Returned report #{report.id} · {report.kind}</div><h2>{report.item_name}</h2><p>{report.description}</p>
      <button className="button primary" onClick={() => closeRecovery(report.id)}>Close recovery</button>
    </article>) : !error && <div className="empty">No returned recoveries need closure.</div>)}
    {tab === 'audit' && (data.audit.length ? <div className="table-wrap"><table><thead><tr><th>When</th><th>Actor</th><th>Action</th><th>Record</th></tr></thead><tbody>
      {data.audit.map(event => <tr key={event.event_id}><td>{new Date(event.timestamp).toLocaleString()}</td><td>{event.actor_id ?? 'System'}</td><td>{event.action}</td><td>{event.entity_type} #{event.entity_id}</td></tr>)}
    </tbody></table></div> : !error && <div className="empty">No audit events have been recorded.</div>)}
  </section>
}

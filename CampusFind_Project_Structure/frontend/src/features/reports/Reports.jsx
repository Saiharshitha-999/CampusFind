import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { request, user, assetUrl } from '../../api/client.js'
import { Notice, AuthPrompt } from '../../shared/Feedback.jsx'
import { ClaimForm } from '../claims/ClaimForm.jsx'
import { Matches } from '../matching/Matches.jsx'

export function ReportForm({kind}) {
  const [error,setError]=useState(''); const [busy,setBusy]=useState(false); const nav=useNavigate()
  async function submit(e) {
    e.preventDefault(); setError(''); setBusy(true)
    const f=new FormData(e.currentTarget); const body=new FormData()
    const files=f.getAll('images').filter(file=>file.size)
    if(files.length>5 || files.some(file=>file.size>5*1024*1024)){setError('Choose up to five photos, each no larger than 5 MB.');setBusy(false);return}
    for(const key of ['item_name','category','description','occurred_at','location','custody_location'])if(f.get(key))body.append(key,f.get(key))
    for(const file of files)body.append('images',file)
    try { await request(`/reports/${kind}`,{method:'POST',body}); nav('/dashboard',{state:{notice:'Your report was submitted and is waiting for moderator review.'}}) }
    catch(err) { setError(err.message) } finally { setBusy(false) }
  }
  if(!user())return <AuthPrompt/>
  return <section className="narrow page"><div className="panel"><p className="eyebrow">Share a report</p><h1 className="page-title">Report a {kind} item</h1><p className="muted">A moderator reviews reports before they appear in public search. Contact uses your private verified account email.</p><Notice error={error}/><form className="form" onSubmit={submit}><div className="form-grid"><label>Item name<input name="item_name" required maxLength="120" placeholder="Blue water bottle"/></label><label>Category<input name="category" required maxLength="80" placeholder="Bottle, electronics, ID…"/></label></div><label>Description<textarea name="description" required maxLength="3000" rows="4" placeholder="Describe identifying details. Keep one unique detail for claim verification."/></label><div className="form-grid"><label>{kind==='lost'?'When did you lose it?':'When did you find it?'}<input type="datetime-local" name="occurred_at" required/></label><label>{kind==='found'?'Where was it found?':'Where was it last seen?'}<input name="location" required maxLength="200"/></label></div>{kind==='found'&&<label>Current custody location<input name="custody_location" required maxLength="200" placeholder="For example, Student Union front desk"/></label>}<label>Photos (up to 5, JPEG/PNG/WebP)<input type="file" name="images" accept="image/jpeg,image/png,image/webp" multiple/></label><p className="field-hint">Use clear photos under 5 MB each. Contact details and claim proof are never shown in public search.</p><button className="button primary" disabled={busy}>{busy?'Submitting…':'Submit for review'}</button></form></div></section>
}

export function ItemDetail() {
  const { id } = useParams()
  const [item, setItem] = useState(null)
  const [matches, setMatches] = useState([])
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const me = user()
  useEffect(() => {
    let active = true
    setItem(null); setMatches([]); setHistory([]); setError(''); setLoading(true)
    request(`/items/${id}`).then(data => { if (active) setItem(data) })
      .catch(err => { if (active) setError(err.message) })
      .finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [id])
  useEffect(() => {
    let active = true
    if (item && me && (me.id === item.owner_id || me.role === 'Administrator')) {
      request(`/items/${id}/history`).then(data => { if (active) setHistory(data) }).catch(() => {})
      if (me.id === item.owner_id) request(`/items/${id}/matches`).then(data => { if (active) setMatches(data) }).catch(() => {})
    }
    return () => { active = false }
  }, [id, item])
  return <section className="page">
    {loading && <div className="empty loading-state"><span className="loading-dot"/><p>Loading report…</p></div>}
    {error && !item && <div className="empty"><p className="eyebrow">Report unavailable</p><h1 className="page-title">We couldn’t open this report.</h1><p>{error}</p><Link className="button secondary" to="/items">Back to reports</Link></div>}
    {item && <>
      <Link to="/items" className="back-link">← All reports</Link>
      <div className="detail-layout"><div className="detail-image">{item.images?.[0] ? <img src={assetUrl(item.images[0])} alt={item.item_name}/> : <span aria-hidden="true">✳</span>}</div>
        <div className="detail-copy"><div className="detail-badges"><span className={`badge ${item.kind}`}>{item.kind}</span>{item.status !== 'Active' && <span className="status">{item.status}</span>}</div>
          <p className="category">{item.category}</p><h1 className="page-title">{item.item_name}</h1><p>{item.description}</p>
          <dl><dt>{item.kind === 'found' ? 'Found at' : 'Last seen'}</dt><dd>{item.location}</dd><dt>Date</dt><dd>{new Date(item.occurred_at).toLocaleString()}</dd>{item.custody_location && <><dt>Current custody</dt><dd>{item.custody_location}</dd></>}</dl>
          {item.kind === 'found' && item.status === 'Match Found' && (!me || me.id !== item.owner_id) && <ClaimForm itemId={id}/>}
        </div>
      </div>
      {me && me.id === item.owner_id && <Matches items={matches}/>}
      {me && (me.id === item.owner_id || me.role === 'Administrator') && <section className="matches"><p className="eyebrow">Report timeline</p><h2>Status history</h2>{history.length ? <ol>{history.map((entry, index) => <li key={`${entry.changed_at}-${index}`}><strong>{entry.new_status}</strong><span className="muted">{entry.old_status ? ` from ${entry.old_status}` : ' created'} · {new Date(entry.changed_at).toLocaleString()}</span></li>)}</ol> : <p className="muted">No status changes have been recorded yet.</p>}</section>}
    </>}
  </section>
}

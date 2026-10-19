import { useState } from 'react'
import { Link } from 'react-router-dom'
import { request, user } from '../../api/client.js'
import { Notice } from '../../shared/Feedback.jsx'

export function ClaimForm({ itemId }) {
  const [proofFile, setProofFile] = useState(null)
  const [complete, setComplete] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setBusy(true)
    try {
      if (!proofFile) throw new Error('Attach a proof file before submitting your claim.')
      const form = new FormData()
      form.append('file', proofFile)
      const claim = await request(`/items/${itemId}/claims`, { method: 'POST', body: form })
      setProofFile(null)
      setComplete(true)
      setMessage(`Claim #${claim.id} submitted with private proof. Track it from your dashboard.`)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return <div className="claim-box"><p className="eyebrow">Ownership claim</p><h2>Is this yours?</h2><p>Attach a document or image that supports your ownership. An administrator will review your claim.</p><Notice error={error} success={message}/>{user() ? complete ? <Link className="button secondary" to="/dashboard">View your claim →</Link> : <>
    <form onSubmit={submit} className="form">
      <label>Proof file (JPEG, PNG, WebP, or PDF; up to 5 MB)<input type="file" accept="image/jpeg,image/png,image/webp,application/pdf" required onChange={event => setProofFile(event.target.files?.[0] || null)} /></label>
      <button className="button primary" disabled={busy}>{busy ? 'Submitting…' : 'Submit a claim'}</button>
    </form>
  </> : <Link className="button primary" to="/login">Sign in to claim</Link>}</div>
}

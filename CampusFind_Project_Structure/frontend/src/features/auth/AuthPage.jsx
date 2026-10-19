import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { request, saveSession } from '../../api/client.js'
import { Notice } from '../../shared/Feedback.jsx'

export function AuthPage({ mode }) {
  const nav = useNavigate()
  const query = new URLSearchParams(window.location.search)
  const linkToken = query.get('token') || ''
  const initialEmail = query.get('email') || ''
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [needsVerification, setNeedsVerification] = useState(false)
  const [attemptedEmail, setAttemptedEmail] = useState('')
  const [loginEmail, setLoginEmail] = useState('')

  useEffect(() => {
    if (mode !== 'verify' || !linkToken) return
    window.history.replaceState(window.history.state, '', window.location.pathname)
    setBusy(true)
    request('/auth/verify-email', { method: 'POST', body: JSON.stringify({ token: linkToken }) })
      .then((data) => setMessage(data.message))
      .catch((err) => setError(err.message))
      .finally(() => setBusy(false))
  }, [mode, linkToken])

  useEffect(() => {
    if (mode === 'confirm' && linkToken) window.history.replaceState(window.history.state, '', window.location.pathname)
  }, [mode, linkToken])

  async function submit(event) {
    event.preventDefault()
    setBusy(true)
    setError('')
    setMessage('')
    setNeedsVerification(false)
    const form = new FormData(event.currentTarget)
    if (mode === 'login') setAttemptedEmail(String(form.get('email') || ''))
    try {
      if (mode === 'register') {
        const data = await request('/auth/register', { method: 'POST', body: JSON.stringify({ email: form.get('email'), password: form.get('password'), display_name: form.get('name') }) })
        setMessage(data.message)
      } else if (mode === 'login') {
        const data = await request('/auth/login', { method: 'POST', body: JSON.stringify({ email: form.get('email'), password: form.get('password') }) })
        saveSession(data)
        nav('/dashboard')
      } else if (mode === 'verify') {
        const data = await request('/auth/verification/request', { method: 'POST', body: JSON.stringify({ email: form.get('email') }) })
        setMessage(data.message)
      } else if (mode === 'reset') {
        const data = await request('/auth/password-reset/request', { method: 'POST', body: JSON.stringify({ email: form.get('email') }) })
        setMessage(data.message)
      } else {
        const data = await request('/auth/password-reset/confirm', { method: 'POST', body: JSON.stringify({ token: form.get('token'), password: form.get('password') }) })
        setMessage(data.message)
      }
    } catch (err) {
      setError(err.message)
      if (mode === 'login' && err.message.toLowerCase().includes('verify your email')) setNeedsVerification(true)
    } finally {
      setBusy(false)
    }
  }

  const title = { register: 'Create your account', login: 'Welcome back', verify: 'Verify your email', reset: 'Reset your password', confirm: 'Choose a new password' }[mode]
  const showTokenInput = mode === 'confirm' && !!linkToken

  return <section className="narrow page"><div className="panel">
    <p className="eyebrow">CampusFind account</p><h1 className="page-title">{title}</h1>
    {mode === 'verify' && !linkToken && <p className="muted">Already signed up? Enter your email and we’ll send a fresh verification link.</p>}
    <Notice error={error} success={message || (mode === 'verify' && linkToken && busy ? 'Verifying your email…' : '')} />
    {!(mode === 'register' && message) && !(mode === 'confirm' && !linkToken) && <form className="form" onSubmit={submit}>
      {['register', 'login', 'reset'].includes(mode) || (mode === 'verify' && !linkToken) ? <label>Email address<input name="email" type="email" required autoComplete="email" defaultValue={mode === 'verify' ? initialEmail : undefined} onChange={mode === 'login' ? event => setLoginEmail(event.target.value) : undefined} /></label> : null}
      {mode === 'register' && <label>Display name<input name="name" required maxLength="100" autoComplete="name" /></label>}
      {['register', 'login', 'confirm'].includes(mode) && <label>Password<input name="password" type="password" minLength="8" required autoComplete={mode === 'login' ? 'current-password' : 'new-password'} /></label>}
      {showTokenInput && <input type="hidden" name="token" value={linkToken} readOnly />}
      {mode === 'confirm' && !linkToken ? <p className="muted">Open the password reset link from your email, or request a new one below.</p> : mode !== 'verify' || !linkToken ? <button className="button primary" disabled={busy}>{busy ? 'Working…' : mode === 'login' ? 'Sign in' : mode === 'register' ? 'Create account' : mode === 'verify' ? 'Send verification link' : mode === 'reset' ? 'Send reset link' : 'Update password'}</button> : null}
    </form>}
    {needsVerification && <Link className="button secondary verification-cta" to={`/verify-email?email=${encodeURIComponent(attemptedEmail)}`}>Resend verification link →</Link>}
    <div className="form-links">
      {mode === 'login' ? <><Link to="/register">Create account</Link><Link to="/password-reset">Forgot password?</Link><Link to={`/verify-email?email=${encodeURIComponent(attemptedEmail || loginEmail)}`}>Resend verification email</Link></> : mode === 'register' ? message ? <Link to="/verify-email">Resend verification email</Link> : <Link to="/login">Already registered? Sign in</Link> : mode === 'reset' ? <Link to="/login">Return to sign in</Link> : mode === 'confirm' && !linkToken ? <Link to="/password-reset">Request a reset link</Link> : mode === 'verify' && !linkToken ? <Link to="/register">Back to sign up</Link> : <Link to="/login">Return to sign in</Link>}
      {mode === 'verify' && linkToken && !message && !error ? <span className="muted">Verifying your email…</span> : null}
    </div>
  </div></section>
}

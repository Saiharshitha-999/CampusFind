import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { user, clearSession } from './api/client.js'
import { Home } from './pages/HomePage.jsx'
import { AuthPage } from './features/auth/AuthPage.jsx'
import { ReportForm, ItemDetail } from './features/reports/Reports.jsx'
import { SearchPage } from './features/search/SearchPage.jsx'
import { Dashboard } from './features/claims/Dashboard.jsx'
import { Notifications } from './features/notifications/Notifications.jsx'
import { Admin } from './features/admin/Admin.jsx'
import './styles/app.css'

function Frame({ children }) {
  const [me, setMe] = useState(user())
  const location = useLocation()
  const navigate = useNavigate()
  useEffect(() => setMe(user()), [location.pathname])
  useEffect(() => {
    const syncSession = () => setMe(user())
    window.addEventListener('campusfind:session-expired', syncSession)
    return () => window.removeEventListener('campusfind:session-expired', syncSession)
  }, [])
  function signOut() {
    clearSession()
    setMe(null)
    navigate('/')
  }
  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Skip to content</a>
    <header className="site-header">
      <Link className="brand" to="/" aria-label="CampusFind home">Campus<span>Find</span><i aria-hidden="true">•</i></Link>
      <nav aria-label="Main navigation">
        <NavLink to="/items">Find items</NavLink>
        <NavLink to="/report-lost">Report lost</NavLink>
        <NavLink to="/report-found">Report found</NavLink>
        {me ? <>
          <NavLink to="/dashboard">My account</NavLink>
          <NavLink to="/notifications">Alerts</NavLink>
          {me.role === 'Administrator' && <NavLink to="/admin">Admin</NavLink>}
          <button className="link-button sign-out" onClick={signOut}>Sign out</button>
        </> : <><NavLink to="/login">Sign in</NavLink><Link className="nav-join" to="/register">Join CampusFind</Link></>}
      </nav>
    </header>
    <main id="main-content">{children}</main>
    <footer><span className="footer-brand">CampusFind</span><span>·</span> A safer way to reunite campus items <span className="footer-note">Built for the campus community</span></footer>
  </div>
}

function Missing() {
  return <section className="narrow page"><div className="panel"><p className="eyebrow">404 · Lost in the halls?</p><h1 className="page-title">We couldn’t find that page.</h1><p className="muted">The address may have changed. Head back and keep searching.</p><Link className="button primary" to="/">Back to CampusFind</Link></div></section>
}

export default function App() {
  return <Frame><Routes>
    <Route path="/" element={<Home/>}/>
    <Route path="/items" element={<SearchPage/>}/>
    <Route path="/items/:id" element={<ItemDetail/>}/>
    <Route path="/register" element={<AuthPage mode="register"/>}/>
    <Route path="/login" element={<AuthPage mode="login"/>}/>
    <Route path="/verify-email" element={<AuthPage mode="verify"/>}/>
    <Route path="/password-reset" element={<AuthPage mode="reset"/>}/>
    <Route path="/password-reset/confirm" element={<AuthPage mode="confirm"/>}/>
    <Route path="/report-lost" element={<ReportForm kind="lost"/>}/>
    <Route path="/report-found" element={<ReportForm kind="found"/>}/>
    <Route path="/dashboard" element={<Dashboard/>}/>
    <Route path="/notifications" element={<Notifications/>}/>
    <Route path="/admin" element={<Admin/>}/>
    <Route path="*" element={<Missing/>}/>
  </Routes></Frame>
}

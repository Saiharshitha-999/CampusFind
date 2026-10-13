import { Link, Route, Routes } from 'react-router-dom'
import HomePage from './pages/HomePage.jsx'
import './styles/app.css'
export default function App() {
  return <div className="app-shell">
    <header className="site-header">
      <Link className="brand" to="/">CampusFind</Link>
      <nav aria-label="Main navigation">
        <Link to="/items">Search items</Link><Link to="/report-lost">Report lost</Link>
        <Link to="/report-found">Report found</Link><Link to="/login">Login</Link>
      </nav>
    </header>
    <main><Routes><Route path="/" element={<HomePage />} /><Route path="*" element={<section className="page"><h1>Page under development</h1><p>Implement this page in your assigned feature folder.</p></section>} /></Routes></main>
    <footer>CampusFind · Smart Lost-and-Found Recovery</footer>
  </div>
}

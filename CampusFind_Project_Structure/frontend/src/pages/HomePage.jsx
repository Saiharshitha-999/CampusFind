import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { apiUrl, assetUrl } from '../api/client.js'

const steps = [
  { number: '01', title: 'Search the board', copy: 'Browse reviewed lost and found reports from around campus.' },
  { number: '02', title: 'Share what happened', copy: 'Add useful details and a photo so the community can help.' },
  { number: '03', title: 'Verify it privately', copy: 'Prove ownership with a private detail, then arrange a safe handoff.' },
]

export function Home() {
  const [reports, setReports] = useState([])
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  useEffect(() => {
    fetch(apiUrl('/items?limit=3'))
      .then((response) => response.ok ? response.json() : Promise.reject())
      .then((data) => setReports(data.items || []))
      .catch(() => setReports([]))
  }, [])
  function search(event) {
    event.preventDefault()
    navigate(`/items${query.trim() ? `?q=${encodeURIComponent(query.trim())}` : ''}`)
  }

  return <>
    <section className="home-hero">
      <div className="hero page">
        <div className="hero-copy">
          <p className="eyebrow"><span className="eyebrow-dot"/> The campus lost & found</p>
          <h1>Lost something?<br/><em>Let’s bring it back.</em></h1>
          <p className="hero-intro">A thoughtful place to report lost items, find what’s been turned in, and get it back into the right hands.</p>
          <form className="hero-search" onSubmit={search} role="search">
            <span aria-hidden="true">⌕</span>
            <input aria-label="Search lost and found reports" placeholder="Try “blue water bottle”…" value={query} onChange={(event) => setQuery(event.target.value)}/>
            <button className="button primary">Search reports <span aria-hidden="true">→</span></button>
          </form>
          <div className="hero-actions"><Link className="text-link" to="/report-lost">I lost something <span>↗</span></Link><Link className="text-link" to="/report-found">I found something <span>↗</span></Link></div>
          <div className="hero-assurance"><span>✓ Reports are reviewed</span><span>✓ Claim details stay private</span></div>
        </div>
        <div className="hero-art" aria-label="CampusFind helps reunite found items with their owners">
          <div className="art-orbit orbit-one"/><div className="art-orbit orbit-two"/>
          <div className="art-center"><span aria-hidden="true">✳</span><strong>Found<br/>your way<br/>back.</strong></div>
          <div className="art-note note-top"><span className="note-icon book">▤</span><span><strong>Found on campus</strong><small>Ready for its owner</small></span><b>↗</b></div>
          <div className="art-note note-bottom"><span className="note-icon heart">♥</span><span><strong>Private by design</strong><small>Safe claim verification</small></span><b>✓</b></div>
          <span className="art-spark spark-a">✳</span><span className="art-spark spark-b">✦</span>
        </div>
      </div>
      <div className="hero-bottom"><span>MADE FOR THE MOMENTS THAT MATTER</span><span className="hero-bottom-line"/><span>SEARCH · REPORT · REUNITE</span></div>
    </section>

    <section className="page home-section latest-section">
      <div className="section-heading"><div><p className="eyebrow">The community board</p><h2 className="section-title">Recently reported</h2><p className="muted">Fresh finds and reports, reviewed before they’re shared.</p></div><Link className="text-link" to="/items">Explore all reports <span>→</span></Link></div>
      {reports.length ? <div className="cards home-cards">{reports.map((item) => <Link className="item-card" to={`/items/${item.id}`} key={item.id}>
        <div className="item-photo">{item.images?.[0] ? <img src={assetUrl(item.images[0])} alt={item.item_name}/> : <span aria-hidden="true">✳</span>}<span className={`badge ${item.kind}`}>{item.kind}</span></div>
        <div className="item-body"><p className="category">{item.category}</p><h3>{item.item_name}</h3><p>{item.location}</p><div className="card-bottom"><span>{new Date(item.occurred_at).toLocaleDateString()}</span><span>View report →</span></div></div>
      </Link>)}</div> : <div className="latest-empty"><span className="latest-empty-mark">✳</span><div><strong>Your next find starts here.</strong><p>New Active campus reports will show up in this space.</p></div><Link className="text-link" to="/items">Browse reports <span>→</span></Link></div>}
    </section>

    <section className="how-section"><div className="page"><div className="section-heading"><div><p className="eyebrow">A little help goes a long way</p><h2 className="section-title">From lost to found.</h2></div><p className="muted how-lede">A clear, considerate process makes returning an item easier for everyone.</p></div><div className="steps-grid">{steps.map((step) => <article className="step-card" key={step.number}><span>{step.number}</span><h3>{step.title}</h3><p>{step.copy}</p></article>)}</div></div></section>
    <section className="closing-cta page"><div><p className="eyebrow">Small action. Big relief.</p><h2>Help something find<br/>its way home.</h2></div><div className="closing-actions"><Link className="button primary" to="/report-found">Report a found item <span>→</span></Link><Link className="button secondary" to="/items">Search reports</Link></div></section>
  </>
}

import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { request, assetUrl } from '../../api/client.js'
import { Notice } from '../../shared/Feedback.jsx'

const PAGE_SIZE = 12

export function ItemCard({ item }) {
  const date = new Date(item.occurred_at)
  return <Link className="item-card" to={`/items/${item.id}`}>
    <div className="item-photo">{item.images?.[0] ? <img src={assetUrl(item.images[0])} alt={item.item_name}/> : <span aria-hidden="true">✳</span>}<span className={`badge ${item.kind}`}>{item.kind}</span></div>
    <div className="item-body"><p className="category">{item.category}</p><h2>{item.item_name}</h2><p>{item.location}</p><div className="card-bottom"><span>{Number.isNaN(date.getTime()) ? 'Date unavailable' : date.toLocaleDateString()}</span><span>View details →</span></div></div>
  </Link>
}

export function SearchPage() {
  const [urlParams] = useSearchParams()
  const [data, setData] = useState({ items: [], total: 0, pages: 0 })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const [page, setPage] = useState(1)
  const [params, setParams] = useState(() => ({ q: urlParams.get('q') || '', kind: urlParams.get('kind') || '', category: urlParams.get('category') || '', location: urlParams.get('location') || '', sort: urlParams.get('sort') || 'newest' }))

  async function load(filters = params, pageNumber = 1) {
    setBusy(true)
    setError('')
    try {
      const query = new URLSearchParams({ ...filters, page: String(pageNumber), limit: String(PAGE_SIZE) })
      setData(await request(`/items?${query}`))
      setPage(pageNumber)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }
  useEffect(() => { load(params, 1) }, []) // Fetch the filters supplied by home page links.
  function submit(event) { event.preventDefault(); load(params, 1) }
  function clear() {
    const empty = { q: '', kind: '', category: '', location: '', sort: 'newest' }
    setParams(empty)
    load(empty, 1)
  }

  return <section className="page search-page">
    <div className="page-heading"><div><p className="eyebrow">The campus board</p><h1 className="page-title">Find an item.</h1><p className="muted">Search active campus reports. Contact information and claim evidence stay private.</p></div><Link className="button primary" to="/report-lost">Create a report <span>→</span></Link></div>
    <form className="filters" onSubmit={submit} role="search">
      <input aria-label="Search terms" placeholder="Item name or description" value={params.q} onChange={event => setParams({ ...params, q: event.target.value })}/>
      <input aria-label="Category" placeholder="Category" value={params.category} onChange={event => setParams({ ...params, category: event.target.value })}/>
      <input aria-label="Location" placeholder="Location" value={params.location} onChange={event => setParams({ ...params, location: event.target.value })}/>
      <select aria-label="Report type" value={params.kind} onChange={event => setParams({ ...params, kind: event.target.value })}><option value="">Lost and found</option><option value="found">Found</option><option value="lost">Lost</option></select>
      <select aria-label="Sort reports" value={params.sort} onChange={event => setParams({ ...params, sort: event.target.value })}><option value="newest">Newest</option><option value="oldest">Oldest</option><option value="name">Name A–Z</option></select>
      <button className="button primary" disabled={busy}>{busy ? 'Searching…' : 'Search'}</button>
    </form>
    <Notice error={error}/>
    {busy && !data.items.length ? <div className="empty loading-state"><span className="loading-dot"/><p>Looking through campus reports…</p></div> : data.items.length ? <>
      <div className="results-meta"><p className="result-count">{data.total} report{data.total === 1 ? '' : 's'}</p>{Object.values(params).some(Boolean) && <button className="text-button" type="button" onClick={clear}>Clear filters</button>}</div>
      <div className="cards">{data.items.map(item => <ItemCard key={item.id} item={item}/>)}</div>
      {data.pages > 1 && <div className="pagination"><button className="button secondary" disabled={busy || page <= 1} onClick={() => load(params, page - 1)}>← Previous</button><span>Page {page} of {data.pages}</span><button className="button secondary" disabled={busy || page >= data.pages} onClick={() => load(params, page + 1)}>Next →</button></div>}
    </> : !error && <div className="empty"><div>⌕</div><h2>No reports found</h2><p>{Object.values(params).some(Boolean) ? 'Try broadening your search, or clear the filters to see all reports.' : 'New reports will appear after administrator approval.'}</p>{Object.values(params).some(Boolean) && <button className="button secondary" onClick={clear}>Clear filters</button>}</div>}
  </section>
}

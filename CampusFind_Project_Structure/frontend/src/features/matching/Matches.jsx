import { Link } from 'react-router-dom'

export function Matches({items=[]}) {
  if(!items.length)return null
  return <section className="matches"><p className="eyebrow">Possible matches</p><h2>Suggested reports</h2><p className="muted">Suggestions are not proof of ownership.</p><div className="cards">{items.map(m=><Link key={m.item.id} to={`/items/${m.item.id}`} className="match-card"><span className={`confidence ${m.confidence.toLowerCase()}`}>{m.confidence} match · {m.score}%</span><h3>{m.item.item_name}</h3><p>{m.item.category} · {m.item.location}</p></Link>)}</div></section>
}

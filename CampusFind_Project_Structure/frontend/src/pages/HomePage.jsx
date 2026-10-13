export default function HomePage() {
  return <section className="hero page">
    <p className="eyebrow">Campus lost and found</p>
    <h1>Lost something? Let's help it find its way home.</h1>
    <p>Report missing items, share found items, and review possible matches in one campus space.</p>
    <div className="hero-actions"><a className="button primary" href="/report-lost">Report a lost item</a><a className="button secondary" href="/items">Search reports</a></div>
    <p className="notice">Starter UI only — connect actions to the implemented API before release.</p>
  </section>
}

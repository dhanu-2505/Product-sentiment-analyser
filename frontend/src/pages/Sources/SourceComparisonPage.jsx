import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { getProduct, getProductSources } from '../../services/api'

const formatPrice = (price, currency) => {
  if (price === null || price === undefined) return 'Unavailable'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency || 'INR',
    maximumFractionDigits: 2,
  }).format(price)
}

function SourceComparisonPage() {
  const { productId } = useParams()
  const [product, setProduct] = useState(null)
  const [sources, setSources] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    let active = true
    Promise.all([getProduct(productId), getProductSources(productId)])
      .then(([productResponse, sourceResponse]) => {
        if (!active) return
        setProduct(productResponse.data)
        setSources(sourceResponse.data.items || [])
      })
      .catch((requestError) => {
        if (active) setError(requestError?.response?.data?.detail || 'Unable to load source comparison.')
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => { active = false }
  }, [productId])

  const observations = useMemo(
    () => sources.filter((source) => source.price !== null || source.rating !== null || source.review_count !== null),
    [sources],
  )
  const prices = observations.map((source) => source.price).filter((price) => price !== null)
  const lowestPrice = prices.length ? Math.min(...prices) : null
  const highestPrice = prices.length ? Math.max(...prices) : null

  if (loading) return <main className="page"><div className="loading-grid"><div className="skeleton-line large" /><div className="skeleton-card large" /></div></main>
  if (error) return <main className="page"><div className="error-state"><h2>Source comparison unavailable</h2><p>{error}</p></div></main>

  return (
    <main className="page">
      <header className="section-header">
        <div>
          <p className="eyebrow muted">Cross-platform intelligence</p>
          <h2>{product?.name} source comparison</h2>
          <p>Only recorded observations are shown. Unsupported live checks remain unavailable.</p>
        </div>
        <Link className="ghost-button" to={`/dashboard/${productId}`}>Product analytics</Link>
      </header>

      <section className="kpi-grid">
        <div className="kpi-card"><span className="label">Sources with observations</span><strong>{observations.length}</strong></div>
        <div className="kpi-card"><span className="label">Lowest observed price</span><strong>{lowestPrice === null ? 'Unavailable' : formatPrice(lowestPrice)}</strong></div>
        <div className="kpi-card"><span className="label">Highest observed price</span><strong>{highestPrice === null ? 'Unavailable' : formatPrice(highestPrice)}</strong></div>
        <div className="kpi-card"><span className="label">Price history</span><strong>Insufficient historical price data.</strong></div>
      </section>

      <section className="table-panel">
        <div className="section-header">
          <div><p className="eyebrow muted">20 supported retailers</p><h3>Source status and observations</h3></div>
        </div>
        <div className="table-wrap">
          <table className="data-table">
            <thead><tr><th>Source</th><th>Status</th><th>Price</th><th>Rating</th><th>Reviews</th><th>Availability</th><th>Last checked</th></tr></thead>
            <tbody>
              {sources.map((source) => (
                <tr key={source.source}>
                  <td>{source.source_name}</td>
                  <td><span className={`badge provenance-${source.status === 'live' ? 'live' : source.status === 'seeded_demo' ? 'demo' : 'unknown'}`}>
                    {source.status === 'live' ? 'Live' : source.status === 'seeded_demo' ? 'Seeded demo' : source.status === 'stored' ? 'Stored' : 'Unavailable'}
                  </span></td>
                  <td>{formatPrice(source.price, source.currency)}</td>
                  <td>{source.rating ?? 'Unavailable'}</td>
                  <td>{source.review_count ?? 'Unavailable'}</td>
                  <td>{source.availability === null ? 'Unavailable' : source.availability ? 'Available' : 'Unavailable'}</td>
                  <td>{source.last_checked_at ? new Date(source.last_checked_at).toLocaleString() : 'Not checked'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {observations.length === 0 && <p className="empty-state">Live data unavailable for these sources. No stored observations are available for this product.</p>}
      </section>
    </main>
  )
}

export default SourceComparisonPage

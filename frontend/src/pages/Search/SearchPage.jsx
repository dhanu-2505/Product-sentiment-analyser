import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ArrowRight, Search as SearchIcon } from 'lucide-react'

import { getSources, searchProduct } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'
import SourceSelector from '../../components/SourceSelector'
import StoreComparison from '../../components/StoreComparison'

const STORAGE_KEY = 'recent-product-searches'

function SearchPage() {
  const navigate = useNavigate()
  const { token } = useAuth()
  const [query, setQuery] = useState('')
  const [platform, setPlatform] = useState('amazon')
  const [sources, setSources] = useState([])
  const [sourcesLoading, setSourcesLoading] = useState(true)
  const [sourcesError, setSourcesError] = useState('')
  const [sourceEvidence, setSourceEvidence] = useState({})
  const [comparisonCategory, setComparisonCategory] = useState('')
  const [comparisonRun, setComparisonRun] = useState(null)
  const [comparisonRunId, setComparisonRunId] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [recentSearches, setRecentSearches] = useState([])
  const [preview, setPreview] = useState(null)

  useEffect(() => {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      try {
        setRecentSearches(JSON.parse(saved))
      } catch {
        setRecentSearches([])
      }
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    getSources()
      .then((response) => {
        if (!cancelled) setSources(response.data.items || [])
      })
      .catch((requestError) => {
        if (!cancelled) setSourcesError(requestError?.response?.data?.detail || 'Unable to load configured retailers.')
      })
      .finally(() => {
        if (!cancelled) setSourcesLoading(false)
      })
    return () => { cancelled = true }
  }, [])

  const selectedSource = sources.find((source) => source.code === platform)

  const saveRecentSearch = (productName, sourceCode) => {
    const nextSearches = [
      { name: productName, platform: sourceCode },
      ...recentSearches.filter((item) => `${item.name}:${item.platform}` !== `${productName}:${sourceCode}`),
    ].slice(0, 5)
    localStorage.setItem(STORAGE_KEY, JSON.stringify(nextSearches))
    setRecentSearches(nextSearches)
  }

  const handleAnalyze = async (event) => {
    event.preventDefault()
    if (!query.trim()) {
      setError('Please enter a product name to analyze.')
      return
    }

    setLoading(true)
    setError('')

    try {
      if (platform === 'all') {
        setError('Choose a retailer to analyze, or use Compare Across Stores to inspect recorded evidence.')
        return
      }

      const response = await searchProduct({ query, source: platform }, token)
      const product = response.data.product
      saveRecentSearch(product.name, platform)
      setPreview({ ...response.data.summary, data_type: product.source_data_type || product.data_type })
      navigate(`/dashboard/${product.id}?source=${encodeURIComponent(platform)}`)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Unable to analyze this product right now.')
    } finally {
      setLoading(false)
    }
  }

  const handleCompare = () => {
    if (!query.trim()) {
      setError('Enter a product name to compare recorded retailer evidence.')
      return
    }
    if (!sources.length) {
      setError(sourcesError || 'The retailer registry is unavailable, so a comparison cannot be made.')
      return
    }
    setError('')
    setSourceEvidence({})
    setComparisonRunId((current) => current + 1)
    setComparisonRun(query.trim())
  }

  const reviewEvidenceAvailable = Number(preview?.total_reviews || 0) > 0
  const provenance = preview?.data_type === 'live_scraped'
    ? 'live'
    : preview?.data_type === 'seeded_demo'
      ? 'seeded_demo'
      : preview?.data_type === 'stored'
        ? 'stored'
        : 'unavailable'

  return (
    <div className="page">
      <div className="search-layout">
        <section className="search-panel">
          <p className="eyebrow muted">Search product</p>
          <h2>Compare this product across multiple stores.</h2>
          <p className="muted">Search stored product matches and retailer observations. Choose All Sources to include every configured retailer.</p>

          <form onSubmit={handleAnalyze}>
            <div className="search-input-row">
              <input
                className="field"
                type="text"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search product..."
                aria-label="Search product"
              />

              <SourceSelector sources={sources} value={platform} onChange={setPlatform} category={comparisonCategory} loading={sourcesLoading} sourceEvidence={sourceEvidence} />

              <div className="search-actions">
                <button className="primary-button" type="submit" disabled={loading || sourcesLoading || platform === 'all'} title={platform === 'all' ? 'Choose a retailer to analyze' : undefined}>
                  <SearchIcon size={16} />
                  {loading ? 'Analyzing...' : 'Analyze'}
                </button>
                <button className="ghost-button" type="button" onClick={handleCompare} disabled={sourcesLoading || !sources.length}>
                  {platform === 'all' ? 'Compare Across Stores' : `Compare ${selectedSource?.name || 'Store'}`}
                </button>
              </div>
            </div>
          </form>

          {sourcesError ? <p className="empty-state" role="status">{sourcesError}</p> : <p className="source-registry-summary">{sources.length} configured retailers · Registry availability is not a product observation.</p>}
          {error ? <div className="error-state" style={{ marginTop: 16 }}>{error}</div> : null}

          <div style={{ marginTop: 24 }}>
            <p className="eyebrow muted">Quick insight</p>
            <div className="mini-stat" style={{ maxWidth: 220 }}>
              <strong>{reviewEvidenceAvailable ? `${Number(preview.positive_percentage || 0).toFixed(1)}%` : '—'}</strong>
              <span>{reviewEvidenceAvailable ? `Positive sentiment · ${provenance}` : preview ? 'No review sentiment available' : 'Positive sentiment signal'}</span>
            </div>
          </div>

          {recentSearches.length ? (
            <div style={{ marginTop: 24 }}>
              <p className="eyebrow muted">Recent searches</p>
              <div className="recent-list">
                {recentSearches.map((item, index) => (
                  <button key={`${item.name}-${index}`} type="button" className="ghost-button recent-item" onClick={() => { setQuery(item.name); setPlatform(item.platform) }}>
                    <span>{item.name}</span>
                    <ArrowRight size={14} />
                  </button>
                ))}
              </div>
            </div>
          ) : null}
        </section>

        <aside className="summary-panel">
          <p className="eyebrow muted">Snapshot</p>
          <h3>Product overview</h3>

          <div className="kpi-grid">
            <div className="kpi-card">
              <span className="label">Total reviews</span>
              <strong>{preview?.total_reviews ?? '—'}</strong>
              <span className="trend">{preview ? provenance : 'No product analyzed'}</span>
            </div>
            <div className="kpi-card">
              <span className="label">Avg rating</span>
              <strong>{reviewEvidenceAvailable ? preview.average_rating : 'unavailable'}</strong>
              <span className="trend">{reviewEvidenceAvailable ? 'Review-derived rating' : 'No rating evidence'}</span>
            </div>
            <div className="kpi-card">
              <span className="label">Positive</span>
              <strong>{reviewEvidenceAvailable ? `${Number(preview.positive_percentage || 0).toFixed(1)}%` : 'unavailable'}</strong>
              <span className="trend">{reviewEvidenceAvailable ? `Positive · ${provenance}` : 'No sentiment evidence'}</span>
            </div>
            <div className="kpi-card">
              <span className="label">Source selection</span>
              <strong>{platform === 'all' ? 'All Sources' : selectedSource?.name || 'Loading'}</strong>
              <span className="trend">{platform === 'all' ? `${sources.length} configured retailers` : selectedSource?.live_connector_configured ? 'Connector configured' : 'Live connector unavailable'}</span>
            </div>
          </div>
        </aside>
      </div>
      {comparisonRun && <StoreComparison key={comparisonRunId} query={comparisonRun} selectedSource={platform} sources={sources} onCategoryChange={setComparisonCategory} onSourceEvidenceChange={setSourceEvidence} />}
    </div>
  )
}

export default SearchPage

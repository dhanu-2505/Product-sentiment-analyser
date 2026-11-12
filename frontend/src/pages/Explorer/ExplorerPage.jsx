import { useEffect, useMemo, useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import {
  Search,
  Filter,
  CheckCircle,
  Calendar,
  Star,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  ExternalLink,
} from 'lucide-react'
import { getProducts, getProductReviews, getReviewQuality } from '../../services/api'

const ASPECTS = [
  'All Aspects',
  'Camera',
  'Battery',
  'Display',
  'Performance',
  'Design',
  'Build Quality',
  'Price',
  'Sound',
  'Comfort',
  'Charging',
  'Software',
  'Durability',
]

function ExplorerPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const initialProductId = searchParams.get('productId') || ''
  const initialCategory = searchParams.get('category') || ''

  const [products, setProducts] = useState([])
  const [selectedProductId, setSelectedProductId] = useState(initialProductId)
  const [categoryFilter, setCategoryFilter] = useState(initialCategory)
  const [reviews, setReviews] = useState([])
  const [totalReviews, setTotalReviews] = useState(0)
  const [totalPages, setTotalPages] = useState(1)
  const [quality, setQuality] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Filters
  const [searchTerm, setSearchTerm] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [ratingFilter, setRatingFilter] = useState('all')
  const [aspectFilter, setAspectFilter] = useState('All Aspects')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [dataTypeFilter, setDataTypeFilter] = useState('all')
  const [verifiedFilter, setVerifiedFilter] = useState('all')
  const [dateStart, setDateStart] = useState('')
  const [dateEnd, setDateEnd] = useState('')
  const [sortBy, setSortBy] = useState('newest')

  // Pagination
  const [currentPage, setCurrentPage] = useState(1)
  const itemsPerPage = 20

  // Load products list on mount
  useEffect(() => {
    const loadProducts = async () => {
      try {
        const res = await getProducts()
        const items = res.data.items || []
        setProducts(items)
        if (!selectedProductId && items.length > 0) {
          const categoryProduct = categoryFilter ? items.find((product) => product.category === categoryFilter) : null
          setSelectedProductId(String(categoryProduct?.id || items[0].id))
        }
      } catch (err) {
        console.error('Failed to load products list', err)
      }
    }
    loadProducts()
  }, [])

  const categoryOptions = useMemo(() => [...new Set(products.map((product) => product.category).filter(Boolean))].sort(), [products])
  const categoryProducts = categoryFilter ? products.filter((product) => product.category === categoryFilter) : products

  // Load reviews whenever selected product changes
  useEffect(() => {
    if (!selectedProductId) return

    const loadReviews = async () => {
      setLoading(true)
      setError('')
      try {
        const params = {
          page: currentPage,
          limit: itemsPerPage,
          search: searchTerm.trim() || undefined,
          sentiment: sentimentFilter === 'all' ? undefined : sentimentFilter,
          rating: ratingFilter === 'all' ? undefined : Number(ratingFilter),
          aspect: aspectFilter === 'All Aspects' ? undefined : aspectFilter,
          source: sourceFilter === 'all' ? undefined : sourceFilter,
          data_type: dataTypeFilter === 'all' ? undefined : dataTypeFilter,
          verified_purchase: verifiedFilter === 'all' ? undefined : verifiedFilter === 'true',
          start_date: dateStart ? `${dateStart}T00:00:00` : undefined,
          end_date: dateEnd ? `${dateEnd}T23:59:59` : undefined,
          sort: sortBy === 'rating_high' ? 'highest' : sortBy === 'rating_low' ? 'lowest' : sortBy,
        }
        const res = await getProductReviews(selectedProductId, params)
        setReviews(res.data.items || [])
        setTotalReviews(res.data.total || 0)
        setTotalPages(res.data.pages || 1)
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to load reviews for this product.')
      } finally {
        setLoading(false)
      }
    }

    loadReviews()
    setSearchParams({ productId: selectedProductId, ...(categoryFilter ? { category: categoryFilter } : {}) }, { replace: true })
  }, [selectedProductId, searchTerm, sentimentFilter, ratingFilter, aspectFilter, sourceFilter, dataTypeFilter, verifiedFilter, dateStart, dateEnd, sortBy, currentPage])

  useEffect(() => {
    if (!selectedProductId) return
    getReviewQuality(selectedProductId)
      .then((response) => setQuality(response.data))
      .catch(() => setQuality(null))
  }, [selectedProductId])

  const selectedProduct = useMemo(() => {
    return products.find((p) => String(p.id) === String(selectedProductId))
  }, [products, selectedProductId])

  const paginatedReviews = reviews

  const renderStars = (rating) => {
    return Array.from({ length: 5 }, (_, i) => (
      <Star
        key={i}
        size={14}
        fill={i < rating ? '#fbbf24' : 'none'}
        stroke={i < rating ? '#fbbf24' : 'rgba(148,163,184,0.4)'}
      />
    ))
  }

  const parseAspects = (raw) => {
    if (!raw) return {}
    if (Array.isArray(raw)) {
      return Object.fromEntries(raw.filter((aspect) => aspect?.aspect).map((aspect) => [aspect.aspect, aspect]))
    }
    if (typeof raw === 'object') return raw
    try {
      return JSON.parse(raw)
    } catch {
      return {}
    }
  }

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">Review Intelligence</p>
          <h2>Customer Review Explorer</h2>
        </div>
        {selectedProduct && (
          <Link to={`/dashboard/${selectedProduct.id}`} className="ghost-button">
            View Analytics Dashboard
            <ExternalLink size={14} style={{ marginLeft: 6 }} />
          </Link>
        )}
      </div>

      {/* Product Selector Bar */}
      <div className="table-panel" style={{ padding: '16px 20px', marginBottom: 20 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
          <label style={{ fontSize: 13, color: 'var(--text-soft)', fontWeight: 500 }}>
            Select Product:
          </label>
          <select className="select-field" value={categoryFilter} onChange={(event) => {
            const nextCategory = event.target.value
            setCategoryFilter(nextCategory)
            const nextProducts = nextCategory ? products.filter((product) => product.category === nextCategory) : products
            if (nextProducts.length) setSelectedProductId(String(nextProducts[0].id))
          }} aria-label="Filter products by category">
            <option value="">All categories</option>
            {categoryOptions.map((category) => <option key={category} value={category}>{category}</option>)}
          </select>
          <select
            className="select-field"
            style={{ minWidth: 260, flex: '1 1 300px' }}
            value={selectedProductId}
            onChange={(e) => setSelectedProductId(e.target.value)}
          >
            {categoryProducts.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} ({p.brand || p.category} - {p.average_rating}★)
              </option>
            ))}
          </select>

          {selectedProduct && (
            <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
              <span className="badge" style={{ background: 'var(--primary-soft)', color: 'var(--primary)' }}>
                {selectedProduct.category}
              </span>
              <span style={{ fontSize: 13, color: 'var(--text-soft)' }}>
                {reviews.length} total reviews analyzed
              </span>
            </div>
          )}
        </div>
      </div>

      <section className="table-panel">
        <div className="section-header">
          <div><p className="eyebrow muted">Review quality signals</p><h3>Patterns in this review sample</h3></div>
          <span className="muted">{quality?.review_count ?? 0} reviews · {quality?.coverage === 'insufficient_data' ? 'insufficient data' : quality?.coverage === 'analyzed_first_500_unique_texts' ? 'first 500 unique texts analyzed' : 'all reviews analyzed'}</span>
        </div>
        {!quality || quality.coverage === 'insufficient_data' ? <p className="empty-state">Insufficient review data to assess patterns.</p> : quality.signals.length === 0 ? <p>{quality.summary}</p> : (
          <div className="card-grid">
            {quality.signals.map((signal) => <article className="feature-card card" key={signal.type}>
              <p className="eyebrow muted">{signal.level.replaceAll('_', ' ')}</p>
              <h4>{signal.type.replaceAll('_', ' ')}</h4>
              <p>{signal.message}</p>
              <span className="muted">{signal.count ?? signal.group_count ?? signal.pair_count ?? signal.sample_size ?? 0} supporting records</span>
            </article>)}
          </div>
        )}
      </section>

      {/* Filter and Search Controls */}
      <div className="table-panel" style={{ padding: '18px 20px', marginBottom: 24 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12 }}>
          {/* Search box */}
          <div style={{ position: 'relative', gridColumn: 'span 2' }}>
            <Search size={16} style={{ position: 'absolute', left: 12, top: 13, color: 'var(--muted)' }} />
            <input
              className="field"
              style={{ paddingLeft: 36 }}
              type="text"
              placeholder="Search in review text or author..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value)
                setCurrentPage(1)
              }}
            />
          </div>

          {/* Sentiment Filter */}
          <select
            className="select-field"
            value={sentimentFilter}
            onChange={(e) => {
              setSentimentFilter(e.target.value)
              setCurrentPage(1)
            }}
          >
            <option value="all">All Sentiments</option>
            <option value="positive">Positive</option>
            <option value="neutral">Neutral</option>
            <option value="negative">Negative</option>
          </select>

          <select className="select-field" value={dataTypeFilter} onChange={(e) => { setDataTypeFilter(e.target.value); setCurrentPage(1) }} aria-label="Filter by data provenance">
            <option value="all">All data provenance</option>
            <option value="live_scraped">Live scraped</option>
            <option value="stored">Stored</option>
            <option value="seeded_demo">Seeded demo</option>
            <option value="unverified">Unverified</option>
          </select>

          <select className="select-field" value={verifiedFilter} onChange={(e) => { setVerifiedFilter(e.target.value); setCurrentPage(1) }} aria-label="Filter verified purchases">
            <option value="all">All purchase verification</option>
            <option value="true">Verified purchase</option>
            <option value="false">Not verified</option>
          </select>

          <label className="auth-field"><span>From date</span><input className="field" type="date" value={dateStart} onChange={(e) => { setDateStart(e.target.value); setCurrentPage(1) }} /></label>
          <label className="auth-field"><span>To date</span><input className="field" type="date" value={dateEnd} onChange={(e) => { setDateEnd(e.target.value); setCurrentPage(1) }} /></label>

          {/* Rating Filter */}
          <select
            className="select-field"
            value={ratingFilter}
            onChange={(e) => {
              setRatingFilter(e.target.value)
              setCurrentPage(1)
            }}
          >
            <option value="all">All Star Ratings</option>
            <option value="5">5 Stars</option>
            <option value="4">4 Stars</option>
            <option value="3">3 Stars</option>
            <option value="2">2 Stars</option>
            <option value="1">1 Star</option>
          </select>

          {/* Aspect Filter */}
          <select
            className="select-field"
            value={aspectFilter}
            onChange={(e) => {
              setAspectFilter(e.target.value)
              setCurrentPage(1)
            }}
          >
            {ASPECTS.map((aspect) => (
              <option key={aspect} value={aspect}>
                {aspect === 'All Aspects' ? 'All Feature Aspects' : `Aspect: ${aspect}`}
              </option>
            ))}
          </select>

          {/* Source Filter */}
          <select
            className="select-field"
            value={sourceFilter}
            onChange={(e) => {
              setSourceFilter(e.target.value)
              setCurrentPage(1)
            }}
          >
            <option value="all">All Sources</option>
            <option value="amazon">Amazon</option>
            <option value="flipkart">Flipkart</option>
            <option value="seed">Seed catalog</option>
          </select>

          {/* Sort By */}
          <select
            className="select-field"
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
          >
            <option value="newest">Newest First</option>
            <option value="oldest">Oldest First</option>
            <option value="rating_high">Highest Rating</option>
            <option value="rating_low">Lowest Rating</option>
            <option value="confidence">Highest Confidence</option>
          </select>
        </div>

        {/* Results summary bar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--line)', fontSize: 13, color: 'var(--muted)' }}>
          <span>
            Showing <strong>{reviews.length}</strong> of <strong>{totalReviews}</strong> matching reviews
          </span>
          {(searchTerm || sentimentFilter !== 'all' || ratingFilter !== 'all' || aspectFilter !== 'All Aspects' || sourceFilter !== 'all' || dataTypeFilter !== 'all' || verifiedFilter !== 'all' || dateStart || dateEnd || sortBy !== 'newest') && (
            <button
              className="ghost-button"
              style={{ padding: '4px 10px', fontSize: 12 }}
              onClick={() => {
                setSearchTerm('')
                setSentimentFilter('all')
                setRatingFilter('all')
                setAspectFilter('All Aspects')
                setSourceFilter('all')
                setDataTypeFilter('all')
                setVerifiedFilter('all')
                setDateStart('')
                setDateEnd('')
                setSortBy('newest')
                setCurrentPage(1)
              }}
            >
              Reset Filters
            </button>
          )}
        </div>
      </div>

      {/* Review List */}
      {loading ? (
        <div className="loading-grid">
          <div className="skeleton-line large" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
        </div>
      ) : error ? (
        <div className="error-state">
          <h3>Error loading reviews</h3>
          <p>{error}</p>
        </div>
      ) : paginatedReviews.length === 0 ? (
        <div className="empty-state">
          <Sparkles size={36} style={{ color: 'var(--primary)', marginBottom: 12 }} />
          <h3>No reviews match your filters</h3>
          <p>Try clearing search keywords or selecting different sentiment and aspect filters.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {paginatedReviews.map((rev) => {
            const detectedAspects = parseAspects(rev.aspects || rev.sentiment_aspects)
            const aspectEntries = Object.entries(detectedAspects)

            return (
              <div
                key={rev.id}
                className="feature-card card"
                style={{ padding: '18px 22px', borderRadius: '16px' }}
              >
                {/* Header row: Reviewer info, verified badge, rating, date */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <div
                      style={{
                        width: 32,
                        height: 32,
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(56, 189, 248, 0.4))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 600,
                        fontSize: 13,
                        color: 'var(--text)',
                      }}
                    >
                      {(rev.reviewer_name || 'U').charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                        <span style={{ fontWeight: 600, fontSize: 14, color: 'var(--text)' }}>
                          {rev.reviewer_name || 'Anonymous Purchaser'}
                        </span>
                        {rev.verified_purchase === true ? (
                          <span
                            title="Verified Purchase"
                            style={{
                              display: 'inline-flex',
                              alignItems: 'center',
                              gap: 3,
                              fontSize: 11,
                              color: 'var(--green)',
                              background: 'var(--green-soft)',
                              padding: '2px 6px',
                              borderRadius: '4px',
                            }}
                          >
                            <CheckCircle size={11} />
                            Verified
                          </span>
                        ) : <span className="muted">Not verified</span>}
                        <span className={`badge provenance-${rev.data_type === 'seeded_demo' ? 'demo' : rev.data_type === 'live_scraped' ? 'live' : 'unknown'}`}>
                          {rev.data_type === 'seeded_demo' ? 'Seeded demo' : rev.data_type === 'live_scraped' ? 'Live scraped' : 'Unverified'}
                        </span>
                        <span
                          style={{
                            fontSize: 11,
                            color: 'var(--muted)',
                            background: 'rgba(148,163,184,0.1)',
                            padding: '2px 6px',
                            borderRadius: '4px',
                            textTransform: 'capitalize',
                          }}
                        >
                          {rev.source || 'Source unavailable'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginTop: 2 }}>
                        <div style={{ display: 'flex', gap: 2 }}>{renderStars(rev.rating)}</div>
                        <span style={{ fontSize: 12, color: 'var(--muted)' }}>
                          {rev.review_date
                            ? new Date(rev.review_date).toLocaleDateString(undefined, {
                                year: 'numeric',
                                month: 'short',
                                day: 'numeric',
                              })
                            : 'Recent'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Sentiment and Quality badge */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span className={`badge ${rev.sentiment || 'neutral'}`}>
                      {rev.sentiment || 'neutral'}
                    </span>
                    {rev.sentiment_score > 0 && (
                      <span style={{ fontSize: 12, color: 'var(--text-soft)' }}>
                        {Math.round(rev.sentiment_score * 100)}% conf
                      </span>
                    )}
                  </div>
                </div>

                <details className="review-details">
                  <summary>Review text and details</summary>
                  <p style={{ margin: '8px 0 12px 0', fontSize: 14, lineHeight: 1.6, color: 'var(--text)' }}>{rev.review_text}</p>
                  <p className="muted">Source: {rev.source || 'Unavailable'} · Provenance: {rev.data_type} · Confidence: {Math.round((rev.confidence || 0) * 100)}%</p>
                </details>

                {/* Aspect breakdown chips */}
                {aspectEntries.length > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, paddingTop: 8, borderTop: '1px solid rgba(148,163,184,0.1)' }}>
                    <span style={{ fontSize: 11, color: 'var(--muted)', alignSelf: 'center', marginRight: 4 }}>
                      Detected Aspects:
                    </span>
                    {aspectEntries.map(([aspect, details]) => {
                      const sent = details?.sentiment || 'neutral'
                      const isPos = sent === 'positive'
                      const isNeg = sent === 'negative'
                      const color = isPos ? 'var(--green)' : isNeg ? 'var(--red)' : 'var(--amber)'
                      const bg = isPos ? 'var(--green-soft)' : isNeg ? 'var(--red-soft)' : 'var(--amber-soft)'

                      return (
                        <span
                          key={aspect}
                          style={{
                            fontSize: 11,
                            padding: '3px 8px',
                            borderRadius: '6px',
                            background: bg,
                            color: color,
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 4,
                          }}
                        >
                          <strong>{aspect}:</strong> {sent}
                        </span>
                      )
                    })}
                  </div>
                )}
              </div>
            )
          })}

          {/* Pagination Controls */}
          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 12, marginTop: 20 }}>
              <button
                className="ghost-button"
                disabled={currentPage === 1}
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              >
                <ChevronLeft size={16} />
                Previous
              </button>
              <span style={{ fontSize: 13, color: 'var(--text-soft)' }}>
                Page {currentPage} of {totalPages}
              </span>
              <button
                className="ghost-button"
                disabled={currentPage === totalPages}
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              >
                Next
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default ExplorerPage

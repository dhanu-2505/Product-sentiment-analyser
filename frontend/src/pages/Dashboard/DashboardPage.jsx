import { useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Bookmark } from 'lucide-react'
import CompactChartTooltip from '../../components/CompactChartTooltip'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Area,
  AreaChart,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { getAnalytics, getDashboardOverview, getProduct, getProductReviews, getProductSources, getProducts, getReviewQuality, saveProduct } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

const COLORS = ['#34d399', '#fbbf24', '#f87171']
const DETAIL_TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'reviews', label: 'Reviews' },
  { id: 'sentiment', label: 'Sentiment' },
  { id: 'aspects', label: 'Aspects' },
  { id: 'priceSources', label: 'Price & Sources' },
  { id: 'analytics', label: 'Analytics & Trends' },
  { id: 'quality', label: 'Review Quality' },
  { id: 'comparison', label: 'Compare & Related' },
  { id: 'reports', label: 'Reports' },
]

const evidenceTypeLabel = (value) => {
  if (value === 'seeded_demo') return 'seeded_demo'
  if (value === 'live' || value === 'live_scraped') return 'live'
  if (value === 'stored') return 'stored'
  return 'unavailable'
}

function DashboardPage() {
  const { productId } = useParams()
  const [searchParams] = useSearchParams()
  const selectedSource = searchParams.get('source') || ''
  const { token } = useAuth()
  const [product, setProduct] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [reviews, setReviews] = useState([])
  const [reviewTotal, setReviewTotal] = useState(0)
  const [reviewQuality, setReviewQuality] = useState(null)
  const [sources, setSources] = useState([])
  const [relatedProducts, setRelatedProducts] = useState([])
  const [activeTab, setActiveTab] = useState('overview')
  const [historyRange, setHistoryRange] = useState('all')
  const [saved, setSaved] = useState(false)
  const [saveMessage, setSaveMessage] = useState('')
  const [saving, setSaving] = useState(false)
  const [overview, setOverview] = useState(null)
  const [catalog, setCatalog] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!productId) {
      const fetchOverview = async () => {
        setLoading(true)
        setError('')
        try {
          const [overviewResponse, productsResponse] = await Promise.all([
            getDashboardOverview(),
            getProducts({ sort: 'popular' }),
          ])
          setOverview(overviewResponse.data)
          setCatalog(productsResponse.data.items || [])
        } catch (requestError) {
          setError(requestError?.response?.data?.detail || 'Unable to load the dashboard overview.')
        } finally {
          setLoading(false)
        }
      }
      fetchOverview()
      return
    }

    const fetchDashboard = async () => {
      setLoading(true)
      setError('')
      setActiveTab('overview')

      try {
        const [productRes, analyticsRes, reviewsRes, sourcesRes, qualityRes] = await Promise.all([
          getProduct(productId),
          getAnalytics(productId, selectedSource ? { source: selectedSource } : {}),
          getProductReviews(productId, { limit: 100, ...(selectedSource ? { source: selectedSource } : {}) }),
          getProductSources(productId),
          getReviewQuality(productId, selectedSource ? { source: selectedSource } : {}).catch(() => ({ data: null })),
        ])

        setProduct(productRes.data)
        setAnalytics(analyticsRes.data)
        setReviews(reviewsRes.data.items || [])
        setReviewTotal(reviewsRes.data.total ?? reviewsRes.data.items?.length ?? 0)
        setReviewQuality(qualityRes.data)
        setSources(sourcesRes.data.items || [])
        setRelatedProducts([])
        if (productRes.data.category) {
          getProducts({ category: productRes.data.category, sort: 'popular' })
            .then((response) => setRelatedProducts((response.data.items || []).filter((item) => item.id !== productRes.data.id).slice(0, 4)))
            .catch(() => setRelatedProducts([]))
        }
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to analyze this product')
      } finally {
        setLoading(false)
      }
    }

    fetchDashboard()
  }, [productId, selectedSource])

  const sentimentData = useMemo(() => {
    if (!analytics) {
      return []
    }

    return [
      { name: 'Positive', value: Number(analytics.positive_percentage || 0), color: COLORS[0] },
      { name: 'Neutral', value: Number(analytics.neutral_percentage || 0), color: COLORS[1] },
      { name: 'Negative', value: Number(analytics.negative_percentage || 0), color: COLORS[2] },
    ]
  }, [analytics])

  const ratingData = useMemo(() => {
    if (!analytics?.rating_distribution) {
      return []
    }

    return Object.entries(analytics.rating_distribution).map(([star, count]) => ({ name: `${star}★`, count }))
  }, [analytics])

  const trendData = useMemo(() => analytics?.sentiment_trend || [], [analytics])
  const wordData = useMemo(() => analytics?.word_frequency || [], [analytics])
  const sentimentHistory = analytics?.sentiment_history || []
  const filteredSentimentHistory = useMemo(() => {
    if (historyRange === 'all') return sentimentHistory
    const days = Number(historyRange)
    const threshold = Date.now() - days * 24 * 60 * 60 * 1000
    return sentimentHistory.filter((record) => record.date && new Date(record.date).getTime() >= threshold)
  }, [sentimentHistory, historyRange])
  const priceHistorySources = sources
    .map((source) => ({
      ...source,
      price_history: (source.price_history || []).filter((point) => (
        point.price != null && point.observed_at && ['stored', 'live', 'live_scraped'].includes(point.data_type)
      )),
    }))
    .filter((source) => source.price_history.length >= 2)
  const priceHistoryDates = [...new Set(priceHistorySources.flatMap((source) => source.price_history.map((point) => point.observed_at)))].sort()
  const priceHistoryData = priceHistoryDates.map((date) => ({
    date,
    ...Object.fromEntries(priceHistorySources.map((source) => [
      source.source,
      source.price_history.find((point) => point.observed_at === date)?.price ?? null,
    ])),
  }))
  const reviewProvenance = [...new Set(reviews.map((review) => evidenceTypeLabel(review.data_type)))].join(', ') || 'unavailable'
  const hasReviewData = Number(analytics?.total_reviews ?? 0) > 0
  const averageRating = analytics?.average_rating ?? product?.average_rating
  const intelligenceScore = analytics?.product_intelligence?.overall_score

  const addToWatchlist = async () => {
    setSaving(true)
    setSaveMessage('')
    try {
      await saveProduct({ product_id: Number(productId) }, token)
      setSaved(true)
      setSaveMessage('Added to your watchlist.')
    } catch (requestError) {
      setSaveMessage(requestError?.response?.data?.detail || 'Unable to save this product.')
    } finally {
      setSaving(false)
    }
  }

  if (!productId && overview) {
    return (
      <main className="page">
        <header className="section-header">
          <div><p className="eyebrow muted">Workspace overview</p><h2>Customer feedback intelligence</h2></div>
          <Link to="/analyze" className="primary-button">Analyze a product</Link>
        </header>
        <section className="kpi-grid">
          <div className="kpi-card"><span className="label">Products</span><strong>{overview.total_products}</strong></div>
          <div className="kpi-card"><span className="label">Reviews</span><strong>{overview.total_reviews}</strong></div>
          <div className="kpi-card"><span className="label">Average rating</span><strong>{overview.average_product_rating}/5</strong></div>
          <div className="kpi-card"><span className="label">Positive sentiment</span><strong>{overview.positive_reviews_percentage}%</strong></div>
          <div className="kpi-card"><span className="label">Neutral sentiment</span><strong>{overview.neutral_reviews_percentage}%</strong></div>
          <div className="kpi-card"><span className="label">Negative sentiment</span><strong>{overview.negative_reviews_percentage}%</strong></div>
        </section>
        <section className="dashboard-grid">
          <div className="chart-panel">
            <h4>Rating distribution</h4>
            <div style={{ width: '100%', height: 260 }}><ResponsiveContainer><BarChart data={Object.entries(overview.rating_distribution || {}).map(([rating, count]) => ({ name: `${rating} stars`, count }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" /><XAxis dataKey="name" /><YAxis allowDecimals={false} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Bar dataKey="count" fill="#60a5fa" radius={[5, 5, 0, 0]} isAnimationActive />
            </BarChart></ResponsiveContainer></div>
          </div>
          <div className="chart-panel">
            <h4>Popular categories</h4>
            <div style={{ width: '100%', height: 260 }}><ResponsiveContainer><BarChart data={(overview.top_categories || []).slice(0, 7)} layout="vertical" margin={{ left: 16 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" /><XAxis type="number" allowDecimals={false} /><YAxis dataKey="category" type="category" width={120} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Bar dataKey="count" fill="#34d399" radius={[0, 5, 5, 0]} isAnimationActive />
            </BarChart></ResponsiveContainer></div>
          </div>
          <div className="chart-panel" style={{ gridColumn: '1 / -1' }}>
            <h4>Most reviewed products</h4>
            {catalog.length === 0 ? <p className="empty-state">No products are available yet.</p> : <div className="table-wrap"><table className="data-table">
              <thead><tr><th>Product</th><th>Brand</th><th>Rating</th><th>Reviews</th><th>Analysis</th></tr></thead>
              <tbody>{catalog.slice(0, 8).map((item) => <tr key={item.id}><td>{item.name}</td><td>{item.brand || 'Unknown'}</td><td>{item.average_rating ?? 'Unavailable'}</td><td>{item.total_reviews ?? 0}</td><td><Link to={`/products/${item.id}`}>Open analysis</Link></td></tr>)}</tbody>
            </table></div>}
          </div>
        </section>
      </main>
    )
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading-grid">
          <div className="skeleton-line large" />
          <div className="skeleton-line short" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
          <div className="skeleton-card large" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-state">
          <h3>Unable to analyze this product</h3>
          <p>{error}</p>
          <Link to="/search" className="primary-button">Try Again</Link>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">Dashboard</p>
          <h3>{product?.name || 'Product analysis'}</h3>
          <span className="badge provenance-unknown">Catalog data: {evidenceTypeLabel(product?.data_type)}</span>
          {selectedSource && <span className="badge provenance-unknown">Source analysis: {sources.find((source) => source.source === selectedSource)?.source_name || selectedSource}</span>}
        </div>
        <div className="hero-actions">
          <button type="button" className="ghost-button" onClick={addToWatchlist} disabled={saving || saved} title={saved ? 'Already in your wishlist' : 'Add this product to your wishlist'}><Bookmark size={16} /> {saved ? 'Wishlist' : saving ? 'Saving...' : 'Add to wishlist'}</button>
          <Link to={`/products/${productId}/sources`} className="ghost-button">Source comparison</Link>
          <Link to="/compare" className="ghost-button">Compare products</Link>
          <Link to="/search" className="primary-button">Analyze again</Link>
        </div>
      </div>
      {saveMessage && <p className={saved ? 'success-message' : 'error-state'} role="status">{saveMessage}</p>}

      <div className="kpi-grid" style={{ marginTop: 8 }}>
        <div className="kpi-card">
          <span className="label">Total reviews</span>
          <strong>{analytics?.total_reviews ?? product?.total_reviews ?? 0}</strong>
          <span className="trend">Review sample: {reviewProvenance}</span>
        </div>
        <div className="kpi-card">
          <span className="label">Average rating</span>
          <strong>{hasReviewData && averageRating != null ? `${Number(averageRating).toFixed(1)}/5` : 'Unavailable'}</strong>
          <span className="trend">{hasReviewData ? `Review data type: ${reviewProvenance}` : 'unavailable'}</span>
        </div>
        <div className="kpi-card">
          <span className="label">Positive / neutral / negative</span>
          <strong>{hasReviewData ? `${analytics.positive_percentage}% / ${analytics.neutral_percentage}% / ${analytics.negative_percentage}%` : 'Unavailable'}</strong>
          <span className="trend">{hasReviewData ? reviewProvenance : 'unavailable'}</span>
        </div>
        <div className="kpi-card">
          <span className="label">Intelligence score</span>
          <strong>{intelligenceScore == null ? 'Unavailable' : `${intelligenceScore}/100`}</strong>
          <span className="trend">Evidence-weighted summary</span>
        </div>
      </div>

      <nav className="detail-tabs" role="tablist" aria-label="Product detail sections">
        {DETAIL_TABS.map((tab) => (
          <button key={tab.id} id={`detail-tab-${tab.id}`} type="button" role="tab" aria-controls="detail-panel" aria-selected={activeTab === tab.id} className={activeTab === tab.id ? 'active' : ''} onClick={() => setActiveTab(tab.id)}>
            {tab.label}
          </button>
        ))}
      </nav>

      <div id="detail-panel" className="detail-tab-content" key={activeTab} role="tabpanel" aria-labelledby={`detail-tab-${activeTab}`}>
      {activeTab === 'overview' && <>
      {!hasReviewData ? <section className="table-panel"><h3>Review evidence unavailable</h3><p className="empty-state">No stored reviews are available for this product yet. Ratings, sentiment, aspects, and review-derived scores are unavailable.</p></section> :
      <div className="dashboard-grid">
        <div className="chart-panel">
          <h4>Sentiment distribution</h4>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <PieChart>
                <Pie data={sentimentData} innerRadius={55} outerRadius={90} dataKey="value" paddingAngle={3}>
                  {sentimentData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel">
          <h4>Rating distribution</h4>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={ratingData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis dataKey="name" stroke="#c7d2eb" />
                <YAxis stroke="#c7d2eb" />
                <Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
                <Bar dataKey="count" fill="#8b5cf6" radius={[10, 10, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel" style={{ gridColumn: '1 / -1' }}>
          <h4>Sentiment trend</h4>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis dataKey="date" stroke="#c7d2eb" />
                <YAxis stroke="#c7d2eb" />
                <Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
                <Line type="monotone" dataKey="positive" stroke="#34d399" strokeWidth={3} />
                <Line type="monotone" dataKey="neutral" stroke="#fbbf24" strokeWidth={3} />
                <Line type="monotone" dataKey="negative" stroke="#f87171" strokeWidth={3} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="chart-panel">
          <h4>Frequently mentioned words</h4>
          <div style={{ width: '100%', height: 260 }}>
            <ResponsiveContainer>
              <BarChart data={wordData.slice(0, 8)} layout="vertical" margin={{ left: 18 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(148,163,184,0.14)" />
                <XAxis type="number" stroke="#c7d2eb" />
                <YAxis dataKey="word" type="category" width={110} stroke="#c7d2eb" />
                <Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />
                <Bar dataKey="count" fill="#60a5fa" radius={[0, 10, 10, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>}

      <div className="table-panel">
        <div className="section-header">
          <div>
            <p className="eyebrow muted">Recent reviews</p>
            <h3>Customer feedback</h3>
          </div>
          <Link to={`/reviews/${productId}`} className="ghost-button">View all</Link>
        </div>

        {reviews.length === 0 ? <p className="empty-state">No stored reviews are available for this product.</p> : <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>Reviewer</th>
                <th>Rating</th>
                <th>Review</th>
                <th>Sentiment</th>
                <th>Score</th>
                <th>Data origin</th>
              </tr>
            </thead>
            <tbody>
              {(reviews || []).slice(0, 5).map((review) => (
                <tr key={review.id}>
                  <td>{review.reviewer_name || 'Anonymous'}</td>
                  <td>{review.rating}/5</td>
                  <td>{review.review_text}</td>
                  <td><span className={`badge ${review.sentiment}`}>{review.sentiment}</span></td>
                  <td>{Number(review.sentiment_score || 0).toFixed(2)}</td>
                  <td>
                    <span className={`badge provenance-${review.data_type === 'seeded_demo' ? 'demo' : review.data_type === 'live_scraped' ? 'live' : 'unknown'}`}>
                      {evidenceTypeLabel(review.data_type)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>}
      </div>
      </>}

      {activeTab === 'reviews' && <section className="table-panel">
        <div className="section-header"><div><p className="eyebrow muted">Review explorer</p><h3>Customer feedback</h3><p className="muted">Showing up to 100 of {reviewTotal} stored reviews · {reviewProvenance}</p></div><Link to={`/explorer?productId=${productId}`} className="ghost-button">Open review explorer</Link></div>
        {reviews.length === 0 ? <p className="empty-state">No stored reviews are available for this product.</p> : <div className="table-wrap"><table className="data-table">
          <thead><tr><th>Reviewer</th><th>Rating</th><th>Review</th><th>Date</th><th>Sentiment</th><th>Score</th><th>Data type</th></tr></thead>
          <tbody>{reviews.map((review) => <tr key={review.id}><td>{review.reviewer_name || 'Anonymous'}</td><td>{review.rating}/5</td><td>{review.review_text}</td><td>{review.review_date ? new Date(review.review_date).toLocaleDateString() : 'unavailable'}</td><td><span className={`badge ${review.sentiment}`}>{review.sentiment}</span></td><td>{Number(review.sentiment_score || 0).toFixed(2)}</td><td>{evidenceTypeLabel(review.data_type)}</td></tr>)}</tbody>
        </table></div>}
      </section>}

      {activeTab === 'sentiment' && <section className="dashboard-grid">
        {!hasReviewData ? <div className="chart-panel" style={{ gridColumn: '1 / -1' }}><h4>Sentiment evidence unavailable</h4><p className="empty-state">No stored reviews are available to calculate a sentiment distribution.</p></div> : <>
        <div className="chart-panel"><h4>Sentiment distribution</h4><div style={{ width: '100%', height: 280 }}><ResponsiveContainer><PieChart><Pie data={sentimentData} innerRadius={58} outerRadius={100} dataKey="value" paddingAngle={3}>{sentimentData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}</Pie><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /></PieChart></ResponsiveContainer></div><p className="muted">Review data type: {reviewProvenance}</p></div>
        <div className="chart-panel"><h4>Review sentiment by date</h4>{trendData.length ? <div style={{ width: '100%', height: 280 }}><ResponsiveContainer><AreaChart data={trendData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis domain={[0, 1]} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Area type="monotone" dataKey="positive" stroke="#34d399" fill="#34d399" fillOpacity={0.18} /><Area type="monotone" dataKey="negative" stroke="#f87171" fill="#f87171" fillOpacity={0.12} /></AreaChart></ResponsiveContainer></div> : <p className="empty-state">Review-date sentiment trend is unavailable.</p>}</div>
        </>}
      </section>}

      {activeTab === 'aspects' && <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Review-derived evidence</p><h3>Aspect satisfaction</h3></div><span className="badge provenance-unknown">{hasReviewData ? reviewProvenance : 'unavailable'}</span></div>{(analytics?.top_aspects || []).length === 0 ? <p className="empty-state">No aspect mentions are available in stored reviews.</p> : <div className="table-wrap"><table className="data-table"><thead><tr><th>Aspect</th><th>Positive</th><th>Neutral</th><th>Negative</th><th>Total mentions</th><th>Positive mention share</th><th>Average evidence score</th></tr></thead><tbody>{analytics.top_aspects.map((item) => <tr key={item.aspect}><td>{item.aspect}</td><td>{item.positive}</td><td>{item.neutral}</td><td>{item.negative}</td><td>{item.total}</td><td>{item.total ? `${((item.positive / item.total) * 100).toFixed(1)}%` : 'unavailable'}</td><td>{item.avg_score ?? 'unavailable'}</td></tr>)}</tbody></table></div>}</section>}

      {activeTab === 'priceSources' && <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Retailer observations</p><h3>Price & Sources</h3></div><Link to={`/products/${productId}/sources`} className="ghost-button">Source comparison</Link></div><p className="muted">Only recorded observations are shown. Live prices and availability are never inferred from catalog data.</p><div className="table-wrap"><table className="data-table"><thead><tr><th>Source</th><th>Data type</th><th>Observed price</th><th>Retailer rating</th><th>Review count</th><th>Availability</th><th>Observed at</th></tr></thead><tbody>{sources.map((source) => <tr key={source.source}><td>{source.source_name}</td><td>{evidenceTypeLabel(source.status)}</td><td>{source.price == null ? 'unavailable' : `${source.currency ? `${source.currency} ` : ''}${source.price}`}</td><td>{source.rating ?? 'unavailable'}</td><td>{source.review_count ?? 'unavailable'}</td><td>{source.availability == null ? 'unavailable' : source.availability ? 'available' : 'unavailable'}</td><td>{source.observed_at ? new Date(source.observed_at).toLocaleString() : 'unavailable'}</td></tr>)}</tbody></table></div>{priceHistoryData.length >= 2 ? <div className="chart-panel detail-chart"><h4>Recorded price history</h4><div style={{ width: '100%', height: 300 }}><ResponsiveContainer><LineChart data={priceHistoryData}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} />{priceHistorySources.map((source) => <Line key={source.source} type="monotone" dataKey={source.source} name={source.source_name} isAnimationActive />)}</LineChart></ResponsiveContainer></div><p className="muted">Only sources with at least two recorded stored/live observations are charted.</p></div> : <p className="empty-state">Historical price trends are unavailable; no source has at least two recorded price observations.</p>}</section>}

      {activeTab === 'analytics' && <>
        <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Explainable score</p><h3>Product intelligence</h3></div><strong>{intelligenceScore == null ? 'Unavailable' : `${intelligenceScore}/100`}</strong></div><p className="muted">Composite score derived from available review, rating, sentiment, aspect, and volume evidence. It is not a product ranking.</p><div className="card-grid">{Object.entries(analytics?.product_intelligence?.breakdown || {}).filter(([key]) => ['customer_sentiment', 'rating_quality', 'feature_satisfaction', 'review_consistency', 'value_perception', 'review_volume'].includes(key)).map(([key, value]) => <article className="feature-card card" key={key}><p className="eyebrow muted">{value.weight}</p><h4>{value.title}</h4><strong>{value.score == null ? 'Unavailable' : `${value.score}/100`}</strong><p>{value.detail}</p></article>)}</div></section>
        <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Stored analysis snapshots</p><h3>Sentiment history</h3></div><select className="select-field" value={historyRange} onChange={(event) => setHistoryRange(event.target.value)} aria-label="Filter sentiment history"><option value="7">7 days</option><option value="30">30 days</option><option value="90">90 days</option><option value="180">6 months</option><option value="365">1 year</option><option value="all">All available</option></select></div>{filteredSentimentHistory.length === 0 ? <p className="empty-state">Stored sentiment trends are unavailable for this product and time range.</p> : <div style={{ width: '100%', height: 300 }}><ResponsiveContainer><LineChart data={filteredSentimentHistory}><CartesianGrid strokeDasharray="3 3" /><XAxis dataKey="date" /><YAxis domain={[0, 100]} /><Tooltip content={<CompactChartTooltip />} offset={8} wrapperStyle={{ pointerEvents: 'none' }} /><Line type="monotone" dataKey="positive_percentage" name="Positive %" stroke="#34d399" isAnimationActive /><Line type="monotone" dataKey="neutral_percentage" name="Neutral %" stroke="#fbbf24" isAnimationActive /><Line type="monotone" dataKey="negative_percentage" name="Negative %" stroke="#f87171" isAnimationActive /></LineChart></ResponsiveContainer></div>}</section>
      </>}

      {activeTab === 'quality' && <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Review quality signals</p><h3>Patterns in stored reviews</h3></div><span className="badge provenance-unknown">{reviewQuality ? `${reviewQuality.review_count} analyzed` : 'unavailable'}</span></div>{!reviewQuality || reviewQuality.coverage === 'insufficient_data' ? <p className="empty-state">Insufficient review data to assess patterns.</p> : <><p className="muted">{reviewQuality.summary} Coverage: {reviewQuality.coverage === 'analyzed_first_500_unique_texts' ? 'first 500 unique texts analyzed' : 'all reviews analyzed'}.</p>{reviewQuality.signals.length === 0 ? <p>No configured review-pattern signals were found in this sample.</p> : <div className="card-grid">{reviewQuality.signals.map((signal) => <article className="feature-card card" key={signal.type}><p className="eyebrow muted">{signal.level}</p><h4>{signal.type.replaceAll('_', ' ')}</h4><p>{signal.message}</p></article>)}</div>}</>}</section>}

      {activeTab === 'comparison' && <section className="table-panel"><div className="section-header"><div><p className="eyebrow muted">Comparable evidence</p><h3>Related products</h3></div><Link to="/compare" className="primary-button">Open comparison</Link></div><p className="muted">Compare products using recorded price, ratings, review volume, and aspects. No universal winner is assigned.</p>{relatedProducts.length === 0 ? <p className="empty-state">No other products in this category are available for comparison.</p> : <div className="card-grid">{relatedProducts.map((item) => <article className="feature-card card" key={item.id}><p className="eyebrow muted">{item.category || 'Category unavailable'}</p><h4>{item.name}</h4><p>{item.brand || 'Brand unavailable'}</p><p>Rating: {item.total_reviews > 0 ? `${Number(item.average_rating).toFixed(1)}/5` : 'unavailable'} · Reviews: {item.total_reviews ?? 'unavailable'}</p><span className="badge provenance-unknown">Catalog data: {evidenceTypeLabel(item.data_type)}</span><Link to={`/products/${item.id}`} className="ghost-button">View details</Link></article>)}</div>}</section>}

      {activeTab === 'reports' && <section className="table-panel"><p>Generate a persisted report containing the available reviews, aspects, source observations, history, and provenance for this product.</p><div className="hero-actions"><Link to={`/reports?productId=${productId}`} className="primary-button">Open report center</Link><Link to={`/explorer?productId=${productId}`} className="ghost-button">Review explorer</Link></div></section>}
      </div>
    </div>
  )
}

export default DashboardPage

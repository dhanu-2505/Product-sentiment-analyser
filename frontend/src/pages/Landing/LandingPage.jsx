import { ArrowRight, BarChart3, Bot, Database, Search, Sparkles, TrendingUp } from 'lucide-react'
import { useEffect, useState } from 'react'
import { motion, useMotionValue, useSpring } from 'framer-motion'
import { Link } from 'react-router-dom'
import { getDashboardOverview, getProducts } from '../../services/api'

const features = [
  {
    icon: Search,
    title: 'Dynamic review discovery',
    description: 'Search the stored catalog and inspect review data with explicit source provenance.',
  },
  {
    icon: Bot,
    title: 'NLP-powered insights',
    description: 'Classify feedback into positive, neutral and negative with VADER-based scoring.',
  },
  {
    icon: TrendingUp,
    title: 'Actionable analytics',
    description: 'Understand rating patterns, sentiment drift, and common themes in the language your users use.',
  },
  {
    icon: Database,
    title: 'Historical intelligence',
    description: 'Track product performance over time and compare sentiment trends across analyses.',
  },
]

const steps = [
  'Search Product',
  'Collect Reviews',
  'Analyze Sentiment',
  'Generate Insights',
  'Explore Dashboard',
]

const tech = ['React', 'FastAPI', 'PostgreSQL', 'Selenium', 'VADER']

function LandingPage() {
  const [overview, setOverview] = useState(null)
  const [catalog, setCatalog] = useState([])
  const [metricsUnavailable, setMetricsUnavailable] = useState(false)
  const cursorX = useMotionValue(0)
  const cursorY = useMotionValue(0)
  const traceX = useSpring(cursorX, { stiffness: 90, damping: 24 })
  const traceY = useSpring(cursorY, { stiffness: 90, damping: 24 })

  useEffect(() => {
    Promise.all([getDashboardOverview(), getProducts()])
      .then(([overviewResponse, productsResponse]) => {
        setOverview(overviewResponse.data)
        setCatalog(productsResponse.data.items || [])
      })
      .catch(() => setMetricsUnavailable(true))
  }, [])

  const dataTypes = overview?.review_data_types || {}
  const seededReviews = Number(dataTypes.seeded_demo || 0)
  const liveReviews = Number(dataTypes.live_scraped || 0)
  const provenanceLabel = !overview
    ? metricsUnavailable ? 'Data unavailable' : 'Loading data'
    : seededReviews > 0 && liveReviews > 0
      ? 'Demo + live data'
      : seededReviews > 0
        ? 'Seeded demo data'
        : liveReviews > 0
          ? 'Live-scraped data'
          : 'No review data'
  const provenanceClass = seededReviews > 0 && liveReviews > 0
    ? 'unknown'
    : seededReviews > 0
      ? 'demo'
      : liveReviews > 0
        ? 'live'
        : 'unknown'
  const categories = [...new Set(catalog.map((product) => product.category).filter(Boolean))].sort()
  const reviewedProducts = catalog.filter((product) => Number(product.total_reviews || 0) > 0)
  const mostReviewed = [...reviewedProducts].sort((left, right) => right.total_reviews - left.total_reviews).slice(0, 4)
  const highlyRated = [...reviewedProducts].sort((left, right) => right.average_rating - left.average_rating).slice(0, 4)
  const moveDataTrace = (event) => {
    const bounds = event.currentTarget.getBoundingClientRect()
    cursorX.set(event.clientX - bounds.left)
    cursorY.set(event.clientY - bounds.top)
  }

  return (
    <div className="page">
      <motion.section className="hero" onPointerMove={moveDataTrace} initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, ease: 'easeOut' }}>
        <motion.div className="hero-cursor-line" aria-hidden="true" style={{ left: traceX, top: traceY }} />
        <div className="hero-grid">
          <div className="hero-copy">
            <p className="eyebrow">Customer intelligence platform</p>
            <h1>Understand What Customers Really Think.</h1>
            <p>
              Transform product reviews into meaningful sentiment and customer intelligence.
            </p>

            <div className="hero-actions">
              <Link to="/search" className="primary-button">Analyze Products</Link>
              <Link to="/login" className="secondary-button">Login</Link>
            </div>

            <div className="metrics-row">
              <div className="mini-stat">
                <strong>{overview?.total_products?.toLocaleString() ?? '—'}</strong>
                <span>Products in catalog</span>
              </div>
              <div className="mini-stat">
                <strong>{overview?.total_reviews?.toLocaleString() ?? '—'}</strong>
                <span>Stored reviews</span>
              </div>
              <div className="mini-stat">
                <strong>{overview ? `${Number(overview.average_product_rating || 0).toFixed(1)}/5` : '—'}</strong>
                <span>Average product rating</span>
              </div>
            </div>
          </div>

          <motion.div className="dashboard-preview" whileHover={{ y: -4 }} transition={{ duration: 0.25 }}>
            <div className="preview-top">
              <div>
                <p className="eyebrow muted">Stored review data</p>
                <strong>Catalog overview</strong>
              </div>
              <span className={`badge provenance-${provenanceClass}`}>{provenanceLabel}</span>
            </div>

            <div className="preview-grid">
              <div className="preview-card">
                <span className="label">Total reviews</span>
                <strong>{overview?.total_reviews?.toLocaleString() ?? '—'}</strong>
              </div>
              <div className="preview-card">
                <span className="label">Avg rating</span>
                <strong>{overview ? Number(overview.average_product_rating || 0).toFixed(1) : '—'}</strong>
              </div>
              <div className="preview-card">
                <span className="label">Neutral</span>
                <strong>{overview ? `${Number(overview.neutral_reviews_percentage || 0).toFixed(1)}%` : '—'}</strong>
              </div>
              <div className="preview-card">
                <span className="label">Negative</span>
                <strong>{overview ? `${Number(overview.negative_reviews_percentage || 0).toFixed(1)}%` : '—'}</strong>
              </div>
            </div>

            <div className="preview-card">
              <span className="label">Positive</span>
              <strong>{overview ? `${Number(overview.positive_reviews_percentage || 0).toFixed(1)}%` : '—'}</strong>
            </div>
          </motion.div>
        </div>
      </motion.section>

      <section className="section">
        <div className="section-header"><div><p className="eyebrow muted">Discover</p><h3>Explore the stored catalog</h3></div><Link to="/products" className="ghost-button">All products</Link></div>
        <div className="category-grid">
          {categories.map((category) => <Link key={category} className="category-item" to={`/products?category=${encodeURIComponent(category)}`}>
            <span>{category}</span>
            <strong>{catalog.filter((product) => product.category === category).length}</strong>
          </Link>)}
        </div>
      </section>

      <section className="discovery-columns">
        <div className="table-panel">
          <div className="section-header"><div><p className="eyebrow muted">By review volume</p><h3>Most reviewed</h3></div></div>
          {mostReviewed.length ? <div className="discovery-list">{mostReviewed.map((product) => <Link key={product.id} to={`/products/${product.id}`} className="discovery-row"><span>{product.name}</span><span>{product.total_reviews} reviews</span></Link>)}</div> : <p className="empty-state">No reviewed products in the catalog.</p>}
        </div>
        <div className="table-panel">
          <div className="section-header"><div><p className="eyebrow muted">By stored rating</p><h3>Highly rated</h3></div></div>
          {highlyRated.length ? <div className="discovery-list">{highlyRated.map((product) => <Link key={product.id} to={`/products/${product.id}`} className="discovery-row"><span>{product.name}</span><span>{Number(product.average_rating).toFixed(1)} / 5 · {product.total_reviews} reviews</span></Link>)}</div> : <p className="empty-state">No rated products in the catalog.</p>}
        </div>
      </section>

      <section className="discovery-columns">
        <div className="table-panel"><p className="eyebrow muted">Sentiment movement</p><h3>Rising and falling sentiment</h3><p className="empty-state">Insufficient comparable historical snapshots to identify a rise or fall.</p></div>
        <div className="table-panel"><p className="eyebrow muted">Price discovery</p><h3>Price opportunities</h3><p className="empty-state">No current source price observations are available.</p><Link to="/products" className="ghost-button">Browse catalog</Link></div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow muted">Capabilities</p>
            <h3>Built for modern product teams</h3>
          </div>
        </div>

        <div className="card-grid">
          {features.map(({ icon: Icon, title, description }) => (
            <motion.article key={title} className="card feature-card" whileHover={{ y: -3 }} transition={{ duration: 0.18 }}>
              <div className="icon-box">
                <Icon size={22} color="#b8c3ff" />
              </div>
              <h4>{title}</h4>
              <p>{description}</p>
            </motion.article>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow muted">Workflow</p>
            <h3>How it works</h3>
          </div>
        </div>

        <div className="steps">
          {steps.map((step, index) => (
            <div key={step} className="card step-card">
              <div className="step-number">{index + 1}</div>
              <strong>{step}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="section">
        <div className="section-header">
          <div>
            <p className="eyebrow muted">Technology</p>
            <h3>Stack built for intelligence</h3>
          </div>
        </div>

        <div className="tech-grid">
          {tech.map((item) => (
            <div key={item} className="tech-pill">
              {item}
            </div>
          ))}
        </div>
      </section>

      <section className="cta-panel card">
        <div>
          <p className="eyebrow muted">Start today</p>
          <h3>Start analyzing customer voice</h3>
          <p>Transform recorded feedback into product decisions with explainable sentiment analysis.</p>
        </div>
        <Link to="/search" className="primary-button">
          Analyze Products <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  )
}

export default LandingPage

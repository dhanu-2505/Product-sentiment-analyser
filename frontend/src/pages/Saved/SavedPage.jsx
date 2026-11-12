import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, Trash2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { getWatchlist, removeSavedProduct } from '../../services/api'

function SavedPage() {
  const { token } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchSaved = async () => {
      try {
        const response = await getWatchlist(token)
        setItems(response.data.items || [])
      } catch (requestError) {
        setError(requestError?.response?.data?.detail || 'Unable to load your watchlist.')
      } finally {
        setLoading(false)
      }
    }

    fetchSaved()
  }, [])

  const removeItem = async (savedId) => {
    setError('')
    try {
      await removeSavedProduct(savedId, token)
      setItems((current) => current.filter((item) => item.id !== savedId))
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to remove this product.')
    }
  }

  if (loading) {
    return <div className="page"><div className="loading-grid"><div className="skeleton-line large" /><div className="skeleton-card" /></div></div>
  }

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">Watchlist</p>
          <h2>Products you follow</h2>
        </div>
        <Bookmark size={20} />
      </div>

      {error && <div className="error-state" role="alert"><p>{error}</p></div>}

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>No saved products yet</h3>
          <p>Save a product from its analysis page to add it to your watchlist.</p>
          <Link to="/analyze" className="primary-button">Find a product</Link>
        </div>
      ) : (
        <div className="card-grid">
          {items.map((item) => (
            <div key={item.id} className="feature-card card">
              <h4>{item.product_name}</h4>
              <p className="muted">{item.brand || 'Brand unavailable'} · {item.category || 'Category unavailable'}</p>
              <p>Rating {item.average_rating || 'Unavailable'} · Price unavailable</p>
              <p className="muted">Saved {item.saved_at ? new Date(item.saved_at).toLocaleDateString() : '—'}</p>
              <div className="hero-actions">
                <Link to={`/products/${item.product_id}`} className="ghost-button">Open analysis</Link>
                <button className="icon-button" type="button" onClick={() => removeItem(item.id)} title="Remove from watchlist" aria-label={`Remove ${item.product_name} from watchlist`}><Trash2 size={16} /></button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SavedPage

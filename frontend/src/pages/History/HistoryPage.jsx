import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Trash2 } from 'lucide-react'

import { clearHistory, getHistory } from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

function HistoryPage() {
  const navigate = useNavigate()
  const { token } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const response = await getHistory(token)
        setItems(response.data.items || [])
      } catch (err) {
        setError(err?.response?.data?.detail || 'Unable to load analysis history')
      } finally {
        setLoading(false)
      }
    }

    fetchHistory()
  }, [token])

  const handleClear = async () => {
    setError('')
    try {
      await clearHistory(token)
      setItems([])
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to clear search history.')
    }
  }

  if (loading) {
    return (
      <div className="page">
        <div className="loading-grid">
          <div className="skeleton-line large" />
          <div className="skeleton-card" />
          <div className="skeleton-card" />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="page">
        <div className="error-state">
          <h3>Unable to load history</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">History</p>
          <h2>Search history</h2>
        </div>
        <button className="ghost-button" type="button" onClick={handleClear} disabled={items.length === 0} title="Clear your search history"><Trash2 size={16} /> Clear history</button>
      </div>

      {items.length === 0 ? (
        <div className="empty-state">
          <h3>No product analysis yet</h3>
          <p>Search a product to create your first sentiment dashboard.</p>
        </div>
      ) : (
        <div className="table-panel">
          <div className="table-wrap">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Product</th>
                  <th>Platform</th>
                  <th>Reviews</th>
                  <th>Positive %</th>
                  <th>Neutral %</th>
                  <th>Negative %</th>
                  <th>Avg rating</th>
                  <th>Date</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} onClick={() => item.product_id && navigate(`/products/${item.product_id}`)} style={{ cursor: item.product_id ? 'pointer' : 'default' }}>
                    <td>{item.product_name}</td>
                    <td>{item.platform}</td>
                    <td>{item.total_reviews}</td>
                    <td>{Number(item.positive_percentage || 0).toFixed(1)}%</td>
                    <td>{Number(item.neutral_percentage || 0).toFixed(1)}%</td>
                    <td>{Number(item.negative_percentage || 0).toFixed(1)}%</td>
                    <td>{Number(item.average_rating || 0).toFixed(1)}</td>
                    <td>{item.analyzed_at ? new Date(item.analyzed_at).toLocaleDateString() : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}

export default HistoryPage

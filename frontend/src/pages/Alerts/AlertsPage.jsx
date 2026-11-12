import { useEffect, useState } from 'react'
import { Bell, Check } from 'lucide-react'
import { Link } from 'react-router-dom'
import { useAuth } from '../../contexts/AuthContext'
import { getAlerts, markAlertRead } from '../../services/api'

function AlertsPage() {
  const { token } = useAuth()
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState(null)

  const refresh = async () => {
    const response = await getAlerts(token)
    setItems(response.data.items || [])
  }

  useEffect(() => {
    refresh()
      .catch((requestError) => setError(requestError?.response?.data?.detail || 'Unable to load alerts.'))
      .finally(() => setLoading(false))
  }, [token])

  const markRead = async (alertId) => {
    setBusyId(alertId)
    setError('')
    try {
      await markAlertRead(alertId, token)
      setItems((current) => current.map((item) => item.id === alertId ? { ...item, is_read: true } : item))
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to update this alert.')
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <main className="page"><div className="loading-grid"><div className="skeleton-line large" /><div className="skeleton-card" /></div></main>

  return (
    <main className="page">
      <header className="section-header"><div><p className="eyebrow muted">Notifications</p><h2>Sentiment alerts</h2></div><Bell size={20} /></header>
      {error && <div className="error-state" role="alert"><p>{error}</p></div>}
      {items.length === 0 ? <div className="empty-state"><h3>No stored alerts</h3><p>Alerts appear here only when a monitored change has actually been recorded.</p></div> : (
        <div className="table-panel">
          <div className="table-wrap"><table className="data-table">
            <thead><tr><th>Alert</th><th>Product</th><th>Recorded</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>{items.map((item) => <tr key={item.id}>
              <td><strong>{item.alert_type.replaceAll('_', ' ')}</strong><p>{item.message}</p></td>
              <td><Link to={`/products/${item.product_id}`}>{item.product_name}</Link></td>
              <td>{item.created_at ? new Date(item.created_at).toLocaleString() : 'Unknown'}</td>
              <td>{item.is_read ? 'Read' : 'Unread'}</td>
              <td><button className="icon-button" type="button" onClick={() => markRead(item.id)} disabled={item.is_read || busyId === item.id} title={item.is_read ? 'Already read' : 'Mark as read'} aria-label="Mark alert as read"><Check size={16} /></button></td>
            </tr>)}</tbody>
          </table></div>
        </div>
      )}
    </main>
  )
}

export default AlertsPage

import { Link } from 'react-router-dom'

function NotFoundPage() {
  return (
    <div className="page" style={{ display: 'grid', placeItems: 'center', minHeight: '70vh' }}>
      <div className="card" style={{ padding: '40px 32px', textAlign: 'center', maxWidth: 520 }}>
        <p className="eyebrow muted">404</p>
        <h2 style={{ marginTop: 12, marginBottom: 8 }}>Page not found</h2>
        <p style={{ color: '#c7d2eb', marginBottom: 20 }}>
          The resource you requested is unavailable or was moved.
        </p>
        <Link to="/" className="primary-button">Return home</Link>
      </div>
    </div>
  )
}

export default NotFoundPage

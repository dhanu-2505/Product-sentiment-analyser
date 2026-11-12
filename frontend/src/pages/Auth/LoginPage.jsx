import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { LockKeyhole, Mail, Sparkles } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { getApiErrorMessage, loginUser } from '../../services/api'

function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ email: 'demo@reviewlens.ai', password: 'demo123' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await loginUser({ email: form.email, password: form.password })
      login(response.data.token, {
        id: response.data.id,
        name: response.data.name,
        email: response.data.email,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to sign in'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <div className="auth-panel auth-brand-panel">
          <div className="brand-mark auth-mark">
            <Sparkles size={20} />
          </div>
          <p className="eyebrow muted">ReviewLens</p>
          <h1>Product Intelligence from Customer Reviews</h1>
          <p>
            Turn customer feedback into product decisions with faster sentiment analysis,
            smarter comparisons, and executive-ready reports.
          </p>
          <ul className="auth-points">
            <li>Product search with explicit data provenance</li>
            <li>Theme discovery across customer reviews</li>
            <li>Watchlists, alerts, and comparisons</li>
          </ul>
        </div>

        <div className="auth-panel auth-form-panel">
          <div className="auth-header">
            <p className="eyebrow muted">Welcome back</p>
            <h2>Login to your workspace</h2>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <label className="auth-field">
              <span>Email</span>
              <div className="input-with-icon">
                <Mail size={16} />
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                  placeholder="you@company.com"
                  required
                />
              </div>
            </label>

            <label className="auth-field">
              <span>Password</span>
              <div className="input-with-icon">
                <LockKeyhole size={16} />
                <input
                  type="password"
                  value={form.password}
                  onChange={(event) => setForm((current) => ({ ...current, password: event.target.value }))}
                  placeholder="••••••••"
                  required
                />
              </div>
            </label>

            {error ? <div className="auth-error">{error}</div> : null}

            <button type="submit" className="primary-button auth-submit" disabled={loading}>
              {loading ? 'Signing in...' : 'Sign in'}
            </button>
          </form>

          <p className="auth-footer">
            Need an account? <Link to="/register">Create one</Link>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { UserRound, LockKeyhole, Mail } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { getApiErrorMessage, registerUser } from '../../services/api'

function RegisterPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [form, setForm] = useState({ name: '', email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = async (event) => {
    event.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await registerUser(form)
      login(response.data.token, {
        id: response.data.id,
        name: response.data.name,
        email: response.data.email,
      })
      navigate('/dashboard')
    } catch (err) {
      setError(getApiErrorMessage(err, 'Unable to create your account'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-shell">
        <div className="auth-panel auth-form-panel">
          <div className="auth-header">
            <p className="eyebrow muted">Create account</p>
            <h2>Launch your product intelligence workspace</h2>
          </div>

          <form onSubmit={handleSubmit} className="auth-form">
            <label className="auth-field">
              <span>Full name</span>
              <div className="input-with-icon">
                <UserRound size={16} />
                <input
                  type="text"
                  value={form.name}
                  onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))}
                  placeholder="Alex Morgan"
                  required
                />
              </div>
            </label>

            <label className="auth-field">
              <span>Email</span>
              <div className="input-with-icon">
                <Mail size={16} />
                <input
                  type="email"
                  value={form.email}
                  onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))}
                  placeholder="alex@reviewlens.ai"
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
                  placeholder="Create a secure password"
                  required
                />
              </div>
            </label>

            {error ? <div className="auth-error">{error}</div> : null}

            <button type="submit" className="primary-button auth-submit" disabled={loading}>
              {loading ? 'Creating account...' : 'Create account'}
            </button>
          </form>

          <p className="auth-footer">
            Already have an account? <Link to="/login">Log in</Link>
          </p>
        </div>

        <div className="auth-panel auth-brand-panel">
          <p className="eyebrow muted">Why teams switch</p>
          <h1>From scattered feedback to clear product direction.</h1>
          <p>
            ReviewLens helps product teams summarize sentiment, compare product stories,
            and flag what customers care about before issues turn into churn.
          </p>
          <div className="auth-metric-grid">
            <div className="mini-stat"><strong>74%</strong><span>Positive sentiment</span></div>
            <div className="mini-stat"><strong>3.2x</strong><span>Faster triage</span></div>
            <div className="mini-stat"><strong>40+</strong><span>Insight reports</span></div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage

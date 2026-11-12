import { useEffect, useState } from 'react'
import { Save, UserRound } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { getProfile, updateProfile } from '../../services/api'

function ProfilePage() {
  const { token, user, login } = useAuth()
  const [profile, setProfile] = useState(null)
  const [form, setForm] = useState({ name: '', email: '' })
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')

  useEffect(() => {
    getProfile(token)
      .then((response) => {
        setProfile(response.data)
        setForm({ name: response.data.name, email: response.data.email })
      })
      .catch((requestError) => setError(requestError?.response?.data?.detail || 'Unable to load profile.'))
      .finally(() => setLoading(false))
  }, [token])

  const save = async (event) => {
    event.preventDefault()
    setSaving(true)
    setError('')
    setNotice('')
    try {
      const response = await updateProfile(form, token)
      login(token, { ...user, ...response.data })
      setProfile((current) => ({ ...current, ...response.data }))
      setNotice('Profile updated.')
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || 'Unable to update profile.')
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <main className="page"><div className="loading-grid"><div className="skeleton-line large" /><div className="skeleton-card" /></div></main>

  return (
    <main className="page">
      <header className="section-header"><div><p className="eyebrow muted">Account</p><h2>Your profile</h2></div><UserRound size={20} /></header>
      {error && <div className="error-state" role="alert"><p>{error}</p></div>}
      {notice && <p className="success-message" role="status">{notice}</p>}
      <section className="table-panel">
        <form className="auth-form" onSubmit={save}>
          <label className="auth-field"><span>Name</span><input className="field" value={form.name} onChange={(event) => setForm((current) => ({ ...current, name: event.target.value }))} required /></label>
          <label className="auth-field"><span>Email</span><input className="field" type="email" value={form.email} onChange={(event) => setForm((current) => ({ ...current, email: event.target.value }))} required /></label>
          <p className="muted">Account created {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : 'date unavailable'}</p>
          <button className="primary-button" type="submit" disabled={saving}><Save size={16} /> {saving ? 'Saving...' : 'Save profile'}</button>
        </form>
      </section>
      <section className="kpi-grid">
        <div className="kpi-card"><span className="label">Watchlist</span><strong>{profile?.saved_product_count ?? 0}</strong></div>
        <div className="kpi-card"><span className="label">Searches</span><strong>{profile?.search_count ?? 0}</strong></div>
        <div className="kpi-card"><span className="label">Reports generated</span><strong>{profile?.report_count ?? 0}</strong></div>
      </section>
    </main>
  )
}

export default ProfilePage

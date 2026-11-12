import { useState } from 'react'

function SettingsPage() {
  const [email, setEmail] = useState('demo@sentiLens.ai')
  const [theme, setTheme] = useState('dark')

  return (
    <div className="page">
      <div className="section-header">
        <div>
          <p className="eyebrow muted">Settings</p>
          <h3>Workspace preferences</h3>
        </div>
      </div>

      <div className="table-panel" style={{ maxWidth: 720 }}>
        <div className="field-group">
          <label className="eyebrow muted">Workspace email</label>
          <input className="field" value={email} onChange={(event) => setEmail(event.target.value)} />
        </div>

        <div className="field-group" style={{ marginTop: 18 }}>
          <label className="eyebrow muted">Theme</label>
          <select className="select-field" value={theme} onChange={(event) => setTheme(event.target.value)}>
            <option value="dark">Dark</option>
            <option value="light">Light</option>
            <option value="midnight">Midnight</option>
          </select>
        </div>

        <div style={{ marginTop: 24 }}>
          <button className="primary-button">Save preferences</button>
        </div>
      </div>
    </div>
  )
}

export default SettingsPage

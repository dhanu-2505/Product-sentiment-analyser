import { Link, Outlet, NavLink, useNavigate } from 'react-router-dom'
import { BarChart3, Bell, ChartColumnBig, History, Search, Settings, Sparkles, Bookmark, FileText, Menu, X, LogOut, UserRound } from 'lucide-react'
import { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'

const navItems = [
  { label: 'Home', to: '/', icon: Sparkles },
  { label: 'Search', to: '/search', icon: Search },
  { label: 'Compare', to: '/compare', icon: ChartColumnBig },
  { label: 'Saved', to: '/saved', icon: Bookmark },
  { label: 'Alerts', to: '/alerts', icon: Bell },
  { label: 'Profile', to: '/profile', icon: UserRound },
  { label: 'Reports', to: '/reports', icon: FileText },
  { label: 'History', to: '/history', icon: History },
  { label: 'Settings', to: '/settings', icon: Settings },
]

function AppLayout() {
  const navigate = useNavigate()
  const [mobileOpen, setMobileOpen] = useState(false)
  const { user, logout } = useAuth()

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <aside className={`sidebar ${mobileOpen ? 'open' : ''}`}>
        <div className="brand-wrap">
          <div className="brand-mark">
            <BarChart3 size={18} />
          </div>
          <div>
            <p className="eyebrow muted">Product intelligence</p>
            <h3>ReviewLens</h3>
          </div>
        </div>

        <nav className="sidebar-nav">
          {navItems.map(({ label, to, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={() => setMobileOpen(false)}
            >
              <Icon size={18} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <button className="nav-item sidebar-logout" type="button" onClick={handleLogout}>
          <LogOut size={18} />
          <span>Logout</span>
        </button>
      </aside>

      <div className="content-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button className="menu-button" onClick={() => setMobileOpen(!mobileOpen)}>
              {mobileOpen ? <X size={18} /> : <Menu size={18} />}
            </button>
            <div>
              <p className="eyebrow muted">Overview</p>
              <h2>Customer feedback intelligence</h2>
            </div>
          </div>

          <div className="topbar-actions">
            <div className="user-pill">
              <span className="user-badge">{user?.name?.charAt(0)?.toUpperCase() || 'R'}</span>
              <span>{user?.name || 'ReviewLens user'}</span>
            </div>
            <button className="ghost-button" type="button" onClick={handleLogout}>
              <LogOut size={16} />
              Logout
            </button>
            <Link className="primary-button" to="/search">Analyze product</Link>
          </div>
        </header>

        <main className="page-shell">
          <Outlet />
        </main>
      </div>
    </div>
  )
}

export default AppLayout

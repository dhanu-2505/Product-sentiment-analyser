import { Routes, Route } from 'react-router-dom'
import LandingPage from './pages/Landing/LandingPage'
import LoginPage from './pages/Auth/LoginPage'
import RegisterPage from './pages/Auth/RegisterPage'
import SearchPage from './pages/Search/SearchPage'
import ExplorerPage from './pages/Explorer/ExplorerPage'
import DashboardPage from './pages/Dashboard/DashboardPage'
import ReviewsPage from './pages/Reviews/ReviewsPage'
import HistoryPage from './pages/History/HistoryPage'
import ComparePage from './pages/Compare/ComparePage'
import SavedPage from './pages/Saved/SavedPage'
import SettingsPage from './pages/Settings/SettingsPage'
import ReportsPage from './pages/Reports/ReportsPage'
import NotFoundPage from './pages/NotFound/NotFoundPage'
import SourceComparisonPage from './pages/Sources/SourceComparisonPage'
import AlertsPage from './pages/Alerts/AlertsPage'
import ProfilePage from './pages/Profile/ProfilePage'
import AppLayout from './layouts/AppLayout'
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/search" element={<SearchPage />} />
        <Route path="/analyze" element={<SearchPage />} />
        <Route path="/products" element={<ExplorerPage />} />
        <Route path="/explorer" element={<ExplorerPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard/:productId" element={<DashboardPage />} />
        <Route path="/products/:productId" element={<DashboardPage />} />
        <Route path="/products/:productId/sources" element={<SourceComparisonPage />} />
        <Route path="/reviews/:productId" element={<ReviewsPage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/compare" element={<ComparePage />} />
        <Route path="/saved" element={<SavedPage />} />
        <Route path="/watchlist" element={<SavedPage />} />
        <Route path="/alerts" element={<AlertsPage />} />
        <Route path="/profile" element={<ProfilePage />} />
        <Route path="/reports" element={<ReportsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

export default App

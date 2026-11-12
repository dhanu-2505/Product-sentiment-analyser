import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8001',
  timeout: 15000,
})

export const getApiErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (Array.isArray(detail)) return detail.map((issue) => issue.msg).join(' ')
  if (typeof detail === 'string') return detail
  if (!error?.response) {
    return `Cannot reach the ReviewLens API at ${api.defaults.baseURL}. Check that the backend is running.`
  }
  return `${fallback} (HTTP ${error.response.status}).`
}

export const getHealth = () => api.get('/health')
export const getSources = () => api.get('/api/sources')
export const getDashboardOverview = () => api.get('/api/dashboard/overview')
export const getProducts = (params = {}) => api.get('/api/products', { params })
export const getSearchSuggestions = (query) => api.get('/api/products/search-suggestions', { params: { query } })
export const searchProduct = (payload, token) => api.post('/api/products/search', payload, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined)
export const getProduct = (productId) => api.get(`/api/products/${productId}`)
export const getProductReviews = (productId, params = {}) => api.get(`/api/products/${productId}/reviews`, { params })
export const getReviewQuality = (productId, params = {}) => api.get(`/api/products/${productId}/review-quality`, { params })
export const getProductSources = (productId) => api.get(`/api/products/${productId}/sources`)
export const getAnalytics = (productId, params = {}) => api.get(`/api/products/${productId}/analytics`, { params })
export const getHistory = (token) => api.get('/api/history', { headers: { Authorization: `Bearer ${token}` } })
export const clearHistory = (token) => api.delete('/api/history', { headers: { Authorization: `Bearer ${token}` } })
export const registerUser = (payload) => api.post('/api/auth/register', payload)
export const loginUser = (payload) => api.post('/api/auth/login', payload)
export const getCurrentUser = (token) => api.get('/api/auth/me', { headers: { Authorization: `Bearer ${token}` } })
export const getProfile = (token) => api.get('/api/profile', { headers: { Authorization: `Bearer ${token}` } })
export const updateProfile = (payload, token) => api.put('/api/profile', payload, { headers: { Authorization: `Bearer ${token}` } })
export const saveProduct = (payload, token) => api.post('/api/saved-products', payload, { headers: { Authorization: `Bearer ${token}` } })
export const getSavedProducts = (token) => api.get('/api/saved-products', { headers: { Authorization: `Bearer ${token}` } })
export const compareProducts = (payload) => api.post('/api/compare', payload)
export const getReports = (token) => api.get('/api/reports', { headers: { Authorization: `Bearer ${token}` } })
export const getReport = (reportId, token) => api.get(`/api/reports/${reportId}`, { headers: { Authorization: `Bearer ${token}` } })
export const downloadReport = (reportId, token) => api.get(`/api/reports/${reportId}/download`, { headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' })
export const exportCsv = (dataType, params, token) => api.get(`/api/exports/${dataType}.csv`, { params, headers: { Authorization: `Bearer ${token}` }, responseType: 'blob' })
export const getAlerts = (token) => api.get('/api/alerts', { headers: { Authorization: `Bearer ${token}` } })
export const markAlertRead = (alertId, token) => api.post(`/api/alerts/${alertId}/read`, {}, { headers: { Authorization: `Bearer ${token}` } })
export const getWatchlist = (token) => api.get('/api/watchlist', { headers: { Authorization: `Bearer ${token}` } })
export const removeSavedProduct = (savedId, token) => api.delete(`/api/saved-products/${savedId}`, { headers: { Authorization: `Bearer ${token}` } })
export const generateReport = (payload, token) => api.post('/api/reports', payload, { headers: { Authorization: `Bearer ${token}` } })

export default api

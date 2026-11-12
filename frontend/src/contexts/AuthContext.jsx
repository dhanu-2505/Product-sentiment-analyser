import { createContext, useContext, useMemo, useState } from 'react'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [token, setToken] = useState(() => localStorage.getItem('reviewlens-token') || '')
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem('reviewlens-user')
    return storedUser ? JSON.parse(storedUser) : null
  })

  const login = (nextToken, nextUser) => {
    localStorage.setItem('reviewlens-token', nextToken)
    localStorage.setItem('reviewlens-user', JSON.stringify(nextUser))
    setToken(nextToken)
    setUser(nextUser)
  }

  const logout = () => {
    localStorage.removeItem('reviewlens-token')
    localStorage.removeItem('reviewlens-user')
    setToken('')
    setUser(null)
  }

  const value = useMemo(() => ({ token, user, login, logout }), [token, user])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)

  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }

  return context
}

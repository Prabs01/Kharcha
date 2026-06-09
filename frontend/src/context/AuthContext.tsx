import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { clearStoredToken, getStoredToken, setStoredToken } from '../api/client'
import { getCurrentUser, loginUser, loginWithGoogle, registerUser } from '../api/users'
import type { User, UserCreate } from '../api/types'

interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: (credential: string) => Promise<void>
  register: (data: UserCreate) => Promise<void>
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = getStoredToken()
    if (!token) {
      setLoading(false)
      return
    }

    getCurrentUser()
      .then(setUser)
      .catch(() => clearStoredToken())
      .finally(() => setLoading(false))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const token = await loginUser(email, password)
    setStoredToken(token.access_token)
    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }, [])

  const loginWithGoogleCallback = useCallback(async (credential: string) => {
    const token = await loginWithGoogle(credential)
    setStoredToken(token.access_token)
    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }, [])

  const register = useCallback(async (data: UserCreate) => {
    await registerUser(data)
    await login(data.email, data.password)
  }, [login])

  const logout = useCallback(() => {
    clearStoredToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({ user, loading, login, loginWithGoogle: loginWithGoogleCallback, register, logout }),
    [user, loading, login, loginWithGoogleCallback, register, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}

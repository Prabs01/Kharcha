import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import {
  clearStoredToken,
  getStoredToken,
  setStoredToken,
} from '../api/client'
import {
  getCurrentUser,
  loginUser,
  loginWithGoogle,
  registerUser,
} from '../api/users'
import type { User, UserCreate } from '../api/types'
import { AuthContext } from './useAuth'

export interface AuthContextValue {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void>
  loginWithGoogle: (credential: string) => Promise<void>
  register: (data: UserCreate) => Promise<void>
  logout: () => void
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      const token = getStoredToken()

      if (!token) {
        setUser(null)
        setLoading(false)
        return
      }

      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch {
        clearStoredToken()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    initAuth()
  }, [])

  useEffect(() => {
    const syncAuthAcrossTabs = async (e: StorageEvent) => {
      if (e.key !== 'token') return

      const token = getStoredToken()

      if (!token) {
        setUser(null)
        setLoading(false)
        return
      }

      setLoading(true)

      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch {
        clearStoredToken()
        setUser(null)
      } finally {
        setLoading(false)
      }
    }

    window.addEventListener('storage', syncAuthAcrossTabs)
    return () => window.removeEventListener('storage', syncAuthAcrossTabs)
  }, [])

  useEffect(() => {
    const onFocus = async () => {
      const token = getStoredToken()
      if (!token) return

      try {
        const currentUser = await getCurrentUser()
        setUser(currentUser)
      } catch {
        clearStoredToken()
        setUser(null)
      }
    }

    window.addEventListener('focus', onFocus)
    return () => window.removeEventListener('focus', onFocus)
  }, [])


  const login = useCallback(async (email: string, password: string) => {
    const token = await loginUser(email, password)

    setStoredToken(token.access_token)

    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }, [])


  const loginWithGoogleCallback = useCallback(async (credential: string) => {
    const token = await loginWithGoogle({ token: credential })

    setStoredToken(token.access_token)

    const currentUser = await getCurrentUser()
    setUser(currentUser)
  }, [])


  const register = useCallback(
    async (data: UserCreate) => {
      await registerUser(data)
      await login(data.email, data.password)
    },
    [login],
  )

  const logout = useCallback(() => {
    clearStoredToken()
    setUser(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      loading,
      login,
      loginWithGoogle: loginWithGoogleCallback,
      register,
      logout,
    }),
    [user, loading, login, loginWithGoogleCallback, register, logout],
  )

  return (
    <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
  )
}
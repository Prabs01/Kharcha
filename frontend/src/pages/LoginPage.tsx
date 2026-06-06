import { useState, type FormEvent } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { getErrorMessage } from '../api/client'
import { useAuth } from '../context/AuthContext'
import { Logo } from '../components/Logo'

export function LoginPage() {
  const { user, login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  if (user) return <Navigate to="/" replace />

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await login(email, password)
    } catch (err) {
      setError(getErrorMessage(err))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-brand-panel">
        <Logo height={52} variant="dark" showTagline />
        <p className="auth-slogan">Split the bill, not the bond.</p>
        <p className="auth-nepali">खर्च — Kharcha</p>
      </aside>

      <div className="auth-card">
        <div className="auth-header">
          <h1>Welcome back</h1>
          <p>Sign in to manage shared expenses</p>
        </div>

        <form className="form" onSubmit={handleSubmit}>
          {error && <div className="alert alert-error">{error}</div>}

          <label className="field">
            <span>Email</span>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </label>

          <label className="field">
            <span>Password</span>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              autoComplete="current-password"
            />
          </label>

          <button type="submit" className="btn btn-primary btn-full" disabled={submitting}>
            {submitting ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="auth-footer">
          No account? <Link to="/register">Create one</Link>
        </p>
      </div>
    </div>
  )
}

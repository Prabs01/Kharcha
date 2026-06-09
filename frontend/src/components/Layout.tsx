import { Link, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/useAuth'
import { Logo } from './Logo'

export function Layout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Link to="/" className="brand">
          <Logo height={30} />
        </Link>
        <div className="header-actions">
          {user && <span className="user-greeting">Hi, {user.name}</span>}
          <button type="button" className="btn btn-ghost" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>
      <main className="app-main">
        <Outlet />
      </main>
    </div>
  )
}

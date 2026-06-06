import logoDark from '../assets/logo-dark.svg'
import logoLight from '../assets/logo-light.svg'
import logoMark from '../assets/logo-mark.svg'

const LOGO_ASPECT = 200 / 60
const MARK_ASPECT = 56 / 58

interface LogoMarkProps {
  height?: number
  className?: string
}

export function LogoMark({ height = 32, className }: LogoMarkProps) {
  return (
    <img
      src={logoMark}
      alt=""
      width={height * MARK_ASPECT}
      height={height}
      className={className}
      aria-hidden
    />
  )
}

interface LogoProps {
  height?: number
  variant?: 'light' | 'dark'
  showTagline?: boolean
  className?: string
}

export function Logo({
  height = 32,
  variant = 'light',
  showTagline = false,
  className,
}: LogoProps) {
  const src = variant === 'dark' ? logoDark : logoLight

  return (
    <div className={`logo-lockup ${className ?? ''}`}>
      <img
        src={src}
        alt="kharcha"
        width={height * LOGO_ASPECT}
        height={height}
        className="logo-img"
      />
      {showTagline && (
        <span className={`logo-tagline ${variant}`}>split smart</span>
      )}
    </div>
  )
}

import { NPR_SYMBOL } from '../lib/currency'

interface CurrencyAmountProps {
  amount: number
  className?: string
  showPlus?: boolean
}

export function CurrencyAmount({
  amount,
  className,
  showPlus = false,
}: CurrencyAmountProps) {
  const negative = amount < 0
  const value = new Intl.NumberFormat('en-NP', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount))

  const prefix = negative ? '-' : showPlus && amount > 0 ? '+' : ''

  return (
    <span className={`amount ${className ?? ''}`}>
      {prefix}
      <span className="npr-logo" aria-label="Nepali Rupees">
        {NPR_SYMBOL}
      </span>
      <span className="npr-value">{value}</span>
    </span>
  )
}

/** Nepali Rupee — रू */
export const NPR_SYMBOL = 'रू'

export function formatCurrency(amount: number): string {
  const sign = amount < 0 ? '-' : ''
  const formatted = new Intl.NumberFormat('en-NP', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(Math.abs(amount))

  return `${sign}${NPR_SYMBOL}\u00a0${formatted}`
}

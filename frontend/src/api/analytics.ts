import { api } from './client'
import type { Balance, Settlement, SuggestedSettlement } from './types'

const api_url: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function getGroupBalances(
  groupId: number,
): Promise<{ group_id: number; balances: Balance[] }> {
  const res = await api.get(`${api_url}/groups/${groupId}/balances`)
  return res.data
}

export async function getSuggestedSettlements(
  groupId: number,
): Promise<{ group_id: number; settlements: SuggestedSettlement[] }> {
  const res = await api.get(`${api_url}/groups/${groupId}/settlements/suggested`)
  return res.data
}

export async function listSettlements(
  groupId: number,
): Promise<{ group_id: number; settlements: Settlement[] }> {
  const res = await api.get(`${api_url}/groups/${groupId}/settlements`)
  return res.data
}

export async function recordSettlement(
  groupId: number,
  data: { from_user_id: number; to_user_id: number; amount: number },
): Promise<Settlement> {
  const res = await api.post(`${api_url}/groups/${groupId}/settlements`, data)
  return res.data
}

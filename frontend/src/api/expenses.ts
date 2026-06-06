import { api } from './client'
import type { Expense, ExpenseCreate, ExpenseSplit } from './types'

const api_url: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function listExpenses(groupId: number): Promise<Expense[]> {
  const res = await api.get<Expense[]>(`${api_url}/groups/${groupId}/expenses`)
  return res.data
}

export async function createExpense(
  groupId: number,
  data: ExpenseCreate,
): Promise<Expense> {
  const res = await api.post<Expense>(`${api_url}/groups/${groupId}/expenses`, data)
  return res.data
}

export async function deleteExpense(
  groupId: number,
  expenseId: number,
): Promise<void> {
  await api.delete(`${api_url}/groups/${groupId}/expenses/${expenseId}`)
}

export async function listExpenseSplits(
  groupId: number,
  expenseId: number,
): Promise<ExpenseSplit[]> {
  const res = await api.get<ExpenseSplit[]>(
    `${api_url}/groups/${groupId}/expenses/${expenseId}/splits`,
  )
  return res.data
}

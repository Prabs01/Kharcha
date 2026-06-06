import { api } from './client'
import type { Expense, ExpenseCreate, ExpenseSplit } from './types'

export async function listExpenses(groupId: number): Promise<Expense[]> {
  const res = await api.get<Expense[]>(`/groups/${groupId}/expenses`)
  return res.data
}

export async function createExpense(
  groupId: number,
  data: ExpenseCreate,
): Promise<Expense> {
  const res = await api.post<Expense>(`/groups/${groupId}/expenses`, data)
  return res.data
}

export async function deleteExpense(
  groupId: number,
  expenseId: number,
): Promise<void> {
  await api.delete(`/groups/${groupId}/expenses/${expenseId}`)
}

export async function listExpenseSplits(
  groupId: number,
  expenseId: number,
): Promise<ExpenseSplit[]> {
  const res = await api.get<ExpenseSplit[]>(
    `/groups/${groupId}/expenses/${expenseId}/splits`,
  )
  return res.data
}

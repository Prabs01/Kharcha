export interface User {
  id: number
  name: string
  email: string
}

export interface UserCreate {
  name: string
  email: string
  password: string
}

export interface Token {
  access_token: string
  token_type: string
}

export interface Group {
  id: number
  name: string
}

export interface GroupMember {
  id: number
  user: User
}

export interface Expense {
  id: number
  group: Group
  paid_by_user: User
  title: string
  total_amount: number
  created_at: string
}

export type SplitMethod = 'equal' | 'exact' | 'percentage'

export interface SplitParticipant {
  user_id: number
  percentage?: number
  amount?: number
}

export interface ExpenseCreate {
  paid_by_user_id: number
  title: string
  total_amount: number
  split_method?: SplitMethod
  split_participants?: SplitParticipant[]
}

export interface ExpenseSplit {
  id: number
  user: User
  amount_owed: number
  amount_paid: number
}

export interface Balance {
  user_id: number
  balance: number
}

export interface SuggestedSettlement {
  from_user_id: number
  to_user_id: number
  amount: number
}

export interface Settlement {
  id: number
  group_id: number
  from_user_id: number
  to_user_id: number
  amount: number
  status: string
  settled_at: string
}

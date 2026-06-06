import { api } from './client'
import type { Token, User, UserCreate } from './types'

export async function registerUser(data: UserCreate): Promise<User> {
  const res = await api.post<User>('/users/', data)
  return res.data
}

export async function loginUser(email: string, password: string): Promise<Token> {
  const params = new URLSearchParams()
  params.append('username', email)
  params.append('password', password)
  const res = await api.post<Token>('/users/token', params, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return res.data
}

export async function getCurrentUser(): Promise<User> {
  const res = await api.get<User>('/users/me')
  return res.data
}

export async function listUsers(): Promise<User[]> {
  const res = await api.get<User[]>('/users/')
  return res.data
}

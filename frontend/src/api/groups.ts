import { api } from './client'
import type { Group, GroupMember, User } from './types'

const api_url: string = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export async function listGroups(): Promise<Group[]> {
  const res = await api.get<Group[]>(`${api_url}/groups`)
  return res.data
}

export async function createGroup(name: string): Promise<Group> {
  const res = await api.post<Group>(`${api_url}/groups`, { name })
  return res.data
}

export async function getGroup(groupId: number): Promise<Group> {
  const res = await api.get<Group>(`${api_url}/groups/${groupId}`)
  return res.data
}

export async function deleteGroup(groupId: number): Promise<void> {
  await api.delete(`${api_url}/groups/${groupId}`)
}

export async function listGroupMembers(groupId: number): Promise<User[]> {
  const res = await api.get<User[]>(`${api_url}/groups/${groupId}/members`)
  return res.data
}

export async function addGroupMember(
  groupId: number,
  userId: number,
): Promise<GroupMember> {
  const res = await api.post<GroupMember>(`${api_url}/groups/${groupId}/members`, {
    user_id: userId,
  })
  return res.data
}

export async function removeGroupMember(
  groupId: number,
  userId: number,
): Promise<void> {
  await api.delete(`${api_url}/groups/${groupId}/members/${userId}`)
}

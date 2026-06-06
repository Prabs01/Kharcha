import { api } from './client'
import type { Group, GroupMember, User } from './types'

export async function listGroups(): Promise<Group[]> {
  const res = await api.get<Group[]>('/groups')
  return res.data
}

export async function createGroup(name: string): Promise<Group> {
  const res = await api.post<Group>('/groups', { name })
  return res.data
}

export async function getGroup(groupId: number): Promise<Group> {
  const res = await api.get<Group>(`/groups/${groupId}`)
  return res.data
}

export async function deleteGroup(groupId: number): Promise<void> {
  await api.delete(`/groups/${groupId}`)
}

export async function listGroupMembers(groupId: number): Promise<User[]> {
  const res = await api.get<User[]>(`/groups/${groupId}/members`)
  return res.data
}

export async function addGroupMember(
  groupId: number,
  userId: number,
): Promise<GroupMember> {
  const res = await api.post<GroupMember>(`/groups/${groupId}/members`, {
    user_id: userId,
  })
  return res.data
}

export async function removeGroupMember(
  groupId: number,
  userId: number,
): Promise<void> {
  await api.delete(`/groups/${groupId}/members/${userId}`)
}

import apiClient from './client'
import type { UserResponse, UserCreateRequest, UserUpdateRequest } from './types'

export async function getUsers(): Promise<UserResponse[]> {
  const res = await apiClient.get<UserResponse[]>('/api/admin/users')
  return res.data
}

export async function createUser(data: UserCreateRequest): Promise<UserResponse> {
  const res = await apiClient.post<UserResponse>('/api/admin/users', data)
  return res.data
}

export async function updateUser(userId: number, data: UserUpdateRequest): Promise<UserResponse> {
  const res = await apiClient.put<UserResponse>(`/api/admin/users/${userId}`, data)
  return res.data
}

export async function deleteUser(userId: number): Promise<void> {
  await apiClient.delete(`/api/admin/users/${userId}`)
}

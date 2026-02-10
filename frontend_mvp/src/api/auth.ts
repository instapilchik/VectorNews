import apiClient from './client'
import type { LoginRequest, LoginResponse, UserResponse } from './types'

export async function login(data: LoginRequest): Promise<LoginResponse> {
  const res = await apiClient.post<LoginResponse>('/api/auth/login', data)
  return res.data
}

export async function getMe(): Promise<UserResponse> {
  const res = await apiClient.get<UserResponse>('/api/auth/me')
  return res.data
}

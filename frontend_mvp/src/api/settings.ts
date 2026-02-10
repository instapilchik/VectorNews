import apiClient from './client'
import type { AgentSettings } from './types'

export async function getSettings(): Promise<AgentSettings> {
  const res = await apiClient.get<AgentSettings>('/api/agent/settings')
  return res.data
}

export async function updateSettings(data: AgentSettings): Promise<AgentSettings> {
  const res = await apiClient.put<AgentSettings>('/api/agent/settings', data)
  return res.data
}

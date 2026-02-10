import apiClient from './client'
import type { ChatRequest, ChatResponse } from './types'

export async function sendChatMessage(data: ChatRequest): Promise<ChatResponse> {
  const res = await apiClient.post<ChatResponse>('/api/agent/chat', data, {
    timeout: 60000,
  })
  return res.data
}

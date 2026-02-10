import apiClient from './client'
import type { HotTopic, ChatResponse, NewsCard, NewsCategory } from './types'

export async function getHotTopics(): Promise<HotTopic[]> {
  const res = await apiClient.get<HotTopic[]>('/api/dashboards/hot-topics')
  return res.data
}

export async function getDailyBriefing(): Promise<ChatResponse> {
  const res = await apiClient.get<ChatResponse>('/api/dashboards/daily-briefing')
  return res.data
}

export async function getThematicNews(
  category: NewsCategory,
  limit: number = 20,
): Promise<NewsCard[]> {
  const res = await apiClient.get<NewsCard[]>('/api/dashboards/thematic', {
    params: { category, limit },
  })
  return res.data
}

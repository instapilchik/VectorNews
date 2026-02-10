import apiClient from './client'
import type { NewsCard, NewsCategory } from './types'

export async function getRecentNews(params: {
  category?: NewsCategory
  limit?: number
  offset?: number
}): Promise<NewsCard[]> {
  const res = await apiClient.get<NewsCard[]>('/api/dashboards/thematic', {
    params: {
      category: params.category || 'Общее',
      limit: params.limit || 20,
    },
  })
  return res.data
}

import { ref, watch } from 'vue'
import { getRecentNews } from '@/api/news'
import type { NewsCard, NewsCategory } from '@/api/types'

export function useNewsFeed() {
  const items = ref<NewsCard[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  const category = ref<NewsCategory>('Общее')
  const hasMore = ref(true)

  const PAGE_SIZE = 20

  async function load(reset = false) {
    if (loading.value) return
    loading.value = true
    error.value = null

    if (reset) {
      items.value = []
      hasMore.value = true
    }

    try {
      const data = await getRecentNews({
        category: category.value,
        limit: PAGE_SIZE,
        offset: items.value.length,
      })
      items.value.push(...data)
      hasMore.value = data.length === PAGE_SIZE
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка загрузки новостей'
    } finally {
      loading.value = false
    }
  }

  function setCategory(cat: NewsCategory) {
    category.value = cat
  }

  watch(category, () => load(true))

  return { items, loading, error, category, hasMore, load, setCategory }
}

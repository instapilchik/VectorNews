<script setup lang="ts">
import { ref } from 'vue'
import type { HotTopic, NewsCard } from '@/api/types'
import { getNewsByIds } from '@/api/dashboards'
import NSpinner from '@/components/common/NSpinner.vue'

const props = defineProps<{
  topic: HotTopic
}>()

const expanded = ref(false)
const news = ref<NewsCard[]>([])
const loading = ref(false)

async function toggle() {
  expanded.value = !expanded.value
  if (expanded.value && news.value.length === 0) {
    loading.value = true
    try {
      news.value = await getNewsByIds(props.topic.news_ids)
    } catch {
      // silent
    } finally {
      loading.value = false
    }
  }
}

function relativeTime(dateStr: string): string {
  const diffMs = Date.now() - new Date(dateStr).getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  if (diffHours < 1) return 'менее часа назад'
  if (diffHours < 24) return `${diffHours}ч назад`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'вчера'
  return `${diffDays}д назад`
}
</script>

<template>
  <div class="card-hover cursor-pointer" @click="toggle">
    <div class="flex items-start justify-between">
      <h3 class="text-sm font-medium text-stone-900 dark:text-stone-50">
        {{ topic.title }}
      </h3>
      <div class="ml-2 flex items-center gap-2">
        <span class="flex-shrink-0 rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-600 dark:bg-stone-800 dark:text-stone-400">
          {{ topic.news_count }}
        </span>
        <svg
          class="h-4 w-4 text-stone-400 transition-transform duration-200"
          :class="{ 'rotate-180': expanded }"
          fill="none" viewBox="0 0 24 24" stroke="currentColor"
        >
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
        </svg>
      </div>
    </div>

    <div v-if="expanded" class="mt-3 space-y-2" @click.stop>
      <div v-if="loading" class="flex justify-center py-3">
        <NSpinner size="sm" />
      </div>
      <a
        v-for="item in news"
        :key="item.id"
        :href="item.tg_link"
        target="_blank"
        rel="noopener noreferrer"
        class="block rounded-md border border-stone-200 p-2.5 transition-base hover:border-stone-300 hover:bg-stone-50 dark:border-stone-700 dark:hover:border-stone-600 dark:hover:bg-stone-800"
      >
        <p class="text-xs font-medium text-stone-900 dark:text-stone-50">{{ item.title }}</p>
        <div class="mt-1 flex items-center gap-2 text-xs text-stone-400 dark:text-stone-500">
          <span>{{ item.source_channel }}</span>
          <span>&middot;</span>
          <span>{{ relativeTime(item.published_at) }}</span>
        </div>
      </a>
    </div>
  </div>
</template>

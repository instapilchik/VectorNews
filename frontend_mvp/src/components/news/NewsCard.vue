<script setup lang="ts">
import { computed } from 'vue'
import type { NewsCard } from '@/api/types'
import NBadge from '@/components/common/NBadge.vue'

const props = defineProps<{
  news: NewsCard
}>()

const relativeTime = computed(() => {
  const date = new Date(props.news.published_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) return 'менее часа назад'
  if (diffHours < 24) return `${diffHours}ч назад`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'вчера'
  return `${diffDays}д назад`
})

const importancePercent = computed(() => {
  if (!props.news.importance_score) return 0
  return Math.round(props.news.importance_score * 100)
})

const importanceColor = computed(() => {
  const score = props.news.importance_score ?? 0
  if (score >= 0.7) return 'bg-danger'
  if (score >= 0.4) return 'bg-warning'
  return 'bg-stone-300 dark:bg-stone-600'
})
</script>

<template>
  <a
    :href="news.tg_link"
    target="_blank"
    rel="noopener noreferrer"
    class="block rounded-card border border-stone-200 bg-white p-4 transition-base hover:border-stone-300 hover:shadow-card-hover dark:border-stone-800 dark:bg-stone-900 dark:hover:border-stone-700"
  >
    <div class="flex items-start justify-between gap-3">
      <h3 class="flex-1 text-sm font-medium text-stone-900 dark:text-stone-50">
        {{ news.title }}
      </h3>
      <NBadge color="default">{{ news.source_channel }}</NBadge>
    </div>

    <div class="mt-3 flex items-center gap-3">
      <!-- Importance bar -->
      <div v-if="news.importance_score" class="flex items-center gap-2">
        <div class="h-1.5 w-16 overflow-hidden rounded-full bg-stone-100 dark:bg-stone-800">
          <div
            class="h-full rounded-full transition-all"
            :class="importanceColor"
            :style="{ width: `${importancePercent}%` }"
          />
        </div>
        <span class="text-xs text-stone-400 dark:text-stone-500">{{ importancePercent }}%</span>
      </div>

      <span class="ml-auto text-xs text-stone-400 dark:text-stone-500">{{ relativeTime }}</span>
    </div>
  </a>
</template>

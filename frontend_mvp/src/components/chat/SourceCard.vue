<script setup lang="ts">
import type { NewsSourceResponse } from '@/api/types'
import { computed } from 'vue'

const props = defineProps<{
  source: NewsSourceResponse
  index?: number
}>()

const relativeTime = computed(() => {
  const date = new Date(props.source.published_at)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))

  if (diffHours < 1) return 'менее часа назад'
  if (diffHours < 24) return `${diffHours}ч назад`
  const diffDays = Math.floor(diffHours / 24)
  if (diffDays === 1) return 'вчера'
  return `${diffDays}д назад`
})
</script>

<template>
  <a
    :href="source.tg_link"
    target="_blank"
    rel="noopener noreferrer"
    class="block rounded-md border border-stone-200 p-3 transition-base hover:border-stone-300 hover:bg-stone-50 dark:border-stone-700 dark:hover:border-stone-600 dark:hover:bg-stone-800"
  >
    <p class="text-sm text-stone-900 dark:text-stone-50">
      <span v-if="index" class="mr-1.5 inline-flex h-5 w-5 items-center justify-center rounded bg-stone-200 text-xs font-medium text-stone-600 dark:bg-stone-700 dark:text-stone-300">{{ index }}</span>
      {{ source.summary }}
    </p>
    <div class="mt-1.5 flex items-center gap-2 text-xs text-stone-400 dark:text-stone-500">
      <span>{{ source.source_channel }}</span>
      <span>&middot;</span>
      <span>{{ relativeTime }}</span>
    </div>
  </a>
</template>

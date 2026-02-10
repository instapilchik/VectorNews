<script setup lang="ts">
import type { HotTopic } from '@/api/types'

defineProps<{
  topic: HotTopic
}>()
</script>

<template>
  <div class="card-hover cursor-default">
    <div class="flex items-start justify-between">
      <h3 class="text-sm font-medium text-stone-900 dark:text-stone-50">
        {{ topic.title }}
      </h3>
      <span class="ml-2 flex-shrink-0 rounded-full bg-stone-100 px-2 py-0.5 text-xs font-medium text-stone-600 dark:bg-stone-800 dark:text-stone-400">
        {{ topic.news_count }}
      </span>
    </div>
  </div>
</template>

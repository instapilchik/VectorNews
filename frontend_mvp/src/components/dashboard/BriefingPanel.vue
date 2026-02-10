<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ChatResponse } from '@/api/types'
import SourceCard from '@/components/chat/SourceCard.vue'

const props = defineProps<{
  data: ChatResponse | null
  loading: boolean
}>()

const renderedContent = computed(() => {
  if (!props.data) return ''
  return marked.parse(props.data.answer) as string
})
</script>

<template>
  <div>
    <!-- Skeleton -->
    <div v-if="loading" class="space-y-3">
      <div class="h-4 w-3/4 animate-pulse rounded bg-stone-200 dark:bg-stone-700" />
      <div class="h-4 w-full animate-pulse rounded bg-stone-200 dark:bg-stone-700" />
      <div class="h-4 w-5/6 animate-pulse rounded bg-stone-200 dark:bg-stone-700" />
      <div class="h-4 w-2/3 animate-pulse rounded bg-stone-200 dark:bg-stone-700" />
      <div class="h-4 w-full animate-pulse rounded bg-stone-200 dark:bg-stone-700" />
    </div>

    <template v-else-if="data">
      <div class="prose-custom" v-html="renderedContent" />

      <div v-if="data.sources.length > 0" class="mt-4 space-y-2">
        <p class="text-xs font-medium text-stone-500 dark:text-stone-400">Источники:</p>
        <SourceCard
          v-for="source in data.sources"
          :key="source.id"
          :source="source"
        />
      </div>
    </template>

    <div v-else class="py-8 text-center text-sm text-stone-400 dark:text-stone-500">
      Нет данных
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ChatMessage } from '@/composables/useChat'
import SourceCard from './SourceCard.vue'

const props = defineProps<{
  message: ChatMessage
}>()

const renderedContent = computed(() => {
  if (props.message.loading) return ''
  return marked.parse(props.message.content) as string
})
</script>

<template>
  <div
    class="flex"
    :class="message.role === 'user' ? 'justify-end' : 'justify-start'"
  >
    <div
      :class="[
        message.role === 'user'
          ? 'max-w-[75%] rounded-card bg-accent px-4 py-3 text-white dark:bg-accent-light dark:text-stone-950'
          : 'max-w-full',
      ]"
    >
      <!-- Loading indicator -->
      <div v-if="message.loading" class="flex items-center gap-1 py-2">
        <span class="h-2 w-2 animate-pulse rounded-full bg-stone-400 dark:bg-stone-500" style="animation-delay: 0ms" />
        <span class="h-2 w-2 animate-pulse rounded-full bg-stone-400 dark:bg-stone-500" style="animation-delay: 200ms" />
        <span class="h-2 w-2 animate-pulse rounded-full bg-stone-400 dark:bg-stone-500" style="animation-delay: 400ms" />
      </div>

      <!-- Content -->
      <div
        v-else-if="message.role === 'assistant'"
        class="prose-custom"
        v-html="renderedContent"
      />
      <div v-else class="text-sm" v-html="renderedContent" />

      <!-- Sources -->
      <div v-if="message.sources && message.sources.length > 0" class="mt-3 space-y-2">
        <p class="text-xs font-medium text-stone-500 dark:text-stone-400">Источники:</p>
        <SourceCard
          v-for="source in message.sources"
          :key="source.id"
          :source="source"
        />
      </div>
    </div>
  </div>
</template>

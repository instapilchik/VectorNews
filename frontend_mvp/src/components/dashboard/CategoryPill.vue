<script setup lang="ts">
import type { NewsCategory } from '@/api/types'

defineProps<{
  category: NewsCategory
  active?: boolean
}>()

defineEmits<{
  click: []
}>()
</script>

<template>
  <button
    class="rounded-full px-3 py-1 text-xs font-medium transition-base"
    :class="[
      active
        ? 'bg-accent text-white dark:bg-accent-light dark:text-stone-950'
        : 'bg-stone-100 text-stone-600 hover:bg-stone-200 dark:bg-stone-800 dark:text-stone-400 dark:hover:bg-stone-700',
    ]"
    @click="$emit('click')"
  >
    {{ category }}
  </button>
</template>

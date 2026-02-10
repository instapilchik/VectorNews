<script setup lang="ts">
import type { NewsCategory } from '@/api/types'
import { NEWS_CATEGORIES } from '@/api/types'
import CategoryPill from '@/components/dashboard/CategoryPill.vue'

defineProps<{
  selected: NewsCategory
}>()

defineEmits<{
  select: [category: NewsCategory]
}>()
</script>

<template>
  <div class="flex flex-wrap gap-2">
    <CategoryPill
      v-for="cat in NEWS_CATEGORIES"
      :key="cat"
      :category="cat"
      :active="cat === selected"
      @click="$emit('select', cat)"
    />
  </div>
</template>

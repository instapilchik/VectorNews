<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNewsFeed } from '@/composables/useNewsFeed'
import type { NewsCategory } from '@/api/types'
import CategoryFilter from '@/components/news/CategoryFilter.vue'
import NewsList from '@/components/news/NewsList.vue'

const route = useRoute()
const { items, loading, hasMore, category, load, setCategory } = useNewsFeed()

onMounted(() => {
  const queryCategory = route.query.category as NewsCategory | undefined
  if (queryCategory) {
    setCategory(queryCategory)
  }
  load(true)
})
</script>

<template>
  <div class="space-y-4">
    <CategoryFilter :selected="category" @select="setCategory" />
    <NewsList :items="items" :loading="loading" :has-more="hasMore" @load-more="load()" />
  </div>
</template>

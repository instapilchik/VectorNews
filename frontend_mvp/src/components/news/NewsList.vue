<script setup lang="ts">
import type { NewsCard as NewsCardType } from '@/api/types'
import NewsCard from './NewsCard.vue'
import NSpinner from '@/components/common/NSpinner.vue'
import NEmptyState from '@/components/common/NEmptyState.vue'
import NButton from '@/components/common/NButton.vue'

defineProps<{
  items: NewsCardType[]
  loading: boolean
  hasMore: boolean
}>()

defineEmits<{
  loadMore: []
}>()
</script>

<template>
  <div>
    <div v-if="items.length > 0" class="space-y-3">
      <NewsCard
        v-for="news in items"
        :key="news.id"
        :news="news"
      />
    </div>

    <div v-if="loading" class="flex justify-center py-6">
      <NSpinner />
    </div>

    <NEmptyState
      v-else-if="items.length === 0"
      message="Нет новостей"
      description="Попробуйте выбрать другую категорию"
    />

    <div v-if="hasMore && items.length > 0 && !loading" class="flex justify-center pt-4">
      <NButton variant="secondary" @click="$emit('loadMore')">
        Загрузить ещё
      </NButton>
    </div>
  </div>
</template>

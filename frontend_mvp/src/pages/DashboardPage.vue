<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getHotTopics, getDailyBriefing } from '@/api/dashboards'
import { NEWS_CATEGORIES } from '@/api/types'
import type { HotTopic, ChatResponse, NewsCategory } from '@/api/types'
import NCard from '@/components/common/NCard.vue'
import NSpinner from '@/components/common/NSpinner.vue'
import HotTopicCard from '@/components/dashboard/HotTopicCard.vue'
import BriefingPanel from '@/components/dashboard/BriefingPanel.vue'
import CategoryPill from '@/components/dashboard/CategoryPill.vue'

const router = useRouter()

const hotTopics = ref<HotTopic[]>([])
const briefing = ref<ChatResponse | null>(null)
const loadingTopics = ref(false)
const loadingBriefing = ref(false)

onMounted(async () => {
  loadingTopics.value = true
  loadingBriefing.value = true

  try {
    hotTopics.value = await getHotTopics()
  } catch {
    // silent
  } finally {
    loadingTopics.value = false
  }

  try {
    briefing.value = await getDailyBriefing()
  } catch {
    // silent
  } finally {
    loadingBriefing.value = false
  }
})

function goToCategory(cat: NewsCategory) {
  router.push({ name: 'news', query: { category: cat } })
}
</script>

<template>
  <div class="space-y-6">
    <div class="grid gap-6 lg:grid-cols-5">
      <!-- Daily Briefing -->
      <NCard class="lg:col-span-3">
        <h2 class="mb-4 text-base font-semibold text-stone-900 dark:text-stone-50">
          Главное за день
        </h2>
        <BriefingPanel :data="briefing" :loading="loadingBriefing" />
      </NCard>

      <!-- Hot Topics -->
      <div class="lg:col-span-2">
        <h2 class="mb-3 text-base font-semibold text-stone-900 dark:text-stone-50">
          Горячие темы
        </h2>
        <div v-if="loadingTopics" class="flex justify-center py-8">
          <NSpinner />
        </div>
        <div v-else-if="hotTopics.length > 0" class="space-y-3">
          <HotTopicCard
            v-for="topic in hotTopics"
            :key="topic.title"
            :topic="topic"
          />
        </div>
        <div v-else class="py-8 text-center text-sm text-stone-400 dark:text-stone-500">
          Нет данных о горячих темах
        </div>
      </div>
    </div>

    <!-- Category pills -->
    <NCard>
      <h2 class="mb-3 text-sm font-semibold text-stone-900 dark:text-stone-50">
        По категориям
      </h2>
      <div class="flex flex-wrap gap-2">
        <CategoryPill
          v-for="cat in NEWS_CATEGORIES"
          :key="cat"
          :category="cat"
          @click="goToCategory(cat)"
        />
      </div>
    </NCard>
  </div>
</template>

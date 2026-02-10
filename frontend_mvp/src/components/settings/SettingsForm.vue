<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AgentSettings } from '@/api/types'
import {
  NEWS_CATEGORIES,
  INFORMATION_STYLES,
  COMMUNICATION_TONES,
  ANALYSIS_DEPTHS,
} from '@/api/types'
import NInput from '@/components/common/NInput.vue'
import NButton from '@/components/common/NButton.vue'

const props = defineProps<{
  settings: AgentSettings
  loading: boolean
}>()

const emit = defineEmits<{
  save: [data: AgentSettings]
}>()

const form = ref<AgentSettings>({ ...props.settings })

watch(
  () => props.settings,
  (val) => {
    form.value = { ...val }
  },
)

function toggleInterest(cat: string) {
  const idx = form.value.focus_interests.indexOf(cat)
  if (idx >= 0) {
    form.value.focus_interests.splice(idx, 1)
  } else {
    form.value.focus_interests.push(cat)
  }
}

function handleSubmit() {
  emit('save', { ...form.value })
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div class="space-y-6">
      <!-- Agent name -->
      <NInput
        v-model="form.agent_name"
        label="Имя агента"
        placeholder="Аналитик"
      />

      <!-- Focus interests -->
      <div>
        <label class="mb-2 block text-sm font-medium text-stone-700 dark:text-stone-300">
          Фокус интересов
        </label>
        <div class="flex flex-wrap gap-2">
          <button
            v-for="cat in NEWS_CATEGORIES"
            :key="cat"
            type="button"
            class="rounded-full px-3 py-1 text-xs font-medium transition-base"
            :class="[
              form.focus_interests.includes(cat)
                ? 'bg-accent text-white dark:bg-accent-light dark:text-stone-950'
                : 'bg-stone-100 text-stone-600 hover:bg-stone-200 dark:bg-stone-800 dark:text-stone-400 dark:hover:bg-stone-700',
            ]"
            @click="toggleInterest(cat)"
          >
            {{ cat }}
          </button>
        </div>
      </div>

      <!-- Information style -->
      <div>
        <label class="mb-2 block text-sm font-medium text-stone-700 dark:text-stone-300">
          Стиль информации
        </label>
        <div class="space-y-2">
          <label
            v-for="opt in INFORMATION_STYLES"
            :key="opt.value"
            class="flex cursor-pointer items-center gap-2 text-sm text-stone-700 dark:text-stone-300"
          >
            <input
              v-model="form.information_style"
              type="radio"
              :value="opt.value"
              class="text-accent focus:ring-accent dark:text-accent-light"
            />
            {{ opt.label }}
          </label>
        </div>
      </div>

      <!-- Communication tone -->
      <div>
        <label class="mb-2 block text-sm font-medium text-stone-700 dark:text-stone-300">
          Тон коммуникации
        </label>
        <div class="space-y-2">
          <label
            v-for="opt in COMMUNICATION_TONES"
            :key="opt.value"
            class="flex cursor-pointer items-center gap-2 text-sm text-stone-700 dark:text-stone-300"
          >
            <input
              v-model="form.communication_tone"
              type="radio"
              :value="opt.value"
              class="text-accent focus:ring-accent dark:text-accent-light"
            />
            {{ opt.label }}
          </label>
        </div>
      </div>

      <!-- Analysis depth -->
      <div>
        <label class="mb-2 block text-sm font-medium text-stone-700 dark:text-stone-300">
          Глубина анализа
        </label>
        <div class="space-y-2">
          <label
            v-for="opt in ANALYSIS_DEPTHS"
            :key="opt.value"
            class="flex cursor-pointer items-center gap-2 text-sm text-stone-700 dark:text-stone-300"
          >
            <input
              v-model="form.analysis_depth"
              type="radio"
              :value="opt.value"
              class="text-accent focus:ring-accent dark:text-accent-light"
            />
            {{ opt.label }}
          </label>
        </div>
      </div>

      <!-- Historical context days -->
      <div>
        <label class="mb-2 block text-sm font-medium text-stone-700 dark:text-stone-300">
          Глубина исторического контекста: {{ form.historical_context_days }} дн.
        </label>
        <input
          v-model.number="form.historical_context_days"
          type="range"
          min="1"
          max="30"
          class="w-full accent-accent dark:accent-accent-light"
        />
        <div class="mt-1 flex justify-between text-xs text-stone-400 dark:text-stone-500">
          <span>1 день</span>
          <span>30 дней</span>
        </div>
      </div>

      <!-- Submit -->
      <NButton type="submit" :loading="loading">
        Сохранить
      </NButton>
    </div>
  </form>
</template>

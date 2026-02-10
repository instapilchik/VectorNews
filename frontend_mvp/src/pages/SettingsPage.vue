<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useSettingsStore } from '@/stores/settings'
import type { AgentSettings } from '@/api/types'
import NCard from '@/components/common/NCard.vue'
import NSpinner from '@/components/common/NSpinner.vue'
import SettingsForm from '@/components/settings/SettingsForm.vue'

const settingsStore = useSettingsStore()
const saved = ref(false)

onMounted(() => {
  settingsStore.fetch()
})

async function handleSave(data: AgentSettings) {
  saved.value = false
  try {
    await settingsStore.save(data)
    saved.value = true
    setTimeout(() => { saved.value = false }, 3000)
  } catch {
    // error is in the store
  }
}
</script>

<template>
  <div class="mx-auto max-w-xl">
    <NCard>
      <h2 class="mb-6 text-base font-semibold text-stone-900 dark:text-stone-50">
        Настройки аналитика
      </h2>

      <div v-if="settingsStore.loading && !settingsStore.settings" class="flex justify-center py-8">
        <NSpinner />
      </div>

      <SettingsForm
        v-else-if="settingsStore.settings"
        :settings="settingsStore.settings"
        :loading="settingsStore.loading"
        @save="handleSave"
      />

      <div v-if="settingsStore.error" class="mt-4 rounded-md bg-red-50 p-3 text-sm text-danger dark:bg-red-900/20">
        {{ settingsStore.error }}
      </div>

      <div v-if="saved" class="mt-4 rounded-md bg-emerald-50 p-3 text-sm text-success dark:bg-emerald-900/20">
        Настройки сохранены
      </div>
    </NCard>
  </div>
</template>

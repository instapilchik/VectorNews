import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getSettings, updateSettings } from '@/api/settings'
import type { AgentSettings } from '@/api/types'

export const useSettingsStore = defineStore('settings', () => {
  const settings = ref<AgentSettings | null>(null)
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetch() {
    loading.value = true
    error.value = null
    try {
      settings.value = await getSettings()
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка загрузки настроек'
    } finally {
      loading.value = false
    }
  }

  async function save(data: AgentSettings) {
    loading.value = true
    error.value = null
    try {
      settings.value = await updateSettings(data)
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Ошибка сохранения настроек'
      throw e
    } finally {
      loading.value = false
    }
  }

  return { settings, loading, error, fetch, save }
})

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import ThemeToggle from './ThemeToggle.vue'

defineProps<{
  sidebarCollapsed: boolean
}>()

defineEmits<{
  toggleSidebar: []
}>()

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const showUserMenu = ref(false)

const pageTitle = computed(() => {
  const titles: Record<string, string> = {
    dashboard: 'Дашборд',
    chat: 'Чат с аналитиком',
    news: 'Лента новостей',
    settings: 'Настройки',
    admin: 'Администрирование',
  }
  return titles[route.name as string] || ''
})

function logout() {
  authStore.logout()
  router.push('/login')
}
</script>

<template>
  <header class="flex h-14 items-center justify-between border-b border-stone-200 bg-white px-4 dark:border-stone-800 dark:bg-stone-900">
    <div class="flex items-center gap-3">
      <button
        class="rounded-md p-1.5 text-stone-500 transition-base hover:bg-stone-100 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-50 lg:hidden"
        @click="$emit('toggleSidebar')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>
      <h1 class="text-base font-semibold text-stone-900 dark:text-stone-50">
        {{ pageTitle }}
      </h1>
    </div>

    <div class="flex items-center gap-2">
      <ThemeToggle />

      <!-- User menu -->
      <div class="relative">
        <button
          class="flex items-center gap-2 rounded-md px-2 py-1.5 text-sm text-stone-600 transition-base hover:bg-stone-100 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-50"
          @click="showUserMenu = !showUserMenu"
        >
          <div class="flex h-7 w-7 items-center justify-center rounded-full bg-stone-200 text-xs font-medium text-stone-700 dark:bg-stone-700 dark:text-stone-300">
            {{ authStore.user?.display_name?.charAt(0)?.toUpperCase() || 'U' }}
          </div>
          <span class="hidden sm:inline">{{ authStore.user?.display_name || authStore.user?.username }}</span>
        </button>

        <div
          v-if="showUserMenu"
          class="absolute right-0 top-full z-50 mt-1 w-48 rounded-card border border-stone-200 bg-white py-1 shadow-card dark:border-stone-800 dark:bg-stone-900"
          @click="showUserMenu = false"
        >
          <div class="border-b border-stone-200 px-3 py-2 dark:border-stone-800">
            <p class="text-sm font-medium text-stone-900 dark:text-stone-50">
              {{ authStore.user?.display_name }}
            </p>
            <p class="text-xs text-stone-500 dark:text-stone-400">
              {{ authStore.user?.role === 'admin' ? 'Администратор' : 'Пользователь' }}
            </p>
          </div>
          <button
            class="flex w-full items-center px-3 py-2 text-sm text-stone-600 transition-base hover:bg-stone-100 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800 dark:hover:text-stone-50"
            @click="logout"
          >
            Выйти
          </button>
        </div>
      </div>
    </div>
  </header>

  <!-- Backdrop for user menu -->
  <div
    v-if="showUserMenu"
    class="fixed inset-0 z-40"
    @click="showUserMenu = false"
  />
</template>

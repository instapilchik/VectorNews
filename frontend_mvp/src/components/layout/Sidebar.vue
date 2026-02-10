<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{
  collapsed: boolean
}>()

defineEmits<{
  toggle: []
}>()

const route = useRoute()
const authStore = useAuthStore()

interface NavItem {
  name: string
  path: string
  label: string
  icon: string
  adminOnly?: boolean
}

const navItems: NavItem[] = [
  { name: 'dashboard', path: '/', label: 'Дашборд', icon: 'M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6' },
  { name: 'chat', path: '/chat', label: 'Чат', icon: 'M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z' },
  { name: 'news', path: '/news', label: 'Новости', icon: 'M19 20H5a2 2 0 01-2-2V6a2 2 0 012-2h10a2 2 0 012 2v1m2 13a2 2 0 01-2-2V7m2 13a2 2 0 002-2V9a2 2 0 00-2-2h-2m-4-3H9M7 16h6M7 8h6v4H7V8z' },
  { name: 'settings', path: '/settings', label: 'Настройки', icon: 'M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.066 2.573c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.573 1.066c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.066-2.573c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z' },
  { name: 'admin', path: '/admin', label: 'Админ', icon: 'M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z', adminOnly: true },
]

const visibleItems = computed(() =>
  navItems.filter((item) => !item.adminOnly || authStore.isAdmin),
)

function isActive(item: NavItem): boolean {
  if (item.path === '/') return route.path === '/'
  return route.path.startsWith(item.path)
}
</script>

<template>
  <aside
    class="flex h-full flex-col border-r border-stone-200 bg-stone-100 transition-base dark:border-stone-800 dark:bg-stone-900"
    :class="collapsed ? 'w-sidebar-collapsed' : 'w-sidebar'"
  >
    <!-- Logo -->
    <div class="flex h-14 items-center border-b border-stone-200 px-4 dark:border-stone-800">
      <span
        v-if="!collapsed"
        class="text-lg font-bold tracking-tight text-stone-900 dark:text-stone-50"
      >
        NewsEdge
      </span>
      <span
        v-else
        class="mx-auto text-lg font-bold text-stone-900 dark:text-stone-50"
      >
        N
      </span>
    </div>

    <!-- Navigation -->
    <nav class="flex-1 space-y-1 px-2 py-3">
      <router-link
        v-for="item in visibleItems"
        :key="item.name"
        :to="item.path"
        class="group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-base"
        :class="[
          isActive(item)
            ? 'bg-white text-accent shadow-card dark:bg-stone-800 dark:text-accent-light'
            : 'text-stone-600 hover:bg-white/60 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800/60 dark:hover:text-stone-50',
        ]"
        :title="collapsed ? item.label : undefined"
      >
        <svg
          class="h-5 w-5 flex-shrink-0"
          :class="collapsed ? 'mx-auto' : 'mr-3'"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          stroke-width="1.5"
        >
          <path stroke-linecap="round" stroke-linejoin="round" :d="item.icon" />
        </svg>
        <span v-if="!collapsed">{{ item.label }}</span>
      </router-link>
    </nav>

    <!-- Collapse button -->
    <div class="border-t border-stone-200 p-2 dark:border-stone-800">
      <button
        class="flex w-full items-center justify-center rounded-md p-2 text-stone-500 transition-base hover:bg-white/60 hover:text-stone-900 dark:text-stone-400 dark:hover:bg-stone-800/60 dark:hover:text-stone-50"
        @click="$emit('toggle')"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            :d="collapsed ? 'M13 5l7 7-7 7M5 5l7 7-7 7' : 'M11 19l-7-7 7-7m8 14l-7-7 7-7'"
          />
        </svg>
      </button>
    </div>
  </aside>
</template>

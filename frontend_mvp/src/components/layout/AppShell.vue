<script setup lang="ts">
import { ref } from 'vue'
import Sidebar from './Sidebar.vue'
import TopBar from './TopBar.vue'

const sidebarCollapsed = ref(false)

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-stone-50 dark:bg-stone-950">
    <Sidebar :collapsed="sidebarCollapsed" @toggle="toggleSidebar" />
    <div class="flex flex-1 flex-col overflow-hidden">
      <TopBar :sidebar-collapsed="sidebarCollapsed" @toggle-sidebar="toggleSidebar" />
      <main class="flex-1 overflow-y-auto scrollbar-thin p-6">
        <div class="mx-auto max-w-content">
          <slot />
        </div>
      </main>
    </div>
  </div>
</template>

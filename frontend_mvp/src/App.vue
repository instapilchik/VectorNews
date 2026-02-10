<script setup lang="ts">
import { useRoute } from 'vue-router'
import { computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import AppShell from '@/components/layout/AppShell.vue'

const route = useRoute()
const authStore = useAuthStore()

const showShell = computed(() => authStore.isAuthenticated && route.name !== 'login')
</script>

<template>
  <AppShell v-if="showShell">
    <router-view />
  </AppShell>
  <router-view v-else />
</template>

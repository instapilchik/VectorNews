<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import NInput from '@/components/common/NInput.vue'
import NButton from '@/components/common/NButton.vue'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  if (!username.value || !password.value) {
    error.value = 'Заполните все поля'
    return
  }

  loading.value = true
  error.value = ''

  try {
    await authStore.login(username.value, password.value)
    router.push('/')
  } catch (e: unknown) {
    if (e && typeof e === 'object' && 'response' in e) {
      const axiosError = e as { response?: { status: number } }
      if (axiosError.response?.status === 401) {
        error.value = 'Неверное имя пользователя или пароль'
      } else {
        error.value = 'Ошибка сервера. Попробуйте позже.'
      }
    } else {
      error.value = 'Не удалось подключиться к серверу'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-stone-50 px-4 dark:bg-stone-950">
    <div class="w-full max-w-sm">
      <!-- Logo -->
      <div class="mb-8 text-center">
        <h1 class="text-2xl font-bold tracking-tight text-stone-900 dark:text-stone-50">
          NewsEdge
        </h1>
        <p class="mt-1 text-sm text-stone-500 dark:text-stone-400">
          Аналитика финансовых новостей
        </p>
      </div>

      <!-- Login card -->
      <div class="rounded-card border border-stone-200 bg-white p-6 shadow-card dark:border-stone-800 dark:bg-stone-900">
        <form @submit.prevent="handleLogin">
          <div class="space-y-4">
            <NInput
              v-model="username"
              label="Имя пользователя"
              placeholder="username"
              :disabled="loading"
            />
            <NInput
              v-model="password"
              label="Пароль"
              type="password"
              placeholder="Пароль"
              :disabled="loading"
            />

            <div v-if="error" class="rounded-md bg-red-50 p-3 text-sm text-danger dark:bg-red-900/20">
              {{ error }}
            </div>

            <NButton type="submit" :loading="loading" class="w-full">
              Войти
            </NButton>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { login as apiLogin, getMe } from '@/api/auth'
import { setAuthInterceptors } from '@/api/client'
import type { UserResponse } from '@/api/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(sessionStorage.getItem('auth_token'))
  const user = ref<UserResponse | null>(null)

  const isAuthenticated = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  function setupInterceptors() {
    setAuthInterceptors(
      () => token.value,
      () => logout(),
    )
  }

  async function login(username: string, password: string) {
    const response = await apiLogin({ username, password })
    token.value = response.access_token
    user.value = response.user
    sessionStorage.setItem('auth_token', response.access_token)
  }

  async function init() {
    if (token.value) {
      try {
        user.value = await getMe()
      } catch {
        logout()
      }
    }
  }

  async function fetchUser() {
    if (!token.value) return
    user.value = await getMe()
  }

  function logout() {
    token.value = null
    user.value = null
    sessionStorage.removeItem('auth_token')
  }

  return {
    token,
    user,
    isAuthenticated,
    isAdmin,
    setupInterceptors,
    login,
    init,
    fetchUser,
    logout,
  }
})

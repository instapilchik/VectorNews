<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getUsers, createUser, updateUser } from '@/api/admin'
import type { UserResponse, UserCreateRequest } from '@/api/types'
import NCard from '@/components/common/NCard.vue'
import NButton from '@/components/common/NButton.vue'
import NSpinner from '@/components/common/NSpinner.vue'
import UserTable from '@/components/admin/UserTable.vue'
import UserCreateModal from '@/components/admin/UserCreateModal.vue'

const users = ref<UserResponse[]>([])
const loading = ref(false)
const showCreateModal = ref(false)
const createLoading = ref(false)
const error = ref<string | null>(null)

async function fetchUsers() {
  loading.value = true
  try {
    users.value = await getUsers()
  } catch {
    error.value = 'Ошибка загрузки пользователей'
  } finally {
    loading.value = false
  }
}

async function handleCreate(data: UserCreateRequest) {
  createLoading.value = true
  try {
    await createUser(data)
    showCreateModal.value = false
    await fetchUsers()
  } catch {
    error.value = 'Ошибка создания пользователя'
  } finally {
    createLoading.value = false
  }
}

async function handleToggleActive(user: UserResponse) {
  try {
    await updateUser(user.id, { is_active: !user.is_active })
    await fetchUsers()
  } catch {
    error.value = 'Ошибка обновления пользователя'
  }
}

onMounted(fetchUsers)
</script>

<template>
  <div>
    <div class="mb-4 flex items-center justify-between">
      <h2 class="text-base font-semibold text-stone-900 dark:text-stone-50">Пользователи</h2>
      <NButton @click="showCreateModal = true">Создать</NButton>
    </div>

    <div v-if="error" class="mb-4 rounded-md bg-red-50 p-3 text-sm text-danger dark:bg-red-900/20">
      {{ error }}
    </div>

    <NCard :padding="false">
      <div v-if="loading" class="flex justify-center py-8">
        <NSpinner />
      </div>
      <UserTable
        v-else
        :users="users"
        @toggle-active="handleToggleActive"
        @edit="() => {}"
      />
    </NCard>

    <UserCreateModal
      v-if="showCreateModal"
      :loading="createLoading"
      @close="showCreateModal = false"
      @create="handleCreate"
    />
  </div>
</template>

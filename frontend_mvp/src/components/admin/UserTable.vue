<script setup lang="ts">
import type { UserResponse } from '@/api/types'
import NBadge from '@/components/common/NBadge.vue'
import NButton from '@/components/common/NButton.vue'

defineProps<{
  users: UserResponse[]
}>()

defineEmits<{
  toggleActive: [user: UserResponse]
  edit: [user: UserResponse]
}>()

</script>

<template>
  <div class="overflow-x-auto">
    <table class="w-full text-sm">
      <thead>
        <tr class="border-b border-stone-200 dark:border-stone-800">
          <th class="px-3 py-3 text-left font-medium text-stone-500 dark:text-stone-400">Имя пользователя</th>
          <th class="px-3 py-3 text-left font-medium text-stone-500 dark:text-stone-400">Отображаемое имя</th>
          <th class="px-3 py-3 text-left font-medium text-stone-500 dark:text-stone-400">Роль</th>
          <th class="px-3 py-3 text-left font-medium text-stone-500 dark:text-stone-400">Статус</th>
          <th class="px-3 py-3 text-right font-medium text-stone-500 dark:text-stone-400">Действия</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="user in users"
          :key="user.id"
          class="border-b border-stone-100 dark:border-stone-800/50"
        >
          <td class="px-3 py-3 font-medium text-stone-900 dark:text-stone-50">{{ user.username }}</td>
          <td class="px-3 py-3 text-stone-600 dark:text-stone-400">{{ user.display_name }}</td>
          <td class="px-3 py-3">
            <NBadge :color="user.role === 'admin' ? 'accent' : 'default'">
              {{ user.role === 'admin' ? 'Админ' : 'Пользователь' }}
            </NBadge>
          </td>
          <td class="px-3 py-3">
            <NBadge :color="user.is_active ? 'success' : 'danger'">
              {{ user.is_active ? 'Активен' : 'Отключён' }}
            </NBadge>
          </td>
          <td class="px-3 py-3">
            <div class="flex items-center justify-end gap-2">
              <NButton size="sm" variant="ghost" @click="$emit('edit', user)">
                Изменить
              </NButton>
              <NButton
                size="sm"
                :variant="user.is_active ? 'danger' : 'secondary'"
                @click="$emit('toggleActive', user)"
              >
                {{ user.is_active ? 'Отключить' : 'Включить' }}
              </NButton>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

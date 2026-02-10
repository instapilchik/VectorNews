<script setup lang="ts">
import { ref } from 'vue'
import type { UserCreateRequest } from '@/api/types'
import NModal from '@/components/common/NModal.vue'
import NInput from '@/components/common/NInput.vue'
import NSelect from '@/components/common/NSelect.vue'
import NButton from '@/components/common/NButton.vue'

defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  close: []
  create: [data: UserCreateRequest]
}>()

const form = ref<UserCreateRequest>({
  username: '',
  display_name: '',
  password: '',
  role: 'user',
})

const errors = ref<Record<string, string>>({})

function validate(): boolean {
  errors.value = {}
  if (!form.value.username.trim()) errors.value.username = 'Обязательное поле'
  if (!form.value.display_name.trim()) errors.value.display_name = 'Обязательное поле'
  if (!form.value.password || form.value.password.length < 6) errors.value.password = 'Минимум 6 символов'
  return Object.keys(errors.value).length === 0
}

function handleSubmit() {
  if (!validate()) return
  emit('create', { ...form.value })
}
</script>

<template>
  <NModal title="Создать пользователя" @close="$emit('close')">
    <form class="space-y-4" @submit.prevent="handleSubmit">
      <NInput
        v-model="form.username"
        label="Имя пользователя"
        placeholder="username"
        :error="errors.username"
      />
      <NInput
        v-model="form.display_name"
        label="Отображаемое имя"
        placeholder="Иван Иванов"
        :error="errors.display_name"
      />
      <NInput
        v-model="form.password"
        label="Пароль"
        type="password"
        placeholder="Минимум 6 символов"
        :error="errors.password"
      />
      <NSelect
        v-model="form.role"
        label="Роль"
        :options="[
          { value: 'user', label: 'Пользователь' },
          { value: 'admin', label: 'Администратор' },
        ]"
      />
    </form>

    <template #footer>
      <NButton variant="secondary" @click="$emit('close')">Отмена</NButton>
      <NButton :loading="loading" @click="handleSubmit">Создать</NButton>
    </template>
  </NModal>
</template>

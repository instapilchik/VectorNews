<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { useChat } from '@/composables/useChat'
import ChatMessage from './ChatMessage.vue'
import ChatInput from './ChatInput.vue'

const { messages, isLoading, error, send, clear } = useChat()
const scrollContainer = ref<HTMLElement | null>(null)

watch(
  () => messages.value.length,
  async () => {
    await nextTick()
    if (scrollContainer.value) {
      scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight
    }
  },
)

async function handleSend(text: string) {
  await send(text)
}
</script>

<template>
  <div class="flex h-full flex-col">
    <!-- Messages -->
    <div ref="scrollContainer" class="flex-1 overflow-y-auto scrollbar-thin px-4 py-4">
      <div v-if="messages.length === 0" class="flex h-full items-center justify-center">
        <div class="text-center">
          <p class="text-sm text-stone-500 dark:text-stone-400">
            Задайте вопрос о финансовых новостях
          </p>
          <p class="mt-1 text-xs text-stone-400 dark:text-stone-500">
            Аналитик ответит, используя актуальные данные
          </p>
        </div>
      </div>

      <div v-else class="space-y-4">
        <ChatMessage
          v-for="(msg, idx) in messages"
          :key="idx"
          :message="msg"
        />
      </div>
    </div>

    <!-- Error -->
    <div v-if="error" class="mx-4 mb-2 rounded-card bg-red-50 p-3 text-sm text-danger dark:bg-red-900/20">
      {{ error }}
    </div>

    <!-- Input -->
    <ChatInput
      :loading="isLoading"
      @send="handleSend"
    />

    <!-- Clear button -->
    <div v-if="messages.length > 0" class="flex justify-center border-t border-stone-200 py-2 dark:border-stone-800">
      <button
        class="text-xs text-stone-400 transition-base hover:text-stone-600 dark:hover:text-stone-300"
        @click="clear"
      >
        Очистить чат
      </button>
    </div>
  </div>
</template>

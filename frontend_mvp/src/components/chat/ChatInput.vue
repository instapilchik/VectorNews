<script setup lang="ts">
import { ref } from 'vue'

defineProps<{
  loading: boolean
}>()

const emit = defineEmits<{
  send: [text: string]
}>()

const text = ref('')

function handleSend() {
  const trimmed = text.value.trim()
  if (!trimmed) return
  emit('send', trimmed)
  text.value = ''
}

function handleKeydown(e: KeyboardEvent) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    handleSend()
  }
}
</script>

<template>
  <div class="border-t border-stone-200 p-4 dark:border-stone-800">
    <div class="flex items-end gap-2">
      <textarea
        v-model="text"
        rows="1"
        class="max-h-32 min-h-[40px] flex-1 resize-none rounded-card border border-stone-200 bg-white px-3 py-2.5 text-sm text-stone-900 transition-base placeholder:text-stone-400 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-50 dark:placeholder:text-stone-500 dark:focus:border-accent-light dark:focus:ring-accent-light/20"
        placeholder="Задайте вопрос..."
        :disabled="loading"
        @keydown="handleKeydown"
      />
      <button
        class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-card bg-accent text-white transition-base hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50 dark:bg-accent-light dark:text-stone-950 dark:hover:bg-teal-300"
        :disabled="loading || !text.trim()"
        @click="handleSend"
      >
        <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5" />
        </svg>
      </button>
    </div>
  </div>
</template>

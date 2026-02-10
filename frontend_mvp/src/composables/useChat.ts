import { ref } from 'vue'
import { sendChatMessage } from '@/api/agent'
import type { ChatHistoryEntry, NewsSourceResponse } from '@/api/types'

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  sources?: NewsSourceResponse[]
  loading?: boolean
}

export function useChat() {
  const messages = ref<ChatMessage[]>([])
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  function buildHistory(): ChatHistoryEntry[] {
    return messages.value
      .filter((m) => !m.loading)
      .map((m) => ({ role: m.role, content: m.content }))
  }

  async function send(query: string) {
    if (!query.trim() || isLoading.value) return

    error.value = null
    messages.value.push({ role: 'user', content: query })
    messages.value.push({ role: 'assistant', content: '', loading: true })
    isLoading.value = true

    try {
      const history = buildHistory().slice(0, -1) // exclude the loading placeholder
      const response = await sendChatMessage({
        query,
        chat_history: history.length > 1 ? history.slice(0, -1) : undefined,
      })

      // Replace loading message with actual response
      messages.value[messages.value.length - 1] = {
        role: 'assistant',
        content: response.answer,
        sources: response.sources,
      }
    } catch (e: unknown) {
      messages.value.pop() // remove loading message
      error.value = e instanceof Error ? e.message : 'Ошибка при отправке сообщения'
    } finally {
      isLoading.value = false
    }
  }

  function clear() {
    messages.value = []
    error.value = null
  }

  return { messages, isLoading, error, send, clear }
}

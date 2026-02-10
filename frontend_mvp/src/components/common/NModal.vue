<script setup lang="ts">
interface Props {
  title?: string
  wide?: boolean
}

withDefaults(defineProps<Props>(), {
  title: undefined,
  wide: false,
})

defineEmits<{
  close: []
}>()
</script>

<template>
  <Teleport to="body">
    <div class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <!-- Backdrop -->
      <div
        class="absolute inset-0 bg-stone-900/50 dark:bg-black/60"
        @click="$emit('close')"
      />

      <!-- Modal -->
      <div
        class="relative z-10 w-full rounded-card border border-stone-200 bg-white shadow-lg dark:border-stone-800 dark:bg-stone-900"
        :class="wide ? 'max-w-2xl' : 'max-w-md'"
      >
        <!-- Header -->
        <div v-if="title" class="flex items-center justify-between border-b border-stone-200 px-5 py-4 dark:border-stone-800">
          <h2 class="text-base font-semibold text-stone-900 dark:text-stone-50">{{ title }}</h2>
          <button
            class="rounded-md p-1 text-stone-400 transition-base hover:text-stone-600 dark:hover:text-stone-300"
            @click="$emit('close')"
          >
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
              <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="p-5">
          <slot />
        </div>

        <!-- Footer -->
        <div v-if="$slots.footer" class="flex items-center justify-end gap-2 border-t border-stone-200 px-5 py-4 dark:border-stone-800">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

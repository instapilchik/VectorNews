<script setup lang="ts">
interface Props {
  modelValue: string
  label?: string
  placeholder?: string
  type?: string
  error?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  label: undefined,
  placeholder: '',
  type: 'text',
  error: undefined,
  disabled: false,
})

defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div>
    <label v-if="label" class="mb-1.5 block text-sm font-medium text-stone-700 dark:text-stone-300">
      {{ label }}
    </label>
    <input
      :type="type"
      :value="modelValue"
      :placeholder="placeholder"
      :disabled="disabled"
      class="w-full rounded-card border border-stone-200 bg-white px-3 py-2 text-sm text-stone-900 transition-base placeholder:text-stone-400 focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/20 disabled:cursor-not-allowed disabled:opacity-50 dark:border-stone-700 dark:bg-stone-800 dark:text-stone-50 dark:placeholder:text-stone-500 dark:focus:border-accent-light dark:focus:ring-accent-light/20"
      :class="error ? 'border-danger focus:border-danger focus:ring-danger/20' : ''"
      @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    />
    <p v-if="error" class="mt-1 text-xs text-danger">{{ error }}</p>
  </div>
</template>

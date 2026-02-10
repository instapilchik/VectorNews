<script setup lang="ts">
interface Props {
  color?: 'default' | 'accent' | 'danger' | 'warning' | 'success'
}

withDefaults(defineProps<Props>(), {
  color: 'default',
})

const colorClasses: Record<string, string> = {
  default: 'bg-stone-100 text-stone-600 dark:bg-stone-800 dark:text-stone-400',
  accent: 'bg-teal-50 text-accent dark:bg-teal-900/30 dark:text-accent-light',
  danger: 'bg-red-50 text-danger dark:bg-red-900/30 dark:text-red-400',
  warning: 'bg-amber-50 text-warning dark:bg-amber-900/30 dark:text-amber-400',
  success: 'bg-emerald-50 text-success dark:bg-emerald-900/30 dark:text-emerald-400',
}
</script>

<template>
  <span
    class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
    :class="colorClasses[color]"
  >
    <slot />
  </span>
</template>

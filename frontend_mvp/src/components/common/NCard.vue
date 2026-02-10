<script setup lang="ts">
interface Props {
  hoverable?: boolean
  padding?: boolean
}

withDefaults(defineProps<Props>(), {
  hoverable: false,
  padding: true,
})
</script>

<template>
  <div
    class="rounded-card border border-stone-200 bg-white dark:border-stone-800 dark:bg-stone-900"
    :class="[
      padding ? 'p-5' : '',
      hoverable ? 'shadow-card transition-shadow duration-200 hover:shadow-card-hover' : 'shadow-card',
    ]"
  >
    <slot />
  </div>
</template>

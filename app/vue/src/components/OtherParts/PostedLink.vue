<script lang="ts" setup>
defineProps({ links: { type: Array, default: () => [] } })
</script>

<template>
  {{ links }}
</template>

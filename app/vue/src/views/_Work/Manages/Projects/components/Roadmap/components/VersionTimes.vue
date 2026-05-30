<script lang="ts" setup>
import { computed, type PropType } from 'vue'

defineProps({
  issues: { type: Array as PropType<any[]>, default: () => [] },
  versionPk: { type: Number, default: null },
})

const get_total_spent_times = computed(() => 0)
</script>

<template>
  <div v-if="false"></div>
</template>

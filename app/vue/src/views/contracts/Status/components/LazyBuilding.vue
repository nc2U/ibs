<script lang="ts" setup>
import { ref, onMounted, onUnmounted, type PropType } from 'vue'
import Building from './Building.vue'
import { type SimpleUnit } from './ContractBoard.vue'

const props = defineProps({
  bldg: { type: Number, required: true },
  maxFloor: { type: Number, required: true },
  units: { type: Object as PropType<SimpleUnit[]>, required: true },
})

const isVisible = ref(false)
const hasBeenVisible = ref(false) // 한 번 로드되면 유지
const container = ref<HTMLElement | null>(null)
let observer: IntersectionObserver | null = null

onMounted(() => {
  observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          isVisible.value = true
          hasBeenVisible.value = true
        } else {
          isVisible.value = false
        }
      })
    },
    {
      rootMargin: '300px', // 뷰포트 300px 전에 미리 로드
      threshold: 0.01,
    },
  )

  if (container.value) {
    observer.observe(container.value)
  }
})

onUnmounted(() => {
  if (observer && container.value) {
    observer.unobserve(container.value)
  }
})
</script>

<template>
  <div ref="container" class="lazy-building-wrapper">
    <Building v-if="hasBeenVisible" :bldg="bldg" :max-floor="maxFloor" :units="units" />
    <div v-else class="loading-placeholder">
      <CSpinner size="sm" color="primary" />
      <span class="ms-2 text-muted">로딩 중...</span>
    </div>
  </div>
</template>

<style scoped>
.lazy-building-wrapper {
  display: inline-block;
  min-height: 100px;
  min-width: 100px;
}

.loading-placeholder {
  min-height: 100px;
  min-width: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  opacity: 0.6;
}
</style>

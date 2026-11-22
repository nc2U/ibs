<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useStore } from '@/store'
import type { SimpleUnit } from '@/store/types/project'

const props = defineProps({
  unit: { type: Object as PropType<SimpleUnit | null>, default: null },
  floor: { type: Number, default: 1 },
  line: { type: Number, default: 1 },
})

const store = useStore()
const isDark = computed(() => store.theme === 'dark')

const color = computed(() => {
  if (props.unit?.color) return props.unit.color
  return props.floor < 3 ? (isDark.value ? '#3a3d4a' : '#ccc') : ''
})

// 배경색(#RGB / #RRGGBB)의 상대 휘도를 계산해 시인성이 높은 텍스트 색상 반환
const textColor = computed(() => {
  const bg = props.unit?.color?.trim()
  if (!bg || !bg.startsWith('#')) return ''
  let hex = bg.slice(1)
  if (hex.length === 3) {
    hex = hex
      .split('')
      .map(c => c + c)
      .join('')
  }
  if (hex.length !== 6) return '#212529'
  const r = parseInt(hex.slice(0, 2), 16)
  const g = parseInt(hex.slice(2, 4), 16)
  const b = parseInt(hex.slice(4, 6), 16)
  if ([r, g, b].some(Number.isNaN)) return '#212529'
  const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  return luminance > 0.55 ? '#212529' : '#ffffff'
})
</script>

<template>
  <div
    class="unit"
    :class="{
      border: !!unit || floor < 3,
    }"
    :style="{ background: color, color: textColor }"
  >
    <span v-if="unit">{{ unit.name }}</span>
  </div>
</template>

<style lang="scss" scoped>
.unit {
  width: 60px;
  height: 20px;
  padding: 0;
  font-size: 10px;
  text-align: center;
  vertical-align: middle;
}
</style>

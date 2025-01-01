<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, type PropType, ref } from 'vue'
import { GGanttChart } from '@infectoone/vue-ganttastic'
import type { Gantts } from '@/store/types/work'
import { getToday } from '@/utils/baseMixins'

const props = defineProps({ gantts: { type: Array as PropType<Gantts[][]>, default: () => [] } })

const isDark = inject<ComputedRef<boolean>>('isDark')

const chartStart = ref()
const chartEnd = ref()

const getChartStart = (date = new Date()) => {
  date.setDate(date.getDate() - 15)
  return new Date(date.getFullYear(), date.getMonth(), 1)
}
const getChartEnd = (date = new Date()) => {
  date.setDate(date.getDate() - 15)
  return new Date(date.getFullYear(), date.getMonth() + 6, 0)
}

const style = computed(() => `border-bottom: #${isDark?.value ? '666' : 'ddd'} 1px solid`)
const remain = computed(() => (props.gantts.length > 10 ? 5 : 15 - props.gantts.length))

onBeforeMount(() => {
  chartStart.value = getChartStart()
  chartEnd.value = getChartEnd()
})
</script>

<template>
  <g-gantt-chart
    :color-scheme="isDark ? 'dark' : ''"
    label-column-width="450px"
    label-column-title=" "
    :current-time-label="getToday()"
    :chart-start="chartStart"
    :chart-end="chartEnd"
    date-format="YYYY-MM-DD"
    precision="week"
    bar-start="start"
    bar-end="due"
    :row-height="20"
    current-time
    :style="style"
    grid
  >
    <g-gantt-row label="" :bars="[]" />
    <g-gantt-row
      v-for="(gantt, i) in gantts"
      :label="gantt[0].name"
      :bars="gantt as any[]"
      highlight-on-hover
      :key="`gantt-${i}`"
    />
    <g-gantt-row v-for="i in remain" label="" :bars="[]" :key="`remain-${i}`" />
  </g-gantt-chart>
</template>

<script lang="ts" setup>
import { computed, type ComputedRef, inject, type PropType } from 'vue'
import { getToday } from '@/utils/baseMixins'
import type { Gantts } from '@/store/types/work'
import { GGanttChart } from '@infectoone/vue-ganttastic'
import sanitizeHtml from 'sanitize-html'

const props = defineProps({ gantts: { type: Array as PropType<Gantts[][]>, default: () => [] } })

const isDark = inject<ComputedRef<boolean>>('isDark')

const chartStart = (date = new Date()) => new Date(date.getFullYear(), date.getMonth(), 1)
const chartEnd = (date = new Date()) => new Date(date.getFullYear(), date.getMonth() + 6, 0)

const remain = computed(() => (props.gantts.length > 10 ? 5 : 15 - props.gantts.length))

const onMouseenterBar = (bar: any) => console.log(bar)
const onMouseleaveBar = (bar: any) => console.log(bar)
</script>

<template>
  <g-gantt-chart
    :style="`border-bottom: #${isDark ? '666' : 'ddd'} 1px solid`"
    :current-time-label="getToday()"
    label-column-title=" "
    :chart-start="chartStart()"
    :chart-end="chartEnd()"
    date-format="YYYY-MM-DD"
    precision="week"
    bar-start="start"
    bar-end="due"
    :row-height="20"
    label-column-width="450px"
    :color-scheme="isDark ? 'dark' : ''"
    current-time
    grid
    @mouseenter-bar="onMouseenterBar($event.bar)"
    @mouseleave-bar="onMouseleaveBar($event.bar)"
  >
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

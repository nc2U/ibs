<script lang="ts" setup>
import { type ComputedRef, inject, ref } from 'vue'
import { getToday } from '@/utils/baseMixins'
import { GGanttChart } from '@infectoone/vue-ganttastic'

const isDark = inject<ComputedRef<boolean>>('isDark')

const rowBarList = ref([
  [
    {
      label: '토지 목록 작성',
      sDate: '2024-12-13',
      eDate: '2024-12-23',
      ganttBarConfig: {
        id: '1',
        label: '0%',
        immobile: true,
        html: '',
      },
      highlightOnHover: true,
    },
  ],
  [
    {
      label: '설립 인가 신청',
      sDate: '2024-12-13',
      eDate: '2025-04-30',
      ganttBarConfig: {
        id: '2',
        label: '0%',
        immobile: true,
        html: '',
        style: {
          background: 'lightgreen',
          // color: 'black',
          // borderRadius: '20px',
          // fontSize: '',
        },
      },
    },
  ],
])
</script>

<template>
  <g-gantt-chart
    :style="`border-bottom: #${isDark ? '666' : 'ddd'} 1px solid`"
    :current-time-label="getToday()"
    label-column-title="[인천] 석남동 조합"
    chart-start="2024-12-01"
    chart-end="2025-05-31"
    date-format="YYYY-MM-DD"
    precision="week"
    bar-start="sDate"
    bar-end="eDate"
    current-time
    row-height="20"
    label-column-width="450px"
    :color-scheme="isDark ? 'dark' : ''"
    grid
  >
    <g-gantt-row
      v-for="row in rowBarList"
      :label="row[0].label"
      :bars="row"
      highlight-on-hover
      :key="row[0].ganttBarConfig.id"
    />
    <g-gantt-row v-for="i in 10" label="" :bars="[]" :key="i" />
  </g-gantt-chart>
</template>

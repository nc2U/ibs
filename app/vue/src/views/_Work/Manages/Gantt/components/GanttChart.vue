<script lang="ts" setup>
import { type ComputedRef, inject, type PropType, ref } from 'vue'
import { getToday } from '@/utils/baseMixins'
import type { GanttProject } from '@/store/types/work'
import { GGanttChart } from '@infectoone/vue-ganttastic'

defineProps({ ganttIssues: { type: Array as PropType<GanttProject[]>, default: () => [] } })

const isDark = inject<ComputedRef<boolean>>('isDark')

const chartStart = (date = new Date()) => new Date(date.getFullYear(), date.getMonth(), 1)
const chartEnd = (date = new Date()) => new Date(date.getFullYear(), date.getMonth() + 6, 0)

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

const onMouseenterBar = (bar: any) => console.log(bar)
const onMouseleaveBar = (bar: any) => console.log(bar)
</script>

<template>
  <div v-for="gantt in ganttIssues" :key="gantt.pk">
    <div v-if="gantt.depth == 0">
      <span v-if="gantt.issues.length">
        {{ gantt.name }}/{{ gantt.start_first }}/{{ gantt.due_last }}
      </span>
      <div v-for="issue in gantt.issues" :key="issue.pk">{{ issue }}</div>
      <div v-if="gantt.sub_projects.length">
        <div v-for="sub in gantt.sub_projects" :key="sub.pk">
          <div v-if="sub.depth == 1" :class="`pl-${sub.depth * 3}`">
            <span v-if="sub.issues.length">
              {{ sub.name }}/{{ sub.start_first }}/{{ sub.due_last }}
            </span>
            <div v-for="issue in sub.issues" :key="issue.pk">
              {{ issue }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <g-gantt-chart
    :style="`border-bottom: #${isDark ? '666' : 'ddd'} 1px solid`"
    :current-time-label="getToday()"
    label-column-title="[인천] 석남동 조합"
    :chart-start="chartStart()"
    :chart-end="chartEnd()"
    date-format="YYYY-MM-DD"
    precision="week"
    bar-start="sDate"
    bar-end="eDate"
    :row-height="20"
    label-column-width="450px"
    :color-scheme="isDark ? 'dark' : ''"
    current-time
    grid
    @mouseenter-bar="onMouseenterBar($event.bar)"
    @mouseleave-bar="onMouseleaveBar($event.bar)"
  >
    <g-gantt-row
      v-for="row in rowBarList"
      :label="row[0].label"
      :bars="row"
      highlight-on-hover
      :key="row[0].ganttBarConfig.id"
    />
    <g-gantt-row v-for="i in 15" label="" :bars="[]" :key="i" />
  </g-gantt-chart>
</template>

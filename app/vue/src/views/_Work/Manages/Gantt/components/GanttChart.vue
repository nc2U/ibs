<script lang="ts" setup>
import { computed, type ComputedRef, inject, onBeforeMount, type PropType, ref } from 'vue'
import { GGanttChart } from '@infectoone/vue-ganttastic'
import type { Gantts } from '@/store/types/work_issue.ts'
import { getToday } from '@/utils/baseMixins'

const props = defineProps({ gantts: { type: Array as PropType<Gantts[][]>, default: () => [] } })

const isDark = inject<ComputedRef<boolean>>('isDark')

const baseDate = ref(new Date(new Date().setDate(new Date().getDate() - 15)))

const chartStart = ref()
const chartEnd = ref()

const getChartStart = () => new Date(baseDate.value.getFullYear(), baseDate.value.getMonth(), 1)
const getChartEnd = () => new Date(baseDate.value.getFullYear(), baseDate.value.getMonth() + 6, 0)

const style = computed(() => `border-bottom: #${isDark?.value ? '666' : 'ddd'} 1px solid`)
const remain = computed(() => (props.gantts.length > 10 ? 5 : 15 - props.gantts.length))

const toMonthPrev = (n: number) => {
  baseDate.value = new Date(baseDate.value.setMonth(baseDate.value.getMonth() - n))
  chartStart.value = getChartStart()
  chartEnd.value = getChartEnd()
}

const toMonthNext = (n: number) => {
  baseDate.value = new Date(baseDate.value.setMonth(baseDate.value.getMonth() + n))
  chartStart.value = getChartStart()
  chartEnd.value = getChartEnd()
}

const prev = computed(() => {
  const year = baseDate.value.getFullYear()
  const month = baseDate.value.getMonth()
  return month === 0 ? `12월 ${year}` : `${month}월`
})
const next = computed(() => {
  const year = baseDate.value.getFullYear()
  const month = baseDate.value.getMonth()
  return month === 11 ? `01월 ${year + 1}` : `${month + 2}월`
})

onBeforeMount(() => {
  chartStart.value = getChartStart()
  chartEnd.value = getChartEnd()
})
</script>

<template>
  <CRow class="mb-1">
    <CCol class="text-right">
      <span @click="toMonthPrev(1)" class="pointer">
        « <a href="javascript:void(0)">{{ prev }}</a>
      </span>
      <span class="px-2">|</span>
      <span @click="toMonthNext(1)" class="pointer">
        <a href="javascript:void(0)">{{ next }}</a> »
      </span>
    </CCol>
  </CRow>
  <CRow class="mb-3">
    <CCol>
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
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <v-btn-group density="compact" role="group">
        <v-btn color="primary" variant="outlined" size="small" @click="toMonthPrev(6)">
          « 뒤로
        </v-btn>
        <v-btn color="primary" variant="outlined" size="small" @click="toMonthNext(6)">
          다음 »
        </v-btn>
      </v-btn-group>
    </CCol>
  </CRow>
</template>

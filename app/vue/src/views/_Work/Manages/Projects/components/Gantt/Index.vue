<script lang="ts" setup>
import { type ComputedRef, inject, onBeforeMount, ref } from 'vue'
import { getToday } from '@/utils/baseMixins'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'

const emit = defineEmits(['aside-visible'])

const isDark = inject<ComputedRef<boolean>>('isDark')

const row1BarList = ref([
  {
    sDate: '2024-12-13 00:00',
    eDate: '2024-12-23 00:00',
    ganttBarConfig: {
      // each bar must have a nested ganttBarConfig object ...
      id: 'unique-id-1', // ... and a unique "id" property
      label: '0%',
    },
  },
])
const row2BarList = ref([
  {
    sDate: '2024-12-13 00:00',
    eDate: '2025-04-30 00:00',
    ganttBarConfig: {
      id: 'another-unique-id-2',
      hasHandles: true,
      label: '0%',
      style: {
        // arbitrary CSS styling for your bar
        background: 'orange',
        borderRadius: '20px',
        color: 'black',
      },
    },
  },
])

onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <CRow class="py-2">
    <CCol>
      <h5>간트차트</h5>
    </CCol>
  </CRow>

  <SearchList />

  <CRow class="mb-3">
    <CCol>
      <g-gantt-chart
        :style="`border-bottom: #${isDark ? '666' : 'ddd'} 1px solid`"
        :current-time-label="getToday()"
        label-column-title="[인천] 석남동 조합"
        chart-start="2024-12-01 00:00"
        chart-end="2025-05-31 00:00"
        precision="week"
        bar-start="sDate"
        bar-end="eDate"
        current-time
        label-column-width="450px"
        row-height="20"
        :color-scheme="isDark ? 'slumber' : ''"
        grid
      >
        <g-gantt-row label="토지 목록 작성" :bars="row1BarList" />
        <g-gantt-row label="설립인가 신청" :bars="row2BarList" />
        <g-gantt-row v-for="i in 10" label="" :bars="[]" :key="i" />
      </g-gantt-chart>
    </CCol>
  </CRow>

  <CRow>
    <CCol>
      <CButtonGroup role="group">
        <CButton color="primary" variant="outline" size="sm">« 뒤로</CButton>
        <CButton color="primary" variant="outline" size="sm">다음 »</CButton>
      </CButtonGroup>
    </CCol>
  </CRow>
</template>

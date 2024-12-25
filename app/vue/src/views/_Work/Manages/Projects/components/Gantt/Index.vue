<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'

const emit = defineEmits(['aside-visible'])

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
    <CCol class="col-3"> IBS</CCol>
    <CCol>
      <g-gantt-chart
        chart-start="2024-12-01 00:00"
        chart-end="2025-05-31 00:00"
        precision="week"
        bar-start="sDate"
        bar-end="eDate"
      >
        <g-gantt-row label="1" :bars="row1BarList" />
        <g-gantt-row label="2" :bars="row2BarList" />
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

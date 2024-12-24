<script lang="ts" setup>
import { onBeforeMount, ref } from 'vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'

const emit = defineEmits(['aside-visible'])

const row1BarList = ref([
  {
    myBeginDate: '2021-07-13 13:00',
    myEndDate: '2021-07-13 19:00',
    ganttBarConfig: {
      // each bar must have a nested ganttBarConfig object ...
      id: 'unique-id-1', // ... and a unique "id" property
      label: 'Lorem ipsum dolor',
    },
  },
])

const row2BarList = ref([
  {
    myBeginDate: '2021-07-13 00:00',
    myEndDate: '2021-07-14 02:00',
    ganttBarConfig: {
      id: 'another-unique-id-2',
      hasHandles: true,
      label: 'Hey, look at me',
      style: {
        // arbitrary CSS styling for your bar
        background: '#e09b69',
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
        chart-start="2021-07-12 12:00"
        chart-end="2021-07-14 12:00"
        precision="hour"
        bar-start="myBeginDate"
        bar-end="myEndDate"
      >
        <g-gantt-row label="My row 1" :bars="row1BarList" />
        <g-gantt-row label="My row 2" :bars="row2BarList" />
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

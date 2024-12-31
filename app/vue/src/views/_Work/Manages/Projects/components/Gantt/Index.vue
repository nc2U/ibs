<script lang="ts" setup>
import { computed, onBeforeMount, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import GanttChart from '@/views/_Work/Manages/Gantt/components/GanttChart.vue'

const emit = defineEmits(['aside-visible'])

const route = useRoute()

const workStore = useWork()
const getGantts = computed(() => workStore.getGantts)

watch(
  () => route.params.projId,
  nVal => {
    if (nVal) workStore.fetchGanttIssues(nVal as string)
  },
)

onBeforeMount(() => {
  emit('aside-visible', true)
  if (route.params.projId) workStore.fetchGanttIssues(route.params.projId as string)
})
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
      <GanttChart :gantts="getGantts" />
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

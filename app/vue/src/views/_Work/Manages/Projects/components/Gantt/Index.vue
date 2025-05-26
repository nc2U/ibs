<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project.ts'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import GanttChart from '@/views/_Work/Manages/Gantt/components/GanttChart.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

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
  if (route.params.projId) workStore.fetchGanttIssues(route.params.projId as string)
})
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>간트차트</h5>
        </CCol>
      </CRow>

      <SearchList />

      <GanttChart :gantts="getGantts" />
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>

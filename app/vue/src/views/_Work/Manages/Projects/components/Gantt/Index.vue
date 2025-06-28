<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useIssue } from '@/store/pinia/work_issue.ts'
import Loading from '@/components/Loading/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import GanttChart from '@/views/_Work/Manages/Gantt/components/GanttChart.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const issueStore = useIssue()
const getGantts = computed(() => issueStore.getGantts)

const route = useRoute()
watch(
  () => route.params.projId,
  nVal => {
    if (nVal) issueStore.fetchGanttIssues(nVal as string)
  },
)

const loading = ref(true)
onBeforeMount(async () => {
  if (route.params.projId) await issueStore.fetchGanttIssues(route.params.projId as string)
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
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

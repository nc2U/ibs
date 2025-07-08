<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { ActLogEntry } from '@/store/types/work_logging.ts'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from '@/views/_Work/Manages/Activity/components/ActivityLogList.vue'
import AsideController from '@/views/_Work/Manages/Activity/components/aside/AsideController.vue'

const emit = defineEmits(['to-back', 'to-next'])

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const workStore = useWork()
const hasSubs = computed(() => !!(workStore.issueProject as IssueProject)?.sub_projects.length)

const toDate = ref(new Date())
const fromDate = computed(() => new Date(toDate.value.getTime() - 9 * 24 * 60 * 60 * 1000))

const logStore = useLogging()
const groupedActivities = computed<{ [key: string]: ActLogEntry[] }>(
  () => logStore.groupedActivities,
)

const RefActCont = ref()

const toMove = (date: Date) => {
  toDate.value = date
  RefActCont.value.filterActivity()
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <ActivityLogList
        :to-date="toDate"
        :from-date="fromDate"
        :activities="groupedActivities"
        @to-move="toMove"
      />
    </template>

    <template v-slot:aside>
      <AsideController
        ref="RefActCont"
        :to-date="toDate"
        :from-date="fromDate"
        :has-subs="hasSubs"
      />
    </template>
  </ContentBody>
</template>

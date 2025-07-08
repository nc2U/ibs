<script lang="ts" setup>
import { computed, onBeforeMount, type PropType, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins.ts'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { IssueProject } from '@/store/types/work_project.ts'
import type { ActLogEntryFilter } from '@/store/types/work_logging.ts'
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

const route = useRoute()

const toDate = ref(new Date())
const fromDate = computed(() => new Date(toDate.value.getTime() - 9 * 24 * 60 * 60 * 1000))

const activityFilter = ref<ActLogEntryFilter>({
  project: '',
  project__search: '',
  to_act_date: dateFormat(toDate.value),
  from_act_date: dateFormat(fromDate.value),
  user: '',
  sort: [],
})

const logStore = useLogging()
const toMove = (date: Date) => {
  toDate.value = date
  activityFilter.value.to_act_date = dateFormat(date)
  activityFilter.value.from_act_date = dateFormat(
    new Date(date.getTime() - 9 * 24 * 60 * 60 * 1000),
  )
  console.log(dateFormat(new Date(date.getTime() - 9 * 24 * 60 * 60 * 1000)))
  logStore.fetchActivityLogList(activityFilter.value)
}

const setFilter = (payload: ActLogEntryFilter) => {
  if (payload.to_act_date) toDate.value = new Date(payload.to_act_date)
  activityFilter.value.project = payload.project ?? ''
  activityFilter.value.project__search = payload.project__search ?? ''
  activityFilter.value.user = payload.user ?? ''
  activityFilter.value.sort = payload.sort
  logStore.fetchActivityLogList(payload)
}

watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) {
      activityFilter.value.project = nVal as string
    }
  },
)

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  if (route.params.projId) activityFilter.value.project = route.params.projId as string
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <ActivityLogList
        :to-date="toDate"
        :activity-filter="activityFilter"
        @to-back="toMove"
        @to-next="toMove"
      />
    </template>

    <template v-slot:aside>
      <AsideController :to-date="toDate" :has-subs="hasSubs" @set-filter="setFilter" />
    </template>
  </ContentBody>
</template>

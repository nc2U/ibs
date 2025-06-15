<script setup lang="ts">
import { computed, type ComputedRef, inject, onBeforeMount, provide, ref } from 'vue'
import { navMenu1, navMenu2 } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { dateFormat } from '@/utils/baseMixins'
import { useWork } from '@/store/pinia/work_project.ts'
import { useLogging } from '@/store/pinia/work_logging.ts'
import type { Company } from '@/store/types/settings'
import type { ActLogEntryFilter } from '@/store/types/work_logging.ts'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import ActivityLogList from '@/views/_Work/Manages/Activity/components/ActivityLogsComponent.vue'
import AsideActivity from '@/views/_Work/Manages/Activity/components/aside/AsideActivity.vue'

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)

const sideNavCAll = () => cBody.value.toggle()

const navMenu = computed(() => (!issueProjects.value.length ? navMenu1 : navMenu2))

const workStore = useWork()
const issueProjects = computed(() => workStore.issueProjects)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

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
  logStore.fetchActivityLogList(activityFilter.value)
}

const filterActivity = (payload: ActLogEntryFilter) => {
  if (payload.to_act_date) toDate.value = new Date(payload.to_act_date)
  activityFilter.value.project = payload.project ?? ''
  activityFilter.value.project__search = payload.project__search ?? ''
  activityFilter.value.user = payload.user ?? ''
  activityFilter.value.sort = payload.sort
  logStore.fetchActivityLogList(payload)
}

const loading = ref<boolean>(true)
onBeforeMount(async () => {
  await workStore.fetchIssueProjectList({})
  if (route.query.user) activityFilter.value.user = route.query.user as string
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <ActivityLogList
        :to-date="toDate"
        :activity-filter="activityFilter"
        @to-back="toMove"
        @to-next="toMove"
      />
    </template>

    <template v-slot:aside>
      <AsideActivity :to-date="toDate" @filter-activity="filterActivity" />
    </template>
  </ContentBody>
</template>

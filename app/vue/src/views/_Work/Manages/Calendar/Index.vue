<script setup lang="ts">
import { computed, provide, ref, onBeforeMount } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import { useWork } from '@/store/pinia/work_project'
import { useCompany } from '@/store/pinia/company.ts'
import { useCalendar } from '@/store/pinia/work_calendar'
import { useCalendarFilter } from '@/store/pinia/work_calendar_filter.ts'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import { useMeeting } from '@/store/pinia/work_meeting'
import type { Company } from '@/store/types/settings'
import type { IssueFilter } from '@/store/types/work_issue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from './components/QuerySection.vue'
import SharedCalendar from './components/SharedCalendar.vue'
import SummaryStatus from '@/views/_Work/Manages/Calendar/components/SummaryStatus.vue'
import SavedQueryAside from '@/views/_Work/components/asides/SavedQueryAside.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

const { can, PERM } = usePerms()
const canPubQuery = computed(() => can(PERM.PROJECT_PUB_QUERY))

const route = useRoute()
provide('navMenu', navMenu)
provide('query', route?.query)

const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const workStore = useWork()
const calendarStore = useCalendar()
const accStore = useAccount()
const issueStore = useIssue()
const meetingStore = useMeeting()

const allReadableProjects = computed(() => workStore.getAllReadableProjects)
const getUsers = computed(() => accStore.getUsers)
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const meetingCategories = computed(() => meetingStore.categoryList)

const calendarFilterStore = useCalendarFilter()
const activeProject = ref<string | undefined>(route.query.project as string | undefined)
const activeFilters = ref<Record<string, any>>(calendarFilterStore.buildFilterPayload())
const calendarRef = ref()
const querySectionRef = ref()
const activeQueryId = computed(() => calendarFilterStore.activeQueryId)

const filterSubmit = (payload: IssueFilter) => {
  activeProject.value = payload.project
  activeFilters.value = { ...payload }
  const range = calendarRef.value?.currentRange || { start: '', end: '' }
  calendarStore.fetchCalendarEvents(payload, range.start, range.end)
}

const onQueryClick = (query: any) => {
  querySectionRef.value?.applyQuery(query)
}

const onResetQuery = () => {
  querySectionRef.value?.resetFilter()
}

const loading = ref(true)
onBeforeMount(async () => {
  try {
    await workStore.fetchMemberList()
    await meetingStore.fetchCategoryList()
  } catch (err) {
    console.error('Failed to load calendar data:', err)
  } finally {
    loading.value = false
  }
})

const summary = computed(() => {
  const events = calendarStore.events
  const issues = events.filter(e => e.type === 'issue')
  return {
    total: issues.length,
    open: issues.filter(i => i.status && !i.status.closed).length,
    closed: issues.filter(i => i.status && i.status.closed).length,
  }
})
</script>

<template>
  <Loading :active="loading || calendarStore.loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query" :aside="true">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-calendar-clock" color="primary" size="small" class="mr-2" />
            캘린더
          </h5>
        </CCol>
      </CRow>

      <QuerySection
        ref="querySectionRef"
        :search-projects="allReadableProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :priority-list="priorityList"
        :meeting-categories="meetingCategories"
        :get-users="getUsers"
        @filter-submit="filterSubmit"
      />

      <CRow class="mb-3">
        <CCol>
          <SharedCalendar
            ref="calendarRef"
            :project-slug="activeProject"
            :issue-filters="activeFilters"
          />
        </CCol>
      </CRow>

      <CRow class="mb-3">
        <CCol>
          <SummaryStatus :summary="summary" />
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside>
      <SavedQueryAside
        target-type="calendar"
        :active-query-id="activeQueryId ?? undefined"
        :can-project-pub-query="canPubQuery"
        @on-query-click="onQueryClick"
        @on-reset-query="onResetQuery"
      />
    </template>
  </ContentBody>
</template>

<style lang="scss" scoped>
.border-dashed {
  border-style: dashed !important;
  border-width: 1.5px !important;
}

.gap-4 {
  gap: 1rem;
}
</style>

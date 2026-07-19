<script setup lang="ts">
import { computed, provide, ref, onBeforeMount } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useCompany } from '@/store/pinia/company.ts'
import { useCalendar } from '@/store/pinia/work_calendar'
import { useAccount } from '@/store/pinia/account'
import { useIssue } from '@/store/pinia/work_issue'
import type { Company } from '@/store/types/settings'
import type { IssueFilter } from '@/store/types/work_issue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import QuerySection from '@/views/_Work/Manages/Issues/components/QuerySection.vue'
import SharedCalendar from './components/SharedCalendar.vue'
import SummaryStatus from '@/views/_Work/Manages/Calendar/components/SummaryStatus.vue'
import Loading from '@/components/Loading/Index.vue'

const cBody = ref()
const sideNavCAll = () => cBody.value.toggle()

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

const allReadableProjects = computed(() => workStore.getAllReadableProjects)
const getUsers = computed(() => accStore.getUsers)
const getVersions = computed(() => workStore.getVersions)
const statusList = computed(() => issueStore.statusList)
const trackerList = computed(() => issueStore.trackerList)
const priorityList = computed(() => issueStore.priorityList)
const categoryList = computed(() => issueStore.categoryList)
const getIssues = computed(() => issueStore.getIssues)

const activeProject = ref<string | undefined>(route.query.project as string | undefined)
const activeFilters = ref<Record<string, any>>({})
const calendarRef = ref()

const filterSubmit = (payload: IssueFilter) => {
  activeProject.value = payload.project
  activeFilters.value = { ...payload }
  const range = calendarRef.value?.currentRange || { start: '', end: '' }
  calendarStore.fetchCalendarEvents(payload, range.start, range.end)
}

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchMemberList()
  loading.value = false
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

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>
            <v-icon icon="mdi-calendar-clock" color="primary" size="small" class="mr-2" />캘린더
          </h5>
        </CCol>
      </CRow>

      <QuerySection
        :search-projects="allReadableProjects"
        :status-list="statusList"
        :tracker-list="trackerList"
        :priority-list="priorityList"
        :category-list="categoryList"
        :get-issues="getIssues"
        :get-users="getUsers"
        :get-versions="getVersions"
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

    <template v-slot:aside></template>
  </ContentBody>
</template>

<style lang="scss" scoped>
:deep(.fc) {
  --fc-border-color: rgba(0, 0, 0, 0.05);
  --fc-daygrid-event-dot-width: 8px;

  .fc-scrollgrid {
    border-radius: 8px;
    overflow: hidden;
    border-color: var(--fc-border-color);
  }

  .fc-col-header-cell {
    padding: 8px 0;
    background: rgba(0, 0, 0, 0.02);
    font-weight: 600;
    color: #4f5d73; // CoreUI neutral text
  }

  .fc-col-header-cell-cushion {
    color: #4f5d73 !important;
    text-decoration: none !important;
  }

  .fc-daygrid-day-number {
    color: #4f5d73; // CoreUI neutral text
    padding: 4px 8px !important;
    text-decoration: none !important;
  }

  .fc-day-sun {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #e55353 !important; // CoreUI danger/red
    }
    background-color: rgba(229, 83, 83, 0.02);
  }
  .fc-day-sat {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #3399ff !important; // CoreUI info/blue
    }
    background-color: rgba(51, 153, 255, 0.02);
  }

  .fc-day-today {
    background: rgba(var(--v-theme-primary), 0.05) !important;
    .fc-daygrid-day-number {
      background: rgb(var(--v-theme-primary)) !important;
      color: white !important;
      border-radius: 4px;
      min-width: 24px;
      height: 24px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin: 4px;
    }
  }

  .fc-event {
    border: none;
    border-radius: 4px;
    padding: 1px 2px;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    transition:
      transform 0.1s ease,
      box-shadow 0.1s ease;
    cursor: pointer;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
      filter: brightness(1.1);
    }
  }

  .fc-event-title {
    font-weight: 500;
  }
}

.dark-theme :deep(.fc) {
  --fc-border-color: rgba(255, 255, 255, 0.1);

  .fc-col-header-cell {
    background: rgba(255, 255, 255, 0.05);
    color: #d1d5db;
  }

  .fc-col-header-cell-cushion {
    color: #d1d5db !important;
  }

  .fc-daygrid-day-number {
    color: #d1d5db;
  }

  .fc-day-sun {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #ef4444 !important;
    }
    background-color: rgba(239, 68, 68, 0.05);
  }
  .fc-day-sat {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #60a5fa !important;
    }
    background-color: rgba(96, 165, 250, 0.05);
  }
}

.border-dashed {
  border-style: dashed !important;
  border-width: 1.5px !important;
}

.gap-4 {
  gap: 1rem;
}
</style>

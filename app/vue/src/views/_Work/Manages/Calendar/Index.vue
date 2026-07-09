<script setup lang="ts">
import { computed, onBeforeMount, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import { useWork } from '@/store/pinia/work_project'
import { useCompany } from '@/store/pinia/company.ts'
import { useCalendar } from '@/store/pinia/work_calendar'
import type { Company } from '@/store/types/settings'
import type { IssueFilter } from '@/store/types/work_issue'
import Loading from '@/components/Loading/Index.vue'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import SharedCalendar from './components/SharedCalendar.vue'

const cBody = ref()
const comStore = useCompany()
const company = computed<Company | null>(() => comStore.company)
const comName = computed(() => company?.value?.name)

const route = useRoute()
const workStore = useWork()
const calendarStore = useCalendar()

provide('navMenu', navMenu)
provide('query', route?.query)

const allProjects = computed(() => workStore.getAllProjects)

const sideNavCAll = () => cBody.value.toggle()

const activeProject = ref<string | undefined>(route.query.project as string | undefined)
const calendarRef = ref()

const filterSubmit = (payload: IssueFilter) => {
  activeProject.value = payload.project
  const range = calendarRef.value?.currentRange || { start: '', end: '' }
  calendarStore.fetchCalendarEvents(payload.project, range.start, range.end)
}

const summary = computed(() => {
  const events = calendarStore.events
  const issues = events.filter(e => e.type === 'issue')
  return {
    total: issues.length,
    open: issues.filter(i => i.status && !i.status.closed).length,
    closed: issues.filter(i => i.status && i.status.closed).length,
  }
})

const loading = ref(true)

onBeforeMount(async () => {
  await workStore.fetchAllProjectList()
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
        </CCol>
      </CRow>

      <SearchList :all-projects="allProjects" @filter-submit="filterSubmit" />

      <CRow class="mb-3">
        <CCol>
          <SharedCalendar ref="calendarRef" :project-slug="activeProject" />
        </CCol>
      </CRow>

      <v-card variant="outlined" class="mt-4 pa-4 border-dashed rounded-lg">
        <CRow align="center">
          <CCol md="4" class="border-right d-none d-md-block">
            <div class="text-subtitle-2 text-grey mb-2">이번 달 업무 현황</div>
            <div class="d-flex justify-space-around align-center">
              <div class="text-center">
                <div class="text-h6 font-weight-bold">{{ summary.total }}</div>
                <div class="text-caption text-grey">전체</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-info">{{ summary.open }}</div>
                <div class="text-caption text-grey">진행중</div>
              </div>
              <div class="text-center">
                <div class="text-h6 font-weight-bold text-success">{{ summary.closed }}</div>
                <div class="text-caption text-grey">완료</div>
              </div>
            </div>
          </CCol>
          <CCol md="8" class="pl-md-6">
            <div class="text-subtitle-2 text-grey mb-2">일정 가이드</div>
            <div class="d-flex flex-wrap gap-4">
              <div class="d-flex align-center mr-4">
                <v-icon icon="mdi-arrow-right-bold" color="success" size="small" class="mr-1" />
                <span class="text-body-2">오늘 시작</span>
              </div>
              <div class="d-flex align-center mr-4">
                <v-icon icon="mdi-arrow-left-bold" color="danger" size="small" class="mr-1" />
                <span class="text-body-2">오늘 종료</span>
              </div>
              <div class="d-flex align-center">
                <v-icon icon="mdi-rhombus" color="danger" size="small" class="mr-1" />
                <span class="text-body-2">오늘 시작/종료</span>
              </div>
            </div>
            <div class="mt-2 text-caption text-grey-darken-1">
              * 바(Bar)의 색상은 업무의 현재 상태(신규/진행/완료 등)를 나타냅니다.
            </div>
          </CCol>
        </CRow>
      </v-card>
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

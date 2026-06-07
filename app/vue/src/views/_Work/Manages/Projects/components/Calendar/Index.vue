<script lang="ts" setup>
import { computed, onBeforeMount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useStore } from '@/store'
import { useIssue } from '@/store/pinia/work_issue'
import { useWork } from '@/store/pinia/work_project'
import { addDaysToDate, cutString, getToday } from '@/utils/baseMixins'
import type { Issue, IssueFilter } from '@/store/types/work_issue'
import Loading from '@/components/Loading/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const route = useRoute()
const router = useRouter()
const store = useStore()
const issueStore = useIssue()
const workStore = useWork()

const allProjects = computed(() => workStore.getAllProjects)
const isDark = computed(() => store.theme === 'dark')

const getEventColor = (status: { pk: number; closed: boolean }) => {
  const colors = {
    light: {
      1: '#e57373', // 신규 (Muted Red)
      2: '#64b5f6', // 진행 (Muted Blue)
      3: '#ffb74d', // 검토 (Muted Amber)
      4: '#90a4ae', // 보류 (Muted Blue Grey)
      5: '#81c784', // 종료 (Muted Green)
      6: '#78909c', // 거절 (Deep Blue Grey)
      default: '#cfd8dc',
    },
    dark: {
      1: '#b35c5c', // 신규 (Muted Deep Red)
      2: '#5c86b3', // 진행 (Muted Steel Blue)
      3: '#b3915c', // 검토 (Muted Ochre)
      4: '#64748b', // 보류 (Slate Grey)
      5: '#5cb377', // 종료 (Muted Sage)
      6: '#475569', // 거절 (Dark Slate)
      default: '#475569',
    },
  }

  const palette = isDark.value ? colors.dark : colors.light
  return (palette as any)[status.pk] || palette.default
}

const calendarEvents = computed(() => {
  return issueStore.issueList.map((issue: Issue) => {
    const assignee = issue.assigned_to ? `(${issue.assigned_to.username})` : ''
    return {
      id: issue.pk.toString(),
      title: `[${issue.tracker.name}] ${cutString(issue.subject, 15)}${assignee}`,
      start: issue.start_date,
      end: issue.due_date ? addDaysToDate(issue.due_date, 1) : addDaysToDate(issue.start_date, 1),
      allDay: true,
      backgroundColor: getEventColor(issue.status),
      borderColor: getEventColor(issue.status),
      extendedProps: {
        project: issue.project.slug,
        pk: issue.pk,
        start: issue.start_date,
        end: issue.due_date,
        expected_duration: issue.expected_duration,
      },
    }
  })
})

const handleEventClick = (info: any) => {
  const { project, pk } = info.event.extendedProps
  router.push({
    name: '(업무) - 보기',
    params: { projId: project, issueId: pk },
  })
}

const renderEventContent = (eventInfo: any) => {
  const { start, end, expected_duration } = eventInfo.event.extendedProps // start_date, due_date
  const today = getToday()
  const isStartToday = start === today
  const isEndToday = !!end && end === today
  const isSameDayTask = expected_duration === '0'

  let icon = ''
  let color = 'white'

  // 우선순위 1: 오늘 시작하고 종료하는 업무 (기한이 오늘이거나 당일 처리인 경우)
  if (isStartToday && (isEndToday || isSameDayTask)) {
    icon = 'mdi-rhombus' // 오늘 시작하고 종료
    color = '#f87171' // danger
  }
  // 우선순위 2: 오늘 시작하는 업무
  else if (isStartToday) {
    icon = 'mdi-arrow-right-bold' // 오늘 시작
    color = '#4ade80' // success
  }
  // 우선순위 3: 오늘 종료하는 업무
  else if (isEndToday) {
    icon = 'mdi-arrow-left-bold' // 오늘 종료
    color = '#f87171' // danger
  }

  return {
    html: `
      <div class="fc-event-main-frame" style="overflow: hidden; text-overflow: ellipsis;">
        <div class="fc-event-title-container">
          <div class="fc-event-title fc-sticky" style="font-size: 0.85em; white-space: nowrap;">
            ${icon ? `<i class="mdi ${icon}" style="color: ${color}; font-size: 12px;"></i>` : ''}
            ${eventInfo.event.title}
          </div>
        </div>
      </div>
    `,
  }
}

const calendarOptions = computed(() => ({
  timeZone: 'local',
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  weekends: true,
  selectable: true,
  height: 630,
  showNonCurrentDates: false,
  events: calendarEvents.value,
  eventClick: handleEventClick,
  eventContent: renderEventContent,
}))

const fetchIssues = async (slug?: string) => {
  if (slug) {
    await issueStore.fetchIssueList({ project: slug })
  }
}

watch(
  () => route.params?.projId,
  nVal => {
    if (nVal) fetchIssues(nVal as string)
  },
)

const filterSubmit = (payload: IssueFilter) => {
  issueStore.fetchIssueList({ ...payload, project: route.params.projId as string })
}

const summary = computed(() => {
  const issues = issueStore.issueList
  return {
    total: issues.length,
    open: issues.filter(i => !i.status.closed).length,
    closed: issues.filter(i => i.status.closed).length,
  }
})

const loading = ref(true)
onBeforeMount(async () => {
  await workStore.fetchAllIssueProjectList()
  if (route.params.projId) {
    await fetchIssues(route.params.projId as string)
  }
  loading.value = false
})
</script>

<template>
  <Loading v-model:active="loading" />
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>달력</h5>
        </CCol>
      </CRow>

      <SearchList :all-projects="allProjects" @filter-submit="filterSubmit" />

      <CRow class="mb-3">
        <CCol>
          <FullCalendar :options="calendarOptions" />
        </CCol>
      </CRow>

      <v-card variant="outlined" class="mt-4 pa-4 border-dashed rounded-lg">
        <CRow align="center">
          <CCol md="4" class="border-right d-none d-md-block">
            <div class="text-subtitle-2 text-grey mb-2">프로젝트 업무 현황</div>
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

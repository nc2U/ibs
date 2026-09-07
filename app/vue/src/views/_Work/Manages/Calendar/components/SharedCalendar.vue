<script lang="ts" setup>
import { computed, type PropType, ref } from 'vue'
import { useRouter } from 'vue-router'
import { message } from '@/utils/helper.ts'
import { usePerms } from '@/composables/usePerms.ts'
import { addDaysToDate, getToday } from '@/utils/baseMixins'
import { useStore } from '@/store'
import { useCalendar } from '@/store/pinia/work_calendar'
import type { CalendarOptions } from '@fullcalendar/core'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const props = defineProps({
  projectSlug: { type: String, default: undefined },
  issueFilters: { type: Object as PropType<Record<string, any>>, default: () => ({}) },
})

const router = useRouter()
const store = useStore()
const calendarStore = useCalendar()

const { can, PERM } = usePerms()
const canCalendarRead = computed(() => can(PERM.CALENDAR_READ))

const isDark = computed(() => store.isDark)

const getEventColor = (type: 'issue' | 'meeting', status?: { pk: number; closed: boolean }) => {
  if (type === 'meeting' || !status) {
    return isDark.value ? '#a78bfa' : '#d1c4e9'
  }
  const colors = {
    light: {
      1: '#e57373',
      2: '#64b5f6',
      3: '#ffb74d',
      4: '#90a4ae',
      5: '#81c784',
      6: '#78909c',
      default: '#cfd8dc',
    },
    dark: {
      1: '#f87171',
      2: '#38bdf8',
      3: '#fbbf24',
      4: '#94a3b8',
      5: '#4ade80',
      6: '#64748b',
      default: '#64748b',
    },
  }
  const palette = isDark.value ? colors.dark : colors.light
  return (palette as any)[status.pk] || palette.default
}

const calendarEvents = computed(() => {
  return calendarStore.events.map(event => {
    if (event.type === 'meeting') {
      return {
        id: event.id,
        title: event.title,
        start: event.start || undefined,
        allDay: false,
        backgroundColor: getEventColor('meeting'),
        borderColor: getEventColor('meeting'),
        extendedProps: {
          type: 'meeting',
          project: event.project,
          pk: parseInt(event.id.replace('m-', '')),
        },
      }
    }

    // issue
    return {
      id: event.id,
      title: event.title,
      start: event.start,
      end: event.end ? addDaysToDate(event.end, 1) : addDaysToDate(event.start, 1),
      allDay: true,
      backgroundColor: getEventColor('issue', event.status),
      borderColor: getEventColor('issue', event.status),
      extendedProps: {
        type: 'issue',
        project: event.project,
        pk: parseInt(event.id),
        start: event.start,
        end: event.end,
        expected_duration: event.expected_duration,
        status: event.status,
      },
    }
  })
})

const handleEventClick = (info: any) => {
  if (!canCalendarRead.value) return

  const { type, project, pk } = info.event.extendedProps
  if (type === 'issue') {
    router.push({
      name: '(업무) - 보기',
      params: { projId: project, issueId: pk },
    })
  } else if (type === 'meeting') {
    if (project) {
      router.push({
        name: '(회의) - 보기',
        params: { projId: project, meetingId: pk },
      })
    } else {
      message('warning', '', '소속 프로젝트 슬러그가 없어 회의록 상세 페이지로 이동할 수 없습니다.')
    }
  }
}

const renderEventContent = (eventInfo: any) => {
  const { type, status } = eventInfo.event.extendedProps
  if (type === 'meeting') {
    return {
      html: `
        <div class="fc-event-main-frame d-flex align-items-center" style="overflow: hidden; text-overflow: ellipsis; padding: 1px 4px;">
          <span class="fc-event-title" style="font-size: 0.85em; font-weight: 600; white-space: nowrap;">
            📅 ${eventInfo.event.title}
          </span>
        </div>
      `,
    }
  }

  const { start, end, expected_duration } = eventInfo.event.extendedProps
  const today = getToday()
  const isStartToday = start === today
  const isEndToday = !!end && end === today
  const isSameDayTask = expected_duration === '0'
  const isClosed = !!status?.closed

  let icon = ''
  let color = 'white'

  if (isClosed) {
    icon = 'mdi-check'
    color = '#ffffff'
  } else if (isStartToday && (isEndToday || isSameDayTask)) {
    icon = 'mdi-rhombus'
    color = '#f87171'
  } else if (isStartToday) {
    icon = 'mdi-arrow-right-bold'
    color = '#4ade80'
  } else if (isEndToday) {
    icon = 'mdi-arrow-left-bold'
    color = '#f87171'
  }

  const titleStyle = isClosed ? 'text-decoration: line-through; opacity: 0.85;' : ''

  return {
    html: `
      <div class="fc-event-main-frame" style="overflow: hidden; text-overflow: ellipsis;">
        <div class="fc-event-title-container">
          <div class="fc-event-title fc-sticky" style="font-size: 0.85em; white-space: nowrap; ${titleStyle}">
            ${icon ? `<i class="mdi ${icon}" style="color: ${color}; font-size: 12px; margin-right: 2px;"></i>` : ''}
            ${eventInfo.event.title}
          </div>
        </div>
      </div>
    `,
  }
}

// 캘린더의 현재 조회 범위를 기록해두고 외부 필터에서 쓸 수 있도록 노출
const currentRange = ref({ start: '', end: '' })

const handleDatesSet = (dateInfo: any) => {
  const startStr = dateInfo.startStr.split('T')[0]
  const endStr = dateInfo.endStr.split('T')[0]
  currentRange.value = { start: startStr, end: endStr }

  const reqFilters = { ...props.issueFilters }
  if (props.projectSlug && !reqFilters.project) {
    reqFilters.project = props.projectSlug
  }
  calendarStore.fetchCalendarEvents(reqFilters, startStr, endStr)
}

const handleEventDidMount = (info: any) => {
  // 권한이 있는 경우에만 pointer 클래스 추가
  if (canCalendarRead.value) info.el.classList.add('pointer')
  else info.el.style.cursor = 'not-allowed' // 권한이 없으면 기본 커서로 강제 지정
}

const calendarOptions = computed<CalendarOptions>(() => ({
  timeZone: 'local',
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  weekends: true,
  selectable: true,
  firstDay: 1,
  height: 'auto',
  showNonCurrentDates: false,
  events: calendarEvents.value,
  eventDidMount: handleEventDidMount,
  eventClick: handleEventClick,
  eventContent: renderEventContent,
  datesSet: handleDatesSet,
}))

defineExpose({ calendarOptions, currentRange })
</script>

<template>
  <FullCalendar :key="`${canCalendarRead}-${isDark}`" :options="calendarOptions" />
</template>

<style lang="scss" scoped>
// Inherit/share styles from parent or define common styles here
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
    color: #4f5d73;
  }

  .fc-col-header-cell-cushion {
    color: #4f5d73 !important;
    text-decoration: none !important;
  }

  .fc-daygrid-day-number {
    color: #4f5d73;
    padding: 4px 8px !important;
    text-decoration: none !important;
  }

  .fc-day-sun {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #e55353 !important;
    }
    background-color: rgba(229, 83, 83, 0.02);
  }
  .fc-day-sat {
    .fc-col-header-cell-cushion,
    .fc-daygrid-day-number {
      color: #3399ff !important;
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

  .fc-event,
  a.fc-event {
    border: none;
    border-radius: 4px;
    padding: 1px 2px;
    color: #1e293b !important;
    text-decoration: none !important;
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    transition:
      transform 0.1s ease,
      box-shadow 0.1s ease;
    cursor: pointer;

    &:hover {
      transform: translateY(-1px);
      box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15);
      filter: brightness(1.1);
      color: #1e293b !important;
      text-decoration: none !important;
    }
  }

  .fc-event-title {
    font-weight: 500;
    color: inherit;
  }
}

:global(body.dark-theme) :deep(.fc),
:global(.dark-theme) :deep(.fc),
:global(.dark-layout) :deep(.fc) {
  --fc-border-color: rgba(255, 255, 255, 0.1);

  .fc-col-header-cell {
    background: #252631 !important;
    color: #e5e7eb !important;
    border-color: rgba(255, 255, 255, 0.1) !important;
  }

  .fc-col-header-cell-cushion {
    color: #e5e7eb !important;
  }

  .fc-daygrid-day-number {
    color: #d1d5db !important;
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

  .fc-event,
  a.fc-event,
  .fc-event-title {
    color: #ffffff !important;
    font-weight: 600;

    &:hover {
      color: #ffffff !important;
    }
  }
}
</style>

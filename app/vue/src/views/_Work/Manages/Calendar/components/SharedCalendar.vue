<script lang="ts" setup>
import { computed, ref } from 'vue'
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
})

const router = useRouter()
const store = useStore()
const calendarStore = useCalendar()

const { can, PERM } = usePerms()
const canCalendarRead = computed(() => can(PERM.CALENDAR_READ))

const isDark = computed(() => store.theme === 'dark')

const getEventColor = (type: 'issue' | 'meeting', status?: { pk: number; closed: boolean }) => {
  if (type === 'meeting' || !status) {
    return '#9575cd'
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
      1: '#b35c5c',
      2: '#5c86b3',
      3: '#b3915c',
      4: '#64748b',
      5: '#5cb377',
      6: '#475569',
      default: '#475569',
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
        backgroundColor: '#9575cd',
        borderColor: '#9575cd',
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
  const { type } = eventInfo.event.extendedProps
  if (type === 'meeting') {
    return {
      html: `<div class="fc-event-main-frame" style="overflow: hidden; text-overflow: ellipsis;">
               <div class="fc-event-title" style="font-size: 0.85em; white-space: nowrap;">${eventInfo.event.title}</div>
             </div>`,
    }
  }

  const { start, end, expected_duration } = eventInfo.event.extendedProps
  const today = getToday()
  const isStartToday = start === today
  const isEndToday = !!end && end === today
  const isSameDayTask = expected_duration === '0'

  let icon = ''
  let color = 'white'

  if (isStartToday && (isEndToday || isSameDayTask)) {
    icon = 'mdi-rhombus'
    color = '#f87171'
  } else if (isStartToday) {
    icon = 'mdi-arrow-right-bold'
    color = '#4ade80'
  } else if (isEndToday) {
    icon = 'mdi-arrow-left-bold'
    color = '#f87171'
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

// 달력의 현재 조회 범위를 기록해두고 외부 필터에서 쓸 수 있도록 노출
const currentRange = ref({ start: '', end: '' })

const handleDatesSet = (dateInfo: any) => {
  const startStr = dateInfo.startStr.split('T')[0]
  const endStr = dateInfo.endStr.split('T')[0]
  currentRange.value = { start: startStr, end: endStr }
  calendarStore.fetchCalendarEvents(props.projectSlug, startStr, endStr)
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
  height: 630,
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
  <FullCalendar :key="`${canCalendarRead}`" :options="calendarOptions" />
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
  // ... rest of dark theme styles
}
</style>

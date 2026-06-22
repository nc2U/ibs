<script lang="ts" setup>
import { computed, inject, onBeforeMount, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from '@/store'
import { useIssue } from '@/store/pinia/work_issue'
import { useMeeting } from '@/store/pinia/work_meeting'
import { addDaysToDate, cutString, getToday } from '@/utils/baseMixins'
import type { Issue } from '@/store/types/work_issue'
import type { Meeting } from '@/store/types/work_meeting'
import type { CalendarOptions } from '@fullcalendar/core'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const props = defineProps({
  projectId: { type: String, default: undefined },
})

const router = useRouter()
const store = useStore()
const issueStore = useIssue()
const meetingStore = useMeeting()

const isDark = computed(() => store.theme === 'dark')

const getEventColor = (status: { pk: number; closed: boolean }) => {
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
  const issueEvents = issueStore.issueList.map((issue: Issue) => {
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
        type: 'issue',
        project: issue.project.slug,
        pk: issue.pk,
      },
    }
  })

  const meetingEvents = meetingStore.meetingList.map((meeting: Meeting) => {
    return {
      id: `m-${meeting.pk}`,
      title: `[회의] ${cutString(meeting.title, 15)}`,
      start: meeting.meeting_date || undefined,
      allDay: false,
      backgroundColor: '#9575cd',
      borderColor: '#9575cd',
      extendedProps: {
        type: 'meeting',
        project: meeting.project_desc?.slug,
        pk: meeting.pk,
      },
    }
  })

  return [...issueEvents, ...meetingEvents]
})

const handleEventClick = (info: any) => {
  const { type, project, pk } = info.event.extendedProps
  if (type === 'issue') {
    router.push({
      name: '(업무) - 보기',
      params: { projId: project, issueId: pk },
    })
  } else if (type === 'meeting') {
    const routeName = project ? '(회의) - 보기' : '회의 - 보기'
    const params = project ? { projId: project, meetingId: pk } : { meetingId: pk }
    router.push({ name: routeName, params: params })
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

const calendarOptions = computed<CalendarOptions>(() => ({
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

defineExpose({ calendarOptions })
</script>

<template>
  <FullCalendar :options="calendarOptions" />
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

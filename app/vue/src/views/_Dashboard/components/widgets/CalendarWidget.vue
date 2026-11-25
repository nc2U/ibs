<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { type CalendarEvent, useCalendar } from '@/store/pinia/work_calendar'
import { useRouter } from 'vue-router'
import { cutString, dateFormat, getToday } from '@/utils/baseMixins'
import WidgetWrapper from '../WidgetWrapper.vue'

interface WeekDay {
  dateStr: string
  dayNum: number
  dayOfWeek: number
  isToday: boolean
}

defineProps<{
  widgetId: string
  title: string
  icon?: string
}>()

const router = useRouter()
const calendarStore = useCalendar()
const todayStr = getToday()

// 7일간의 날짜 데이터 생성 (월요일 ~ 일요일)
const getWeekDays = (): WeekDay[] => {
  const current = new Date()
  const day = current.getDay() // 0: 일, 1: 월, ... 6: 토

  // 이번 주 월요일 계산 (오늘이 일요일(0)이면 6일 전, 그 외에는 day - 1일 전)
  const monday = new Date(current)
  const distanceToMonday = day === 0 ? 6 : day - 1
  monday.setDate(current.getDate() - distanceToMonday)

  const days: WeekDay[] = []
  for (let i = 0; i < 7; i++) {
    const d = new Date(monday)
    d.setDate(monday.getDate() + i)
    days.push({
      dateStr: dateFormat(d),
      dayNum: d.getDate(),
      dayOfWeek: d.getDay(), // 0 ~ 6
      isToday: dateFormat(d) === todayStr,
    })
  }
  return days
}

const weekDays = ref<WeekDay[]>(getWeekDays())

// 요일 한글 매핑
const dayNames = ['일', '월', '화', '수', '목', '금', '토']

// 일정 색상 계산 함수
const getEventColor = (type: 'issue' | 'meeting', status?: { pk: number; closed: boolean }) => {
  if (type === 'meeting' || !status) {
    return 'deep-purple-lighten-2'
  }
  const colors: Record<number, string> = {
    1: 'red-lighten-1',
    2: 'blue-lighten-1',
    3: 'orange-lighten-1',
    4: 'blue-grey-lighten-1',
    5: 'green-lighten-1',
    6: 'blue-grey-darken-1',
  }
  return colors[status.pk] || 'grey-lighten-1'
}

// 가져온 일정을 시작~종료 범위에 맞춰 요일별로 분배 (다일 일정 포함)
const weekEvents = computed<Record<string, CalendarEvent[]>>(() => {
  const map: Record<string, CalendarEvent[]> = {}
  weekDays.value.forEach(d => {
    map[d.dateStr] = []
  })

  calendarStore.events.forEach(event => {
    const startStr = event.start
    if (!startStr) return
    const endStr = event.end && event.end >= startStr ? event.end : startStr

    weekDays.value.forEach(d => {
      if (d.dateStr >= startStr && d.dateStr <= endStr) {
        map[d.dateStr].push(event)
      }
    })
  })

  return map
})

const fetchCalendar = async () => {
  if (weekDays.value.length > 0) {
    const startStr = weekDays.value[0].dateStr
    const endStr = weekDays.value[6].dateStr
    await calendarStore.fetchCalendarEvents(undefined, startStr, endStr)
  }
}

onMounted(fetchCalendar)

const handleEventClick = (event: CalendarEvent) => {
  if (!event.project) return
  if (event.type === 'issue') {
    const pk = parseInt(event.id, 10)
    if (Number.isNaN(pk)) return
    router.push({
      name: '(업무) - 보기',
      params: { projId: event.project, issueId: pk },
    })
  } else if (event.type === 'meeting') {
    const pk = parseInt(event.id.replace('m-', ''), 10)
    if (Number.isNaN(pk)) return
    router.push({
      name: '(회의) - 보기',
      params: { projId: event.project, meetingId: pk },
    })
  }
}
</script>

<template>
  <WidgetWrapper
    :widget-id="widgetId"
    :title="title"
    :icon="icon"
    refreshable
    @refresh="fetchCalendar"
  >
    <div class="calendar-widget">
      <!-- 7열 주간 캘린더 그리드 (레드마인 스타일) -->
      <div class="week-grid">
        <div
          v-for="day in weekDays"
          :key="day.dateStr"
          class="day-col"
          :class="{
            'is-today': day.isToday,
            'is-sun': day.dayOfWeek === 0,
            'is-sat': day.dayOfWeek === 6,
          }"
        >
          <!-- 요일 및 날짜 헤더 -->
          <div class="day-header text-center py-1">
            <span class="text-caption font-weight-medium d-block">{{
              dayNames[day.dayOfWeek]
            }}</span>
            <span class="day-number font-weight-bold">{{ day.dayNum }}</span>
          </div>

          <!-- 일정 목록 구역 -->
          <div class="day-content pa-1">
            <div
              v-for="event in weekEvents[day.dateStr]"
              :key="event.id"
              class="event-bar text-truncate text-caption px-1 mb-1 rounded cursor-pointer text-truncate"
              :class="`bg-${getEventColor(event.type, event.status)} text-white`"
              :title="event.title"
              @click="handleEventClick(event)"
            >
              <v-icon
                :icon="
                  event.type === 'meeting' ? 'mdi-account-group' : 'mdi-clipboard-text-outline'
                "
                size="10"
                class="mr-1"
              />
              {{ cutString(event.title, 24) }}
            </div>
          </div>
        </div>
      </div>

      <v-btn
        variant="text"
        color="primary"
        size="small"
        class="mt-3"
        block
        :to="{ name: '캘린더' }"
      >
        전체 일정 보기
        <v-icon icon="mdi-chevron-right" size="small" />
      </v-btn>
    </div>
  </WidgetWrapper>
</template>

<style scoped lang="scss">
.calendar-widget {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.week-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  border: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  border-radius: 8px;
  overflow: hidden;
  background-color: #ffffff;
}

body.dark-theme .week-grid {
  background-color: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.08);
}

.day-col {
  border-right: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  min-height: 160px;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: transparent;

  &:last-child {
    border-right: none;
  }
}

body.dark-theme .day-col {
  border-right-color: rgba(255, 255, 255, 0.08);
}

.day-header {
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
  background-color: rgba(var(--v-theme-on-surface), 0.02);
}

body.dark-theme .day-header {
  border-bottom-color: rgba(255, 255, 255, 0.08);
  background-color: rgba(255, 255, 255, 0.05);
}

.day-number {
  font-size: 1.1rem;
}

.is-sun {
  .day-header {
    color: #e55353;
    background-color: rgba(229, 83, 83, 0.03);
  }
}

.is-sat {
  .day-header {
    color: #3399ff;
    background-color: rgba(51, 153, 255, 0.03);
  }
}

.is-today {
  outline: 2px solid rgb(var(--v-theme-primary));
  z-index: 1;
  .day-header {
    background-color: rgb(var(--v-theme-primary)) !important;
    color: #ffffff !important;
  }
}

.day-content {
  flex-grow: 1;
}

.event-bar {
  font-size: 0.75rem;
  line-height: 1.4;
  cursor: pointer;
  transition: opacity 0.2s;
  user-select: none;

  &:hover {
    opacity: 0.85;
  }
}
</style>

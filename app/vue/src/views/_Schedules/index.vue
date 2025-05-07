<script lang="ts" setup>
import { computed, onBeforeMount, reactive, ref, watch } from 'vue'
import { useAccount } from '@/store/pinia/account'
import { useSchedule } from '@/store/pinia/schedule'
import { addDays, diffDate } from '@/utils/baseMixins'
import type { Event } from '@/store/types/schedule'
import type {
  EventApi,
  DateSelectArg,
  EventClickArg,
  DatesSetArg,
  EventChangeArg,
  CalendarOptions,
} from '@fullcalendar/core'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import timeGridPlugin from '@fullcalendar/timegrid'
import interactionPlugin from '@fullcalendar/interaction'
import CalendarInfo from './components/CalendarInfo.vue'
import FormModal from '@/components/Modals/FormModal.vue'
import ConfirmModal from '@/components/Modals/ConfirmModal.vue'
import AlertModal from '@/components/Modals/AlertModal.vue'

const cal = ref()
const month = ref('')
const scheduleStore = useSchedule()
const currentEvents = computed(() => scheduleStore.events)

const fetchScheduleList = (mon = '') => scheduleStore.fetchScheduleList(mon)
const createSchedule = (payload: Event) => scheduleStore.createSchedule(payload)
const updateSchedule = (payload: { pk: string; data: Event }) =>
  scheduleStore.updateSchedule(payload)

const mode = ref<'create' | 'update'>('create')

const refFormModal = ref()
const refAlertModal = ref()
const eventId = ref<string>('')
const eventTitle = ref('')

type CalEvent = {
  start: string
  end: string
  allDay: boolean
}

const newEvent = reactive<CalEvent>({
  start: '',
  end: '',
  allDay: true,
})

const accountStore = useAccount()
const handleDateSelect = (selectInfo: DateSelectArg) => {
  if (accountStore.staffAuth) {
    mode.value = 'create'
    eventTitle.value = ''
    refFormModal.value.callModal()
    const calendarApi = selectInfo.view.calendar
    calendarApi.unselect() // clear date selection
    newEvent.start = selectInfo.startStr
    newEvent.end = selectInfo.endStr
    newEvent.allDay = selectInfo.allDay
  } else
    refAlertModal.value.callModal(
      '',
      '스태프(일정 등록) 권한이 없습니다. 관리자에게 문의하여 주십시요.',
    )
}

const eventManagement = () => {
  const eventData = { title: eventTitle.value, ...newEvent }
  if (mode.value === 'create') createSchedule(eventData)
  else if (mode.value === 'update')
    updateSchedule({
      pk: eventId.value,
      ...{ data: eventData },
    })
  refFormModal.value.close()
}

type CurrEvent = EventApi & { _instance: { range: { start: Date; end: Date } } }

const transformData = (event: CurrEvent) => {
  const title = event.title
  const allDay = event.allDay
  const s = event._instance?.range.start.toISOString().replace('.000Z', '+09:00')
  const e = event._instance?.range.end.toISOString().replace('.000Z', '+09:00')
  const start = allDay ? s?.substring(0, 10) : s
  const end = allDay ? e?.substring(0, 10) : e
  return { title, allDay, start, end }
}

const handleChange = (el: EventChangeArg) => {
  const pk = el.event.id
  const eventDate = transformData(el.event as CurrEvent)
  scheduleStore.updateSchedule({ pk, data: eventDate })
}

const refConfirmModal = ref()
const handleEventClick = (clickInfo: EventClickArg) => {
  if (accountStore.staffAuth) {
    mode.value = 'update'
    eventId.value = clickInfo.event.id
    eventTitle.value = clickInfo.event.title
    newEvent.start = clickInfo.event.startStr
    newEvent.end = clickInfo.event.endStr
    newEvent.allDay = clickInfo.event.allDay
    refFormModal.value.callModal()
  } else
    refAlertModal.value.callModal(
      '',
      '스태프(일정 수정) 권한이 없습니다. 관리자에게 문의하여 주십시요.',
    )
}

const removeConfirm = () => {
  refFormModal.value.close()
  refConfirmModal.value.callModal()
}

const eventRemove = () => {
  const mon = newEvent.start.substring(0, 7)
  scheduleStore.deleteSchedule(eventId.value, mon)
  refConfirmModal.value.close()
}

const handleMonthChange = (payload: DatesSetArg) => {
  const diff = diffDate(payload.start, new Date(payload.end))
  const addDay = diff > 10 ? 7 : 1
  const date = new Date(addDays(new Date(payload.start), addDay))
  month.value = date.toISOString().substring(0, 7)
}

watch(month, val => fetchScheduleList(val))

const calendarOptions = reactive<CalendarOptions>({
  plugins: [
    dayGridPlugin,
    timeGridPlugin,
    interactionPlugin, // needed for dateClick
  ],
  headerToolbar: {
    left: 'prev,next today',
    center: 'title',
    right: 'dayGridMonth,timeGridWeek,timeGridDay',
  },
  initialView: 'dayGridMonth',
  events: currentEvents as any,
  editable: true,
  selectable: true,
  selectMirror: true,
  dayMaxEvents: true,

  weekends: true,

  select: handleDateSelect,
  eventClick: handleEventClick,
  datesSet: handleMonthChange, // prev, next button click event

  // you can update a remote database when these fire:
  eventAdd: () => console.log('created!'),
  eventChange: handleChange,
  eventRemove: () => console.log('deleted!'),
})

const handleWeekendsToggle = () => {
  calendarOptions.weekends = !calendarOptions.weekends // update a property
}

onBeforeMount(() => {
  fetchScheduleList(month.value)
})
</script>

<template>
  <div class="demo-app">
    <CRow>
      <CCol md="9">
        <CCard>
          <CCardHeader class="text-body">
            <CIcon name="cil-calendar" class="mr-2" />
            <h6 class="d-inline">Calendar</h6>
            <CBadge color="primary" class="ml-2">IBS</CBadge>
          </CCardHeader>
          <CCardBody>
            <div class="demo-app text-body">
              <div class="demo-app-main">
                <FullCalendar ref="cal" class="demo-app-calendar" :options="calendarOptions">
                  <template #eventContent="arg">
                    <b>{{ arg.timeText }} </b>
                    <i class="ml-1">{{ arg.event.title }}</i>
                  </template>
                </FullCalendar>
              </div>
            </div>
          </CCardBody>
        </CCard>
      </CCol>

      <CalendarInfo
        :calendar-options="calendarOptions"
        :current-events="currentEvents as any"
        @weekends-toggle="handleWeekendsToggle"
      />
    </CRow>
  </div>

  <FormModal ref="refFormModal">
    <template #icon>
      <v-icon
        icon="mdi-calendar-clock-outline"
        color="blue-grey-darken-1"
        class="mr-2"
        size="small"
      />
    </template>
    <template #header> 진행 일정 - 이벤트 {{ mode === 'create' ? '등록' : '편집' }}</template>
    <template #default>
      <CModalBody>
        <CRow>
          <CCol>
            <CFormInput
              id="event-title"
              v-model="eventTitle"
              type="text"
              placeholder="진행 일정"
              @keydown.enter="eventManagement"
            />
          </CCol>
        </CRow>
      </CModalBody>
      <CModalFooter>
        <v-btn color="light" @click="refFormModal.close"> 닫기</v-btn>
        <v-btn v-if="mode === 'create'" color="primary" @click="eventManagement"> 등록</v-btn>
        <v-btn v-if="mode === 'update'" color="success" @click="eventManagement"> 수정</v-btn>
        <v-btn v-if="mode === 'update'" color="warning" @click="removeConfirm"> 삭제</v-btn>
      </CModalFooter>
    </template>
  </FormModal>

  <ConfirmModal ref="refConfirmModal">
    <template #icon>
      <v-icon icon="mdi-trash-can-outline" color="blue-grey-darken-1" class="mr-2" size="small" />
    </template>
    <template #header> 진행 일정 - 이벤트 삭제</template>
    [{{ eventTitle }}] - 삭제 후 복구할 수 없습니다. 해당 일정을 삭제 하시겠습니까?
    <template #footer>
      <v-btn color="warning" @click="eventRemove">삭제</v-btn>
    </template>
  </ConfirmModal>

  <AlertModal ref="refAlertModal" />
</template>

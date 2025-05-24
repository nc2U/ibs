<script lang="ts" setup>
import { computed, onBeforeMount, ref } from 'vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'

const emit = defineEmits(['aside-visible'])

const cBody = ref()
const toggle = () => cBody.value.toggle()
defineExpose({ toggle })

const calendarOptions = computed(() => ({
  timeZone: 'local',
  plugins: [dayGridPlugin, interactionPlugin],
  initialView: 'dayGridMonth',
  weekends: true,
  // dateClick: handleDateClick,
  selectable: true,
  height: 630,
  showNonCurrentDates: false,
  events: [{ title: 'Meeting', start: new Date() }],
}))

const handleDateClick = (arg: any) => alert('date click! ' + arg.dateStr)

onBeforeMount(() => emit('aside-visible', true))
</script>

<template>
  <ContentBody ref="cBody">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>달력</h5>
        </CCol>
      </CRow>

      <SearchList />

      <CRow class="mb-3">
        <CCol>
          <FullCalendar :options="calendarOptions" />
        </CCol>
      </CRow>

      <CRow>
        <CCol>
          <v-icon icon="mdi-arrow-right-bold" color="success" size="sm" />
          오늘 시작하는 업무(task)
        </CCol>
      </CRow>
      <CRow>
        <CCol>
          <v-icon icon="mdi-arrow-left-bold" color="danger" size="sm" />
          오늘 종료하는 업무(task)
        </CCol>
      </CRow>
      <CRow>
        <CCol>
          <v-icon icon="mdi-rhombus" color="danger" size="sm" />
          오늘 시작하고 종료하는 업무(task)
        </CCol>
      </CRow>
    </template>

    <template v-slot:aside></template>
  </ContentBody>
</template>

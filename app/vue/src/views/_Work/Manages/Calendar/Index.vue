<script setup lang="ts">
import { computed, type ComputedRef, inject, provide, ref } from 'vue'
import { navMenu2 as navMenu } from '@/views/_Work/_menu/headermixin1'
import { useRoute } from 'vue-router'
import type { Company } from '@/store/types/settings'
import Header from '@/views/_Work/components/Header/Index.vue'
import ContentBody from '@/views/_Work/components/ContentBody/Index.vue'
import SearchList from '@/views/_Work/Manages/Projects/components/SearchList.vue'
import FullCalendar from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/daygrid'
import interactionPlugin from '@fullcalendar/interaction'

const cBody = ref()
const company = inject<ComputedRef<Company>>('company')
const comName = computed(() => company?.value?.name)

const route = useRoute()

provide('navMenu', navMenu)
provide('query', route?.query)

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

const sideNavCAll = () => cBody.value.toggle()
</script>

<template>
  <Header :page-title="comName" :nav-menu="navMenu" @side-nav-call="sideNavCAll" />

  <ContentBody ref="cBody" :nav-menu="navMenu" :query="route?.query">
    <template v-slot:default>
      <CRow class="py-2">
        <CCol>
          <h5>{{ route.name }}</h5>
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

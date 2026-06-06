<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import type { Meeting } from '@/store/types/work_meeting.ts'

const props = defineProps({
  meeting: { type: Object as PropType<Meeting>, required: true },
})

const route = useRoute()

const meetingDate = computed(() =>
  props.meeting.meeting_date ? props.meeting.meeting_date.substring(0, 10) : '',
)

const createdDate = computed(() => props.meeting.created.substring(0, 10))

const totalAttendees = computed(() => {
  const usersCount = props.meeting.attendees.length
  const otherCount = props.meeting.other_attendees
    ? props.meeting.other_attendees.split(',').length
    : 0
  return usersCount + otherCount
})

const statusColor = computed(() => {
  if (props.meeting.status === '1') return 'info'
  if (props.meeting.status === '2') return 'success'
  if (props.meeting.status === '3') return 'secondary'
  return 'secondary'
})

const statusText = computed(() => {
  if (props.meeting.status === '1') return '준비중'
  if (props.meeting.status === '2') return '완료됨'
  if (props.meeting.status === '3') return '취소됨'
  return '-'
})
</script>

<template>
  <CTableDataCell>{{ meeting.pk }}</CTableDataCell>
  <CTableDataCell v-if="!route.params.projId">{{ meeting.project_desc?.name }}</CTableDataCell>
  <CTableDataCell>
    <v-chip :color="statusColor" size="x-small" variant="flat">
      {{ statusText }}
    </v-chip>
  </CTableDataCell>
  <CTableDataCell>{{ meeting.category_desc?.name }}</CTableDataCell>
  <CTableDataCell class="text-left">
    <router-link to="">{{ meeting.title }}</router-link>
  </CTableDataCell>
  <CTableDataCell>{{ meetingDate }}</CTableDataCell>
  <CTableDataCell>{{ meeting.creator.username }}</CTableDataCell>
  <CTableDataCell>{{ totalAttendees }}</CTableDataCell>
  <CTableDataCell>{{ createdDate }}</CTableDataCell>
</template>

<script lang="ts" setup>
import { computed, type PropType } from 'vue'
import { useRoute } from 'vue-router'
import { useMeeting } from '@/store/pinia/work_meeting.ts'
import type { Meeting } from '@/store/types/work_meeting.ts'
import { timeFormat, diffDate, getMeetingStatusColor } from '@/utils/baseMixins.ts'

const props = defineProps({
  meeting: { type: Object as PropType<Meeting>, required: true },
})

const route = useRoute()
const meetingStore = useMeeting()

const meetingDate = computed(() =>
  props.meeting.meeting_date ? props.meeting.meeting_date.substring(0, 10) : '',
)

const createdDate = computed(() => props.meeting.created.substring(0, 10))

const totalAttendees = computed(() => {
  const usersCount = props.meeting.attendees.length
  const otherCount = props.meeting.other_attendees
    ? props.meeting.other_attendees.split(',').filter(v => v.trim()).length
    : 0
  return usersCount + otherCount
})

const statusColor = computed(() => getMeetingStatusColor(props.meeting.status))

const needConfirm = computed(() => {
  const meeting = props.meeting
  return (
    meeting.status === '2' &&
    !meeting?.is_confirmed &&
    meetingDate.value &&
    diffDate(meetingDate.value) > 5
  )
})

const confirmAlertColor = computed(() => {
  const meetingDate = props.meeting.meeting_date

  if (!meetingDate) return ''

  const diff = diffDate(meetingDate)

  return diff > 10 ? 'danger' : 'warning'
})

const downloadPdf = (event: Event) => {
  event.stopPropagation()
  meetingStore.generatePdf(props.meeting.pk)
}
</script>

<template>
  <CTableDataCell>{{ meeting.pk }}</CTableDataCell>
  <CTableDataCell v-if="!route.params.projId">{{ meeting.project_desc?.name }}</CTableDataCell>
  <CTableDataCell class="text-left">
    <v-chip :color="statusColor" size="x-small" variant="flat">
      {{ meeting.status_display }}
    </v-chip>

    <v-chip
      v-if="needConfirm"
      :color="confirmAlertColor"
      size="x-small"
      variant="flat"
      class="ml-1"
    >
      확정 필요
    </v-chip>
    <v-chip v-if="meeting.is_confirmed" color="success" size="x-small" variant="flat" class="ml-1">
      확정
    </v-chip>
  </CTableDataCell>
  <CTableDataCell>{{ meeting.category_desc?.name }}</CTableDataCell>
  <CTableDataCell class="text-left" :class="{ closed: meeting.status === '3' }">
    <router-link to="">{{ meeting.title }}</router-link>
    {{ diffDate(meeting.meeting_date as string) }}
  </CTableDataCell>
  <CTableDataCell>{{ timeFormat(meeting.meeting_date as string, 'min') }}</CTableDataCell>
  <CTableDataCell>{{ meeting.creator.username }}</CTableDataCell>
  <CTableDataCell>{{ totalAttendees }}</CTableDataCell>
  <CTableDataCell>{{ createdDate }}</CTableDataCell>
  <CTableDataCell class="text-center">
    <v-icon icon="mdi-file-pdf-box" color="blue-grey-lighten-3" size="20" @click="downloadPdf" />
  </CTableDataCell>
</template>

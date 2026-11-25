<script lang="ts" setup>
import { type PropType } from 'vue'
import { DEFAULT_MEETING_COLUMNS, MEETING_COLUMN_LABEL_MAP } from '../constants'
import { useMeeting } from '@/store/pinia/work_meeting'
import { useRoute, useRouter } from 'vue-router'
import { usePerms } from '@/composables/usePerms'
import type { Meeting } from '@/store/types/work_meeting'
import Pagination from '@/components/Pagination'
import MeetingItem from './MeetingItem.vue'

defineProps({
  meetingList: { type: Array as PropType<Meeting[]>, default: () => [] },
  columns: {
    type: Array as PropType<string[]>,
    default: () => DEFAULT_MEETING_COLUMNS,
  },
  page: { type: Number, default: 1 },
})

const emit = defineEmits(['page-select'])

const route = useRoute()
const router = useRouter()
const { can, PERM } = usePerms()

const meetingStore = useMeeting()
const meetingPages = (limit: number) => meetingStore.meetingPages(limit)

const goDetail = (meeting: Meeting) => {
  const projId = meeting.project_desc?.slug || (route.params.projId as string)
  if (projId && meeting.pk && can(PERM.MEETING_READ, projId)) {
    router.push({ name: '(회의) - 보기', params: { projId, meetingId: meeting.pk } })
  }
}

const pageSelect = (page: number) => emit('page-select', page)
</script>

<template>
  <CCol col="12">
    <v-divider class="mb-0" />
    <CTable striped hover small responsive align="middle">
      <CTableHead>
        <CTableRow class="text-center">
          <CTableHeaderCell scope="col">#</CTableHeaderCell>
          <template v-for="colKey in columns" :key="'head-' + colKey">
            <CTableHeaderCell
              scope="col"
              :class="{
                'text-start': colKey === 'status' || colKey === 'title',
              }"
            >
              {{ MEETING_COLUMN_LABEL_MAP[colKey] || colKey }}
            </CTableHeaderCell>
          </template>
        </CTableRow>
      </CTableHead>

      <CTableBody>
        <CTableRow
          v-for="meeting in meetingList"
          @click="goDetail(meeting)"
          class="text-center table-row pointer"
          :key="meeting.pk"
        >
          <MeetingItem :meeting="meeting" :columns="columns" />
        </CTableRow>
      </CTableBody>
    </CTable>

    <Pagination
      :active-page="page"
      :limit="8"
      :pages="meetingPages(20)"
      @active-page-change="pageSelect"
      class="mt-3"
    />
  </CCol>
</template>
